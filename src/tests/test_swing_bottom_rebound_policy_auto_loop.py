from __future__ import annotations

from pathlib import Path

from src.engine.swing import bottom_rebound_policy_auto_loop as mod


def _research() -> dict:
    return {
        "report_type": "bottom_rebound_pattern_research",
        "date": "2026-05-26",
        "decision_authority": "research_only",
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "summary": {
            "top_primary_source_quality_adjusted_ev_pct": 1.43,
            "backtest_trade_count": 291,
        },
    }


def _research_with_candidates() -> dict:
    payload = _research()
    payload["latest_as_of_research_only_candidates"] = [
        {
            "stock_code": "005930",
            "stock_name": "Samsung",
            "backtest_rank_score": 4.2,
            "vwap_distance_pct": -1.1,
            "dist_low60_pct": 0.8,
        }
    ]
    return payload


def _ev_report_without_bottom_bucket() -> dict:
    return {
        "report_type": "swing_strategy_discovery_ev",
        "date": "2026-05-26",
        "decision_authority": "swing_sim_exploration_only",
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "aggregates": {"selection_arm": [], "volatility_bucket": []},
    }


def _candidate_source_blocked() -> dict:
    return {
        "report_type": "swing_bottom_rebound_candidate_source",
        "date": "2026-05-26",
        "decision_authority": "swing_sim_candidate_source_only",
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "source_quality": {"selected_candidate_count": 0},
    }


def test_bootstrap_research_edge_can_promote_without_downstream_candidate_deadlock(tmp_path: Path) -> None:
    report = mod.build_policy_auto_loop_report(
        "2026-05-26",
        provider="none",
        source_paths={
            "bottom_rebound_research": tmp_path / "missing-research.json",
            "candidate_source": tmp_path / "missing-candidate.json",
            "swing_strategy_discovery_ev": tmp_path / "missing-ev.json",
        },
        config=mod.PolicyAutoLoopConfig(target_date="2026-05-26"),
        ai_raw_response={
            "schema_version": 1,
            "interpretation": {
                "policy_edge_state": "candidate_policy_better",
                "evidence": ["research bootstrap"],
            },
            "audit": {
                "status": "pass",
                "explicit_gaps": [],
                "forbidden_use_violations": [],
                "runtime_authority_preserved": True,
            },
            "final_conclusion": {
                "classification_state": "sim_auto_approved",
                "promote_policy": True,
                "reason": "Research bootstrap edge is positive and source-only.",
            },
        },
    )

    assert report["final_conclusion"]["classification_state"] == "source_only_keep_collecting"
    assert "bottom_rebound_research_contract_failed" in report["final_conclusion"]["explicit_gaps"]


def test_policy_auto_loop_promotes_research_bootstrap_when_source_contracts_pass(
    tmp_path: Path, monkeypatch
) -> None:
    source_payloads = {
        "bottom_rebound_research": _research(),
        "candidate_source": _candidate_source_blocked(),
        "swing_strategy_discovery_ev": _ev_report_without_bottom_bucket(),
    }

    def fake_load(path: Path) -> dict:
        return source_payloads[path.name]

    paths = {name: Path(name) for name in source_payloads}
    monkeypatch.setattr(mod, "_load_json", fake_load)

    report = mod.build_policy_auto_loop_report(
        "2026-05-26",
        provider="none",
        source_paths=paths,
        ai_raw_response={
            "schema_version": 1,
            "interpretation": {
                "policy_edge_state": "candidate_policy_better",
                "evidence": ["absolute_improvement_pct=1.43", "sample_count=291"],
            },
            "audit": {
                "status": "pass",
                "explicit_gaps": [],
                "forbidden_use_violations": [],
                "runtime_authority_preserved": True,
            },
            "final_conclusion": {
                "classification_state": "sim_auto_approved",
                "promote_policy": True,
                "reason": "Candidate policy is source-only and passes the bootstrap edge rule.",
            },
        },
    )

    assert report["ai_tier2_review"]["status"] == "parsed"
    assert report["source_context"]["metrics"]["candidate_ev_evidence_source"] == "bottom_rebound_research_backtest_bootstrap"
    assert report["source_context"]["downstream_contracts"]["candidate_source_selected_count"] == 0
    assert report["final_conclusion"]["classification_state"] == "sim_auto_approved"
    assert report["sim_auto_approved_policy"]["policy_version"] == "bottom_rebound_swing_source_v2"
    assert report["runtime_effect"] is False
    assert report["broker_order_forbidden"] is True


