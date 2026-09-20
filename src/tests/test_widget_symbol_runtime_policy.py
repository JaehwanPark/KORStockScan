from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

from src.engine.monitoring import widget_symbol_runtime_policy as runtime
from src.engine.monitoring import (
    widget_symbol_signal_policy_research as research_module,
)
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


def test_build_policy_promotes_integrity_bound_research_watch_symbol():
    research = _research()
    watch = "138080"
    research["symbols"][watch] = {
        **deepcopy(research["symbols"]["006800"]),
        "robust_calibration_score": 0.2,
    }
    research["source_meta"][watch] = {
        "symbol": watch,
        "request_code": watch,
        "market": "KRX_regular",
        "source_quality_status": "PASS",
    }
    research["symbol_universe"] = {**SYMBOLS, watch: "오이솔루션"}
    research["symbol_origins"] = {
        **{symbol: "established_widget_symbol" for symbol in SYMBOLS},
        watch: "operator_enrolled_research_watch",
    }

    policy = runtime.build_policy(research)

    assert set(policy["symbols"]) == {"006800", watch}
    assert watch in policy["observation_symbols"]
    assert policy["symbols"][watch]["name"] == "오이솔루션"


def test_build_policy_promotes_every_passing_research_watch_symbol_without_cap():
    research = _research()
    watches = {
        "138080": "오이솔루션",
        "214450": "파마리서치",
        "298040": "효성중공업",
        "347860": "알체라",
    }
    research["symbol_universe"] = {**SYMBOLS, **watches}
    research["symbol_origins"] = {
        **{symbol: "established_widget_symbol" for symbol in SYMBOLS},
        **{symbol: "operator_enrolled_research_watch" for symbol in watches},
    }
    for symbol in watches:
        research["symbols"][symbol] = deepcopy(research["symbols"]["006800"])
        research["source_meta"][symbol] = {
            "symbol": symbol,
            "request_code": symbol,
            "market": "KRX_regular",
            "source_quality_status": "PASS",
        }

    policy = runtime.build_policy(research)

    assert set(watches).issubset(policy["symbols"])
    assert set(watches).issubset(policy["observation_symbols"])
    assert (
        "runtime_collector_capacity_cap"
        not in policy.get("execution_quality_blocks", {}).values()
    )


def test_symbol_universe_excludes_mature_nonperformer_from_watch_and_discovery(
    monkeypatch,
):
    from src.engine.monitoring import widget_research_watch_collector as collector

    monkeypatch.setattr(
        collector,
        "load_config",
        lambda **_: {
            "symbols": [
                {
                    "stock_code": "138080",
                    "stock_name": "오이솔루션",
                    "recommendation_tier": "research_watch",
                },
                {
                    "stock_code": "214450",
                    "stock_name": "파마리서치",
                    "recommendation_tier": "research_watch",
                },
            ]
        },
    )
    monkeypatch.setattr(
        research_module,
        "widget_long_term_pruned_symbols",
        lambda *_: {"138080": "mature_calibration_and_holdout_ev_nonpositive"},
    )
    monkeypatch.setattr(
        research_module,
        "completed_daily_recommendation_symbols",
        lambda *_, **__: (
            date(2026, 9, 15),
            {"138080": "오이솔루션", "298040": "효성중공업"},
        ),
    )

    universe, origins = research_module.load_symbol_universe(
        observed_date=date(2026, 9, 16)
    )

    assert "138080" not in universe
    assert origins["214450"] == "operator_enrolled_research_watch"
    assert origins["298040"] == "completed_daily_recommendation_auto_discovery"


def test_execution_quality_handoff_is_consumed_without_disabling_observation(tmp_path):
    from src.engine.monitoring.widget_execution_quality import load_execution_incidents

    research = _research()
    research["execution_quality_by_symbol"] = {
        symbol: load_execution_incidents(
            symbol,
            target_date=date(2026, 8, 11),
            session="KRX_REGULAR",
            event_dir=tmp_path,
        )
        for symbol in SYMBOLS
    }
    policy = runtime.build_policy(research)
    assert set(policy["symbols"]) == {"006800"}
    research["execution_quality_by_symbol"]["006800"]["runtime_apply_allowed"] = False
    blocked = runtime.build_policy(research)
    assert "006800" not in blocked["symbols"]
    assert "006800" in blocked["observation_symbols"]
    assert "006800" in blocked["execution_quality_blocks"]


def test_new_source_date_requires_execution_quality_but_old_policy_shape_is_preserved():
    research = _research()
    assert "execution_quality_blocks" not in runtime.build_policy(research)
    research["end_date"] = "2026-09-09"
    policy = runtime.build_policy(research)
    assert policy["symbols"] == {}
    assert "006800" in policy["execution_quality_blocks"]


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


