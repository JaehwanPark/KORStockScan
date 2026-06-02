import json
from pathlib import Path

import pytest

from src.engine import build_next_stage2_checklist as mod
from src.engine.sync_docs_backlog_to_project import parse_checklist_tasks


def _patch_dirs(monkeypatch, tmp_path):
    docs = tmp_path / "docs"
    ev = tmp_path / "data" / "report" / "threshold_cycle_ev"
    openai = tmp_path / "data" / "report" / "openai_ws"
    swing = tmp_path / "data" / "report" / "swing_runtime_approval"
    code = tmp_path / "data" / "report" / "code_improvement_workorder"
    runtime_gap = tmp_path / "data" / "report" / "runtime_apply_gap_audit"
    tuning_performance = tmp_path / "data" / "report" / "tuning_performance_control_tower"
    trigger_decision = tmp_path / "data" / "report" / "automation_chain_trigger_decision"
    for path in (docs, ev, openai, swing, code, runtime_gap, tuning_performance, trigger_decision):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "DOCS_DIR", docs)
    monkeypatch.setattr(mod, "CHECKLIST_DIR", docs / "checklists")
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev)
    monkeypatch.setattr(mod, "OPENAI_WS_REPORT_DIR", openai)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_REPORT_DIR", code)
    monkeypatch.setattr(mod, "RUNTIME_APPLY_GAP_REPORT_DIR", runtime_gap)
    monkeypatch.setattr(mod, "TUNING_PERFORMANCE_REPORT_DIR", tuning_performance)
    monkeypatch.setattr(mod, "AUTOMATION_TRIGGER_DECISION_REPORT_DIR", trigger_decision)
    return docs, ev, openai, swing, code


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_next_stage2_checklist_generates_next_trading_day_and_tasks(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    trigger_dir = mod.AUTOMATION_TRIGGER_DECISION_REPORT_DIR
    tuning_dir = mod.TUNING_PERFORMANCE_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-08.json",
        {
            "runtime_apply": {
                "runtime_change": True,
                "selected_families": ["score65_74_recovery_probe"],
            },
            "scalp_simulator": {"event_count": 3},
            "code_improvement_workorder": {"selected_order_count": 2},
        },
    )
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-08.json",
        {
            "decision": "keep_ws",
            "entry_price_canary_summary": {
                "canary_event_count": 2,
                "transport_observable_count": 0,
                "instrumentation_gap": True,
            },
        },
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-08.json", {"approval_requests": [{"id": "req"}]})
    _write_json(code_dir / "code_improvement_workorder_2026-05-08.json", {"summary": {"selected_order_count": 2}})
    _write_json(tuning_dir / "tuning_performance_control_tower_2026-05-08.json", {"summary": {}})
    (docs / "code-improvement-workorders").mkdir(parents=True, exist_ok=True)
    (docs / "code-improvement-workorders" / "code_improvement_workorder_2026-05-08.md").write_text(
        "# workorder",
        encoding="utf-8",
    )
    _write_json(
        trigger_dir / "automation_chain_trigger_decision_2026-05-08.json",
        {"summary": {"total_steps": 1, "run_count": 1, "skip_count": 0}, "decisions": []},
    )

    summary = mod.build_next_stage2_checklist("2026-05-08")

    assert summary["target_date"] == "2026-05-11"
    checklist = docs / "checklists" / "2026-05-11-stage2-todo-checklist.md"
    text = checklist.read_text(encoding="utf-8")
    assert "[ThresholdEnvAutoApplyPreopen0511]" in text
    assert "[SwingPreFinalAutoAndFinalApprovalPreopen0511]" in text
    assert "[RuntimeEnvIntradayObserve0511]" in text
    assert "[AITransportIntradaySample0511]" in text
    assert "[SimProbeIntradayCoverage0511]" in text
    assert "[CodeImprovementWorkorderReview0511]" in text
    assert "[AutomationTriggerDecisionSummary0511]" in text
    assert "tuning_performance_control_tower_2026-05-08.json" in text
    assert "codex_daily_workorder_*.md" in text


