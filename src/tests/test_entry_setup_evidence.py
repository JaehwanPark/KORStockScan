import json

import pytest

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping.entry_setup_evidence import (
    ENTRY_RISK_ADJUDICATION_SCHEMA,
    ENTRY_SETUP_EVIDENCE_SCHEMA,
    build_entry_setup_evidence,
    compose_entry_decision,
    entry_risk_adjudication_openai_schema,
    repair_invalid_entry_risk_adjudication,
    validate_entry_risk_adjudication,
)


def _exact_analysis(**fact_overrides):
    facts = {
        "structural_edge_floor": True,
        "early_session_structural_edge_floor": False,
        "early_session_probe_candidate": False,
        "orderly_pullback_recovery": False,
        "trusted_supportive_trigger": True,
        "adverse_distribution_no_edge": False,
        "blocking_overextension": False,
        "ask_wall_wide_spread": False,
        **fact_overrides,
    }
    return {
        "schema": "exact_payload_analysis_v1",
        "source_quality": {"status": "pass", "completed_bar_count": 20},
        "executable_liquidity": {"execution_cost_state": "low"},
        "contradictions": [],
        "deterministic_contract_facts": facts,
    }


def _recovery_analysis(*, clean=False, recovery=False, source_mode="fresh_dual"):
    return {
        "schema": "anticipatory_reversal_analysis_v1",
        "source_mode": source_mode,
        "hard_blockers": [],
        "clean_continuation_probe": {"eligible": clean},
        "recovery_confirmation_probe": {"eligible": recovery},
    }


def _risk(verdict, codes, *, support=None, contradict=None, confidence=70):
    return {
        "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
        "risk_verdict": verdict,
        "risk_codes": codes,
        "supporting_fact_ids": support or [],
        "contradicting_fact_ids": contradict or [],
        "confidence": confidence,
    }


def test_risk_schema_has_unique_required_fields_and_no_action_authority():
    schema = entry_risk_adjudication_openai_schema()

    assert schema["additionalProperties"] is False
    assert len(schema["required"]) == len(set(schema["required"]))
    assert "action" not in schema["properties"]
    assert "score" not in schema["properties"]
    assert "price" not in schema["properties"]
    assert schema["properties"]["supporting_fact_ids"]["maxItems"] == 8
    assert "enum" not in schema["properties"]["supporting_fact_ids"]["items"]
    assert schema["properties"]["contradicting_fact_ids"]["maxItems"] == 8
    assert "enum" not in schema["properties"]["contradicting_fact_ids"]["items"]


def test_risk_schema_constrains_fact_ids_to_the_exact_setup_ledger():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            **_exact_analysis(trusted_supportive_trigger=False),
            "contradictions": ["multi_horizon_direction_conflict"],
        },
        recovery_analysis=_recovery_analysis(clean=True),
    )

    schema = entry_risk_adjudication_openai_schema(evidence)

    assert schema["properties"]["supporting_fact_ids"]["items"]["enum"] == (
        evidence["positive_facts"]
    )
    assert schema["properties"]["contradicting_fact_ids"]["items"]["enum"] == [
        *evidence["contradicting_facts"],
        *evidence["invalidation_facts"],
    ]


def test_risk_schema_forces_empty_fact_arrays_when_ledger_has_no_matching_facts():
    schema = entry_risk_adjudication_openai_schema(
        {
            "positive_facts": [],
            "contradicting_facts": [],
            "invalidation_facts": [],
        }
    )

    assert schema["properties"]["supporting_fact_ids"]["maxItems"] == 0
    assert schema["properties"]["contradicting_fact_ids"]["maxItems"] == 0


def test_invalid_risk_schema_requires_an_exact_invalidation_fact():
    schema = entry_risk_adjudication_openai_schema(
        {
            "setup_state": "INVALID",
            "positive_facts": ["liquidity_supportive"],
            "contradicting_facts": ["trigger_confirmation_missing"],
            "invalidation_facts": ["no_supported_setup"],
        }
    )

    contradicting = schema["properties"]["contradicting_fact_ids"]
    assert contradicting["minItems"] == 1
    assert contradicting["items"]["enum"] == ["no_supported_setup"]


def test_wait_risk_schema_requires_a_ledger_backed_adverse_fact():
    schema = entry_risk_adjudication_openai_schema(
        {
            "setup_state": "WAIT_CONFIRMATION",
            "positive_facts": ["liquidity_supportive"],
            "contradicting_facts": ["trigger_confirmation_missing"],
            "invalidation_facts": [],
        }
    )

    contradicting = schema["properties"]["contradicting_fact_ids"]
    assert contradicting["minItems"] == 1
    assert contradicting["items"]["enum"] == ["trigger_confirmation_missing"]


def test_offline_candidate_schema_enforces_exact_fact_roles_per_request():
    setup = {
        "positive_facts": ["liquidity_supportive"],
        "contradicting_facts": ["program_flow_net_and_delta_sell"],
        "invalidation_facts": ["no_supported_setup"],
    }

    schema = quality._candidate_openai_schema(
        stage="entry",
        candidate={
            "semantic_validator_version": (
                quality.ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
            )
        },
        setup_evidence=setup,
    )

    assert schema["properties"]["supporting_fact_ids"]["items"]["enum"] == [
        "liquidity_supportive"
    ]
    assert schema["properties"]["contradicting_fact_ids"]["items"]["enum"] == [
        "program_flow_net_and_delta_sell",
        "no_supported_setup",
    ]


def test_response_schema_instance_hash_does_not_split_prompt_contract():
    base = {
        "prompt_version": "decision_quality_v2_15_bounded_recovery_entry",
        "system_prompt_sha256": "prompt-hash",
        "response_schema_sha256": "template-hash",
        "response_schema_instance_policy": "exact_fact_role_enum_v1",
    }

    first = quality._candidate_contract_sha256(
        {**base, "response_schema_instance_sha256": "fact-ledger-a"}
    )
    second = quality._candidate_contract_sha256(
        {**base, "response_schema_instance_sha256": "fact-ledger-b"}
    )

    assert first == second


def test_setup_evidence_is_symbol_agnostic_and_ready_for_clean_continuation():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}, "symbol": "005930"},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )

    assert evidence["schema"] == ENTRY_SETUP_EVIDENCE_SCHEMA
    assert evidence["version"] == "entry_setup_evidence_policy_v9"
    assert evidence["setup_family"] == "CLEAN_CONTINUATION"
    assert evidence["setup_state"] == "READY"
    assert evidence["structure_phase"] == "continuation"
    assert evidence["structure_phase_policy_version"] == (
        "entry_completed_bar_structure_phase_v2"
    )
    assert evidence["structure_phase_stable_on_completed_bar"] is True
    assert evidence["execution_readiness_state"] == "READY"
    assert evidence["symbol_specific_branching"] is False
    assert evidence["widget_dependency"] is False
    assert evidence["runtime_effect"] is False
    assert evidence["observation_contract"]["runtime_effect"] is False
    assert evidence["observation_contract"]["broker_order_forbidden"] is True
    assert evidence["context_observations"]["market_relative"]["status"] == (
        "unavailable"
    )
    assert (
        evidence["context_observations"]["external_market"]["usable_for_risk"] is False
    )


