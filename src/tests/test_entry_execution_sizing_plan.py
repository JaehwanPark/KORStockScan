from src.engine.scalping.entry_execution_sizing_plan import (
    POLICY_VERSION,
    compose_entry_execution_sizing_plan,
)
from src.engine.scalping.entry_split_order_plan import build_probe_residual_orders


def _receipt(**updates):
    result = {
        "evaluation_attempt_id": "aims-test-1",
        "entry_primary_decision_owner": "mechanistic_entry_adjudicator",
        "entry_mechanistic_action": "ENTER_NOW",
        "entry_ai_screen_pass": True,
    }
    result.update(updates)
    return result


def test_atomic_plan_preserves_existing_multi_leg_shape_and_quantity():
    original = [
        {"qty": 2, "price": 1000, "entry_split_order_execution_mode": "resolver_limit"},
        {"qty": 1, "price": 995, "entry_split_order_execution_mode": "resolver_limit"},
    ]

    orders, fields = compose_entry_execution_sizing_plan(
        original,
        expected_total_qty=3,
        action_receipt=_receipt(),
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="split:test",
    )

    assert [item["qty"] for item in orders] == [2, 1]
    assert [item["price"] for item in orders] == [1000, 995]
    assert fields["entry_execution_sizing_valid"] is True
    assert fields["entry_execution_sizing_quantity_conservation_holds"] is True
    assert fields["entry_execution_sizing_policy"] == POLICY_VERSION
    assert all(item["entry_execution_sizing_plan_id"] for item in orders)
    assert fields["entry_execution_sizing_plan"]["legs"] == [
        {
            "leg_index": 1,
            "qty": 2,
            "price_candidate_id": "resolver_limit:leg1",
            "numeric_price": 1000,
            "execution_phase": "immediate",
        },
        {
            "leg_index": 2,
            "qty": 1,
            "price_candidate_id": "resolver_limit:leg2",
            "numeric_price": 995,
            "execution_phase": "immediate",
        },
    ]


def test_probe_and_frozen_residual_share_one_conserved_plan():
    continuation = {
        "requested_qty": 4,
        "residual_qty": 3,
        "residual_quantities": [2, 1],
        "common_fields": {},
    }
    orders, fields = compose_entry_execution_sizing_plan(
        [
            {
                "qty": 1,
                "price": 1000,
                "order_type_code": "3",
                "entry_split_order_execution_mode": "probe_first_market",
                "entry_split_order_probe_continuation": continuation,
            }
        ],
        expected_total_qty=4,
        action_receipt=_receipt(),
        quantity_policy_version="entry_type_5stage_cap25_v1",
        split_policy_version="split:test",
    )

    assert fields["entry_execution_sizing_valid"] is True
    assert fields["entry_execution_sizing_immediate_qty"] == 1
    assert fields["entry_execution_sizing_deferred_qty"] == 3
    assert [leg["qty"] for leg in fields["entry_execution_sizing_plan"]["legs"]] == [
        1,
        2,
        1,
    ]
    assert (
        orders[0]["entry_split_order_probe_continuation"]["common_fields"][
            "entry_execution_sizing_plan_id"
        ]
        == fields["entry_execution_sizing_plan_id"]
    )
    residual, receipt = build_probe_residual_orders(
        orders[0]["entry_split_order_probe_continuation"],
        probe_fill_price=1000,
        best_bid=995,
        best_ask=1000,
    )
    assert receipt["allowed"] is True
    assert [item["price_candidate_id"] for item in residual] == [
        "probe_residual_resolver:leg2",
        "probe_residual_resolver:leg3",
    ]
    assert all(
        item["entry_execution_sizing_plan_id"]
        == fields["entry_execution_sizing_plan_id"]
        for item in residual
    )


def test_plan_rejects_quantity_increase_or_missing_action_authority():
    _, increased = compose_entry_execution_sizing_plan(
        [{"qty": 3, "price": 1000}],
        expected_total_qty=2,
        action_receipt=_receipt(),
        quantity_policy_version=None,
        split_policy_version=None,
    )
    _, unauthorized = compose_entry_execution_sizing_plan(
        [{"qty": 1, "price": 1000}],
        expected_total_qty=1,
        action_receipt={},
        quantity_policy_version=None,
        split_policy_version=None,
    )

    assert increased["entry_execution_sizing_valid"] is False
    assert (
        "quantity_conservation_failed" in increased["entry_execution_sizing_blockers"]
    )
    assert unauthorized["entry_execution_sizing_valid"] is False
    assert (
        "action_receipt_id_missing" in unauthorized["entry_execution_sizing_blockers"]
    )