@pytest.mark.parametrize("tamper", [None, "authority", "missing_ledger", "count", "all_invalid"])
def test_identified_source_quarantine_excludes_failed_symbol_and_retains_valid_policy(tamper):
    report = _research()
    rejected = next(symbol for symbol in SYMBOLS if symbol != "006800")
    reason = rejected + "_source_quality_fail"
    report["source_quarantine"] = {rejected: reason}
    report["quarantined_source_symbol_count"] = 1
    report["symbols"][rejected] = dict(
        symbol=rejected, decision="source_quality_quarantined_no_evaluation",
        source_quality_reason=reason, runtime_effect=False, allowed_runtime_apply=False,
    )
    report["source_meta"][rejected] = dict(
        source_quality_status="FAIL", source_quality_reason=reason,
    )
    if tamper == "authority":
        report["symbols"][rejected]["allowed_runtime_apply"] = True
    elif tamper == "missing_ledger":
        report["source_quarantine"] = {};report["quarantined_source_symbol_count"] = 0
    elif tamper == "count":
        report["quarantined_source_symbol_count"] = True
    elif tamper == "all_invalid":
        report["source_quarantine"] = {symbol: symbol+"_source_quality_fail" for symbol in SYMBOLS}
        report["quarantined_source_symbol_count"] = len(SYMBOLS)
    if tamper is not None:
        with pytest.raises(ValueError, match="source_quarantine_invalid|krx_source_provenance_invalid"):
            runtime.build_policy(report)
        return
    policy = runtime.build_policy(report)
    assert set(policy["symbols"]) == {"006800"}
    assert rejected not in policy["observation_symbols"]
    assert policy["execution_quality_blocks"][rejected] == "source_quality_quarantined_no_evaluation"
    assert policy["symbols"]["006800"]["execution_policy"]["leg_quantity_each"] == 10


def test_research_diagnostic_seed_enrolls_without_execution_promotion():
    report = _research()
    universe = {**SYMBOLS, "999999": "research"}
    report["symbol_universe"] = universe
    report["symbol_origins"] = {
        symbol: "established_widget_symbol" for symbol in SYMBOLS
    }
    report["symbol_origins"]["999999"] = "operator_enrolled_research_watch"
    parameters = report["symbols"]["006800"]["selected_policy"]
    report["symbols"]["999999"] = {
        "decision": "no_robust_calibration_policy",
        "best_diagnostic_candidate": {"parameters": deepcopy(parameters)},
        "runtime_effect": False,
    }
    report["source_meta"]["999999"] = {
        "symbol": "999999",
        "request_code": "999999",
        "market": "KRX_regular",
        "source_quality_status": "PASS",
    }
    report["generated_at_kst"] = "2026-08-12T10:23:30+09:00"
    policy = runtime.build_policy(report)
    assert "999999" not in policy["symbols"]
    seed = policy["observation_symbols"]["999999"]
    assert seed["effective_at_kst"] == "2026-08-12T10:23:30+09:00"
    assert seed["aftermarket_effective_at_kst"] == "2026-08-12T16:03:00+09:00"
    assert seed["runtime_effect"] is False and seed["broker_order_forbidden"] is True
    assert seed["parameters_sha256"] == runtime._payload_sha256(seed["signal_policy"])
    assert seed["source_report_sha256"] == runtime._payload_sha256(report)
    legacy = runtime.build_policy(report, legacy_observation_enrollment=True)
    assert "999999" not in legacy["observation_symbols"]


def test_prior_catalog_still_loads_without_backfilling_seed_registration(tmp_path):
    report = _research()
    evidence = tmp_path / "report.json"
    evidence.write_text(json.dumps(report))
    policy = runtime.build_policy(
        report, evidence_report_path=evidence, legacy_observation_enrollment=True
    )
    path = tmp_path / f"{runtime.POLICY_PREFIX}_{policy['effective_date']}.json"
    path.write_text(json.dumps(policy))
    resolved = runtime.WidgetSymbolRuntimePolicyLoader(
        tmp_path
    ).resolve_observation_all(
        observed_date=date.fromisoformat(policy["effective_date"])
    )
    assert set(resolved) == set(policy["observation_symbols"])
    assert all(value["registered_at_kst"] is None for value in resolved.values())