def test_context_inputs_are_null_aware_bounded_risk_only():
    exact_payload = {
        "current": {"price": 10000},
        "entry_candle_context": {
            "multi_timeframe_context": {
                "market_context": {
                    "source": "fixture_market",
                    "source_quality": {"status": "pass"},
                    "return_5m_pct": 0.3,
                    "return_15m_pct": 0.5,
                },
                "sector_context": {
                    "source": "fixture_sector",
                    "source_quality": {"status": "pass"},
                    "stock_return_5m_pct": -0.4,
                    "stock_return_15m_pct": -0.3,
                    "sector_relative_return_5m_pct": -0.8,
                    "sector_relative_return_15m_pct": -0.7,
                },
            }
        },
        "ai_market_snapshot_v1": {
            "sources": {
                "program": {
                    "quality": "fresh",
                    "source": "ws_0w",
                    "observed_at": "2026-08-07T09:00:00+09:00",
                    "value": {"net_qty": -100, "delta_qty": -20},
                },
                "investor": {
                    "quality": "fresh",
                    "source": "fixture_investor",
                    "observed_at": "2026-08-07T09:00:00+09:00",
                    "value": {"foreign_net": 0, "inst_net": 0},
                },
            }
        },
        "external_market_context": {
            "quality": "fresh",
            "source": "fixture_external",
            "observed_at": "2026-08-07T09:00:00+09:00",
            "risk_state": "RISK_OFF",
        },
    }
    evidence = build_entry_setup_evidence(
        exact_payload=exact_payload,
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )

    assert evidence["setup_state"] == "READY"
    assert (
        evidence["context_observations"]["market_relative"]["usable_for_risk"] is True
    )
    assert evidence["context_observations"]["investor_flow"]["status"] == (
        "observed_zero_or_not_yet_reported"
    )
    assert evidence["context_observations"]["investor_flow"]["usable_for_risk"] is False
    assert {
        "market_relative_weak_5m_15m",
        "sector_relative_weak_5m_15m",
        "program_flow_net_and_delta_sell",
        "external_market_risk_off",
    }.issubset(set(evidence["contradicting_facts"]))
    assert evidence["corroborated_risk_codes"] == ["ADVERSE_TAPE"]
    assert evidence["invalidation_facts"] == []

    composed = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=_risk(
            "VETO",
            ["ADVERSE_TAPE"],
            contradict=["market_relative_weak_5m_15m"],
        ),
    )
    assert composed["action"] == "WAIT"
    assert composed["entry_probe_intent"] is True
    assert composed["entry_ai_bounded_risk_codes"] == ["ADVERSE_TAPE"]
    assert composed["entry_setup_market_relative_status"] == "observed"
    assert composed["entry_setup_program_flow_usable_for_risk"] is True
    assert composed["entry_setup_investor_flow_status"] == (
        "observed_zero_or_not_yet_reported"
    )
    assert composed["entry_setup_external_market_usable_for_risk"] is True


def test_context_flow_and_external_fresh_labels_require_observation_time():
    evidence = build_entry_setup_evidence(
        exact_payload={
            "current": {"price": 10000},
            "ai_market_snapshot_v1": {
                "sources": {
                    "program": {
                        "quality": "fresh",
                        "value": {"net_qty": -100, "delta_qty": -20},
                    },
                    "investor": {
                        "quality": "fresh",
                        "value": {"foreign_net": -10, "inst_net": -20},
                    },
                }
            },
            "external_market_context": {
                "quality": "fresh",
                "risk_state": "RISK_OFF",
            },
        },
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )

    observations = evidence["context_observations"]
    assert observations["program_flow"]["usable_for_risk"] is False
    assert observations["investor_flow"]["usable_for_risk"] is False
    assert observations["external_market"]["usable_for_risk"] is False
    assert "program_flow_net_and_delta_sell" not in evidence["contradicting_facts"]
    assert "foreign_institutional_joint_sell" not in evidence["contradicting_facts"]
    assert "external_market_risk_off" not in evidence["contradicting_facts"]


def test_setup_evidence_waits_for_pullback_confirmation_and_fails_closed():
    waiting = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(
            orderly_pullback_recovery=True,
            trusted_supportive_trigger=False,
        ),
        recovery_analysis=_recovery_analysis(),
    )
    assert waiting["setup_family"] == "PULLBACK_RECOVERY"
    assert waiting["setup_state"] == "WAIT_CONFIRMATION"
    assert "trigger_confirmation_missing" in waiting["contradicting_facts"]
    assert "CONFIRMATION_MISSING" in waiting["corroborated_risk_codes"]
    assert waiting["recheck_reasons"] == ["TRIGGER_CONFIRMATION_RECHECK"]
    waiting_composed = compose_entry_decision(
        setup_evidence=waiting,
        risk_adjudication=_risk(
            "CAUTION",
            ["CONFIRMATION_MISSING"],
            contradict=["trigger_confirmation_missing"],
        ),
    )
    assert waiting_composed["action"] == "WAIT"
    assert waiting_composed["entry_probe_intent"] is True
    assert waiting_composed["entry_recheck_intent"] is True

    insufficient = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            **_exact_analysis(),
            "source_quality": {"status": "stale", "completed_bar_count": 20},
        },
        recovery_analysis=_recovery_analysis(source_mode="unusable"),
    )
    assert insufficient["setup_state"] == "INSUFFICIENT"
    assert "SOURCE_QUALITY_GAP" in insufficient["corroborated_risk_codes"]

    unknown_status = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            **_exact_analysis(),
            "source_quality": {"status": "unknown", "completed_bar_count": 20},
        },
        recovery_analysis=_recovery_analysis(source_mode="fresh_dual"),
    )
    assert unknown_status["setup_state"] == "INSUFFICIENT"
    assert "source_quality_unusable" in unknown_status["invalidation_facts"]
    assert "SOURCE_QUALITY_GAP" in unknown_status["corroborated_risk_codes"]


def test_setup_evidence_promotes_trusted_supportive_trigger_to_ready():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(),
    )

    assert evidence["setup_family"] == "CLEAN_CONTINUATION"
    assert evidence["setup_state"] == "READY"
    assert "trusted_supportive_trigger" in evidence["positive_facts"]


