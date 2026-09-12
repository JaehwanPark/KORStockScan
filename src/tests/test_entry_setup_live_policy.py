from datetime import datetime

import pytest

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
    DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION,
)
from src.engine.scalping import entry_setup_live_policy as policy
from src.engine.scalping import entry_setup_scalping_rollout as rollout
from src.engine.scalping.entry_setup_evidence import (
    ENTRY_DECISION_COMPOSER_VERSION,
    ENTRY_DECISION_COMPOSER_V2_15_VERSION,
    ENTRY_SETUP_EVIDENCE_VERSION,
    STRUCTURE_PHASE_POLICY_VERSION,
)

SOURCE_DATE = "2026-08-06"
TARGET_DATE = "2026-08-07"
POSTCLOSE_GENERATED_AT = datetime(2026, 8, 6, 21, 5, tzinfo=policy.KST)


def _configure_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(policy, "LIVE_CANDIDATE_DIR", tmp_path / "candidates")
    monkeypatch.setattr(policy, "ACTIVATION_DIR", tmp_path / "activations")
    monkeypatch.setattr(policy, "DETAILED_REPORT_DIR", tmp_path / "detailed")
    monkeypatch.setattr(policy, "BATCH_REPORT_DIR", tmp_path / "batch")
    policy._ACTIVATION_CACHE.clear()


def _enable_probe_contract(monkeypatch):
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOWED_SCOPES", "KRX|KRX_REGULAR"
    )
    for key in (
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED",
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED",
    ):
        monkeypatch.setenv(key, "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION",
        "false",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", "DAILY")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", TARGET_DATE)
    monkeypatch.setenv(
        "KORSTOCKSCAN_OPENAI_ANALYZE_TARGET_PROMPT_VERSION",
        DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    )


def test_nxt_exact_candidate_preopen_and_runtime_are_isolated(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    _enable_probe_contract(monkeypatch)
    cohort = ("NXT", "NXT_AFTERMARKET")
    detailed = _valid_detailed_report()
    detailed["cohort_filter"] = dict(zip(("effective_venue", "session_bucket"), cohort))
    detailed["cumulative_learning"]["cohort_scope"].update(detailed["cohort_filter"])
    batch = _valid_batch_report()
    batch["cohorts"][0].update(detailed["cohort_filter"])
    batch["cohorts"] = batch["cohorts"][:1]
    detailed_path = policy.detailed_report_path(SOURCE_DATE, cohort=cohort)
    policy._atomic_write_json(detailed_path, detailed)
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)
    candidate = policy.build_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        detailed_report=detailed,
        detailed_path=detailed_path,
        generated_at=POSTCLOSE_GENERATED_AT,
        cohort=cohort,
    )
    assert candidate["allowed_runtime_apply"] is True, candidate["blocking_reasons"]
    policy._atomic_write_json(
        policy.live_candidate_path(SOURCE_DATE, cohort=cohort), candidate
    )
    blocked = policy.build_preopen_activation(target_date=TARGET_DATE, cohort=cohort)
    assert "runtime_contract_exact_recheck_scope_missing" in blocked["blocking_reasons"]
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOWED_SCOPES", "NXT|NXT_AFTERMARKET"
    )
    activation = policy.write_preopen_activation(target_date=TARGET_DATE, cohort=cohort)
    assert activation["status"] == "active_bounded_canary"
    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        effective_venue=cohort[0],
        session_bucket=cohort[1],
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 16, 5, tzinfo=policy.KST),
    )
    assert resolved["status"] == "active_bounded_nxt_canary"
    assert not policy.build_preopen_activation(target_date=TARGET_DATE)[
        "allowed_runtime_apply"
    ]
    # KRX sources cannot be relabelled as NXT, and an NXT switch never affects KRX.
    wrong = policy.build_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=_valid_batch_report(),
        detailed_report=_valid_detailed_report(),
        detailed_path=detailed_path,
        generated_at=POSTCLOSE_GENERATED_AT,
        cohort=cohort,
    )
    assert wrong["allowed_runtime_apply"] is False
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SETUP_NXT_CANARY_ENABLED", "false")
    assert (
        "operator_disabled"
        in policy.build_preopen_activation(target_date=TARGET_DATE, cohort=cohort)[
            "blocking_reasons"
        ]
    )


