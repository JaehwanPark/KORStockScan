import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.engine.scalping.micro_reversion.collection_targets import (
    build_collection_targets,
    load_exact_date_collection_targets,
    write_collection_targets,
)

KST = ZoneInfo("Asia/Seoul")


def _report(gaps):
    return {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": "2026-08-14",
        "producer_consumer_gaps": gaps,
    }


def test_unobserved_symbols_become_bounded_next_trading_day_targets():
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
                    "owner": "widget",
                    "scope_id": "222222",
                    "scope_kind": "prospective_widget_research",
                    "symbol": "222222",
                    "expected_venues": ["NXT"],
                    "gap_class": "micro_symbol_not_observed",
                },
                {
                    "owner": "widget",
                    "scope_id": "333333",
                    "scope_kind": "prospective_widget_research",
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
    assert payload["budget"]["selected_symbol_count"] == 2
    assert payload["budget"]["overflow_symbol_count"] == 1
    assert payload["selected_targets"][0]["symbol"] == "111111"
    assert payload["selected_targets"][0]["registration_item"] == "111111_AL"
    assert all(
        row["manual_control_exclusion_applied"] is False
        and row["market_data_subscription_effect"] is True
        and row["trading_target_created"] is False
        for row in payload["selected_targets"]
    )


def test_duplicate_profile_gaps_merge_to_one_symbol_target():
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


def test_dynamic_machine_universe_continues_bounded_policy_sample_collection():
    report = _report([])
    report["consumers"] = {
        "widget_postclose_tuning": {
            "symbols": {
                "005930": {
                    "symbol": "005930",
                    "scopes": ["active_widget_owner"],
                    "expected_venues": ["KRX"],
                }
            }
        },
        "episode_machine_postclose_tuning": {
            "profiles": {
                "episode_a": {
                    "symbol": "000660",
                    "scope": "prospective_episode_research",
                    "expected_venues": ["SOR"],
                }
            }
        },
    }

    payload = build_collection_targets(report, max_symbols=2)

    assert payload["status"] == "ready"
    assert {row["symbol"] for row in payload["selected_targets"]} == {
        "005930",
        "000660",
    }


def test_widget_policy_sample_uses_exact_scope_venues_not_aggregate_fallback():
    report = _report([])
    report["consumers"] = {
        "widget_postclose_tuning": {
            "symbols": {
                "111111": {
                    "symbol": "111111",
                    "scopes": ["prospective_widget_research"],
                    "expected_venues": ["KRX", "SOR"],
                    "owner_scope_ids": ["research:111111:KRX_REGULAR"],
                    "owner_scope_kinds": {
                        "research:111111:KRX_REGULAR": ("prospective_widget_research")
                    },
                    "owner_scope_expected_venues": {
                        "research:111111:KRX_REGULAR": ["KRX"]
                    },
                }
            }
        }
    }

    payload = build_collection_targets(report, max_symbols=1)

    assert payload["selected_targets"][0]["expected_venue"] == "KRX"
    assert payload["selected_targets"][0]["registration_item"] == "111111"
    assert all(
        "micro_policy_sample_accumulation" in row["collection_reasons"]
        for row in payload["selected_targets"]
    )
    assert all(not row["gap_classes"] for row in payload["selected_targets"])


def test_actual_widget_execution_gap_keeps_active_owner_collection_priority():
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "widget",
                    "scope_id": "actual:005930:KRX_REGULAR",
                    "scope_kind": "active_widget_actual_execution",
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
    assert target["actual_execution_observed"] is True
    assert target["priority_class"] == "active_owner_collection"
    assert target["expected_venue"] == "KRX"


def test_exact_date_loader_rejects_stale_or_authority_mutation(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "widget",
                    "scope_id": "555555",
                    "scope_kind": "active_widget_owner",
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


def test_exact_date_loader_rejects_top_level_runtime_authority_mutation(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "widget",
                    "scope_id": "555555",
                    "scope_kind": "active_widget_owner",
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


def test_exact_date_loader_rejects_non_adjacent_source_date(tmp_path):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "widget",
                    "scope_id": "555555",
                    "scope_kind": "active_widget_owner",
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


def test_malformed_symbol_is_not_silently_truncated_into_a_target():
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "widget",
                    "scope_id": "malformed",
                    "scope_kind": "active_widget_owner",
                    "symbol": "A123456junk",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                }
            ]
        )
    )

    assert payload["selected_targets"] == []
    assert payload["status"] == "no_repairable_gap"