def test_deep_drawdown_recovery_is_not_mislabeled_clean_continuation():
    analysis = _exact_analysis()
    analysis["completed_structure"] = {
        "phase": "recovery_continuation",
        "phase_policy_version": "entry_completed_bar_structure_phase_v2",
        "peak_drawdown_pct": -10.4651,
        "returns_pct": {"1m": 0.3257, "3m": 0.3257, "5m": -0.1621},
    }
    evidence = build_entry_setup_evidence(
        exact_payload={
            "current": {"price": 3080},
            "entry_candle_context": {
                "source_quality": {
                    "decision_window": {"end_timestamp": "2026-08-07T13:45:00+09:00"}
                }
            },
        },
        exact_analysis=analysis,
        recovery_analysis=_recovery_analysis(),
    )

    assert evidence["setup_family"] == "RECOVERY_CONFIRMATION"
    assert evidence["setup_state"] == "READY"
    assert evidence["structure_phase"] == "recovery_continuation"
    assert evidence["structure_phase_bar_end"] == "2026-08-07T13:45:00+09:00"
    assert len(evidence["structure_phase_sha256"]) == 64


def test_intrabar_readiness_can_change_without_rewriting_structure_phase():
    stable_structure = {
        "phase": "recovery_continuation",
        "phase_policy_version": "entry_completed_bar_structure_phase_v2",
        "peak_drawdown_pct": -8.0,
    }
    ready = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={**_exact_analysis(), "completed_structure": stable_structure},
        recovery_analysis=_recovery_analysis(),
    )
    waiting_analysis = _exact_analysis(trusted_supportive_trigger=False)
    waiting_analysis["completed_structure"] = stable_structure
    waiting = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=waiting_analysis,
        recovery_analysis=_recovery_analysis(),
    )

    assert ready["structure_phase"] == waiting["structure_phase"]
    assert ready["structure_phase_sha256"] == waiting["structure_phase_sha256"]
    assert ready["setup_family"] == waiting["setup_family"] == ("RECOVERY_CONFIRMATION")
    assert ready["execution_readiness_state"] == "READY"
    assert waiting["execution_readiness_state"] == "WAIT_CONFIRMATION"


def test_rebound_attempt_keeps_structural_family_while_micro_confirmation_waits():
    analysis = _exact_analysis(trusted_supportive_trigger=False)
    analysis["completed_structure"] = {
        "phase": "rebound_attempt",
        "phase_policy_version": "entry_completed_bar_structure_phase_v2",
        "peak_drawdown_pct": -4.2,
    }
    recovery = _recovery_analysis(clean=False)
    recovery["eligible_for_counterfactual_probe"] = False
    recovery["bounded_opportunity"] = {"eligible_for_one_share_probe": False}
    recovery["recovery_confirmation_probe"] = {"eligible": False}

    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=analysis,
        recovery_analysis=recovery,
    )

    assert evidence["structure_phase"] == "rebound_attempt"
    assert evidence["setup_family"] == "RECOVERY_CONFIRMATION"
    assert evidence["setup_state"] == "WAIT_CONFIRMATION"
    assert evidence["recheck_reasons"] == ["TRIGGER_CONFIRMATION_RECHECK"]


def test_tail_liquidity_fragility_is_bounded_probe_risk_not_entry_veto():
    analysis = _exact_analysis()
    analysis["executable_liquidity"] = {
        "state": "adverse",
        "execution_cost_state": "wide_but_observable",
        "spread_bp": 123.76,
        "fillability_score": 10,
        "top3_ask_to_bid_ratio": 7.4,
    }
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=analysis,
        recovery_analysis=_recovery_analysis(clean=True),
    )

    assert evidence["setup_state"] == "READY"
    assert evidence["recheck_reasons"] == []
    assert "tail_liquidity_fragility" in evidence["contradicting_facts"]
    assert "LIQUIDITY_FRAGILE" in evidence["corroborated_risk_codes"]
    assert evidence["tail_risk_assessment"]["state"] == (
        "elevated_depth_spread_fragility"
    )

    composed = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=_risk(
            "VETO",
            ["LIQUIDITY_FRAGILE"],
            contradict=["tail_liquidity_fragility"],
        ),
    )
    assert composed["action"] == "WAIT"
    assert composed["entry_probe_intent"] is True
    assert composed["entry_recheck_intent"] is False


def test_wide_ask_wall_is_observed_as_fragile_until_downstream_submit_guard():
    analysis = _exact_analysis(ask_wall_wide_spread=True)
    analysis["executable_liquidity"] = {
        "state": "blocking",
        "execution_cost_state": "wide_but_observable",
        "spread_bp": 60,
    }

    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=analysis,
        recovery_analysis=_recovery_analysis(clean=True),
    )

    assert evidence["setup_state"] == "READY"
    assert evidence["invalidation_facts"] == []
    assert "ask_wall_wide_spread" in evidence["contradicting_facts"]
    assert "LIQUIDITY_FRAGILE" in evidence["corroborated_risk_codes"]


def test_large_sell_only_blocker_becomes_recheck_not_probe():
    analysis = _exact_analysis(trusted_supportive_trigger=False)
    analysis["volume_confirmation"] = {
        "state": "confirmed",
        "volume_ratio": 1.4,
    }
    recovery = _recovery_analysis()
    recovery["hard_blockers"] = ["large_sell_print_present"]
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=analysis,
        recovery_analysis=recovery,
    )

    assert evidence["setup_family"] == "CLEAN_CONTINUATION"
    assert evidence["setup_state"] == "WAIT_CONFIRMATION"
    assert evidence["recheck_reasons"] == ["LARGE_SELL_EXHAUSTION_RECHECK"]
    assert "trigger_confirmation_missing" not in evidence["contradicting_facts"]

    composed = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=_risk(
            "VETO",
            ["STRUCTURE_INVALIDATED"],
            contradict=["hard_blocker:large_sell_print_present"],
        ),
    )
    assert composed["action"] == "WAIT"
    assert composed["entry_probe_intent"] is False
    assert composed["entry_recheck_intent"] is True


