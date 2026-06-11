import json
import os
from datetime import datetime
from pathlib import Path

from src.engine import verify_threshold_cycle_postclose_chain as mod


def test_source_quality_hard_block_status_fails_runtime_candidate_without_handoff():
    preflight = {
        "summary": {
            "tuning_input_allowed": False,
            "hard_blocking_contract_gap_count": 1,
            "hard_blocking_stages": ["blocked_ai_score"],
        }
    }

    status = mod._source_quality_hard_block_status(
        preflight,
        ev_report={"approval_requests": [{"family": "score65_74_recovery_probe"}]},
        runtime_summary={},
        ldm_report={},
        bridge_report={},
        workorder={"orders": []},
    )

    assert status["status"] == "fail"
    assert status["candidate_violation_sources"] == ["threshold_cycle_ev"]
    assert status["workorder_handoff_present"] is False


def test_source_quality_hard_block_status_detects_bridge_selected_alias_without_handoff():
    preflight = {
        "status": "warning",
        "tuning_input_allowed": False,
        "blocked_reason": "blocked_contract_gap",
        "hard_blocking_contract_gap_count": 1,
        "hard_blocking_stages": ["scalp_sim_duplicate_buy_signal"],
    }

    status = mod._source_quality_hard_block_status(
        preflight,
        ev_report={},
        runtime_summary={},
        ldm_report={},
        bridge_report={
            "runtime_apply_bridge": {
                "selected": [{"family": "entry_wait6579_score66_69_recovery_gate_v1"}],
                "selected_count": 1,
                "approved_requests": [{"family": "entry_wait6579_score66_69_recovery_gate_v1"}],
            }
        },
        workorder={"orders": [{"order_id": "order_observation_source_quality_hard_block_contract_gap"}]},
    )

    assert status["status"] == "fail"
    assert status["candidate_violation_sources"] == ["runtime_apply_bridge"]
    assert status["workorder_handoff_present"] is True


def test_source_quality_hard_block_status_passes_when_blocked_artifacts_handoff_only():
    preflight = {
        "summary": {
            "tuning_input_allowed": False,
            "hard_blocking_contract_gap_count": 1,
            "hard_blocking_stages": ["blocked_ai_score"],
        }
    }

    status = mod._source_quality_hard_block_status(
        preflight,
        ev_report={"status": "source_quality_blocked", "allowed_runtime_apply": False},
        runtime_summary={"status": "source_quality_blocked", "summary": {"runtime_candidate_count": 0}},
        ldm_report={"status": "source_quality_blocked", "runtime_approval_candidates": []},
        bridge_report={},
        workorder={"orders": [{"order_id": "order_observation_source_quality_hard_block_contract_gap"}]},
    )

    assert status["status"] == "pass"
    assert status["candidate_violation_sources"] == []
    assert status["workorder_handoff_present"] is True


def test_raw_row_exclusion_handoff_fails_without_producer_fix_workorder():
    status = mod._raw_row_exclusion_handoff_status(
        {
            "raw_row_exclusion": {
                "excluded_row_count": 2,
                "stage_counts": {"custom_runtime_context_stage": 2},
                "exclusion_reasons": {"required_field_missing": 2},
            }
        },
        workorder={"orders": []},
    )

    assert status["status"] == "fail"
    assert status["excluded_row_count"] == 2
    assert status["workorder_handoff_present"] is False


def test_conversion_kpi_warns_when_new_postclose_candidate_not_due_until_next_preopen():
    status, issues, warnings = mod._conversion_kpi_health(
        conversion_check_enabled=True,
        key_lineage_ledger={"summary": {}},
        conversion_lane={"summary": {"conversion_candidate_count": 1}},
        key_lineage_summary={
            "preopen_missing_count": 23,
            "new_postclose_candidates_due_state": "not_due_until_next_preopen",
        },
        conversion_lane_summary={"conversion_candidate_count": 1},
    )

    assert status == "warning"
    assert issues == []
    assert warnings == ["active_or_hypothesis_preopen_handoff_pending"]


def test_conversion_kpi_fails_when_due_preopen_candidate_is_missing():
    status, issues, warnings = mod._conversion_kpi_health(
        conversion_check_enabled=True,
        key_lineage_ledger={"summary": {}},
        conversion_lane={"summary": {"conversion_candidate_count": 1}},
        key_lineage_summary={
            "preopen_missing_count": 1,
            "new_postclose_candidates_due_state": "due_same_day",
        },
        conversion_lane_summary={"conversion_candidate_count": 1},
    )

    assert status == "fail"
    assert issues == ["active_or_hypothesis_preopen_missing"]
    assert warnings == []


def test_raw_row_exclusion_handoff_passes_with_producer_fix_workorder():
    status = mod._raw_row_exclusion_handoff_status(
        {"raw_row_exclusion": {"excluded_row_count": 1}},
        workorder={
            "orders": [
                {
                    "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "forbidden_uses": ["real_order_authority"],
                }
            ]
        },
    )

    assert status["status"] == "pass"
    assert status["workorder_handoff_present"] is True


def test_raw_row_exclusion_handoff_passes_with_limit_up_review_only_context():
    status = mod._raw_row_exclusion_handoff_status(
        {
            "raw_row_exclusion": {
                "excluded_row_count": 6,
                "stage_counts": {"blocked_overbought": 3, "blocked_strength_momentum": 3},
                "field_gap_counts": {"zero_fields:intraday_range_pct": 6},
            }
        },
        workorder={
            "orders": [],
            "non_selected_orders": [
                {
                    "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                    "improvement_type": "source_quality_raw_row_exclusion_limit_up_locked_context",
                    "route": "review_required_limit_up_locked_context",
                    "raw_row_exclusion_context_classification": "limit_up_locked_context",
                    "decision": "attach_existing_family",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            ],
        },
    )

    assert status["status"] == "pass"
    assert status["workorder_handoff_present"] is True
    assert status["review_only_context_count"] == 1


def test_raw_row_exclusion_handoff_passes_with_market_halt_review_only_context():
    status = mod._raw_row_exclusion_handoff_status(
        {
            "raw_row_exclusion": {
                "excluded_row_count": 10,
                "stage_counts": {"blocked_strength_momentum": 10},
                "field_gap_counts": {"zero_fields:intraday_range_pct": 10},
                "market_halt_or_circuit_window_overlap": True,
            }
        },
        workorder={
            "orders": [],
            "non_selected_orders": [
                {
                    "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                    "improvement_type": "source_quality_raw_row_exclusion_market_halt_context",
                    "route": "review_required_market_halt_context",
                    "raw_row_exclusion_context_classification": (
                        "market_halt_or_circuit_window_overlap"
                    ),
                    "decision": "attach_existing_family",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            ],
        },
    )

    assert status["status"] == "pass"
    assert status["workorder_handoff_present"] is True
    assert status["review_only_context_count"] == 1


def test_raw_row_exclusion_handoff_fails_when_order_is_non_selected_only():
    status = mod._raw_row_exclusion_handoff_status(
        {"raw_row_exclusion": {"excluded_row_count": 1}},
        workorder={
            "orders": [],
            "non_selected_orders": [
                {
                    "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                    "decision": "implement_now",
                    "runtime_effect": False,
                }
            ],
        },
    )

    assert status["status"] == "fail"
    assert status["workorder_handoff_present"] is False


def test_raw_row_exclusion_handoff_fails_when_safe_producer_fix_is_non_selected_only():
    status = mod._raw_row_exclusion_handoff_status(
        {"raw_row_exclusion": {"excluded_row_count": 1}},
        workorder={
            "orders": [],
            "non_selected_orders": [
                {
                    "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "forbidden_uses": ["real_order_authority"],
                }
            ],
        },
    )

    assert status["status"] == "fail"
    assert status["workorder_handoff_present"] is False


def test_raw_row_exclusion_handoff_fails_when_workorder_contract_is_not_safe_scope():
    status = mod._raw_row_exclusion_handoff_status(
        {"raw_row_exclusion": {"excluded_row_count": 1}},
        workorder={
            "orders": [
                {
                    "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                    "decision": "implement_now",
                    "runtime_effect": True,
                    "allowed_runtime_apply": False,
                    "forbidden_uses": ["real_order_authority"],
                }
            ],
        },
    )

    assert status["status"] == "fail"
    assert status["workorder_handoff_present"] is False
    assert status["invalid_contract_reasons"] == ["runtime_effect_not_false"]


def test_raw_row_exclusion_handoff_fails_without_forbidden_uses_contract():
    status = mod._raw_row_exclusion_handoff_status(
        {"raw_row_exclusion": {"excluded_row_count": 1}},
        workorder={
            "orders": [
                {
                    "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
                    "decision": "implement_now",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            ],
        },
    )

    assert status["status"] == "fail"
    assert status["workorder_handoff_present"] is False
    assert status["invalid_contract_reasons"] == ["missing_forbidden_uses_contract"]


def test_read_lines_includes_rotated_numeric_log(tmp_path):
    log_path = tmp_path / "threshold_cycle_postclose_cron.log"
    (tmp_path / "threshold_cycle_postclose_cron.log.1").write_text(
        "[START] threshold-cycle postclose target_date=2026-05-22\n"
        "[DONE] threshold-cycle postclose target_date=2026-05-22\n",
        encoding="utf-8",
    )
    log_path.write_text("", encoding="utf-8")

    lines = mod._read_lines(log_path)

    assert any("[DONE] threshold-cycle postclose target_date=2026-05-22" in line for line in lines)


def test_clean_baseline_report_residue_status_fails_pre_baseline_reports(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE", "2026-06-04")
    monkeypatch.setenv("KORSTOCKSCAN_CLEAN_TUNING_BASELINE_TS_KST", "2026-06-04T14:29:09+09:00")
    old_report = tmp_path / "threshold_cycle_ev" / "threshold_cycle_ev_2026-06-02.json"
    same_day_old_report = tmp_path / "threshold_cycle_ev" / "threshold_cycle_ev_2026-06-04.json"
    future_report = tmp_path / "threshold_cycle_ev" / "threshold_cycle_ev_2026-06-05.json"
    for path, generated_at in (
        (old_report, "2026-06-02T18:00:00+09:00"),
        (same_day_old_report, "2026-06-04T13:00:00+09:00"),
        (future_report, "2026-06-05T18:00:00+09:00"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"generated_at": generated_at}), encoding="utf-8")

    status = mod._clean_baseline_report_residue_status(tmp_path)

    assert status["status"] == "fail"
    assert status["residue_count"] == 2
    reasons = {item["reason"] for item in status["residue"]}
    assert "pre_clean_baseline_report_archive_only" in reasons
    assert "same_day_pre_clean_baseline_report_archive_only" in reasons


def test_clean_baseline_analytics_residue_status_fails_old_parquet_and_duckdb(tmp_path, monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE", "2026-06-04")
    monkeypatch.setenv("KORSTOCKSCAN_CLEAN_TUNING_BASELINE_TS_KST", "2026-06-04T14:29:09+09:00")
    old_parquet = tmp_path / "parquet" / "pipeline_events" / "date=2026-06-02" / "pipeline_events.parquet"
    new_parquet = tmp_path / "parquet" / "pipeline_events" / "date=2026-06-04" / "pipeline_events.parquet"
    duckdb_path = tmp_path / "duckdb" / "korstockscan_analytics.duckdb"
    for path in (old_parquet, new_parquet, duckdb_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    os.utime(duckdb_path, (0, 0))

    status = mod._clean_baseline_analytics_residue_status(tmp_path)

    assert status["status"] == "fail"
    assert status["residue_count"] == 2
    reasons = {item["reason"] for item in status["residue"]}
    assert "pre_clean_baseline_parquet_archive_only" in reasons
    assert "pre_clean_baseline_duckdb_archive_only" in reasons


def test_latest_run_lines_prefers_repaired_full_done_marker_after_partial_marker():
    log_lines = [
        "[START] threshold-cycle postclose target_date=2026-05-28 started_at=2026-05-28T19:30:30+0900",
        "[DONE] threshold-cycle postclose target_date=2026-05-28 swing_lifecycle=false lifecycle_decision_matrix=false lifecycle_bucket_discovery=false runtime_apply_bridge=false finished_at=2026-05-28T19:34:29+0900",
        "[START] threshold-cycle postclose target_date=2026-05-28 started_at=2026-05-29T12:35:33+0900",
        "[DONE] threshold-cycle postclose target_date=2026-05-28 swing_lifecycle=true lifecycle_decision_matrix=true lifecycle_bucket_discovery=true runtime_apply_bridge=true finished_at=2026-05-29T12:58:25+0900",
    ]

    run_lines, start_line = mod._latest_run_lines(log_lines, "2026-05-28")
    done_line = next(line for line in run_lines if "[DONE] threshold-cycle postclose" in line)

    assert "2026-05-29T12:35:33+0900" in (start_line or "")
    assert "2026-05-29T12:58:25+0900" in done_line
    assert mod._parse_bool_flags(done_line)["runtime_apply_bridge"] is True
    assert mod._parse_bool_flags(done_line)["lifecycle_bucket_discovery"] is True


def test_postclose_verifier_fails_runtime_apply_gap_audit_fail(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    (project_root / "logs").mkdir(parents=True)
    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")
    (project_root / "docs" / "checklists").mkdir(parents=True)
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# checklist\n",
        encoding="utf-8",
    )
    for label, path in mod._artifact_paths("2026-05-12").items():
        if label == "next_stage2_checklist":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"report_type": label}
        if label == "runtime_apply_gap_audit":
            payload = {
                "report_type": label,
                "status": "fail",
                "summary": {
                    "critical_failure_count": 1,
                    "ai_review_retry_pending": False,
                },
                "retry_queue": [{"failure_code": "producer_consumer_handoff_missing"}],
            }
        path.write_text(json.dumps(payload), encoding="utf-8")
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=false pattern_labs=false deepseek_swing_lab=false pattern_lab_currentness_audit=false pattern_lab_propagation_audit=false scalp_entry_adm=false lifecycle_decision_matrix=false code_improvement_workorder=false daily_ev=false runtime_approval_summary=false runtime_apply_gap_audit=true next_stage2_checklist=false finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "fail"
    assert "runtime_apply_gap_audit_failed" in report["runtime_apply_gap_audit"]["issues"]


def test_postclose_verifier_fails_stale_runtime_apply_gap_after_bridge_update(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    (project_root / "logs").mkdir(parents=True)
    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-27")
    (project_root / "docs" / "checklists").mkdir(parents=True)
    (project_root / "docs" / "checklists" / "2026-05-27-stage2-todo-checklist.md").write_text(
        "# checklist\n",
        encoding="utf-8",
    )
    for label, path in mod._artifact_paths("2026-05-26").items():
        if label == "next_stage2_checklist":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"report_type": label, "generated_at": "2026-05-26T21:00:00+09:00"}
        if label == "runtime_apply_gap_audit":
            payload = {
                "report_type": label,
                "status": "pass",
                "generated_at": "2026-05-26T21:00:00+09:00",
                "summary": {"critical_failure_count": 0, "ai_review_retry_pending": False},
                "retry_queue": [],
            }
        elif label == "runtime_apply_bridge":
            payload = {
                "report_type": label,
                "generated_at": "2026-05-26T22:00:00+09:00",
                "candidates": [],
            }
        elif label == "threshold_preopen_apply_next":
            payload = {
                "report_type": label,
                "generated_at": "2026-05-26T22:05:00+09:00",
            }
        path.write_text(json.dumps(payload), encoding="utf-8")
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-26 started_at=2026-05-26T21:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-26 swing_lifecycle=false pattern_labs=false deepseek_swing_lab=false pattern_lab_currentness_audit=false pattern_lab_propagation_audit=false scalp_entry_adm=false lifecycle_decision_matrix=false runtime_apply_bridge=true code_improvement_workorder=false daily_ev=false runtime_approval_summary=false runtime_apply_gap_audit=true next_stage2_checklist=false finished_at=2026-05-26T22:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )

    report = mod.build_threshold_cycle_postclose_verification("2026-05-26")

    assert report["status"] == "fail"
    assert "runtime_apply_gap_audit_stale_before_runtime_apply_bridge" in report["runtime_apply_gap_audit"]["issues"]
    assert "runtime_apply_gap_audit_stale_before_threshold_preopen_apply" in report["runtime_apply_gap_audit"]["issues"]


def test_overnight_bucket_handoff_status_detects_downstream_drops():
    ldm = {
        "overnight_bucket_attribution": {
            "runtime_approval_candidates": [
                {"candidate_id": "overnight_bucket_1", "bucket_type": "overnight_action", "bucket_key": "SELL_TODAY"}
            ],
            "code_improvement_workorders": [
                {"bucket_type": "overnight_status", "bucket_key": "HOLD_OVERNIGHT"}
            ],
        }
    }

    report = mod._overnight_bucket_handoff_status(ldm, {}, {}, {"orders": []})

    assert report["status"] == "fail"
    assert report["missing_ev_candidate_ids"] == ["overnight_bucket_1"]
    assert report["missing_runtime_summary_candidate_ids"] == ["overnight_bucket_1"]
    assert report["missing_workorder_order_ids"] == [
        "order_lifecycle_overnight_bucket_overnight_status_hold_overnight"
    ]


def test_lifecycle_bucket_discovery_handoff_detects_missing_downstream():
    discovery = {
        "surfaced_candidates": [
            {
                "bucket_id": "entry:combo:test",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": "entry_wait6579_score66_69_recovery_gate_v1",
            },
            {
                "bucket_id": "entry:combo:unknown",
                "classification_state": "new_bucket_candidate",
            },
        ]
    }

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, {"orders": []})

    assert report["status"] == "fail"
    assert report["missing_bridge_families"] == ["entry_wait6579_score66_69_recovery_gate_v1"]
    assert "runtime_approval_summary_lifecycle_bucket_discovery_missing" in report["missing"]
    assert "code_improvement_workorder_lifecycle_bucket_discovery_orders_missing" in report["missing"]


def test_lifecycle_bucket_discovery_handoff_warns_when_source_dimension_gap_not_surfaced():
    discovery = {
        "surfaced_candidates": [
            {
                "bucket_id": "entry:combo:unknown",
                "stage": "entry",
                "classification_state": "source_only_keep_collecting",
                "source_dimension_gap": "unknown_source_dimensions",
                "recommended_resolution": "resolve_unknown_source_dimensions",
            }
        ]
    }
    runtime_summary = {"surfaced_candidate_ids": ["entry:combo:unknown"]}

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, runtime_summary, {"orders": []})

    assert report["status"] == "warning"
    assert "lifecycle_source_dimension_gap_handoff_missing" in report["warnings"]
    assert report["actionable_source_dimension_gap_bucket_ids"] == ["entry:combo:unknown"]


def test_lifecycle_bucket_discovery_handoff_warns_from_source_dimension_summary():
    discovery = {
        "source_dimension_gap_summary": {
            "actionable_unknown_gap_count": 2,
            "actionable_candidates": [],
        },
        "surfaced_candidates": [],
    }

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, {"orders": []})

    assert report["status"] == "warning"
    assert "lifecycle_source_dimension_gap_handoff_missing" in report["warnings"]
    assert report["actionable_source_dimension_gap_bucket_ids"] == ["source_dimension_gap_summary"]
    assert report["actionable_source_dimension_gap_count"] == 2