def test_dual_cohort_is_source_registered_but_cannot_be_live(
    monkeypatch, tmp_path
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    cohort = policy.DUAL_OBSERVE_ONLY_COHORT
    detailed = _valid_detailed_report()
    detailed["cohort_filter"] = dict(
        zip(("effective_venue", "session_bucket"), cohort)
    )
    detailed["cumulative_learning"]["cohort_scope"].update(
        detailed["cohort_filter"]
    )
    batch = _valid_batch_report()
    batch["cohorts"][0].update(detailed["cohort_filter"])
    detailed_path = tmp_path / "dual-detailed.json"
    policy._atomic_write_json(detailed_path, detailed)

    candidate = policy.build_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        detailed_report=detailed,
        detailed_path=detailed_path,
        generated_at=POSTCLOSE_GENERATED_AT,
        cohort=cohort,
    )
    assert candidate["status"] == "blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["operator_approval_required"] is True
    assert candidate["decision_authority"] == "observe_only_no_live_approval"
    assert "dual_cohort_observe_only_no_live_approval" in candidate[
        "blocking_reasons"
    ]
    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue=cohort[0],
        session_bucket=cohort[1],
        position_tag="SCANNER",
        strategy="SCALPING",
        now=datetime(2026, 9, 14, 16, 5, tzinfo=policy.KST),
    )
    assert resolved["enabled"] is False
    assert resolved["runtime_effect"] is False
    assert resolved["status"] == "fallback_dual_observe_only_no_live_approval"
    scope = "|".join(cohort)
    assert scope not in rollout.SCOPES
    assert rollout.scope_authority_mode(*cohort) == "observe_only_no_live_approval"


