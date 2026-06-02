import json

from src.engine import runtime_apply_bridge as bridge_mod
from src.engine import scalp_sim_scale_in_window_approval as scale_in_approval_mod
from src.engine import threshold_cycle_preopen_apply as mod
from src.engine import lifecycle_bucket_discovery as discovery_mod
from src.engine.scalping import scalp_sim_auto_approval_control_tower as scalp_sim_auto_mod
from src.engine.swing import sim_auto_approval_control_tower as swing_sim_mod


def _bounded_real_canary_tier2_contract() -> dict:
    return {
        "state": "bounded_real_canary_auto_approved",
        "tier2_status": "parsed",
        "tier2_policy": "fail_closed",
        "tier2_fail_closed": False,
        "primary_ev_uplift_threshold_pct": 1.0,
        "final_user_approval_boundary": "full_live_only",
    }


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


def test_score65_74_entry_unlock_candidate_accepts_score60_74_alias_metrics():
    assert mod._score65_74_entry_unlock_candidate(
        {
            "family": "score65_74_recovery_probe",
            "sample_count": 24,
            "sample_floor": 20,
            "source_metrics": {
                "score60_74_avg_expected_ev_pct": 3.1,
                "score60_74_avg_close_10m_pct": 1.4,
                "order_bundle_submitted": 0,
            },
        }
    ) is True


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


