import json
from datetime import datetime
from pathlib import Path

from src.engine import verify_threshold_cycle_postclose_chain as mod


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


def test_consumer_stale_detects_generated_at_ordering():
    consumer = {"generated_at": "2026-05-12T21:20:00+09:00"}
    source = {"generated_at": "2026-05-12T21:21:00+09:00"}

    assert mod._consumer_stale(consumer, source) is True
    assert mod._consumer_stale(source, consumer) is False


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

    strict_report = mod.build_threshold_cycle_postclose_verification("2026-05-12")

    assert strict_report["status"] == "fail"
    assert "postclose_done_marker_missing" in strict_report["predecessor_integrity"]["log_issues"]


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