def _valid_detailed_report():
    prompt_version = (
        f"{DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION}_entry"
    )
    return {
        "schema": policy.DETAILED_REPORT_SCHEMA,
        "target_date": SOURCE_DATE,
        "cohort_filter": {
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
        },
        "requests": [
            {
                "candidate": {
                    "prompt_version": prompt_version,
                    "entry_setup_evidence_version": ENTRY_SETUP_EVIDENCE_VERSION,
                    "entry_decision_composer_version": (
                        ENTRY_DECISION_COMPOSER_VERSION
                    ),
                    "entry_structure_phase_policy_version": (
                        STRUCTURE_PHASE_POLICY_VERSION
                    ),
                }
            }
        ],
        "entry_setup_evidence_version": ENTRY_SETUP_EVIDENCE_VERSION,
        "entry_decision_composer_version": ENTRY_DECISION_COMPOSER_VERSION,
        "entry_structure_phase_policy_version": STRUCTURE_PHASE_POLICY_VERSION,
        "request_count": 1,
        "candidate_execution_selection": {
            "policy": policy.EXPECTED_CANDIDATE_SELECTION_POLICY,
            "outcome_blind": True,
            "contract_pass": True,
            "checkpoint_evaluated_setup_state_counts": {"READY": 1},
        },
        "promotion_report_integrity_pass": True,
        "promotion_quality_gate_pass": True,
        "provider_failed_count": 0,
        "candidate_provider_none_count": 0,
        "candidate_exposure_decision_count": 2,
        "candidate_exposure_unique_symbol_count": 1,
        "candidate_primary_decision_ev_pct": 0.31,
        "candidate_execution_cost_adjusted_ev_pct": 0.24,
        "candidate_exposure_sample_floor": {"pass": False},
        "candidate_probe_arm_decision_count": 12,
        "candidate_probe_arm_unique_symbol_count": 4,
        "candidate_probe_arm_sample_floor": {"pass": True},
        "candidate_contract_sha256": "candidate-contract-sha",
        "cumulative_learning": {
            "schema": "anticipatory_reversal_cumulative_learning_v2",
            "status": "cumulative_learning_updated",
            "as_of_date": SOURCE_DATE,
            "clean_tuning_baseline_date": policy.CLEAN_TUNING_BASELINE_DATE,
            "promotion_quality_gate_pass": True,
            "promotion_quality_checks": {
                key: True for key in policy.CUMULATIVE_PROMOTION_CHECK_KEYS
            },
            "candidate_contract_sha256": "candidate-contract-sha",
            "candidate_prompt_version": (
                DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
            ),
            "cohort_scope": {
                "isolated": True,
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
            },
            "promotion_evidence_floor": {"pass": True},
            "candidate_exposure_decision_count": 12,
            "candidate_exposure_unique_symbol_count": 4,
            "candidate_primary_decision_ev_pct": 0.28,
            "candidate_exposure_probe_cost_adjusted_ev_pct": 0.21,
            "full_cost_economics": {
                "schema": "entry_paired_full_cost_economics_v1",
                "pass": True,
                "sample_floor_pass": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "verified_pair_count": 12,
                "candidate_exposure_count": 12,
                "candidate_unique_symbol_count": 4,
                "candidate_net_ev_pct": 0.05,
                "paired_net_decision_delta_pct": 0.01,
                "actual_fill_proven": False,
                "additional_cost_subtracted_here": False,
            },
            "candidate_probe_arm_decision_count": 12,
            "candidate_probe_arm_unique_symbol_count": 4,
            "exploration_evidence_floor": {"pass": True},
            "opportunity_capture_tradeoff": {"net_missed_upside_value_pct": 0.16},
            "candidate_probe_risk_budget": {"pass": True},
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "opportunity_capture_tradeoff": {"net_missed_upside_value_pct": 0.18},
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _valid_batch_report():
    selection = {
        "policy": policy.EXPECTED_CANDIDATE_SELECTION_POLICY,
        "outcome_blind": True,
        "contract_pass": True,
        "checkpoint_evaluated_setup_state_counts": {"READY": 1},
    }
    return {
        "schema": policy.BATCH_SCHEMA,
        "target_date": SOURCE_DATE,
        "status": "completed_offline_only",
        "candidate_prompt_version": (
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
        "cohorts": [
            {
                "effective_venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "status": "completed_offline_only",
                "evaluated_request_count": 1,
                "promotion_quality_gate_pass": True,
                "candidate_prompt_version": (
                    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
                ),
                "candidate_execution_selection": selection,
            },
            {
                "effective_venue": "NXT",
                "session_bucket": "NXT_AFTERMARKET",
                "status": "completed_offline_only",
                "evaluated_request_count": 1,
                "promotion_quality_gate_pass": False,
                "candidate_execution_selection": selection,
            },
        ],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _valid_runtime_env():
    return {
        "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED": "true",
        "KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE": TARGET_DATE,
        "KORSTOCKSCAN_OPENAI_ANALYZE_TARGET_PROMPT_VERSION": (
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOWED_SCOPES": "KRX|KRX_REGULAR",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOW_WAIT_PROBE_INTENT": "true",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_PROBE_FIRST_CONTRACT": "true",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION": "false",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED": "true",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE": "DAILY",
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY": "1",
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED": "true",
    }


def _write_ready_chain(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    _enable_probe_contract(monkeypatch)
    detailed = _valid_detailed_report()
    detailed_path = policy.detailed_report_path(SOURCE_DATE)
    policy._atomic_write_json(detailed_path, detailed)
    batch = _valid_batch_report()
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)
    published = policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=True,
        generated_at=POSTCLOSE_GENERATED_AT,
    )
    activation = policy.write_preopen_activation(target_date=TARGET_DATE)
    return published, activation


def test_setup_canary_requires_reachable_exact_krx_recheck_scope(monkeypatch):
    key = "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOWED_SCOPES"
    monkeypatch.setenv(key, "KRX|KRX_REGULAR")
    for scopes in (None, "", "NXT|NXT_REGULAR", "krx|krx_regular", "KRX"):
        env = _valid_runtime_env()
        if scopes is None:
            env.pop(key)
        else:
            env[key] = scopes
        assert "runtime_contract_krx_recheck_scope_missing" in (
            policy._runtime_probe_contract_errors(target_date=TARGET_DATE, env=env)
        )
    env = _valid_runtime_env()
    env[key] = " NXT|NXT_REGULAR, KRX|KRX_REGULAR "
    assert policy._runtime_probe_contract_errors(target_date=TARGET_DATE, env=env) == []


def test_active_setup_falls_back_if_runtime_loses_krx_recheck_scope(
    monkeypatch, tmp_path
):
    _, activation = _write_ready_chain(monkeypatch, tmp_path)
    assert activation["status"] == "active_bounded_canary"
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ALLOWED_SCOPES", "")
    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 9, 10, tzinfo=policy.KST),
    )
    assert resolved["enabled"] is False
    assert resolved["status"] == "fallback_probe_first_runtime_contract_invalid"
    assert resolved["runtime_contract_errors"] == [
        "runtime_contract_krx_recheck_scope_missing"
    ]


def test_passed_postclose_candidate_activates_only_next_day_krx(monkeypatch, tmp_path):
    published, activation = _write_ready_chain(monkeypatch, tmp_path)

    assert published["status"] == "live_auto_apply_ready"
    assert published["effective_date"] == TARGET_DATE
    assert activation["status"] == "active_bounded_canary"
    assert activation["runtime_effect"] is True
    candidate = policy._read_json(policy.live_candidate_path(SOURCE_DATE))
    assert (
        candidate["promotion_metrics"]["daily_candidate_exposure_decision_count"] == 2
    )
    assert candidate["promotion_metrics"]["candidate_exposure_decision_count"] == 12
    assert candidate["canary_mode"] == policy.PERFORMANCE_CANARY_MODE
    assert candidate["risk_contract"]["eligible_position_tags"] == ["SCANNER"]
    assert candidate["entry_setup_evidence_version"] == ENTRY_SETUP_EVIDENCE_VERSION
    assert activation["entry_structure_phase_policy_version"] == (
        STRUCTURE_PHASE_POLICY_VERSION
    )
    assert activation["activation_contract"]["eligible_position_tags"] == ["SCANNER"]

    krx = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 9, 10, tzinfo=policy.KST),
    )
    assert krx["enabled"] is True
    assert krx["canary_mode"] == policy.PERFORMANCE_CANARY_MODE
    assert krx["entry_setup_evidence_version"] == ENTRY_SETUP_EVIDENCE_VERSION
    assert krx["entry_structure_phase_policy_version"] == (
        STRUCTURE_PHASE_POLICY_VERSION
    )
    assert krx["selected_prompt_version"] == (
        DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
    )

    nxt = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue="NXT",
        session_bucket="NXT_AFTERMARKET",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 16, 0, tzinfo=policy.KST),
    )
    assert nxt["enabled"] is False
    assert nxt["selected_prompt_version"] == (
        DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
    )


