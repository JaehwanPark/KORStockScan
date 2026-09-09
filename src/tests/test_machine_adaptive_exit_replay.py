from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.engine.monitoring.machine_adaptive_exit_replay import (
    build_adaptive_exit_source_census,
    replay_decisions,
)
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.tests.test_machine_adaptive_exit_decision import inputs


def test_same_pure_decision_replay_does_not_manufacture_cf_fills():
    policy, pos, snap, clock, _ = inputs()
    result = replay_decisions(policy, pos, [(clock, snap)])
    assert result["decisions"][0]["action"] == "REQUEST_EARLY_EXIT"
    assert result["counterfactual_exit_resolved"] is False
    assert result["actual_broker_terminal"] is False
    assert result["net_ev_pct"] is None


def test_replay_persists_extension_once():
    policy, pos, snap, clock, _ = inputs(support=True)
    later = replace(
        snap, observed_at_ms=190000, quote_at_ms=190000, sequence=2, supportive=False
    )
    result = replay_decisions(
        policy, pos, [(clock, snap), (replace(clock, now_ms=190000), later)]
    )
    assert [d["action"] for d in result["decisions"]] == [
        "GRANT_EXTENSION",
        "REQUEST_EARLY_EXIT",
    ]


def test_replay_never_sorts_future_or_regressed_events_into_a_valid_path():
    policy, pos, snap, clock, _ = inputs(age=20_000)
    older = replace(snap, observed_at_ms=119000, quote_at_ms=119000, sequence=0)
    result = replay_decisions(policy, pos, [(clock, snap), (clock, older)])
    assert result["status"] == "source_gap"
    assert result["net_ev_pct"] is None


def report(anchors):
    return {
        "target_date": "2026-09-09",
        "rolling_policy_source_contract": {"ready": True},
        "sources": {"source": "raw_hash"},
        "consumers": {
            "widget_postclose_tuning": {
                "symbols": {"005930": {"anchor_results": anchors}}
            },
            "episode_machine_postclose_tuning": {"profiles": {}},
        },
    }


def anchor(**kwargs):
    return {
        "owner": "widget",
        "scope_id": "p1",
        "symbol": "005930",
        "session": "KRX",
        "lifecycle_id": "ep1",
        "lifecycle_stage": "entry",
        **kwargs,
    }


def test_census_deduplicates_leg_stage_anchors_without_merging_owner_or_session():
    result = build_adaptive_exit_source_census(
        report(
            [
                anchor(),
                anchor(lifecycle_stage="exit"),
                anchor(owner="episode"),
                anchor(session="NXT"),
            ]
        )
    )
    population = result["population_contract"]
    assert population["observed_unique_lifecycles"] == 3
    assert population["source_invalid"] == 3 and population["eligible"] == 0
    assert population["conservation_valid"] is True
    assert population["all_owner_episode_census_complete"] is False
    assert result["canonical_sha256"] == canonical_sha256(result)
    assert not result["policy_promotion_candidates"]


def test_parent_hash_is_not_recursively_embedded_and_source_mutation_invalidates_child():
    parent = report([anchor()])
    first = build_adaptive_exit_source_census(parent)
    parent["rolling_policy_research_v2"] = first
    assert build_adaptive_exit_source_census(parent) == first
    parent["sources"]["source"] = "changed"
    assert (
        build_adaptive_exit_source_census(parent)["canonical_sha256"]
        != first["canonical_sha256"]
    )


@pytest.mark.parametrize(
    "anchors", [[None], [{"owner": "widget"}], [anchor(symbol=[])], [1]]
)
def test_malformed_anchor_is_not_an_empty_healthy_population(anchors):
    result = build_adaptive_exit_source_census(report(anchors))
    assert result["status"] == "blocked_source_contract"
    assert result["population_contract"]["malformed_anchor_count"] == 1


def test_unserializable_legacy_source_is_isolated_to_optional_child():
    parent = report([anchor()])
    parent["sources"]["value"] = float("nan")
    result = build_adaptive_exit_source_census(parent)
    assert result["source_binding"]["sha256"] is None
    assert "source_projection_not_finite_json" in result["contract_gaps"]
    assert result["canonical_sha256"] == canonical_sha256(result)


def test_existing_attribution_producer_and_markdown_are_connected(tmp_path):
    from src.engine.monitoring.machine_microstructure_attribution import (
        build_report,
        render_markdown,
    )

    result = build_report(
        "2026-09-09",
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        source_exclusion_manifest_path=tmp_path / "absent.json",
        canary_snapshot_path=None,
        canary_snapshot_dir=tmp_path / "canary",
        now=datetime(2026, 9, 9, 22, tzinfo=ZoneInfo("Asia/Seoul")),
    )
    child = result["rolling_policy_research_v2"]
    assert child["authority"]["runtime_effect"] is False
    assert child["runtime_automation"]["preopen_consumer_registered"] is False
    assert "Adaptive Exit Source Census" in render_markdown(result)
    assert "rolling_paired_policy_research" in result  # Legacy consumers unchanged.
