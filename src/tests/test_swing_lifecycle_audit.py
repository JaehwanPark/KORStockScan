from src.engine import swing_lifecycle_audit as mod


def test_swing_entry_bottleneck_classifies_submit_zero_with_blockers():
    bottleneck = mod.build_swing_entry_bottleneck(
        {
            "raw_counts": {
                "blocked_gatekeeper_reject": 113,
                "blocked_swing_score_vpw": 80,
                "blocked_swing_gap": 58,
            },
            "unique_record_counts": {
                "blocked_gatekeeper_reject": 11,
                "blocked_swing_score_vpw": 9,
                "blocked_swing_gap": 9,
                "swing_probe_entry_candidate": 12,
            },
            "group_unique_counts": {"entry": 15},
            "submitted_unique_records": 0,
            "simulated_order_unique_records": 20,
            "gatekeeper_actions": {"눌림 대기": 113},
            "cooldown_policies": {"pullback_wait": 113},
            "ofi_qi_summary": {
                "stale_missing_ratio": 0.91,
                "stale_missing_group_unique_record_counts": {"entry": 12},
            },
        }
    )

    assert bottleneck["primary"] == "SWING_ENTRY_DROUGHT_CRITICAL"
    assert bottleneck["operator_action_required"] is False
    assert bottleneck["runtime_effect"] is False
    assert bottleneck["allowed_runtime_apply"] is False
    assert "GATEKEEPER_PULLBACK_WAIT" in bottleneck["matches"]
    assert "SUBMIT_ZERO" in bottleneck["matches"]
    assert bottleneck["next_route"] == "code_improvement_workorder"


def test_swing_improvement_automation_adds_entry_bottleneck_order():
    audit = {
        "date": "2026-05-22",
        "model_selection": {},
        "recommendation_csv": {},
        "db_lifecycle": {},
        "recommendation_db_load": {},
        "lifecycle_events": {
            "raw_counts": {},
            "unique_record_counts": {"blocked_gatekeeper_reject": 11},
            "group_unique_counts": {"entry": 15, "scale_in": 1},
            "ofi_qi_summary": {},
            "scale_in_observation": {"post_add_outcomes": {"observed": 1}},
            "ai_contract_metrics": {},
        },
        "swing_entry_bottleneck": {
            "primary": "SWING_ENTRY_DROUGHT_CRITICAL",
            "matches": ["GATEKEEPER_PULLBACK_WAIT", "SUBMIT_ZERO"],
            "counts": {
                "entry_unique": 15,
                "submitted_unique_records": 0,
                "blocker_unique_total": 11,
            },
            "ratios": {"probe_to_blocked_unique_pct": 0.0},
            "gatekeeper_actions": {"눌림 대기": 11},
        },
        "swing_lifecycle_contract_gaps": {"gap_count": 0, "gaps": []},
        "observation_axis_summary": {},
        "simulation_opportunity": {},
    }

    report = mod.build_swing_improvement_automation_report(audit)

    order = next(
        item
        for item in report["code_improvement_orders"]
        if item["order_id"] == "order_swing_entry_bottleneck_auto_resolution"
    )
    assert order["priority"] == 0
    assert order["decision_hint"] == "implement_now"
    assert order["mapped_family"] == "swing_gatekeeper_accept_reject"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert report["swing_entry_bottleneck"]["primary"] == "SWING_ENTRY_DROUGHT_CRITICAL"


def test_swing_improvement_automation_surfaces_downstream_contract_gap_orders():
    audit = {
        "date": "2026-05-22",
        "model_selection": {},
        "recommendation_csv": {},
        "db_lifecycle": {},
        "recommendation_db_load": {},
        "lifecycle_events": {
            "raw_counts": {},
            "unique_record_counts": {},
            "group_unique_counts": {"holding": 3, "exit": 2, "scale_in": 1},
            "ofi_qi_summary": {},
            "scale_in_observation": {},
            "ai_contract_metrics": {},
        },
        "swing_entry_bottleneck": {
            "primary": "SWING_ENTRY_BOTTLENECK_OBSERVE",
            "matches": [],
        },
        "swing_lifecycle_contract_gaps": {
            "gap_count": 2,
            "gaps": [
                {"gap_id": "SWING_HOLDING_EXIT_CONTRACT_GAP", "next_route": "code_improvement_workorder"},
                {"gap_id": "SWING_SCALE_IN_CONTRACT_GAP", "next_route": "code_improvement_workorder"},
            ],
        },
        "observation_axis_summary": {},
        "simulation_opportunity": {},
    }

    report = mod.build_swing_improvement_automation_report(audit)
    order_ids = {item["order_id"] for item in report["code_improvement_orders"]}

    assert "order_swing_holding_exit_contract_gap_review" in order_ids
    assert "order_swing_scale_in_contract_gap_review" in order_ids
    assert all(
        item["runtime_effect"] is False and item["allowed_runtime_apply"] is False
        for item in report["code_improvement_orders"]
        if item["order_id"] in {
            "order_swing_holding_exit_contract_gap_review",
            "order_swing_scale_in_contract_gap_review",
        }
    )
