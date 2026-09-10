from copy import deepcopy
from dataclasses import replace

import pytest

from src.tests.test_machine_adaptive_exit_natural_source import (
    DAY,
    SCOPE,
    FIELD,
    collect,
    leg_source,
)
from src.trading.config.machine_adaptive_exit_policy import AUTHORITY, canonical_sha256
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.adaptive_exit.target_group import (
    CancelAccounting,
    group_from_observation,
    plan_runner_release,
    reconcile_group_cancel,
)
from src.engine.monitoring.machine_adaptive_exit_study import run_study
from src.engine.monitoring.machine_adaptive_exit_source import bind_ordered_paths
from src.engine.monitoring.machine_microstructure_attribution import render_markdown


def source():
    first = leg_source()
    second = leg_source(lot="leg2")
    second["buy_order_no"] = "1111112"
    receipt = deepcopy(next(iter(first[FIELD].values())))
    extra = deepcopy(receipt["entries"][0])
    extra.update(lot_id="leg2", order_no="1111112")
    receipt["entries"].append(extra)
    receipt["target"]["quantity"] = 20
    receipt["canonical_sha256"] = canonical_sha256(receipt)
    for leg in (first, second):
        leg["target_quantity"] = 20
        leg[FIELD] = {DAY + ":2222222": deepcopy(receipt)}
    return receipt, [first, second]


def group():
    return group_from_observation(source()[0], scope=SCOPE)


def proof(**changes):
    g = group()
    return replace(
        CancelAccounting(
            group_hash=g.to_payload()["canonical_sha256"],
            target=g.target,
            cancel_order=OrderKey(DAY, "3333333"),
            requested_qty=10,
            confirmed_canceled_qty=10,
            filled_before=0,
            remaining_before=20,
            filled_after=3,
            remaining_after=7,
            cancel_terminal_reconciled=True,
            source_hash="a" * 64,
        ),
        **changes,
    )


def test_group_uses_original_lots_and_single_target_without_fill_attribution():
    g = group()
    assert g.quantity == 20 and len(g.lots) == 2
    assert g.to_payload()["authority"] == AUTHORITY
    assert g.target == OrderKey(DAY, "2222222")


@pytest.mark.parametrize(
    "kind",
    [
        "quantity",
        "duplicate_lot",
        "duplicate_buy",
        "mixed_episode",
        "mixed_date",
        "route",
        "policy",
        "authority",
        "partial_buy",
        "missing_clock",
        "future_fill",
        "prior_day_clock",
        "prior_day_ack",
    ],
)
def test_invalid_group_rejected_even_after_rehash(kind):
    receipt, _ = source()
    if kind == "quantity":
        receipt["target"]["quantity"] += 1
    elif kind == "duplicate_lot":
        receipt["entries"][1]["lot_id"] = "leg1"
    elif kind == "duplicate_buy":
        receipt["entries"][1]["order_no"] = "1111111"
    elif kind == "mixed_episode":
        receipt["entries"][1]["episode_id"] = "other"
    elif kind == "mixed_date":
        receipt["entries"][1]["order_date"] = "2026-09-08"
    elif kind == "route":
        receipt["target"]["route"] = "NXT"
    elif kind == "policy":
        receipt["entry_policy_hash"] = "b" * 64
    elif kind == "authority":
        receipt["authority"]["runtime_effect"] = 0
    elif kind == "partial_buy":
        receipt["entries"][1]["requested_quantity"] = 20
    elif kind == "missing_clock":
        receipt["entries"][1]["first_fill_observation"][
            "status"
        ] = "legacy_first_fill_unavailable"
    elif kind == "prior_day_clock":
        receipt["entries"][1]["first_fill_observation"][
            "first_observed_at"
        ] = "2026-09-08T09:00:00+09:00"
    elif kind == "prior_day_ack":
        receipt["target_ack_observed_at"] = "2026-09-08T09:00:01+09:00"
    else:
        receipt["entries"][1]["first_fill_observation"]["first_observed_at"] = (
            DAY + "T09:00:02+09:00"
        )
    receipt["canonical_sha256"] = canonical_sha256(receipt)
    with pytest.raises(ValueError):
        group_from_observation(receipt, scope=SCOPE)


@pytest.mark.parametrize("filled", range(21))
def test_runner_bounds_contain_every_possible_actual_lot_allocation(filled):
    plan = plan_runner_release(
        group(),
        runner_lot_ids=("leg2",),
        target_filled_qty=filled,
        target_remaining_qty=20 - filled,
    )
    possible = [
        10 - runner_fill for runner_fill in range(11) if 0 <= filled - runner_fill <= 10
    ]
    assert min(possible) == plan["runner_open_qty_lower_bound"]
    assert max(possible) == plan["runner_open_qty_upper_bound"]
    assert plan["cancel_quantity"] is None
    assert plan["live_partial_cancel_supported"] is False