def test_report_attributes_tail_fragility_as_bounded_probe_stress(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(quality, "DETAILED_PAIRED_REPORT_DIR", tmp_path)
    analysis = _exact_analysis()
    analysis["executable_liquidity"] = {
        "state": "adverse",
        "execution_cost_state": "wide_but_observable",
        "spread_bp": 123.76,
        "fillability_score": 10,
        "top3_ask_to_bid_ratio": 7.4,
    }
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=analysis,
        recovery_analysis=_recovery_analysis(clean=True),
    )
    candidate_response = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=_risk(
            "VETO",
            ["LIQUIDITY_FRAGILE"],
            contradict=["tail_liquidity_fragility"],
        ),
    )
    candidate_contract = {
        "prompt_version": "tail-recheck-entry",
        "system_prompt_sha256": "tail-recheck-prompt",
        "response_schema_sha256": "tail-recheck-schema",
        "exposure_semantics": "offline_counterfactual_passive_probe_only",
    }
    candidate_contract["contract_sha256"] = quality._candidate_contract_sha256(
        candidate_contract
    )
    report = quality.build_paired_replay_report(
        target_date="2026-08-05",
        requests=[
            {
                "decision_trace_id": "tail-recheck",
                "paired_replay_id": "tail-recheck-pair",
                "stock_code": "000001",
                "candidate": candidate_contract,
                "anticipatory_reversal_analysis": {
                    "execution_cost": {"conservative_execution_cost_pct": 0.6}
                },
            }
        ],
        results=[
            {
                "decision_trace_id": "tail-recheck",
                "paired_replay_id": "tail-recheck-pair",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "pass",
                "same_payload_confirmed": True,
                "candidate_contract_sha256": candidate_contract["contract_sha256"],
                "control_response": {"action": "WAIT"},
                "candidate_response": candidate_response,
            }
        ],
        labels=[
            {
                "decision_trace_id": "tail-recheck",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 1.0,
                        "mfe_pct": 1.7,
                        "mae_pct": -1.96,
                        "first_hit": "adverse",
                        "entry_path_first_hit": "adverse_first",
                    }
                },
            }
        ],
    )

    row = report["paired_comparisons"][0]
    assert row["candidate_exposure_selected"] is False
    assert row["candidate_probe_armed"] is True
    assert row["entry_recheck_intent"] is False
    assert row["entry_ai_bounded_risk_codes"] == ["LIQUIDITY_FRAGILE"]
    assert report["candidate_probe_loss_budget_breach_count"] == 0
    assert report["candidate_probe_severe_tail_exposure_count"] == 0
    assert report["candidate_probe_risk_budget"]["pass"] is False
    assert report["candidate_probe_arm_risk_budget"]["loss_budget_breach_count"] == 1
    assert report["candidate_probe_arm_risk_budget"]["severe_tail_count"] == 1
    assert report["candidate_probe_arm_risk_budget"]["pass"] is False


def test_risk_adjudication_rejects_invented_facts_and_semantic_drift():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )
    valid = _risk(
        "PASS",
        ["NO_BLOCKING_RISK"],
        support=["structural_edge_floor"],
    )
    assert validate_entry_risk_adjudication(valid, setup_evidence=evidence) == []

    invented = {
        **valid,
        "supporting_fact_ids": ["symbol_specific_secret_signal"],
    }
    assert "entry_risk_supporting_fact_ids_invented" in (
        validate_entry_risk_adjudication(invented, setup_evidence=evidence)
    )
    assert "entry_risk_pass_codes_invalid" in validate_entry_risk_adjudication(
        {**valid, "risk_codes": ["ADVERSE_TAPE"]},
        setup_evidence=evidence,
    )
    assert "entry_risk_unexpected_fields" in validate_entry_risk_adjudication(
        {**valid, "action": "BUY"},
        setup_evidence=evidence,
    )
    assert "entry_risk_unfounded_insufficient" in validate_entry_risk_adjudication(
        _risk("INSUFFICIENT", ["SOURCE_QUALITY_GAP"]),
        setup_evidence=evidence,
    )

    invalid = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            **_exact_analysis(blocking_overextension=True),
            "contradictions": ["multi_horizon_direction_conflict"],
        },
        recovery_analysis=_recovery_analysis(clean=True),
    )
    assert "entry_risk_invalid_setup_invalidation_fact_required" in (
        validate_entry_risk_adjudication(
            _risk(
                "VETO",
                ["REWARD_RISK_WEAK"],
                contradict=["multi_horizon_direction_conflict"],
            ),
            setup_evidence=invalid,
        )
    )

    waiting = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(trusted_supportive_trigger=False),
        recovery_analysis=_recovery_analysis(),
    )
    assert "entry_risk_no_blocking_verdict_invalid" in (
        validate_entry_risk_adjudication(
            _risk(
                "CAUTION",
                ["NO_BLOCKING_RISK"],
                contradict=["trigger_confirmation_missing"],
            ),
            setup_evidence=waiting,
        )
    )


def test_invalid_entry_risk_repair_copies_only_ledger_invalidation_and_stays_veto():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            **_exact_analysis(blocking_overextension=True),
            "contradictions": ["multi_horizon_direction_conflict"],
        },
        recovery_analysis=_recovery_analysis(clean=True),
    )
    response = _risk(
        "VETO",
        ["STRUCTURE_INVALIDATED", "CONFIRMATION_MISSING"],
        support=["structural_edge_floor"],
        contradict=["multi_horizon_direction_conflict"],
    )

    repaired, repairs = repair_invalid_entry_risk_adjudication(
        response,
        setup_evidence=evidence,
    )

    assert repairs == ["invalid_setup_invalidation_fact_copied_from_ledger"]
    assert repaired["risk_verdict"] == "VETO"
    assert repaired["risk_codes"] == response["risk_codes"]
    assert repaired["contradicting_fact_ids"][0] in evidence["invalidation_facts"]
    assert (
        validate_entry_risk_adjudication(
            repaired,
            setup_evidence=evidence,
        )
        == []
    )