def test_lifecycle_bucket_discovery_handoff_fails_when_sim_source_dimension_gap_not_surfaced():
    discovery = {
        "surfaced_candidates": [
            {
                "bucket_id": "lifecycle_flow:combo:unknown",
                "stage": "lifecycle_flow",
                "classification_state": "lifecycle_flow_sim_probe_candidate",
                "source_dimension_gap": "unknown_source_dimensions",
                "recommended_resolution": "resolve_unknown_source_dimensions",
            }
        ]
    }
    runtime_summary = {"surfaced_candidate_ids": ["lifecycle_flow:combo:unknown"]}

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, runtime_summary, {"orders": []})

    assert report["status"] == "fail"
    assert "lifecycle_source_dimension_gap_handoff_missing" in report["missing"]
    assert report["blocking_source_dimension_gap_bucket_ids"] == ["lifecycle_flow:combo:unknown"]


def test_lifecycle_bucket_discovery_handoff_warns_when_quiet_gap_rollup_missing():
    discovery = {
        "quiet_gap_summary": {
            "quiet_gap_count": 2,
            "rollup_required_count": 2,
            "sim_live_connected_quiet_gap_count": 0,
        },
        "surfaced_candidates": [],
    }

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, {"orders": []})

    assert report["status"] == "warning"
    assert "lifecycle_quiet_gap_handoff_missing" in report["warnings"]
    assert report["quiet_gap_count"] == 2
    assert report["has_quiet_gap_rollup_workorder"] is False


def test_lifecycle_bucket_discovery_handoff_fails_when_sim_quiet_gap_rollup_missing():
    discovery = {
        "quiet_gap_summary": {
            "quiet_gap_count": 1,
            "rollup_required_count": 1,
            "sim_live_connected_quiet_gap_count": 1,
            "sim_live_connected_candidate_ids": ["lifecycle_flow:sim-probe"],
        },
        "surfaced_candidates": [],
    }

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, {"orders": []})

    assert report["status"] == "fail"
    assert "lifecycle_quiet_gap_handoff_missing" in report["missing"]
    assert report["sim_live_connected_quiet_gap_count"] == 1


def test_lifecycle_bucket_discovery_handoff_passes_when_quiet_gap_rollup_exists():
    discovery = {
        "quiet_gap_summary": {"quiet_gap_count": 1, "rollup_required_count": 1},
        "surfaced_candidates": [],
    }
    workorder = {"orders": [{"order_id": "order_lifecycle_quiet_gap_parent_conflict_rollup"}]}

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, workorder)

    assert report["status"] == "pass"
    assert report["has_quiet_gap_rollup_workorder"] is True


def test_lifecycle_bucket_discovery_handoff_warns_when_quiet_gap_rollup_is_partial():
    discovery = {
        "quiet_gap_summary": {
            "quiet_gap_count": 2,
            "rollup_required_count": 2,
            "quiet_gap_type_counts": {
                "parent_conflict_child": 1,
                "ai_review_parsed_low_coverage": 1,
            },
        },
        "surfaced_candidates": [],
    }
    workorder = {"orders": [{"order_id": "order_lifecycle_quiet_gap_parent_conflict_rollup"}]}

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, workorder)

    assert report["status"] == "warning"
    assert report["missing_quiet_gap_workorder_order_ids"] == ["order_lifecycle_quiet_gap_ai_review_coverage_rollup"]
    assert report["has_quiet_gap_rollup_workorder"] is False


def test_lifecycle_bucket_discovery_greenfield_bridge_exclusion_is_not_missing_family():
    discovery = {
        "summary": {"source_contract_status": "pass", "ai_two_pass_review_status": "parsed"},
        "surfaced_candidates": [
            {
                "bucket_id": "lifecycle_flow:combo:greenfield",
                "stage": "lifecycle_flow",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": "greenfield_real_environment_authority",
            }
        ],
    }
    bridge = {"summary": {"greenfield_policy_emit_state": "not_emitted_no_complete_lifecycle_flow"}}
    runtime_summary = {"surfaced_candidate_ids": ["lifecycle_flow:combo:greenfield"]}

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, bridge, runtime_summary, {"orders": []})

    assert report["status"] == "pass"
    assert report["missing_bridge_families"] == []
    assert report["explicit_bridge_exclusion_families"] == ["greenfield_real_environment_authority"]


def test_lifecycle_bucket_windows_status_fails_missing_enabled_windows(tmp_path):
    paths = {}
    for suffix in ("rolling5d", "rolling10d", "mtd"):
        paths[f"lifecycle_decision_matrix_{suffix}"] = tmp_path / f"lifecycle_decision_matrix_2026-05-29_{suffix}.json"
        paths[f"lifecycle_bucket_discovery_{suffix}"] = tmp_path / f"lifecycle_bucket_discovery_2026-05-29_{suffix}.json"

    report = mod._lifecycle_bucket_windows_status(
        paths=paths,
        done_line="[DONE] threshold-cycle postclose target_date=2026-05-29 lifecycle_bucket_windows=true",
        bridge_report={},
        ev_report={},
        runtime_summary={},
    )

    assert report["status"] == "fail"
    assert "lifecycle_bucket_windows_marker_true_but_artifacts_missing" in report["missing"]
    assert "lifecycle_bucket_discovery_mtd_missing" in report["missing"]


def test_lifecycle_bucket_windows_status_blocks_daily_only_authority(tmp_path):
    paths = {}
    for suffix in ("rolling5d", "rolling10d", "mtd"):
        ldm = tmp_path / f"lifecycle_decision_matrix_2026-05-29_{suffix}.json"
        discovery = tmp_path / f"lifecycle_bucket_discovery_2026-05-29_{suffix}.json"
        ldm.write_text("{}", encoding="utf-8")
        discovery.write_text(
            json.dumps(
                {
                    "summary": {
                        "source_contract_status": "pass",
                        "parent_granularity_status": "target_pass",
                        "parent_bucket_count": 36,
                    }
                }
            ),
            encoding="utf-8",
        )
        paths[f"lifecycle_decision_matrix_{suffix}"] = ldm
        paths[f"lifecycle_bucket_discovery_{suffix}"] = discovery

    report = mod._lifecycle_bucket_windows_status(
        paths=paths,
        done_line="[DONE] threshold-cycle postclose target_date=2026-05-29 lifecycle_bucket_windows=true",
        bridge_report={"summary": {"live_auto_apply_ready_count": 1, "lifecycle_bucket_promotion_contract_passed": False}},
        ev_report={},
        runtime_summary={},
    )

    assert report["status"] == "fail"
    assert "runtime_apply_bridge_daily_only_live_authority" in report["missing"]


def test_stage_hook_workorder_handoff_detects_missing_selected_order():
    stage_hook = {
        "status": "warning",
        "summary": {"ai_two_pass_review_status": "parsed", "audit_status": "pass"},
        "ai_two_pass_review": {
            "provider": "openai",
            "provider_status": {"provider": "openai", "status": "success"},
        },
        "context": {"consumed_candidate_ids": ["producer_gap_sim_holding_runner_gap_missing"]},
        "code_improvement_orders": [
            {
                "order_id": "order_stage_hook_runner",
                "stage_hook_priority": "high",
                "stage_hook_candidate_contract": {"readiness_tier": "implementation_workorder_ready"},
            }
        ],
    }
    producer_gap = {
        "producer_gap_candidates": [
            {
                "candidate_id": "producer_gap_sim_holding_runner_gap_missing",
                "pattern_type": "sim_holding_runner_gap_missing",
            }
        ]
    }

    report = mod._stage_hook_workorder_handoff_status(stage_hook, producer_gap, {"orders": []})

    assert report["status"] == "fail"
    assert report["missing_workorder_order_ids"] == ["order_stage_hook_runner"]
    assert "stage_hook_workorder_handoff_missing" in report["missing"]


def test_stage_hook_workorder_handoff_allows_blocked_source_quality_without_order():
    stage_hook = {
        "status": "pass",
        "summary": {"ai_two_pass_review_status": "parsed", "audit_status": "pass"},
        "ai_two_pass_review": {
            "provider": "openai",
            "provider_status": {"provider": "openai", "status": "success"},
        },
        "context": {"consumed_candidate_ids": ["producer_gap_sim_source_quality_join_gap_missing"]},
        "code_improvement_orders": [],
    }
    producer_gap = {
        "producer_gap_candidates": [
            {
                "candidate_id": "producer_gap_sim_source_quality_join_gap_missing",
                "pattern_type": "sim_source_quality_join_gap_missing",
            }
        ]
    }

    report = mod._stage_hook_workorder_handoff_status(stage_hook, producer_gap, {"orders": []})

    assert report["status"] == "pass"
    assert report["missing_workorder_order_ids"] == []


def test_lifecycle_bucket_discovery_handoff_surfaces_ai_followup_without_fail():
    discovery = {
        "summary": {
            "source_contract_status": "pass",
            "ai_two_pass_review_status": "unavailable",
        },
        "warnings": ["ai_two_pass_review_unavailable_live_auto_deferred_to_post_apply"],
        "surfaced_candidates": [
            {
                "bucket_id": "entry:combo:test",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": "entry_wait6579_score66_69_recovery_gate_v1",
                "ai_review_followup_required": "post_apply_verification",
            }
        ],
    }
    bridge = {"candidates": [{"family": "entry_wait6579_score66_69_recovery_gate_v1"}]}
    runtime_summary = {"surfaced_candidate_ids": ["entry:combo:test"]}

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, bridge, runtime_summary, {"orders": []})

    assert report["status"] == "pass"
    assert report["ai_post_apply_followup_bucket_ids"] == ["entry:combo:test"]
    assert "lifecycle_bucket_discovery_ai_post_apply_followup_required" in report["warnings"]


def test_lifecycle_bucket_discovery_handoff_fails_source_contract_fail():
    discovery = {
        "summary": {"source_contract_status": "fail"},
        "surfaced_candidates": [],
    }

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, {"orders": []})

    assert report["status"] == "fail"
    assert "lifecycle_bucket_discovery_source_contract_fail" in report["missing"]


def test_lifecycle_bucket_discovery_handoff_warns_policy_key_required_missing():
    discovery = {
        "source_dimension_gap_summary": {
            "missing_dimension_key_counts": {"policy_key": 5},
            "policy_key_gap_classification_counts": {"policy_key_required_missing": 3, "policy_key_provided": 12},
        },
        "surfaced_candidates": [],
    }

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, {"orders": []})

    assert report["status"] == "warning"
    assert "lifecycle_bucket_discovery_policy_key_required_missing" in report["warnings"]


