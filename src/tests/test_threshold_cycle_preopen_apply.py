import json

from src.engine import threshold_cycle_preopen_apply as mod


def test_preopen_apply_rejects_panic_lifecycle_standalone_env_candidate():
    selected, decisions, env = mod._select_auto_apply_candidates(
        [
            {
                "family": "panic_lifecycle_actuator",
                "family_type": "sim_lifecycle_source",
                "stage": "entry",
                "calibration_state": "adjust_up",
                "allowed_runtime_apply": True,
                "safety_revert_required": False,
                "target_env_keys": ["LIFECYCLE_DECISION_MATRIX_ENABLED"],
                "recommended_values": {"enabled": True},
            }
        ],
        ai_review={"items_by_family": {}},
        require_ai=False,
    )

    assert selected == []
    assert env == {}
    assert decisions[0]["selected"] is False
    assert decisions[0]["decision_reason"] == "non_live_selectable_sim_lifecycle_source"


def test_build_preopen_apply_manifest_uses_latest_prior_report(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)

    (report_dir / "threshold_cycle_2026-04-29.json").write_text(
        json.dumps({"date": "2026-04-29", "apply_candidate_list": [{"family": "old"}]}),
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_2026-04-30.json").write_text(
        json.dumps(
            {
                "date": "2026-04-30",
                "apply_candidate_list": [{"family": "bad_entry_block", "stage": "holding_exit"}],
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "calibration_state": "adjust_up",
                        "safety_revert_required": False,
                    }
                ],
                "threshold_snapshot": {"bad_entry_block": {"apply_ready": True}},
                "post_apply_attribution": {"status": "pending_applied_cohort"},
                "safety_guard_pack": [{"family": "soft_stop_whipsaw_confirmation"}],
                "calibration_trigger_pack": [{"family": "soft_stop_whipsaw_confirmation"}],
                "rollback_guard_pack": [{"family": "bad_entry_block"}],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest("2026-05-04")

    assert manifest["status"] == "manifest_ready"
    assert manifest["runtime_change"] is False
    assert manifest["source_date"] == "2026-04-30"
    assert manifest["candidates"] == [{"family": "bad_entry_block", "stage": "holding_exit"}]
    assert manifest["calibration_candidates"][0]["family"] == "soft_stop_whipsaw_confirmation"
    assert manifest["calibration_policy"]["condition_miss_action"] == "calibration_trigger"
    saved = json.loads((apply_dir / "threshold_apply_2026-05-04.json").read_text(encoding="utf-8"))
    assert saved["source_date"] == "2026-04-30"


def test_build_preopen_apply_manifest_accepts_calibrated_apply_candidate(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)

    (report_dir / "threshold_cycle_2026-05-07.json").write_text(
        json.dumps(
            {
                "date": "2026-05-07",
                "apply_candidate_list": [],
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "apply_mode": "calibrated_apply_candidate",
                        "safety_revert_required": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-08",
        source_date="2026-05-07",
        apply_mode="calibrated_apply_candidate",
    )

    assert manifest["status"] == "calibrated_manifest_ready"
    assert manifest["runtime_change"] is False
    assert manifest["calibration_candidates"][0]["apply_mode"] == "calibrated_apply_candidate"
    assert manifest["calibration_policy"]["rollback_policy"] == "safety_breach_only"


def test_build_preopen_apply_manifest_accepts_efficient_tradeoff_candidate(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-07.json").write_text(
        json.dumps(
            {
                "date": "2026-05-07",
                "apply_candidate_list": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "apply_mode": "efficient_tradeoff_canary_candidate",
                    }
                ],
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "apply_mode": "efficient_tradeoff_canary_candidate",
                        "calibration_state": "adjust_up",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-08",
        source_date="2026-05-07",
        apply_mode="efficient_tradeoff_canary_candidate",
    )

    assert manifest["status"] == "efficient_tradeoff_manifest_ready"
    assert manifest["runtime_change"] is False
    assert manifest["candidates"][0]["family"] == "score65_74_recovery_probe"
    assert manifest["calibration_policy"]["sample_shortfall_action"] == "cap_reduce_or_hold_sample_or_max_step_shrink"


def test_auto_bounded_live_writes_runtime_env_with_ai_guard_and_stage_priority(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "apply_candidate_list": [],
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding_exit",
                        "priority": 1,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED",
                            "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC",
                        ],
                        "recommended_values": {"enabled": True, "confirm_sec": 45},
                        "threshold_version": "soft_stop_whipsaw_confirmation:test",
                    },
                    {
                        "family": "bad_entry_refined_canary",
                        "stage": "holding_exit",
                        "priority": 20,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED"],
                        "recommended_values": {"enabled": True},
                    },
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
                            "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE",
                        ],
                        "recommended_values": {"enabled": True, "min_buy_pressure": 65.0},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "ai_model": "tier2-plus",
                "items": [
                    {"family": "soft_stop_whipsaw_confirmation", "guard_accepted": True, "ai_anomaly_route": "threshold_candidate"},
                    {"family": "bad_entry_refined_canary", "guard_accepted": True, "ai_anomaly_route": "threshold_candidate"},
                    {"family": "score65_74_recovery_probe", "guard_accepted": True, "ai_anomaly_route": "threshold_candidate"},
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["runtime_change"] is True
    selected = {item["family"] for item in manifest["auto_apply_selected"]}
    assert selected == {"soft_stop_whipsaw_confirmation", "score65_74_recovery_probe"}
    blocked = [item for item in manifest["auto_apply_decisions"] if item["family"] == "bad_entry_refined_canary"][0]
    assert blocked["selected"] is False
    assert blocked["decision_reason"] == "same_stage_owner_conflict:soft_stop_whipsaw_confirmation"
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC=45" in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=65" in env_text


def test_auto_bounded_live_imports_latency_classifier_recommendation(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    latency_dir = report_dir / "latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    latency_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "apply_candidate_list": [], "calibration_candidates": []}),
        encoding="utf-8",
    )
    (latency_dir / "latency_classifier_recommendation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "latency_block_count": 24,
                "selected_profile_id": "balanced_1200_1500_0100",
                "calibration_candidates": [
                    {
                        "family": "latency_classifier_runtime_profile",
                        "stage": "entry_latency_classifier",
                        "priority": 6,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION",
                            "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION",
                            "SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION",
                        ],
                        "current_values": {
                            "max_ws_age_ms_for_caution": 700,
                            "max_ws_jitter_ms_for_caution": 300,
                            "max_spread_ratio_for_caution": 0.005,
                        },
                        "recommended_values": {
                            "max_ws_age_ms_for_caution": 1200,
                            "max_ws_jitter_ms_for_caution": 1500,
                            "max_spread_ratio_for_caution": 0.01,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["latency_classifier_recommendation"]["status"] == "loaded"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION"] == "1200"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION"] == "1500"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION"] == "0.01"


def test_auto_bounded_live_writes_lifecycle_decision_matrix_policy_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    policy_file = "data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-08.json"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "stage": "lifecycle",
                        "priority": 31,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "LIFECYCLE_DECISION_MATRIX_ENABLED",
                            "LIFECYCLE_DECISION_MATRIX_POLICY_FILE",
                            "LIFECYCLE_DECISION_MATRIX_POLICY_VERSION",
                            "LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED",
                            "LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY",
                            "LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "policy_file": policy_file,
                            "policy_version": "lifecycle_decision_matrix_v1_2026-05-08",
                            "promote_enabled": True,
                            "max_promotes_per_day": 3,
                            "min_stage_confidence": 0.6,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED"] == "true"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_POLICY_FILE"] == policy_file
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED"] == "true"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY"] == "3"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE"] == "0.6"


def test_auto_bounded_live_writes_lifecycle_context_and_bias_off_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    context_file = "data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-08.json"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "stage": "lifecycle",
                        "priority": 31,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED",
                            "LIFECYCLE_AI_CONTEXT_ENABLED",
                            "LIFECYCLE_AI_CONTEXT_FILE",
                            "LIFECYCLE_AI_CONTEXT_VERSION",
                            "SCALP_ENTRY_ADM_ADVISORY_ENABLED",
                            "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED",
                            "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED",
                            "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED",
                            "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED",
                        ],
                        "recommended_values": {
                            "runtime_effect_enabled": False,
                            "lifecycle_ai_context_enabled": True,
                            "lifecycle_ai_context_file": context_file,
                            "lifecycle_ai_context_version": "lifecycle_ai_context_v1_2026-05-08",
                            "entry_adm_advisory_enabled": True,
                            "entry_adm_runtime_bias_enabled": False,
                            "holding_exit_matrix_advisory_enabled": True,
                            "holding_exit_matrix_runtime_bias_enabled": False,
                            "holding_exit_matrix_scale_in_bias_enabled": False,
                        },
                        "current_values": {
                            "runtime_effect_enabled": True,
                            "lifecycle_ai_context_enabled": False,
                            "lifecycle_ai_context_file": "",
                            "lifecycle_ai_context_version": "",
                            "entry_adm_advisory_enabled": True,
                            "entry_adm_runtime_bias_enabled": True,
                            "holding_exit_matrix_advisory_enabled": True,
                            "holding_exit_matrix_runtime_bias_enabled": True,
                            "holding_exit_matrix_scale_in_bias_enabled": True,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_FILE"] == context_file
    assert env["KORSTOCKSCAN_SCALP_ENTRY_ADM_ADVISORY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_ADVISORY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED"] == "false"


def test_lifecycle_context_overlay_bypasses_same_stage_runtime_selection(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    context_file = "data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-08.json"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "bad_entry_refined_canary",
                        "stage": "holding_exit",
                        "priority": 1,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED"],
                        "recommended_values": {"enabled": True},
                        "current_values": {"enabled": False},
                    },
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "stage": "holding_exit",
                        "priority": 31,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": [
                            "LIFECYCLE_DECISION_MATRIX_ENABLED",
                            "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED",
                            "LIFECYCLE_AI_CONTEXT_ENABLED",
                            "LIFECYCLE_AI_CONTEXT_FILE",
                            "LIFECYCLE_AI_CONTEXT_VERSION",
                            "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED",
                            "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED",
                            "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "runtime_effect_enabled": False,
                            "lifecycle_ai_context_enabled": True,
                            "lifecycle_ai_context_file": context_file,
                            "lifecycle_ai_context_version": "lifecycle_ai_context_v1_2026-05-08",
                            "entry_adm_advisory_enabled": True,
                            "entry_adm_runtime_bias_enabled": False,
                            "holding_exit_matrix_advisory_enabled": True,
                            "holding_exit_matrix_runtime_bias_enabled": False,
                            "holding_exit_matrix_scale_in_bias_enabled": False,
                        },
                        "current_values": {
                            "enabled": False,
                            "runtime_effect_enabled": False,
                            "lifecycle_ai_context_enabled": False,
                            "lifecycle_ai_context_file": "",
                            "lifecycle_ai_context_version": "",
                            "entry_adm_runtime_bias_enabled": False,
                            "holding_exit_matrix_runtime_bias_enabled": False,
                            "holding_exit_matrix_scale_in_bias_enabled": False,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {"family": "bad_entry_refined_canary", "guard_accepted": True},
                    {"family": "lifecycle_decision_matrix_runtime", "guard_accepted": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    selected_families = {item["family"] for item in manifest["auto_apply_selected"]}
    assert "lifecycle_decision_matrix_runtime" not in selected_families
    assert manifest["lifecycle_ai_context_overlay"]["selected"] is True
    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_FILE"] == context_file
    assert env["KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED"] == "false"
    assert env["KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED"] == "false"


def test_auto_bounded_live_excludes_ai_instrumentation_gap(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    report_dir.mkdir(parents=True)
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-08_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "score65_74_recovery_probe",
                        "guard_accepted": True,
                        "ai_anomaly_route": "instrumentation_gap",
                        "route_action": "exclude_from_threshold_candidate_review",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_blocked"
    assert manifest["runtime_change"] is False
    assert manifest["runtime_env_file"] == str(runtime_dir / "threshold_runtime_env_2026-05-11.env")
    assert manifest["auto_apply_decisions"][0]["decision_reason"] == "ai_route_excluded_from_threshold_candidate"
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env_text


def test_score65_74_entry_unlock_can_use_intraday_source_and_ignore_no_applied_gap(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    ai_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)

    (calibration_dir / "threshold_cycle_calibration_2026-05-18_intraday.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "run_phase": "intraday",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding_exit",
                        "priority": 1,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"],
                        "recommended_values": {"enabled": True},
                    },
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "sample_count": 50,
                        "sample_floor": 20,
                        "target_env_keys": [
                            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
                            "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW",
                            "AI_WAIT6579_PROBE_CANARY_MAX_QTY",
                        ],
                        "recommended_values": {"enabled": True, "max_budget_krw": 50000, "max_qty": 1},
                        "source_metrics": {
                            "entry_unlock_probe_ready": True,
                            "panic_state": "NORMAL",
                            "panic_regime_mode": "NORMAL",
                            "score65_74_avg_expected_ev_pct": 4.5,
                            "score65_74_avg_close_10m_pct": 5.2,
                            "order_bundle_submitted": 0,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_intraday.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    },
                    {
                        "family": "score65_74_recovery_probe",
                        "guard_accepted": True,
                        "guard_decision": {
                            "anomaly_route": "instrumentation_gap",
                            "route_action": "exclude_from_threshold_candidate_review",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-18",
        source_date="2026-05-18",
        source_phase="intraday",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        include_families={"score65_74_recovery_probe"},
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    blocked = [item for item in manifest["auto_apply_decisions"] if item["family"] == "soft_stop_whipsaw_confirmation"][0]
    assert blocked["decision_reason"] == "operator_family_filter_excluded"
    decision = [item for item in manifest["auto_apply_decisions"] if item["family"] == "score65_74_recovery_probe"][0]
    assert decision["selected"] is True
    assert decision["decision_reason"] == "entry_unlock_probe_ready_overrides_no_applied_probe_gap"
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-18.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW=50000" in env_text
    assert "KORSTOCKSCAN_WAIT6579_PROBE_CANARY_MAX_QTY=1" in env_text


def test_preopen_apply_does_not_fallback_to_intraday_when_postclose_ai_unavailable(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "calibration_candidates": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "stage": "holding",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": False,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "unavailable",
                "parse_warnings": ["ai correction response not provided"],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_intraday.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "soft_stop_whipsaw_confirmation",
                        "guard_accepted": True,
                        "ai_anomaly_route": "threshold_candidate",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-19",
        source_date="2026-05-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["ai_correction_review"]["status"] == "unavailable"
    assert manifest["ai_correction_review"]["phase"] == "postclose"
    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert decision["decision_reason"] == "ai_review_missing"


def test_operator_runtime_env_lock_preserves_score65_probe_through_sample_gap(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": False,
                        "safety_revert_required": False,
                        "calibration_state": "hold_sample",
                        "calibration_reason": "sample_shortfall_no_applied_probe_gap",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "items": [
                    {
                        "family": "score65_74_recovery_probe",
                        "guard_accepted": True,
                        "ai_anomaly_route": "instrumentation_gap",
                        "route_action": "exclude_from_threshold_candidate_review",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-05-18.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_entry_unlock_operator_override_2026-05-18",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "env_key": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
                "env_value": "true",
                "active_from_date": "2026-05-18",
                "min_observation_until_date": "2026-05-18",
                "allowed_close_reason_keywords": ["safety_revert", "severe_loss", "stale_quote"],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-19",
        source_date="2026-05-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is True
    assert decision["decision_reason"] == (
        "operator_runtime_env_lock_preserved:score65_74_entry_unlock_operator_override_2026-05-18"
    )
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"] == "true"
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-19.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true" in env_text


def test_operator_runtime_env_lock_does_not_preserve_score65_probe_on_safety_revert(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
                        "stage": "entry",
                        "priority": 10,
                        "allowed_runtime_apply": True,
                        "safety_revert_required": True,
                        "calibration_state": "adjust_up",
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_postclose.json").write_text(
        json.dumps({"ai_status": "parsed", "items": [{"family": "score65_74_recovery_probe", "guard_accepted": True}]}),
        encoding="utf-8",
    )
    (lock_dir / "score65_74_recovery_probe_2026-05-18.json").write_text(
        json.dumps(
            {
                "lock_id": "score65_74_entry_unlock_operator_override_2026-05-18",
                "enabled": True,
                "family": "score65_74_recovery_probe",
                "stage": "entry",
                "env_key": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
                "env_value": "true",
                "active_from_date": "2026-05-18",
                "min_observation_until_date": "2026-05-18",
                "allowed_close_reason_keywords": ["safety_revert", "severe_loss", "stale_quote"],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-19",
        source_date="2026-05-18",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    decision = manifest["auto_apply_decisions"][0]
    assert decision["selected"] is False
    assert decision["decision_reason"] == "safety_revert_required"
    assert decision["operator_runtime_env_lock"]["allowed_close"] is True
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in manifest["runtime_env_overrides"]


def test_operator_runtime_env_lock_supports_env_overrides_without_env_key(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    report_dir.mkdir(parents=True)
    lock_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (report_dir / "threshold_cycle_2026-05-19.json").write_text(
        json.dumps({"date": "2026-05-19", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "scalp_sim_ai_budget_manager_2026-05-19.json").write_text(
        json.dumps(
            {
                "lock_id": "scalp_sim_ai_budget_manager_continuous",
                "enabled": True,
                "family": "scalp_sim_ai_budget_manager",
                "stage": "sim_holding_ai_budget",
                "active_from_date": "2026-05-19",
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SIM_AI_MAX_CALLS_PER_MIN": "10",
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-20",
        source_date="2026-05-19",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = [
        item for item in manifest["auto_apply_decisions"] if item["family"] == "scalp_sim_ai_budget_manager"
    ][0]
    assert decision["selected"] is True
    assert decision["operator_runtime_env_lock"]["applied"] is True
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED"] == "true"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AI_MAX_CALLS_PER_MIN"] == "10"


def test_swing_approval_required_request_does_not_auto_apply_without_artifact(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    report_dir.mkdir(parents=True)
    swing_request_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0",
                    "real_order_allowed_actions": ["BUY_INITIAL", "SELL_CLOSE"],
                    "sim_only_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                    "blocked_real_order_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                },
                "approval_requests": [
                    {
                        "approval_id": "swing_runtime_approval:2026-05-08:swing_model_floor",
                        "family": "swing_model_floor",
                        "stage": "selection",
                        "target_env_keys": ["SWING_FLOOR_BULL"],
                        "current_values": {"floor_bull": 0.35},
                        "recommended_values": {"floor_bull": 0.30},
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["swing_runtime_approval"]["requested"] == 1
    assert manifest["swing_runtime_approval"]["approved"] == 0
    assert "approval_artifact_missing" in manifest["swing_runtime_approval"]["blocked"]
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SWING_FLOOR_BULL" not in env_text


def test_swing_user_approval_artifact_applies_env_and_keeps_dry_run(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_runtime_approval:2026-05-08:swing_model_floor"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {
                    "policy_id": "swing_one_share_real_canary_phase0",
                    "real_order_allowed_actions": ["BUY_INITIAL", "SELL_CLOSE"],
                    "sim_only_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                    "blocked_real_order_actions": ["AVG_DOWN", "PYRAMID", "SCALE_IN"],
                },
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "family": "swing_model_floor",
                        "stage": "selection",
                        "target_env_keys": ["SWING_FLOOR_BULL", "SWING_FLOOR_BEAR"],
                        "current_values": {"floor_bull": 0.35, "floor_bear": 0.40},
                        "recommended_values": {"floor_bull": 0.30, "floor_bear": 0.35},
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "swing_runtime_approvals_2026-05-08.json").write_text(
        json.dumps({"approved_requests": [{"approval_id": approval_id, "approved": True}]}),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is True
    assert manifest["swing_runtime_approval"]["approved"] == 1
    assert (
        manifest["swing_runtime_approval"]["real_canary_policy"]["policy_id"]
        == "swing_one_share_real_canary_phase0"
    )
    assert manifest["swing_runtime_approval"]["real_canary_policy"]["sim_only_actions"] == [
        "AVG_DOWN",
        "PYRAMID",
        "SCALE_IN",
    ]
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_FLOOR_BULL"] == "0.3"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"] == "true"
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SWING_FLOOR_BULL=0.3" in env_text
    assert "KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true" in env_text


def test_swing_scale_in_real_canary_requires_separate_artifact(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_scale_in_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "scale_in_real_canary_policy": {"policy_id": "swing_scale_in_real_canary_phase0"},
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_scale_in_real_canary_phase0",
                        "family": "swing_scale_in_real_canary_phase0",
                        "stage": "scale_in",
                        "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                        "target_env_keys": ["SWING_SCALE_IN_REAL_CANARY_ENABLED"],
                        "current_values": {"enabled": False},
                        "recommended_values": {"enabled": True},
                        "dry_run_required": False,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert "scale_in_real_canary_approval_artifact_missing" in manifest["swing_runtime_approval"]["blocked"]
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_ENABLED" not in env_text


def test_swing_one_share_real_canary_requires_separate_artifact(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_one_share_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {"policy_id": "swing_one_share_real_canary_phase0"},
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_one_share_real_canary_phase0",
                        "family": "swing_one_share_real_canary_phase0",
                        "stage": "real_canary_entry",
                        "target_env_keys": ["SWING_ONE_SHARE_REAL_CANARY_ENABLED"],
                        "current_values": {"enabled": False},
                        "recommended_values": {"enabled": True, "allowed_codes": "123456"},
                        "candidate_codes": ["123456"],
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert "one_share_real_canary_approval_artifact_missing" in manifest["swing_runtime_approval"]["blocked"]
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true" in env_text
    assert "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED" not in env_text


def test_swing_one_share_real_canary_artifact_applies_env_and_keeps_dry_run(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_one_share_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "real_canary_policy": {"policy_id": "swing_one_share_real_canary_phase0"},
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_one_share_real_canary_phase0",
                        "family": "swing_one_share_real_canary_phase0",
                        "stage": "real_canary_entry",
                        "target_env_keys": [
                            "SWING_ONE_SHARE_REAL_CANARY_ENABLED",
                            "SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_QTY",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW",
                            "SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT",
                        ],
                        "current_values": {
                            "enabled": False,
                            "allowed_codes": "",
                            "max_order_qty": 1,
                            "max_new_entries_per_day": 1,
                            "max_open_positions": 3,
                            "max_total_notional_krw": 300000,
                            "require_approval_artifact": True,
                        },
                        "recommended_values": {
                            "enabled": True,
                            "allowed_codes": "123456",
                            "max_order_qty": 1,
                            "max_new_entries_per_day": 1,
                            "max_open_positions": 3,
                            "max_total_notional_krw": 300000,
                            "require_approval_artifact": True,
                        },
                        "candidate_codes": ["123456"],
                        "dry_run_required": True,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "swing_one_share_real_canary_2026-05-08.json").write_text(
        json.dumps(
            {
                "policy_id": "swing_one_share_real_canary_phase0",
                "approved": True,
                "target_date": "2026-05-11",
                "allowed_codes": ["123456"],
                "max_order_qty": 1,
                "max_new_entries_per_day": 1,
                "max_open_positions": 3,
                "max_total_notional_krw": 300000,
                "approval_source_report": "data/report/swing_runtime_approval/swing_runtime_approval_2026-05-08.json",
                "approved_request_ids": [approval_id],
                "expires_after_target_date": True,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is True
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED"] == "true"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES"] == "123456"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_QTY"] == "1"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"] == "true"
    assert manifest["swing_runtime_approval"]["selected"][0]["family"] == "swing_one_share_real_canary_phase0"
    assert manifest["swing_runtime_approval"]["selected"][0]["one_share_real_canary"] is True


def test_swing_scale_in_real_canary_artifact_applies_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    for directory in (report_dir, swing_request_dir, approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)

    approval_id = "swing_scale_in_real_canary:2026-05-08:phase0"
    (report_dir / "threshold_cycle_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (swing_request_dir / "swing_runtime_approval_2026-05-08.json").write_text(
        json.dumps(
            {
                "scale_in_real_canary_policy": {"policy_id": "swing_scale_in_real_canary_phase0"},
                "approval_requests": [
                    {
                        "approval_id": approval_id,
                        "policy_id": "swing_scale_in_real_canary_phase0",
                        "family": "swing_scale_in_real_canary_phase0",
                        "stage": "scale_in",
                        "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                        "target_env_keys": [
                            "SWING_SCALE_IN_REAL_CANARY_ENABLED",
                            "SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_QTY",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION",
                        ],
                        "current_values": {
                            "enabled": False,
                            "allowed_arms": "",
                            "max_order_qty": 1,
                            "max_orders_per_day": 1,
                            "max_orders_per_position": 1,
                        },
                        "recommended_values": {
                            "enabled": True,
                            "allowed_arms": "PYRAMID,AVG_DOWN",
                            "max_order_qty": 1,
                            "max_orders_per_day": 1,
                            "max_orders_per_position": 1,
                        },
                        "dry_run_required": False,
                        "actual_order_submitted": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "swing_scale_in_real_canary_2026-05-08.json").write_text(
        json.dumps(
            {
                "policy_id": "swing_scale_in_real_canary_phase0",
                "approved": True,
                "target_date": "2026-05-11",
                "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                "max_order_qty": 1,
                "max_orders_per_day": 1,
                "max_orders_per_position": 1,
                "approval_source_report": "data/report/swing_runtime_approval/swing_runtime_approval_2026-05-08.json",
                "approved_request_ids": [approval_id],
                "expires_after_target_date": True,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is True
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_ENABLED"] == "true"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS"] == "AVG_DOWN,PYRAMID"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_MAX_QTY"] == "1"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"] == "true"
    assert manifest["swing_runtime_approval"]["selected"][0]["family"] == "swing_scale_in_real_canary_phase0"


def test_build_preopen_apply_manifest_reports_missing_source(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", tmp_path / "apply_plans")

    manifest = mod.build_preopen_apply_manifest("2026-05-04")

    assert manifest["status"] == "missing_source_report"
    assert manifest["runtime_change"] is False
    assert manifest["candidates"] == []


def test_scalp_sim_scale_in_window_approval_writes_runtime_env(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    approval_dir = tmp_path / "approvals"
    report_dir.mkdir(parents=True)
    approval_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", tmp_path / "latency")

    (report_dir / "threshold_cycle_2026-05-19.json").write_text(
        json.dumps({"date": "2026-05-19", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_scale_in_window_expansion_2026-05-19.json").write_text(
        json.dumps(
            {
                "policy_id": "scalp_sim_scale_in_window_expansion",
                "family": "scalp_sim_scale_in_window_expansion",
                "approved": True,
                "target_env_keys": [
                    "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED",
                    "SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS",
                    "SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT",
                    "SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT",
                    "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION",
                    "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY",
                ],
                "recommended_values": {
                    "enabled": True,
                    "allowed_arms": "PYRAMID,AVG_DOWN",
                    "min_profit_pct": -2.5,
                    "max_profit_pct": 2.5,
                    "max_orders_per_position": 1,
                    "max_orders_per_day": 30,
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-20",
        source_date="2026-05-19",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is True
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"]
        == "true"
    )
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS"]
        == "PYRAMID,AVG_DOWN"
    )
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY"] == "30"
    assert manifest["scalp_sim_scale_in_window_approval"]["selected"][0]["family"] == (
        "scalp_sim_scale_in_window_expansion"
    )
    assert manifest["calibration_candidates"] == []