def test_v2_15_uses_registered_one_share_exploration_bridge(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    _enable_probe_contract(monkeypatch)
    detailed = _valid_detailed_report()
    detailed["requests"][0]["candidate"].update(
        {
            "prompt_version": (
                f"{DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION}_entry"
            ),
            "entry_decision_composer_version": ENTRY_DECISION_COMPOSER_V2_15_VERSION,
        }
    )
    detailed["entry_decision_composer_version"] = ENTRY_DECISION_COMPOSER_V2_15_VERSION
    detailed["cumulative_learning"][
        "candidate_prompt_version"
    ] = DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
    detailed_path = policy.detailed_report_path(
        SOURCE_DATE, DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
    )
    policy._atomic_write_json(detailed_path, detailed)
    batch = _valid_batch_report()
    batch["candidate_prompt_version"] = (
        DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
    )
    batch["cohorts"][0][
        "candidate_prompt_version"
    ] = DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)

    published = policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=True,
        candidate_prompt_version=(
            DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
        ),
        generated_at=POSTCLOSE_GENERATED_AT,
    )
    activation = policy.write_preopen_activation(target_date=TARGET_DATE)
    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 8, 30, tzinfo=policy.KST),
    )

    assert published["status"] == "bounded_exploration_apply_ready"
    assert activation["canary_mode"] == policy.EXPLORATION_CANARY_MODE
    assert resolved["selected_prompt_version"] == (
        DECISION_QUALITY_V2_15_BOUNDED_RECOVERY_PROMPT_VERSION
    )
    candidate = policy._read_json(policy.live_candidate_path(SOURCE_DATE))
    assert candidate["risk_contract"]["residual_multi_leg_forbidden"] is False
    assert candidate["risk_contract"]["quantity_policy_owner"] == (
        "position_sizing_dynamic_formula"
    )
    assert candidate["entry_decision_composer_version"] == (
        ENTRY_DECISION_COMPOSER_V2_15_VERSION
    )


def test_live_policy_falls_back_for_unknown_or_non_scanner_owner(monkeypatch, tmp_path):
    _write_ready_chain(monkeypatch, tmp_path)

    for position_tag in (None, "", "OPEN_RECLAIM", "VWAP_RECLAIM"):
        resolved = policy.resolve_live_prompt_policy(
            configured_prompt_version=(
                DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
            ),
            effective_venue="KRX",
            session_bucket="KRX_REGULAR",
            position_tag=position_tag,
            now=datetime(2026, 8, 7, 9, 10, tzinfo=policy.KST),
        )

        assert resolved["enabled"] is False
        assert resolved["status"] == "fallback_position_owner_out_of_scope"
        assert resolved["selected_prompt_version"] == (
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        )


def test_delayed_candidate_rolls_to_first_preopen_not_already_consumed(
    monkeypatch, tmp_path
):
    _configure_paths(monkeypatch, tmp_path)
    detailed = _valid_detailed_report()
    policy._atomic_write_json(policy.detailed_report_path(SOURCE_DATE), detailed)
    batch = _valid_batch_report()
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)

    before_cutoff = policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=False,
        generated_at=datetime(2026, 8, 7, 7, 34, tzinfo=policy.KST),
    )
    after_cutoff = policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=True,
        generated_at=datetime(2026, 8, 7, 8, 19, tzinfo=policy.KST),
    )

    assert before_cutoff["effective_date"] == "2026-08-07"
    assert after_cutoff["effective_date"] == "2026-08-10"
    candidate = policy._read_json(policy.live_candidate_path(SOURCE_DATE))
    assert candidate["effective_date_policy"] == policy.EFFECTIVE_DATE_POLICY
    assert candidate["preopen_candidate_cutoff_kst"] == "07:35:00"
    assert (
        policy._validate_candidate_artifact(
            candidate,
            target_date="2026-08-10",
            candidate_path=policy.live_candidate_path(SOURCE_DATE),
            runtime_env={
                **_valid_runtime_env(),
                "KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE": "2026-08-10",
            },
        )
        == []
    )