def test_composer_uses_only_corroborated_veto_as_offline_block():
    ready = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )
    passed = compose_entry_decision(
        setup_evidence=ready,
        risk_adjudication=_risk(
            "PASS",
            ["NO_BLOCKING_RISK"],
            support=["structural_edge_floor"],
        ),
    )
    assert passed["action"] == "BUY"
    assert passed["composer_version"] == "entry_decision_composer_policy_v8"
    assert passed["score_authority"] == (
        "legacy_response_shape_only_not_a_decision_gate"
    )
    assert passed["entry_probe_intent"] is True
    assert passed["runtime_effect"] is False
    assert passed["broker_order_forbidden"] is True

    ready_with_conflict = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis={
            **_exact_analysis(),
            "contradictions": ["multi_horizon_direction_conflict"],
        },
        recovery_analysis=_recovery_analysis(clean=True),
    )
    uncorroborated = compose_entry_decision(
        setup_evidence=ready_with_conflict,
        risk_adjudication=_risk(
            "VETO",
            ["REWARD_RISK_WEAK"],
            contradict=["multi_horizon_direction_conflict"],
        ),
    )
    assert uncorroborated["action"] == "WAIT"
    assert uncorroborated["entry_probe_intent"] is True
    assert uncorroborated["entry_ai_veto_corroborated"] is False

    adverse_tape_analysis = _exact_analysis()
    adverse_tape_analysis["tape_sample"] = {
        "state": "sufficient",
        "raw_status": "adverse",
    }
    ready_with_adverse_tape = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=adverse_tape_analysis,
        recovery_analysis=_recovery_analysis(clean=True),
    )
    bounded = compose_entry_decision(
        setup_evidence=ready_with_adverse_tape,
        risk_adjudication=_risk(
            "VETO",
            ["ADVERSE_TAPE"],
            contradict=["tape_adverse"],
        ),
    )
    assert bounded["action"] == "WAIT"
    assert bounded["entry_probe_intent"] is True
    assert bounded["entry_ai_veto_corroborated"] is False
    assert bounded["entry_ai_bounded_risk_codes"] == ["ADVERSE_TAPE"]
    assert bounded["downstream_guard_contract"]["guard_bypass_allowed"] is False
    assert "entry_risk_pass_ignores_corroborated_risk" in (
        validate_entry_risk_adjudication(
            _risk(
                "PASS",
                ["NO_BLOCKING_RISK"],
                support=["structural_edge_floor"],
            ),
            setup_evidence=ready_with_adverse_tape,
        )
    )

    invalid = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(blocking_overextension=True),
        recovery_analysis=_recovery_analysis(clean=True),
    )
    blocked = compose_entry_decision(
        setup_evidence=invalid,
        risk_adjudication=_risk(
            "VETO",
            ["OVEREXTENSION_CHASE"],
            contradict=["blocking_overextension"],
        ),
    )
    assert blocked["action"] == "DROP"
    assert blocked["entry_ai_veto_corroborated"] is True


def test_composer_fails_closed_when_direct_caller_skips_validation():
    ready = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )

    composed = compose_entry_decision(
        setup_evidence=ready,
        risk_adjudication=_risk("PASS", ["NO_BLOCKING_RISK"]),
    )

    assert composed["action"] == "WAIT"
    assert composed["entry_probe_intent"] is False
    assert composed["entry_ai_contract_valid"] is False
    assert composed["decision_quality_contract_status"] == "fail_closed"
    assert "entry_risk_fact_reference_required" in composed["entry_ai_contract_errors"]


def test_setup_evidence_contract_rejects_authority_or_family_state_drift():
    ready = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )
    authority_drift = {
        **ready,
        "runtime_effect": True,
    }
    authority_drift["evidence_sha256"] = quality._sha256(
        {
            key: value
            for key, value in authority_drift.items()
            if key != "evidence_sha256"
        }
    )
    authority_result = compose_entry_decision(
        setup_evidence=authority_drift,
        risk_adjudication=_risk(
            "PASS",
            ["NO_BLOCKING_RISK"],
            support=["structural_edge_floor"],
        ),
    )
    assert authority_result["action"] == "WAIT"
    assert (
        "entry_setup_authority_contract_invalid"
        in authority_result["entry_ai_contract_errors"]
    )

    family_drift = {
        **ready,
        "setup_family": "NO_VALID_SETUP",
    }
    family_drift["evidence_sha256"] = quality._sha256(
        {key: value for key, value in family_drift.items() if key != "evidence_sha256"}
    )
    family_result = compose_entry_decision(
        setup_evidence=family_drift,
        risk_adjudication=_risk(
            "PASS",
            ["NO_BLOCKING_RISK"],
            support=["structural_edge_floor"],
        ),
    )
    assert family_result["action"] == "WAIT"
    assert (
        "entry_setup_family_state_inconsistent"
        in family_result["entry_ai_contract_errors"]
    )


def test_v2_14_detailed_replay_composes_risk_only_response(monkeypatch):
    exact_payload = {"current": {"price": 10000}}
    base_request = {
        "paired_replay_id": "pair-v2-14",
        "decision_trace_id": "trace-v2-14",
        "stage": "entry",
        "stock_code": "000001",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "payload_sha256": quality._sha256(exact_payload),
        "exact_payload": exact_payload,
        "control": {
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "captured_action": "WAIT",
        },
        "candidate": {
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "response_schema_sha256": "old-schema",
        },
        "sample_floor": {"pass": True},
        **quality.OFFLINE_CONTRACT,
    }
    monkeypatch.setattr(
        quality,
        "build_exact_payload_analysis_v1",
        lambda *_args, **_kwargs: {
            **_exact_analysis(),
            "analysis_sha256": "exact-analysis-hash",
        },
    )
    monkeypatch.setattr(
        quality,
        "build_v2_13_recovery_confirmation_analysis_v1",
        lambda *_args, **_kwargs: {
            **_recovery_analysis(clean=True),
            "analysis_sha256": "recovery-analysis-hash",
        },
    )

    request = quality.prepare_detailed_paired_replay_requests(
        [base_request],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
    )[0]
    assert request["candidate"]["system_prompt"].isascii()
    assert request["candidate"]["semantic_validator_version"] == (
        quality.ENTRY_SETUP_RISK_SEMANTIC_VALIDATOR_VERSION
    )
    assert request["candidate"]["semantic_repair_version"] == (
        quality.ENTRY_RISK_ADJUDICATION_REPAIR_VERSION
    )
    assert request["candidate"]["tail_risk_observation_contract_sha256"] == (
        quality._sha256(quality.TAIL_RISK_OBSERVATION_CONTRACT)
    )
    assert request["candidate"]["entry_structure_phase_policy_version"] == (
        quality.STRUCTURE_PHASE_POLICY_VERSION
    )
    assert request["sample_floor"]["promotion_evidence_floor"] == {
        "candidate_exposure_decision_rows": 10,
        "candidate_exposure_unique_symbols": 3,
        "pass": None,
        "evaluation_stage": "post_candidate_exposure_outcome_join",
        "promotion_authority": False,
    }
    assert (
        request["candidate_input"][ENTRY_SETUP_EVIDENCE_SCHEMA]["setup_state"]
        == "READY"
    )

    response = _risk(
        "PASS",
        ["NO_BLOCKING_RISK"],
        support=["structural_edge_floor"],
    )
    results = quality.run_paired_replay(
        [request],
        control_runner=lambda _: {"action": "WAIT"},
        candidate_runner=lambda _: response,
    )
    assert results[0]["status"] == "pass"
    assert results[0]["candidate_response"]["action"] == "BUY"
    assert results[0]["candidate_response"]["entry_probe_intent"] is True
    assert results[0]["candidate_risk_adjudication_response"] == response
    assert (
        quality.validate_replay_candidate_response(
            request,
            results[0]["candidate_response"],
        )
        == []
    )
    assert results[0]["runtime_effect"] is False

    report = quality.build_paired_replay_report(
        target_date="2026-08-06",
        requests=[request],
        results=results,
        labels=[
            {
                "decision_trace_id": "trace-v2-14",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": 1.0,
                        "mfe_pct": 1.2,
                        "mae_pct": -0.2,
                        "first_hit": "target",
                    }
                },
            }
        ],
    )
    assert report["entry_setup_adjudicator_summary"]["setup_state_counts"] == {
        "READY": 1
    }
    assert report["entry_setup_evidence_version"] == (
        request["candidate"]["entry_setup_evidence_version"]
    )
    assert report["entry_structure_phase_policy_version"] == (
        quality.STRUCTURE_PHASE_POLICY_VERSION
    )
    assert report["paired_comparisons"][0]["entry_composed_action"] == "BUY"
    assert report["runtime_effect"] is False


