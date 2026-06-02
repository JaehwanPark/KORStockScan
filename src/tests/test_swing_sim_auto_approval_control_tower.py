from __future__ import annotations

import json

from src.engine.swing import sim_auto_approval_control_tower as mod


def _swing_discovery() -> dict:
    return {
        "report_type": "swing_lifecycle_bucket_discovery",
        "date": "2026-05-22",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "sim_auto_approved_candidates": [
            {
                "bucket_id": "swing_bucket_entry_combo_probe",
                "lifecycle_stage": "entry",
                "bucket_type": "combo_entry_spot",
                "bucket_key": "probe",
                "source_quality_adjusted_ev_pct": 1.4,
            }
        ],
    }


def _bottom_policy() -> dict:
    return {
        "report_type": "swing_bottom_rebound_policy_auto_loop",
        "date": "2026-05-22",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "final_conclusion": {"classification_state": "sim_auto_approved", "promote_policy": True},
        "sim_auto_approved_policy": {
            "policy_version": "bottom_rebound_swing_source_v2",
            "max_candidates": 40,
            "min_backtest_rank_score": 2.5,
            "min_primary_adjusted_ev_pct": 0.1,
        },
    }


def _runtime_policy() -> dict:
    return {
        "report_type": "swing_runtime_approval",
        "date": "2026-05-22",
        "approval_requests": [
            {
                "approval_id": "swing_runtime_approval:2026-05-22:swing_model_floor",
                "family": "swing_model_floor",
                "stage": "selection",
                "calibration_state": "dry_run_auto_apply_ready",
                "auto_approval_state": "ai_tier2_auto_approved",
                "tradeoff_score": 0.72,
                "sample_count": 30,
                "sample_floor": 20,
                "auto_promotion_contract": {
                    "state": "dry_run_auto_apply_ready",
                    "tier2_status": "parsed",
                    "tier2_policy": "fail_closed",
                    "tier2_fail_closed": False,
                    "final_user_approval_boundary": "full_live_only",
                },
            },
            {
                "approval_id": "swing_one_share_real_canary:2026-05-22:phase0",
                "family": "swing_one_share_real_canary_phase0",
                "stage": "real_canary_entry",
                "calibration_state": "auto_approved_real_canary",
                "auto_approval_state": "real_canary_phase0_auto_approved",
                "auto_promotion_contract": {
                    "state": "bounded_real_canary_auto_approved",
                    "tier2_status": "parsed",
                    "tier2_policy": "fail_closed",
                    "tier2_fail_closed": False,
                    "final_user_approval_boundary": "full_live_only",
                },
            },
        ],
    }


def test_control_tower_merges_swing_ldm_and_bottom_rebound_sources() -> None:
    approval = mod.build_swing_sim_auto_approval(
        "2026-05-22",
        swing_lifecycle_bucket_report=_swing_discovery(),
        bottom_rebound_policy_report=_bottom_policy(),
        swing_runtime_approval_report=_runtime_policy(),
        swing_strategy_discovery_ev_report={},
    )

    assert approval["approved"] is True
    assert approval["approved_policy_count"] == 3
    assert approval["approved_source_ids"] == [
        "bottom_rebound_policy_auto_loop",
        "swing_lifecycle_bucket_discovery",
        "swing_runtime_approval",
        "swing_strategy_discovery_ev",
    ]
    assert approval["final_user_approval_boundary"] == "full_live_only"
    assert approval["runtime_effect"] is False
    assert approval["actual_order_submitted"] is False
    assert approval["broker_order_forbidden"] is True
    assert approval["allowed_runtime_apply"] is False
    assert mod.bottom_rebound_is_approved_by_control_tower(approval) is True
    bucket_priority = next(
        item
        for item in approval["active_arm_priority_policies"]
        if item.get("priority_bucket_id") == "swing_bucket_entry_combo_probe"
    )
    assert bucket_priority["priority_source"] == "sim_auto_approved_candidates"
    assert bucket_priority["status"] == "active"
    assert bucket_priority["actual_order_submitted"] is False
    assert bucket_priority["broker_order_forbidden"] is True
    assert {item["policy_kind"] for item in approval["approved_policies"]} >= {
        "swing_runtime_dry_run_pre_final_policy",
    }
    assert "swing_bounded_real_canary_pre_final_policy" not in {
        item["policy_kind"] for item in approval["approved_policies"]
    }
    assert all(
        (item.get("auto_promotion_contract") or {}).get("tier2_status") == "parsed"
        for item in approval["approved_policies"]
        if item.get("source_id") == "swing_runtime_approval"
    )


