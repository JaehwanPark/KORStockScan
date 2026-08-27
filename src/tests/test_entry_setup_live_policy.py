from datetime import datetime

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION,
    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
)
from src.engine.scalping import entry_setup_live_policy as policy
from src.engine.scalping.entry_setup_evidence import (
    ENTRY_DECISION_COMPOSER_VERSION,
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
    assert policy._validate_candidate_artifact(
        candidate,
        target_date="2026-08-10",
        candidate_path=policy.live_candidate_path(SOURCE_DATE),
        runtime_env={
            **_valid_runtime_env(),
            "KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE": "2026-08-10",
        },
    ) == []


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


def test_failed_promotion_writes_inactive_preopen_fallback(monkeypatch, tmp_path):
    _configure_paths(monkeypatch, tmp_path)
    detailed = _valid_detailed_report()
    detailed["promotion_quality_gate_pass"] = False
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
    assert candidate["risk_contract"]["residual_multi_leg_forbidden"] is True
    assert candidate["risk_contract"]["scale_in_forbidden"] is True
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