def test_v2_15_soft_distribution_keeps_only_bounded_recovery_probe():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )
    evidence.update(
        {
            "setup_family": "NO_VALID_SETUP",
            "setup_state": "INVALID",
            "structure_phase": "distribution",
            "execution_readiness_state": "INVALID",
            "positive_facts": ["liquidity_supportive", "volume_confirmed"],
            "contradicting_facts": ["supportive_micro_tape_vs_program_net_sell"],
            "invalidation_facts": ["no_supported_setup"],
            "corroborated_risk_codes": ["STRUCTURE_INVALIDATED"],
            "recheck_reasons": [],
            "source_quality": {
                "status": "fresh_consistent",
                "source_mode": "fresh_dual",
                "completed_bar_count": 20,
            },
        }
    )
    evidence["evidence_sha256"] = quality._sha256(
        {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    )
    risk = _risk(
        "VETO",
        ["STRUCTURE_INVALIDATED"],
        support=["liquidity_supportive"],
        contradict=["no_supported_setup"],
    )

    legacy = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=risk,
    )
    candidate = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=risk,
        bounded_recovery_policy=True,
    )

    assert legacy["action"] == "DROP"
    assert candidate["action"] == "WAIT"
    assert candidate["entry_probe_intent"] is True
    assert candidate["entry_recheck_intent"] is True
    assert candidate["entry_bounded_recovery_eligible"] is True
    assert candidate["entry_bounded_recovery_path"] == (
        "soft_distribution_micro_program_divergence"
    )
    assert candidate["composer_version"] == "entry_decision_composer_policy_v9"
    assert candidate["actual_order_submitted"] is False


def test_v2_15_preparation_uses_constrained_schema_and_offline_composer(monkeypatch):
    exact_payload = {"current": {"price": 10000}}
    monkeypatch.setattr(
        quality,
        "build_exact_payload_analysis_v1",
        lambda *_args, **_kwargs: {
            **_exact_analysis(),
            "analysis_sha256": "exact-analysis-hash",
        },
    )
    monkeypatch.setattr(
        quality,
        "build_v2_13_recovery_confirmation_analysis_v1",
        lambda *_args, **_kwargs: {
            **_recovery_analysis(clean=True),
            "analysis_sha256": "recovery-analysis-hash",
        },
    )

    request = quality.prepare_detailed_paired_replay_requests(
        [
            {
                "paired_replay_id": "pair-v2-15",
                "decision_trace_id": "trace-v2-15",
                "stage": "entry",
                "stock_code": "000001",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "payload_sha256": quality._sha256(exact_payload),
                "exact_payload": exact_payload,
                "control": {"provider": "openai", "model": "gpt-5.4-nano"},
                "candidate": {"provider": "openai", "model": "gpt-5.4-nano"},
                "sample_floor": {"pass": True},
                **quality.OFFLINE_CONTRACT,
            }
        ],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
        ),
    )[0]

    candidate = request["candidate"]
    evidence = request["entry_setup_evidence"]
    assert candidate["system_prompt"].isascii()
    assert candidate["entry_decision_composer_version"] == (
        "entry_decision_composer_policy_v9"
    )
    instance_schema = quality._candidate_openai_schema(
        stage="entry",
        candidate=candidate,
        setup_evidence=evidence,
    )
    assert (
        instance_schema["properties"]["supporting_fact_ids"]["items"]["enum"]
        == evidence["positive_facts"]
    )
    assert candidate["response_schema_sha256"] == quality._sha256(
        candidate["response_schema"]
    )
    assert candidate["response_schema_instance_sha256"] == quality._sha256(
        instance_schema
    )
    assert candidate["response_schema_instance_policy"] == "exact_fact_role_enum_v1"
    assert request["runtime_effect"] is False
    assert request["actual_order_submitted"] is False


def test_v2_15_hard_blocker_never_becomes_bounded_recovery_support():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(clean=True),
    )
    evidence.update(
        {
            "setup_family": "NO_VALID_SETUP",
            "setup_state": "INVALID",
            "structure_phase": "distribution",
            "execution_readiness_state": "INVALID",
            "positive_facts": ["liquidity_supportive", "tape_supportive"],
            "contradicting_facts": ["supportive_micro_tape_vs_program_net_sell"],
            "invalidation_facts": ["hard_blocker:large_sell_print_present"],
            "corroborated_risk_codes": ["STRUCTURE_INVALIDATED"],
            "recheck_reasons": [],
            "source_quality": {
                "status": "fresh_consistent",
                "source_mode": "fresh_dual",
                "completed_bar_count": 20,
            },
        }
    )
    evidence["evidence_sha256"] = quality._sha256(
        {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    )

    result = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=_risk(
            "VETO",
            ["STRUCTURE_INVALIDATED"],
            support=["liquidity_supportive"],
            contradict=["hard_blocker:large_sell_print_present"],
        ),
        bounded_recovery_policy=True,
    )

    assert result["action"] == "DROP"
    assert result["entry_probe_intent"] is False
    assert result["entry_bounded_recovery_eligible"] is False