@pytest.mark.parametrize(
    "runners", [(), ("leg1", "leg2"), ("leg1", "leg1"), ("foreign",), ["leg1"]]
)
def test_runner_subset_is_explicit_not_entire_target(runners):
    with pytest.raises(ValueError):
        plan_runner_release(
            group(),
            runner_lot_ids=runners,
            target_filled_qty=0,
            target_remaining_qty=20,
        )


def test_partial_cancel_preserves_live_target_remainder_not_false_terminal():
    result = reconcile_group_cancel(group(), proof())
    assert result["owned_open_qty"] == 17
    assert result["target_reserved_qty"] == 7
    assert result["unreserved_qty"] == 10
    assert result["actual_lot_fill_attribution"] is None
    assert result["runtime_reservation_release_allowed"] is False
    assert result["authority"] == AUTHORITY


@pytest.mark.parametrize("fill_after,canceled", [(0, 10), (3, 10), (15, 5), (20, 0)])
def test_cancel_fill_race_never_recreates_sold_quantity(fill_after, canceled):
    result = reconcile_group_cancel(
        group(),
        proof(
            filled_after=fill_after,
            confirmed_canceled_qty=canceled,
            remaining_after=20 - fill_after - canceled,
        ),
    )
    assert (
        result["owned_open_qty"]
        == result["target_reserved_qty"] + result["unreserved_qty"]
    )
    assert result["unreserved_qty"] <= 10


@pytest.mark.parametrize(
    "changes",
    [
        {"cancel_terminal_reconciled": False},
        {"cancel_terminal_reconciled": 1},
        {"requested_qty": True},
        {"confirmed_canceled_qty": 11},
        {"remaining_after": 8},
        {"remaining_after": -1},
        {"filled_before": 5, "remaining_before": 15},
        {"group_hash": "b" * 64},
        {"source_hash": "unknown"},
        {"cancel_order": OrderKey("2026-09-08", "3333333")},
        {"cancel_order": OrderKey(DAY, "2222222")},
    ],
)
def test_ack_malformed_or_mismatched_accounting_never_releases_reservation(changes):
    with pytest.raises(ValueError):
        reconcile_group_cancel(group(), proof(**changes))


def test_natural_census_deduplicates_shared_target_and_passes_diagnostic_to_study(
    tmp_path,
):
    _, legs = source()
    census, anchors = collect(tmp_path, legs)
    census = bind_ordered_paths(census, {})
    row = census["scopes"][SCOPE.key]
    groups = row["shared_target_groups"]
    assert len(groups) == 1
    assert len(row["lots"]) == 2
    assert row["complete"] and len(anchors) == 2
    assert not row["lot_paths"]  # Missing market windows remain missing.
    assert groups[DAY + ":2222222"]["status"] == "source_bound_runtime_unavailable"
    assert row["expected_episode_lots"] == {f"samsung:midday:{DAY}": ["leg1", "leg2"]}
    result = run_study(target_date=DAY, catalog=(SCOPE,), source=census, contract=None)
    summary = next(s for s in result["scopes"] if s["scope_key"] == SCOPE.key)
    assert summary["shared_target_groups"] == groups
    assert summary["shared_target_runtime_supported"] is False
    assert not result["policy_promotion_candidates"]
    markdown = render_markdown(
        {
            "target_date": DAY,
            "status": "warning",
            "decision": "observe",
            "summary": dict.fromkeys(
                (
                    "dynamic_symbol_count",
                    "widget_symbol_count",
                    "episode_profile_count",
                    "anchor_count",
                    "matched_anchor_count",
                    "producer_consumer_gap_count",
                ),
                0,
            ),
            "producer_consumer_gaps": [],
            "rolling_policy_research_v2": {
                "natural_owner_census": census,
                "all_scope_study": result,
            },
        }
    )
    assert markdown.count(DAY + ":2222222") == 1
    assert "source_bound_runtime_unavailable" in markdown
    assert "not broker partial-cancel support" in markdown


def test_group_missing_second_current_owned_lot_is_not_source_bound(tmp_path):
    _, legs = source()
    census, anchors = collect(tmp_path, legs[:1])
    record = census["scopes"][SCOPE.key]["shared_target_groups"][DAY + ":2222222"]
    assert record["status"] == "source_invalid"
    assert record["reason"] == "shared_target_current_owner_lot_mismatch"
    assert not anchors


def test_changed_current_fill_price_does_not_reuse_frozen_group(tmp_path):
    _, legs = source()
    legs[1]["fill_price"] = 10010
    census, anchors = collect(tmp_path, legs)
    record = census["scopes"][SCOPE.key]["shared_target_groups"][DAY + ":2222222"]
    assert record["status"] == "source_invalid"
    assert not record["current_target_epoch_verified"]
    assert not anchors


def test_pure_reconciliation_is_restart_deterministic_and_does_not_mutate_input():
    g, p = group(), proof()
    before = deepcopy((g, p))
    assert reconcile_group_cancel(g, p) == reconcile_group_cancel(g, p)
    assert (g, p) == before