def test_non_trading_source_date_cannot_overwrite_next_session_targets():
    report = _report([])
    report["target_date"] = "2026-08-15"

    with pytest.raises(
        ValueError, match="collection_target_source_date_not_krx_trading_day"
    ):
        build_collection_targets(report)


def test_loader_rejects_non_trading_source_date_even_for_next_trading_day(
    tmp_path,
):
    payload = build_collection_targets(
        _report(
            [
                {
                    "owner": "widget",
                    "scope_id": "555555",
                    "scope_kind": "active_widget_owner",
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


def test_stable_priority_cohort_round_robin_has_bounded_symbol_coverage():
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

    assert observed == {"111111", "222222", "333333", "444444", "555555", "666666"}


def test_multi_venue_symbol_rotates_routes_across_trading_days():
    gap = {
        "owner": "widget",
        "scope_id": "multi_venue",
        "scope_kind": "active_widget_owner",
        "symbol": "111111",
        "expected_venues": ["KRX", "NXT", "SOR"],
        "gap_class": "micro_symbol_not_observed",
    }
    venues = set()
    for source_date in ("2026-08-10", "2026-08-11", "2026-08-12"):
        report = _report([gap])
        report["target_date"] = source_date
        payload = build_collection_targets(report, max_symbols=1)
        venues.add(payload["selected_targets"][0]["expected_venue"])

    assert venues == {"KRX", "NXT", "SOR"}


def test_symbol_and_venue_round_robins_do_not_phase_lock():
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
    observed_venues = {symbol: set() for symbol in symbols}
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
        selected = payload["selected_targets"][0]
        observed_venues[selected["symbol"]].add(selected["expected_venue"])
        assert payload["budget"]["venue_rotation_policy"] == (
            "independent_symbol_phase_after_selection_cohort_cycle"
        )

    assert all(venues == {"KRX", "NXT", "SOR"} for venues in observed_venues.values())


def test_single_symbol_budget_keeps_active_owner_ahead_of_prospective_owner():
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
                    "owner": "widget",
                    "scope_id": "prospective",
                    "scope_kind": "prospective_widget_research",
                    "symbol": "222222",
                    "expected_venues": ["SOR"],
                    "gap_class": "micro_symbol_not_observed",
                },
            ]
        ),
        max_symbols=1,
    )

    assert [row["symbol"] for row in payload["selected_targets"]] == ["111111"]


def test_active_owner_overflow_does_not_reserve_a_prospective_slot():
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
            "owner": "widget",
            "scope_id": "prospective",
            "scope_kind": "prospective_widget_research",
            "symbol": "444444",
            "expected_venues": ["SOR"],
            "gap_class": "micro_symbol_not_observed",
        }
    )

    payload = build_collection_targets(_report(gaps), max_symbols=2)

    assert all(row["active_owner"] for row in payload["selected_targets"])
    assert payload["budget"]["prospective_reserve_applied"] == 0
    assert payload["budget"]["active_owner_overflow_count"] == 1


def test_actual_widget_execution_precedes_other_active_owner_with_tight_budget():
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
                    "owner": "widget",
                    "scope_id": "actual_widget",
                    "scope_kind": "active_widget_actual_execution",
                    "symbol": "222222",
                    "expected_venues": ["KRX"],
                    "gap_class": "micro_symbol_not_observed",
                },
            ]
        ),
        max_symbols=1,
    )

    assert [row["symbol"] for row in payload["selected_targets"]] == ["222222"]
    assert payload["selected_targets"][0]["actual_execution_observed"] is True