def test_runtime_falls_back_when_probe_first_contract_is_missing(monkeypatch, tmp_path):
    _write_ready_chain(monkeypatch, tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "2")

    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 9, 10, tzinfo=policy.KST),
    )

    assert resolved["enabled"] is False
    assert resolved["status"] == "fallback_probe_first_runtime_contract_invalid"
    assert "runtime_contract_probe_qty_not_one" in resolved["runtime_contract_errors"]


def test_runtime_falls_back_when_candidate_is_tampered(monkeypatch, tmp_path):
    _write_ready_chain(monkeypatch, tmp_path)
    candidate_path = policy.live_candidate_path(SOURCE_DATE)
    candidate_path.write_text(
        candidate_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 9, 10, tzinfo=policy.KST),
    )

    assert resolved["enabled"] is False
    assert resolved["status"] == "fallback_activation_contract_invalid"


def test_preexisting_candidate_without_current_phase_contract_falls_back(
    monkeypatch, tmp_path
):
    _write_ready_chain(monkeypatch, tmp_path)
    candidate_path = policy.live_candidate_path(SOURCE_DATE)
    candidate = policy._read_json(candidate_path)
    candidate.pop("entry_structure_phase_policy_version")
    candidate["artifact_sha256"] = policy._canonical_sha256(
        {key: value for key, value in candidate.items() if key != "artifact_sha256"}
    )
    policy._atomic_write_json(candidate_path, candidate)
    activation = policy.build_preopen_activation(target_date=TARGET_DATE)

    assert activation["status"] == "inactive_fallback_v2_13"
    assert (
        "candidate_entry_structure_phase_policy_version_stale"
        in activation["blocking_reasons"]
    )


def test_candidate_without_position_owner_scope_fails_closed(monkeypatch, tmp_path):
    _write_ready_chain(monkeypatch, tmp_path)
    candidate_path = policy.live_candidate_path(SOURCE_DATE)
    candidate = policy._read_json(candidate_path)
    candidate["risk_contract"].pop("eligible_position_tags")
    candidate["artifact_sha256"] = policy._canonical_sha256(
        {key: value for key, value in candidate.items() if key != "artifact_sha256"}
    )
    policy._atomic_write_json(candidate_path, candidate)

    activation = policy.build_preopen_activation(target_date=TARGET_DATE)

    assert activation["status"] == "inactive_fallback_v2_13"
    assert (
        "runtime_candidate_position_owner_scope_invalid"
        in activation["blocking_reasons"]
    )


def test_old_economic_basis_cannot_be_rehashed_into_new_runtime_authority(
    monkeypatch, tmp_path
):
    _write_ready_chain(monkeypatch, tmp_path)
    path = policy.live_candidate_path(SOURCE_DATE)
    candidate = policy._read_json(path)
    candidate["promotion_metrics"].pop("economic_gate_basis")
    candidate["artifact_sha256"] = policy._canonical_sha256(
        {key: value for key, value in candidate.items() if key != "artifact_sha256"}
    )
    policy._atomic_write_json(path, candidate)
    activation = policy.build_preopen_activation(target_date=TARGET_DATE)
    assert activation["status"] == "inactive_fallback_v2_13"
    assert "candidate_economic_gate_basis_stale" in activation["blocking_reasons"]
    assert (
        "runtime_candidate_economic_gate_basis_stale"
        in policy._runtime_candidate_contract_errors(
            candidate,
            target_date=TARGET_DATE,
        )
    )


def test_runtime_rejects_preexisting_activation_without_current_phase_contract(
    monkeypatch, tmp_path
):
    _write_ready_chain(monkeypatch, tmp_path)
    activation_path = policy.activation_path(TARGET_DATE)
    activation = policy._read_json(activation_path)
    activation.pop("entry_structure_phase_policy_version")
    activation["artifact_sha256"] = policy._canonical_sha256(
        {key: value for key, value in activation.items() if key != "artifact_sha256"}
    )
    policy._atomic_write_json(activation_path, activation)
    policy._ACTIVATION_CACHE.clear()

    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 9, 10, tzinfo=policy.KST),
    )

    assert resolved["enabled"] is False
    assert resolved["status"] == "fallback_activation_contract_invalid"