def test_lifecycle_bucket_discovery_handoff_warns_policy_key_missing_non_blocking_context():
    discovery = {
        "source_dimension_gap_summary": {
            "missing_dimension_key_counts": {"policy_key": 8},
            "policy_key_gap_classification_counts": {"policy_key_not_required_context_row": 5, "policy_key_not_applicable_matrix_missing": 3},
        },
        "surfaced_candidates": [],
    }

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, {"orders": []})

    assert report["status"] == "warning"
    assert "lifecycle_bucket_discovery_policy_key_missing_non_blocking_context" in report["warnings"]


def test_lifecycle_bucket_discovery_handoff_warns_policy_key_missing_await_classification():
    discovery = {
        "source_dimension_gap_summary": {
            "missing_dimension_key_counts": {"policy_key": 10},
        },
        "surfaced_candidates": [],
    }

    report = mod._lifecycle_bucket_discovery_handoff_status(discovery, {}, {}, {"orders": []})

    assert report["status"] == "warning"
    assert "lifecycle_bucket_discovery_policy_key_missing_await_classification" in report["warnings"]


def test_warning_followup_summary_breaks_down_postclose_warning_priorities():
    summary = mod._warning_followup_summary(
        buy_funnel_submit_drought_handoff={
            "status": "pass",
            "critical": True,
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            "missing": [],
        },
        scalp_entry_adm={
            "summary": {
                "status": "warning",
                "warnings": ["unknown_bucket_source_quality_gap"],
                "unknown_bucket_summary": {
                    "affected_rows": 255,
                    "dimension_counts": {"score_bucket": 255},
                    "recommended_route": "source_quality_workorder",
                    "not_available_route": "field_legitimately_unavailable_no_workorder",
                },
                "adm_bucket_lookup_status_counts": {
                    "new_or_unseen_token_vs_prior_adm": 386,
                    "matched_prior_bucket": 373,
                },
            }
        },
        currentness_audit={"status": "pass", "summary": {"fail_count": 0}},
        pattern_lab_ai_review={"status": "pass", "summary": {"workorder_count": 0}},
        discovery_report={
            "summary": {
                "live_auto_apply_ready_count": 0,
                "state_counts": {"source_only_keep_collecting": 401},
                "source_bucket_kind_counts": {"source_only_observation": 335},
                "source_contract_status": "warning",
                "source_contract_change_count": 11,
                "ai_two_pass_review_status": "parsed",
            }
        },
        runtime_apply_gap_audit={
            "summary": {
                "derived_review_category_counts": {"source_quality_blocker": 536},
                "positive_edge_source_quality_pass_count": 24,
                "bridge_blocker_ledger_count": 200,
                "runtime_uptake_rate_pct": 0.0,
            }
        },
        lifecycle_bucket_discovery_handoff={
            "warnings": ["lifecycle_bucket_discovery_source_contract_warning"]
        },
    )

    items = {item["topic"]: item for item in summary["items"]}
    assert summary["status"] == "warning"
    assert summary["runtime_effect"] is False
    assert summary["allowed_runtime_apply"] is False
    assert items["submit_drought"]["decision"] == "pass_handoff_closed"
    assert items["scalp_entry_adm_unknown_bucket_source_quality_gap"]["decision"] == (
        "source_quality_followup_required"
    )
    assert items["pattern_lab_warning"]["decision"] == "pass_no_current_handoff_workorder"
    assert items["live_auto_ready_zero_breakdown"]["decision"] == "warning_explained_no_live_auto_ready"
    assert items["live_auto_ready_zero_breakdown"]["evidence"]["runtime_gap_categories"] == {
        "source_quality_blocker": 536
    }


def test_submit_bucket_handoff_status_detects_downstream_drops():
    ldm = {
        "submit_bucket_attribution": {
            "runtime_approval_candidates": [
                {"candidate_id": "submit_bucket_1", "bucket_type": "revalidation_state", "bucket_key": "ok"}
            ],
            "code_improvement_workorders": [
                {
                    "bucket_type": "broker_receipt_contract_gap",
                    "bucket_key": "broker_receipt_or_real_submit_flag_missing",
                }
            ],
        }
    }

    report = mod._submit_bucket_handoff_status(ldm, {}, {}, {"orders": []})

    assert report["status"] == "fail"
    assert report["missing_ev_candidate_ids"] == ["submit_bucket_1"]
    assert report["missing_runtime_summary_candidate_ids"] == ["submit_bucket_1"]
    assert report["missing_workorder_order_ids"] == [
        "order_lifecycle_submit_bucket_broker_receipt_contract_gap_broker_receipt_or_real_submit_flag_missing"
    ]


def test_submit_bucket_handoff_preserves_named_entry_contract_order_ids():
    ldm = {
        "submit_bucket_attribution": {
            "code_improvement_workorders": [
                {
                    "workorder_id": "order_entry_broker_receipt_contract_gap_review",
                    "bucket_type": "broker_receipt_contract_gap",
                    "bucket_key": "broker_receipt_or_real_submit_flag_missing",
                }
            ],
        }
    }

    report = mod._submit_bucket_handoff_status(ldm, {}, {}, {"orders": []})

    assert report["missing_workorder_order_ids"] == ["order_entry_broker_receipt_contract_gap_review"]


def test_stage_only_holding_bucket_handoff_detects_runtime_candidates_and_drops():
    workorder = {
        "workorder_id": "holding_bucket_source_quality_1",
        "bucket_type": "combo_holding_flow",
        "bucket_key": "source=sim|action=HOLD|profit=profit_unknown|held=held_unknown",
    }
    ldm = {
        "holding_bucket_attribution": {
            "summary": {"bucket_count": 1, "workorder_count": 1},
            "runtime_approval_candidates": [{"candidate_id": "forbidden"}],
            "code_improvement_workorders": [workorder],
        }
    }
    ev = {"lifecycle_decision_matrix": {"holding_bucket_code_improvement_workorders": []}}
    runtime = {"lifecycle_decision_matrix": {"holding_bucket_code_improvement_workorders": []}}

    report = mod._stage_only_bucket_handoff_status(ldm, ev, runtime, {"orders": []}, stage="holding")

    assert report["status"] == "fail"
    assert "holding_stage_only_runtime_candidates_forbidden" in report["missing"]
    assert "threshold_cycle_ev_holding_bucket_count_missing" in report["missing"]
    assert "runtime_approval_summary_holding_bucket_count_missing" in report["missing"]
    assert "threshold_cycle_ev_holding_bucket_workorders_missing" in report["missing"]
    assert "runtime_approval_summary_holding_bucket_workorders_missing" in report["missing"]
    assert report["missing_workorder_order_ids"] == [mod._stage_bucket_order_id("holding", workorder)]


def test_stage_only_holding_bucket_handoff_passes_when_counts_and_orders_propagate():
    workorder = {
        "workorder_id": "holding_bucket_source_quality_1",
        "bucket_type": "combo_holding_flow",
        "bucket_key": "source=sim|action=HOLD|profit=profit_unknown|held=held_unknown",
    }
    order_id = mod._stage_bucket_order_id("holding", workorder)
    ldm = {
        "holding_bucket_attribution": {
            "summary": {"bucket_count": 1, "workorder_count": 1},
            "runtime_approval_candidates": [],
            "code_improvement_workorders": [workorder],
        }
    }
    ev = {
        "lifecycle_decision_matrix": {
            "holding_bucket_count": 1,
            "holding_bucket_workorder_count": 1,
            "holding_bucket_code_improvement_workorders": [workorder],
        }
    }
    runtime = {
        "lifecycle_decision_matrix": {
            "holding_bucket_count": 1,
            "holding_bucket_workorder_count": 1,
            "holding_bucket_code_improvement_workorders": [workorder],
        }
    }

    report = mod._stage_only_bucket_handoff_status(
        ldm,
        ev,
        runtime,
        {"orders": [{"order_id": order_id}]},
        stage="holding",
    )

    assert report["status"] == "pass"
    assert report["missing"] == []


def test_lifecycle_flow_handoff_fails_when_complete_flow_absent():
    ldm = {
        "lifecycle_flow_bucket_attribution": {
            "summary": {
                "flow_count": 4,
                "complete_flow_count": 0,
                "direct_sim_record_complete_flow_count": 0,
                "adm_bridge_complete_flow_count": 0,
                "fallback_complete_flow_count": 0,
                "incomplete_flow_count": 4,
                "complete_flow_rate": 0.0,
                "join_contract_blocked": True,
                "bundle_ev_tuning_state": "blocked_join_gap",
                "top_incomplete_reason": "identity_namespace_mismatch",
            },
            "runtime_approval_candidates": [],
            "code_improvement_workorders": [],
        }
    }

    report = mod._lifecycle_flow_bucket_handoff_status(ldm, {}, {}, {"orders": []})

    assert report["status"] == "fail"
    assert "lifecycle_complete_flow_absent" in report["missing"]
    assert "lifecycle_join_contract_blocked" in report["missing"]
    assert report["bundle_ev_tuning_state"] == "blocked_join_gap"
    assert report["direct_sim_record_complete_flow_count"] == 0
    assert report["adm_bridge_complete_flow_count"] == 0


def test_buy_funnel_submit_drought_handoff_fails_when_downstream_missing():
    buy = {
        "classification": {
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
        }
    }

    report = mod._buy_funnel_submit_drought_handoff_status(buy, {}, {}, {}, {"orders": []})

    assert report["status"] == "fail"
    assert report["critical"] is True
    assert "code_improvement_workorder_entry_submit_drought_orders_missing" in report["missing"]
    assert "order_entry_submit_drought_auto_resolution" in report["missing_workorder_order_ids"]
    assert "order_entry_broker_receipt_contract_gap_review" in report["missing_workorder_order_ids"]
    assert "ldm_submit_bucket_attribution_missing" in report["missing"]


def test_buy_funnel_submit_drought_handoff_passes_when_surfaced():
    buy = {
        "classification": {
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
        }
    }
    ldm = {"submit_bucket_attribution": {"summary": {"submit_rows": 3}}}
    ev_report = {
        "buy_funnel_sentinel": {"primary": "SUBMIT_DROUGHT_CRITICAL"},
        "entry_funnel": {"entry_submit_drought_handoff_selected": True},
    }
    runtime_summary = {
        "buy_funnel_sentinel": {"primary": "SUBMIT_DROUGHT_CRITICAL"},
        "summary": {"entry_submit_drought_handoff_selected": True},
    }
    workorder = {
        "orders": [
            {"order_id": "order_entry_submit_drought_auto_resolution"},
            {"order_id": "order_entry_post_submit_contract_gap_review"},
            {"order_id": "order_entry_broker_receipt_contract_gap_review"},
            {"order_id": "order_entry_fill_quality_contract_gap_review"},
            {"order_id": "order_entry_telegram_post_submit_contract_gap_review"},
            {"order_id": "order_entry_source_taxonomy_contract_gap_review"},
        ]
    }

    report = mod._buy_funnel_submit_drought_handoff_status(
        buy, ldm, ev_report, runtime_summary, workorder
    )

    assert report["status"] == "pass"
    assert report["missing"] == []


def test_buy_funnel_submit_drought_handoff_surfaces_post_submit_join_gap():
    buy = {
        "classification": {
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
        }
    }
    ldm = {
        "submit_bucket_attribution": {
            "summary": {
                "submit_rows": 41,
                "real_submitted_row_count": 17,
                "missing_broker_order_key_count": 17,
                "missing_broker_order_key_rate": 1.0,
                "post_submit_provenance_join_gap": True,
            }
        }
    }
    ev_report = {
        "buy_funnel_sentinel": {"primary": "SUBMIT_DROUGHT_CRITICAL"},
        "entry_funnel": {"entry_submit_drought_handoff_selected": True},
    }
    runtime_summary = {
        "buy_funnel_sentinel": {"primary": "SUBMIT_DROUGHT_CRITICAL"},
        "summary": {"entry_submit_drought_handoff_selected": True},
    }
    workorder = {
        "orders": [
            {"order_id": "order_entry_submit_drought_auto_resolution"},
            {"order_id": "order_entry_post_submit_contract_gap_review"},
            {"order_id": "order_entry_broker_receipt_contract_gap_review"},
            {"order_id": "order_entry_fill_quality_contract_gap_review"},
            {"order_id": "order_entry_telegram_post_submit_contract_gap_review"},
            {"order_id": "order_entry_source_taxonomy_contract_gap_review"},
        ]
    }

    report = mod._buy_funnel_submit_drought_handoff_status(
        buy, ldm, ev_report, runtime_summary, workorder
    )

    assert report["status"] == "pass"
    assert report["ldm_submit_real_submitted_row_count"] == 17
    assert report["ldm_submit_missing_broker_order_key_count"] == 17
    assert report["ldm_submit_missing_broker_order_key_rate"] == 1.0
    assert report["ldm_submit_post_submit_provenance_join_gap"] is True


def test_warning_followup_submit_drought_reports_join_gap():
    summary = mod._warning_followup_summary(
        buy_funnel_submit_drought_handoff={
            "status": "pass",
            "critical": True,
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            "missing": [],
            "ldm_submit_real_submitted_row_count": 17,
            "ldm_submit_missing_broker_order_key_count": 17,
            "ldm_submit_missing_broker_order_key_rate": 1.0,
            "ldm_submit_post_submit_provenance_join_gap": True,
        },
        scalp_entry_adm={},
        currentness_audit={},
        pattern_lab_ai_review={},
        discovery_report={},
        runtime_apply_gap_audit={},
        lifecycle_bucket_discovery_handoff={},
    )

    submit_item = summary["items"][0]

    assert summary["status"] == "warning"
    assert submit_item["decision"] == "post_submit_provenance_join_gap_open"
    assert submit_item["evidence"]["ldm_submit_missing_broker_order_key_count"] == 17
    assert "broker_order_no" in submit_item["next_action"]


def test_warning_followup_submit_drought_reports_exact_bot_history_resolution():
    summary = mod._warning_followup_summary(
        buy_funnel_submit_drought_handoff={
            "status": "pass",
            "critical": True,
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            "missing": [],
            "ldm_submit_real_submitted_row_count": 17,
            "ldm_submit_missing_broker_order_key_count": 17,
            "ldm_submit_missing_broker_order_key_rate": 1.0,
            "ldm_submit_post_submit_provenance_join_gap_raw": True,
            "ldm_submit_post_submit_provenance_join_gap": False,
            "ldm_submit_bot_history_backfill_candidate_count": 17,
            "ldm_submit_bot_history_backfill_full_coverage": True,
            "ldm_submit_bot_history_exact_mapping_count": 17,
            "ldm_submit_bot_history_exact_mapping_full_coverage": True,
            "ldm_submit_post_submit_provenance_join_resolution": (
                "resolved_by_exact_bot_history_submit_time_mapping"
            ),
        },
        scalp_entry_adm={},
        currentness_audit={},
        pattern_lab_ai_review={},
        discovery_report={},
        runtime_apply_gap_audit={},
        lifecycle_bucket_discovery_handoff={},
    )

    submit_item = summary["items"][0]

    assert summary["status"] == "pass"
    assert submit_item["decision"] == "post_submit_provenance_join_gap_resolved_by_bot_history"
    assert submit_item["evidence"]["ldm_submit_bot_history_exact_mapping_count"] == 17
    assert "Exact same-stock" in submit_item["next_action"]