def test_preopen_apply_consumes_lifecycle_bucket_auto_apply_without_human_artifact(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    bridge_dir = tmp_path / "bridge"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim_auto"
    swing_sim_approval_dir = tmp_path / "swing_sim_auto"
    swing_sim_policy_dir = tmp_path / "swing_sim_policy"
    report_dir.mkdir(parents=True)
    bridge_dir.mkdir(parents=True)
    catalog_dir.mkdir(parents=True)
    sim_dir.mkdir(parents=True)
    swing_sim_approval_dir.mkdir(parents=True)
    swing_sim_policy_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(bridge_mod, "REPORT_DIR", bridge_dir)
    monkeypatch.setattr(discovery_mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(discovery_mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    monkeypatch.setattr(discovery_mod, "REPORT_DIR", report_dir / "lifecycle_bucket_discovery")
    monkeypatch.setattr(swing_sim_mod, "SIM_AUTO_APPROVAL_DIR", swing_sim_approval_dir)
    monkeypatch.setattr(swing_sim_mod, "SWING_SIM_POLICY_DIR", swing_sim_policy_dir)

    (report_dir / "threshold_cycle_2026-05-22.json").write_text(
        json.dumps({"date": "2026-05-22", "apply_candidate_list": [], "calibration_candidates": []}),
        encoding="utf-8",
    )
    (bridge_dir / "runtime_apply_bridge_2026-05-22.json").write_text(
        json.dumps(
            {
                "date": "2026-05-22",
                "candidates": [
                    {
                        "candidate_id": "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22",
                        "family": bridge_mod.ENTRY_BRIDGE_FAMILY,
                        "stage": "entry",
                        "priority": 9,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "target_env_keys": [
                            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
                            "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE",
                            "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE",
                        ],
                        "recommended_values": {"enabled": True, "min_score": 66, "max_score": 69},
                        "current_values": {"enabled": False, "min_score": 65, "max_score": 74},
                        "runtime_effect_after_approval": "bounded_entry_probe_recovery_live_auto",
                        "lifecycle_bucket_discovery_bucket_id": "entry:combo_entry_spot:score_66_69",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "auto_promotion_contract": {"tier2_status": "parsed", "tier2_policy": "fail_closed"},
                        "source_bucket_keys": ["score=score_66_69"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (catalog_dir / "lifecycle_bucket_catalog_2026-05-22.json").write_text("{}", encoding="utf-8")
    (sim_dir / "lifecycle_bucket_sim_auto_approval_2026-05-22.json").write_text(
        json.dumps(
            {
                "approved": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "approved_bucket_ids": ["entry:combo:test"],
                "approved_bucket_count": 1,
            }
        ),
        encoding="utf-8",
    )
    (swing_sim_policy_dir / "swing_sim_policy_catalog_2026-05-22.json").write_text(
        json.dumps({"schema_version": "swing_sim_policy_catalog_v1", "active_arm_priority_policies": []}),
        encoding="utf-8",
    )
    (swing_sim_approval_dir / "swing_sim_auto_approval_2026-05-22.json").write_text(
        json.dumps(
            {
                "report_type": "swing_sim_auto_approval",
                "approved": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "approved_source_ids": ["swing_lifecycle_bucket_discovery", "bottom_rebound_policy_auto_loop"],
                "approved_policy_count": 2,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-23",
        source_date="2026-05-22",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "auto_bounded_live_ready"
    assert manifest["runtime_apply_bridge"]["approved"] == 1
    assert manifest["runtime_apply_bridge"]["selected"][0]["family"] == bridge_mod.ENTRY_BRIDGE_FAMILY
    assert manifest["lifecycle_bucket_discovery"]["approved"] == 1
    assert manifest["lifecycle_bucket_discovery"]["selected"][0]["recommended_values"]["live_auto_apply_enabled"] is False
    assert manifest["swing_sim_auto_approval"]["approved"] == 1
    assert manifest["swing_sim_auto_approval"]["selected"][0]["approved_source_ids"] == [
        "swing_lifecycle_bucket_discovery",
        "bottom_rebound_policy_auto_loop",
    ]


def test_preopen_apply_blocks_empty_lifecycle_bucket_sim_auto_approval(tmp_path, monkeypatch):
    report_dir = tmp_path / "reports"
    runtime_dir = tmp_path / "runtime_env"
    bridge_dir = report_dir / "runtime_apply_bridge"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim_auto"
    apply_dir = tmp_path / "apply"
    for path in (report_dir, runtime_dir, bridge_dir, catalog_dir, sim_dir, apply_dir):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(bridge_mod, "REPORT_DIR", bridge_dir)
    monkeypatch.setattr(discovery_mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(discovery_mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    monkeypatch.setattr(discovery_mod, "REPORT_DIR", report_dir / "lifecycle_bucket_discovery")

    (report_dir / "threshold_cycle_2026-05-22.json").write_text(
        json.dumps({"date": "2026-05-22", "apply_candidate_list": [], "calibration_candidates": []}),
        encoding="utf-8",
    )
    (bridge_dir / "runtime_apply_bridge_2026-05-22.json").write_text(
        json.dumps({"date": "2026-05-22", "candidates": []}),
        encoding="utf-8",
    )
    (catalog_dir / "lifecycle_bucket_catalog_2026-05-22.json").write_text("{}", encoding="utf-8")
    (sim_dir / "lifecycle_bucket_sim_auto_approval_2026-05-22.json").write_text(
        json.dumps(
            {
                "approved": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "approved_bucket_ids": [],
                "approved_bucket_count": 0,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-23",
        source_date="2026-05-22",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["lifecycle_bucket_discovery"]["approved"] == 0
    assert manifest["lifecycle_bucket_discovery"]["selected"] == []
    assert "sim_auto_approval_empty" in manifest["lifecycle_bucket_discovery"]["blocked"]
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-23.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env_text
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE" not in env_text
    assert "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED=true" not in env_text


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
                            "SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED",
                            "SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE",
                            "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS",
                            "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS",
                            "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO",
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
                            "recovery_enabled": True,
                            "recovery_min_signal_score": 75.0,
                            "recovery_max_ws_age_ms": 1200,
                            "recovery_max_ws_jitter_ms": 1500,
                            "recovery_max_spread_ratio": 0.01,
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
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED"] == "true"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE"] == "75"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS"] == "1200"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS"] == "1500"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO"] == "0.01"


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


def test_latest_preopen_source_ignores_intraday_only_artifact(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    ai_dir = report_dir / "threshold_cycle_ai_review"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    latency_dir = tmp_path / "missing_latency_classifier_recommendation"
    ai_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "AI_REVIEW_DIR", ai_dir)
    monkeypatch.setattr(mod, "CALIBRATION_REPORT_DIR", calibration_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", latency_dir)

    (calibration_dir / "threshold_cycle_calibration_2026-05-18_intraday.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "run_phase": "intraday",
                "calibration_candidates": [
                    {
                        "family": "score65_74_recovery_probe",
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
    (ai_dir / "threshold_cycle_ai_review_2026-05-18_intraday.json").write_text(
        json.dumps({"ai_status": "parsed", "items": []}),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-19",
        apply_mode="auto_bounded_live",
        auto_apply=True,
    )

    assert manifest["status"] == "missing_source_report"
    assert manifest["runtime_change"] is False


def test_intraday_source_phase_blocks_auto_apply_even_when_candidate_ready(tmp_path, monkeypatch):
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

    assert manifest["status"] == "auto_bounded_live_blocked"
    assert manifest["runtime_change"] is False
    assert manifest["source_phase_auto_apply_blocked"] is True
    assert manifest["warnings"] == ["intraday_source_phase_auto_apply_blocked"]
    assert manifest["auto_apply_decisions"] == []
    assert manifest["runtime_env_overrides"] == {}
    assert not (runtime_dir / "threshold_runtime_env_2026-05-18.env").exists()


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


def test_scalp_sim_candidate_window_operator_lock_applies_240_daily_quota(tmp_path, monkeypatch):
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

    (report_dir / "threshold_cycle_2026-05-29.json").write_text(
        json.dumps({"date": "2026-05-29", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (lock_dir / "scalp_sim_candidate_window_expansion_2026-05-19.json").write_text(
        json.dumps(
            {
                "lock_id": "scalp_sim_candidate_window_expansion_continuous_2026-05-19",
                "enabled": True,
                "family": "scalp_sim_candidate_window_expansion",
                "stage": "sim_entry_candidate_window",
                "active_from_date": "2026-05-19",
                "env_overrides": {
                    "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED": "true",
                    "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY": "240",
                    "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY": (
                        "09:00-10:00=84,10:00-12:00=48,12:00-14:00=60,14:00-15:30=48"
                    ),
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-29",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    decision = [
        item
        for item in manifest["auto_apply_decisions"]
        if item["family"] == "scalp_sim_candidate_window_expansion"
    ][0]
    assert decision["selected"] is True
    assert decision["operator_runtime_env_lock"]["applied"] is True
    env = manifest["runtime_env_overrides"]
    assert env["KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY"] == "240"
    assert env["KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY"] == (
        "09:00-10:00=84,10:00-12:00=48,12:00-14:00=60,14:00-15:30=48"
    )


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
    assert "real_canary_policy" not in manifest["swing_runtime_approval"]
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_FLOOR_BULL"] == "0.3"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"] == "true"
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SWING_FLOOR_BULL=0.3" in env_text
    assert "KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true" in env_text


def test_swing_scale_in_real_canary_auto_approves_without_separate_artifact(tmp_path, monkeypatch):
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
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
                        "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                        "target_env_keys": [
                            "SWING_SCALE_IN_REAL_CANARY_ENABLED",
                            "SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_QTY",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION",
                            "SWING_SCALE_IN_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT",
                        ],
                        "current_values": {"enabled": False},
                        "recommended_values": {
                            "enabled": True,
                            "max_order_qty": 1,
                            "max_orders_per_day": 1,
                            "max_orders_per_position": 1,
                            "require_approval_artifact": False,
                        },
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
    assert manifest["swing_runtime_approval"]["legacy_phase0_real_canary_ignored"] is True
    assert (
        "blocked_legacy_real_canary_removed:swing_scale_in_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    assert manifest["swing_runtime_approval"]["approved"] == 0
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY" not in env_text


def test_swing_one_share_real_canary_auto_approves_without_separate_artifact(tmp_path, monkeypatch):
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
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
                        "target_env_keys": [
                            "SWING_ONE_SHARE_REAL_CANARY_ENABLED",
                            "SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_QTY",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS",
                            "SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW",
                            "SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT",
                        ],
                        "current_values": {"enabled": False},
                        "recommended_values": {
                            "enabled": True,
                            "allowed_codes": "123456",
                            "max_order_qty": 1,
                            "max_new_entries_per_day": 1,
                            "max_open_positions": 3,
                            "max_total_notional_krw": 300000,
                            "require_approval_artifact": False,
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

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-11",
        source_date="2026-05-08",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert manifest["swing_runtime_approval"]["legacy_phase0_real_canary_ignored"] is True
    assert (
        "blocked_legacy_real_canary_removed:swing_one_share_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    assert manifest["swing_runtime_approval"]["approved"] == 0
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY" not in env_text


def test_swing_scale_in_real_canary_rejects_qty_cap_above_phase0(tmp_path, monkeypatch):
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
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
                        "allowed_actions": ["PYRAMID", "AVG_DOWN"],
                        "target_env_keys": [
                            "SWING_SCALE_IN_REAL_CANARY_ENABLED",
                            "SWING_SCALE_IN_REAL_CANARY_MAX_QTY",
                        ],
                        "recommended_values": {"enabled": True, "max_order_qty": 2},
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
    assert (
        "blocked_legacy_real_canary_removed:swing_scale_in_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_ENABLED" not in env_text


def test_swing_real_canary_does_not_auto_apply_without_auto_approval_state(tmp_path, monkeypatch):
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
                        "calibration_state": "approval_required",
                        "target_env_keys": [
                            "SWING_ONE_SHARE_REAL_CANARY_ENABLED",
                            "SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES",
                        ],
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
    assert (
        "blocked_legacy_real_canary_removed:swing_one_share_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-11.env").read_text(encoding="utf-8")
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
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
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

    assert manifest["runtime_change"] is False
    assert manifest["runtime_env_overrides"] == {}
    assert manifest["swing_runtime_approval"]["legacy_phase0_real_canary_ignored"] is True
    assert (
        "blocked_legacy_real_canary_removed:swing_one_share_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    assert manifest["swing_runtime_approval"]["selected"] == []


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
                        "calibration_state": "auto_approved_real_canary",
                        "auto_approved_real_canary": True,
                        "auto_approval_state": "real_canary_phase0_auto_approved",
                        "auto_promotion_contract": _bounded_real_canary_tier2_contract(),
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

    assert manifest["runtime_change"] is False
    assert manifest["runtime_env_overrides"] == {}
    assert manifest["swing_runtime_approval"]["legacy_phase0_real_canary_ignored"] is True
    assert (
        "blocked_legacy_real_canary_removed:swing_scale_in_real_canary:2026-05-08:phase0"
        in manifest["swing_runtime_approval"]["blocked"]
    )
    assert manifest["swing_runtime_approval"]["selected"] == []


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
                "approval_state": "sim_auto_approved",
                "human_approval_required": False,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "source_quality_status": "pass",
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
    assert manifest["scalp_sim_scale_in_window_approval"]["decisions"][0]["decision_reason"] == (
        "sim_auto_approval_artifact_accepted"
    )
    assert manifest["calibration_candidates"] == []


def test_scalp_sim_scale_in_window_artifact_is_sim_auto_approved(tmp_path, monkeypatch):
    approval_dir = tmp_path / "approvals"
    report_dir = tmp_path / "lifecycle_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(scale_in_approval_mod, "APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scale_in_approval_mod, "REPORT_DIR", report_dir)

    (report_dir / "lifecycle_decision_matrix_2026-05-22.json").write_text(
        json.dumps(
            {
                "summary": {"status": "pass"},
                "sources": {"scalp_sim_scale_in": {"rows": 3, "filled_events": 1, "unfilled_events": 2}},
                "policy_entries": [
                    {
                        "stage": "scale_in",
                        "sample": 3,
                        "joined_sample": 3,
                        "source_quality_gate": "hold_sample",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    artifact = scale_in_approval_mod.build_scalp_sim_scale_in_window_approval("2026-05-22")

    assert artifact["approved"] is True
    assert artifact["approval_state"] == "sim_auto_approved"
    assert artifact["human_approval_required"] is False
    assert artifact["decision_authority"] == "sim_auto_approval_only"
    assert artifact["runtime_effect"] is False
    assert artifact["allowed_runtime_apply"] is True
    assert artifact["actual_order_submitted"] is False
    assert artifact["broker_order_forbidden"] is True
    assert artifact["source_quality_status"] == "pass"
    assert artifact["blocked_reasons"] == []
    assert artifact["approval_contract"]["operator_action"] == "none_required_for_sim_policy"
    saved = json.loads(
        (approval_dir / "scalp_sim_scale_in_window_expansion_2026-05-22.json").read_text(encoding="utf-8")
    )
    assert saved["approval_state"] == "sim_auto_approved"


def test_scalp_sim_scale_in_window_artifact_blocks_missing_source_report(tmp_path, monkeypatch):
    approval_dir = tmp_path / "approvals"
    report_dir = tmp_path / "lifecycle_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(scale_in_approval_mod, "APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scale_in_approval_mod, "REPORT_DIR", report_dir)

    artifact = scale_in_approval_mod.build_scalp_sim_scale_in_window_approval("2026-05-22")

    assert artifact["approved"] is False
    assert artifact["approval_state"] == "source_quality_blocked"
    assert artifact["source_quality_status"] == "source_report_missing"
    assert artifact["blocked_reasons"] == ["source_report_missing"]


def test_scalp_sim_scale_in_window_artifact_blocks_unreadable_source_report(tmp_path, monkeypatch):
    approval_dir = tmp_path / "approvals"
    report_dir = tmp_path / "lifecycle_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(scale_in_approval_mod, "APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scale_in_approval_mod, "REPORT_DIR", report_dir)
    (report_dir / "lifecycle_decision_matrix_2026-05-22.json").write_text("{not-json", encoding="utf-8")

    artifact = scale_in_approval_mod.build_scalp_sim_scale_in_window_approval("2026-05-22")

    assert artifact["approved"] is False
    assert artifact["approval_state"] == "source_quality_blocked"
    assert artifact["source_quality_status"] == "source_report_unreadable"
    assert artifact["blocked_reasons"] == ["source_report_unreadable"]


def test_scalp_sim_scale_in_window_preopen_rejects_source_quality_blocked_artifact(tmp_path, monkeypatch):
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

    (report_dir / "threshold_cycle_2026-05-22.json").write_text(
        json.dumps({"date": "2026-05-22", "calibration_candidates": []}),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_scale_in_window_expansion_2026-05-22.json").write_text(
        json.dumps(
            {
                "policy_id": "scalp_sim_scale_in_window_expansion",
                "family": "scalp_sim_scale_in_window_expansion",
                "approved": False,
                "approval_state": "source_quality_blocked",
                "human_approval_required": False,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "source_quality_status": "source_report_missing",
                "target_env_keys": ["SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"],
                "recommended_values": {"enabled": True},
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-26",
        source_date="2026-05-22",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_env_overrides"].get("KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED") is None
    assert manifest["scalp_sim_scale_in_window_approval"]["selected"] == []
    assert "sim_auto_approval_not_approved" in manifest["scalp_sim_scale_in_window_approval"]["blocked"]


def _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    approval_dir = tmp_path / "sim_auto_approvals"
    policy_dir = tmp_path / "scalp_sim_policies"
    legacy_approval_dir = tmp_path / "approvals"
    for directory in (report_dir, approval_dir, policy_dir, legacy_approval_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", legacy_approval_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", tmp_path / "latency")
    monkeypatch.setattr(scalp_sim_auto_mod, "SIM_AUTO_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(scalp_sim_auto_mod, "SCALP_SIM_POLICY_DIR", policy_dir)
    (report_dir / "threshold_cycle_2026-05-26.json").write_text(
        json.dumps({"date": "2026-05-26", "calibration_candidates": []}),
        encoding="utf-8",
    )
    return runtime_dir, approval_dir, policy_dir, legacy_approval_dir


def test_scalp_sim_auto_approval_writes_sim_policy_env(tmp_path, monkeypatch):
    runtime_dir, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch)
    catalog_path = policy_dir / "scalp_sim_policy_catalog_2026-05-26.json"
    catalog_path.write_text(json.dumps({"schema_version": "scalp_sim_policy_catalog_v1"}), encoding="utf-8")
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"],
                "approved_policy_count": 2,
                "approved_policies": [
                    {
                        "policy_id": "scalp_sim_scale_in_window_expansion",
                        "target_env_keys": ["SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED"] == "true"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE"] == str(catalog_path)
    assert (
        manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_VERSION"]
        == "scalp_sim_auto_approval:2026-05-26"
    )
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED"] == "true"
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"] == "true"
    assert manifest["scalp_sim_auto_approval"]["selected"][0]["family"] == "scalp_sim_auto_approval"
    assert manifest["scalp_sim_scale_in_window_approval"]["selected"] == []
    assert manifest["lifecycle_bucket_discovery"]["selected"] == []
    env_text = (runtime_dir / "threshold_runtime_env_2026-05-27.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED=true" in env_text


def test_scalp_sim_auto_approval_missing_keeps_legacy_scale_in_fallback(tmp_path, monkeypatch):
    _, _, _, legacy_approval_dir = _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch)
    (legacy_approval_dir / "scalp_sim_scale_in_window_expansion_2026-05-26.json").write_text(
        json.dumps(
            {
                "policy_id": "scalp_sim_scale_in_window_expansion",
                "family": "scalp_sim_scale_in_window_expansion",
                "approved": True,
                "approval_state": "sim_auto_approved",
                "human_approval_required": False,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "source_quality_status": "pass",
                "target_env_keys": ["SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"],
                "recommended_values": {"enabled": True},
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert manifest["scalp_sim_scale_in_window_approval"]["selected"][0]["family"] == (
        "scalp_sim_scale_in_window_expansion"
    )
    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"] == "true"


def test_scalp_sim_auto_approval_blocked_does_not_write_env(tmp_path, monkeypatch):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch)
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text("{}", encoding="utf-8")
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED" not in manifest["runtime_env_overrides"]


def test_scalp_sim_auto_approval_rejects_empty_policy_artifact(tmp_path, monkeypatch):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch)
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps({"schema_version": "scalp_sim_policy_catalog_v1"}),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": [],
                "approved_policy_count": 0,
                "approved_policies": [],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert "scalp_sim_auto_approval_empty" in manifest["scalp_sim_auto_approval"]["blocked"]
    assert "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED" not in manifest["runtime_env_overrides"]


def test_scalp_sim_auto_approval_rejects_active_priority_posterior_prefix(tmp_path, monkeypatch):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch)
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_bad",
                        "source_parent_bucket_id": "parent_positive",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_watch_recovery",
                            "entry_source_parent": "entry_source_action_decision",
                            "exit_outcome_parent": "posterior_positive",
                        },
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["lifecycle_bucket_discovery"],
                "approved_policy_count": 1,
                "approved_policies": [
                    {
                        "policy_id": "scalp_sim_candidate_window_expansion",
                        "target_env_keys": ["SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert "active_sim_priority_seed_observable_prefix_forbidden_dimension" in manifest["scalp_sim_auto_approval"]["blocked"]
    assert "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED" not in manifest["runtime_env_overrides"]


def test_scalp_sim_auto_approval_rejects_malformed_policy_count(tmp_path, monkeypatch):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch)
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps({"schema_version": "scalp_sim_policy_catalog_v1"}),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["scalp_sim_scale_in_window_approval"],
                "approved_policy_count": "not-a-number",
                "approved_policies": [
                    {
                        "policy_id": "scalp_sim_scale_in_window_expansion",
                        "target_env_keys": ["SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["scalp_sim_auto_approval"]["selected"] == []
    assert "scalp_sim_auto_approval_empty" in manifest["scalp_sim_auto_approval"]["blocked"]


def test_scalp_sim_auto_approval_ignores_non_scalp_nested_env_keys(tmp_path, monkeypatch):
    _, approval_dir, policy_dir, _ = _install_scalp_sim_auto_test_dirs(tmp_path, monkeypatch)
    (policy_dir / "scalp_sim_policy_catalog_2026-05-26.json").write_text(
        json.dumps({"schema_version": "scalp_sim_policy_catalog_v1"}),
        encoding="utf-8",
    )
    (approval_dir / "scalp_sim_auto_approval_2026-05-26.json").write_text(
        json.dumps(
            {
                "report_type": "scalp_sim_auto_approval",
                "approved": True,
                "human_approval_required": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "scalp_sim_auto_approval_control_tower",
                "approved_source_ids": ["scalp_sim_scale_in_window_approval"],
                "approved_policy_count": 1,
                "approved_policies": [
                    {
                        "policy_id": "scalp_sim_scale_in_window_expansion",
                        "target_env_keys": [
                            "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED",
                            "SWING_ONE_SHARE_REAL_CANARY_ENABLED",
                        ],
                        "recommended_values": {"enabled": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-05-27",
        source_date="2026-05-26",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_env_overrides"]["KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"] == "true"
    assert "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED" not in manifest["runtime_env_overrides"]


def _install_runtime_bridge_test_dirs(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    apply_dir = tmp_path / "apply_plans"
    runtime_dir = tmp_path / "runtime_env"
    bridge_dir = tmp_path / "runtime_apply_bridge"
    approval_dir = tmp_path / "approvals"
    swing_request_dir = tmp_path / "swing_runtime_approval"
    lock_dir = tmp_path / "operator_runtime_env_locks"
    for directory in (report_dir, bridge_dir, approval_dir, swing_request_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    monkeypatch.setattr(mod, "RUNTIME_ENV_DIR", runtime_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_REPORT_DIR", swing_request_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)
    monkeypatch.setattr(mod, "LATENCY_CLASSIFIER_RECOMMENDATION_DIR", tmp_path / "latency")
    monkeypatch.setattr(mod, "OPERATOR_RUNTIME_ENV_LOCK_DIR", lock_dir)
    monkeypatch.setattr(bridge_mod, "REPORT_DIR", bridge_dir)
    monkeypatch.setattr(bridge_mod, "APPROVAL_DIR", approval_dir)
    (report_dir / "threshold_cycle_2026-05-30.json").write_text(
        json.dumps({"date": "2026-05-30", "calibration_candidates": []}),
        encoding="utf-8",
    )
    return runtime_dir, bridge_dir, approval_dir


def test_runtime_apply_bridge_entry_requires_ready_state_and_artifact(tmp_path, monkeypatch):
    runtime_dir, bridge_dir, approval_dir = _install_runtime_bridge_test_dirs(tmp_path, monkeypatch)
    family = bridge_mod.ENTRY_BRIDGE_FAMILY
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "entry",
                        "priority": 9,
                        "bridge_candidate_state": "bootstrap_pending",
                        "allowed_runtime_apply": False,
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                        "current_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "ldm_entry_runtime_bridge_2026-05-30.json").write_text(
        json.dumps({"approved": True, "family": family, "candidate_id": candidate_id}),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert f"runtime_apply_blocked_bridge_not_ready:bootstrap_pending:{family}" in manifest["runtime_apply_bridge"]["blocked"]
    env_text = (runtime_dir / "threshold_runtime_env_2026-06-01.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env_text


def test_runtime_apply_bridge_entry_wait6579_live_auto_writes_probe_env(tmp_path, monkeypatch):
    runtime_dir, bridge_dir, approval_dir = _install_runtime_bridge_test_dirs(tmp_path, monkeypatch)
    family = bridge_mod.ENTRY_BRIDGE_FAMILY
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "entry",
                        "priority": 9,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "bounded_entry_probe_recovery_live_auto",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "auto_promotion_contract": {"tier2_status": "parsed", "tier2_policy": "fail_closed"},
                        "target_env_keys": [
                            "AI_SCORE65_74_RECOVERY_PROBE_ENABLED",
                            "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE",
                            "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE",
                            "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW",
                            "AI_WAIT6579_PROBE_CANARY_MAX_QTY",
                            "AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "min_score": 66,
                            "max_score": 69,
                            "max_budget_krw": 50000,
                            "max_qty": 1,
                            "threshold_version": candidate_id,
                        },
                        "current_values": {
                            "enabled": False,
                            "min_score": 65,
                            "max_score": 74,
                            "max_budget_krw": 50000,
                            "max_qty": 1,
                            "threshold_version": "runtime_default",
                        },
                        "source_bucket_keys": [bridge_mod.ENTRY_TARGET_BUCKET_KEY],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    env = manifest["runtime_env_overrides"]
    assert manifest["runtime_change"] is True
    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE"] == "66"
    assert env["KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MAX_SCORE"] == "69"
    assert manifest["runtime_apply_bridge"]["selected"][0]["family"] == family
    env_manifest = json.loads((runtime_dir / "threshold_runtime_env_2026-06-01.json").read_text(encoding="utf-8"))
    assert family in env_manifest["selected_families"]


def test_runtime_apply_bridge_greenfield_live_auto_writes_full_lifecycle_env(tmp_path, monkeypatch):
    runtime_dir, bridge_dir, _approval_dir = _install_runtime_bridge_test_dirs(tmp_path, monkeypatch)
    family = bridge_mod.GREENFIELD_REAL_ENV_FAMILY
    policy_file = tmp_path / "greenfield_real_env_policy_2026-05-30.json"
    candidate_id = f"{family}:2026-05-30"
    policy_file.write_text(
        json.dumps(
            {
                "policy_id": family,
                "policy_version": candidate_id,
                "scope": "full_lifecycle",
                "allowlist": [
                    {
                        "bucket_id": "entry:score_66_69",
                        "family": bridge_mod.ENTRY_BRIDGE_FAMILY,
                        "stage": "entry",
                        "action": "BUY",
                        "source_quality_gate": "pass",
                        "ai_tier2_status": "parsed",
                    },
                    {
                        "bucket_id": "submit:allow_submit:thin_ok",
                        "family": "submit_bucket_runtime_policy_v1",
                        "stage": "submit",
                        "action": "ALLOW_SUBMIT",
                        "source_quality_gate": "pass",
                        "ai_tier2_status": "parsed",
                    },
                    {
                        "bucket_id": "holding:flow:baseline_hold",
                        "family": "holding_bucket_runtime_policy_v1",
                        "stage": "holding",
                        "action": "HOLD",
                        "source_quality_gate": "pass",
                        "ai_tier2_status": "parsed",
                    },
                    {
                        "bucket_id": "exit:rule:baseline_exit",
                        "family": "exit_bucket_runtime_policy_v1",
                        "stage": "exit",
                        "action": "SELL",
                        "source_quality_gate": "pass",
                        "ai_tier2_status": "parsed",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "greenfield_real_env",
                        "priority": 7,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "full_lifecycle_greenfield_real_env_authority",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "target_env_keys": [
                            "GREENFIELD_REAL_ENV_AUTHORITY_ENABLED",
                            "GREENFIELD_REAL_ENV_AUTHORITY_SCOPE",
                            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE",
                            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION",
                            "GREENFIELD_REAL_ENV_TELEGRAM_ENABLED",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "scope": "full_lifecycle",
                            "policy_file": str(policy_file),
                            "policy_version": candidate_id,
                            "telegram_enabled": True,
                        },
                        "current_values": {
                            "enabled": False,
                            "scope": "inactive",
                            "policy_file": "",
                            "policy_version": "runtime_default",
                            "telegram_enabled": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    env = manifest["runtime_env_overrides"]
    assert manifest["runtime_change"] is True
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_ENABLED"] == "true"
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_SCOPE"] == "full_lifecycle"
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE"] == str(policy_file)
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION"] == candidate_id
    assert env["KORSTOCKSCAN_GREENFIELD_REAL_ENV_TELEGRAM_ENABLED"] == "true"
    env_manifest = json.loads((runtime_dir / "threshold_runtime_env_2026-06-01.json").read_text(encoding="utf-8"))
    assert family in env_manifest["selected_families"]


def test_runtime_apply_bridge_greenfield_blocks_missing_policy_file(tmp_path, monkeypatch):
    _runtime_dir, bridge_dir, _approval_dir = _install_runtime_bridge_test_dirs(tmp_path, monkeypatch)
    family = bridge_mod.GREENFIELD_REAL_ENV_FAMILY
    policy_file = tmp_path / "missing_greenfield_real_env_policy_2026-05-30.json"
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "greenfield_real_env",
                        "priority": 7,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "full_lifecycle_greenfield_real_env_authority",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "target_env_keys": [
                            "GREENFIELD_REAL_ENV_AUTHORITY_ENABLED",
                            "GREENFIELD_REAL_ENV_AUTHORITY_SCOPE",
                            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE",
                            "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION",
                            "GREENFIELD_REAL_ENV_TELEGRAM_ENABLED",
                        ],
                        "recommended_values": {
                            "enabled": True,
                            "scope": "full_lifecycle",
                            "policy_file": str(policy_file),
                            "policy_version": candidate_id,
                            "telegram_enabled": True,
                        },
                        "current_values": {
                            "enabled": False,
                            "scope": "inactive",
                            "policy_file": "",
                            "policy_version": "runtime_default",
                            "telegram_enabled": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_ENABLED" not in manifest["runtime_env_overrides"]
    assert f"greenfield_policy_file_missing:{family}" in manifest["runtime_apply_bridge"]["blocked"]


def test_runtime_apply_bridge_legacy_ready_for_approval_is_blocked(tmp_path, monkeypatch):
    runtime_dir, bridge_dir, approval_dir = _install_runtime_bridge_test_dirs(tmp_path, monkeypatch)
    family = bridge_mod.ENTRY_BRIDGE_FAMILY
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "entry",
                        "priority": 9,
                        "bridge_candidate_state": "ready_for_approval",
                        "allowed_runtime_apply": True,
                        "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                        "recommended_values": {"enabled": True},
                        "current_values": {"enabled": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (approval_dir / "ldm_entry_runtime_bridge_2026-05-30.json").write_text(
        json.dumps({"approved": True, "family": family, "candidate_id": candidate_id, "approval_id": "entry-approve"}),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    assert manifest["runtime_change"] is False
    assert f"runtime_apply_blocked_bridge_not_ready:ready_for_approval:{family}" in manifest["runtime_apply_bridge"]["blocked"]
    env_text = (runtime_dir / "threshold_runtime_env_2026-06-01.env").read_text(encoding="utf-8")
    assert "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED" not in env_text


def test_runtime_apply_bridge_scale_live_auto_writes_tighten_env_without_guard_bypass(tmp_path, monkeypatch):
    _runtime_dir, bridge_dir, approval_dir = _install_runtime_bridge_test_dirs(tmp_path, monkeypatch)
    family = bridge_mod.SCALE_IN_BRIDGE_FAMILY
    candidate_id = f"{family}:2026-05-30"
    (bridge_dir / "runtime_apply_bridge_2026-05-30.json").write_text(
        json.dumps(
            {
                "date": "2026-05-30",
                "candidates": [
                    {
                        "candidate_id": candidate_id,
                        "family": family,
                        "stage": "scale_in",
                        "priority": 39,
                        "bridge_candidate_state": "live_auto_apply_ready",
                        "approval_required": False,
                        "live_auto_apply": True,
                        "allowed_runtime_apply": True,
                        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten_live_auto",
                        "lifecycle_bucket_discovery_ai_review_status": "parsed",
                        "auto_promotion_contract": {"tier2_status": "parsed", "tier2_policy": "fail_closed"},
                        "target_env_keys": [
                            "SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP",
                            "SCALPING_ENABLE_PYRAMID",
                            "REVERSAL_ADD_MIN_AI_SCORE",
                            "REVERSAL_ADD_MIN_BUY_PRESSURE",
                            "REVERSAL_ADD_MIN_TICK_ACCEL",
                        ],
                        "recommended_values": {
                            "effective_qty_cap": 1,
                            "scalping_enable_pyramid": False,
                            "reversal_add_min_ai_score": 65,
                            "reversal_add_min_buy_pressure": 60.0,
                            "reversal_add_min_tick_accel": 1.05,
                        },
                        "current_values": {
                            "effective_qty_cap": 1,
                            "scalping_enable_pyramid": True,
                            "reversal_add_min_ai_score": 60,
                            "reversal_add_min_buy_pressure": 55.0,
                            "reversal_add_min_tick_accel": 0.95,
                        },
                        "forbidden_uses": ["scale_in_safety_guard_bypass", "position_cap_release"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = mod.build_preopen_apply_manifest(
        "2026-06-01",
        source_date="2026-05-30",
        apply_mode="auto_bounded_live",
        auto_apply=True,
        require_ai=False,
    )

    env = manifest["runtime_env_overrides"]
    assert manifest["runtime_change"] is True
    assert env["KORSTOCKSCAN_SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP"] == "1"
    assert env["KORSTOCKSCAN_SCALPING_ENABLE_PYRAMID"] == "false"
    assert env["KORSTOCKSCAN_REVERSAL_ADD_MIN_AI_SCORE"] == "65"
    assert env["KORSTOCKSCAN_REVERSAL_ADD_MIN_BUY_PRESSURE"] == "60"
    assert env["KORSTOCKSCAN_REVERSAL_ADD_MIN_TICK_ACCEL"] == "1.05"
    assert "scale_in_safety_guard_bypass" in manifest["runtime_apply_bridge"]["selected"][0]["forbidden_uses"]