def test_sparse_daily_arms_use_cumulative_exploration_floor_only():
    detailed = _valid_detailed_report()
    detailed["candidate_probe_arm_decision_count"] = 2
    detailed["candidate_probe_arm_unique_symbol_count"] = 1
    detailed["candidate_probe_arm_sample_floor"] = {"pass": False}
    detailed["cumulative_learning"]["candidate_exposure_decision_count"] = 0
    detailed["cumulative_learning"]["candidate_exposure_unique_symbol_count"] = 0
    errors = policy._exploration_source_errors(
        source_errors=[], detailed_report=detailed
    )
    assert errors == []
    detailed["cumulative_learning"]["candidate_probe_arm_decision_count"] = 9
    assert (
        "cumulative_probe_arm_counts_below_floor"
        in policy._exploration_source_errors(
            source_errors=[],
            detailed_report=detailed,
        )
    )
    assert (
        "runtime_contract_disabled:KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED"
        in policy._exploration_source_errors(
            source_errors=[
                "runtime_contract_disabled:KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED"
            ],
            detailed_report=detailed,
        )
    )


def test_failed_promotion_writes_inactive_preopen_fallback(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    detailed = _valid_detailed_report()
    detailed["promotion_quality_gate_pass"] = False
    detailed["cumulative_learning"]["full_cost_economics"]["pass"] = False
    detailed["candidate_probe_arm_sample_floor"] = {"pass": False}
    detailed["cumulative_learning"]["exploration_evidence_floor"] = {"pass": False}
    policy._atomic_write_json(policy.detailed_report_path(SOURCE_DATE), detailed)
    batch = _valid_batch_report()
    batch["cohorts"][0]["promotion_quality_gate_pass"] = False
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)

    published = policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=True,
        generated_at=POSTCLOSE_GENERATED_AT,
    )
    activation = policy.write_preopen_activation(target_date=TARGET_DATE)

    assert published["status"] == "blocked"
    assert activation["status"] == "inactive_fallback_v2_13"
    assert activation["runtime_effect"] is False
    assert "candidate_not_live_ready" in activation["blocking_reasons"]


def test_exploration_probe_cap_ledger_is_daily_durable_and_deduplicated(
    monkeypatch, tmp_path
):
    _configure_paths(monkeypatch, tmp_path)

    assert policy.read_exploration_probe_submit_count(TARGET_DATE) == 0
    assert (
        policy.record_exploration_probe_submission(
            trade_date=TARGET_DATE,
            stock_code="005930",
            broker_order_no="order-1",
        )
        == 1
    )
    assert (
        policy.record_exploration_probe_submission(
            trade_date=TARGET_DATE,
            stock_code="005930",
            broker_order_no="order-1",
        )
        == 1
    )
    assert (
        policy.record_exploration_probe_submission(
            trade_date=TARGET_DATE,
            stock_code="000660",
            broker_order_no="order-2",
        )
        == 2
    )
    assert policy.read_exploration_probe_submit_count(TARGET_DATE) == 2


def test_exploration_probe_cap_ledger_corruption_fails_closed(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    path = policy.exploration_probe_cap_path(TARGET_DATE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")

    assert policy.read_exploration_probe_submit_count(TARGET_DATE) is None


def test_exploration_probe_cap_failure_marker_survives_restart(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    policy.mark_exploration_probe_cap_fail_closed(
        trade_date=TARGET_DATE,
        reason="atomic_replace_failed",
    )

    assert policy.read_exploration_probe_submit_count(TARGET_DATE) is None


def test_negative_performance_can_use_guarded_one_share_exploration(
    monkeypatch, tmp_path
):
    _configure_paths(monkeypatch, tmp_path)
    _enable_probe_contract(monkeypatch)
    detailed = _valid_detailed_report()
    detailed["promotion_quality_gate_pass"] = False
    cumulative = detailed["cumulative_learning"]
    cumulative["promotion_quality_gate_pass"] = False
    cumulative["promotion_quality_checks"] = {
        key: False for key in policy.CUMULATIVE_PROMOTION_CHECK_KEYS
    }
    cumulative["promotion_evidence_floor"] = {"pass": False}
    cumulative["candidate_exposure_decision_count"] = 0
    cumulative["candidate_exposure_unique_symbol_count"] = 0
    cumulative["candidate_probe_risk_budget"] = {"pass": False}
    policy._atomic_write_json(policy.detailed_report_path(SOURCE_DATE), detailed)
    batch = _valid_batch_report()
    batch["cohorts"][0]["promotion_quality_gate_pass"] = False
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)

    published = policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=True,
        generated_at=POSTCLOSE_GENERATED_AT,
    )
    activation = policy.write_preopen_activation(target_date=TARGET_DATE)
    candidate = policy._read_json(policy.live_candidate_path(SOURCE_DATE))

    assert published["status"] == "bounded_exploration_apply_ready"
    assert candidate["canary_mode"] == policy.EXPLORATION_CANARY_MODE
    assert candidate["risk_contract"]["residual_multi_leg_forbidden"] is False
    assert candidate["risk_contract"]["scale_in_forbidden"] is False
    assert candidate["risk_contract"]["quantity_policy_owner"] == (
        "position_sizing_dynamic_formula"
    )
    assert candidate["risk_contract"]["maximum_daily_exploration_probes"] == 3
    assert activation["status"] == "active_bounded_canary"
    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 9, 10, tzinfo=policy.KST),
    )
    assert resolved["enabled"] is True
    assert resolved["canary_mode"] == policy.EXPLORATION_CANARY_MODE
    assert resolved["maximum_daily_exploration_probes"] == 3