def test_producer_gap_discovery_handoff_fails_ai_review_or_missing_workorder():
    producer_gap = {
        "status": "fail",
        "summary": {
            "ai_two_pass_review_status": "parse_rejected",
            "audit_status": "correction_required",
            "candidate_count": 1,
            "workorder_count": 1,
        },
        "code_improvement_orders": [
            {
                "order_id": "order_producer_gap_discovery_time_window_policy_exception",
                "producer_gap_priority": "high",
            }
        ],
    }

    report = mod._producer_gap_discovery_handoff_status(producer_gap, {"orders": []})

    assert report["status"] == "fail"
    assert "producer_gap_discovery_ai_review_failed" in report["missing"]
    assert "producer_gap_discovery_ai_review_not_parsed" in report["missing"]
    assert "producer_gap_discovery_ai_audit_not_pass" in report["missing"]
    assert "code_improvement_workorder_producer_gap_orders_missing" in report["missing"]
    assert report["missing_workorder_order_ids"] == [
        "order_producer_gap_discovery_time_window_policy_exception"
    ]


def test_producer_gap_discovery_handoff_passes_when_ai_and_workorder_close():
    producer_gap = {
        "status": "warning",
        "summary": {
            "ai_two_pass_review_status": "parsed",
            "audit_status": "pass",
            "candidate_count": 1,
            "workorder_count": 1,
            "provider": "openai",
            "model": "gpt-5.4",
        },
        "ai_two_pass_review": {
            "provider": "openai",
            "model": "gpt-5.4",
            "provider_status": {"provider": "openai", "status": "success", "model": "gpt-5.4"},
        },
        "code_improvement_orders": [
            {
                "order_id": "order_producer_gap_discovery_scale_in",
                "producer_gap_priority": "high",
            }
        ],
    }
    workorder = {"orders": [{"order_id": "order_producer_gap_discovery_scale_in"}]}

    report = mod._producer_gap_discovery_handoff_status(producer_gap, workorder)

    assert report["status"] == "pass"
    assert report["missing"] == []


def test_producer_gap_discovery_handoff_treats_parsed_followup_as_workorder_not_ai_failure():
    followup_order_id = "order_producer_gap_discovery_ai_review_followup_20260526"
    producer_gap = {
        "status": "warning",
        "summary": {
            "ai_two_pass_review_status": "parsed",
            "audit_status": "correction_required",
            "ai_review_followup_required": True,
            "ai_review_followup_reasons": ["audit_status=correction_required"],
            "candidate_count": 1,
            "workorder_count": 1,
            "provider": "openai",
            "model": "gpt-5.4-mini",
        },
        "ai_two_pass_review": {
            "provider": "openai",
            "model": "gpt-5.4-mini",
            "provider_status": {"provider": "openai", "status": "success", "model": "gpt-5.4-mini"},
        },
        "code_improvement_orders": [
            {
                "order_id": followup_order_id,
                "producer_gap_priority": "high",
                "improvement_type": "ai_review_followup",
            }
        ],
    }
    workorder = {"orders": [{"order_id": followup_order_id}]}

    report = mod._producer_gap_discovery_handoff_status(producer_gap, workorder)

    assert report["status"] == "pass"
    assert "producer_gap_discovery_ai_audit_not_pass" not in report["missing"]
    assert report["ai_review_followup_required"] is True
    assert report["missing_ai_review_followup_workorder_order_ids"] == []


def test_producer_gap_discovery_handoff_fails_without_openai_tier2_review():
    producer_gap = {
        "status": "warning",
        "summary": {
            "ai_two_pass_review_status": "parsed",
            "audit_status": "pass",
            "candidate_count": 1,
            "workorder_count": 1,
            "provider": "none",
            "model": None,
        },
        "ai_two_pass_review": {
            "provider": "none",
            "model": None,
            "provider_status": {"provider": "none", "status": "provided_response", "model": None},
        },
        "code_improvement_orders": [
            {
                "order_id": "order_producer_gap_discovery_scale_in",
                "producer_gap_priority": "high",
            }
        ],
    }
    workorder = {"orders": [{"order_id": "order_producer_gap_discovery_scale_in"}]}

    report = mod._producer_gap_discovery_handoff_status(producer_gap, workorder)

    assert report["status"] == "fail"
    assert "producer_gap_discovery_tier2_provider_review_missing" in report["missing"]


def test_stage_hook_handoff_treats_parsed_followup_as_workorder_not_ai_failure():
    followup_order_id = "order_stage_hook_workorder_discovery_ai_review_followup_20260526"
    stage_hook = {
        "status": "warning",
        "summary": {
            "ai_two_pass_review_status": "parsed",
            "audit_status": "correction_required",
            "ai_review_followup_required": True,
            "ai_review_followup_reasons": ["forbidden_use_violation"],
            "candidate_count": 1,
            "workorder_count": 1,
            "provider": "openai",
        },
        "ai_two_pass_review": {
            "provider": "openai",
            "provider_status": {"provider": "openai", "status": "success", "model": "gpt-5.4-mini"},
        },
        "code_improvement_orders": [
            {
                "order_id": followup_order_id,
                "stage_hook_priority": "high",
                "improvement_type": "ai_review_followup",
            }
        ],
        "context": {"consumed_candidate_ids": []},
    }
    workorder = {"orders": [{"order_id": followup_order_id}]}

    report = mod._stage_hook_workorder_handoff_status(stage_hook, {}, workorder)

    assert report["status"] == "pass"
    assert "stage_hook_workorder_discovery_ai_audit_not_pass" not in report["missing"]
    assert report["ai_review_followup_required"] is True
    assert report["missing_ai_review_followup_workorder_order_ids"] == []


def test_ai_correction_status_reads_current_provider_status_key(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    review_dir = report_dir / "threshold_cycle_ai_review"
    calibration_dir = report_dir / "threshold_cycle_calibration"
    review_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    (review_dir / "threshold_cycle_ai_review_2026-05-26_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "parsed",
                "ai_provider_status": {
                    "provider": "openai",
                    "status": "success",
                    "schema_name": "threshold_ai_correction_v1",
                },
                "parse_warnings": [],
            }
        ),
        encoding="utf-8",
    )
    (calibration_dir / "threshold_cycle_calibration_2026-05-26_postclose.json").write_text(
        json.dumps({"calibration_candidates": []}),
        encoding="utf-8",
    )

    report = mod._ai_correction_status("2026-05-26")

    assert report["status"] == "pass"
    assert report["provider_status"]["provider"] == "openai"


def test_producer_gap_discovery_handoff_fails_sim_first_coverage_gap_without_workorder():
    producer_gap = {
        "status": "warning",
        "summary": {
            "ai_two_pass_review_status": "parsed",
            "audit_status": "pass",
            "candidate_count": 1,
            "workorder_count": 0,
            "sim_first_coverage_status": "warning",
        },
        "producer_gap_candidates": [
            {
                "candidate_id": "producer_gap_sim_first_coverage_gap",
                "pattern_type": "sim_first_coverage_gap",
                "ai_priority": "high",
            }
        ],
        "code_improvement_orders": [],
    }

    report = mod._producer_gap_discovery_handoff_status(producer_gap, {"orders": []})

    assert report["status"] == "fail"
    assert "producer_gap_discovery_sim_first_coverage_handoff_missing" in report["missing"]
    assert report["missing_workorder_order_ids"] == [
        "order_producer_gap_discovery_producer_gap_sim_first_coverage_gap"
    ]


def test_bottom_rebound_sim_handoff_passes_when_persisted():
    sim_report = {
        "source_quality": {
            "bottom_rebound_source": {"status": "ok"},
            "bottom_rebound_source_rows": 3,
        },
        "summary": {
            "bottom_rebound_selected_candidate_count": 3,
            "bottom_rebound_arm_count": 9,
            "bottom_rebound_persisted_candidate_count": 3,
            "bottom_rebound_persisted_arm_count": 9,
        },
        "persist_summary": {"candidate_rows": 3, "arm_rows": 9},
    }

    report = mod._bottom_rebound_sim_handoff_status(sim_report)

    assert report["status"] == "pass"
    assert report["included"] is True
    assert report["missing"] == []


def test_bottom_rebound_sim_handoff_fails_when_included_but_not_persisted():
    sim_report = {
        "source_quality": {
            "bottom_rebound_source": {"status": "ok"},
            "bottom_rebound_source_rows": 2,
        },
        "summary": {
            "bottom_rebound_selected_candidate_count": 2,
            "bottom_rebound_arm_count": 6,
            "bottom_rebound_persisted_candidate_count": 0,
            "bottom_rebound_persisted_arm_count": 0,
        },
        "persist_summary": {"candidate_rows": 0, "arm_rows": 0},
    }

    report = mod._bottom_rebound_sim_handoff_status(sim_report)

    assert report["status"] == "fail"
    assert "bottom_rebound_persisted_candidates_missing" in report["missing"]
    assert "bottom_rebound_persisted_arms_missing" in report["missing"]


def test_bottom_rebound_sim_handoff_not_applicable_when_source_absent():
    report = mod._bottom_rebound_sim_handoff_status(
        {
            "source_quality": {
                "bottom_rebound_source": {"status": "disabled"},
                "bottom_rebound_source_rows": 0,
            },
            "summary": {},
            "persist_summary": {"candidate_rows": 5, "arm_rows": 30},
        }
    )

    assert report["status"] == "not_applicable"
    assert report["included"] is False


def test_active_sim_priority_handoff_passes_with_matching_preopen_and_runtime(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_iter_pipeline_event_fields",
        lambda target_date: [
            {
                "active_seed_id": "active_seed_test",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ],
    )

    status = mod._active_sim_priority_handoff_status(
        target_date="2026-06-01",
        discovery={
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "active_seed_test",
                    "source_parent_bucket_id": "parent_positive",
                    "status": "active",
                }
            ]
        },
        scalp_catalog={
            "schema_version": "scalp_sim_policy_catalog_v1",
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "active_seed_test",
                    "source_parent_bucket_id": "parent_positive",
                    "status": "active",
                    "observable_prefix": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_blocked_ai_score",
                    },
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                }
            ]
        },
        swing_catalog={
            "schema_version": "swing_sim_policy_catalog_v1",
            "active_arm_priority_policies": [
                {
                    "priority_policy_id": "priority_arm05",
                    "priority_arm_id": "arm05_breakout_conf_trailing",
                    "source_report_date": "2026-06-01",
                    "status": "active",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                }
            ]
        },
        preopen_apply={
            "selected": [
                {
                    "family": "scalp_sim_auto_approval",
                    "selected": True,
                    "active_sim_priority_seed_ids": ["active_seed_test"],
                },
                {
                    "family": "swing_sim_auto_approval",
                    "selected": True,
                    "active_arm_priority_policy_ids": ["priority_arm05"],
                },
            ]
        },
        swing_sim_report={"summary": {"active_arm_priority_arm_count": 1}},
    )

    assert status["status"] == "pass"
    assert status["active_seed_ids"] == ["active_seed_test"]
    assert status["active_swing_priority_policy_ids"] == ["priority_arm05"]


def test_active_sim_priority_handoff_fails_unknown_runtime_key(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_iter_pipeline_event_fields",
        lambda target_date: [
            {
                "active_seed_id": "active_seed_unknown",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ],
    )

    status = mod._active_sim_priority_handoff_status(
        target_date="2026-06-01",
        discovery={},
        scalp_catalog={
            "schema_version": "scalp_sim_policy_catalog_v1",
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "active_seed_test",
                    "source_parent_bucket_id": "parent_positive",
                    "status": "active",
                    "observable_prefix": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_blocked_ai_score",
                    },
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                }
            ]
        },
        swing_catalog={},
        preopen_apply={
            "selected": [
                {
                    "family": "scalp_sim_auto_approval",
                    "selected": True,
                    "active_sim_priority_seed_ids": ["active_seed_test"],
                }
            ]
        },
        swing_sim_report={},
    )

    assert status["status"] == "fail"
    assert "active_sim_priority_unknown_key_observed" in status["missing"]