def test_native_publisher_separates_observation_and_execution_catalogs(tmp_path):
    report = _research()
    report["symbol_universe"] = {**SYMBOLS, "999999": "research"}
    report["symbol_origins"] = {
        symbol: "established_widget_symbol" for symbol in SYMBOLS
    }
    report["symbol_origins"]["999999"] = "operator_enrolled_research_watch"
    report["symbols"]["999999"] = {
        "decision": "no_robust_calibration_policy",
        "runtime_effect": False,
        "best_diagnostic_candidate": {
            "parameters": deepcopy(report["symbols"]["006800"]["selected_policy"])
        },
    }
    report["source_meta"]["999999"] = {
        "symbol": "999999",
        "request_code": "999999",
        "market": "KRX_regular",
        "source_quality_status": "PASS",
    }
    evidence = tmp_path / "report.json"
    evidence.write_text(json.dumps(report))
    path, _, receipt = runtime.write_outputs(
        report,
        policy_dir=tmp_path / "policy",
        apply_report_dir=tmp_path / "apply",
        evidence_report_path=evidence,
    )
    canonical = json.loads(path.read_text())
    assert "observation_catalog_version" not in canonical
    assert canonical == runtime.build_policy(
        report, evidence_report_path=evidence, legacy_observation_enrollment=True
    )
    catalog = json.loads(Path(receipt["observation_catalog_path"]).read_text())
    assert catalog["symbols"] == {} and catalog["runtime_effect"] is False
    assert (
        catalog["allowed_runtime_apply"] is False
        and catalog["broker_order_forbidden"] is True
    )
    assert receipt["policy_verification"]["status"] == "pass"
    loader = runtime.WidgetSymbolRuntimePolicyLoader(path.parent)
    assert "999999" in loader.resolve_observation_all(
        observed_date=date.fromisoformat(canonical["effective_date"])
    )
    assert "999999" not in loader.resolve_all(
        observed_date=date.fromisoformat(canonical["effective_date"])
    )


def test_new_proxy_promotion_needs_closed_loop_contract_and_keeps_observation_lane():
    report = _research()
    report["end_date"] = "2026-09-17"
    policy = runtime.build_policy(report)
    assert "006800" not in policy["symbols"]
    assert "006800" in policy["observation_symbols"]
    assert (
        policy["execution_quality_blocks"]["006800"]
        == "closed_loop_evidence_contract_missing"
    )


def test_verified_unchanged_incumbent_carry_does_not_require_new_proxy_receipt(
    monkeypatch, tmp_path
):
    from src.engine.monitoring.widget_execution_quality import load_execution_incidents

    report = _research()
    report["end_date"] = "2026-09-17"
    incumbent = runtime._normalized_selected_parameters(
        report["symbols"]["006800"]["selected_policy"]
    )
    report["execution_quality_by_symbol"] = {
        symbol: load_execution_incidents(
            symbol,
            target_date=date(2026, 9, 17),
            session="KRX_REGULAR",
            event_dir=tmp_path,
        )
        for symbol in SYMBOLS
    }
    monkeypatch.setattr(
        runtime.WidgetSymbolRuntimePolicyLoader,
        "resolve_all",
        lambda self, observed_date: {"006800": incumbent},
    )
    policy = runtime.build_policy(report)
    assert "006800" in policy["symbols"]


def test_new_policy_generation_blocks_pending_successor_but_frozen_reader_stays_available(tmp_path):
    from src.engine.monitoring import research_closed_loop as loop
    report = _research()
    evidence = tmp_path/'widget_symbol_signal_policy_research_2026-08-11.json'
    loop.atomic_write(tmp_path/'source_waiting_2026-08-11.json', dict(
        schema='widget_signal_research_source_waiting_v1', status='waiting', end_date='2026-08-11',
        source_waiting={'006800': 'source_not_attempted'}, **loop.AUTHORITY))
    with pytest.raises(ValueError, match='source_still_waiting'):
        runtime.build_policy(report, evidence_report_path=evidence)
    policy = runtime.build_policy(report, evidence_report_path=evidence, reader_validation=True)
    assert '006800' in policy['symbols']


def test_republication_keeps_source_and_loader_uses_recorded_publication(monkeypatch, tmp_path):
    research = _research()
    research_path = tmp_path / "research.json"
    research_path.write_text(json.dumps(research))
    monkeypatch.setenv("POSTCLOSE_POLICY_PUBLICATION_DATE", "2026-08-13")
    path, _, report = runtime.write_outputs(research, policy_dir=tmp_path / "policy",
        apply_report_dir=tmp_path / "report", evidence_report_path=research_path)
    payload = json.loads(path.read_text())
    assert payload["source_target_date"] == "2026-08-11"
    assert payload["publication_date"] == "2026-08-13"
    assert payload["effective_date"] == "2026-08-14"
    monkeypatch.delenv("POSTCLOSE_POLICY_PUBLICATION_DATE")
    loader = runtime.WidgetSymbolRuntimePolicyLoader(tmp_path / "policy")
    assert set(loader.resolve_all(observed_date=date(2026, 8, 14))) == {"006800"}
    payload["publication_date"] = "invalid"
    path.write_text(json.dumps(payload))
    assert loader.resolve_all(observed_date=date(2026, 8, 14)) == {}
