"""Shared deterministic contracts for the existing entry recheck family.

This module owns report/PREOPEN decisions, not a new trading axis. It has no
I/O, broker access or mutable runtime authority.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

from src.utils.market_day import is_krx_trading_day

POLICY_VERSION = "entry_opportunity_recheck_drought_controller_v4"
ATTRIBUTION_VERSION = "entry_opportunity_recheck_exact_attempt_v3"
PROFILE_VERSION = "entry_recheck_bounded_wait_probe_v2"
EXACT_WINDOW_DAYS = 20
COOLDOWN_TRADING_DAYS = 3
SCOPES = frozenset(
    {
        "KRX|KRX_REGULAR",
        "NXT|NXT_REGULAR",
        "NXT|NXT_AFTERMARKET",
        "PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE",
    }
)
ADDRESSABLE_AXES = frozenset({"UPSTREAM_GATE", "ENTRY_AI_AUTHORITY_REVALIDATION"})
BOUNDED_PROFILE = {
    "min_ai_score": 69.0,
    "max_ai_score": 74.999,
    "max_recheck_per_symbol": 1,
    "max_daily_recheck": 10,
    "max_daily_buy_recovery": 3,
    "max_ws_age_ms": 1500,
    "forbid_danger": True,
    "require_fresh_quote": True,
    "require_explicit_buy_action": False,
    "allow_wait_probe_intent": True,
    "require_probe_first_contract": True,
}


def runtime_scope(venue: Any, session: Any) -> str:
    venue, session = str(venue or "").upper(), str(session or "").upper()
    if venue == "NXT" and session in {"KRX_REGULAR", "NXT_REGULAR_OVERLAP"}:
        session = "NXT_REGULAR"
    return f"{venue}|{session}"


def valid_previous_state(state: Any, target_date: str, baseline: str) -> bool:
    if state == {}:
        return True
    if (
        not isinstance(state, dict)
        or state.get("policy_version") != POLICY_VERSION
        or state.get("invalid")
    ):
        return False
    try:
        last = date.fromisoformat(state["last_source_date"])
        start = date.fromisoformat(state["evidence_start_date"])
        if not date.fromisoformat(baseline) <= last < date.fromisoformat(target_date):
            return False
        if not date.fromisoformat(baseline) <= start <= last + timedelta(days=1):
            return False
        if (
            state.get("stop_latched") is True
            and not date.fromisoformat(baseline)
            <= date.fromisoformat(state["stopped_at"])
            <= last
        ):
            return False
        if "scope_states" in state:
            states = state["scope_states"]
            if not isinstance(states, dict) or set(states) != set(SCOPES):
                return False
            if not all(
                isinstance(value, dict)
                and "scope_states" not in value
                and value.get("last_source_date") == state["last_source_date"]
                and valid_previous_state(value, target_date, baseline)
                and set(value.get("active_scopes") or []) <= {scope}
                for scope, value in states.items()
            ):
                return False
        return (
            isinstance(state.get("stop_latched"), bool)
            and isinstance(state.get("recovery_observed"), bool)
            and isinstance(state.get("stop_context"), dict)
            and isinstance(state.get("active_scopes"), list)
            and all(
                isinstance(scope, str) and scope in SCOPES
                for scope in state["active_scopes"]
            )
        )
    except (KeyError, ValueError, TypeError):
        return False


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def count(value: Any) -> int:
    number = finite_number(value)
    return (
        int(number)
        if number is not None and number >= 0 and number.is_integer()
        else -1
    )


def trading_dates(target: str, baseline: str, limit: int) -> list[str]:
    current, lower = date.fromisoformat(target), date.fromisoformat(baseline)
    result = []
    while current >= lower and len(result) < limit:
        if is_krx_trading_day(current):
            result.append(current.isoformat())
        current -= timedelta(days=1)
    return sorted(result)


def scope_summary(scope: str, raw: dict[str, Any]) -> dict[str, Any]:
    counts = (
        raw.get("stage_unique") if isinstance(raw.get("stage_unique"), dict) else {}
    )
    ai, budget, submitted = (
        count(counts.get(k))
        for k in ("ai_confirmed", "budget_pass", "order_bundle_submitted")
    )
    valid = (
        isinstance(scope, str) and scope in SCOPES and min(ai, budget, submitted) >= 0
    )
    ai_floor, budget_floor = valid and ai >= 20, valid and budget >= 3
    branches = []
    if ai_floor and submitted / ai < 0.20:
        branches.append("submitted_to_ai")
    if budget_floor and submitted / budget <= 0.10:
        branches.append("submitted_to_budget")
    raw_axes = raw.get("causal_bottleneck_axes")
    axes = (
        sorted({axis for axis in raw_axes if isinstance(axis, str)} & ADDRESSABLE_AXES)
        if isinstance(raw_axes, list)
        else []
    )
    exact = raw.get("exact_attempt_contract")
    if isinstance(exact, dict) and exact.get("schema_version") in {2, 3}:
        # Wider diagnostics must not widen this family's recheck authority.
        ledger = exact.get("attempt_ledger") or []
        addressable_stages = {
            "UPSTREAM_GATE": {
                "blocked_ai_score",
                "ai_score_50_buy_hold_override",
                "wait65_79_ev_candidate",
                "first_ai_wait",
            },
            "ENTRY_AI_AUTHORITY_REVALIDATION": {
                "pre_submit_entry_ai_authority_guard_block"
            },
        }
        axes = [
            axis
            for axis in axes
            if any(
                row.get("state") == "blocked"
                and row.get("terminal_axis") == axis
                and row.get("terminal_stage") in addressable_stages[axis]
                for row in ledger
                if isinstance(row, dict)
            )
        ]
    critical = bool(
        branches
        and raw.get("critical") is True
        and raw.get("primary") == "SUBMIT_DROUGHT_CRITICAL"
    )
    return {
        "scope": scope,
        **(
            {"sentinel_evidence": raw["sentinel_evidence"]}
            if "sentinel_evidence" in raw
            else {}
        ),
        "stage_unique": {
            "ai_confirmed": ai,
            "budget_pass": budget,
            "order_bundle_submitted": submitted,
        },
        "denominator_floor_passed": bool(ai_floor or budget_floor),
        "critical": critical,
        "addressable": bool(axes),
        "addressable_critical": bool(critical and axes),
        "trigger_branches": branches,
        "causal_bottleneck_axes": axes,
    }


def eligible_scopes(history: list[dict[str, Any]]) -> list[str]:
    if len(history) != 3:
        return []
    sets = [
        {
            r["scope"]
            for r in day.get("eligible_scopes", [])
            if r.get("addressable_critical") is True and r.get("scope") in SCOPES
        }
        for day in history
    ]
    return sorted(scope for scope in sets[-1] if sum(scope in s for s in sets) >= 2)


def _attempt_gaps_are_excluded(exact: dict[str, Any]) -> bool:
    """Identifiable bad attempts are excluded, not a family-wide stop."""
    keys = ("identity_conflict", "contract_gap")
    observed = {key: count(exact.get(f"{key}_count", 0)) for key in keys}
    excluded = exact.get("excluded_attempts", [])
    if not isinstance(excluded, list):
        return False
    seen = set()
    excluded_counts = dict.fromkeys(keys, 0)
    for item in excluded:
        if not isinstance(item, dict):
            return False
        attempt_id, reasons = item.get("attempt_id"), item.get("reasons")
        if (
            not isinstance(attempt_id, str)
            or not attempt_id
            or attempt_id in seen
            or not isinstance(reasons, list)
            or not reasons
            or not all(isinstance(reason, str) and reason in keys for reason in reasons)
            or len(set(reasons)) != len(reasons)
        ):
            return False
        seen.add(attempt_id)
        for reason in reasons:
            excluded_counts[reason] += 1
    return observed == excluded_counts


def _scope_controller_decision(
    *,
    history: list[dict[str, Any]],
    exact: dict[str, Any],
    previous: dict[str, Any],
    target_date: str,
    baseline: str,
    current_enabled: bool = False,
) -> dict[str, Any]:
    """Recompute flags; callers own source preflight and target-date input loading.

    A stop is sticky even after the rolling evidence ages out. A new episode
    needs either observed recovery followed by a new drought, or a different
    addressable causal scope after a three-trading-day cooldown. No cash/order
    evidence is fabricated while OFF, and elapsed time alone cannot reactivate.
    """
    expected = trading_dates(target_date, baseline, 3)
    complete = (
        len(expected) == 3 and [d.get("source_date") for d in history] == expected
    )
    quality = complete and all(d.get("source_quality_pass") is True for d in history)
    scopes = eligible_scopes(history) if quality else []
    activation = bool(scopes)
    noncritical = complete and all(
        d.get("denominator_floor_passed") and not d.get("critical") for d in history
    )
    nonaddressable = complete and all(
        d.get("denominator_floor_passed") and not d.get("addressable")
        for d in history[-2:]
    )
    context = {
        r["scope"]: r["causal_bottleneck_axes"]
        for r in (history[-1].get("eligible_scopes", []) if history else [])
        if r.get("scope") in scopes
    }
    previous_valid = valid_previous_state(previous, target_date, baseline)
    prior = dict(previous) if previous_valid else {}
    if quality and not activation and current_enabled:
        present = {
            r["scope"]
            for r in history[-1].get("eligible_scopes", [])
            if r.get("addressable")
        }
        scopes = sorted(set(prior.get("active_scopes") or []) & present & SCOPES)
    evidence_start = max(baseline, str(prior.get("evidence_start_date") or baseline))
    latched = prior.get("stop_latched") is True
    recovery_observed = bool(
        prior.get("recovery_observed") or (quality and (noncritical or nonaddressable))
    )
    stop_date = str(prior.get("stopped_at") or target_date)
    cooldown = (
        len(trading_dates(target_date, stop_date, COOLDOWN_TRADING_DAYS + 1))
        > COOLDOWN_TRADING_DAYS
    )
    context_changed = bool(context and context != prior.get("stop_context"))
    renewed = bool(
        latched and activation and cooldown and (recovery_observed or context_changed)
    )
    exact_quality = _attempt_gaps_are_excluded(exact) and all(
        count(exact.get(k, 0)) == 0
        for k in (
            "invalid_json_row_count",
            "source_quality_blocked_date_count",
        )
    )
    evaluated, armed, submitted, filled, completed, paired = (
        count(exact.get(k, 0))
        for k in (
            "exact_evaluated_count",
            "exact_armed_count",
            "exact_direct_submitted_count",
            "exact_filled_count",
            "exact_completed_count",
            "exact_paired_economic_sample",
        )
    )
    metrics_consistent = (
        0 <= paired <= completed <= filled <= submitted <= armed <= evaluated
        and count(exact.get("exact_profit_sample", 0)) == paired
        and count(exact.get("exact_net_pnl_sample", 0)) == paired
    )
    ev, net = (
        finite_number(exact.get("equal_weight_avg_profit_pct")),
        finite_number(exact.get("realized_net_pnl_krw")),
    )
    conversion_stop = armed >= 20 and submitted / armed < 0.10
    economic_stop = paired >= 10 and (ev is None or net is None or ev <= 0 or net <= 0)
    cohorts = exact.get("decision_cohorts")
    cohort_positive = True
    if isinstance(cohorts, dict):
        mature = [m for m in cohorts.values() if count(m.get("paired_sample")) >= 10]
        economic_stop = any(
            (finite_number(m.get("equal_weight_avg_profit_pct")) or 0) <= 0
            or (finite_number(m.get("realized_net_pnl_krw")) or 0) <= 0
            for m in mature
        )
        cohort_positive = bool(mature and not economic_stop)
    scoped_economics = exact.get("paired_economics_by_scope") or {}
    if not isinstance(scoped_economics, dict):
        scoped_economics = {}
        metrics_consistent = False
    scoped_pairs = 0
    scoped_net, scoped_weighted_ev = 0.0, 0.0
    for scope, metric in scoped_economics.items():
        metric = metric if isinstance(metric, dict) else {}
        n = count(metric.get("paired_sample"))
        metric_ev = finite_number(metric.get("equal_weight_avg_profit_pct"))
        metric_net = finite_number(metric.get("realized_net_pnl_krw"))
        if scope not in SCOPES or n <= 0 or metric_ev is None or metric_net is None:
            metrics_consistent = False
            continue
        scoped_pairs += n
        scoped_net += metric_net
        scoped_weighted_ev += n * metric_ev
    metrics_consistent = metrics_consistent and scoped_pairs == paired
    if paired and ev is not None and net is not None:
        metrics_consistent = bool(
            metrics_consistent
            and abs(scoped_net - net) <= 0.00011
            and abs(scoped_weighted_ev / paired - ev) <= 0.0000011
        )
    exact_quality = bool(exact_quality and metrics_consistent and previous_valid)
    scoped_escalation = sorted(
        scope
        for scope in scopes
        if exact_quality
        and cohort_positive
        and count((scoped_economics.get(scope) or {}).get("paired_sample")) >= 10
        and (
            finite_number(
                (scoped_economics.get(scope) or {}).get("equal_weight_avg_profit_pct")
            )
            or 0
        )
        > 0
        and (
            finite_number(
                (scoped_economics.get(scope) or {}).get("realized_net_pnl_krw")
            )
            or 0
        )
        > 0
    )
    reasons = []
    if not exact_quality:
        reasons.append("exact_attribution_source_quality_gap")
    if complete and not quality:
        reasons.append("drought_history_source_quality_gap")
    if noncritical:
        reasons.append("three_consecutive_noncritical_days")
    if nonaddressable:
        reasons.append("two_consecutive_nonaddressable_days")
    # A renewal begins *after* today's evidence, without reusing old economics.
    renewed = renewed and exact_quality
    if renewed:
        latched = False
        evidence_start = (
            date.fromisoformat(target_date) + timedelta(days=1)
        ).isoformat()
        recovery_observed = False
    elif exact_quality and (conversion_stop or economic_stop):
        if not latched:
            stop_date = target_date
            prior["stop_context"] = context
            recovery_observed = False
        latched = True
        reasons.extend(
            [
                reason
                for match, reason in (
                    (conversion_stop, "exact_direct_submit_conversion_below_floor"),
                    (economic_stop, "exact_cost_adjusted_economics_non_positive"),
                )
                if match
            ]
        )
    if latched:
        reasons.append("episode_stop_latched_pending_new_causal_evidence")
    return {
        "history_complete": complete,
        "latest_source_is_target_date": bool(
            history and history[-1].get("source_date") == target_date
        ),
        "expected_source_dates": expected,
        "history_source_quality_pass": quality,
        "critical_day_count": sum(bool(d.get("critical")) for d in history),
        "activation_triggered": activation,
        "stop_triggered": bool(reasons),
        "stop_reasons": reasons,
        "desired_enabled": bool(scopes and not reasons),
        "allowed_scopes": scopes if not reasons else [],
        "exact_attribution_source_quality_pass": exact_quality,
        "intraday_escalation_allowed": bool(
            activation
            and not reasons
            and not renewed
            and scoped_escalation
            and paired >= 10
            and ev is not None
            and ev > 0
            and net is not None
            and net > 0
        ),
        "intraday_escalation_scopes": (
            scoped_escalation
            if activation
            and not reasons
            and not renewed
            and paired >= 10
            and ev is not None
            and ev > 0
            and net is not None
            and net > 0
            else []
        ),
        "episode_renewed": renewed,
        "controller_state": {
            "policy_version": POLICY_VERSION,
            "evidence_start_date": evidence_start,
            "stop_latched": latched,
            "stopped_at": stop_date if latched else "",
            "stop_context": prior.get("stop_context", {}) if latched else {},
            "recovery_observed": recovery_observed if latched else False,
            "last_source_date": target_date,
            "active_scopes": scopes if not reasons else [],
            **({"invalid": True} if not previous_valid else {}),
        },
    }


FUNNEL_KEYS = (
    "exact_evaluated_count",
    "exact_armed_count",
    "exact_direct_submitted_count",
    "exact_filled_count",
    "exact_completed_count",
    "exact_paired_economic_sample",
)


def controller_decision(
    *,
    history: list[dict[str, Any]],
    exact: dict[str, Any],
    previous: dict[str, Any],
    target_date: str,
    baseline: str,
    current_enabled: bool = False,
) -> dict[str, Any]:
    """Keep operational stops/renewal local to one market/session.

    Portfolio hard-safety remains outside this family. Aggregate economics is
    diagnostic; a positive mature fill-quality cohort is required for widening.
    """
    global_result = _scope_controller_decision(
        history=history,
        exact=exact,
        previous={},
        target_date=target_date,
        baseline=baseline,
        current_enabled=current_enabled,
    )
    valid_prior = valid_previous_state(previous, target_date, baseline)
    quality = global_result["exact_attribution_source_quality_pass"] and valid_prior
    funnels = exact.get("funnel_by_scope") or {}
    cohorts = exact.get("paired_economics_by_scope_and_cohort") or {}
    economics = exact.get("paired_economics_by_scope") or {}
    if not all(isinstance(value, dict) for value in (funnels, cohorts, economics)):
        funnels, cohorts, economics = {}, {}, {}
        quality = False
    for key in FUNNEL_KEYS:
        values = [
            count(row.get(key)) if isinstance(row, dict) else -1
            for row in funnels.values()
        ]
        if any(n < 0 for n in values) or sum(values) != count(exact.get(key, 0)):
            quality = False
    for scope, row in funnels.items():
        if scope not in SCOPES and (
            not isinstance(row, dict)
            or any(count(row.get(key)) != 0 for key in FUNNEL_KEYS[1:])
        ):
            quality = False
    if set(economics) - set(funnels) or set(cohorts) - set(SCOPES):
        quality = False
    scoped_decisions = {}
    prior_states = previous.get("scope_states") if valid_prior else {}
    for scope in sorted(SCOPES):
        if isinstance(prior_states, dict):
            prior = prior_states.get(scope) or {}
        else:
            # Validated legacy global state: retain its stop conservatively,
            # but never reuse another scope's renewal context/economics.
            prior = (
                {
                    **previous,
                    "active_scopes": (
                        [scope] if scope in previous.get("active_scopes", []) else []
                    ),
                    "stop_context": (
                        {scope: previous["stop_context"][scope]}
                        if scope in previous.get("stop_context", {})
                        else {}
                    ),
                }
                if previous
                else {}
            )
        hist = []
        for day in history:
            rows = [
                r for r in day.get("eligible_scopes", []) if r.get("scope") == scope
            ]
            hist.append(
                {
                    **day,
                    "source_quality_pass": (
                        day.get("source_quality_pass") is True
                        and scope not in (day.get("excluded_sentinel_scopes") or [])
                    ),
                    "eligible_scopes": rows,
                    "denominator_floor_passed": any(
                        r.get("denominator_floor_passed") for r in rows
                    ),
                    "critical": any(r.get("critical") for r in rows),
                    "addressable": any(r.get("addressable") for r in rows),
                }
            )
        metric = economics.get(scope) or {}
        scope_cohorts = cohorts.get(scope) or {}
        scope_quality = quality and isinstance(scope_cohorts, dict)
        scope_funnel = funnels.get(scope) or {}
        if not isinstance(metric, dict) or not isinstance(scope_funnel, dict):
            metric, scope_funnel = {}, {}
            scope_quality = False
        decision_cohorts = {}
        if isinstance(scope_cohorts, dict):
            for cohort, m in scope_cohorts.items():
                if (
                    cohort
                    not in {
                        "probe_only",
                        "probe_residual_full_fill",
                        "probe_residual_partial_fill",
                        "scale_in_mixed",
                    }
                    or not isinstance(m, dict)
                    or count(m.get("paired_sample")) <= 0
                    or finite_number(m.get("equal_weight_avg_profit_pct")) is None
                    or finite_number(m.get("realized_net_pnl_krw")) is None
                    or m.get("decision_eligible") is not (cohort != "scale_in_mixed")
                ):
                    scope_quality = False
                elif cohort != "scale_in_mixed":
                    decision_cohorts[cohort] = m
        pairs = count(metric.get("paired_sample", 0))
        n = sum(count(m["paired_sample"]) for m in decision_cohorts.values())
        if n != pairs:
            scope_quality = False
        if n:
            weighted = (
                sum(
                    count(m["paired_sample"])
                    * finite_number(m["equal_weight_avg_profit_pct"])
                    for m in decision_cohorts.values()
                )
                / n
            )
            net = sum(
                finite_number(m["realized_net_pnl_krw"])
                for m in decision_cohorts.values()
            )
            if (
                abs(
                    weighted
                    - (finite_number(metric.get("equal_weight_avg_profit_pct")) or 0)
                )
                > 0.0000011
                or abs(net - (finite_number(metric.get("realized_net_pnl_krw")) or 0))
                > 0.00011
            ):
                scope_quality = False
        scope_exact = {
            **{key: scope_funnel.get(key, 0) for key in FUNNEL_KEYS},
            "contract_gap_count": 0 if scope_quality else 1,
            "exact_profit_sample": pairs,
            "exact_net_pnl_sample": pairs,
            "paired_economics_by_scope": {scope: metric} if pairs else {},
            "equal_weight_avg_profit_pct": metric.get("equal_weight_avg_profit_pct"),
            "realized_net_pnl_krw": metric.get("realized_net_pnl_krw"),
            "decision_cohorts": decision_cohorts,
        }
        scoped_decisions[scope] = _scope_controller_decision(
            history=hist,
            exact=scope_exact,
            previous=prior,
            target_date=target_date,
            baseline=baseline,
            current_enabled=current_enabled,
        )
    allowed = sorted(
        scope for scope, d in scoped_decisions.items() if d["desired_enabled"]
    )
    escalation = sorted(
        scope
        for scope in allowed
        if scoped_decisions[scope]["intraday_escalation_allowed"]
    )
    states = {scope: d["controller_state"] for scope, d in scoped_decisions.items()}
    latched = [s for s in states.values() if s["stop_latched"]]
    all_reasons = sorted(
        {reason for d in scoped_decisions.values() for reason in d["stop_reasons"]}
    )
    result = {
        **global_result,
        "desired_enabled": bool(allowed),
        "allowed_scopes": allowed,
        "activation_triggered": any(
            d["activation_triggered"] for d in scoped_decisions.values()
        ),
        "stop_triggered": bool(all_reasons and not allowed),
        "stop_reasons": all_reasons if not allowed else [],
        "exact_attribution_source_quality_pass": bool(
            quality
            and all(
                d["exact_attribution_source_quality_pass"]
                for d in scoped_decisions.values()
            )
        ),
        "intraday_escalation_allowed": bool(escalation),
        "intraday_escalation_scopes": escalation,
        "episode_renewed": any(d["episode_renewed"] for d in scoped_decisions.values()),
        "scope_decisions": scoped_decisions,
        "controller_state": {
            "policy_version": POLICY_VERSION,
            "last_source_date": target_date,
            "evidence_start_date": min(
                s["evidence_start_date"] for s in states.values()
            ),
            "active_scopes": allowed,
            "stop_latched": bool(latched),
            "stopped_at": min(s["stopped_at"] for s in latched) if latched else "",
            "stop_context": {
                key: value for s in latched for key, value in s["stop_context"].items()
            },
            "recovery_observed": any(s["recovery_observed"] for s in latched),
            "scope_states": states,
            **({"invalid": True} if not valid_prior else {}),
        },
    }
    return result