def test_v2_15_recovery_confirmation_requires_liquidity_and_tape_support():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(recovery=True),
    )
    evidence.update(
        {
            "setup_family": "RECOVERY_CONFIRMATION",
            "setup_state": "WAIT_CONFIRMATION",
            "structure_phase": "recovery_continuation",
            "execution_readiness_state": "WAIT_CONFIRMATION",
            "positive_facts": ["liquidity_supportive", "tape_supportive"],
            "contradicting_facts": ["trigger_confirmation_missing"],
            "invalidation_facts": [],
            "corroborated_risk_codes": ["CONFIRMATION_MISSING"],
            "recheck_reasons": ["TRIGGER_CONFIRMATION_RECHECK"],
            "source_quality": {
                "status": "fresh_consistent",
                "source_mode": "fresh_dual",
                "completed_bar_count": 20,
            },
        }
    )
    evidence["evidence_sha256"] = quality._sha256(
        {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    )
    risk = _risk(
        "CAUTION",
        ["CONFIRMATION_MISSING"],
        support=["liquidity_supportive", "tape_supportive"],
        contradict=["trigger_confirmation_missing"],
    )

    eligible = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=risk,
        bounded_recovery_policy=True,
    )
    assert eligible["action"] == "WAIT"
    assert eligible["entry_probe_intent"] is True
    assert eligible["entry_bounded_recovery_path"] == (
        "recovery_liquidity_tape_confirmation"
    )

    evidence["positive_facts"] = ["liquidity_supportive"]
    evidence["evidence_sha256"] = quality._sha256(
        {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    )
    not_eligible = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=_risk(
            "CAUTION",
            ["CONFIRMATION_MISSING"],
            support=["liquidity_supportive"],
            contradict=["trigger_confirmation_missing"],
        ),
        bounded_recovery_policy=True,
    )
    assert not_eligible["action"] == "WAIT"
    assert not_eligible["entry_probe_intent"] is False
    assert not_eligible["entry_bounded_recovery_eligible"] is False