def test_active_sim_priority_accepts_runtime_referenced_preopen_catalog(monkeypatch, tmp_path):
    runtime_catalog = tmp_path / "scalp_sim_policy_catalog_2026-06-02.json"
    runtime_catalog.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "active_sim_priority_seeds": [
                    {
                        "active_seed_id": "active_seed_runtime",
                        "source_parent_bucket_id": "parent_runtime",
                        "status": "active",
                        "observable_prefix": {
                            "entry_score_parent": "score_mid_recovery",
                            "entry_source_parent": "entry_source_blocked_ai_score",
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
    monkeypatch.setattr(
        mod,
        "_iter_pipeline_event_fields",
        lambda target_date: [
            {
                "active_seed_id": "active_seed_runtime",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "scalp_sim_auto_policy_file": str(runtime_catalog),
            }
        ],
    )

    status = mod._active_sim_priority_handoff_status(
        target_date="2026-06-04",
        discovery={},
        scalp_catalog={"schema_version": "scalp_sim_policy_catalog_v1", "active_sim_priority_seeds": []},
        swing_catalog={},
        preopen_apply={},
        swing_sim_report={},
    )

    assert status["status"] == "not_applicable"
    assert status["referenced_runtime_seed_ids"] == ["active_seed_runtime"]
    assert "active_sim_priority_unknown_key_observed" not in status["missing"]


def test_active_sim_priority_handoff_fails_unknown_runtime_key_when_catalog_empty(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_iter_pipeline_event_fields",
        lambda target_date: [
            {
                "active_seed_id": "active_seed_unknown",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            {"priority_policy_id": "priority_unknown"},
        ],
    )

    status = mod._active_sim_priority_handoff_status(
        target_date="2026-06-01",
        discovery={},
        scalp_catalog={"schema_version": "scalp_sim_policy_catalog_v1", "active_sim_priority_seeds": []},
        swing_catalog={"schema_version": "swing_sim_policy_catalog_v1", "active_arm_priority_policies": []},
        preopen_apply={},
        swing_sim_report={},
    )

    assert status["status"] == "fail"
    assert "active_sim_priority_unknown_key_observed" in status["missing"]


def test_active_sim_priority_zero_match_gets_absence_diagnosis(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_iter_pipeline_event_fields",
        lambda target_date: [
            {
                "scalp_sim_active_priority_seed_matched": "False",
                "active_seed_candidate_observable_prefix": json.dumps(
                    {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_observed_other",
                    }
                ),
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
            }
        ],
    )

    status = mod._active_sim_priority_handoff_status(
        target_date="2026-06-01",
        discovery={},
        scalp_catalog={
            "schema_version": "scalp_sim_policy_catalog_v1",
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "active_seed_test",
                    "source_parent_bucket_id": "parent_positive",
                    "status": "active",
                    "observable_prefix": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_action_decision",
                    },
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                }
            ],
        },
        swing_catalog={},
        preopen_apply={
            "selected": [
                {
                    "family": "scalp_sim_auto_approval",
                    "selected": True,
                    "active_sim_priority_seed_ids": ["active_seed_test"],
                }
            ]
        },
        swing_sim_report={},
    )

    assert status["status"] == "warning"
    assert "active_sim_priority_runtime_observation_missing" in status["warnings"]
    assert status["active_priority_match_absence_diagnosis"]["diagnosis"] == "active_prefix_too_narrow"
    assert status["active_priority_match_absence_diagnosis"]["status"] == "warning"


def test_active_sim_priority_pending_preopen_does_not_require_runtime_observation(monkeypatch):
    monkeypatch.setattr(mod, "_iter_pipeline_event_fields", lambda target_date: [])

    status = mod._active_sim_priority_handoff_status(
        target_date="2026-06-02",
        discovery={},
        scalp_catalog={
            "schema_version": "scalp_sim_policy_catalog_v1",
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "active_seed_next",
                    "source_parent_bucket_id": "parent_positive_next",
                    "status": "active",
                    "observable_prefix": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_action_decision",
                    },
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                }
            ],
        },
        swing_catalog={
            "schema_version": "swing_sim_policy_catalog_v1",
            "active_arm_priority_policies": [
                {
                    "priority_policy_id": "active_arm_next",
                    "priority_arm_id": "arm05_breakout_conf_trailing",
                    "source_report_date": "2026-06-02",
                    "status": "active",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                }
            ],
        },
        preopen_apply={},
        swing_sim_report={},
    )

    assert status["status"] == "warning"
    assert "active_sim_priority_preopen_handoff_pending" in status["warnings"]
    assert "active_sim_priority_runtime_observation_missing" not in status["warnings"]
    assert "swing_active_arm_priority_runtime_observation_missing" not in status["warnings"]


def test_active_sim_priority_zero_match_prioritizes_posterior_dimension_diagnosis(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_iter_pipeline_event_fields",
        lambda target_date: [
            {
                "scalp_sim_active_priority_seed_matched": "False",
                "active_seed_candidate_observable_prefix": json.dumps(
                    {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_observed_other",
                    }
                ),
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
            }
        ],
    )

    status = mod._active_sim_priority_handoff_status(
        target_date="2026-06-01",
        discovery={},
        scalp_catalog={
            "schema_version": "scalp_sim_policy_catalog_v1",
            "active_sim_priority_seeds": [
                {
                    "active_seed_id": "active_seed_test",
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
        },
        swing_catalog={},
        preopen_apply={
            "selected": [
                {
                    "family": "scalp_sim_auto_approval",
                    "selected": True,
                    "active_sim_priority_seed_ids": ["active_seed_test"],
                }
            ]
        },
        swing_sim_report={},
    )

    assert status["status"] == "fail"
    assert "active_sim_priority_seed_observable_prefix_forbidden_dimension" in status["missing"]
    assert status["active_priority_match_absence_diagnosis"]["diagnosis"] == "posterior_dimension_leaked_into_priority"
    assert status["active_priority_match_absence_diagnosis"]["status"] == "fail"


def test_ldm_refinement_consumption_fails_when_lifecycle_ledger_missing():
    status = mod._ldm_refinement_consumption_status(
        {
            "refinement_inputs": [
                {
                    "refinement_input_id": "ref_input_1",
                    "soft_hypothesis_id": "ldm_hypothesis_test",
                    "classification": "taxonomy_gap_candidate",
                }
            ]
        },
        {},
    )

    assert status["status"] == "fail"
    assert "ldm_refinement_consumption_ledger_missing" in status["missing"]


def test_ldm_refinement_consumption_fails_when_lifecycle_ledger_failed():
    status = mod._ldm_refinement_consumption_status(
        {
            "refinement_inputs": [
                {
                    "refinement_input_id": "ref_input_1",
                    "soft_hypothesis_id": "ldm_hypothesis_test",
                    "classification": "taxonomy_gap_candidate",
                }
            ]
        },
        {
            "ldm_refinement_pressure_consumption": {
                "status": "fail",
                "input_count": 1,
                "consumed_count": 0,
                "contract_issues": ["ldm_refinement_date_mismatch"],
                "entries": [],
            }
        },
    )

    assert status["status"] == "fail"
    assert "ldm_refinement_consumption_ledger_failed" in status["missing"]


def test_ldm_refinement_consumption_ignores_stale_artifact_when_stage_disabled():
    status = mod._ldm_refinement_consumption_status(
        {
            "refinement_inputs": [
                {
                    "refinement_input_id": "ref_input_stale",
                    "soft_hypothesis_id": "ldm_hypothesis_stale",
                    "classification": "taxonomy_gap_candidate",
                }
            ]
        },
        {},
        disabled=True,
    )

    assert status["status"] == "disabled"
    assert status["missing"] == []
    assert status["disabled_reason"] == "ldm_hypothesis_parent_refinement_stage_disabled"


def test_ldm_refinement_consumption_warns_for_all_needs_more_sample_with_reason():
    status = mod._ldm_refinement_consumption_status(
        {
            "refinement_inputs": [
                {
                    "refinement_input_id": "ref_input_1",
                    "soft_hypothesis_id": "ldm_hypothesis_test",
                    "classification": "taxonomy_gap_candidate",
                }
            ]
        },
        {
            "ldm_refinement_pressure_consumption": {
                "input_count": 1,
                "entries": [
                    {
                        "refinement_input_id": "ref_input_1",
                        "closure_status": "needs_more_contrastive_sample",
                        "closure_reason": "contrary_sample_needed_before_parent_structure_change",
                    }
                ],
            }
        },
    )

    assert status["status"] == "warning"
    assert "ldm_refinement_all_needs_more_contrastive_sample" in status["warnings"]


def test_ldm_refinement_consumption_warns_repeated_taxonomy_gap_unresolved():
    status = mod._ldm_refinement_consumption_status(
        {
            "refinement_inputs": [
                {
                    "refinement_input_id": "ref_input_1",
                    "soft_hypothesis_id": "ldm_hypothesis_test",
                    "classification": "taxonomy_gap_candidate",
                    "repeated_gap_count": 2,
                }
            ]
        },
        {
            "ldm_refinement_pressure_consumption": {
                "input_count": 1,
                "entries": [
                    {
                        "refinement_input_id": "ref_input_1",
                        "closure_status": "needs_more_contrastive_sample",
                        "closure_reason": "still_collecting_opposite_sample",
                    }
                ],
            }
        },
    )

    assert status["status"] == "warning"
    assert "ldm_refinement_repeated_taxonomy_gap_unresolved" in status["warnings"]


def test_ldm_refinement_consumption_fails_repeated_status_without_diagnosis():
    status = mod._ldm_refinement_consumption_status(
        {
            "refinement_inputs": [
                {
                    "refinement_input_id": "ref_input_1",
                    "soft_hypothesis_id": "ldm_hypothesis_test",
                    "classification": "parent_support",
                    "retry_count": 3,
                }
            ]
        },
        {
            "ldm_refinement_pressure_consumption": {
                "input_count": 1,
                "entries": [
                    {
                        "refinement_input_id": "ref_input_1",
                        "closure_status": "needs_more_contrastive_sample",
                        "closure_reason": "still_collecting_opposite_sample",
                    }
                ],
            }
        },
    )

    assert status["status"] == "fail"
    assert "ldm_refinement_repeated_status_diagnosis_missing_fail" in status["missing"]


def test_ldm_refinement_consumption_accepts_repeated_status_with_forced_closure():
    status = mod._ldm_refinement_consumption_status(
        {
            "refinement_inputs": [
                {
                    "refinement_input_id": "ref_input_1",
                    "soft_hypothesis_id": "ldm_hypothesis_test",
                    "classification": "taxonomy_gap_candidate",
                    "repeated_gap_count": 2,
                    "retry_count": 2,
                    "diagnosed_status": "taxonomy_gap_candidate",
                    "repeated_status_diagnosis": {
                        "diagnosed_status": "taxonomy_gap_candidate",
                        "retry_count": 2,
                        "recommended_closure_bias": "new_parent_candidate_created",
                    },
                }
            ]
        },
        {
            "ldm_refinement_pressure_consumption": {
                "input_count": 1,
                "closure_counts": {"new_parent_candidate_created": 1},
                "entries": [
                    {
                        "refinement_input_id": "ref_input_1",
                        "closure_status": "new_parent_candidate_created",
                        "closure_reason": "parent_not_found",
                    }
                ],
            }
        },
    )

    assert status["status"] == "pass"
    assert status["diagnosed_repeated_input_ids"] == ["ref_input_1"]


def test_ldm_refinement_consumption_fails_runtime_authority_violation_even_with_closure():
    status = mod._ldm_refinement_consumption_status(
        {
            "refinement_inputs": [
                {
                    "refinement_input_id": "ref_input_authority",
                    "soft_hypothesis_id": "ldm_hypothesis_authority",
                    "classification": "source_quality_gap",
                    "forbidden_contract_violation_count": 1,
                    "diagnosed_status": "contract_or_handoff_gap",
                    "diagnosis_reason": "matched_hypothesis_or_runtime_authority_contract_gap",
                    "recommended_closure_bias": "contract_handoff_gap_created",
                    "repeated_status_diagnosis": {
                        "diagnosed_status": "contract_or_handoff_gap",
                        "diagnosis_reason": "matched_hypothesis_or_runtime_authority_contract_gap",
                        "recommended_closure_bias": "contract_handoff_gap_created",
                    },
                }
            ]
        },
        {
            "ldm_refinement_pressure_consumption": {
                "input_count": 1,
                "closure_counts": {"contract_handoff_gap_created": 1},
                "entries": [
                    {
                        "refinement_input_id": "ref_input_authority",
                        "closure_status": "contract_handoff_gap_created",
                        "closure_reason": "matched_hypothesis_or_runtime_authority_contract_gap",
                    }
                ],
            }
        },
    )

    assert status["status"] == "fail"
    assert "ldm_refinement_runtime_authority_violation_fail" in status["missing"]
    assert status["runtime_authority_violation_input_ids"] == ["ref_input_authority"]


def test_postclose_markdown_surfaces_ldm_and_active_priority_diagnosis():
    markdown = mod._render_markdown(
        {
            "date": "2026-06-01",
            "status": "warning",
            "ldm_hypothesis_parent_refinement_consumption": {
                "status": "fail",
                "input_count": 1,
                "consumed_count": 1,
                "closure_counts": {"contract_handoff_gap_created": 1},
                "missing": ["ldm_refinement_runtime_authority_violation_fail"],
                "warnings": [],
                "diagnosis_missing_warning_input_ids": ["ref_warn"],
                "diagnosis_missing_fail_input_ids": ["ref_fail"],
                "diagnosed_repeated_input_ids": ["ref_diag"],
                "runtime_authority_violation_input_ids": ["ref_auth"],
            },
            "active_sim_priority_handoff": {
                "status": "fail",
                "active_seed_ids": ["active_seed_bad"],
                "observed_seed_ids": [],
                "missing": ["active_sim_priority_seed_observable_prefix_forbidden_dimension"],
                "warnings": [],
                "active_priority_match_absence_diagnosis": {
                    "diagnosis": "posterior_dimension_leaked_into_priority",
                    "reason": "active_prefix_contains_non_runtime_observable_dimension",
                    "candidate_prefix_count": 3,
                    "top_candidate_prefixes": [["{}", 3]],
                },
            },
        }
    )

    assert "runtime_authority_violation_input_ids: `['ref_auth']`" in markdown
    assert "## Active Sim Priority Handoff" in markdown
    assert "match_absence_diagnosis: `posterior_dimension_leaked_into_priority`" in markdown


def test_swing_entry_bottleneck_handoff_fails_when_downstream_missing():
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "swing_entry_bottleneck": {
            "primary": "SWING_ENTRY_DROUGHT_CRITICAL",
            "matches": ["GATEKEEPER_PULLBACK_WAIT", "SUBMIT_ZERO"],
        },
    }

    report = mod._swing_lifecycle_handoff_status(matrix, {}, {}, {}, {"orders": []})

    assert report["status"] == "fail"
    assert report["swing_entry_bottleneck_critical"] is True
    assert "swing_entry_bottleneck_handoff_missing" in report["missing"]
    assert "order_swing_entry_bottleneck_auto_resolution" in report["missing_workorder_order_ids"]


def test_swing_entry_bottleneck_handoff_passes_when_surfaced():
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "swing_entry_bottleneck": {
            "primary": "SWING_ENTRY_DROUGHT_CRITICAL",
            "matches": ["GATEKEEPER_PULLBACK_WAIT", "SUBMIT_ZERO"],
        },
    }
    discovery = {
        "surfaced_candidate_ids": ["swing_entry_bottleneck_swing_entry_drought_critical"],
    }
    ev_report = {
        "swing_lifecycle_decision_matrix": {
            "swing_entry_bottleneck_primary": "SWING_ENTRY_DROUGHT_CRITICAL",
        },
        "swing_lifecycle_bucket_discovery": discovery,
    }
    runtime_summary = {
        "swing_lifecycle_decision_matrix": {
            "swing_entry_bottleneck_primary": "SWING_ENTRY_DROUGHT_CRITICAL",
        },
        "swing_lifecycle_bucket_discovery": discovery,
    }
    workorder = {"orders": [{"order_id": "order_swing_entry_bottleneck_auto_resolution"}]}

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, ev_report, runtime_summary, workorder)

    assert report["status"] == "pass"
    assert report["missing"] == []


def test_swing_parent_flow_handoff_passes_when_ev_and_runtime_include_candidate():
    candidate = {
        "candidate_id": "swing_ldm_lifecycle_flow_combo_parent",
        "bucket_id": "swing_ldm_lifecycle_flow_combo_parent",
    }
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "swing_lifecycle_flow_bucket_attribution": {
            "runtime_approval_candidates": [candidate],
            "sim_auto_approval_candidates": [candidate],
        },
    }
    discovery = {
        "summary": {"ai_two_pass_review_status": "parsed", "ai_fail_closed": False},
        "surfaced_candidate_ids": ["swing_ldm_lifecycle_flow_combo_parent"],
    }
    ev_report = {
        "swing_lifecycle_decision_matrix": {
            "sim_auto_candidate_ids": ["swing_ldm_lifecycle_flow_combo_parent"],
        },
        "swing_lifecycle_bucket_discovery": discovery,
    }
    runtime_summary = {
        "swing_lifecycle_decision_matrix": {
            "sim_auto_candidate_ids": ["swing_ldm_lifecycle_flow_combo_parent"],
        },
        "swing_lifecycle_bucket_discovery": discovery,
    }

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, ev_report, runtime_summary, {"orders": []})

    assert report["status"] == "pass"
    assert report["missing"] == []


