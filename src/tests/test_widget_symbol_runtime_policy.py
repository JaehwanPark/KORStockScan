from __future__ import annotations

import json
from copy import deepcopy
from datetime import date

import pytest

from src.engine.monitoring import widget_symbol_runtime_policy as runtime
from src.engine.monitoring.widget_symbol_signal_policy_research import (
    METRIC_CONTRACT as RESEARCH_METRIC_CONTRACT,
    OWNER_CONTRACT,
    REPORT_SCHEMA,
    SYMBOLS,
)


def _summary(ev: float = 0.2, count: int = 10) -> dict:
    return {
        "episode_count": count,
        "notional_weighted_ev_pct": ev,
        "worst_episode_return_pct": -1.0,
    }


def _research() -> dict:
    selected = {
        "segment": "midday",
        "lookback_bars": 30,
        "drawdown_pct": 1.0,
        "near_low_pct": 0.5,
        "reclaim_ticks": 1,
        "target_bps": 50,
        "anchor_mode": "rolling",
        "minimum_history_bars": 15,
        "max_reclaim_chase_ticks": 2,
        "max_completed_entries_per_day": 3,
        "setup_valid_bars": 5,
        "reentry_cooldown_bars": 10,
        "force_flat_time": "15:19:00",
    }
    passed = {
        "decision": "holdout_pass_widget_signal_policy_candidate",
        "selected_policy": selected,
        "calibration": _summary(),
        "calibration_first_half": _summary(count=5),
        "calibration_second_half": _summary(count=5),
        "holdout": _summary(count=4),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    return {
        "schema": REPORT_SCHEMA,
        "status": "complete",
        "start_date": "2026-06-05",
        "end_date": "2026-08-11",
        "symbols": {
            symbol: deepcopy(
                passed
                if symbol == "006800"
                else {
                    **passed,
                    "decision": "holdout_failed_no_widget_runtime_promotion",
                }
            )
            for symbol in SYMBOLS
        },
        "source_meta": {
            symbol: {
                "symbol": symbol,
                "request_code": symbol,
                "market": "KRX_regular",
                "source_quality_status": "PASS",
            }
            for symbol in SYMBOLS
        },
        "owner_contract": OWNER_CONTRACT,
        "metric_contract": RESEARCH_METRIC_CONTRACT,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_build_policy_promotes_only_holdout_passed_symbol():
    policy = runtime.build_policy(_research())

    assert policy["effective_date"] == "2026-08-12"
    assert set(policy["symbols"]) == {"006800"}
    assert (
        policy["symbols"]["006800"]["execution_policy"]["overnight_forbidden"] is True
    )
    assert (
        policy["symbols"]["006800"]["execution_policy"]["force_exit_time"] == "15:19:00"
    )
    assert policy["symbols"]["006800"]["execution_policy"]["leg_quantity_each"] == 10
    assert (
        policy["symbols"]["006800"]["execution_policy"][
            "add_trigger_bps_from_initial_fill"
        ]
        == []
    )
    assert (
        policy["symbols"]["006800"]["execution_policy"]["source_final_exit_action"]
        == "sell_own_filled_quantity"
    )
    assert policy["official_reference"]["commit_sha"] == (
        "69642586f7d84ba9fd8a6faf1f1537c7fda6568b"
    )


def test_build_policy_preserves_calibrated_anchor_and_early_history_contract():
    research = _research()
    selected = research["symbols"]["006800"]["selected_policy"]
    selected["segment"] = "morning"
    selected["anchor_mode"] = "session"
    selected["minimum_history_bars"] = 15
    selected["max_reclaim_chase_ticks"] = 6

    policy = runtime.build_policy(research)

    signal = policy["symbols"]["006800"]["signal_policy"]
    assert signal["anchor_mode"] == "session"
    assert signal["minimum_history_bars"] == 15
    assert signal["max_reclaim_chase_ticks"] == 6


def test_v2_research_keeps_legacy_signal_shape_for_exact_policy_round_trip():
    research = _research()
    research["schema"] = "widget_symbol_signal_policy_research_v2"
    for result in research["symbols"].values():
        for key in (
            "anchor_mode",
            "minimum_history_bars",
            "max_reclaim_chase_ticks",
        ):
            result["selected_policy"].pop(key)

    policy = runtime.build_policy(research)

    signal = policy["symbols"]["006800"]["signal_policy"]
    assert "anchor_mode" not in signal
    assert "minimum_history_bars" not in signal
    assert "max_reclaim_chase_ticks" not in signal


def test_loader_requires_exact_effective_date_and_round_trip(tmp_path):
    research = _research()
    research_dir = tmp_path / "research"
    research_dir.mkdir()
    research_path = (
        research_dir / "widget_symbol_signal_policy_research_2026-08-11.json"
    )
    research_path.write_text(json.dumps(research), encoding="utf-8")
    policy_path, _, report = runtime.write_outputs(
        research,
        policy_dir=tmp_path / "policy",
        apply_report_dir=tmp_path / "report",
        evidence_report_path=research_path,
    )
    loader = runtime.WidgetSymbolRuntimePolicyLoader(
        tmp_path / "policy", research_dir=research_dir
    )

    assert report["policy_verification"]["status"] == "pass"
    assert set(loader.resolve_all(observed_date=date(2026, 8, 12))) == {"006800"}
    assert set(loader.resolve_observation_all(observed_date=date(2026, 8, 12))) == set(
        SYMBOLS
    )
    assert loader.resolve_all(observed_date=date(2026, 8, 13)) == {}
    research_path.write_text(
        json.dumps({**research, "decision": "tampered"}), encoding="utf-8"
    )
    assert loader.resolve_all(observed_date=date(2026, 8, 12)) == {}
    research_path.write_text(json.dumps(research), encoding="utf-8")
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    payload["symbols"]["006800"]["execution_policy"]["target_profit_bps"] = 999
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    assert loader.resolve_all(observed_date=date(2026, 8, 12)) == {}


def test_negative_holdout_is_never_promoted():
    research = _research()
    research["symbols"]["006800"]["holdout"]["notional_weighted_ev_pct"] = -0.01

    policy = runtime.build_policy(research)

    assert policy["status"] == "observation_only"
    assert policy["symbols"] == {}
    assert policy["runtime_effect"] is False
    assert "006800" in policy["observation_symbols"]
    assert policy["observation_runtime_effect"] is True


def test_high_daily_entry_cap_requires_positive_incremental_ev_in_every_window():
    research = _research()
    selected = research["symbols"]["006800"]["selected_policy"]
    selected["max_completed_entries_per_day"] = 4
    positive = {
        str(cap): {
            "incremental_ev_positive": True,
            "incremental": {
                "episode_count": 1,
                "notional_weighted_ev_pct": 0.1,
            },
        }
        for cap in range(1, 6)
    }
    research["symbols"]["006800"]["entry_cap_comparison"] = {
        window: deepcopy(positive)
        for window in (
            "calibration",
            "calibration_first_half",
            "calibration_second_half",
            "holdout",
        )
    }

    promoted = runtime.build_policy(research)
    assert (
        promoted["symbols"]["006800"]["execution_policy"][
            "max_completed_entries_per_day"
        ]
        == 4
    )

    research["symbols"]["006800"]["entry_cap_comparison"]["holdout"]["4"][
        "incremental_ev_positive"
    ] = False
    blocked = runtime.build_policy(research)
    assert "006800" not in blocked["symbols"]


def test_integrated_sor_research_provenance_is_rejected_for_krx_runtime():
    research = _research()
    research["source_meta"]["006800"]["request_code"] = "006800_AL"
    research["source_meta"]["006800"]["market"] = "KRX_NXT_integrated_SOR_regular"

    with pytest.raises(
        ValueError, match="widget_symbol_research_krx_source_provenance_invalid"
    ):
        runtime.build_policy(research)