def test_v2_16_retains_recovery_seed_without_arming_initial_probe():
    evidence = build_entry_setup_evidence(
        exact_payload={"current": {"price": 10000}},
        exact_analysis=_exact_analysis(),
        recovery_analysis=_recovery_analysis(recovery=True),
    )
    evidence.update(
        {
            "setup_family": "RECOVERY_CONFIRMATION",
            "setup_state": "WAIT_CONFIRMATION",
            "structure_phase": "recovery_continuation",
            "execution_readiness_state": "WAIT_CONFIRMATION",
            "positive_facts": ["liquidity_supportive", "tape_supportive"],
            "contradicting_facts": ["trigger_confirmation_missing"],
            "invalidation_facts": [],
            "corroborated_risk_codes": ["CONFIRMATION_MISSING"],
            "recheck_reasons": ["TRIGGER_CONFIRMATION_RECHECK"],
            "source_quality": {
                "status": "fresh_consistent",
                "source_mode": "fresh_dual",
                "completed_bar_count": 20,
            },
        }
    )
    evidence["evidence_sha256"] = quality._sha256(
        {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    )

    candidate = compose_entry_decision(
        setup_evidence=evidence,
        risk_adjudication=_risk(
            "CAUTION",
            ["CONFIRMATION_MISSING"],
            support=["liquidity_supportive", "tape_supportive"],
            contradict=["trigger_confirmation_missing"],
        ),
        sequential_recovery_policy=True,
    )

    assert candidate["action"] == "WAIT"
    assert candidate["entry_probe_intent"] is False
    assert candidate["entry_recheck_intent"] is True
    assert candidate["entry_sequential_recovery_seed_eligible"] is True
    assert candidate["entry_sequential_recovery_policy_version"] == (
        "entry_sequential_recovery_policy_v1"
    )
    assert candidate["composer_version"] == "entry_decision_composer_policy_v10"
    assert candidate["actual_order_submitted"] is False


def test_recovery_composer_rejects_ambiguous_policy_modes():
    with pytest.raises(
        ValueError, match="entry_recovery_policy_modes_are_mutually_exclusive"
    ):
        compose_entry_decision(
            setup_evidence={},
            risk_adjudication={},
            bounded_recovery_policy=True,
            sequential_recovery_policy=True,
        )


def test_v2_16_preparation_uses_sequential_prompt_and_offline_composer(monkeypatch):
    exact_payload = {"current": {"price": 10000}}
    monkeypatch.setattr(
        quality,
        "build_exact_payload_analysis_v1",
        lambda *_args, **_kwargs: {
            **_exact_analysis(),
            "analysis_sha256": "exact-analysis-hash",
        },
    )
    monkeypatch.setattr(
        quality,
        "build_v2_13_recovery_confirmation_analysis_v1",
        lambda *_args, **_kwargs: {
            **_recovery_analysis(recovery=True),
            "analysis_sha256": "recovery-analysis-hash",
        },
    )

    request = quality.prepare_detailed_paired_replay_requests(
        [
            {
                "paired_replay_id": "pair-v2-16",
                "decision_trace_id": "trace-v2-16",
                "stage": "entry",
                "stock_code": "000001",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "payload_sha256": quality._sha256(exact_payload),
                "exact_payload": exact_payload,
                "control": {"provider": "openai", "model": "gpt-5.4-nano"},
                "candidate": {"provider": "openai", "model": "gpt-5.4-nano"},
                "sample_floor": {"pass": True},
                **quality.OFFLINE_CONTRACT,
            }
        ],
        candidate_prompt_version=(
            quality.DECISION_QUALITY_V2_16_SEQUENTIAL_RECOVERY_PROMPT_VERSION
        ),
    )[0]

    assert request["candidate"]["system_prompt"].isascii()
    assert "no immediate probe" in request["candidate"]["system_prompt"]
    assert request["candidate"]["entry_decision_composer_version"] == (
        "entry_decision_composer_policy_v10"
    )
    assert request["runtime_effect"] is False
    assert request["broker_order_forbidden"] is True


def test_v2_14_cumulative_learning_counts_wait_probe_and_separates_contract(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(quality, "DETAILED_PAIRED_REPORT_DIR", tmp_path)
    prior = {
        "runtime_effect": False,
        "candidate_contract_sha256": "old-contract",
        "paired_comparisons": [
            {
                "decision_trace_id": "old-trace",
                "stock_code": "000999",
                "candidate_action": "BUY",
                "candidate_exposure_selected": True,
                "candidate_execution_cost_adjusted_decision_value_pct": 9.0,
            }
        ],
    }
    (tmp_path / "ai_prompt_detailed_paired_replay_2026-08-04_v214.json").write_text(
        json.dumps(prior), encoding="utf-8"
    )

    summary = quality._anticipatory_cumulative_learning_summary(
        target_date="2026-08-05",
        current_rows=[
            {
                "decision_trace_id": "wait-probe",
                "stock_code": "000001",
                "candidate_action": "WAIT",
                "candidate_exposure_selected": True,
                "control_decision_value_pct": 0.1,
                "candidate_decision_value_pct": 0.6,
                "control_primary_decision_value_pct": 0.0,
                "candidate_primary_decision_value_pct": 0.4,
                "delta_pct": 0.4,
                "candidate_execution_cost_adjusted_decision_value_pct": 0.4,
                "entry_path_first_hit": "target_first",
                "candidate_probe_worst_loss_pct": -0.3,
                "candidate_probe_severe_tail_exposure": False,
            }
        ],
        candidate_prompt_version="v214",
        candidate_contract_sha256="current-contract",
    )

    assert summary["decision_count"] == 1
    assert summary["candidate_exposure_decision_count"] == 1
    assert summary["candidate_exposure_unique_symbol_count"] == 1
    assert summary["candidate_contract_sha256"] == "current-contract"
    assert summary["control_source_quality_adjusted_ev_pct"] == 0.1
    assert summary["candidate_source_quality_adjusted_ev_pct"] == 0.6
    assert summary["source_quality_adjusted_ev_delta_pct"] == 0.5
    assert summary["candidate_primary_decision_ev_pct"] == 0.4
    assert summary["candidate_primary_decision_ev_delta_pct"] == 0.4
    assert summary["candidate_exposure_probe_cost_adjusted_ev_pct"] == 0.4
    assert summary["candidate_probe_loss_budget_breach_count"] == 0


def test_bounded_probe_risk_budget_allows_tolerable_tail_not_zero_risk():
    rows = [
        {
            "candidate_probe_worst_loss_pct": -2.5 if index == 0 else -0.5,
            "candidate_probe_severe_tail_exposure": index == 0,
        }
        for index in range(10)
    ]

    budget = quality._bounded_probe_risk_budget(rows)

    assert budget["loss_budget_breach_rate_pct"] == 10.0
    assert budget["severe_tail_rate_pct"] == 10.0
    assert budget["catastrophic_loss_count"] == 0
    assert budget["pass"] is True

    for row in rows[:3]:
        row["candidate_probe_worst_loss_pct"] = -2.5
        row["candidate_probe_severe_tail_exposure"] = True
    assert quality._bounded_probe_risk_budget(rows)["pass"] is False


def test_cumulative_promotion_floor_uses_same_contract_route_samples():
    rows = [
        {
            "decision_trace_id": f"trace-{index}",
            "stock_code": f"{index % 3 + 1:06d}",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "candidate_exposure_selected": True,
            "candidate_execution_cost_contract_applied": True,
            "candidate_execution_cost_pct": 0.1,
            "control_decision_value_pct": 0.0,
            "candidate_decision_value_pct": 0.5,
            "control_primary_decision_value_pct": 0.0,
            "candidate_primary_decision_value_pct": 0.4,
            "delta_pct": 0.4,
            "candidate_probe_worst_loss_pct": -2.5 if index == 0 else -0.4,
            "candidate_probe_severe_tail_exposure": index == 0,
            "control_missed_upside": True,
            "candidate_missed_upside": False,
            "control_drawdown_recovery_captured": False,
            "candidate_drawdown_recovery_captured": False,
            "entry_recheck_intent": False,
        }
        for index in range(10)
    ]

    summary = quality._anticipatory_cumulative_learning_summary(
        target_date="2026-08-06",
        current_rows=rows,
        candidate_prompt_version="v214",
        candidate_contract_sha256="contract",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
    )

    assert summary["promotion_evidence_floor"]["pass"] is True
    assert summary["candidate_probe_risk_budget"]["pass"] is True
    assert summary["promotion_quality_gate_pass"] is True
    assert summary["cohort_scope"]["isolated"] is True

    missing_cost_rows = [dict(row) for row in rows]
    missing_cost_rows[0]["candidate_execution_cost_pct"] = None
    missing_cost_summary = quality._anticipatory_cumulative_learning_summary(
        target_date="2026-08-06",
        current_rows=missing_cost_rows,
        candidate_prompt_version="v214",
        candidate_contract_sha256="contract",
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
    )
    assert missing_cost_summary["promotion_quality_gate_pass"] is False
    assert (
        missing_cost_summary["promotion_quality_checks"][
            "candidate_exposure_probe_cost_adjusted_ev_positive"
        ]
        is False
    )


def test_entry_recheck_transition_attributes_later_ready_probe_same_route():
    rows = [
        {
            "decision_trace_id": "wait",
            "decision_ts": "2026-08-06T09:00:00+09:00",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "entry_recheck_intent": True,
            "entry_setup_state": "WAIT_CONFIRMATION",
            "candidate_exposure_selected": False,
        },
        {
            "decision_trace_id": "ready",
            "decision_ts": "2026-08-06T09:01:00+09:00",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "entry_recheck_intent": False,
            "entry_setup_state": "READY",
            "candidate_exposure_selected": True,
            "candidate_primary_decision_value_pct": 0.8,
            "entry_path_first_hit": "target_first",
        },
    ]

    summary = quality._attach_entry_recheck_transitions(rows)

    assert summary["ready_exposure_confirmed_count"] == 1
    assert summary["confirmed_exposure_cost_adjusted_ev_pct"] == 0.8
    assert rows[0]["entry_recheck_confirmation_delay_sec"] == 60.0


def test_wait_probe_is_attributed_as_arm_not_unsubmitted_exposure():
    report = quality.build_paired_replay_report(
        target_date="2026-08-05",
        requests=[
            {
                "decision_trace_id": "wait-probe-risk",
                "paired_replay_id": "wait-probe-risk-pair",
                "stock_code": "000001",
                "candidate": {
                    "exposure_semantics": ("offline_counterfactual_passive_probe_only")
                },
                "anticipatory_reversal_analysis": {
                    "execution_cost": {"conservative_execution_cost_pct": 0.1}
                },
            }
        ],
        results=[
            {
                "decision_trace_id": "wait-probe-risk",
                "paired_replay_id": "wait-probe-risk-pair",
                "stage": "entry",
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "pass",
                "same_payload_confirmed": True,
                "control_response": {"action": "WAIT"},
                "candidate_response": {
                    "action": "WAIT",
                    "entry_probe_intent": True,
                    "entry_probe_intent_status": "eligible_wait_probe",
                },
            }
        ],
        labels=[
            {
                "decision_trace_id": "wait-probe-risk",
                "source_quality_status": "pass",
                "decision_stage": "entry",
                "horizon_metrics": {
                    "10m": {
                        "end_return_pct": -0.8,
                        "mfe_pct": 1.2,
                        "mae_pct": -1.2,
                        "first_hit": "adverse",
                        "entry_path_first_hit": "adverse_first",
                    }
                },
            }
        ],
    )

    row = report["paired_comparisons"][0]
    assert row["candidate_exposure_selected"] is False
    assert row["candidate_probe_armed"] is True
    assert "false_buy" not in row["candidate_error_taxonomy"]
    assert "false_buy_tight_stop_adverse_first" not in row["candidate_error_taxonomy"]
    assert "false_wait" in row["candidate_error_taxonomy"]
    assert report["candidate_probe_arm_risk_budget"]["evaluable_count"] == 1
    assert report["candidate_probe_arm_risk_budget"]["pass"] is True
