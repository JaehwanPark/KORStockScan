"""Atomic, behavior-equivalent execution sizing receipts for scalping BUYs.

The position-sizing allocator owns total quantity, the split resolver owns leg
shape, and the mechanistic entry-price resolver owns numeric prices.  This
module only validates and binds those already-authorized results into one
immutable plan.  It cannot authorize an entry, recalculate price, or increase
quantity.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

SCHEMA_VERSION = "entry_execution_sizing_plan_v1"
SCALE_IN_SCHEMA_VERSION = "scale_in_execution_sizing_plan_v1"
PRICE_SCHEMA_VERSION = "entry_price_plan_v1"
SCALE_IN_PRICE_SCHEMA_VERSION = "scale_in_price_plan_v1"
POLICY_VERSION = "execution_sizing_baseline_v1"
ENTRY_EXECUTION_SIZING_POLICY_SCHEMA = "entry_execution_sizing_policy_v1"
MECHANISTIC_ENTRY_PRICE_POLICY_SCHEMA = "mechanistic_entry_price_policy_v1"
SCALE_IN_POLICY_VERSIONS = {
    "AVG_DOWN": "avg_down_execution_sizing_baseline_v1",
    "PYRAMID": "pyramid_execution_sizing_baseline_v1",
}
OWNER = "entry_execution_sizing_owner"
SCALE_IN_OWNERS = {
    "AVG_DOWN": "avg_down_execution_sizing_owner",
    "PYRAMID": "pyramid_execution_sizing_owner",
}
SCALE_IN_ACTION_OWNERS = {
    "AVG_DOWN": "avg_down_action_owner",
    "PYRAMID": "pyramid_action_owner",
}
PRICE_OWNER = "mechanistic_entry_price_resolver"
ENTRY_PRICE_POLICY_VERSION = "mechanistic_entry_price_p1_baseline_v1"
ENTRY_PRICE_POLICY_SHA256 = hashlib.sha256(
    ENTRY_PRICE_POLICY_VERSION.encode("ascii")
).hexdigest()
SCALE_IN_PRICE_OWNER = "existing_scale_in_price_resolver"
QUANTITY_OWNER = "position_sizing_dynamic_formula"
PRICE_POLICY_ENV_KEYS = frozenset({
    "KORSTOCKSCAN_SCALPING_NORMAL_DEFENSIVE_BPS",
    "KORSTOCKSCAN_SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS",
    "KORSTOCKSCAN_SCALPING_NORMAL_FAVORABLE_DEFENSIVE_BPS",
    "KORSTOCKSCAN_SCALPING_NORMAL_WEAK_DEFENSIVE_BPS",
})

_ENTRY_EXECUTION_POLICY_PREFIX = "KORSTOCKSCAN_ENTRY_EXECUTION_SIZING_POLICY_"
_ENTRY_PRICE_POLICY_PREFIX = "KORSTOCKSCAN_MECHANISTIC_ENTRY_PRICE_POLICY_"


def _enabled(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _runtime_policy(
    *,
    prefix: str,
    schema: str,
    owner: str,
    active_date: str | None = None,
) -> tuple[dict[str, Any] | None, str]:
    """Load one immutable dated policy without granting additional authority."""

    if not _enabled(os.getenv(f"{prefix}ENABLED")):
        return None, "disabled_baseline"
    policy_path = Path(str(os.getenv(f"{prefix}FILE") or "").strip())
    expected_version = str(os.getenv(f"{prefix}VERSION") or "").strip()
    expected_source_date = str(os.getenv(f"{prefix}SOURCE_DATE") or "").strip()
    expected_active_date = str(os.getenv(f"{prefix}ACTIVE_DATE") or "").strip()
    expected_sha256 = str(os.getenv(f"{prefix}SHA256") or "").strip().lower()
    if not all(
        (str(policy_path), expected_version, expected_source_date, expected_active_date, expected_sha256)
    ) or not policy_path.is_file():
        return None, "policy_identity_missing"
    try:
        encoded = policy_path.read_bytes()
        payload = json.loads(encoded.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "policy_unreadable"
    if not isinstance(payload, dict):
        return None, "policy_payload_invalid"
    checks = (
        payload.get("schema_version") == schema,
        payload.get("policy_owner") == owner,
        payload.get("policy_version") == expected_version,
        payload.get("source_date") == expected_source_date,
        payload.get("active_date") == expected_active_date,
        hashlib.sha256(encoded).hexdigest() == expected_sha256,
        payload.get("runtime_apply_allowed") is True,
    )
    if not all(checks):
        return None, "policy_contract_invalid"
    runtime_date = str(active_date or datetime.now(KST).date().isoformat())
    if expected_active_date != runtime_date:
        return None, "policy_inactive_date"
    return payload, "loaded"


# Existing approved numeric BPS envelope; replay cannot broaden this surface.
PRICE_POLICY_BPS_BOUNDS = {
    'normal_defensive_bps': (20, 50), 'conditional_strong_defensive_bps': (5, 20),
    'normal_favorable_defensive_bps': (10, 35), 'normal_weak_defensive_bps': (35, 65),
}


def mechanistic_entry_price_authority_valid(policy: Any) -> bool:
    """The numeric-price owner cannot acquire action or sizing authority."""
    if not isinstance(policy, dict):
        return False
    runtime_env = policy.get("runtime_env")
    evidence = policy.get("price_selection_evidence")
    if evidence is not None:
        from src.engine.scalping.strategy_owner_replay import entry_price_selection_evidence_valid
        if (not entry_price_selection_evidence_valid(evidence)
            or policy.get("cost_adjusted_ev_pct") != evidence["metrics"]["source_quality_adjusted_ev_pct"]
            or policy.get("exact_terminal_sample_count") != evidence["metrics"]["paired_sample_count"]
            or evidence["holdout_dates"][-1] > str(policy.get("source_date") or "")
            or policy.get("minimum_cost_adjusted_ev_pct") != 0.0
            or runtime_env != {"KORSTOCKSCAN_SCALPING_" + evidence["target_value_key"].upper():
                               str(evidence["selected_bps"])}):
            return False
    elif (policy.get("minimum_cost_adjusted_ev_pct") == 0.0
          or str(policy.get("source_date") or "") >= "2026-09-17"):
        return False
    return bool(
        policy.get("policy_owner") == PRICE_OWNER
        and type(policy.get("provider_calls")) is int
        and policy["provider_calls"] == 0
        and policy.get("ai_price_authority") is False
        and policy.get("action_quantity_leg_scale_in_authority", False) is False
        and str(policy.get("candidate_id") or "").strip()
        and "ai" not in str(policy["candidate_id"]).lower()
        and isinstance(runtime_env, dict)
        and len(runtime_env) == 1
        and set(runtime_env) <= PRICE_POLICY_ENV_KEYS
        and all(_positive_int(value) > 0 for value in runtime_env.values())
    )


def runtime_mechanistic_entry_price_policy(
    *, active_date: str | None = None
) -> tuple[dict[str, Any], str]:
    policy, status = _runtime_policy(
        prefix=_ENTRY_PRICE_POLICY_PREFIX,
        schema=MECHANISTIC_ENTRY_PRICE_POLICY_SCHEMA,
        owner=PRICE_OWNER,
        active_date=active_date,
    )
    if policy is None:
        if status == "disabled_baseline":
            return {
                "policy_version": ENTRY_PRICE_POLICY_VERSION,
                "policy_sha256": ENTRY_PRICE_POLICY_SHA256,
                "candidate_id": "p1_current_resolver",
                "runtime_env": {},
            }, status
        return {}, status
    if not mechanistic_entry_price_authority_valid(policy):
        return {}, "policy_authority_invalid"
    candidate_id = str(policy.get("candidate_id") or "").strip()
    if not candidate_id or "ai" in candidate_id.lower():
        return {}, "policy_candidate_invalid"
    runtime_env = policy.get("runtime_env")
    if not isinstance(runtime_env, dict) or any(
        str(os.getenv(str(key)) or "") != str(value)
        for key, value in runtime_env.items()
    ):
        return {}, "policy_runtime_env_mismatch"
    return {
        **policy,
        "policy_sha256": str(os.getenv(f"{_ENTRY_PRICE_POLICY_PREFIX}SHA256")),
    }, status


def scoped_entry_price_bps(profile, configured_bps, *, venue, session, policy_bundle_sha256=None):
    """A global env surface carries a scoped policy, never a cross-venue trial."""
    policy, status = runtime_mechanistic_entry_price_policy()
    proof = policy.get('price_selection_evidence')
    if not proof or status != 'loaded':
        return configured_bps
    from src.engine.scalping.strategy_owner_replay import ENTRY_REPLAY_PROFILES
    if ENTRY_REPLAY_PROFILES.get(profile) != proof['target_value_key']:
        return configured_bps
    return (proof['selected_bps'] if profile == proof['profile']
            and [venue, session, policy_bundle_sha256] == proof['scope_parent'][:3]
            else proof['incumbent_bps'])


def runtime_entry_execution_sizing_policy(
    *, active_date: str | None = None
) -> tuple[dict[str, Any] | None, str]:
    policy, status = _runtime_policy(
        prefix=_ENTRY_EXECUTION_POLICY_PREFIX,
        schema=ENTRY_EXECUTION_SIZING_POLICY_SCHEMA,
        owner=OWNER,
        active_date=active_date,
    )
    if policy is None:
        return None, status
    if (
        policy.get("action_authority") is not False
        or policy.get("price_authority") is not False
        or policy.get("scale_in_authority") is not False
        or policy.get("quantity_conservation_required") is not True
    ):
        return None, "policy_authority_invalid"
    from src.engine.scalping.entry_split_order_plan import quantity_leg_policy_selection_evidence_valid

    if not quantity_leg_policy_selection_evidence_valid(policy):
        return None, "selection_evidence_invalid"
    for path_key, sha_key in (
        ("quantity_policy_file", "quantity_policy_sha256"),
        ("split_policy_file", "split_policy_sha256"),
    ):
        referenced_path = Path(str(policy.get(path_key) or "").strip())
        expected_sha256 = str(policy.get(sha_key) or "").strip().lower()
        try:
            observed_sha256 = hashlib.sha256(referenced_path.read_bytes()).hexdigest()
        except OSError:
            return None, "referenced_policy_missing"
        if not expected_sha256 or observed_sha256 != expected_sha256:
            return None, "referenced_policy_hash_invalid"
    return policy, status


def _positive_int(value: Any) -> int:
    if isinstance(value, bool) or type(value) not in (str, int, float):
        return 0
    try:
        if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
            return 0
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def _content_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _price_candidate_id(order: dict[str, Any], index: int) -> str:
    del index
    existing = str(order.get("price_candidate_id") or "").strip()
    if existing:
        return existing
    mode = str(
        order.get("entry_split_order_execution_mode")
        or order.get("price_source")
        or "current_resolver"
    ).strip()
    return mode


def _price_plan_receipt(
    *,
    schema_version: str,
    stage: str,
    action_receipt_id: str,
    owner: str,
    policy_version: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Freeze resolver output so sizing can reference, but not rewrite, prices."""

    core = {
        "schema_version": schema_version,
        "stage": stage,
        "action_receipt_id": action_receipt_id,
        "price_owner": owner,
        "price_policy_version": policy_version,
        "price_candidates": candidates,
    }
    receipt_sha256 = _content_sha256(core)
    return {
        **core,
        "price_plan_id": f"{stage}-price-{receipt_sha256[:24]}",
        "price_plan_sha256": receipt_sha256,
    }


