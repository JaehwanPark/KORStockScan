"""Independent runtime and counterfactual contracts for BUY cancel wait tuning."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RUNTIME_FAMILY = "entry_cancel_wait_runtime"
POLICY_VERSION = "entry_cancel_wait_runtime_v1"
COUNTERFACTUAL_AUTHORITY = "entry_cancel_wait_counterfactual_only"
DEFAULT_THRESHOLDS = {
    "standard": 60,
    "breakout": 120,
    "pullback": 600,
    "reserve": 1200,
}
ECONOMIC_SCHEMA = "entry_cancel_wait_submitted_paired_v2"
SELECTION_RULE = "entry_cancel_wait_joint_ev_daily_lower_bound_v1"
KST = ZoneInfo("Asia/Seoul")


def bounded_candidates(profile, incumbent):
    """Freeze the values that can actually be applied, before ranking."""
    step = 30 if profile in {"standard", "breakout"} else max(1, round(incumbent * .1))
    return sorted({max(5, min(1200, incumbent + d)) for d in (-step, 0, step)})


def submission_fields(stock, order, *, seed, qty, price, route, timeout_sec, now_ts):
    from src.engine.scalping.strategy_owner_components import digest
    profile = (stock.get("entry_cancel_wait_policy_receipt") or {}).get("entry_cancel_wait_wait_profile") or resolve_profile(stock.get("position_tag"), stock.get("entry_mode"))
    context = dict(schema=ECONOMIC_SCHEMA, frozen_at=datetime.fromtimestamp(now_ts, KST).isoformat(),
        source_date=datetime.fromtimestamp(now_ts, KST).date().isoformat(),
        parent_id=(seed or {}).get("plan_sha256"), stock_code=stock.get("code"),
        child_id=str(order.get("tag") or ""), wait_profile=profile,
        requested_qty=qty, submitted_price=price, broker_route=route,
        actual_timeout_sec=timeout_sec, candidate_timeout_secs=bounded_candidates(profile, timeout_sec),
        seed=seed, policy_receipt=stock.get("entry_cancel_wait_policy_receipt") or {},
        runtime_pid=os.getpid(), observation_only=True)
    context["sha256"] = digest(context)
    return dict(entry_cancel_wait_submission_context=json.dumps(context, sort_keys=True, separators=(",", ":")),
        runtime_family=RUNTIME_FAMILY, wait_profile=profile, broker_call_attempted=True,
        actual_order_submitted=False, broker_order_forbidden=False,
        metric_role="execution_quality_real_only", decision_authority="submission_lineage_only",
        runtime_effect=False, allowed_runtime_apply=False)


def submission_response_fields(response):
    response = response if isinstance(response, dict) else {}
    number = str(response.get("ord_no") or response.get("odno") or "")
    code = str(response.get("return_code", response.get("rt_cd", "")))
    return dict(broker_order_no=number, broker_return_code=code,
        owner_registry_intent_id=str(response.get("owner_registry_intent_id") or ""),
        dispatch_disposition="accepted" if code == "0" and number else "unproven_dispatch",
        actual_order_submitted=bool(code == "0" and number))


@lru_cache(maxsize=4)
def _read_loaded_policy(path, expected_hash, size, mtime_ns):
    import hashlib
    candidate = Path(path)
    if candidate.is_symlink() or size > 64 * 1024 * 1024:
        raise ValueError("cancel_wait_policy_source_invalid")
    raw = candidate.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError("cancel_wait_policy_loaded_hash_mismatch")
    policy = json.loads(raw)
    from src.engine.scalping.strategy_owner_components import digest
    if (policy.get("schema") != ECONOMIC_SCHEMA or policy.get("runtime_family") != RUNTIME_FAMILY
        or policy.get("sha256") != digest({k:v for k,v in policy.items() if k != "sha256"})):
        raise ValueError("cancel_wait_policy_contract_invalid")
    return policy


def resolve_scoped_timeout(stock, profile, baseline, *, enabled, now_ts=None):
    """Use only the hash/date/scope bound PREOPEN policy; preserve fallback."""
    stock = stock if isinstance(stock, dict) else {}
    now = datetime.fromtimestamp(now_ts, KST) if now_ts is not None else datetime.now(KST)
    receipt = dict(entry_cancel_wait_policy_applied=False, entry_cancel_wait_timeout_sec=baseline,
                   entry_cancel_wait_runtime_pid=os.getpid(), entry_cancel_wait_wait_profile=profile,
                   entry_cancel_wait_policy_status="incumbent_preserved")
    try:
        if not enabled:
            raise ValueError("explicit_off_or_attribution_disabled")
        path = os.environ.get("KORSTOCKSCAN_ENTRY_CANCEL_WAIT_POLICY_FILE", "")
        sha = os.environ.get("KORSTOCKSCAN_ENTRY_CANCEL_WAIT_POLICY_SHA256", "")
        if not path or not sha:
            raise ValueError("dated_policy_not_loaded")
        stat = Path(path).stat()
        policy = _read_loaded_policy(path, sha, stat.st_size, stat.st_mtime_ns)
        if policy.get("effective_date") != now.date().isoformat():
            raise ValueError("dated_policy_not_effective_today")
        receipt.update(entry_cancel_wait_policy_sha256=sha, entry_cancel_wait_policy_version=policy["policy_version"],
                       entry_cancel_wait_policy_source_date=policy["source_date"])
        machine=stock.get('last_watching_ai_machine_primary_fields') or {}
        dimensions = (
            ('effective_venue', 'entry_setup_live_policy_effective_venue'),
            ('market_session_bucket', 'session_bucket', 'entry_setup_live_policy_session_bucket'),
            ('entry_execution_broker_route', 'broker_route', 'ai_trace_broker_route'),
        )
        resolved = []
        for keys in dimensions:
            values = {str(context[key]).upper() for context in (stock, machine)
                      for key in keys if context.get(key)}
            if len(values) > 1:
                raise ValueError('cancel_wait_scope_context_conflict')
            resolved.append(next(iter(values), ''))
        scope = (*resolved, profile)
        for row in policy.get("scope_overrides", []):
            if tuple(row["scope"]) == scope and row.get('base_timeout_sec',row["incumbent_timeout_sec"]) == baseline:
                value = row["timeout_sec"]
                if type(value) is not int or value not in bounded_candidates(profile, row['incumbent_timeout_sec']):
                    raise ValueError("cancel_wait_policy_step_outside_bound")
                receipt.update(entry_cancel_wait_policy_applied=True, entry_cancel_wait_timeout_sec=value,
                               entry_cancel_wait_policy_status="validated_scope_policy")
                stock["entry_cancel_wait_policy_receipt"] = receipt
                return value
    except (OSError, ValueError, TypeError, KeyError) as exc:
        receipt["entry_cancel_wait_policy_status"] = str(exc)
    if isinstance(stock, dict):
        stock["entry_cancel_wait_policy_receipt"] = receipt
    return baseline


def evaluate_economic_search(rows, model, source_counts, *, consumed_holdouts=()):
    """Freeze training choice before reading its independent policy holdout."""
    from src.engine.scalping.strategy_owner_components import digest
    result = dict(selection_rule_version=SELECTION_RULE, status="model_unvalidated", candidates=[],
        selected=None, consumed_holdouts=list(consumed_holdouts), paired_count=0,
        incumbent_ev_pct=None, candidate_ev_pct=None, delta_ev_pct=None, mean_day_delta_krw=None,
        delta_ev_lower_bound_pct=None, day_delta_lower_bound_krw=None)
    if not model.get("validated"):
        return result
    days = sorted(d for d in source_counts if d > model["available_after_date"])
    if len(days) < 2:
        return {**result, "status":"waiting_outcome", "blocker":"independent_policy_training_and_holdout_dates_missing"}
    training, holdout = days[:-1], days[-1]
    if holdout in consumed_holdouts:
        return {**result, "status":"holdout_already_consumed"}
    indexed = {}
    try:
        for row in rows:
            key = row["parent_id"]
            if key in indexed and indexed[key] != row:
                raise ValueError("conflicting_parent")
            indexed[key] = row
        rows = list(indexed.values())
        if any(sum(r["source_date"] == d for r in rows) != source_counts[d] for d in days):
            raise ValueError("complete_submitted_union_not_available_for_portfolio")
        if any(r["parent_id"] in model["actual_parent_ids"] for r in rows if r["source_date"] in days):
            raise ValueError("model_policy_parent_overlap")
        usable = [r for r in rows if r["source_date"] in days]
        for r in usable:
            affected = r['scope'] == model['scope']
            if (affected and r["fill_class"] not in model["supported_states"] or r["notional_krw"] <= 0
                or not math.isfinite(r["notional_krw"]) or r["budget_krw"] <= 0):
                raise ValueError("unsupported_state_or_capital")
            required = r['arms'].values() if affected else [r['arms'][str(r['incumbent_timeout_sec'])]]
            for a in required:
                if (a.get("status") != "completed_source_only" or not all(type(a.get(k)) in (int,float)
                    and math.isfinite(a[k]) for k in ("net_pnl_krw","stress_net_pnl_krw","capital_krw_minutes","reserve_krw_minutes"))):
                    raise ValueError("common_menu_terminal_cost_or_pending_policy_unsupported")
                state = 'no_fill' if a.get('modeled_filled_qty') == 0 else 'full' if a.get('modeled_filled_qty') == r.get('requested_qty') else 'partial'
                if affected and state not in model['supported_states']:
                    raise ValueError('candidate_state_not_validated_on_actual_model_holdout')
                if str(a["modeled_exit_at"])[:10] != r["source_date"]:
                    raise ValueError("overnight_inventory_day_cash_contract_unsupported")

        def metrics(selected_rows, scope, timeout, window):
            daily, daily_error, exposures = {d:0. for d in window}, {d:0. for d in window}, []
            daily_base, daily_candidate = {d:0. for d in window}, {d:0. for d in window}
            net = base_net = error = stress_delta = 0.
            base_capital = cap = base_reserve = reserve = 0.
            different = False
            for r in selected_rows:
                baseline = r["arms"][str(r["incumbent_timeout_sec"])]
                arm = r["arms"][str(timeout)] if tuple(r["scope"]) == scope else baseline
                delta = arm["net_pnl_krw"] - baseline["net_pnl_krw"]
                daily[r["source_date"]] += delta
                daily_base[r['source_date']] += baseline['net_pnl_krw']
                daily_candidate[r['source_date']] += arm['net_pnl_krw']
                penalty = 2 * model["net_error_pct"] * r["notional_krw"] / 100 if arm is not baseline else 0.
                error += penalty; daily_error[r["source_date"]] += penalty
                net += arm["net_pnl_krw"]; base_net += baseline["net_pnl_krw"]
                stress_delta += arm["stress_net_pnl_krw"] - baseline["stress_net_pnl_krw"]
                cap += arm["capital_krw_minutes"]; reserve += arm["reserve_krw_minutes"]
                base_capital += baseline["capital_krw_minutes"]; base_reserve += baseline["reserve_krw_minutes"]
                different |= arm.get("behavior_sha256") != baseline.get("behavior_sha256")
                # Park the same requested notional through each terminal. This
                # conservatively proves every actual submitted order fits the
                # fixed budget without inventing freed-capital reinvestments.
                for name, a in (("candidate",arm),("incumbent",baseline)):
                    exposures.append((r["submitted_at"],1,r["source_date"],name,r["notional_krw"]))
                    exposures.append((a["modeled_exit_at"],0,r["source_date"],name,-r["notional_krw"]))
            budget = min(r["budget_krw"] for r in selected_rows)
            active = {}; peak = {}
            for _,_,d,name,value in sorted(exposures):
                key=(d,name); active[key]=active.get(key,0.)+value; peak[key]=max(peak.get(key,0.),active[key])
            capital_supported = all(v <= budget+1e-8 for v in peak.values())
            notional = sum(r["notional_krw"] for r in selected_rows)
            ev, base_ev = 100*net/notional, 100*base_net/notional
            average = sum(daily.values())/len(window)
            low = (sum(daily.values())-sum(daily_error.values()))/len(window)
            ev_low = 100*(net-base_net-error)/notional
            # Risk remains the existing no-tail/no-capital-degradation contract.
            before_returns = sorted(r['arms'][str(r['incumbent_timeout_sec'])]['net_pnl_krw']/r['notional_krw'] for r in selected_rows)
            after_returns = sorted((r['arms'][str(timeout)] if tuple(r['scope']) == scope else r['arms'][str(r['incumbent_timeout_sec'])])['net_pnl_krw']/r['notional_krw'] for r in selected_rows)
            n = max(1,math.ceil(len(selected_rows)*.1))
            tails_ok = after_returns[0] >= before_returns[0] and sum(after_returns[:n]) >= sum(before_returns[:n])
            eligible = different and average>0 and ev-base_ev>0 and low>0 and ev_low>0 and stress_delta>error and tails_ok and capital_supported
            return dict(incumbent_ev_pct=base_ev,candidate_ev_pct=ev,delta_ev_pct=ev-base_ev,
                mean_day_delta_krw=average, day_delta_lower_bound_krw=low, delta_ev_lower_bound_pct=ev_low,
                paired_count=len(selected_rows), fixed_notional_krw=notional, verification_dates=window,
                daily_delta_krw=daily, daily_error_krw=daily_error, model_error_krw=error,
                daily_incumbent_net_krw=daily_base,daily_candidate_net_krw=daily_candidate,
                cumulative_delta_krw=sum(daily.values()),worst_day_delta_krw=min(daily.values()),
                incumbent_worst_return_pct=100*before_returns[0],candidate_worst_return_pct=100*after_returns[0],
                incumbent_es10_pct=100*sum(before_returns[:n])/n,candidate_es10_pct=100*sum(after_returns[:n])/n,
                stress_delta_krw=stress_delta,capital_supported=capital_supported,budget_krw=budget,
                peak_reserved_and_inventory_krw={str(k):v for k,v in peak.items()},
                capital_krw_minutes=cap,incumbent_capital_krw_minutes=base_capital,
                reserve_krw_minutes=reserve,incumbent_reserve_krw_minutes=base_reserve,
                tail_supported=tails_ok,behavior_difference=different,eligible=eligible)

        train_rows = [r for r in usable if r["source_date"] in training]
        held_rows = [r for r in usable if r["source_date"] == holdout]
        if not train_rows or not held_rows:
            return {**result,"status":"waiting_outcome","blocker":"policy_window_has_no_submitted_parent"}
        scope_menus = {}
        for r in usable:
            scope = tuple(r["scope"])
            if list(scope) != model['scope']:continue
            menu = (r["incumbent_timeout_sec"],tuple(sorted(map(int,r["arms"]))))
            if scope in scope_menus and scope_menus[scope] != menu:
                raise ValueError("incumbent_or_menu_changed_within_policy_window")
            scope_menus[scope] = menu
        for scope,(incumbent,menu) in sorted(scope_menus.items()):
            for timeout in menu:
                if timeout == incumbent:continue
                m = metrics(train_rows,scope,timeout,training)
                cid=digest([scope,incumbent,timeout])
                result["candidates"].append(dict(candidate_id=cid,scope=list(scope),timeout_sec=timeout,
                    incumbent_timeout_sec=incumbent,training=m))
        eligible=[c for c in result["candidates"] if c["training"]["eligible"]]
        eligible.sort(key=lambda c:(-round(c["training"]["day_delta_lower_bound_krw"],8),
            -round(c["training"]["delta_ev_lower_bound_pct"],8),abs(c["timeout_sec"]-c["incumbent_timeout_sec"]),c["candidate_id"]))
        if not eligible:
            state = "no_policy_difference" if result["candidates"] and not any(c["training"]["behavior_difference"] for c in result["candidates"]) else "no_edge"
            return {**result,"status":state}
        selected=eligible[0]
        held=metrics(held_rows,tuple(selected["scope"]),selected["timeout_sec"],[holdout])
        selected={**selected,"holdout":held,"holdout_date":holdout}
        result.update(selected=selected,status="economic_improvement_validated" if held["eligible"] else "holdout_rejected",
                      consumed_holdouts=sorted(set(consumed_holdouts)|{holdout}),**{k:held[k] for k in
                      ("paired_count","incumbent_ev_pct","candidate_ev_pct","delta_ev_pct","mean_day_delta_krw","delta_ev_lower_bound_pct","day_delta_lower_bound_krw")})
        return result
    except (KeyError,ValueError,TypeError,ZeroDivisionError) as exc:
        return {**result,"status":"unsupported_scope","blocker":str(exc),"selected":None}


def resolve_profile(position_tag: Any = "", entry_mode: Any = "") -> str:
    text = f"{position_tag or ''}|{entry_mode or ''}".upper()
    if "RESERVE" in text:
        return "reserve"
    if "PULLBACK" in text:
        return "pullback"
    if "BREAKOUT" in text:
        return "breakout"
    return "standard"


def candidate_thresholds(profile: str, selected_timeout_sec: int) -> list[int]:
    selected = max(
        5, min(1200, int(selected_timeout_sec or DEFAULT_THRESHOLDS[profile]))
    )
    if profile in {"standard", "breakout"}:
        step = 30
    else:
        step = max(30, int(round(selected * 0.10)))
    return sorted({max(5, selected - step), selected, min(1200, selected + step)})


def new_counterfactual_observation(
    *,
    order_no: str,
    submitted_at: float,
    cancelled_at: float,
    submitted_price: int,
    qty: int,
    profile: str,
    actual_timeout_sec: int,
    selected_timeout_sec: int,
) -> dict[str, Any]:
    return {
        "runtime_family": RUNTIME_FAMILY,
        "policy_version": POLICY_VERSION,
        "order_no": str(order_no or ""),
        "submitted_at": float(submitted_at or cancelled_at),
        "cancelled_at": float(cancelled_at),
        "submitted_price": int(submitted_price or 0),
        "qty": int(qty or 0),
        "profile": profile,
        "actual_timeout_sec": int(actual_timeout_sec or 0),
        "selected_timeout_sec": int(selected_timeout_sec or 0),
        "candidate_timeout_secs": candidate_thresholds(profile, selected_timeout_sec),
        "candidates": {},
        "completed": False,
    }


def observe_counterfactual(
    observation: dict[str, Any], *, now_ts: float, current_price: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Advance one observation without creating order or lifecycle authority."""
    state = dict(observation or {})
    candidates = dict(state.get("candidates") or {})
    events: list[dict[str, Any]] = []
    submitted_at = float(state.get("submitted_at") or now_ts)
    order_price = int(state.get("submitted_price") or 0)
    qty = int(state.get("qty") or 0)
    elapsed = max(0.0, float(now_ts) - submitted_at)
    for timeout in state.get("candidate_timeout_secs") or []:
        key = str(int(timeout))
        candidate = dict(candidates.get(key) or {})
        if not candidate.get("evaluated") and elapsed >= int(timeout):
            would_fill = bool(
                order_price > 0 and current_price > 0 and current_price <= order_price
            )
            candidate.update(
                {
                    "evaluated": True,
                    "would_fill": would_fill,
                    "fill_price": order_price if would_fill else 0,
                    "evaluated_at": float(now_ts),
                    "evaluation_price": int(current_price or 0),
                }
            )
            events.append(
                {
                    "stage": "entry_cancel_wait_counterfactual_threshold",
                    "timeout_sec": int(timeout),
                    **candidate,
                }
            )
        if candidate.get("would_fill") and not candidate.get("completed"):
            fill_at = float(candidate.get("evaluated_at") or now_ts)
            if now_ts - fill_at >= 60:
                fill_price = int(candidate.get("fill_price") or 0)
                pnl_pct = (
                    ((current_price - fill_price) / fill_price * 100.0)
                    if fill_price > 0
                    else 0.0
                )
                candidate.update(
                    {
                        "completed": True,
                        "mark_price_60s": int(current_price or 0),
                        "counterfactual_ev_pct": round(pnl_pct, 6),
                    }
                )
                events.append(
                    {
                        "stage": "entry_cancel_wait_counterfactual_completed",
                        "timeout_sec": int(timeout),
                        **candidate,
                    }
                )
        candidates[key] = candidate
    max_timeout = max(
        (int(x) for x in state.get("candidate_timeout_secs") or [0]), default=0
    )
    all_evaluated = all(
        (candidates.get(str(int(x))) or {}).get("evaluated")
        for x in state.get("candidate_timeout_secs") or []
    )
    all_fills_completed = all(
        not item.get("would_fill") or item.get("completed")
        for item in candidates.values()
    )
    state["candidates"] = candidates
    state["completed"] = bool(
        all_evaluated and all_fills_completed and elapsed >= max_timeout
    )
    return state, events
