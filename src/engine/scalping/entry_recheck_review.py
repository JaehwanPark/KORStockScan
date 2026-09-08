"""Finite source-only maintenance of recheck evidence; no policy mutation.

Missing economics never postpones investigation of a missing source or hook.
The twenty-date bound is a review deadline, not a replacement promotion floor.
"""

from __future__ import annotations

from datetime import date, timedelta
from math import isfinite

from src.utils.market_day import is_krx_trading_day

REVIEW_DATES = 20
OWNER = "EntryRecheckNaturalAttribution0907"


def _next_dates(day: str, count: int) -> list[str]:
    current = date.fromisoformat(day)
    result = []
    while len(result) < count:
        current += timedelta(days=1)
        if is_krx_trading_day(current):
            result.append(current.isoformat())
    return result


def build_review(policy: dict, days: list[dict], target_date: str) -> dict:
    # Unique exact dates only. Missing/invalid dates cannot satisfy a review floor.
    by_date = {
        d["source_date"]: d
        for d in days
        if isinstance(d.get("source_date"), str) and d["source_date"] <= target_date
    }
    days = [by_date[d] for d in sorted(by_date)][-REVIEW_DATES:]
    history = policy.get("history") or []
    transition = []
    for day in history:
        if day.get("source_quality_pass") is not True or day.get(
            "excluded_sentinel_scopes"
        ):
            transition.append(
                {
                    "source_date": day["source_date"],
                    "source_schema_version": day.get("source_schema_version"),
                    "excluded_scopes": day.get("excluded_sentinel_scopes") or [],
                    "source_validation": day.get("source_validation") or {},
                    "classification": (
                        "schema_transition_unverified"
                        if day.get("source_schema_version") != 6
                        else "source_contract_gap"
                    ),
                    "historical_reconstruction_allowed": False,
                }
            )
    scopes = sorted({r["scope"] for d in days for r in d.get("eligible_scopes", [])})
    exact = policy.get("exact_post_apply_attribution") or {}
    scope_reviews = []
    for scope in scopes:
        drought_dates = [
            d["source_date"]
            for d in days
            if d.get("source_quality_pass") is True
            and any(
                r.get("scope") == scope
                and r.get("critical") is True
                and r.get("addressable") is True
                for r in d.get("eligible_scopes", [])
            )
        ]
        funnel = (exact.get("funnel_by_scope") or {}).get(scope) or {}
        stages = (
            "exact_evaluated_count",
            "exact_armed_count",
            "exact_direct_submitted_count",
            "exact_filled_count",
            "exact_completed_count",
            "exact_paired_economic_sample",
        )
        # Unknown is different from zero; neither proves that a loaded PID was idle.
        floors = {s: (10 if s == "exact_paired_economic_sample" else 1) for s in stages}
        depleted = next(
            (
                s
                for s in stages
                if type(funnel.get(s)) not in (int, float)
                or not isfinite(funnel[s])
                or funnel[s] < floors[s]
            ),
            None,
        )
        if policy.get("exact_attribution_source_quality_pass") is False:
            depleted = "exact_attribution_source_quality"
        bounded_due = len(drought_dates) >= REVIEW_DATES and depleted is not None
        if not drought_dates:
            status = "no_addressable_natural_sample"
        elif depleted == stages[0]:
            status = "policy_or_pid_consumption_evidence_required"
        elif depleted:
            status = "source_only_blocker_review_required"
        else:
            status = "economic_acceptance_separate"
        scope_reviews.append(
            {
                "scope": scope,
                "status": status,
                "valid_addressable_source_dates": drought_dates,
                "review_date_count": len(drought_dates),
                "review_date_floor": REVIEW_DATES,
                "review_date_deficit": max(0, REVIEW_DATES - len(drought_dates)),
                "first_depleted_stage": depleted,
                "funnel": {s: funnel.get(s) for s in stages},
                "stage_floors": floors,
                "exact_attribution_source_quality_pass": policy.get(
                    "exact_attribution_source_quality_pass"
                ),
                "bounded_maintenance_due": bounded_due,
                "review_options": (
                    ["repair", "merge_with_existing_owner", "retire"]
                    if bounded_due
                    else [
                        "investigate_source_and_consumption",
                        "keep_collecting_if_finite",
                    ]
                ),
                "economic_floor_required_for_investigation": False,
                "automatic_runtime_disable_allowed": False,
                "waiting_without_new_source_evidence_allowed": (
                    False if depleted else None
                ),
            }
        )
    # This is conditional scheduling, never a prediction that ON criteria will pass.
    consecutive = 0
    for day in reversed(days[-3:]):
        if day.get("source_quality_pass") is not True:
            break
        consecutive += 1
    needed = max(0, 3 - consecutive)
    future = _next_dates(target_date, needed + 1)
    return {
        "schema_version": 1,
        "target_date": target_date,
        "acceptance_owner": OWNER,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "repair_acceptance": "source_contract_and_last_consumer_receipt",
        "economic_acceptance": "separate_exact_cost_adjusted_scope_cohort",
        "history_transition": transition,
        "source_days": days,
        "conditional_next_preopen_date": future[-1],
        "conditional_date_assumption": "each_required_next_source_date_is_valid; same_scope_drought_and_all_existing_guards_still_required",
        "scopes": scope_reviews,
    }


def review_orders(review: dict) -> list[dict]:
    findings = []
    if review.get("history_transition"):
        findings.append(("history_transition", review["history_transition"]))
    pending = [
        r
        for r in review.get("scopes", [])
        if r.get("first_depleted_stage") and r.get("valid_addressable_source_dates")
    ]
    if pending:
        findings.append(("bounded_maintenance", pending))
    return [
        {
            "order_id": f"order_entry_recheck_{kind}_review",
            "title": f"Entry recheck {kind} source and consumption review",
            "source_report_type": "entry_recheck_drought_controller",
            "target_subsystem": "runtime_instrumentation",
            "lifecycle_stage": "entry_submit",
            "route": "instrumentation_order",
            "priority": 0,
            "decision": "objective_followup_required",
            "acceptance_owner": OWNER,
            "producer_decision": "objective_followup_required",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "intent": "Investigate the first depleted stage now; do not require positive economics for diagnostic repair. Review repair/merge/retire at the declared bound, with separate authority for live changes.",
            "evidence": evidence,
            "implementation_status": "natural_acceptance_pending",
            "required_downstream": [
                "code_improvement_workorder",
                "runtime_approval_summary",
                "postclose_verifier",
                OWNER,
            ],
            "files_likely_touched": [
                "src/engine/scalping/entry_ai_gate_backtest.py",
                "src/engine/scalping/entry_recheck_review.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_entry_recheck_review.py src/tests/test_drought_handoff.py"
            ],
            "next_postclose_metric": "Exact source -> policy/PID receipt -> evaluated/armed/submit/fill/terminal/paired funnel; no indefinite waiting or automatic live mutation.",
        }
        for kind, evidence in findings
    ]


def intake_review_orders(controller: dict, target_date: str) -> list[dict]:
    """Validate producer-issued diagnostics before the common workorder intake."""
    if not controller:
        return []
    review = controller.get("maintenance_review")
    if (
        controller.get("target_date") != target_date
        or not isinstance(review, dict)
        or review.get("target_date") != target_date
        or review.get("runtime_effect") is not False
        or review.get("allowed_runtime_apply") is not False
    ):
        return []  # Final verifier rejects the missing/invalid controller contract.
    try:
        expected = review_orders(review)
    except (TypeError, KeyError, AttributeError, ValueError):
        return []
    if controller.get("code_improvement_orders") != expected:
        return []
    return expected
