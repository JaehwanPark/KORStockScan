from copy import deepcopy

import pytest

from src.engine.monitoring.machine_recommendation_identity import bind_recommendation
from src.engine.monitoring.machine_recommendation_identity import (
    recommendation_inventory,
)
from src.engine.monitoring import (
    low_price_two_leg_expanded_candidate_research as episode,
    widget_collector_expansion_recommendation as expansion,
    widget_symbol_signal_policy_research as widget,
)


def bind(row, **overrides):
    options = dict(
        producer="owner",
        scope="symbol/session",
        axis="entry",
        proposal={"delay": 1},
        consumer="consumer",
        acceptance="exact receipt",
    )
    bind_recommendation(row, **(options | overrides))


def test_identity_stable_across_dates_but_proposal_separately_bound():
    first = {"target_date": "2026-09-07", "decision": "observe"}
    second = {"target_date": "2026-09-08", "decision": "defer"}
    bind(first)
    bind(second, proposal={"delay": 3})
    assert first["recommendation_id"] == second["recommendation_id"]
    assert (
        first["recommendation_proposal_sha256"]
        != second["recommendation_proposal_sha256"]
    )
    assert first["decision"] == "observe"
    assert first["recommendation_identity_grants_authority"] is False
    assert "allowed_runtime_apply" not in first


def test_inventory_includes_primary_recommendations_and_observation_rows_without_mirror_inflation():
    primary = []
    observations = {}
    for index in range(4):
        row = {"decision": "implement_after_approval", "runtime_effect": False}
        bind(row, scope=f"profile/{index}")
        primary.append(row)
    for index in range(5):
        row = {"decision": "keep_collecting", "runtime_effect": False}
        bind(row, scope=f"observe/{index}")
        observations[str(index)] = row
    report = {
        "recommendations": primary,
        "logic_lane": deepcopy(primary[:2]),
        "operator_observation_candidate_inventory": observations,
    }
    before = deepcopy(report)
    rows = recommendation_inventory(report)
    assert len(rows) == 9
    assert sum(len(r["source_locations"]) for r in rows) == 11
    assert report == before
    report["logic_lane"][0]["runtime_effect"] = True
    with pytest.raises(ValueError, match="mirror_conflict"):
        recommendation_inventory(report)


def test_inventory_rejects_missing_or_forged_native_contract():
    with pytest.raises(ValueError, match="primary_id_missing"):
        recommendation_inventory(
            {"recommendations": [{"profile_id": "missing-native"}]}
        )
    for row in ({"recommendation_id": None}, {"recommendation_id": "made_up"}):
        with pytest.raises(ValueError, match="contract_invalid"):
            recommendation_inventory({"recommendations": [row]})
    row = {}
    bind(row)
    row["recommendation_scope"]["scope"] = "different"
    with pytest.raises(ValueError, match="identity_invalid"):
        recommendation_inventory({"recommendations": [row]})


def test_sparse_first_mirror_cannot_hide_conflicting_later_authority():
    row = {}
    bind(row)
    with pytest.raises(ValueError, match="mirror_conflict"):
        recommendation_inventory(
            {
                "mirrors": [
                    row,
                    dict(row, runtime_effect=False),
                    dict(row, runtime_effect=True),
                ]
            }
        )


@pytest.mark.parametrize(
    "override", [{"scope": "other/session"}, {"axis": "exit"}, {"producer": "other"}]
)
def test_independent_owners_scopes_and_axes_have_distinct_ids(override):
    first, second = {}, {}
    bind(first)
    bind(second, **override)
    assert first["recommendation_id"] != second["recommendation_id"]


def test_conflicting_identity_and_nonfinite_proposal_fail_closed():
    row = {}
    bind(row)
    before = deepcopy(row)
    bind(row)
    assert row == before
    with pytest.raises(ValueError, match="identity_conflict"):
        bind(row, proposal={"delay": 3})
    with pytest.raises(ValueError):
        bind({}, proposal={"delay": float("nan")})


def test_producer_contracts_preserve_original_decisions_and_mirrored_ids():
    report = {
        "recommendations": [
            {
                "stock_code": "138080",
                "suggested_session": "KRX_REGULAR",
                "recommendation_tier": "research_watch",
            }
        ]
    }
    expansion.attach_recommendation_contract(report)
    assert report["recommendations"][0]["recommendation_tier"] == "research_watch"
    research = {
        "symbols": {
            "080220": {
                "decision": "holdout_pass_widget_signal_policy_candidate",
                "selected_policy": {"segment": "morning"},
            }
        }
    }
    widget.attach_recommendation_contract(research)
    assert (
        research["symbols"]["080220"]["recommendation_consumer"]
        == "widget_symbol_runtime_policy"
    )
    candidate = {
        "symbol": "137310",
        "session": "afternoon",
        "profile_id": "existing_137310_afternoon",
        "discovery_lane": "existing_symbol_time_extension",
        "recommended_spot": {"target_ticks": 2},
        "runtime_effect": False,
    }
    report = {
        "recommendations": [candidate],
        "postclose_logic_recommendations": [],
        "operator_observation_candidate_inventory": {
            "candidate_475560_morning": {"runtime_effect": False}
        },
    }
    episode.attach_recommendation_contract(report)
    assert (
        report["existing_symbol_time_extension_recommendations"][0]["recommendation_id"]
        == candidate["recommendation_id"]
    )
    assert candidate["runtime_effect"] is False
    assert candidate["recommended_spot"] == {"target_ticks": 2}