def test_swing_lifecycle_handoff_ignores_discovery_source_only_extras_for_required_handoff():
    candidate = {
        "candidate_id": "swing_ldm_lifecycle_flow_combo_parent",
        "bucket_id": "swing_ldm_lifecycle_flow_combo_parent",
    }
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "swing_lifecycle_flow_bucket_attribution": {
            "runtime_approval_candidates": [candidate],
            "sim_auto_approval_candidates": [candidate],
        },
    }
    discovery = {
        "summary": {"ai_two_pass_review_status": "missing", "ai_fail_closed": True},
        "surfaced_candidates": [
            candidate,
            {
                "candidate_id": "swing_bucket_entry_source_only_extra",
                "bucket_id": "swing_bucket_entry_source_only_extra",
                "stage": "entry",
                "lifecycle_stage": "entry",
                "classification_state": "source_only_keep_collecting",
            },
        ],
        "warnings": ["ai_two_pass_review_missing_fail_closed"],
    }
    ev_report = {
        "swing_lifecycle_decision_matrix": {
            "sim_auto_candidate_ids": ["swing_ldm_lifecycle_flow_combo_parent"],
        },
    }
    runtime_summary = {
        "swing_lifecycle_decision_matrix": {
            "sim_auto_candidate_ids": ["swing_ldm_lifecycle_flow_combo_parent"],
        },
    }

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, ev_report, runtime_summary, {"orders": []})

    assert report["status"] == "warning"
    assert report["missing"] == []
    assert report["expected_candidate_ids"] == ["swing_ldm_lifecycle_flow_combo_parent"]
    assert "swing_lifecycle_bucket_discovery:ai_two_pass_review_missing_fail_closed" in report["warnings"]


def test_swing_lifecycle_handoff_requires_non_flow_matrix_approval_candidate():
    candidate = {
        "candidate_id": "swing_ldm_entry_policy_candidate",
        "bucket_id": "swing_ldm_entry_policy_candidate",
        "stage": "entry",
        "lifecycle_stage": "entry",
    }
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "entry_bucket_attribution": {
            "sim_auto_approval_candidates": [candidate],
        },
    }
    discovery = {
        "summary": {"ai_two_pass_review_status": "parsed", "ai_fail_closed": False},
        "surfaced_candidates": [candidate],
    }
    ev_report = {
        "swing_lifecycle_decision_matrix": {
            "sim_auto_candidate_ids": ["swing_ldm_entry_policy_candidate"],
        },
    }
    runtime_summary = {
        "swing_lifecycle_decision_matrix": {
            "sim_auto_candidate_ids": ["swing_ldm_entry_policy_candidate"],
        },
    }

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, ev_report, runtime_summary, {"orders": []})

    assert report["status"] == "pass"
    assert report["missing"] == []
    assert report["required_matrix_candidate_ids"] == ["swing_ldm_entry_policy_candidate"]
    assert report["expected_candidate_ids"] == ["swing_ldm_entry_policy_candidate"]


def test_swing_lifecycle_handoff_fails_when_matrix_candidate_missing_from_discovery():
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "swing_lifecycle_flow_bucket_attribution": {
            "sim_auto_approval_candidates": [
                {
                    "candidate_id": "swing_ldm_lifecycle_flow_combo_parent",
                    "bucket_id": "swing_ldm_lifecycle_flow_combo_parent",
                }
            ],
        },
    }
    discovery = {
        "summary": {"ai_two_pass_review_status": "parsed", "ai_fail_closed": False},
        "surfaced_candidate_ids": ["swing_ldm_lifecycle_flow_renamed"],
    }
    ev_report = {
        "swing_lifecycle_decision_matrix": {
            "sim_auto_candidate_ids": ["swing_ldm_lifecycle_flow_combo_parent"],
        },
        "swing_lifecycle_bucket_discovery": discovery,
    }
    runtime_summary = {
        "swing_lifecycle_decision_matrix": {
            "sim_auto_candidate_ids": ["swing_ldm_lifecycle_flow_combo_parent"],
        },
        "swing_lifecycle_bucket_discovery": discovery,
    }

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, ev_report, runtime_summary, {"orders": []})

    assert report["status"] == "fail"
    assert "swing_lifecycle_matrix_to_discovery_candidate_handoff_missing" in report["missing"]
    assert report["missing_matrix_to_discovery_candidate_ids"] == ["swing_ldm_lifecycle_flow_combo_parent"]


def test_swing_lifecycle_handoff_warns_on_ai_two_pass_missing():
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "entry_bucket_attribution": {"buckets": []},
    }
    discovery = {
        "summary": {
            "ai_two_pass_review_status": "missing",
            "ai_fail_closed": True,
            "ai_review_blocker_state": "provider_disabled",
            "pre_review_sim_auto_candidate_count": 1,
            "deterministic_proposal_count": 1,
            "ai_tier2_proposal_count": 0,
        },
        "surfaced_candidate_ids": [],
        "warnings": ["ai_two_pass_review_missing_fail_closed"],
    }

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, {}, {}, {"orders": []})

    assert report["status"] == "warning"
    assert report["missing"] == []
    assert report["ai_two_pass_review_status"] == "missing"
    assert report["ai_review_blocker_state"] == "provider_disabled"
    assert report["pre_review_sim_auto_candidate_count"] == 1
    assert "swing_lifecycle_bucket_discovery:ai_two_pass_review_fail_closed_sim_auto_blocked" in report["warnings"]


def test_swing_lifecycle_handoff_warns_on_discovery_stage_unknown():
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "entry_bucket_attribution": {"buckets": []},
    }
    discovery = {
        "summary": {"ai_two_pass_review_status": "parsed", "ai_fail_closed": False},
        "surfaced_candidates": [{"candidate_id": "swing:unknown-stage", "bucket_id": "swing:unknown-stage"}],
        "surfaced_candidate_ids": [],
        "warnings": [],
    }
    ev_report = {"swing_lifecycle_bucket_discovery": discovery}
    runtime_summary = {"swing_lifecycle_bucket_discovery": discovery}

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, ev_report, runtime_summary, {"orders": []})

    assert report["status"] == "warning"
    assert report["stage_unknown_candidate_ids"] == ["swing:unknown-stage"]
    assert "swing_lifecycle_bucket_discovery:stage_unknown" in report["warnings"]


def test_swing_lifecycle_handoff_warns_on_low_ldm_event_coverage():
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "summary": {
            "raw_swing_event_count": 1200,
            "ldm_consumed_event_count": 5,
            "ldm_event_coverage_rate": 0.004167,
            "unmapped_swing_stage_counts": {"swing_custom_event": 1195},
        },
        "entry_bucket_attribution": {"buckets": []},
    }
    discovery = {
        "summary": {"ai_two_pass_review_status": "parsed", "ai_fail_closed": False},
        "surfaced_candidate_ids": [],
        "warnings": [],
    }

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, {}, {}, {"orders": []})

    assert report["status"] == "warning"
    assert report["raw_swing_event_count"] == 1200
    assert report["ldm_consumed_event_count"] == 5
    assert report["ldm_event_coverage_rate"] == 0.004167
    assert report["unmapped_swing_stage_counts"] == {"swing_custom_event": 1195}
    assert "swing_lifecycle_decision_matrix:low_event_coverage" in report["warnings"]


def test_swing_lifecycle_handoff_warns_on_nan_ldm_event_coverage():
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "summary": {
            "raw_swing_event_count": 1200,
            "ldm_consumed_event_count": 5,
            "ldm_event_coverage_rate": "nan",
            "unmapped_swing_stage_counts": {"swing_custom_event": 1195},
        },
        "entry_bucket_attribution": {"buckets": []},
    }
    discovery = {
        "summary": {"ai_two_pass_review_status": "parsed", "ai_fail_closed": False},
        "surfaced_candidate_ids": [],
        "warnings": [],
    }

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, {}, {}, {"orders": []})

    assert report["status"] == "warning"
    assert report["ldm_event_coverage_rate"] == 0.0
    assert "swing_lifecycle_decision_matrix:low_event_coverage" in report["warnings"]


def test_swing_lifecycle_handoff_passes_without_ai_warning_when_parsed():
    matrix = {
        "input_contract": {"swing_daily_simulation_consumed": False},
        "entry_bucket_attribution": {"buckets": []},
    }
    discovery = {
        "summary": {
            "ai_two_pass_review_status": "parsed",
            "ai_fail_closed": False,
            "ai_review_blocker_state": "none",
            "pre_review_sim_auto_candidate_count": 1,
            "deterministic_proposal_count": 1,
            "ai_tier2_proposal_count": 1,
        },
        "surfaced_candidate_ids": [],
        "warnings": [],
    }

    report = mod._swing_lifecycle_handoff_status(matrix, discovery, {}, {}, {"orders": []})

    assert report["status"] == "pass"
    assert report["missing"] == []
    assert report["warnings"] == []
    assert report["ai_review_blocker_state"] == "none"


def test_swing_lifecycle_provider_mismatch_warning_uses_done_marker_provider():
    values = mod._parse_marker_values(
        "[DONE] threshold-cycle postclose target_date=2026-05-12 "
        "swing_lifecycle_bucket_discovery_ai_provider=responses"
    )
    assert values["swing_lifecycle_bucket_discovery_ai_provider"] == "responses"

    warning = mod._swing_lifecycle_provider_mismatch_warning(
        "[DONE] threshold-cycle postclose target_date=2026-05-12 "
        "swing_lifecycle_bucket_discovery_ai_provider=openai",
        {"ai_two_pass_review": {"provider": "none"}},
    )

    assert warning == (
        "swing_lifecycle_bucket_discovery:ai_provider_mismatch:"
        "done_marker=openai:artifact=none"
    )


def test_consumer_stale_detects_generated_at_ordering():
    consumer = {"generated_at": "2026-05-12T21:20:00+09:00"}
    source = {"generated_at": "2026-05-12T21:21:00+09:00"}

    assert mod._consumer_stale(consumer, source) is True
    assert mod._consumer_stale(source, consumer) is False


def test_postclose_verifier_warns_when_ev_runtime_stale_before_ldm_sources(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    (project_root / "logs").mkdir(parents=True)
    (project_root / "docs" / "checklists").mkdir(parents=True)
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# next\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")

    for label, path in mod._artifact_paths("2026-05-12").items():
        if label == "next_stage2_checklist":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"report_type": label, "generated_at": "2026-05-12T17:00:00+09:00"}
        if label == "threshold_cycle_ev":
            payload["sources"] = {
                "code_improvement_workorder": "code_improvement_workorder_2026-05-12.json",
                "pattern_lab_currentness_audit": "pattern_lab_currentness_audit_2026-05-12.json",
                "pattern_lab_ai_review": "pattern_lab_ai_review_2026-05-12.json",
                "producer_gap_discovery": "producer_gap_discovery_2026-05-12.json",
                "stage_hook_workorder_discovery": "stage_hook_workorder_discovery_2026-05-12.json",
                "stage_hook_runtime_scaffold": "stage_hook_runtime_scaffold_2026-05-12.json",
                "pattern_lab_propagation_audit": "pattern_lab_propagation_audit_2026-05-12.json",
                "scalp_entry_action_decision_matrix": "scalp_entry_action_decision_matrix_2026-05-12.json",
                "lifecycle_decision_matrix": "lifecycle_decision_matrix_2026-05-12.json",
                "swing_lifecycle_decision_matrix": "swing_lifecycle_decision_matrix_2026-05-12.json",
                "swing_lifecycle_bucket_discovery": "swing_lifecycle_bucket_discovery_2026-05-12.json",
            }
        elif label == "runtime_approval_summary":
            payload["sources"] = {
                "threshold_cycle_ev": "threshold_cycle_ev_2026-05-12.json",
                "scalp_entry_action_decision_matrix": "scalp_entry_action_decision_matrix_2026-05-12.json",
                "lifecycle_decision_matrix": "lifecycle_decision_matrix_2026-05-12.json",
                "swing_lifecycle_decision_matrix": "swing_lifecycle_decision_matrix_2026-05-12.json",
                "swing_lifecycle_bucket_discovery": "swing_lifecycle_bucket_discovery_2026-05-12.json",
                "pattern_lab_propagation_audit": "pattern_lab_propagation_audit_2026-05-12.json",
                "pattern_lab_ai_review": "pattern_lab_ai_review_2026-05-12.json",
            }
        elif label in {
            "lifecycle_decision_matrix",
            "lifecycle_bucket_discovery",
            "swing_lifecycle_decision_matrix",
            "swing_lifecycle_bucket_discovery",
        }:
            payload["generated_at"] = "2026-05-12T18:00:00+09:00"
            payload["runtime_effect"] = False
            payload["actual_order_submitted"] = False
            payload["broker_order_forbidden"] = True
            payload["allowed_runtime_apply"] = False
            payload["summary"] = {"status": "pass"}
        elif label == "runtime_apply_gap_audit":
            payload.update({"status": "pass", "summary": {"critical_failure_count": 0, "ai_review_retry_pending": False}})
        elif label == "code_improvement_workorder":
            payload.update({"generation_id": "g1", "source_hash": "h1", "lineage": {"previous_exists": False}, "orders": []})
        elif label == "swing_strategy_discovery_sim":
            payload.update({"source_quality": {"bottom_rebound_source": {"status": "disabled"}}, "persist_summary": {}})
        path.write_text(json.dumps(payload), encoding="utf-8")
    log_path.write_text(
        "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T17:00:00+0900\n"
        "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=true pattern_labs=false "
        "deepseek_swing_lab=false pattern_lab_currentness_audit=false pattern_lab_ai_review=false "
        "pattern_lab_propagation_audit=true scalp_entry_adm=true lifecycle_decision_matrix=true "
        "runtime_apply_bridge=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true "
        "runtime_apply_gap_audit=true next_stage2_checklist=true swing_strategy_discovery=true "
        "swing_lifecycle_matrix=true swing_lifecycle_bucket_discovery=true producer_gap_discovery=false "
        "stage_hook_workorder_discovery=false stage_hook_runtime_scaffold=false finished_at=2026-05-12T18:30:00+0900\n",
        encoding="utf-8",
    )

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert "threshold_cycle_ev_stale_before_swing_lifecycle_decision_matrix" in report["source_generation_warnings"]
    assert "runtime_approval_summary_stale_before_lifecycle_bucket_discovery" in report["handoff_warnings"]
    assert report["stale_downstream_links"] == []


