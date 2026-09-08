from copy import deepcopy

from src.engine.scalping.entry_recheck_review import (
    build_review,
    review_orders,
    intake_review_orders,
)
from src.engine.scalping.entry_recheck_policy import trading_dates
from src.tests.test_entry_recheck_policy import history, exact


def test_twenty_addressable_dates_trigger_maintenance_not_automatic_live_disable():
    dates = trading_dates("2026-09-08", "2026-06-05", 20)
    days = history(tuple(dates))
    evidence = exact(armed=0, submitted=0, completed=0, paired=0, ev=None, net=None)
    policy = {"history": days[-3:], "exact_post_apply_attribution": evidence}
    review = build_review(policy, days, dates[-1])
    row = review["scopes"][0]
    assert row["bounded_maintenance_due"] is True
    assert row["status"] == "policy_or_pid_consumption_evidence_required"
    assert row["review_options"] == ["repair", "merge_with_existing_owner", "retire"]
    assert row["economic_floor_required_for_investigation"] is False
    assert row["automatic_runtime_disable_allowed"] is False
    assert review_orders(review)[0]["runtime_effect"] is False


def test_no_natural_addressable_sample_is_not_noop_or_dead_runtime():
    days = history(ai=0, budget=0)
    review = build_review({"history": days}, days, days[-1]["source_date"])
    assert review["scopes"][0]["status"] == "no_addressable_natural_sample"
    assert review["scopes"][0]["bounded_maintenance_due"] is False
    assert review_orders(review) == []


def test_first_day_missing_hook_investigation_does_not_wait_for_economic_floor():
    days = history()
    evidence = exact(armed=0, submitted=0, completed=0, paired=0, ev=None, net=None)
    review = build_review(
        {"history": days, "exact_post_apply_attribution": evidence},
        days,
        days[-1]["source_date"],
    )
    assert review["scopes"][0]["bounded_maintenance_due"] is False
    assert (
        review_orders(review)[0]["order_id"]
        == "order_entry_recheck_bounded_maintenance_review"
    )


def test_duplicate_dates_and_invalid_sources_never_satisfy_review_bound():
    days = history()
    days[-1]["source_quality_pass"] = False
    review = build_review({"history": days}, days * 20, days[-1]["source_date"])
    assert review["scopes"][0]["review_date_count"] == 2
    assert review["scopes"][0]["bounded_maintenance_due"] is False


def test_native_intake_rejects_authority_or_evidence_mutation():
    days = history()
    review = build_review({"history": days}, days, days[-1]["source_date"])
    source = {
        "target_date": days[-1]["source_date"],
        "maintenance_review": review,
        "code_improvement_orders": review_orders(review),
    }
    assert intake_review_orders(source, source["target_date"])
    bad = deepcopy(source)
    bad["code_improvement_orders"][0]["allowed_runtime_apply"] = True
    assert intake_review_orders(bad, source["target_date"]) == []


def test_natural_maintenance_is_not_claimed_as_new_code_implementation():
    from src.engine.build_code_improvement_workorder import _classify_order

    days = history()
    review = build_review({"history": days}, days, days[-1]["source_date"])
    order = review_orders(review)[0]
    result = _classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert result.decision == "defer_evidence"
    assert result.route == "maintenance_review"
    assert result.order["producer_decision"] == "objective_followup_required"


def test_small_but_insufficient_paired_sample_is_finite_maintenance_input():
    dates = trading_dates("2026-09-08", "2026-06-05", 20)
    days = history(tuple(dates))
    evidence = exact(
        armed=10, submitted=10, completed=10, paired=1, ev=0.000001, net=0.01
    )
    review = build_review(
        {"history": days[-3:], "exact_post_apply_attribution": evidence},
        days,
        dates[-1],
    )
    assert review["scopes"][0]["first_depleted_stage"] == "exact_paired_economic_sample"
    assert review["scopes"][0]["bounded_maintenance_due"] is True


def test_source_quality_block_precedes_apparently_complete_economic_counts():
    days = history()
    review = build_review(
        {
            "history": days,
            "exact_post_apply_attribution": exact(),
            "exact_attribution_source_quality_pass": False,
        },
        days,
        days[-1]["source_date"],
    )
    assert (
        review["scopes"][0]["first_depleted_stage"]
        == "exact_attribution_source_quality"
    )
    assert review["scopes"][0]["status"] == "source_only_blocker_review_required"
