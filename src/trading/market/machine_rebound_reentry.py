"""Record natural owner decisions and consume only exact PREOPEN receipts.

No API calls, new subscriptions, order placement, or cancellation changes.
The early exception is limited to an immediately marketable complete plan;
all subsequent owner/broker guards and the existing open-buy cancellation run.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.trading.config.machine_rebound_reentry_policy import (
    DEFAULT_POLICY_DIR,
    SOURCE_AUTHORITY,
    digest,
    load_policy,
    numeric,
    scope_identity,
)
from src.trading.market.micro_confirmation import (
    advance_live_dynamic_confirmation,
    dynamic_policy_for_scope,
    evaluate_dynamic_micro_confirmation,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import write_json_object_generation_safe

SOURCE_ROOT = DATA_DIR / "report" / "machine_rebound_reentry_observations"


def rising_confirmation(frame: dict[str, Any]) -> bool:
    """Shared live/replay decision: flat is not rising; no future checkpoint."""
    checkpoint = frame.get("checkpoint") or {}
    policy = dynamic_policy_for_scope(
        owner=frame.get("owner", ""),
        scope_id=frame.get("scope_id", ""),
        symbol=frame.get("symbol", ""),
    )
    result = evaluate_dynamic_micro_confirmation({0: checkpoint}, policy=policy)
    bid = numeric(checkpoint.get("bid_return_bps"))
    rebound = numeric(checkpoint.get("bid_recovery_from_low_bps"))
    return bool(
        result.get("terminal_action") == "ENTER"
        and result.get("selected_delay_sec") == 0
        and (
            (bid is not None and bid > 0)
            or (rebound is not None and rebound >= policy.minimum_rebound_from_low_bps)
        )
    )


def immediate_plan_feasible(frame: dict[str, Any]) -> bool:
    checkpoint = frame.get("checkpoint") or {}
    ask, depth = numeric(checkpoint.get("best_ask")), numeric(
        checkpoint.get("best_ask_quantity")
    )
    legs = frame.get("legs") or []
    if not legs or ask is None or ask <= 0 or depth is None:
        return False
    quantities = [numeric(leg.get("quantity")) for leg in legs]
    prices = [numeric(leg.get("entry_price")) for leg in legs]
    return bool(
        all(qty is not None and qty > 0 and qty.is_integer() for qty in quantities)
        and all(price is not None and price >= ask for price in prices)
        and depth >= sum(quantities)
    )


def observe_owner_decision(
    *,
    state: dict[str, Any],
    now: datetime,
    decision: Any,
    scope_id: str,
    session: str,
    source_signal_id: str,
    signal_valid_until: datetime,
    owner_contract: dict[str, Any],
    legs: list[dict[str, Any]],
    reference_price: int,
    route: str,
    timing_session: str | None = None,
    source_root: Path = SOURCE_ROOT,
    policy_root: Path = DEFAULT_POLICY_DIR,
) -> dict[str, Any]:
    """Return a short-lived permit; a missing/failed recorder cannot grant one."""
    result: dict[str, Any] = {"allow_market_exception": False, "status": "baseline"}
    if now.tzinfo is None or signal_valid_until.tzinfo is None:
        return {**result, "status": "invalid_signal_time"}
    history = state.get("rebound_reentry_observation") or {}
    if not isinstance(history, dict):
        return {**result, "status": "source_history_invalid"}
    if not decision.blocked and not history.get("opportunity_id"):
        return result
    if (
        not legs
        or now > signal_valid_until
        or any(
            int(leg.get("quantity") or 0) <= 0 or int(leg.get("entry_price") or 0) <= 0
            for leg in legs
        )
    ):
        return {**result, "status": "owner_context_incomplete"}
    scope = {
        "owner": decision.owner,
        "scope_id": scope_id,
        "symbol": decision.symbol,
        "listing_market": decision.listing_market,
        "venue": route,
        "session": session,
        "entry_state": "FLAT_NEW_ENTRY",
    }
    if not history.get("opportunity_id"):
        history = {
            "opportunity_id": digest(
                {
                    **scope,
                    "trade_date": now.date().isoformat(),
                    "source_signal_id": source_signal_id,
                }
            ),
            "basis_notional_krw": sum(
                int(leg["entry_price"]) * int(leg["quantity"]) for leg in legs
            ),
            "scope": scope,
            "first_observed_at": now.isoformat(),
            "last_heartbeat_at": now.isoformat(),
            "trace_complete": True,
            "scan_last_bar": owner_contract.get("scan_last_bar"),
            "source_root": str(source_root),
        }
    if history.get("closed"):
        return result
    cost = comparison_cost_contract(now)
    from src.trading.config.machine_entry_timing_policy import (
        resolve_entry_confirmation_policy,
    )
    from src.trading.order.tick_utils import move_price_by_ticks

    existing_timing = resolve_entry_confirmation_policy(
        target_date=now.date(),
        owner=decision.owner,
        scope_id=scope_id,
        symbol=decision.symbol,
        session=timing_session or session,
        entry_state="UNSPECIFIED",
    )
    owner_runtime_policy_hash = owner_contract.get("runtime_policy_hash")
    owner_contract = {
        **{
            key: value
            for key, value in owner_contract.items()
            if key != "runtime_policy_hash"
        },
        "baseline_confirmation_mode": (
            "immediate_owner_guards"
            if existing_timing.get("mode") == "baseline_immediate"
            else "other_timing_policy"
        ),
    }

    target = move_price_by_ticks(reference_price, int(owner_contract["target_ticks"]))
    confirmation = advance_live_dynamic_confirmation(
        now=now,
        signal_decision_at=now,
        checkpoint_sec=0,
        prior_checkpoints={},
        prior_anchor={},
        symbol=decision.symbol,
        route=route,
        owner=decision.owner,
        baseline_fill_price=reference_price,
        owner_entry_limit_price=min(int(leg["entry_price"]) for leg in legs),
        owner_target_price=target,
        round_trip_cost_pct=cost["round_trip_cost_pct"],
        widget_take_profit=False,
        scope_id=scope_id,
    )
    checkpoint = (confirmation.get("checkpoints") or {}).get("0") or {}
    frame = {
        "schema": "machine_rebound_owner_decision_v1",
        **SOURCE_AUTHORITY,
        **scope,
        "trade_date": now.date().isoformat(),
        "observed_at": now.isoformat(),
        "opportunity_id": history["opportunity_id"],
        "basis_notional_krw": history["basis_notional_krw"],
        "source_signal_id": source_signal_id,
        "owner_signal_valid": True,
        "signal_valid_until": signal_valid_until.isoformat(),
        "baseline_blocked": bool(decision.blocked),
        "baseline_confirmation_mode": owner_contract.get("baseline_confirmation_mode"),
        "market_fresh": decision.state_fresh,
        "market_phase": decision.phase,
        "guard_receipt": decision.event_fields(),
        "checkpoint": checkpoint,
        "owner_contract": owner_contract,
        "owner_runtime_policy_hash": owner_runtime_policy_hash,
        "owner_contract_sha256": digest(owner_contract),
        "legs": legs,
        "reference_price": reference_price,
        "cost_contract": cost,
        "runtime_reachability_status": "unknown_not_evaluated",
        "non_market_guards": "preceding_owner_checks_passed_downstream_guards_not_evaluated",
    }
    frame["content_sha256"] = digest(frame)
    supportive = bool(
        decision.blocked
        and decision.state_fresh
        and immediate_plan_feasible(frame)
        and rising_confirmation(frame)
    )
    policy, status = load_policy(now=now, scope=scope, root=policy_root)
    executable = (policy or {}).get("candidate", {}).get(
        "executable_confirmation"
    ) or {}
    runtime_cost_bound = bool(
        policy is not None
        and executable.get("mode") == "fresh_rebound_checkpoint0"
        and executable.get("round_trip_cost_pct") == cost["round_trip_cost_pct"]
        and executable.get("cost_trade_date") == cost["trade_date"]
        and executable.get("cost_contract_sha256") == cost["contract_sha256"]
    )
    if policy is not None and not runtime_cost_bound:
        policy = None
        status = "runtime_cost_contract_mismatch"
    should_record = bool(
        not history.get("first_recorded")
        or not decision.blocked
        or (supportive and not history.get("early_recorded"))
        or (supportive and policy is not None)
    )
    event_id = digest({"parent": history["opportunity_id"], "at": now.isoformat()})
    path = source_root / now.date().isoformat() / f"{event_id}.json"
    if should_record:
        try:
            write_json_object_generation_safe(path, frame)
        except (OSError, ValueError, TypeError) as exc:
            return {**result, "status": f"source_write_failed:{type(exc).__name__}"}
    else:
        path = Path(history["last_source_path"])
    state["rebound_reentry_observation"] = {
        **history,
        "last_observed_at": now.isoformat(),
        "closed": not decision.blocked,
        "first_recorded": True,
        "early_recorded": bool(history.get("early_recorded") or supportive),
        "last_source_path": str(path),
        "observed_poll_count": int(history.get("observed_poll_count", 0)) + 1,
    }
    result.update(
        {
            "status": status,
            "observation_path": str(path),
            "opportunity_id": history["opportunity_id"],
        }
    )
    if (
        policy is not None
        and decision.blocked
        and decision.exact_market_open_buy_cancel_allowed
        and policy["candidate"]["owner_contract_sha256"]
        == frame["owner_contract_sha256"]
        and owner_contract["baseline_confirmation_mode"] == "immediate_owner_guards"
        and runtime_cost_bound
        and supportive
    ):
        result.update(
            {
                "allow_market_exception": True,
                "status": "bounded_fresh_rebound_permit",
                "policy_hash": policy["policy_hash"],
                "observed_at": now.isoformat(),
                "expires_at": signal_valid_until.isoformat(),
                "legs_sha256": digest(legs),
                "source_signal_id": source_signal_id,
                "scope": scope,
                "cancel_guard_unchanged": True,
            }
        )
    return result


def permit_allows_initial_plan(
    *, state: dict[str, Any], decision: Any, now: datetime
) -> bool:
    """Same-batch only. Partial inventory, retries, stale permits stay blocked."""
    permit = state.get("rebound_reentry_permit") or {}
    if not isinstance(permit, dict):
        return False
    try:
        observed = datetime.fromisoformat(permit["observed_at"])
        expiry = datetime.fromisoformat(permit["expires_at"])
        legs = state.get("legs") or []
        plans = [
            {
                key: leg[key]
                for key in ("leg_id", "price_role", "entry_price", "quantity")
            }
            for leg in legs
        ]
        scope = permit.get("scope") or {}
        policy, _ = load_policy(now=now, scope=scope)
        return bool(
            permit.get("allow_market_exception") is True
            and policy is not None
            and policy["policy_hash"] == permit["policy_hash"]
            and decision.exact_market_open_buy_cancel_allowed
            and scope_identity(scope)["symbol"] == decision.symbol
            and scope_identity(scope)["listing_market"] == decision.listing_market
            and 0 <= (now - observed).total_seconds() <= 1.5
            and now <= expiry
            and legs
            and all(
                leg.get("status") == "PLANNED"
                and not leg.get("buy_order_no")
                and not leg.get("position_qty")
                for leg in legs
            )
            and digest(plans) == permit["legs_sha256"]
        )
    except (ValueError, TypeError, KeyError):
        return False


def observe_owner_terminal(*, state: dict[str, Any], now: datetime) -> bool:
    """A zero control requires an uninterrupted observed owner no-entry trace.

    There is no heartbeat daemon: the existing owner loop supplies progress.
    Restart/gaps/source failures make the zero-control proof ineligible.
    """
    history = state.get("rebound_reentry_observation") or {}
    if not isinstance(history, dict):
        return False
    if not history.get("opportunity_id") or history.get("closed"):
        return False
    try:
        last = datetime.fromisoformat(history["last_heartbeat_at"])
        scan_end = datetime.combine(
            now.date(), time.fromisoformat(history["scan_last_bar"]), tzinfo=now.tzinfo
        ) + timedelta(minutes=1)
        trace_ok = bool(
            history.get("trace_complete") is True
            and last.date() == now.date()
            and 0 <= (now - last).total_seconds() <= 30
            and state.get("status") != "BLOCKED"
            and not any(
                token in str(state.get("blocked_reason") or "").lower()
                for token in ("source", "ambiguous", "unknown")
            )
        )
        history.update(
            {"last_heartbeat_at": now.isoformat(), "trace_complete": trace_ok}
        )
        state["rebound_reentry_observation"] = history
        if now < scan_end or state.get("status") not in {"NO_TRADE", "COMPLETE"}:
            return False
        no_entry = not state.get("legs") and not state.get("attempt_consumed")
        terminal = {
            "schema": "machine_rebound_owner_terminal_v1",
            **SOURCE_AUTHORITY,
            **history["scope"],
            "opportunity_id": history["opportunity_id"],
            "trade_date": now.date().isoformat(),
            "observed_at": now.isoformat(),
            "basis_notional_krw": history["basis_notional_krw"],
            "no_entry_confirmed": bool(trace_ok and no_entry),
            "trace_complete": trace_ok,
            "owner_state": state.get("status"),
            "scan_end": scan_end.isoformat(),
        }
        terminal["content_sha256"] = digest(terminal)
        path = (
            Path(history["source_root"])
            / now.date().isoformat()
            / f"{history['opportunity_id']}_terminal.json"
        )
        write_json_object_generation_safe(path, terminal)
        history.update({"closed": True, "terminal_source_path": str(path)})
        return True
    except (OSError, ValueError, TypeError, KeyError):
        history["trace_complete"] = False
        return False