def _write_adm_artifact(report_dir: Path, target_date: str = "2026-05-12") -> Path:
    path = (
        report_dir
        / "scalp_entry_action_decision_matrix"
        / f"scalp_entry_action_decision_matrix_{target_date}.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"report_type": "scalp_entry_action_decision_matrix"}), encoding="utf-8")
    return path


def _write_lifecycle_artifact(report_dir: Path, target_date: str = "2026-05-12") -> Path:
    path = report_dir / "lifecycle_decision_matrix" / f"lifecycle_decision_matrix_{target_date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"report_type": "lifecycle_decision_matrix"}), encoding="utf-8")
    return path


def _write_swing_discovery_sim_artifact(report_dir: Path, target_date: str = "2026-05-12") -> Path:
    path = report_dir / "swing_strategy_discovery_sim" / f"swing_strategy_discovery_sim_{target_date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "report_type": "swing_strategy_discovery_sim",
                "source_quality": {
                    "bottom_rebound_source": {"status": "disabled"},
                    "bottom_rebound_source_rows": 0,
                },
                "summary": {},
                "persist_summary": {"candidate_rows": 0, "arm_rows": 0},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_build_threshold_cycle_postclose_verification_prefers_workorder_lineage(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    (project_root / "logs").mkdir(parents=True)
    (report_dir / "threshold_cycle_ev").mkdir(parents=True)
    (report_dir / "code_improvement_workorder").mkdir(parents=True)
    (report_dir / "runtime_approval_summary").mkdir(parents=True)
    (report_dir / "pattern_lab_currentness_audit").mkdir(parents=True)
    (report_dir / "pattern_lab_propagation_audit").mkdir(parents=True)
    (report_dir / "market_panic_breadth").mkdir(parents=True)
    (report_dir / "panic_sell_defense").mkdir(parents=True)
    (report_dir / "panic_buying").mkdir(parents=True)
    (report_dir / "swing_daily_simulation").mkdir(parents=True)
    (report_dir / "swing_strategy_discovery_sim").mkdir(parents=True)
    (report_dir / "swing_lifecycle_audit").mkdir(parents=True)
    (project_root / "docs").mkdir(parents=True)
    adm_path = _write_adm_artifact(report_dir)
    lifecycle_path = _write_lifecycle_artifact(report_dir)

    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[threshold-cycle] artifact ready label=swing_daily_simulation.json path=/tmp/a waited=0s json_valid=true",
                "[threshold-cycle] artifact ready label=threshold_cycle_ev_pre_workorder.json path=/tmp/b waited=0s json_valid=true",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=true pattern_labs=true deepseek_swing_lab=true pattern_lab_currentness_audit=true pattern_lab_propagation_audit=true scalp_entry_adm=true lifecycle_decision_matrix=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )

    (report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "code_improvement_workorder": str(
                        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json"
                    ),
                    "pattern_lab_currentness_audit": str(
                        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-12.json"
                    ),
                    "pattern_lab_propagation_audit": str(
                        report_dir / "pattern_lab_propagation_audit" / "pattern_lab_propagation_audit_2026-05-12.json"
                    ),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json").write_text(
        json.dumps(
            {
                "generation_id": "2026-05-12-newhash",
                "source_hash": "newhash",
                "summary": {
                    "new_selected_order_count": 1,
                    "removed_selected_order_count": 0,
                    "decision_changed_order_count": 0,
                },
                "lineage": {
                    "previous_exists": True,
                    "previous_generation_id": "2026-05-12-oldhash",
                    "previous_source_hash": "oldhash",
                    "new_order_ids": ["order_new"],
                    "removed_order_ids": [],
                    "decision_changed_order_ids": [],
                },
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_approval_summary" / "runtime_approval_summary_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "threshold_cycle_ev": str(report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json"),
                    "pattern_lab_propagation_audit": str(
                        report_dir / "pattern_lab_propagation_audit" / "pattern_lab_propagation_audit_2026-05-12.json"
                    ),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-12.json").write_text(
        json.dumps({"report_type": "pattern_lab_currentness_audit"}),
        encoding="utf-8",
    )
    (report_dir / "pattern_lab_propagation_audit" / "pattern_lab_propagation_audit_2026-05-12.json").write_text(
        json.dumps({"report_type": "pattern_lab_propagation_audit"}),
        encoding="utf-8",
    )
    (report_dir / "market_panic_breadth" / "market_panic_breadth_2026-05-12.json").write_text(
        json.dumps({"report_type": "market_panic_breadth"}),
        encoding="utf-8",
    )
    (report_dir / "panic_sell_defense" / "panic_sell_defense_2026-05-12.json").write_text(
        json.dumps({"report_type": "panic_sell_defense"}),
        encoding="utf-8",
    )
    (report_dir / "panic_buying" / "panic_buying_2026-05-12.json").write_text(
        json.dumps({"report_type": "panic_buying"}),
        encoding="utf-8",
    )
    (report_dir / "swing_daily_simulation" / "swing_daily_simulation_2026-05-12.json").write_text("{}", encoding="utf-8")
    (report_dir / "swing_lifecycle_audit" / "swing_lifecycle_audit_2026-05-12.json").write_text("{}", encoding="utf-8")
    _write_swing_discovery_sim_artifact(report_dir)
    (project_root / "docs" / "checklists").mkdir(parents=True)
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# next\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "pass"
    assert report["predecessor_integrity"]["wait_count"] == 0
    assert report["workorder_snapshot"]["status"] == "source_changed_with_lineage"
    assert report["workorder_snapshot"]["new_order_ids"] == ["order_new"]
    assert report["downstream_links"]["runtime_approval_summary_sources_ev"].endswith(
        "threshold_cycle_ev_2026-05-12.json"
    )
    assert report["downstream_links"]["threshold_cycle_ev_sources_pattern_lab_currentness_audit"].endswith(
        "pattern_lab_currentness_audit_2026-05-12.json"
    )
    artifact_labels = {item["label"] for item in report["artifact_status"]}
    assert {"market_panic_breadth", "panic_sell_defense", "panic_buying"}.issubset(artifact_labels)

    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[threshold-cycle] artifact ready label=swing_daily_simulation.json path=/tmp/a waited=0s json_valid=true",
                "[threshold-cycle] artifact ready label=threshold_cycle_ev_pre_workorder.json path=/tmp/b waited=0s json_valid=true",
            ]
        ),
        encoding="utf-8",
    )

    pending_report = mod.build_threshold_cycle_postclose_verification(
        "2026-05-12",
        require_done_marker=False,
    )

    assert pending_report["status"] == "pass_with_pending_done_marker"
    assert pending_report["execution_profile"]["status"] == "pending_done_marker"
    assert pending_report["execution_profile"]["pending_done_marker"] is True
    assert pending_report["predecessor_integrity"]["status"] == "pass_pending_done_marker"
    assert "postclose_done_marker_missing" not in pending_report["predecessor_integrity"]["log_issues"]

    strict_missing_report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert strict_missing_report["status"] == "fail"
    assert "postclose_done_marker_missing" in strict_missing_report["predecessor_integrity"]["log_issues"]

    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 recovery_action=marker_reconciliation full_wrapper_rerun=false finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )

    reconciled_report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert reconciled_report["status"] == "pass"
    assert reconciled_report["execution_profile"]["marker_reconciliation_done"] is True
    assert reconciled_report["execution_profile"]["recovery_done"] is True
    assert reconciled_report["execution_profile"]["recovery_action"] == "marker_reconciliation"
    assert reconciled_report["execution_profile"]["required_flags_checked"] is False
    assert reconciled_report["execution_profile"]["missing_required_flags"] == []
    assert "marker_reconciliation" in reconciled_report["execution_profile"]["interpretation"]

    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[FAIL] threshold-cycle postclose target_date=2026-05-12 reason=command_failed failed_at=2026-05-12T21:10:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 recovery_action=tail_repair_done_reconciliation full_wrapper_rerun=false finished_at=2026-05-12T21:35:00+0900",
            ]
        ),
        encoding="utf-8",
    )

    tail_repair_report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert tail_repair_report["status"] == "pass"
    assert tail_repair_report["execution_profile"]["marker_reconciliation_done"] is False
    assert tail_repair_report["execution_profile"]["recovery_done"] is True
    assert tail_repair_report["execution_profile"]["recovery_action"] == "tail_repair_done_reconciliation"
    assert tail_repair_report["execution_profile"]["required_flags_checked"] is False
    assert tail_repair_report["execution_profile"]["missing_required_flags"] == []
    assert "postclose_fail_marker_present" not in tail_repair_report["predecessor_integrity"]["log_issues"]
    assert "tail_repair_done_reconciliation" in tail_repair_report["execution_profile"]["interpretation"]

    strict_report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert strict_report["status"] == "pass"