def test_policy_auto_loop_generates_source_only_candidate_packet_before_review(
    tmp_path: Path, monkeypatch
) -> None:
    source_payloads = {
        "bottom_rebound_research": _research_with_candidates(),
        "candidate_source": _candidate_source_blocked(),
        "swing_strategy_discovery_ev": _ev_report_without_bottom_bucket(),
    }

    def fake_load(path: Path) -> dict:
        return source_payloads[path.name]

    paths = {name: tmp_path / name for name in source_payloads}
    monkeypatch.setattr(mod, "_load_json", fake_load)

    report = mod.build_policy_auto_loop_report(
        "2026-05-26",
        provider="openai",
        source_paths=paths,
        ai_raw_response={
            "schema_version": 1,
            "interpretation": {
                "policy_edge_state": "candidate_policy_better",
                "evidence": ["source packet generated"],
            },
            "audit": {
                "status": "pass",
                "explicit_gaps": [],
                "forbidden_use_violations": [],
                "runtime_authority_preserved": True,
            },
            "final_conclusion": {
                "classification_state": "sim_auto_approved",
                "promote_policy": True,
                "reason": "Generated source-only candidate packet is valid.",
            },
        },
    )

    assert report["candidate_source_generation"]["status"] == "generated_candidate_source_packet"
    assert report["source_context"]["downstream_contracts"]["candidate_source"] is True
    assert report["source_context"]["downstream_contracts"]["candidate_source_selected_count"] == 1
    assert report["source_context"]["metrics"]["candidate_ev_evidence_source"] == "bottom_rebound_candidate_source_packet"
    assert report["source_context"]["metrics"]["source_quality_adjusted_ev_pct"] == 1.43
    assert report["final_conclusion"]["classification_state"] == "sim_auto_approved"


def test_policy_auto_loop_normalizes_near_miss_ai_shape(tmp_path: Path, monkeypatch) -> None:
    source_payloads = {
        "bottom_rebound_research": _research(),
        "candidate_source": _candidate_source_blocked(),
        "swing_strategy_discovery_ev": _ev_report_without_bottom_bucket(),
    }
    monkeypatch.setattr(mod, "_load_json", lambda path: source_payloads[path.name])

    report = mod.build_policy_auto_loop_report(
        "2026-05-26",
        provider="openai",
        source_paths={name: Path(name) for name in source_payloads},
        ai_raw_response={
            "schema_version": "1",
            "interpretation": {
                "policy_edge_state": "candidate_policy_better",
                "evidence": [],
            },
            "audit": {
                "status": "passed",
                "explicit_gaps": [],
                "forbidden_use_violations": [],
                "runtime_authority_preserved": True,
            },
            "final_conclusions": [
                {
                    "final_classification_state": "sim_auto_approved",
                    "final_decision": "promote",
                    "reason": "Equivalent schema shape.",
                }
            ],
        },
    )

    assert report["ai_tier2_review"]["status"] == "parsed"
    assert "normalized_final_conclusions_array" in report["ai_tier2_review"]["warnings"]
    assert report["final_conclusion"]["promote_policy"] is True


def test_policy_auto_loop_does_not_treat_keep_decision_as_promotion(tmp_path: Path, monkeypatch) -> None:
    source_payloads = {
        "bottom_rebound_research": _research(),
        "candidate_source": _candidate_source_blocked(),
        "swing_strategy_discovery_ev": _ev_report_without_bottom_bucket(),
    }
    monkeypatch.setattr(mod, "_load_json", lambda path: source_payloads[path.name])

    report = mod.build_policy_auto_loop_report(
        "2026-05-26",
        provider="openai",
        source_paths={name: Path(name) for name in source_payloads},
        ai_raw_response={
            "schema_version": 1,
            "interpretation": {
                "policy_edge_state": "keep_current_policy",
                "evidence": [],
            },
            "audit": {
                "status": "pass",
                "explicit_gaps": [],
                "forbidden_use_violations": [],
                "runtime_authority_preserved": True,
            },
            "final_conclusions": [
                {
                    "final_classification_state": "source_only_keep_collecting",
                    "final_decision": "keep",
                    "reason": "Keep collecting.",
                }
            ],
        },
    )

    assert report["ai_tier2_review"]["status"] == "parsed"
    assert report["final_conclusion"]["classification_state"] == "source_only_keep_collecting"
    assert report["sim_auto_approved_policy"] is None
