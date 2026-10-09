"""Archive-only collection metadata regressions and permanent retirement fence.

The explicit historical owner fixture never enables a runtime WS producer.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.micro_reversion.collection_targets import (
    build_collection_targets,
    load_exact_date_collection_targets,
    load_zero_base_route_gap_scopes,
    write_collection_targets,
)

KST = ZoneInfo("Asia/Seoul")


@pytest.fixture(autouse=True)
def historical_owner_fixture(request, monkeypatch):
    # Reproduce immutable historical metadata only. Current Main/WS ownership
    # is checked independently without this fixture below and in WS tests.
    if not request.node.name.startswith("test_archive_"):
        return
    from src.engine.scalping.micro_reversion import collection_targets as targets
    from src.trading.config import owner_retirement
    monkeypatch.setattr(targets, "new_entry_retired", lambda *args: False)
    monkeypatch.setattr(owner_retirement, "new_entry_retired", lambda *args: False)


def _report(gaps):
    return {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": "2026-08-14",
        "producer_consumer_gaps": gaps,
    }


def test_archive_exact_probe_conflict_augments_only_next_session_observation_route(tmp_path):
    source_date = "2026-09-30"
    source_sha = "a" * 64
    rows = [
        {"stage": "zero_base_probe_claim", "stock_code": "010140",
         "emitted_date": source_date, "emitted_at": "2026-09-30T08:38:18",
         "fields": {"zero_base_route": "nxt_only",
                    "zero_base_source_sha256": source_sha}},
        {"stage": "zero_base_probe_result", "stock_code": "010140",
         "emitted_date": source_date, "emitted_at": "2026-09-30T08:38:19",
         "fields": {"zero_base_route": "nxt_only",
                    "zero_base_source_sha256": source_sha,
                    "zero_base_probe_result": "source_unavailable",
                    "zero_base_probe_reason": "exact_route_subscription_conflict",
                    "entry_mechanistic_action": "-",
                    "actual_order_submitted": "False"}},
        {"stage": "zero_base_probe_claim", "stock_code": "034020",
         "emitted_date": source_date, "emitted_at": "2026-09-30T08:38:19",
         "fields": {"zero_base_route": "nxt_only",
                    "zero_base_source_sha256": "b" * 64}},
        {"stage": "zero_base_probe_result", "stock_code": "034020",
         "emitted_date": source_date, "emitted_at": "2026-09-30T08:38:20",
         "fields": {"zero_base_route": "nxt_only",
                    "zero_base_source_sha256": "b" * 64,
                    "zero_base_probe_result": "source_unavailable",
                    "zero_base_probe_reason": "exact_route_subscription_conflict",
                    "entry_mechanistic_action": "-",
                    "actual_order_submitted": "False"}},
    ]
    path = tmp_path / f"pipeline_events_{source_date}.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    target_root = tmp_path / "targets"
    owner_report = {"schema": "machine_microstructure_attribution_v1",
                    "target_date": "2026-09-29",
                    "producer_consumer_gaps": [{
                        "owner": "episode", "scope_id": "010140",
                        "scope_kind": "active_episode_owner", "symbol": "010140",
                        "expected_venues": ["SOR"],
                        "gap_class": "micro_symbol_not_observed",
                    }]}
    write_collection_targets(
        build_collection_targets(owner_report), root=target_root,
    )
    source = load_zero_base_route_gap_scopes(
        source_date, root=tmp_path, collection_target_root=target_root,
    )
    assert source["status"] == "complete"
    assert source["conflict_event_count"] == 2
    assert source["matched_event_count"] == 1
    assert source["scopes"][0]["source_sha256"] == source_sha

    report = {"schema": "machine_microstructure_attribution_v1",
              "target_date": source_date,
              "producer_consumer_gaps": [{
                  "owner": "episode", "scope_id": "010140",
                  "scope_kind": "active_episode_owner", "symbol": "010140",
                  "expected_venues": ["SOR"],
                  "gap_class": "micro_symbol_not_observed",
              }]}
    payload = build_collection_targets(
        report, zero_base_gap_scopes=source["scopes"], max_symbols=1,
    )
    assert payload["effective_date"] == "2026-10-01"
    assert payload["selected_targets"][0]["registration_items"] == [
        "010140_NX", "010140_AL",
    ]
    assert payload["selected_targets"][0]["trading_target_created"] is False
    assert payload["selected_targets"][0]["actual_order_submitted"] is False

    prospective = dict(report)
    prospective["producer_consumer_gaps"] = [{
        **report["producer_consumer_gaps"][0],
        "scope_kind": "prospective_episode_research",
    }]
    bounded = build_collection_targets(
        prospective, zero_base_gap_scopes=source["scopes"], max_symbols=1,
    )
    assert bounded["selected_targets"][0]["registration_items"] == [
        "010140_NX",
    ]


def test_archive_unobserved_symbols_become_bounded_next_trading_day_targets():
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "active_a",
                    "scope_kind": "active_episode_owner",
                    "symbol": "111111",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                },
                {
                    "owner": "episode",
                    "scope_id": "222222",
                    "scope_kind": "prospective_episode_research",
                    "symbol": "222222",
                    "expected_venues": ["NXT"],
                    "gap_class": "micro_symbol_not_observed",
                },
                {
                    "owner": "episode",
                    "scope_id": "333333",
                    "scope_kind": "prospective_episode_research",
                    "symbol": "333333",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                },
            ]
        ),
        max_symbols=2,
        generated_at=datetime(2026, 8, 14, 21, 15, tzinfo=KST),
    )

    assert payload["effective_date"] == "2026-08-18"
    assert payload["budget"]["selected_symbol_count"] == 3
    assert payload["budget"]["overflow_symbol_count"] == 0
    assert payload["selected_targets"][0]["symbol"] == "111111"
    assert payload["selected_targets"][0]["registration_item"] == "111111_AL"
    assert all(
        row["manual_control_exclusion_applied"] is False
        and row["market_data_subscription_effect"] is True
        and row["trading_target_created"] is False
        for row in payload["selected_targets"]
    )


def test_archive_duplicate_profile_gaps_merge_to_one_symbol_target():
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "candidate_a_morning",
                    "scope_kind": "prospective_episode_research",
                    "symbol": "444444",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                },
                {
                    "owner": "episode",
                    "scope_id": "candidate_a_midday",
                    "scope_kind": "prospective_episode_research",
                    "symbol": "444444",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_anchor_window_not_observed",
                },
            ]
        ),
        max_symbols=4,
    )

    assert payload["budget"]["selected_symbol_count"] == 1
    assert payload["selected_targets"][0]["scope_ids"] == [
        "candidate_a_midday",
        "candidate_a_morning",
    ]


def test_archive_dynamic_machine_universe_continues_bounded_policy_sample_collection():
    report = _report([])
    report["consumers"] = {"episode_machine_postclose_tuning": {"profiles": {
        "samsung": dict(symbol="005930", scope="active_episode_owner", expected_venues=["KRX"]),
        "episode_a": dict(symbol="000660", scope="prospective_episode_research", expected_venues=["SOR"]),
    }}}


    payload = build_collection_targets(report, max_symbols=2)

    assert payload["status"] == "ready"
    assert {row["symbol"] for row in payload["selected_targets"]} == {
        "005930",
        "000660",
    }


def test_archive_episode_policy_sample_uses_exact_scope_venues_not_aggregate_fallback():
    report = _report([])
    report["consumers"] = {"episode_machine_postclose_tuning": {"profiles": {
        "research:111111:KRX_REGULAR": dict(symbol="111111", scope="prospective_episode_research",
                                               expected_venues=["KRX"]),
    }}}


    payload = build_collection_targets(report, max_symbols=1)

    assert payload["selected_targets"][0]["expected_venue"] == "KRX"
    assert payload["selected_targets"][0]["registration_item"] == "111111"
    assert all(
        "micro_policy_sample_accumulation" in row["collection_reasons"]
        for row in payload["selected_targets"]
    )
    assert all(not row["gap_classes"] for row in payload["selected_targets"])


def test_archive_actual_episode_execution_gap_keeps_active_owner_collection_priority():
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "actual:005930:KRX_REGULAR",
                    "scope_kind": "active_episode_owner",
                    "symbol": "005930",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        ),
        max_symbols=1,
    )

    target = payload["selected_targets"][0]
    assert target["symbol"] == "005930"
    assert target["active_owner"] is True
    assert target["actual_execution_observed"] is False
    assert target["priority_class"] == "active_owner_collection"
    assert target["expected_venue"] == "KRX"


def test_archive_exact_date_loader_rejects_stale_or_authority_mutation(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "555555",
                    "scope_kind": "active_episode_owner",
                    "symbol": "555555",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )
    path = write_collection_targets(payload, root=tmp_path)

    loaded = load_exact_date_collection_targets("2026-08-18", root=tmp_path)
    assert loaded["status"] == "loaded"
    assert loaded["registration_items"] == ["555555"]
    assert (
        load_exact_date_collection_targets("2026-08-19", root=tmp_path)["status"]
        == "missing"
    )

    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["authority"]["trading_runtime_effect"] = True
    path.write_text(json.dumps(tampered), encoding="utf-8")
    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)
    assert rejected["status"] == "invalid_authority_or_date_contract"
    assert rejected["registration_items"] == []


def test_archive_exact_date_loader_rejects_top_level_runtime_authority_mutation(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "555555",
                    "scope_kind": "active_episode_owner",
                    "symbol": "555555",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )
    path = write_collection_targets(payload, root=tmp_path)
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["authority"]["runtime_effect"] = True
    path.write_text(json.dumps(tampered), encoding="utf-8")

    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert rejected["status"] == "invalid_authority_or_date_contract"
    assert rejected["registration_items"] == []


def test_archive_exact_date_loader_rejects_non_adjacent_source_date(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "555555",
                    "scope_kind": "active_episode_owner",
                    "symbol": "555555",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )
    payload["source_date"] = "2026-08-13"
    write_collection_targets(payload, root=tmp_path)

    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert rejected["status"] == "invalid_authority_or_date_contract"
    assert rejected["registration_items"] == []


def test_archive_malformed_symbol_is_not_silently_truncated_into_a_target():
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "malformed",
                    "scope_kind": "active_episode_owner",
                    "symbol": "A123456junk",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )

    assert payload["selected_targets"] == []
    assert payload["status"] == "no_repairable_gap"


def test_archive_non_trading_source_date_cannot_overwrite_next_session_targets():
    report = _report([])
    report["target_date"] = "2026-08-15"

    with pytest.raises(
        ValueError, match="collection_target_source_date_not_krx_trading_day"
    ):
        build_collection_targets(report)


def test_archive_loader_rejects_non_trading_source_date_even_for_next_trading_day(
    tmp_path,
):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "555555",
                    "scope_kind": "active_episode_owner",
                    "symbol": "555555",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )
    payload["source_date"] = "2026-08-15"
    payload["effective_date"] = "2026-08-18"
    write_collection_targets(payload, root=tmp_path)

    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert rejected["status"] == "invalid_authority_or_date_contract"
    assert rejected["registration_items"] == []


def test_archive_active_owner_symbols_are_not_delayed_by_research_rotation_budget():
    gaps = [
        {
            "owner": "episode",
            "scope_id": f"active_{symbol}",
            "scope_kind": "active_episode_owner",
            "symbol": symbol,
            "expected_venues": ["SOR"],
            "gap_class": "micro_symbol_not_observed",
        }
        for symbol in ("111111", "222222", "333333", "444444", "555555", "666666")
    ]
    observed = set()
    for source_date in ("2026-08-10", "2026-08-11", "2026-08-12"):
        report = _report(gaps)
        report["target_date"] = source_date
        payload = build_collection_targets(report, max_symbols=2)
        observed.update(row["symbol"] for row in payload["selected_targets"])
        assert payload["budget"]["rotation_policy"] == (
            "priority_cohort_deterministic_round_robin"
        )
        assert payload["budget"]["overflow_rotates_on_next_effective_date"] is False
        assert payload["budget"]["coverage_stage"] == (
            "exact_date_target_manifest_selection"
        )
        assert payload["budget"]["runtime_registration_receipt_required"] is True

    assert observed == {"111111", "222222", "333333", "444444", "555555", "666666"}


def test_archive_active_multi_venue_symbol_collects_all_exact_routes_each_day():
    gap = {
        "owner": "episode",
        "scope_id": "multi_venue",
        "scope_kind": "active_episode_owner",
        "symbol": "111111",
        "expected_venues": ["KRX", "NXT", "SOR"],
        "gap_class": "micro_symbol_not_observed",
    }
    for source_date in ("2026-08-10", "2026-08-11", "2026-08-12"):
        report = _report([gap])
        report["target_date"] = source_date
        payload = build_collection_targets(report, max_symbols=1)
        target = payload["selected_targets"][0]
        assert target["expected_venues"] == ["KRX", "NXT", "SOR"]
        assert target["registration_items"] == ["111111", "111111_NX", "111111_AL"]


def test_archive_active_symbol_routes_do_not_compete_for_research_rotation_budget():
    symbols = ("111111", "222222", "333333")
    gaps = [
        {
            "owner": "episode",
            "scope_id": f"active_{symbol}",
            "scope_kind": "active_episode_owner",
            "symbol": symbol,
            "expected_venues": ["KRX", "NXT", "SOR"],
            "gap_class": "micro_symbol_not_observed",
        }
        for symbol in symbols
    ]
    for source_date in (
        "2026-08-10",
        "2026-08-11",
        "2026-08-12",
        "2026-08-13",
        "2026-08-14",
        "2026-08-18",
        "2026-08-19",
        "2026-08-20",
        "2026-08-21",
    ):
        report = _report(gaps)
        report["target_date"] = source_date
        payload = build_collection_targets(report, max_symbols=1)
        for selected in payload["selected_targets"]:
            assert selected["expected_venues"] == ["KRX", "NXT", "SOR"]
            assert len(selected["registration_items"]) == 3
        assert payload["budget"]["venue_rotation_policy"] == (
            "independent_symbol_phase_after_selection_cohort_cycle"
        )


def test_archive_single_symbol_budget_keeps_active_owner_ahead_of_prospective_owner():
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "active",
                    "scope_kind": "active_episode_owner",
                    "symbol": "111111",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                },
                {
                    "owner": "episode",
                    "scope_id": "prospective",
                    "scope_kind": "prospective_episode_research",
                    "symbol": "222222",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                },
            ]
        ),
        max_symbols=1,
    )

    assert [row["symbol"] for row in payload["selected_targets"]] == ["111111", "222222"]


def test_archive_active_owner_full_coverage_precedes_prospective_rotation_budget():
    gaps = [
        {
            "owner": "episode",
            "scope_id": f"active_{symbol}",
            "scope_kind": "active_episode_owner",
            "symbol": symbol,
            "expected_venues": ["SOR"],
            "gap_class": "micro_symbol_not_observed",
        }
        for symbol in ("111111", "222222", "333333")
    ]
    gaps.append(
        {
            "owner": "episode",
            "scope_id": "prospective",
            "scope_kind": "prospective_episode_research",
            "symbol": "444444",
            "expected_venues": ["SOR"],
            "gap_class": "micro_symbol_not_observed",
        }
    )

    payload = build_collection_targets(_report(gaps), max_symbols=2)

    assert [row["symbol"] for row in payload["selected_targets"]] == [
        "111111",
        "222222",
        "333333",
        "444444",
    ]
    assert all(row["active_owner"] for row in payload["selected_targets"][:3])
    assert payload["selected_targets"][3]["active_owner"] is False
    assert payload["budget"]["prospective_reserve_applied"] == 1
    assert payload["budget"]["active_owner_candidate_count"] == 3
    assert payload["budget"]["selected_active_owner_count"] == 3
    assert payload["budget"]["active_owner_overflow_count"] == 0
    assert payload["budget"]["active_owner_exact_route_full_coverage"] is True
    assert payload["overflow_targets"] == []


def test_archive_actual_episode_execution_priority_does_not_drop_other_active_owner():
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "active_episode",
                    "scope_kind": "active_episode_owner",
                    "symbol": "111111",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                },
                {
                    "owner": "episode",
                    "scope_id": "actual_widget",
                    "scope_kind": "active_episode_owner",
                    "symbol": "222222",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                },
            ]
        ),
        max_symbols=1,
    )

    assert [row["symbol"] for row in payload["selected_targets"]] == [
        "111111",
        "222222",
    ]
    assert payload["selected_targets"][0]["actual_execution_observed"] is False


def test_archive_loader_rejects_false_active_owner_full_coverage_claim(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "active_episode",
                    "scope_kind": "active_episode_owner",
                    "symbol": "111111",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )
    payload["budget"]["selected_active_owner_count"] = 0
    write_collection_targets(payload, root=tmp_path)

    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert rejected["status"] == "invalid_budget_contract"
    assert rejected["registration_items"] == []


def test_archive_loader_rejects_active_owner_hidden_in_prospective_overflow(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "active_episode",
                    "scope_kind": "active_episode_owner",
                    "symbol": "111111",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                },
                {
                    "owner": "episode", "scope_id": "extra_research", "scope_kind": "prospective_episode_research", "symbol": "333333", "expected_venues": ["KRX"], "gap_class": "micro_symbol_not_observed",
                },
                {
                    "owner": "episode",
                    "scope_id": "prospective_widget",
                    "scope_kind": "prospective_episode_research",
                    "symbol": "222222",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                },
            ]
        ),
        max_symbols=1,
    )
    payload["overflow_targets"][0]["active_owner"] = True
    write_collection_targets(payload, root=tmp_path)

    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert rejected["status"] == "invalid_budget_contract"
    assert rejected["registration_items"] == []


@pytest.mark.parametrize("invalid_value", [None, 0, 1, "true", "false"])
def test_archive_loader_rejects_non_boolean_selected_active_owner(tmp_path, invalid_value):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "active_episode",
                    "scope_kind": "active_episode_owner",
                    "symbol": "111111",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )
    payload["selected_targets"][0]["active_owner"] = invalid_value
    write_collection_targets(payload, root=tmp_path)

    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert rejected["status"] == "invalid_budget_contract"
    assert rejected["registration_items"] == []


def test_archive_loader_rejects_overflow_count_mismatch(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "prospective_widget",
                    "scope_kind": "prospective_episode_research",
                    "symbol": "222222",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        ),
        max_symbols=1,
    )
    payload["budget"]["overflow_symbol_count"] = 1
    write_collection_targets(payload, root=tmp_path)

    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert rejected["status"] == "invalid_budget_contract"
    assert rejected["registration_items"] == []


def test_archive_loader_rejects_selected_prospective_count_above_research_budget(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "prospective_widget",
                    "scope_kind": "prospective_episode_research",
                    "symbol": "222222",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        ),
        max_symbols=1,
    )
    extra = dict(payload["selected_targets"][0])
    extra["symbol"] = "333333"
    extra["registration_item"] = "333333"
    payload["selected_targets"].append(extra)
    payload["budget"]["selected_symbol_count"] = 2
    payload["budget"]["selected_prospective_owner_count"] = 2
    payload["budget"]["max_symbols"] = 2
    write_collection_targets(payload, root=tmp_path)

    rejected = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert rejected["status"] == "invalid_budget_contract"
    assert rejected["registration_items"] == []


def test_archive_active_owner_capacity_excess_fails_instead_of_silent_overflow():
    gaps = [
        {
            "owner": "episode",
            "scope_id": f"active_{index:06d}",
            "scope_kind": "active_episode_owner",
            "symbol": f"{index:06d}",
            "expected_venues": ["SOR"],
            "gap_class": "micro_symbol_not_observed",
        }
        for index in range(1, 202)
    ]

    with pytest.raises(
        ValueError, match="active_owner_collection_target_capacity_exceeded"
    ):
        build_collection_targets(_report(gaps), max_symbols=1)


def test_archive_loader_remains_compatible_with_exact_date_v1_artifact(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "episode",
                    "scope_id": "legacy_widget",
                    "scope_kind": "active_episode_owner",
                    "symbol": "555555",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )
    payload["schema"] = "scalp_micro_reversion_collection_targets_v1"
    write_collection_targets(payload, root=tmp_path)

    loaded = load_exact_date_collection_targets("2026-08-18", root=tmp_path)

    assert loaded["status"] == "loaded"
    assert loaded["registration_items"] == ["555555"]


def test_archive_independent_prospective_budget_round_trip_and_legacy_contract(tmp_path):
    report = _report([
        {"owner": "episode", "scope_id": "active", "scope_kind": "active_episode_owner", "symbol": "111111", "expected_venues": ["SOR"], "gap_class": "micro_symbol_not_observed"},
        {"owner": "episode", "scope_id": "research", "scope_kind": "prospective_episode_research", "symbol": "222222", "expected_venues": ["KRX"], "gap_class": "micro_symbol_not_observed"},
    ])
    payload = build_collection_targets(report, max_symbols=1)
    write_collection_targets(payload, root=tmp_path)
    assert load_exact_date_collection_targets(payload["effective_date"], root=tmp_path)["status"] == "loaded"
    assert payload["budget"]["selected_prospective_owner_count"] == 1
    # Previously published shared-budget v3 artifacts still validate unchanged.
    prospective = payload["selected_targets"].pop()
    payload["overflow_targets"] = [prospective]
    budget = payload["budget"]
    budget.pop("prospective_budget_policy")
    budget.update(max_symbols=1, selected_symbol_count=1, selected_registration_item_count=1,
                  overflow_symbol_count=1, selected_prospective_owner_count=0, prospective_overflow_count=1, prospective_reserve_applied=0)
    write_collection_targets(payload, root=tmp_path)
    assert load_exact_date_collection_targets(payload["effective_date"], root=tmp_path)["status"] == "loaded"


def test_archive_prospective_budget_respects_remaining_registration_capacity(tmp_path):
    gaps = [
        {"owner": "episode", "scope_id": f"active_{index}",
         "scope_kind": "active_episode_owner", "symbol": f"{index:06d}",
         "expected_venues": ["KRX", "NXT", "SOR"],
         "gap_class": "micro_symbol_not_observed"}
        for index in range(1, 134)
    ] + [
        {"owner": "episode", "scope_id": f"research_{index}",
         "scope_kind": "prospective_episode_research", "symbol": f"{index:06d}",
         "expected_venues": ["KRX"], "gap_class": "micro_symbol_not_observed"}
        for index in (222222, 333333)
    ]
    payload = build_collection_targets(_report(gaps))
    assert payload["budget"]["selected_registration_item_count"] == 400
    assert payload["budget"]["selected_prospective_owner_count"] == 1
    assert payload["budget"]["prospective_overflow_count"] == 1
    write_collection_targets(payload, root=tmp_path)
    assert load_exact_date_collection_targets(payload["effective_date"], root=tmp_path)["status"] == "loaded"


@pytest.mark.parametrize("budget", [None, "invalid", [1], 4, True])
def test_archive_loader_rejects_non_object_budget_without_registering(tmp_path, budget):
    payload = build_collection_targets(_report([]))
    payload["budget"] = budget
    write_collection_targets(payload, root=tmp_path)
    result = load_exact_date_collection_targets(payload["effective_date"], root=tmp_path)
    assert result["status"] == "invalid_budget_contract"
    assert result["registration_items"] == []


@pytest.mark.parametrize("owner", ["episode", "widget_auto_trade"])
def test_current_retirement_excludes_old_collection_producers(owner):
    report = _report([dict(owner=owner, symbol="111111", scope_id="old",
        scope_kind="active_episode_owner", expected_venues=["SOR"],
        gap_class="micro_symbol_not_observed")])
    payload = build_collection_targets(report)
    assert payload["selected_targets"] == []
    assert payload["overflow_targets"] == []
    assert payload["authority"]["trading_runtime_effect"] is False


def test_current_reader_keeps_historical_rows_without_registering_retired_owner(tmp_path, monkeypatch):
    from src.engine.scalping.micro_reversion import collection_targets as targets
    from src.trading.config import owner_retirement
    report = _report([dict(owner="episode", symbol="111111", scope_id="old",
        scope_kind="active_episode_owner", expected_venues=["SOR"],
        gap_class="micro_symbol_not_observed")])
    with monkeypatch.context() as historical:
        historical.setattr(targets, "new_entry_retired", lambda *args: False)
        historical.setattr(owner_retirement, "new_entry_retired", lambda *args: False)
        payload = build_collection_targets(report)
    path = write_collection_targets(payload, root=tmp_path)
    original = path.read_bytes()
    result = load_exact_date_collection_targets(payload["effective_date"], root=tmp_path)
    assert result["status"] == "loaded"
    assert result["registration_items"] == []
    assert result["payload"]["selected_targets"] == payload["selected_targets"]
    assert path.read_bytes() == original