def test_build_threshold_cycle_postclose_verification_warns_on_predecessor_wait(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    (project_root / "logs").mkdir(parents=True)
    (report_dir / "threshold_cycle_ev").mkdir(parents=True)
    (report_dir / "code_improvement_workorder").mkdir(parents=True)
    (report_dir / "runtime_approval_summary").mkdir(parents=True)
    (report_dir / "pattern_lab_currentness_audit").mkdir(parents=True)
    (report_dir / "pattern_lab_propagation_audit").mkdir(parents=True)
    (report_dir / "market_panic_breadth").mkdir(parents=True)
    (report_dir / "panic_sell_defense").mkdir(parents=True)
    (report_dir / "panic_buying").mkdir(parents=True)
    (report_dir / "swing_daily_simulation").mkdir(parents=True)
    (report_dir / "swing_strategy_discovery_sim").mkdir(parents=True)
    (report_dir / "swing_lifecycle_audit").mkdir(parents=True)
    (project_root / "docs").mkdir(parents=True)
    adm_path = _write_adm_artifact(report_dir)
    lifecycle_path = _write_lifecycle_artifact(report_dir)

    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[threshold-cycle] artifact ready label=swing_daily_simulation.json path=/tmp/a waited=5s json_valid=true",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=true pattern_labs=true deepseek_swing_lab=true pattern_lab_currentness_audit=true pattern_lab_propagation_audit=true scalp_entry_adm=true lifecycle_decision_matrix=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )
    for rel in (
        "threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json",
        "code_improvement_workorder/code_improvement_workorder_2026-05-12.json",
        "runtime_approval_summary/runtime_approval_summary_2026-05-12.json",
        "pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-12.json",
        "pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-12.json",
        "market_panic_breadth/market_panic_breadth_2026-05-12.json",
        "panic_sell_defense/panic_sell_defense_2026-05-12.json",
        "panic_buying/panic_buying_2026-05-12.json",
        "swing_daily_simulation/swing_daily_simulation_2026-05-12.json",
        "swing_strategy_discovery_sim/swing_strategy_discovery_sim_2026-05-12.json",
        "swing_lifecycle_audit/swing_lifecycle_audit_2026-05-12.json",
        "lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-12.json",
    ):
        path = report_dir / rel
        path.write_text("{}", encoding="utf-8")
    (report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "code_improvement_workorder": str(report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json"),
                    "pattern_lab_currentness_audit": str(report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-12.json"),
                    "pattern_lab_propagation_audit": str(report_dir / "pattern_lab_propagation_audit" / "pattern_lab_propagation_audit_2026-05-12.json"),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json").write_text(
        json.dumps(
            {
                "generation_id": "2026-05-12-source",
                "source_hash": "source",
                "lineage": {"previous_exists": False},
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_approval_summary" / "runtime_approval_summary_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "threshold_cycle_ev": str(report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json"),
                    "pattern_lab_propagation_audit": str(report_dir / "pattern_lab_propagation_audit" / "pattern_lab_propagation_audit_2026-05-12.json"),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    (project_root / "docs" / "checklists").mkdir(parents=True)
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# next\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "warning"
    assert report["predecessor_integrity"]["wait_count"] == 1

    (report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json").write_text(
        "{}",
        encoding="utf-8",
    )

    missing_snapshot_report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert missing_snapshot_report["status"] == "fail"
    assert missing_snapshot_report["workorder_snapshot"]["status"] == "missing_snapshot_identity"


def test_build_threshold_cycle_postclose_verification_warns_on_recovery_profile(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    (project_root / "logs").mkdir(parents=True)
    for folder in (
        "threshold_cycle_ev",
        "code_improvement_workorder",
        "runtime_approval_summary",
        "pattern_lab_currentness_audit",
        "pattern_lab_propagation_audit",
        "scalp_entry_action_decision_matrix",
        "lifecycle_decision_matrix",
        "market_panic_breadth",
        "panic_sell_defense",
        "panic_buying",
        "swing_daily_simulation",
        "swing_lifecycle_audit",
    ):
        (report_dir / folder).mkdir(parents=True)
    (project_root / "docs" / "checklists").mkdir(parents=True)

    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=false pattern_labs=false deepseek_swing_lab=false pattern_lab_currentness_audit=false pattern_lab_propagation_audit=false scalp_entry_adm=true lifecycle_decision_matrix=false code_improvement_workorder=true daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )
    for rel in (
        "threshold_cycle_ev/threshold_cycle_ev_2026-05-12.json",
        "code_improvement_workorder/code_improvement_workorder_2026-05-12.json",
        "runtime_approval_summary/runtime_approval_summary_2026-05-12.json",
        "scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_2026-05-12.json",
        "market_panic_breadth/market_panic_breadth_2026-05-12.json",
        "panic_sell_defense/panic_sell_defense_2026-05-12.json",
        "panic_buying/panic_buying_2026-05-12.json",
        "swing_daily_simulation/swing_daily_simulation_2026-05-12.json",
        "swing_lifecycle_audit/swing_lifecycle_audit_2026-05-12.json",
    ):
        (report_dir / rel).write_text(
            json.dumps({"generation_id": "g", "source_hash": "h"} if "code_improvement" in rel else {}),
            encoding="utf-8",
        )
    (report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "code_improvement_workorder": str(report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json"),
                    "scalp_entry_action_decision_matrix": str(
                        report_dir
                        / "scalp_entry_action_decision_matrix"
                        / "scalp_entry_action_decision_matrix_2026-05-12.json"
                    ),
                }
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "runtime_approval_summary" / "runtime_approval_summary_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "threshold_cycle_ev": str(report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json"),
                    "scalp_entry_action_decision_matrix": str(
                        report_dir
                        / "scalp_entry_action_decision_matrix"
                        / "scalp_entry_action_decision_matrix_2026-05-12.json"
                    ),
                }
            }
        ),
        encoding="utf-8",
    )
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# next\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "warning"
    assert report["execution_profile"]["status"] == "recovered_partial_profile"
    assert report["execution_profile"]["disabled_stage_flags"] == [
        "swing_lifecycle",
        "pattern_labs",
        "deepseek_swing_lab",
        "pattern_lab_currentness_audit",
        "pattern_lab_propagation_audit",
        "lifecycle_decision_matrix",
    ]


def test_build_threshold_cycle_postclose_verification_fails_on_unavailable_ai_correction(
    tmp_path, monkeypatch
):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    (project_root / "logs").mkdir(parents=True)
    for folder in (
        "threshold_cycle_ev",
        "threshold_cycle_calibration",
        "threshold_cycle_ai_review",
        "code_improvement_workorder",
        "runtime_approval_summary",
        "pattern_lab_currentness_audit",
        "pattern_lab_propagation_audit",
        "market_panic_breadth",
        "panic_sell_defense",
        "panic_buying",
        "swing_daily_simulation",
        "swing_lifecycle_audit",
    ):
        (report_dir / folder).mkdir(parents=True)
    (project_root / "docs" / "checklists").mkdir(parents=True)
    adm_path = _write_adm_artifact(report_dir)
    lifecycle_path = _write_lifecycle_artifact(report_dir)

    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=true pattern_labs=true deepseek_swing_lab=true pattern_lab_currentness_audit=true pattern_lab_propagation_audit=true scalp_entry_adm=true lifecycle_decision_matrix=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )
    ev_path = report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json"
    workorder_path = (
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json"
    )
    propagation_path = (
        report_dir
        / "pattern_lab_propagation_audit"
        / "pattern_lab_propagation_audit_2026-05-12.json"
    )
    currentness_path = (
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-12.json"
    )
    ev_path.write_text(
        json.dumps(
            {
                "sources": {
                    "code_improvement_workorder": str(workorder_path),
                    "pattern_lab_currentness_audit": str(currentness_path),
                    "pattern_lab_propagation_audit": str(propagation_path),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    workorder_path.write_text(
        json.dumps({"generation_id": "g", "source_hash": "h", "lineage": {}}),
        encoding="utf-8",
    )
    (report_dir / "runtime_approval_summary" / "runtime_approval_summary_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "threshold_cycle_ev": str(ev_path),
                    "pattern_lab_propagation_audit": str(propagation_path),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    for path in (
        currentness_path,
        propagation_path,
        report_dir / "market_panic_breadth" / "market_panic_breadth_2026-05-12.json",
        report_dir / "panic_sell_defense" / "panic_sell_defense_2026-05-12.json",
        report_dir / "panic_buying" / "panic_buying_2026-05-12.json",
        report_dir / "swing_daily_simulation" / "swing_daily_simulation_2026-05-12.json",
        report_dir / "swing_lifecycle_audit" / "swing_lifecycle_audit_2026-05-12.json",
    ):
        path.write_text("{}", encoding="utf-8")
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# next\n",
        encoding="utf-8",
    )
    (report_dir / "threshold_cycle_ai_review" / "threshold_cycle_ai_review_2026-05-12_postclose.json").write_text(
        json.dumps(
            {
                "ai_status": "unavailable",
                "provider_status": "timeout",
                "parse_warnings": ["ai correction response not provided"],
            }
        ),
        encoding="utf-8",
    )
    (
        report_dir
        / "threshold_cycle_calibration"
        / "threshold_cycle_calibration_2026-05-12_postclose.json"
    ).write_text(
        json.dumps(
            {
                "calibration_candidates": [
                    {
                        "family": "lifecycle_decision_matrix_runtime",
                        "calibration_state": "adjust_up",
                        "allowed_runtime_apply": True,
                        "human_approval_required": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "fail"
    assert report["ai_correction"]["status"] == "fail"
    assert report["ai_correction"]["blocking_runtime_candidate_families"] == [
        "lifecycle_decision_matrix_runtime"
    ]
    assert (
        "ai_correction_unavailable_blocks_runtime_candidates"
        in report["predecessor_integrity"]["log_issues"]
    )


def test_build_threshold_cycle_postclose_verification_not_yet_due_before_postclose(tmp_path, monkeypatch):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    (project_root / "logs").mkdir(parents=True)
    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    log_path.write_text("", encoding="utf-8")

    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 5, 12, 15, 59, 0)

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")
    monkeypatch.setattr(mod, "datetime", FakeDateTime)

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "not_yet_due"
    assert report["predecessor_integrity"]["status"] == "not_yet_due"
    assert report["predecessor_integrity"]["log_issues"] == []


def test_build_threshold_cycle_postclose_verification_fails_on_ldm_entry_bucket_handoff_drop(
    tmp_path, monkeypatch
):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    (project_root / "logs").mkdir(parents=True)
    for folder in (
        "threshold_cycle_ev",
        "code_improvement_workorder",
        "runtime_approval_summary",
        "pattern_lab_currentness_audit",
        "pattern_lab_propagation_audit",
        "market_panic_breadth",
        "panic_sell_defense",
        "panic_buying",
        "swing_daily_simulation",
        "swing_lifecycle_audit",
    ):
        (report_dir / folder).mkdir(parents=True)
    (project_root / "docs" / "checklists").mkdir(parents=True)
    adm_path = _write_adm_artifact(report_dir)
    lifecycle_path = report_dir / "lifecycle_decision_matrix" / "lifecycle_decision_matrix_2026-05-12.json"
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_path.write_text(
        json.dumps(
            {
                "entry_bucket_attribution": {
                    "runtime_approval_candidates": [
                        {"candidate_id": "entry_bucket_1", "bucket_type": "score_band", "bucket_key": "score_66_69"}
                    ],
                    "code_improvement_workorders": [
                        {"bucket_type": "liquidity_bucket", "bucket_key": "liquidity_unknown"}
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=true pattern_labs=true deepseek_swing_lab=true pattern_lab_currentness_audit=true pattern_lab_propagation_audit=true scalp_entry_adm=true lifecycle_decision_matrix=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )
    workorder_path = report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json"
    ev_path = report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json"
    propagation_path = report_dir / "pattern_lab_propagation_audit" / "pattern_lab_propagation_audit_2026-05-12.json"
    currentness_path = report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-12.json"
    ev_path.write_text(
        json.dumps(
            {
                "sources": {
                    "code_improvement_workorder": str(workorder_path),
                    "pattern_lab_currentness_audit": str(currentness_path),
                    "pattern_lab_propagation_audit": str(propagation_path),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    workorder_path.write_text(json.dumps({"generation_id": "g", "source_hash": "h", "orders": []}), encoding="utf-8")
    (report_dir / "runtime_approval_summary" / "runtime_approval_summary_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "threshold_cycle_ev": str(ev_path),
                    "pattern_lab_propagation_audit": str(propagation_path),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    for path in (
        currentness_path,
        propagation_path,
        report_dir / "market_panic_breadth" / "market_panic_breadth_2026-05-12.json",
        report_dir / "panic_sell_defense" / "panic_sell_defense_2026-05-12.json",
        report_dir / "panic_buying" / "panic_buying_2026-05-12.json",
        report_dir / "swing_daily_simulation" / "swing_daily_simulation_2026-05-12.json",
        report_dir / "swing_lifecycle_audit" / "swing_lifecycle_audit_2026-05-12.json",
    ):
        path.write_text("{}", encoding="utf-8")
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# next\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "fail"
    assert report["entry_bucket_handoff"]["status"] == "fail"
    assert report["entry_bucket_handoff"]["missing_ev_candidate_ids"] == ["entry_bucket_1"]
    assert report["entry_bucket_handoff"]["missing_runtime_summary_candidate_ids"] == ["entry_bucket_1"]
    assert report["entry_bucket_handoff"]["missing_workorder_order_ids"] == [
        "order_lifecycle_entry_bucket_liquidity_bucket_liquidity_unknown"
    ]
    assert "ldm_entry_bucket_handoff_missing" in report["predecessor_integrity"]["log_issues"]


def test_build_threshold_cycle_postclose_verification_fails_on_ldm_scale_in_bucket_handoff_drop(
    tmp_path, monkeypatch
):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    (project_root / "logs").mkdir(parents=True)
    for folder in (
        "threshold_cycle_ev",
        "code_improvement_workorder",
        "runtime_approval_summary",
        "pattern_lab_currentness_audit",
        "pattern_lab_propagation_audit",
        "market_panic_breadth",
        "panic_sell_defense",
        "panic_buying",
        "swing_daily_simulation",
        "swing_lifecycle_audit",
    ):
        (report_dir / folder).mkdir(parents=True)
    (project_root / "docs" / "checklists").mkdir(parents=True)
    adm_path = _write_adm_artifact(report_dir)
    lifecycle_path = report_dir / "lifecycle_decision_matrix" / "lifecycle_decision_matrix_2026-05-12.json"
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_path.write_text(
        json.dumps(
            {
                "sources": {"scale_in_attribution": {"rows": 12}},
                "scale_in_bucket_attribution": {
                    "runtime_approval_candidates": [
                        {"candidate_id": "scale_in_bucket_1", "bucket_type": "arm", "bucket_key": "PYRAMID"}
                    ],
                    "code_improvement_workorders": [
                        {"bucket_type": "blocker_namespace", "bucket_key": "PRICE_GUARD"}
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=true pattern_labs=true deepseek_swing_lab=true pattern_lab_currentness_audit=true pattern_lab_propagation_audit=true scalp_entry_adm=true lifecycle_decision_matrix=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )
    workorder_path = report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json"
    ev_path = report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json"
    propagation_path = report_dir / "pattern_lab_propagation_audit" / "pattern_lab_propagation_audit_2026-05-12.json"
    currentness_path = report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-12.json"
    ev_path.write_text(
        json.dumps(
            {
                "sources": {
                    "code_improvement_workorder": str(workorder_path),
                    "pattern_lab_currentness_audit": str(currentness_path),
                    "pattern_lab_propagation_audit": str(propagation_path),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    workorder_path.write_text(json.dumps({"generation_id": "g", "source_hash": "h", "orders": []}), encoding="utf-8")
    (report_dir / "runtime_approval_summary" / "runtime_approval_summary_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "threshold_cycle_ev": str(ev_path),
                    "pattern_lab_propagation_audit": str(propagation_path),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    for path in (
        currentness_path,
        propagation_path,
        report_dir / "market_panic_breadth" / "market_panic_breadth_2026-05-12.json",
        report_dir / "panic_sell_defense" / "panic_sell_defense_2026-05-12.json",
        report_dir / "panic_buying" / "panic_buying_2026-05-12.json",
        report_dir / "swing_daily_simulation" / "swing_daily_simulation_2026-05-12.json",
        report_dir / "swing_lifecycle_audit" / "swing_lifecycle_audit_2026-05-12.json",
    ):
        path.write_text("{}", encoding="utf-8")
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# next\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "fail"
    assert report["scale_in_bucket_handoff"]["status"] == "fail"
    assert report["scale_in_bucket_handoff"]["missing_ev_candidate_ids"] == ["scale_in_bucket_1"]
    assert report["scale_in_bucket_handoff"]["missing_runtime_summary_candidate_ids"] == ["scale_in_bucket_1"]
    assert report["scale_in_bucket_handoff"]["missing_workorder_order_ids"] == [
        "order_lifecycle_scale_in_bucket_blocker_namespace_price_guard"
    ]
    assert "ldm_scale_in_bucket_handoff_missing" in report["predecessor_integrity"]["log_issues"]


def test_build_threshold_cycle_postclose_verification_fails_when_scale_in_source_lacks_attribution(
    tmp_path, monkeypatch
):
    project_root = tmp_path
    report_dir = project_root / "data" / "report"
    (project_root / "logs").mkdir(parents=True)
    for folder in (
        "threshold_cycle_ev",
        "code_improvement_workorder",
        "runtime_approval_summary",
        "pattern_lab_currentness_audit",
        "pattern_lab_propagation_audit",
        "market_panic_breadth",
        "panic_sell_defense",
        "panic_buying",
        "swing_daily_simulation",
        "swing_lifecycle_audit",
    ):
        (report_dir / folder).mkdir(parents=True)
    (project_root / "docs" / "checklists").mkdir(parents=True)
    adm_path = _write_adm_artifact(report_dir)
    lifecycle_path = report_dir / "lifecycle_decision_matrix" / "lifecycle_decision_matrix_2026-05-12.json"
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_path.write_text(
        json.dumps({"sources": {"scale_in_attribution": {"rows": 3}}, "summary": {"stage_counts": {"scale_in": 3}}}),
        encoding="utf-8",
    )
    log_path = project_root / "logs" / "threshold_cycle_postclose_cron.log"
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-05-12 started_at=2026-05-12T21:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-05-12 swing_lifecycle=true pattern_labs=true deepseek_swing_lab=true pattern_lab_currentness_audit=true pattern_lab_propagation_audit=true scalp_entry_adm=true lifecycle_decision_matrix=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true next_stage2_checklist=true finished_at=2026-05-12T21:30:00+0900",
            ]
        ),
        encoding="utf-8",
    )
    workorder_path = report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-12.json"
    ev_path = report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-12.json"
    propagation_path = report_dir / "pattern_lab_propagation_audit" / "pattern_lab_propagation_audit_2026-05-12.json"
    currentness_path = report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-12.json"
    ev_path.write_text(
        json.dumps(
            {
                "sources": {
                    "code_improvement_workorder": str(workorder_path),
                    "pattern_lab_currentness_audit": str(currentness_path),
                    "pattern_lab_propagation_audit": str(propagation_path),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    workorder_path.write_text(json.dumps({"generation_id": "g", "source_hash": "h", "orders": []}), encoding="utf-8")
    (report_dir / "runtime_approval_summary" / "runtime_approval_summary_2026-05-12.json").write_text(
        json.dumps(
            {
                "sources": {
                    "threshold_cycle_ev": str(ev_path),
                    "pattern_lab_propagation_audit": str(propagation_path),
                    "scalp_entry_action_decision_matrix": str(adm_path),
                    "lifecycle_decision_matrix": str(lifecycle_path),
                }
            }
        ),
        encoding="utf-8",
    )
    for path in (
        currentness_path,
        propagation_path,
        report_dir / "market_panic_breadth" / "market_panic_breadth_2026-05-12.json",
        report_dir / "panic_sell_defense" / "panic_sell_defense_2026-05-12.json",
        report_dir / "panic_buying" / "panic_buying_2026-05-12.json",
        report_dir / "swing_daily_simulation" / "swing_daily_simulation_2026-05-12.json",
        report_dir / "swing_lifecycle_audit" / "swing_lifecycle_audit_2026-05-12.json",
    ):
        path.write_text("{}", encoding="utf-8")
    (project_root / "docs" / "checklists" / "2026-05-13-stage2-todo-checklist.md").write_text(
        "# next\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "VERIFY_DIR", report_dir / "threshold_cycle_postclose_verification")
    monkeypatch.setattr(mod, "LOG_PATH", log_path)
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda target_date: "2026-05-13")

    report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert report["status"] == "fail"
    assert report["scale_in_source_present"] is True
    assert report["scale_in_bucket_attribution_present"] is False
    assert "ldm_scale_in_bucket_attribution_missing" in report["predecessor_integrity"]["log_issues"]