def test_build_next_stage2_checklist_preserves_manual_content_and_replaces_auto_block(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-11.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(openai_dir / "openai_ws_stability_2026-05-11.json", {"decision": "keep_ws"})
    _write_json(swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-11.json", {"summary": {"selected_order_count": 0}})
    target = docs / "checklists" / "2026-05-12-stage2-todo-checklist.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            [
                "# 2026-05-12 Stage2 To-Do Checklist",
                "",
                "- [ ] `[ThresholdEnvAutoApplyPreopen0512] 수동 장전 항목` (`Due: 2026-05-12`, `Slot: PREOPEN`, `TimeWindow: 08:50~09:00`, `Track: RuntimeStability`)",
                "",
                "manual-only-line",
                "",
                "## Project/Calendar 동기화",
                "",
                "manual-sync-line",
            ]
        ),
        encoding="utf-8",
    )

    mod.build_next_stage2_checklist("2026-05-11")
    mod.build_next_stage2_checklist("2026-05-11")

    text = target.read_text(encoding="utf-8")
    assert "manual-only-line" in text
    assert "manual-sync-line" in text
    assert text.count("ThresholdEnvAutoApplyPreopen0512") == 1
    assert text.count(mod.AUTO_START) == 1
    assert text.count(mod.AUTO_END) == 1