def test_mature_negative_exploration_stops_at_next_preopen(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    detailed = _valid_detailed_report()
    detailed["promotion_quality_gate_pass"] = False
    cumulative = detailed["cumulative_learning"]
    cumulative["promotion_quality_gate_pass"] = False
    cumulative["promotion_quality_checks"] = {
        key: False for key in policy.CUMULATIVE_PROMOTION_CHECK_KEYS
    }
    cumulative["candidate_exposure_decision_count"] = 10
    cumulative["candidate_exposure_unique_symbol_count"] = 4
    cumulative["candidate_primary_decision_ev_pct"] = -0.01
    cumulative["candidate_exposure_probe_cost_adjusted_ev_pct"] = -0.2
    cumulative["full_cost_economics"].update(
        {
            "candidate_net_ev_pct": -0.01,
            "paired_net_decision_delta_pct": -0.01,
            "pass": False,
        }
    )
    cumulative["candidate_probe_risk_budget"] = {
        "pass": True,
        "catastrophic_loss_count": 0,
    }
    batch = _valid_batch_report()
    batch["cohorts"][0]["promotion_quality_gate_pass"] = False
    detailed_path = tmp_path / "detailed.json"
    policy._atomic_write_json(detailed_path, detailed)

    candidate = policy.build_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        detailed_report=detailed,
        detailed_path=detailed_path,
        generated_at=POSTCLOSE_GENERATED_AT,
    )

    assert candidate["status"] == "blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert (
        "exploration_continuation_full_cost_economics_not_passed"
        in candidate["blocking_reasons"]
    )
    assert (
        candidate["promotion_metrics"]["exploration_continuation_gate"]["action"]
        == "stop_and_fallback_at_next_preopen"
    )


@pytest.mark.parametrize("failed_guard", [None, "cost", "tail", "source"])
def test_net_positive_candidate_does_not_require_every_gross_pattern_to_improve(
    monkeypatch, tmp_path, failed_guard
):
    _configure_paths(monkeypatch, tmp_path)
    detailed = _valid_detailed_report()
    batch = _valid_batch_report()
    batch["cohorts"][0]["promotion_quality_gate_pass"] = False
    detailed["promotion_quality_gate_pass"] = False
    cumulative = detailed["cumulative_learning"]
    cumulative["promotion_quality_gate_pass"] = False
    for key in policy.CUMULATIVE_PROMOTION_CHECK_KEYS:
        cumulative["promotion_quality_checks"][key] = (
            key in policy.LIVE_REQUIRED_CUMULATIVE_CHECK_KEYS
        )
    # Different gross horizon/proxy losses are not full-cost terminal-path EV.
    cumulative["candidate_primary_decision_ev_pct"] = -0.01
    cumulative["candidate_exposure_probe_cost_adjusted_ev_pct"] = -0.01
    if failed_guard == "cost":
        cumulative["full_cost_economics"]["candidate_net_ev_pct"] = None
    elif failed_guard == "tail":
        cumulative["candidate_probe_risk_budget"]["pass"] = False
    elif failed_guard == "source":
        detailed["promotion_report_integrity_pass"] = False
    path = tmp_path / "net-detailed.json"
    policy._atomic_write_json(path, detailed)
    candidate = policy.build_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        detailed_report=detailed,
        detailed_path=path,
        generated_at=POSTCLOSE_GENERATED_AT,
    )
    assert candidate["status"] == (
        "blocked" if failed_guard else "live_auto_apply_ready"
    )
    assert (
        candidate["promotion_metrics"]["economic_gate_basis"]
        == policy.NET_ECONOMIC_GATE_BASIS
    )
    assert candidate["runtime_effect"] is False
    assert candidate["actual_order_submitted"] is False