def compose_entry_execution_sizing_plan(
    planned_orders: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    expected_total_qty: int,
    action_receipt: dict[str, Any] | None,
    quantity_policy_version: str | None,
    split_policy_version: str | None,
    replay_context: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate and decorate an existing entry plan without changing it.

    Probe-first plans contain only the immediately submitted one-share order;
    their frozen continuation owns the residual quantities.  Both parts are
    included in the same conservation check and plan hash.
    """

    orders = [dict(item) for item in (planned_orders or []) if isinstance(item, dict)]
    receipt = action_receipt if isinstance(action_receipt, dict) else {}
    expected_total_qty = _positive_int(expected_total_qty)
    action_receipt_id = str(receipt.get("evaluation_attempt_id") or "").strip()
    action_owner = str(receipt.get("entry_primary_decision_owner") or "").strip()
    machine_action = str(receipt.get("entry_mechanistic_action") or "").strip().upper()
    ai_screen_pass = receipt.get("entry_ai_screen_pass") is True
    execution_policy, execution_policy_status = (
        runtime_entry_execution_sizing_policy()
    )
    price_policy, price_policy_status = runtime_mechanistic_entry_price_policy()

    blockers: list[str] = []
    if not action_receipt_id:
        blockers.append("action_receipt_id_missing")
    if action_owner != "mechanistic_entry_adjudicator":
        blockers.append("entry_action_owner_invalid")
    if machine_action != "ENTER_NOW":
        blockers.append("entry_action_not_enter_now")
    if not ai_screen_pass:
        blockers.append("auxiliary_ai_pass_missing")
    if expected_total_qty <= 0:
        blockers.append("expected_total_qty_invalid")
    if not orders:
        blockers.append("planned_orders_missing")
    if execution_policy_status not in {"disabled_baseline", "loaded"}:
        blockers.append(f"entry_execution_sizing_{execution_policy_status}")
    if price_policy_status not in {"disabled_baseline", "loaded"}:
        blockers.append(f"entry_price_{price_policy_status}")
    if execution_policy is not None:
        if str(quantity_policy_version or "") != str(
            execution_policy.get("quantity_policy_version") or ""
        ):
            blockers.append("integrated_quantity_policy_version_mismatch")
        if str(split_policy_version or "") != str(
            execution_policy.get("split_policy_version") or ""
        ):
            blockers.append("integrated_split_policy_version_mismatch")

    immediate_qty = sum(_positive_int(item.get("qty")) for item in orders)
    continuation: dict[str, Any] | None = None
    if len(orders) == 1 and isinstance(
        orders[0].get("entry_split_order_probe_continuation"), dict
    ):
        continuation = dict(orders[0]["entry_split_order_probe_continuation"])
    residual_quantities = (
        [
            _positive_int(value)
            for value in continuation.get("residual_quantities") or []
        ]
        if continuation is not None
        else []
    )
    deferred_qty = sum(residual_quantities)
    conserved_total = immediate_qty + deferred_qty
    if any(_positive_int(item.get("qty")) <= 0 for item in orders):
        blockers.append("nonpositive_leg_qty")
    if len(orders) > immediate_qty:
        blockers.append("leg_count_exceeds_immediate_qty")
    if deferred_qty and any(value <= 0 for value in residual_quantities):
        blockers.append("nonpositive_residual_leg_qty")
    if (
        continuation is not None
        and _positive_int(continuation.get("requested_qty")) != expected_total_qty
    ):
        blockers.append("probe_continuation_requested_qty_mismatch")
    if conserved_total != expected_total_qty:
        blockers.append("quantity_conservation_failed")

    price_plan: list[dict[str, Any]] = []
    legs: list[dict[str, Any]] = []
    decorated_orders: list[dict[str, Any]] = []
    price_policy_versions = {
        str(order.get("entry_price_policy_version") or "").strip() for order in orders
    }
    price_policy_versions.discard("")
    price_policy_sha256s = {
        str(order.get("entry_price_policy_sha256") or "").strip() for order in orders
    }
    price_policy_sha256s.discard("")
    price_source_receipt_sha256s = {
        str(order.get("entry_price_receipt_sha256") or "").strip()
        for order in orders
    }
    price_source_receipt_sha256s.discard("")
    price_owners = {
        str(order.get("entry_price_owner") or "").strip() for order in orders
    }
    price_owners.discard("")
    if price_owners != {PRICE_OWNER}:
        blockers.append("entry_price_owner_invalid")
    expected_price_policy_version = str(
        price_policy.get("policy_version") or ENTRY_PRICE_POLICY_VERSION
    )
    expected_price_policy_sha256 = str(
        price_policy.get("policy_sha256") or ENTRY_PRICE_POLICY_SHA256
    )
    if price_policy_versions != {expected_price_policy_version}:
        blockers.append("entry_price_policy_version_missing_or_conflicting")
    if price_policy_sha256s != {expected_price_policy_sha256}:
        blockers.append("entry_price_policy_sha256_missing_or_invalid")
    if len(price_source_receipt_sha256s) != 1 or not all(
        len(value) == 64 and all(character in "0123456789abcdef" for character in value)
        for value in price_source_receipt_sha256s
    ):
        blockers.append("entry_price_source_receipt_sha256_missing_or_conflicting")
    for index, order in enumerate(orders, start=1):
        price = _positive_int(order.get("price"))
        order_type = str(
            order.get("order_type_code") or order.get("order_type") or "00"
        ).strip()
        if price <= 0 and order_type not in {"3", "03"}:
            blockers.append(f"leg_{index}_numeric_price_missing")
        candidate_id = _price_candidate_id(order, index)
        price_leg_id = str(order.get("entry_price_leg_id") or "").strip()
        if not price_leg_id:
            price_leg_id = f"{candidate_id}:leg{index}"
        price_plan.append(
            {
                "price_candidate_id": candidate_id,
                "price_leg_id": price_leg_id,
                "numeric_price": price,
                "order_type_code": order_type,
                "source": PRICE_OWNER,
                "captured_at": order.get("entry_price_captured_at"),
                "route": order.get("entry_price_route"),
                "epoch": order.get("entry_price_epoch"),
                "source_receipt_sha256": order.get("entry_price_receipt_sha256"),
            }
        )
        legs.append(
            {
                "leg_index": index,
                "qty": _positive_int(order.get("qty")),
                "price_candidate_id": candidate_id,
                "price_leg_id": price_leg_id,
                "numeric_price": price,
                "execution_phase": "immediate",
            }
        )
        decorated_orders.append(
            {
                **order,
                "price_candidate_id": candidate_id,
                "entry_price_leg_id": price_leg_id,
            }
        )
    for residual_index, residual_qty in enumerate(residual_quantities, start=1):
        candidate_id = f"probe_residual_resolver:leg{residual_index + 1}"
        legs.append(
            {
                "leg_index": len(orders) + residual_index,
                "qty": residual_qty,
                "price_candidate_id": candidate_id,
                "price_leg_id": candidate_id,
                "numeric_price": None,
                "execution_phase": "after_verified_probe_fill",
            }
        )
        price_plan.append(
            {
                "price_candidate_id": candidate_id,
                "price_leg_id": candidate_id,
                "numeric_price": None,
                "order_type_code": "00",
                "source": "probe_fill_price_resolver",
            }
        )
    immediate_price_candidate_ids = {
        str(item.get("price_candidate_id") or "") for item in price_plan[: len(orders)]
    }
    if len(immediate_price_candidate_ids) != 1:
        blockers.append("entry_price_candidate_conflict")
    price_leg_ids = [str(item.get("price_leg_id") or "") for item in price_plan]
    if len(price_leg_ids) != len(set(price_leg_ids)):
        blockers.append("duplicate_price_leg_id")
    if len(legs) > expected_total_qty:
        blockers.append("leg_count_exceeds_total_qty")

    price_receipt = _price_plan_receipt(
        schema_version=PRICE_SCHEMA_VERSION,
        stage="entry",
        action_receipt_id=action_receipt_id,
        owner=PRICE_OWNER,
        policy_version=(
            next(iter(price_policy_versions))
            if len(price_policy_versions) == 1
            else "invalid"
        ),
        candidates=price_plan,
    )
    valid_price_candidate_ids = {
        str(item.get("price_candidate_id") or "")
        for item in price_receipt["price_candidates"]
    }
    if any(
        str(leg.get("price_candidate_id") or "") not in valid_price_candidate_ids
        for leg in legs
    ):
        blockers.append("price_candidate_not_issued_by_price_owner")

    plan_core = {
        "schema_version": SCHEMA_VERSION,
        "price_schema_version": PRICE_SCHEMA_VERSION,
        "stage": "entry",
        "action_receipt_id": action_receipt_id,
        "action_owner": action_owner,
        "scanner_promotion_id": str(receipt.get("scanner_promotion_id") or ""),
        "policy_bundle_hash": str(
            receipt.get("policy_bundle_hash")
            or receipt.get("machine_bundle_sha256")
            or ""
        ),
        "effective_venue": str(receipt.get("effective_venue") or ""),
        "market_session_bucket": str(receipt.get("market_session_bucket") or ""),
        "quantity_policy_owner": QUANTITY_OWNER,
        "quantity_policy_version": str(quantity_policy_version or "baseline_current"),
        "split_policy_version": str(split_policy_version or "baseline_current"),
        "price_policy_owner": PRICE_OWNER,
        "price_policy_sha256": (
            next(iter(price_policy_sha256s)) if len(price_policy_sha256s) == 1 else None
        ),
        "price_source_receipt_sha256": (
            next(iter(price_source_receipt_sha256s))
            if len(price_source_receipt_sha256s) == 1
            else None
        ),
        "price_plan_id": price_receipt["price_plan_id"],
        "price_plan_sha256": price_receipt["price_plan_sha256"],
        "execution_sizing_policy": str(
            (execution_policy or {}).get("policy_version") or POLICY_VERSION
        ),
        "execution_sizing_policy_status": execution_policy_status,
        "execution_sizing_policy_sha256": (
            str(os.getenv(f"{_ENTRY_EXECUTION_POLICY_PREFIX}SHA256") or "")
            if execution_policy is not None
            else hashlib.sha256(POLICY_VERSION.encode("ascii")).hexdigest()
        ),
        "migration_baseline": execution_policy is None,
        "total_qty": expected_total_qty,
        "immediate_qty": immediate_qty,
        "deferred_probe_residual_qty": deferred_qty,
        "leg_count": len(legs),
        "legs": legs,
        "price_candidates": price_plan,
        "quantity_conservation_holds": conserved_total == expected_total_qty,
        "quantity_increase_forbidden": True,
        "action_authority_forbidden": True,
        "valid": not blockers,
        "blockers": blockers,
    }
    plan_id = f"entry-sizing-{_content_sha256(plan_core)[:24]}"
    common_fields = {
        "entry_execution_sizing_plan_schema": SCHEMA_VERSION,
        "entry_execution_sizing_plan_id": plan_id,
        "entry_execution_sizing_policy": plan_core["execution_sizing_policy"],
        "entry_execution_sizing_policy_status": execution_policy_status,
        "entry_execution_sizing_policy_sha256": plan_core[
            "execution_sizing_policy_sha256"
        ],
        "entry_execution_sizing_action_receipt_id": action_receipt_id or "-",
        "entry_execution_sizing_quantity_policy_version": plan_core[
            "quantity_policy_version"
        ],
        "entry_execution_sizing_split_policy_version": plan_core[
            "split_policy_version"
        ],
        "entry_execution_sizing_total_qty": expected_total_qty,
        "entry_execution_sizing_immediate_qty": immediate_qty,
        "entry_execution_sizing_deferred_qty": deferred_qty,
        "entry_execution_sizing_leg_count": plan_core["leg_count"],
        "entry_execution_sizing_quantity_conservation_holds": plan_core[
            "quantity_conservation_holds"
        ],
        "entry_execution_sizing_quantity_increase_forbidden": True,
        "entry_execution_sizing_migration_baseline": plan_core["migration_baseline"],
        "entry_execution_sizing_plan_emitted": True,
        "entry_execution_sizing_valid": not blockers,
        "entry_execution_sizing_blockers": blockers,
        "entry_execution_sizing_plan_sha256": _content_sha256(plan_core),
        "entry_price_plan_schema": PRICE_SCHEMA_VERSION,
        "entry_price_plan_id": price_receipt["price_plan_id"],
        "entry_price_plan_owner": PRICE_OWNER,
        "entry_price_plan_sha256": price_receipt["price_plan_sha256"],
        "entry_price_source_receipt_sha256": plan_core[
            "price_source_receipt_sha256"
        ],
    }
    decorated_orders = [{**item, **common_fields} for item in decorated_orders]
    if continuation is not None and decorated_orders:
        continuation_common = dict(continuation.get("common_fields") or {})
        continuation["common_fields"] = {**continuation_common, **common_fields}
        decorated_orders[0]["entry_split_order_probe_continuation"] = continuation
    # Observation failure must never alter an already validated broker plan.
    replay_seed = None
    if isinstance(replay_context, dict) and replay_context and not blockers:
        from src.engine.scalping.strategy_owner_replay import freeze_entry_opportunity
        replay_seed = freeze_entry_opportunity(
            plan_core, stock_code=str(replay_context.get("stock_code") or ""),
            observed_at=replay_context.get("observed_at", datetime.now(KST).timestamp()),
            profile=replay_context.get("profile"),
            profile_bps=replay_context.get("profile_bps"),
            sizing_context=replay_context.get('sizing_context'),
            candidate_leg_plan=replay_context.get('candidate_leg_plan'),
            operating_context=replay_context.get('operating_context'),
            anchor_price=(orders[0].get("entry_price_current_price") if orders else None),
        )
    return decorated_orders, {
        **common_fields,
        "entry_opportunity_replay_seed": replay_seed,
        "entry_price_plan": price_receipt,
        "entry_execution_sizing_plan": plan_core,
    }


def compose_scale_in_execution_sizing_plan(
    planned_orders: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    authorized_total_qty: int,
    action_receipt: dict[str, Any] | None,
    quantity_policy_version: str | None,
    split_policy_version: str | None,
    price_policy_version: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Bind an already-authorized AVG_DOWN/PYRAMID plan without changing it.

    The existing action, price, quantity, and hard-safety owners remain
    authoritative.  This receipt only proves that the final multi-leg order
    conserves the quantity those owners allowed and keeps AVG_DOWN/PYRAMID in
    separate namespaces.
    """

    orders = [dict(item) for item in (planned_orders or []) if isinstance(item, dict)]
    receipt = action_receipt if isinstance(action_receipt, dict) else {}
    add_type = (
        str(
            receipt.get("add_type")
            or (orders[0].get("add_type") if orders else "")
            or ""
        )
        .strip()
        .upper()
    )
    action_receipt_id = str(receipt.get("scale_in_decision_id") or "").strip()
    position_episode_id = str(receipt.get("position_episode_id") or "").strip()
    action_owner = str(receipt.get("scale_in_action_owner") or "").strip()
    authorized_total_qty = _positive_int(authorized_total_qty)
    total_qty = sum(_positive_int(item.get("qty")) for item in orders)
    expected_action_owner = SCALE_IN_ACTION_OWNERS.get(add_type, "")
    policy_version = SCALE_IN_POLICY_VERSIONS.get(add_type, "")
    blockers: list[str] = []
    if add_type not in SCALE_IN_POLICY_VERSIONS:
        blockers.append("scale_in_stage_invalid")
    if not action_receipt_id:
        blockers.append("scale_in_action_receipt_id_missing")
    if not position_episode_id:
        blockers.append("scale_in_position_episode_id_missing")
    if not expected_action_owner or action_owner != expected_action_owner:
        blockers.append("scale_in_action_owner_invalid")
    if receipt.get("scale_in_action_receipt_schema") != ("scale_in_action_receipt_v1"):
        blockers.append("scale_in_action_receipt_schema_invalid")
    if receipt.get("should_add") is not True:
        blockers.append("scale_in_action_not_add")
    if authorized_total_qty <= 0:
        blockers.append("authorized_total_qty_invalid")
    if not orders:
        blockers.append("planned_orders_missing")
    if total_qty <= 0 or any(_positive_int(item.get("qty")) <= 0 for item in orders):
        blockers.append("nonpositive_leg_qty")
    if total_qty > authorized_total_qty:
        blockers.append("quantity_increase_detected")
    if total_qty != authorized_total_qty:
        blockers.append("quantity_conservation_failed")
    if len(orders) > total_qty:
        blockers.append("leg_count_exceeds_total_qty")

    legs: list[dict[str, Any]] = []
    price_candidates: list[dict[str, Any]] = []
    decorated_orders: list[dict[str, Any]] = []
    for index, order in enumerate(orders, start=1):
        qty = _positive_int(order.get("qty"))
        numeric_price = _positive_int(order.get("price"))
        order_type_code = str(
            order.get("order_type_code") or order.get("order_type") or "00"
        ).strip()
        is_market = order_type_code in {"3", "03", "6", "06", "16"}
        if numeric_price <= 0 and not is_market:
            blockers.append(f"leg_{index}_numeric_price_missing")
        candidate_id = str(order.get("price_candidate_id") or "").strip()
        if not candidate_id:
            price_source = str(
                order.get("price_source")
                or price_policy_version
                or "current_scale_in_resolver"
            ).strip()
            candidate_id = f"{price_source}:leg{index}"
        leg = {
            "leg_index": index,
            "qty": qty,
            "price_candidate_id": candidate_id,
            "numeric_price": numeric_price,
            "order_type_code": order_type_code,
        }
        legs.append(leg)
        price_candidates.append(
            {
                "price_candidate_id": candidate_id,
                "numeric_price": numeric_price,
                "order_type_code": order_type_code,
                "source": str(price_policy_version or "current_scale_in_resolver"),
            }
        )
        decorated_orders.append({**order, "price_candidate_id": candidate_id})

    price_candidate_ids = [
        str(item.get("price_candidate_id") or "") for item in price_candidates
    ]
    if len(price_candidate_ids) != len(set(price_candidate_ids)):
        blockers.append("duplicate_price_candidate_id")

    price_receipt = _price_plan_receipt(
        schema_version=SCALE_IN_PRICE_SCHEMA_VERSION,
        stage=add_type.lower() if add_type else "scale_in",
        action_receipt_id=action_receipt_id,
        owner=SCALE_IN_PRICE_OWNER,
        policy_version=str(price_policy_version or "current_scale_in_resolver"),
        candidates=price_candidates,
    )
    valid_price_candidate_ids = {
        str(item.get("price_candidate_id") or "")
        for item in price_receipt["price_candidates"]
    }
    if any(
        str(leg.get("price_candidate_id") or "") not in valid_price_candidate_ids
        for leg in legs
    ):
        blockers.append("price_candidate_not_issued_by_price_owner")

    quantity_conservation_holds = bool(
        total_qty > 0
        and total_qty == authorized_total_qty
        and total_qty == sum(leg["qty"] for leg in legs)
    )
    plan_core = {
        "schema_version": SCALE_IN_SCHEMA_VERSION,
        "stage": add_type.lower(),
        "add_type": add_type,
        "action_receipt_id": action_receipt_id,
        "position_episode_id": position_episode_id,
        "action_owner": action_owner,
        "execution_sizing_owner": SCALE_IN_OWNERS.get(add_type, ""),
        "execution_sizing_policy": policy_version,
        "quantity_policy_owner": QUANTITY_OWNER,
        "quantity_policy_version": str(quantity_policy_version or "baseline_current"),
        "split_policy_version": str(
            split_policy_version or f"{add_type.lower()}_unsplit"
        ),
        "price_policy_version": str(
            price_policy_version or "current_scale_in_resolver"
        ),
        "price_plan_schema": SCALE_IN_PRICE_SCHEMA_VERSION,
        "price_plan_id": price_receipt["price_plan_id"],
        "price_plan_sha256": price_receipt["price_plan_sha256"],
        "migration_baseline": True,
        "authorized_total_qty": authorized_total_qty,
        "total_qty": total_qty,
        "leg_count": len(legs),
        "legs": legs,
        "price_candidates": price_candidates,
        "quantity_conservation_holds": quantity_conservation_holds,
        "quantity_increase_forbidden": True,
        "action_authority_forbidden": True,
        "valid": not blockers,
        "blockers": blockers,
    }
    plan_sha256 = _content_sha256(plan_core)
    plan_id = f"{add_type.lower()}-sizing-{plan_sha256[:24]}"
    prefix = "scale_in_execution_sizing_"
    common_fields = {
        f"{prefix}plan_schema": SCALE_IN_SCHEMA_VERSION,
        f"{prefix}plan_id": plan_id,
        f"{prefix}policy": policy_version,
        f"{prefix}stage": add_type,
        f"{prefix}action_receipt_id": action_receipt_id or "-",
        f"{prefix}action_owner": action_owner or "-",
        f"{prefix}quantity_policy_version": plan_core["quantity_policy_version"],
        f"{prefix}split_policy_version": plan_core["split_policy_version"],
        f"{prefix}price_policy_version": plan_core["price_policy_version"],
        f"{prefix}authorized_total_qty": authorized_total_qty,
        f"{prefix}total_qty": total_qty,
        f"{prefix}leg_count": len(legs),
        f"{prefix}quantity_conservation_holds": plan_core[
            "quantity_conservation_holds"
        ],
        f"{prefix}quantity_increase_forbidden": True,
        f"{prefix}migration_baseline": True,
        f"{prefix}plan_emitted": True,
        f"{prefix}valid": not blockers,
        f"{prefix}blockers": blockers,
        f"{prefix}plan_sha256": plan_sha256,
        "scale_in_price_plan_schema": SCALE_IN_PRICE_SCHEMA_VERSION,
        "scale_in_price_plan_id": price_receipt["price_plan_id"],
        "scale_in_price_plan_owner": SCALE_IN_PRICE_OWNER,
        "scale_in_price_plan_sha256": price_receipt["price_plan_sha256"],
    }
    decorated_orders = [{**item, **common_fields} for item in decorated_orders]
    return decorated_orders, {
        **common_fields,
        "scale_in_price_plan": price_receipt,
        "scale_in_execution_sizing_plan": plan_core,
    }