def test_build_next_stage2_checklist_excludes_codex_daily_workorder_snapshots(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    (docs / "code-improvement-workorders").mkdir(parents=True, exist_ok=True)
    (docs / "code-improvement-workorders" / "codex_daily_workorder_2026-05-11_PREOPEN.md").write_text(
        "FakeCodexOnlyFamily",
        encoding="utf-8",
    )
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-11.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-11.json",
        {"decision": "keep_ws", "entry_price_canary_summary": {"canary_event_count": 0}},
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-11.json", {"summary": {"selected_order_count": 0}})

    mod.build_next_stage2_checklist("2026-05-11")

    text = (docs / "checklists" / "2026-05-12-stage2-todo-checklist.md").read_text(encoding="utf-8")
    assert "FakeCodexOnlyFamily" not in text
    assert "RuntimeEnvIntradayObserve0512" not in text


def test_generated_checklist_is_parser_friendly(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    trigger_dir = mod.AUTOMATION_TRIGGER_DECISION_REPORT_DIR
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-11.json", {"runtime_apply": {"runtime_change": True}})
    _write_json(openai_dir / "openai_ws_stability_2026-05-11.json", {"decision": "rollback_http"})
    _write_json(swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-11.json", {"summary": {"selected_order_count": 1}})
    _write_json(
        trigger_dir / "automation_chain_trigger_decision_2026-05-11.json",
        {"summary": {"total_steps": 1, "run_count": 1, "skip_count": 0}, "decisions": []},
    )

    mod.build_next_stage2_checklist("2026-05-11")
    checklist = docs / "checklists" / "2026-05-12-stage2-todo-checklist.md"
    monkeypatch.setenv("DOC_BACKLOG_TODAY", "2026-05-11")
    monkeypatch.setenv("DOC_CHECKLIST_PATH", str(checklist))

    tasks = [task for task in parse_checklist_tasks() if task.source == str(checklist)]
    titles = [task.title for task in tasks]

    assert any("ThresholdEnvAutoApplyPreopen0512" in title for title in titles)
    assert any("RuntimeEnvIntradayObserve0512" in title for title in titles)
    assert any("AITransportPreopenConfirm0512" in title for title in titles)
    assert any("AutomationTriggerDecisionSummary0512" in title for title in titles)
    assert all(task.due_date == "2026-05-12" for task in tasks)


def test_build_next_stage2_checklist_refuses_to_write_when_core_postclose_artifacts_are_missing(monkeypatch, tmp_path):
    docs, _, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    trigger_dir = mod.AUTOMATION_TRIGGER_DECISION_REPORT_DIR
    _write_json(
        trigger_dir / "automation_chain_trigger_decision_2026-06-02.json",
        {"summary": {"total_steps": 1, "run_count": 1}, "decisions": []},
    )

    with pytest.raises(RuntimeError, match="required postclose artifacts are missing"):
        mod.build_next_stage2_checklist("2026-06-02")

    assert not (docs / "checklists" / "2026-06-04-stage2-todo-checklist.md").exists()


def test_build_next_stage2_checklist_skips_optional_tasks_when_optional_artifacts_are_missing(monkeypatch, tmp_path):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-22.json", {"runtime_apply": {"runtime_change": False}})

    summary = mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(encoding="utf-8")
    assert summary["tasks"] == [
        "ThresholdEnvAutoApplyPreopen0526",
        "ThresholdDailyEVReport0526",
        "HumanInterventionSummary0526",
    ]
    assert "AITransportPreopenConfirm0526" not in text
    assert "AITransportIntradaySample0526" not in text
    assert "CodeImprovementWorkorderReview0526" not in text
    assert "AutomationTriggerDecisionSummary0526" not in text
    assert "tuning_performance_control_tower_2026-05-22.json" not in text


def test_automation_trigger_decision_summary_is_surfaced_as_postclose_task(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    trigger_dir = mod.AUTOMATION_TRIGGER_DECISION_REPORT_DIR
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-22.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-22.json",
        {"decision": "keep_ws", "entry_price_canary_summary": {"canary_event_count": 0}},
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-22.json", {"summary": {"selected_order_count": 0}})
    _write_json(
        trigger_dir / "automation_chain_trigger_decision_2026-05-22.json",
        {
            "summary": {
                "total_steps": 3,
                "run_count": 1,
                "skip_count": 2,
                "source_missing_count": 1,
                "force_override_count": 0,
            },
            "decisions": [
                {
                    "step_id": "lifecycle_window_mtd",
                    "decision": "run",
                    "source_missing": True,
                    "trigger_reasons": ["source_missing_or_unreadable"],
                },
                {
                    "step_id": "pattern_lab_ai_review",
                    "decision": "skip",
                    "source_missing": False,
                    "trigger_reasons": ["source_and_output_fresh"],
                },
                {
                    "step_id": "workorder_branch",
                    "decision": "skip",
                    "source_missing": False,
                    "trigger_reasons": ["source_and_output_fresh"],
                },
            ],
        },
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(encoding="utf-8")
    assert "[AutomationTriggerDecisionSummary0526]" in text
    assert "automation_chain_trigger_decision_2026-05-22.json" in text
    assert "run_count=`1`" in text
    assert "skip_count=`2`" in text
    assert "source_missing_count=`1`" in text
    assert "run_steps_sample=`lifecycle_window_mtd`" in text
    assert "skip_steps_sample=`pattern_lab_ai_review, workorder_branch`" in text
    assert "source_and_output_fresh:2" in text
    assert "`[SKIP] threshold-cycle postclose ... trigger_decision=skip`" in text
    assert "`skip_marker_missing`" in text


def test_runtime_apply_gap_pending_is_surfaced_in_preopen_task(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    runtime_gap_dir = mod.RUNTIME_APPLY_GAP_REPORT_DIR
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-22.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-22.json",
        {"decision": "keep_ws", "entry_price_canary_summary": {"canary_event_count": 0}},
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-22.json", {"summary": {"selected_order_count": 0}})
    _write_json(
        runtime_gap_dir / "runtime_apply_gap_audit_2026-05-22.json",
        {
            "candidate_route_ledger": [
                {
                    "candidate_id": "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22",
                    "family": "entry_wait6579_score66_69_recovery_gate_v1",
                    "final_disposition": "post_apply_attribution_pending",
                    "failure_state": "retry_pending",
                    "failure_reason": "ready_but_not_applied",
                    "next_retry_stage": "preopen_apply_candidate",
                }
            ],
            "retry_queue": [],
        },
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(encoding="utf-8")
    assert "runtime_apply_gap_audit_2026-05-22.json" in text
    assert "post_apply_attribution_pending" in text
    assert "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22" in text
    assert "runtime_gap_pending_not_consumed" in text


def test_runtime_apply_gap_codex_directives_are_surfaced_as_postclose_task(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    runtime_gap_dir = mod.RUNTIME_APPLY_GAP_REPORT_DIR
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-22.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-22.json",
        {"decision": "keep_ws", "entry_price_canary_summary": {"canary_event_count": 0}},
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-22.json", {"summary": {"selected_order_count": 0}})
    _write_json(
        runtime_gap_dir / "runtime_apply_gap_audit_2026-05-22.json",
        {
            "summary": {"codex_directive_count": 1},
            "candidate_route_ledger": [],
            "retry_queue": [],
            "codex_workorder_directives": [
                {
                    "directive_type": "IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET",
                    "candidate_id": "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22",
                    "blocking_contract": "env_mapping_contract",
                }
            ],
        },
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(encoding="utf-8")
    assert "[RuntimeApplyGapDirectiveReview0526]" in text
    assert "runtime apply gap Codex 작업지시" in text
    assert "IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET" in text
    assert "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22" in text
    assert "approval artifact나 즉시 runtime env 수정" in text


def test_source_dimension_gap_summary_is_surfaced_even_without_directives(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    runtime_gap_dir = mod.RUNTIME_APPLY_GAP_REPORT_DIR
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-22.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-22.json",
        {"decision": "keep_ws", "entry_price_canary_summary": {"canary_event_count": 0}},
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-22.json", {"summary": {"selected_order_count": 0}})
    _write_json(
        runtime_gap_dir / "runtime_apply_gap_audit_2026-05-22.json",
        {
            "summary": {"codex_directive_count": 0, "actionable_unknown_gap_count": 2},
            "candidate_route_ledger": [],
            "retry_queue": [],
            "codex_workorder_directives": [],
            "source_dimension_gap_summary": {
                "gap_count": 3,
                "actionable_unknown_gap_count": 2,
                "recommended_resolution_counts": {"resolve_unknown_source_dimensions": 2},
                "missing_dimension_key_counts": {"liquidity_bucket": 2},
            },
        },
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(encoding="utf-8")
    assert "[LifecycleSourceDimensionGapReview0526]" in text
    assert "lifecycle source dimension gap 자동 표면화" in text
    assert "actionable_unknown_gap_count=`2`" in text
    assert "`already_covered_by_fallback`" in text


def test_quiet_gap_summary_is_surfaced_even_without_directives(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    runtime_gap_dir = mod.RUNTIME_APPLY_GAP_REPORT_DIR
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-22.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-22.json",
        {"decision": "keep_ws", "entry_price_canary_summary": {"canary_event_count": 0}},
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-22.json", {"summary": {"selected_order_count": 0}})
    _write_json(
        runtime_gap_dir / "runtime_apply_gap_audit_2026-05-22.json",
        {
            "summary": {"codex_directive_count": 0, "quiet_gap_count": 2},
            "candidate_route_ledger": [],
            "retry_queue": [],
            "codex_workorder_directives": [],
            "quiet_gap_summary": {
                "quiet_gap_count": 2,
                "rollup_required_count": 2,
                "sim_live_connected_quiet_gap_count": 0,
                "observation_source_quality_warning_count": 1,
                "quiet_gap_type_counts": {"parent_conflict_child": 1, "positive_source_only_keep_collecting": 1},
            },
        },
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(encoding="utf-8")
    assert "[LifecycleQuietGapReview0526]" in text
    assert "lifecycle quiet gap rollup 자동 표면화" in text
    assert "quiet_gap_count=`2`" in text
    assert "`already_covered_by_parent_policy`" in text


def test_build_next_stage2_checklist_preserves_unknown_tasks_inside_auto_block(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_json(ev_dir / "threshold_cycle_ev_2026-05-22.json", {"runtime_apply": {"runtime_change": False}})
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-22.json",
        {"decision": "keep_ws", "entry_price_canary_summary": {"canary_event_count": 0}},
    )
    _write_json(swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []})
    _write_json(code_dir / "code_improvement_workorder_2026-05-22.json", {"summary": {"selected_order_count": 0}})
    target = docs / "checklists" / "2026-05-26-stage2-todo-checklist.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            [
                "# 2026-05-26 Stage2 To-Do Checklist",
                "",
                mod.AUTO_START,
                "## 자동 생성 체크리스트 (`2026-05-22` postclose -> `2026-05-26`)",
                "",
                "## 장전 체크리스트 (08:45~09:00)",
                "",
                "- [ ] `[CustomPreopen0526] 자동 블록 안 수동 보강 항목` (`Due: 2026-05-26`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: RuntimeStability`)",
                "  - Source: [manual.md](/home/ubuntu/KORStockScan/docs/manual.md)",
                "  - 판정 기준: 지우면 안 된다.",
                "",
                "## 장후 체크리스트 (16:30~18:55)",
                "",
                "- [ ] `[CustomPostclose0526] 자동 블록 안 장후 보강 항목` (`Due: 2026-05-26`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:10`, `Track: Plan`)",
                "  - Source: [manual.md](/home/ubuntu/KORStockScan/docs/manual.md)",
                "  - 판정 기준: 지우면 안 된다.",
                "",
                mod.AUTO_END,
            ]
        ),
        encoding="utf-8",
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = target.read_text(encoding="utf-8")
    assert "[ThresholdEnvAutoApplyPreopen0526]" in text
    assert "[CustomPreopen0526]" in text
    assert "[CustomPostclose0526]" in text
    assert text.index("[CustomPreopen0526]") < text.index("## 장중 체크리스트")
    assert text.index("[CustomPostclose0526]") > text.index("## 장후 체크리스트")