def test_active_arm_priority_missing_uses_two_day_cooldown_and_five_day_retire(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "SWING_SIM_POLICY_DIR", tmp_path)
    previous = {
        "priority_policy_id": "priority_arm05",
        "priority_arm_id": "arm05_breakout_conf_trailing",
        "source_report_date": "2026-05-31",
        "status": "active",
        "consecutive_missing_count": 0,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    tmp_path.joinpath("swing_sim_policy_catalog_2026-05-31.json").write_text(
        json.dumps({"active_arm_priority_policies": [previous]}),
        encoding="utf-8",
    )

    first_missing = mod._active_arm_priority_policies({}, "2026-06-01")
    assert first_missing[0]["status"] == "active"
    assert first_missing[0]["consecutive_missing_count"] == 1

    previous["consecutive_missing_count"] = 1
    tmp_path.joinpath("swing_sim_policy_catalog_2026-05-31.json").write_text(
        json.dumps({"active_arm_priority_policies": [previous]}),
        encoding="utf-8",
    )
    second_missing = mod._active_arm_priority_policies({}, "2026-06-01")
    assert second_missing[0]["status"] == "cooldown"

    previous["consecutive_missing_count"] = 4
    tmp_path.joinpath("swing_sim_policy_catalog_2026-05-31.json").write_text(
        json.dumps({"active_arm_priority_policies": [previous]}),
        encoding="utf-8",
    )
    retired = mod._active_arm_priority_policies({}, "2026-06-01")
    assert retired[0]["status"] == "retired"
    assert retired[0]["retired_reason"] == "consecutive_missing"

    previous["status"] = "cooldown"
    previous["consecutive_missing_count"] = 0
    tmp_path.joinpath("swing_sim_policy_catalog_2026-05-31.json").write_text(
        json.dumps({"active_arm_priority_policies": [previous]}),
        encoding="utf-8",
    )
    cooldown_missing = mod._active_arm_priority_policies({}, "2026-06-01")
    assert cooldown_missing[0]["status"] == "cooldown"
    assert cooldown_missing[0]["consecutive_missing_count"] == 1

    recovered = mod._active_arm_priority_policies(
        {
            "report_type": "swing_strategy_discovery_ev",
            "date": "2026-06-01",
            "surviving_arms": [{"arm_id": "arm05_breakout_conf_trailing"}],
        },
        "2026-06-01",
    )
    assert recovered[0]["status"] == "active"
    assert recovered[0].get("consecutive_missing_count") is None


def test_control_tower_blocks_runtime_pre_final_when_tier2_missing() -> None:
    runtime_policy = _runtime_policy()
    for request in runtime_policy["approval_requests"]:
        request.pop("auto_promotion_contract", None)

    approval = mod.build_swing_sim_auto_approval(
        "2026-05-22",
        swing_lifecycle_bucket_report=_swing_discovery(),
        bottom_rebound_policy_report=_bottom_policy(),
        swing_runtime_approval_report=runtime_policy,
        swing_strategy_discovery_ev_report={},
    )

    assert approval["approved"] is True
    assert approval["approved_policy_count"] == 2
    assert approval["approved_source_ids"] == [
        "bottom_rebound_policy_auto_loop",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
    ]
    assert "swing_runtime_approval" not in approval["approved_source_ids"]
    assert not [
        item
        for item in approval["approved_policies"]
        if str(item.get("policy_kind") or "").startswith("swing_runtime_")
    ]


def test_control_tower_writes_approval_and_catalog(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", tmp_path / "approvals")
    monkeypatch.setattr(mod, "SWING_SIM_POLICY_DIR", tmp_path / "policies")

    approval = mod.build_swing_sim_auto_approval(
        "2026-05-22",
        swing_lifecycle_bucket_report=_swing_discovery(),
        bottom_rebound_policy_report=_bottom_policy(),
        swing_runtime_approval_report={},
        swing_strategy_discovery_ev_report={},
    )
    paths = mod.write_swing_sim_auto_approval(approval)

    written = json.loads(paths["approval"].read_text(encoding="utf-8"))
    catalog = json.loads(paths["catalog"].read_text(encoding="utf-8"))
    assert written["report_type"] == "swing_sim_auto_approval"
    assert catalog["schema_version"] == "swing_sim_policy_catalog_v1"
    assert len(catalog["policies"]) == 2
    assert catalog["broker_order_forbidden"] is True