def test_malformed_candidate_source_paths_fail_closed_without_exception(
    monkeypatch, tmp_path
):
    _configure_paths(monkeypatch, tmp_path)
    malformed = {
        "schema": policy.LIVE_CANDIDATE_SCHEMA,
        "source_date": SOURCE_DATE,
        "effective_date": TARGET_DATE,
        "status": "live_auto_apply_ready",
        "allowed_runtime_apply": True,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "selected_prompt_version": (
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
        "rollback_prompt_version": (
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "source_provenance": {
            "batch_report_path": "",
            "detailed_report_path": "",
        },
    }
    malformed["artifact_sha256"] = policy._canonical_sha256(malformed)
    policy._atomic_write_json(policy.live_candidate_path(SOURCE_DATE), malformed)

    activation = policy.build_preopen_activation(target_date=TARGET_DATE)

    assert activation["status"] == "inactive_fallback_v2_13"
    assert "candidate_batch_path_invalid" in activation["blocking_reasons"]
    assert "candidate_detailed_path_invalid" in activation["blocking_reasons"]


def test_preopen_runtime_env_loader_matches_launcher_override_order(tmp_path):
    runtime_env_file = tmp_path / "threshold.env"
    operator_env_file = tmp_path / "operator.env"
    dated_env_file = tmp_path / "dated.env"
    runtime_env_file.write_text(
        "export KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true\n"
        f"export KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE={TARGET_DATE}\n"
        "export KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED=false\n",
        encoding="utf-8",
    )
    operator_env_file.write_text(
        "export KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED=true\n"
        "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY=2\n",
        encoding="utf-8",
    )
    dated_env_file.write_text(
        "export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY=1\n",
        encoding="utf-8",
    )

    merged, provenance, errors = policy.load_preopen_runtime_env(
        runtime_env_file=runtime_env_file,
        operator_env_file=operator_env_file,
        dated_operator_env_file=dated_env_file,
    )

    assert errors == []
    assert merged["KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED"] == "true"
    assert merged["KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY"] == "1"
    assert provenance["load_order"] == [
        "threshold_runtime_env",
        "operator_runtime_overrides",
        "dated_operator_runtime_overrides",
    ]
    assert provenance["effective_contract_sha256"]


def test_preopen_activation_validates_supplied_launcher_env_not_cron_process_env(
    monkeypatch, tmp_path
):
    _configure_paths(monkeypatch, tmp_path)
    detailed = _valid_detailed_report()
    policy._atomic_write_json(policy.detailed_report_path(SOURCE_DATE), detailed)
    batch = _valid_batch_report()
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)
    policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=True,
        generated_at=POSTCLOSE_GENERATED_AT,
    )
    for key in _valid_runtime_env():
        monkeypatch.delenv(key, raising=False)

    activation = policy.build_preopen_activation(
        target_date=TARGET_DATE,
        runtime_env=_valid_runtime_env(),
        runtime_env_provenance={"source": "test_launcher_merge"},
    )

    assert activation["status"] == "active_bounded_canary"
    assert activation["runtime_env_provenance"] == {"source": "test_launcher_merge"}


def test_preopen_honors_explicit_process_level_operator_off(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    policy._atomic_write_json(
        policy.detailed_report_path(SOURCE_DATE), _valid_detailed_report()
    )
    batch = _valid_batch_report()
    policy._atomic_write_json(policy.batch_report_path(SOURCE_DATE), batch)
    policy.publish_live_candidate(
        source_date=SOURCE_DATE,
        batch_report=batch,
        write=True,
        generated_at=POSTCLOSE_GENERATED_AT,
    )
    monkeypatch.setenv(policy.CANARY_ENV_KEY, "false")

    activation = policy.build_preopen_activation(
        target_date=TARGET_DATE,
        runtime_env=_valid_runtime_env(),
    )

    assert activation["status"] == "inactive_fallback_v2_13"
    assert "operator_disabled" in activation["blocking_reasons"]


def test_running_process_with_previous_runtime_date_falls_back(monkeypatch, tmp_path):
    _write_ready_chain(monkeypatch, tmp_path)
    monkeypatch.setenv("KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE", SOURCE_DATE)

    resolved = policy.resolve_live_prompt_policy(
        configured_prompt_version=(
            DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        ),
        effective_venue="KRX",
        session_bucket="KRX_REGULAR",
        position_tag="SCANNER",
        now=datetime(2026, 8, 7, 9, 10, tzinfo=policy.KST),
    )

    assert resolved["enabled"] is False
    assert resolved["status"] == "fallback_probe_first_runtime_contract_invalid"
    assert (
        "runtime_contract_target_date_mismatch" in resolved["runtime_contract_errors"]
    )
