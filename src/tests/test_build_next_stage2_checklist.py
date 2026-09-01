import hashlib
import json
import os
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

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
    tuning_performance = (
        tmp_path / "data" / "report" / "tuning_performance_control_tower"
    )
    trigger_decision = (
        tmp_path / "data" / "report" / "automation_chain_trigger_decision"
    )
    rising_missed = tmp_path / "data" / "report" / "rising_missed_scout_workorder"
    main_ai_quality = tmp_path / "data" / "report" / "main_ai_quality_r0_r3"
    machine_micro_approval = (
        tmp_path / "data" / "report" / "machine_microstructure_policy_approval"
    )
    machine_micro_attribution = (
        tmp_path / "data" / "report" / "machine_microstructure_attribution"
    )
    for path in (
        docs,
        ev,
        openai,
        swing,
        code,
        runtime_gap,
        tuning_performance,
        trigger_decision,
        rising_missed,
        main_ai_quality,
        machine_micro_approval,
        machine_micro_attribution,
    ):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "DOCS_DIR", docs)
    monkeypatch.setattr(mod, "CHECKLIST_DIR", docs / "checklists")
    monkeypatch.setattr(mod, "CHECKLIST_LOCK_DIR", tmp_path / "checklist-locks")
    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev)
    monkeypatch.setattr(mod, "OPENAI_WS_REPORT_DIR", openai, raising=False)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_REPORT_DIR", code)
    monkeypatch.setattr(mod, "RUNTIME_APPLY_GAP_REPORT_DIR", runtime_gap)
    monkeypatch.setattr(mod, "TUNING_PERFORMANCE_REPORT_DIR", tuning_performance)
    monkeypatch.setattr(mod, "AUTOMATION_TRIGGER_DECISION_REPORT_DIR", trigger_decision)
    monkeypatch.setattr(mod, "RISING_MISSED_SCOUT_WORKORDER_REPORT_DIR", rising_missed)
    monkeypatch.setattr(mod, "MAIN_AI_QUALITY_REPORT_DIR", main_ai_quality)
    monkeypatch.setattr(
        mod,
        "MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR",
        machine_micro_approval,
    )
    monkeypatch.setattr(
        mod,
        "MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_DIR",
        machine_micro_attribution,
    )
    return docs, ev, openai, swing, code


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _main_ai_quality_report(source_date: str, owners: list[str]) -> dict:
    workorders = []
    for owner in owners:
        content = {
            "target_date": source_date,
            "owner": owner,
            "reason_codes": [f"{owner}=1"],
            "acceptance_test": f"{owner} acceptance closes",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        workorders.append(
            {
                "schema": "main_ai_quality_source_only_gap_workorder_v1",
                "workorder_id": f"main-ai-gap-{mod._canonical_sha256(content)[:24]}",
                "status": "open_source_producer_repair",
                **content,
            }
        )
    body = {
        "schema": "main_ai_quality_postclose_r0_r3_cycle_v1",
        "target_date": source_date,
        "decision_authority": "postclose_source_only_ai_quality_research",
        "source_gap_diagnostics": {
            "schema": "main_ai_quality_source_only_gap_diagnostics_v1",
            "target_date": source_date,
            "contract_findings": [],
            "workorders": workorders,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "source_only_gap_workorders": workorders,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "artifact_content_sha256": mod._canonical_sha256(body)}


def _write_machine_micro_approval_report(path: Path, payload: dict) -> None:
    source_date = str(payload.get("target_date") or "")
    attribution_path = (
        mod.MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_DIR
        / f"machine_microstructure_attribution_{source_date}.json"
    )
    _write_json(
        attribution_path,
        {
            "schema": "machine_microstructure_attribution_v1",
            "target_date": source_date,
            "generated_at_kst": datetime.now().astimezone().isoformat(),
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        },
    )
    source_bytes = attribution_path.read_bytes()
    source_stat = attribution_path.stat()
    enriched = dict(payload)
    enriched.setdefault(
        "generated_at_kst",
        datetime.fromtimestamp(source_stat.st_mtime)
        .astimezone()
        .isoformat(timespec="seconds"),
    )
    enriched["source_path"] = str(attribution_path)
    enriched["source_artifact"] = {
        "schema": "machine_microstructure_policy_source_artifact_provenance_v1",
        "path": str(attribution_path),
        "sha256": hashlib.sha256(source_bytes).hexdigest(),
        "mtime_ns": source_stat.st_mtime_ns,
        "size_bytes": source_stat.st_size,
    }
    _write_json(path, enriched)


def _machine_micro_approval_report(
    source_date: str,
    *,
    objective_followups: list[dict] | None = None,
    actionable_candidates: list[dict] | None = None,
    source_status: str = "loaded",
    objective_followup_source_status: str = "loaded",
    objective_followup_rejections: list[dict] | None = None,
) -> dict:
    objectives = [
        {
            "schema": "machine_fast_lifecycle_objective_followup_v1",
            "source_date": source_date,
            "operator_decision_required": False,
            "metric_contract": {
                "decision_authority": "postclose_followup_tracking_only"
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            **row,
        }
        for row in (objective_followups or [])
    ]
    candidates = list(actionable_candidates or [])
    rejections = list(objective_followup_rejections or [])
    return {
        "schema": "machine_microstructure_policy_approval_status_v1",
        "report_type": "machine_microstructure_policy_approval",
        "phase": "postclose",
        "target_date": source_date,
        "source_status": source_status,
        "objective_followup_source_status": objective_followup_source_status,
        "summary": {
            "actionable_candidate_count": len(candidates),
            "actionable_objective_followup_count": len(objectives),
            "objective_followup_rejection_count": len(rejections),
        },
        "actionable_candidates": candidates,
        "objective_followups": objectives,
        "objective_followup_rejections": rejections,
        "authority": {
            "runtime_effect": False,
            "runtime_apply_performed": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }


def test_build_next_stage2_checklist_generates_next_trading_day_and_tasks(
    monkeypatch, tmp_path
):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    trigger_dir = mod.AUTOMATION_TRIGGER_DECISION_REPORT_DIR
    tuning_dir = mod.TUNING_PERFORMANCE_REPORT_DIR
    rising_missed_dir = mod.RISING_MISSED_SCOUT_WORKORDER_REPORT_DIR
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
        swing_dir / "swing_runtime_approval_2026-05-08.json",
        {"approval_requests": [{"id": "req"}]},
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-08.json",
        {"summary": {"selected_order_count": 2}},
    )
    _write_json(
        tuning_dir / "tuning_performance_control_tower_2026-05-08.json", {"summary": {}}
    )
    (docs / "code-improvement-workorders").mkdir(parents=True, exist_ok=True)
    (
        docs
        / "code-improvement-workorders"
        / "code_improvement_workorder_2026-05-08.md"
    ).write_text(
        "# workorder",
        encoding="utf-8",
    )
    _write_json(
        trigger_dir / "automation_chain_trigger_decision_2026-05-08.json",
        {
            "summary": {"total_steps": 1, "run_count": 1, "skip_count": 0},
            "decisions": [],
        },
    )
    _write_json(
        rising_missed_dir / "rising_missed_scout_workorder_2026-05-08.json",
        {
            "summary": {
                "code_improvement_order_count": 2,
                "forced_scout_with_post_sell_count": 5,
                "profitable_forced_scout_count": 3,
                "loss_or_flat_forced_scout_count": 2,
                "current_missed_count": 4,
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
    )
    summary = mod.build_next_stage2_checklist("2026-05-08")

    assert summary["target_date"] == "2026-05-11"
    checklist = docs / "checklists" / "2026-05-11-stage2-todo-checklist.md"
    text = checklist.read_text(encoding="utf-8")
    assert "[ThresholdEnvAutoApplyPreopen0511]" in text
    assert "[RisingMissedScoutRuntimePreopen0511]" in text
    assert "rising_missed_scout_workorder_2026-05-08.json" in text
    assert "rising_missed_normal_buy_bridge_candidate_discovery" not in text
    assert (
        "source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영"
        in text
    )
    assert "runtime_env_reflected_and_verified" in text
    assert "stale submit bypass" in text
    assert "[SwingPreFinalAutoAndFinalApprovalPreopen0511]" in text
    assert "[RuntimeEnvIntradayObserve0511]" in text
    assert "candidate_selected_families=score65_74_recovery_probe" in text
    assert "selection_change_summary" in text
    assert "실제 기동 기대 목록으로 직접 사용하지 않는다" in text
    assert "사용자 명시 override는 fresh/conflict-free source" in text
    assert "장중 runtime threshold mutation은 금지한다" not in text
    assert "기존 `bounded_tunable` 단일 축에 한해 허용" in text
    assert "[SimProbeIntradayCoverage0511]" in text
    assert "[IntradaySourceQualityGateCheck0511]" in text
    assert "[PostcloseSourceQualityGateReview0511]" in text
    assert "## 장전 체크리스트 (07:45~09:00)" in text
    assert "## 장후 체크리스트 (16:25~21:55)" in text
    assert "TimeWindow: 21:40~21:55" in next(
        line
        for line in text.splitlines()
        if "[PostcloseSourceQualityGateReview0511]" in line
    )
    assert "unknown-token warning" in text
    assert "[CodeImprovementWorkorderReview0511]" in text
    assert "terminal_non_implement_longstanding" in text
    assert "repeat_unresolved_structural_blocker" in text
    assert "keep_visible_by_design" in text
    assert "[AutomationTriggerDecisionSummary0511]" in text
    assert "tuning_performance_control_tower_2026-05-08.json" in text
    assert "codex_daily_workorder_*.md" in text


def test_build_next_stage2_checklist_preserves_manual_content_and_replaces_auto_block(
    monkeypatch, tmp_path
):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-11.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-11.json",
        {"summary": {"selected_order_count": 0}},
    )
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
    first_render = target.read_text(encoding="utf-8")
    mod.build_next_stage2_checklist("2026-05-11")

    text = target.read_text(encoding="utf-8")
    assert text == first_render
    assert "manual-only-line" in text
    assert "manual-sync-line" in text
    assert text.count("ThresholdEnvAutoApplyPreopen0512") == 1
    assert text.count(mod.AUTO_START) == 1
    assert text.count(mod.AUTO_END) == 1


def test_build_next_stage2_checklist_excludes_codex_daily_workorder_snapshots(
    monkeypatch, tmp_path
):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    (docs / "code-improvement-workorders").mkdir(parents=True, exist_ok=True)
    (
        docs
        / "code-improvement-workorders"
        / "codex_daily_workorder_2026-05-11_PREOPEN.md"
    ).write_text(
        "FakeCodexOnlyFamily",
        encoding="utf-8",
    )
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-11.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-11.json",
        {"summary": {"selected_order_count": 0}},
    )

    mod.build_next_stage2_checklist("2026-05-11")

    text = (docs / "checklists" / "2026-05-12-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "FakeCodexOnlyFamily" not in text
    assert "RuntimeEnvIntradayObserve0512" not in text


def test_generated_checklist_is_parser_friendly(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    trigger_dir = mod.AUTOMATION_TRIGGER_DECISION_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-11.json",
        {"runtime_apply": {"runtime_change": True}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-11.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-11.json",
        {"summary": {"selected_order_count": 1}},
    )
    _write_json(
        trigger_dir / "automation_chain_trigger_decision_2026-05-11.json",
        {
            "summary": {"total_steps": 1, "run_count": 1, "skip_count": 0},
            "decisions": [],
        },
    )

    mod.build_next_stage2_checklist("2026-05-11")
    checklist = docs / "checklists" / "2026-05-12-stage2-todo-checklist.md"
    monkeypatch.setenv("DOC_BACKLOG_TODAY", "2026-05-11")
    monkeypatch.setenv("DOC_CHECKLIST_PATH", str(checklist))

    tasks = [task for task in parse_checklist_tasks() if task.source == str(checklist)]
    titles = [task.title for task in tasks]

    assert any("ThresholdEnvAutoApplyPreopen0512" in title for title in titles)
    assert any("RisingMissedScoutRuntimePreopen0512" in title for title in titles)
    assert any("RuntimeEnvIntradayObserve0512" in title for title in titles)
    assert any("AutomationTriggerDecisionSummary0512" in title for title in titles)
    assert all(task.due_date == "2026-05-12" for task in tasks)


def test_build_next_stage2_checklist_refuses_to_write_when_core_postclose_artifacts_are_missing(
    monkeypatch, tmp_path
):
    docs, _, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    trigger_dir = mod.AUTOMATION_TRIGGER_DECISION_REPORT_DIR
    _write_json(
        trigger_dir / "automation_chain_trigger_decision_2026-06-02.json",
        {"summary": {"total_steps": 1, "run_count": 1}, "decisions": []},
    )

    with pytest.raises(RuntimeError, match="required postclose artifacts are missing"):
        mod.build_next_stage2_checklist("2026-06-02")

    assert not (docs / "checklists" / "2026-06-04-stage2-todo-checklist.md").exists()


def test_build_next_stage2_checklist_skips_optional_tasks_when_optional_artifacts_are_missing(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )

    summary = mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert summary["tasks"] == [
        "ThresholdEnvAutoApplyPreopen0526",
        "RisingMissedScoutRuntimePreopen0526",
        "IntradaySourceQualityGateCheck0526",
        "ThresholdDailyEVReport0526",
        "HumanInterventionSummary0526",
        "MachineMicroPolicyApprovalSourceGap0526",
        "PostcloseSourceQualityGateReview0526",
    ]
    assert "report_missing_or_unreadable" in text
    assert "source_status=missing" in text
    assert "CodeImprovementWorkorderReview0526" not in text
    assert "AutomationTriggerDecisionSummary0526" not in text
    assert "tuning_performance_control_tower_2026-05-22.json" not in text


def test_automation_trigger_decision_summary_is_surfaced_as_postclose_task(
    monkeypatch, tmp_path
):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    trigger_dir = mod.AUTOMATION_TRIGGER_DECISION_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
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

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
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
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
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

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "runtime_apply_gap_audit_2026-05-22.json" in text
    assert "post_apply_attribution_pending" in text
    assert "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22" in text
    assert "runtime_gap_pending_not_consumed" in text


def test_machine_microstructure_policy_approval_is_surfaced_in_preopen_task(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json",
        {"approval_requests": []},
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report(
            "2026-05-22",
            actionable_candidates=[
                {
                    "candidate_id": "widget:005930:entry:micro_axis",
                    "candidate_sha256": "a" * 64,
                    "state": "REVIEW_READY",
                }
            ],
            objective_followups=[
                {
                    "followup_id": "machine_lifecycle_turnover_policy",
                    "state": "EVIDENCE_ACCUMULATING",
                    "followup_required": True,
                    "next_action": "continue_collection_and_recheck_floors",
                }
            ],
        ),
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineMicroPolicyApprovalPreopen0526]" in text
    assert "widget:005930:entry:micro_axis" in text
    assert "REVIEW_READY" in text
    assert "aaaaaaaaaaaaaaaa" in text
    assert "미등록 runtime family" in text
    objective_task = "[MachineLifecycleTurnoverObjectiveFollowup0526]"
    assert objective_task in text
    assert text.index("[MachineMicroPolicyApprovalPreopen0526]") < text.index(
        "## 장중 체크리스트"
    )
    assert text.index(objective_task) > text.index("## 장후 체크리스트")


def test_machine_microstructure_closed_candidate_removes_builder_owned_preopen_task(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    approval_path = (
        mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json"
    )
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_machine_micro_approval_report(
        approval_path,
        _machine_micro_approval_report(
            "2026-05-22",
            actionable_candidates=[
                {
                    "candidate_id": "widget:005930:entry:micro_axis",
                    "candidate_sha256": "a" * 64,
                    "state": "REVIEW_READY",
                }
            ],
        ),
    )

    mod.build_next_stage2_checklist("2026-05-22")
    target = docs / "checklists" / "2026-05-26-stage2-todo-checklist.md"
    assert "[MachineMicroPolicyApprovalPreopen0526]" in target.read_text(
        encoding="utf-8"
    )

    _write_machine_micro_approval_report(
        approval_path,
        _machine_micro_approval_report("2026-05-22"),
    )
    mod.build_next_stage2_checklist("2026-05-22")

    assert "[MachineMicroPolicyApprovalPreopen0526]" not in target.read_text(
        encoding="utf-8"
    )


def test_machine_microstructure_objective_followup_is_surfaced_without_candidate(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json",
        {"approval_requests": []},
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report(
            "2026-05-22",
            objective_followups=[
                {
                    "followup_id": "machine_lifecycle_turnover_policy_research_v1",
                    "state": "IMPLEMENTATION_REQUIRED",
                    "followup_required": True,
                    "next_action": "implement_source_only_rolling_paired_policy_research",
                }
            ],
        ),
    )

    mod.build_next_stage2_checklist("2026-05-22")

    checklist = docs / "checklists" / "2026-05-26-stage2-todo-checklist.md"
    text = checklist.read_text(encoding="utf-8")
    task = "[MachineLifecycleTurnoverObjectiveFollowup0526]"
    assert task in text
    assert "[MachineMicroPolicyApprovalPreopen0526]" not in text
    assert text.index(task) > text.index("## 장후 체크리스트")
    assert "`Slot: POSTCLOSE`" in text[text.index(task) :]
    assert "machine_lifecycle_turnover_policy_research_v1" in text
    assert "IMPLEMENTATION_REQUIRED" in text
    assert "implement_source_only_rolling_paired_policy_research" in text
    assert "runtime env, 실주문" in text
    monkeypatch.setenv("DOC_CHECKLIST_PATH", str(checklist))
    parsed = [row for row in parse_checklist_tasks() if task in row.title]
    assert len(parsed) == 1
    assert parsed[0].due_date == "2026-05-26"


def test_machine_microstructure_closed_objective_followup_is_removed_on_refresh(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json",
        {"approval_requests": []},
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report(
            "2026-05-22",
            objective_followups=[
                {
                    "followup_id": "machine_lifecycle_turnover_policy",
                    "state": "IMPLEMENTATION_REQUIRED",
                    "followup_required": True,
                    "next_action": "implement_source_only_rolling_paired_policy_research",
                }
            ],
        ),
    )

    mod.build_next_stage2_checklist("2026-05-22")
    target = docs / "checklists" / "2026-05-26-stage2-todo-checklist.md"
    text = target.read_text(encoding="utf-8")
    assert "[MachineLifecycleTurnoverObjectiveFollowup0526]" in text

    auto_end = text.index(mod.AUTO_END)
    target.write_text(
        text[:auto_end] + "- [ ] `[CustomPostclose0526] 수동 auto-block 보강` "
        "(`Due: 2026-05-26`, `Slot: POSTCLOSE`, "
        "`TimeWindow: 21:50~21:55`, `Track: RuntimeStability`)\n"
        "  - Source: [manual.md](/home/ubuntu/KORStockScan/docs/manual.md)\n"
        "  - 판정 기준: builder가 보존해야 한다.\n\n" + text[auto_end:],
        encoding="utf-8",
    )
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report("2026-05-22"),
    )
    mod.build_next_stage2_checklist("2026-05-22")

    text = target.read_text(encoding="utf-8")
    assert "[MachineLifecycleTurnoverObjectiveFollowup0526]" not in text
    assert "[CustomPostclose0526]" in text


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    [
        ({"schema": "wrong"}, "contract_invalid:schema"),
        ({"phase": "preopen"}, "contract_invalid:phase"),
        ({"target_date": "2026-05-21"}, "contract_invalid:target_date"),
        (
            {"generated_at_kst": "not-an-aware-timestamp"},
            "predecessor_invalid:generated_at_kst",
        ),
        (
            {"objective_followup_source_status": "unknown"},
            "contract_invalid:objective_followup_source_status",
        ),
        (
            {
                "summary": {
                    "actionable_objective_followup_count": "0",
                    "objective_followup_rejection_count": 0,
                }
            },
            "contract_invalid:objective_followup_count",
        ),
        (
            {
                "summary": {
                    "actionable_objective_followup_count": 0,
                    "objective_followup_rejection_count": "0",
                }
            },
            "contract_invalid:objective_followup_rejection_count",
        ),
        (
            {
                "authority": {
                    "runtime_effect": True,
                    "runtime_apply_performed": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                }
            },
            "contract_invalid:authority",
        ),
    ],
)
def test_machine_microstructure_approval_contract_gap_is_explicit(
    monkeypatch, tmp_path, mutation, expected_status
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    payload = _machine_micro_approval_report("2026-05-22")
    payload.update(mutation)
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        payload,
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in text
    assert f"source_status={expected_status}" in text
    assert "[MachineLifecycleTurnoverObjectiveFollowup0526]" not in text


def test_stale_same_date_approval_is_not_loaded_after_attribution_refresh(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    approval_path = (
        mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json"
    )
    _write_machine_micro_approval_report(
        approval_path,
        _machine_micro_approval_report(
            "2026-05-22",
            objective_followups=[
                {
                    "followup_id": "machine_lifecycle_turnover_policy_research_v1",
                    "state": "IMPLEMENTATION_REQUIRED",
                    "followup_required": True,
                    "next_action": (
                        "implement_source_only_rolling_paired_policy_research"
                    ),
                }
            ],
        ),
    )
    attribution_path = (
        mod.MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_DIR
        / "machine_microstructure_attribution_2026-05-22.json"
    )
    refreshed = json.loads(attribution_path.read_text(encoding="utf-8"))
    refreshed["generation_id"] = "later_same_date_final_refresh"
    _write_json(attribution_path, refreshed)

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in text
    assert "source_status=predecessor_invalid:source_artifact_sha256" in text
    assert "[MachineLifecycleTurnoverObjectiveFollowup0526]" not in text


def test_completed_refresh_rejects_old_but_mutually_matching_same_date_artifacts(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    approval_path = (
        mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json"
    )
    _write_machine_micro_approval_report(
        approval_path,
        _machine_micro_approval_report("2026-05-22"),
    )

    mod.build_next_stage2_checklist(
        "2026-05-22",
        machine_micro_approval_not_before=(
            datetime.now().astimezone() + timedelta(minutes=1)
        ),
    )

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in text
    assert (
        "source_status=predecessor_invalid:"
        "approval_generated_before_completed_refresh_window"
    ) in text


def test_completed_refresh_rejects_fresh_approval_over_stale_loaded_source(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    approval_path = (
        mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json"
    )
    _write_machine_micro_approval_report(
        approval_path,
        _machine_micro_approval_report("2026-05-22"),
    )
    attribution_path = (
        mod.MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_DIR
        / "machine_microstructure_attribution_2026-05-22.json"
    )
    now = datetime.now().astimezone()
    stale_at = now - timedelta(minutes=65)
    source_payload = json.loads(attribution_path.read_text(encoding="utf-8"))
    source_payload["generated_at_kst"] = stale_at.isoformat()
    _write_json(attribution_path, source_payload)
    os.utime(attribution_path, (stale_at.timestamp(), stale_at.timestamp()))
    source_bytes = attribution_path.read_bytes()
    source_stat = attribution_path.stat()
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload["generated_at_kst"] = now.isoformat(timespec="seconds")
    approval_payload["source_artifact"].update(
        {
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "mtime_ns": source_stat.st_mtime_ns,
            "size_bytes": source_stat.st_size,
        }
    )
    _write_json(approval_path, approval_payload)

    mod.build_next_stage2_checklist(
        "2026-05-22",
        machine_micro_approval_not_before=now - timedelta(minutes=30),
    )

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in text
    assert "source_payload_generated_before_completed_refresh_window" in text
    assert "source_artifact_mtime_before_completed_refresh_window" in text


def test_fresh_explicit_objective_source_gap_preserves_prior_open_objective(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    approval_path = (
        mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json"
    )
    attribution_path = (
        mod.MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_DIR
        / "machine_microstructure_attribution_2026-05-22.json"
    )
    now = datetime.now().astimezone()
    payload = _machine_micro_approval_report(
        "2026-05-22",
        objective_followup_source_status="missing_or_unreadable",
        objective_followups=[
            {
                "followup_id": "machine_lifecycle_turnover_policy_research_v1",
                "source_date": "2026-05-21",
                "state": "EVIDENCE_ACCUMULATING",
                "followup_required": True,
                "next_action": "continue_exact_date_collection",
            }
        ],
    )
    payload.update(
        {
            "generated_at_kst": now.isoformat(timespec="seconds"),
            "source_status": "missing_or_unreadable",
            "source_path": str(attribution_path),
            "source_artifact": {
                "schema": mod.MACHINE_MICROSTRUCTURE_SOURCE_ARTIFACT_SCHEMA,
                "path": str(attribution_path),
                "sha256": None,
                "mtime_ns": None,
                "size_bytes": None,
            },
        }
    )
    _write_json(approval_path, payload)

    summary = mod.build_next_stage2_checklist(
        "2026-05-22",
        machine_micro_approval_not_before=now - timedelta(minutes=1),
    )

    assert "MachineLifecycleTurnoverObjectiveFollowup0526" in summary["tasks"]
    assert "MachineMicroPolicyApprovalSourceGap0526" in summary["tasks"]
    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "source_status=objective_source_gap:missing_or_unreadable" in text
    assert "machine_lifecycle_turnover_policy_research_v1" in text


@pytest.mark.parametrize(
    ("source_mutation", "expected_error"),
    [
        ({"schema": "wrong"}, "source_payload_schema"),
        ({"target_date": "2026-05-21"}, "source_payload_target_date"),
        (
            {
                "authority": {
                    "runtime_effect": True,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                }
            },
            "source_payload_authority",
        ),
    ],
)
def test_approval_predecessor_semantics_are_validated_after_matching_rehash(
    monkeypatch, tmp_path, source_mutation, expected_error
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    approval_path = (
        mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json"
    )
    _write_machine_micro_approval_report(
        approval_path,
        _machine_micro_approval_report("2026-05-22"),
    )
    attribution_path = (
        mod.MACHINE_MICROSTRUCTURE_ATTRIBUTION_REPORT_DIR
        / "machine_microstructure_attribution_2026-05-22.json"
    )
    source_payload = json.loads(attribution_path.read_text(encoding="utf-8"))
    source_payload.update(source_mutation)
    _write_json(attribution_path, source_payload)
    source_bytes = attribution_path.read_bytes()
    source_stat = attribution_path.stat()
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload["generated_at_kst"] = (
        datetime.fromtimestamp(source_stat.st_mtime)
        .astimezone()
        .isoformat(timespec="seconds")
    )
    approval_payload["source_artifact"].update(
        {
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "mtime_ns": source_stat.st_mtime_ns,
            "size_bytes": source_stat.st_size,
        }
    )
    _write_json(approval_path, approval_payload)

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in text
    assert f"source_status=predecessor_invalid:{expected_error}" in text


def test_machine_microstructure_unreadable_approval_gap_is_explicit(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    approval_path = (
        mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json"
    )
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    approval_path.write_text("{not-json", encoding="utf-8")

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in text
    assert "source_status=unreadable" in text


def test_machine_microstructure_source_gap_task_is_removed_after_valid_refresh(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )

    mod.build_next_stage2_checklist("2026-05-22")
    target = docs / "checklists" / "2026-05-26-stage2-todo-checklist.md"
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in target.read_text(
        encoding="utf-8"
    )

    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report("2026-05-22"),
    )
    mod.build_next_stage2_checklist("2026-05-22")

    assert "[MachineMicroPolicyApprovalSourceGap0526]" not in target.read_text(
        encoding="utf-8"
    )


def test_machine_microstructure_prior_open_objective_is_preserved_with_source_gap(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report(
            "2026-05-22",
            source_status="missing_or_unreadable",
            objective_followup_source_status="missing_or_unreadable",
            objective_followups=[
                {
                    "followup_id": "machine_lifecycle_turnover_policy_research_v1",
                    "source_date": "2026-05-21",
                    "state": "EVIDENCE_ACCUMULATING",
                    "followup_required": True,
                    "next_action": "continue_exact_date_collection",
                }
            ],
        ),
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineLifecycleTurnoverObjectiveFollowup0526]" in text
    assert "machine_lifecycle_turnover_policy_research_v1" in text
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in text
    assert "source_status=objective_source_gap:missing_or_unreadable" in text


def test_machine_microstructure_rejected_new_row_preserves_prior_open_objective(
    monkeypatch, tmp_path
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report(
            "2026-05-22",
            objective_followup_source_status="loaded",
            objective_followups=[
                {
                    "followup_id": "machine_lifecycle_turnover_policy_research_v1",
                    "source_date": "2026-05-21",
                    "state": "EVIDENCE_ACCUMULATING",
                    "followup_required": True,
                    "next_action": "continue_exact_date_collection",
                }
            ],
            objective_followup_rejections=[
                {
                    "followup_id": "machine_lifecycle_turnover_policy_research_v1",
                    "errors": ["objective_followup_state_invalid"],
                }
            ],
        ),
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[MachineLifecycleTurnoverObjectiveFollowup0526]" in text
    assert "machine_lifecycle_turnover_policy_research_v1" in text
    assert "[MachineMicroPolicyApprovalSourceGap0526]" in text
    assert "source_status=objective_source_gap:rejected_rows:1" in text


@pytest.mark.parametrize("row_source_date", ["2026-05-17", "2026-05-23"])
def test_machine_microstructure_source_gap_rejects_nontrading_or_future_objective(
    monkeypatch, tmp_path, row_source_date
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report(
            "2026-05-22",
            source_status="contract_invalid",
            objective_followup_source_status="contract_invalid",
            objective_followups=[
                {
                    "followup_id": "machine_lifecycle_turnover_policy_research_v1",
                    "source_date": row_source_date,
                    "state": "EVIDENCE_ACCUMULATING",
                    "followup_required": True,
                    "next_action": "continue_exact_date_collection",
                }
            ],
        ),
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "source_status=contract_invalid:objective_followup_rows" in text
    assert "[MachineLifecycleTurnoverObjectiveFollowup0526]" not in text


@pytest.mark.parametrize(
    "row_mutation",
    [
        {"source_date": "2026-05-21"},
        {"state": "COMPLETE", "followup_required": False},
        {"operator_decision_required": True},
        {"metric_contract": {"decision_authority": "runtime_apply"}},
        {
            "authority": {
                "runtime_effect": True,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        },
    ],
)
def test_machine_microstructure_objective_row_contract_gap_is_explicit(
    monkeypatch, tmp_path, row_mutation
):
    docs, ev_dir, _, _, _ = _patch_dirs(monkeypatch, tmp_path)
    approval_dir = mod.MACHINE_MICROSTRUCTURE_POLICY_APPROVAL_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    row = {
        "followup_id": "machine_lifecycle_turnover_policy_research_v1",
        "state": "IMPLEMENTATION_REQUIRED",
        "followup_required": True,
        "next_action": "implement_source_only_rolling_paired_policy_research",
        **row_mutation,
    }
    _write_machine_micro_approval_report(
        approval_dir
        / "machine_microstructure_policy_approval_postclose_2026-05-22.json",
        _machine_micro_approval_report(
            "2026-05-22",
            objective_followups=[row],
        ),
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "source_status=contract_invalid:objective_followup_rows" in text
    assert "[MachineLifecycleTurnoverObjectiveFollowup0526]" not in text


def test_completed_machine_source_date_mode_is_safe_for_persistent_holiday_catchup(
    monkeypatch, capsys
):
    kst = ZoneInfo("Asia/Seoul")
    resolver = mod.resolve_completed_machine_target_date
    captured: list[tuple[str, datetime | None]] = []
    monkeypatch.setattr(
        mod,
        "resolve_completed_machine_target_date",
        lambda: resolver(now=datetime(2026, 8, 17, 21, 15, tzinfo=kst)),
    )
    monkeypatch.setattr(
        mod,
        "build_next_stage2_checklist",
        lambda source_date, machine_micro_approval_not_before=None: (
            captured.append((source_date, machine_micro_approval_not_before))
            or {"source_date": source_date}
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_next_stage2_checklist", "--completed-machine-source-date"],
    )

    assert mod.main() == 0
    assert captured[0][0] == "2026-08-14"
    assert captured[0][1] is not None
    assert captured[0][1].tzinfo is not None
    assert '"source_date": "2026-08-14"' in capsys.readouterr().out


def test_completed_machine_source_date_mode_accepts_wrapper_pinned_exact_date(
    monkeypatch, capsys
):
    captured: list[tuple[str, datetime | None]] = []
    monkeypatch.setattr(
        mod,
        "build_next_stage2_checklist",
        lambda source_date, machine_micro_approval_not_before=None: (
            captured.append((source_date, machine_micro_approval_not_before))
            or {"source_date": source_date}
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_next_stage2_checklist",
            "--completed-machine-source-date",
            "2026-08-14",
        ],
    )

    assert mod.main() == 0
    assert captured[0][0] == "2026-08-14"
    assert captured[0][1] is not None
    assert '"source_date": "2026-08-14"' in capsys.readouterr().out


def test_checklist_builders_serialize_the_full_read_merge_write_cycle(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "CHECKLIST_LOCK_DIR", tmp_path / "locks")
    monkeypatch.setattr(mod, "CHECKLIST_DIR", tmp_path / "checklists")
    monkeypatch.setattr(mod, "_next_krx_trading_day", lambda _: "2026-05-26")
    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()
    call_order: list[str] = []

    def fake_locked_build(**kwargs):
        call_order.append(threading.current_thread().name)
        if len(call_order) == 1:
            first_entered.set()
            assert release_first.wait(timeout=2)
        else:
            second_entered.set()
        return {"source_date": kwargs["source_date"]}

    monkeypatch.setattr(mod, "_build_next_stage2_checklist_locked", fake_locked_build)
    first = threading.Thread(
        target=mod.build_next_stage2_checklist,
        args=("2026-05-22",),
        name="first",
    )
    second = threading.Thread(
        target=mod.build_next_stage2_checklist,
        args=("2026-05-22",),
        name="second",
    )
    first.start()
    assert first_entered.wait(timeout=2)
    second.start()
    assert not second_entered.wait(timeout=0.1)
    release_first.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert call_order == ["first", "second"]


def test_runtime_apply_gap_codex_directives_are_surfaced_as_postclose_task(
    monkeypatch, tmp_path
):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    runtime_gap_dir = mod.RUNTIME_APPLY_GAP_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
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

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[RuntimeApplyGapDirectiveReview0526]" in text
    assert "runtime apply gap Codex 작업지시" in text
    assert "IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET" in text
    assert "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22" in text
    assert "approval artifact나 즉시 runtime env 수정" in text


def test_source_dimension_gap_summary_is_surfaced_even_without_directives(
    monkeypatch, tmp_path
):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    runtime_gap_dir = mod.RUNTIME_APPLY_GAP_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
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
                "recommended_resolution_counts": {
                    "resolve_unknown_source_dimensions": 2
                },
                "missing_dimension_key_counts": {"liquidity_bucket": 2},
            },
        },
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[LifecycleSourceDimensionGapReview0526]" in text
    assert "lifecycle source dimension gap 자동 표면화" in text
    assert "actionable_unknown_gap_count=`2`" in text
    assert "`already_covered_by_fallback`" in text


def test_quiet_gap_summary_is_surfaced_even_without_directives(monkeypatch, tmp_path):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    runtime_gap_dir = mod.RUNTIME_APPLY_GAP_REPORT_DIR
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
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
                "quiet_gap_type_counts": {
                    "parent_conflict_child": 1,
                    "positive_source_only_keep_collecting": 1,
                },
            },
        },
    )

    mod.build_next_stage2_checklist("2026-05-22")

    text = (docs / "checklists" / "2026-05-26-stage2-todo-checklist.md").read_text(
        encoding="utf-8"
    )
    assert "[LifecycleQuietGapReview0526]" in text
    assert "lifecycle quiet gap rollup 자동 표면화" in text
    assert "quiet_gap_count=`2`" in text
    assert "`already_covered_by_parent_policy`" in text


def test_build_next_stage2_checklist_preserves_unknown_tasks_inside_auto_block(
    monkeypatch, tmp_path
):
    docs, ev_dir, openai_dir, swing_dir, code_dir = _patch_dirs(monkeypatch, tmp_path)
    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-22.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-22.json", {"approval_requests": []}
    )
    _write_json(
        code_dir / "code_improvement_workorder_2026-05-22.json",
        {"summary": {"selected_order_count": 0}},
    )
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
                "## 장후 체크리스트 (20:05~21:55)",
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


def test_build_next_stage2_checklist_hands_off_main_ai_source_gap_workorders(
    monkeypatch, tmp_path
) -> None:
    _docs, ev_dir, _openai_dir, _swing_dir, _code_dir = _patch_dirs(
        monkeypatch, tmp_path
    )
    source_date = "2026-08-21"
    _write_json(
        ev_dir / f"threshold_cycle_ev_{source_date}.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    report_path = (
        mod.MAIN_AI_QUALITY_REPORT_DIR
        / f"main_ai_quality_r0_r3_cycle_{source_date}.json"
    )
    _write_json(
        report_path,
        _main_ai_quality_report(
            source_date,
            [
                "MicroReversionForwardCollectorContinuity",
                "RuntimeExecutionReceiptCustodyRepair",
                "MainAIQualityMaterializedCompanionBindingRepair",
            ],
        ),
    )

    summary = mod.build_next_stage2_checklist(source_date)

    text = Path(summary["path"]).read_text(encoding="utf-8")
    assert (
        "[MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0824]" in text
    )
    assert "[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0824]" in text
    assert (
        "[MainAIQualitySourceGapMainAIQualityMaterializedCompanionBindingRepair0824]"
        in text
    )
    assert "closed-date verified compression" in text
    assert "공식 raw execution envelope" in text
    assert "materialized request/response companion의 exact hash" in text
    assert "runtime env, 실주문·취소" in text
    monkeypatch.setenv("DOC_CHECKLIST_PATH", summary["path"])
    parsed = parse_checklist_tasks()
    parsed_titles = {task.title for task in parsed}
    assert any(
        "MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0824" in title
        for title in parsed_titles
    )
    assert any(
        "MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0824" in title
        for title in parsed_titles
    )
    assert any(
        "MainAIQualitySourceGapMainAIQualityMaterializedCompanionBindingRepair0824"
        in title
        for title in parsed_titles
    )


def test_build_next_stage2_checklist_preserves_full_main_ai_acceptance_contract(
    monkeypatch, tmp_path
) -> None:
    _docs, ev_dir, _openai_dir, _swing_dir, _code_dir = _patch_dirs(
        monkeypatch, tmp_path
    )
    source_date = "2026-08-21"
    _write_json(
        ev_dir / f"threshold_cycle_ev_{source_date}.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    report = _main_ai_quality_report(
        source_date, ["RuntimeExecutionReceiptCustodyRepair"]
    )
    acceptance = (
        "official raw execution envelope/order/execution identity is complete for "
        "at least one reconciled lifecycle; materialized execution companions bind "
        "to their exact request census; custody and order authority remain unchanged"
    )
    workorder = dict(report["source_only_gap_workorders"][0])
    workorder["acceptance_test"] = acceptance
    workorder_content = {
        key: value
        for key, value in workorder.items()
        if key not in {"schema", "workorder_id", "status"}
    }
    workorder["workorder_id"] = (
        f"main-ai-gap-{mod._canonical_sha256(workorder_content)[:24]}"
    )
    report["source_only_gap_workorders"] = [workorder]
    report["source_gap_diagnostics"]["workorders"] = [workorder]
    report["artifact_content_sha256"] = mod._canonical_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "artifact_content_sha256"
        }
    )
    _write_json(
        mod.MAIN_AI_QUALITY_REPORT_DIR
        / f"main_ai_quality_r0_r3_cycle_{source_date}.json",
        report,
    )

    summary = mod.build_next_stage2_checklist(source_date)

    text = Path(summary["path"]).read_text(encoding="utf-8")
    assert f"완료 조건: {acceptance}" in text


def test_build_next_stage2_checklist_rejects_tampered_main_ai_workorder_report(
    monkeypatch, tmp_path
) -> None:
    _docs, ev_dir, _openai_dir, _swing_dir, _code_dir = _patch_dirs(
        monkeypatch, tmp_path
    )
    source_date = "2026-08-21"
    _write_json(
        ev_dir / f"threshold_cycle_ev_{source_date}.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    report = _main_ai_quality_report(
        source_date, ["RuntimeExecutionReceiptCustodyRepair"]
    )
    report["source_only_gap_workorders"][0]["runtime_effect"] = True
    report["artifact_content_sha256"] = mod._canonical_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "artifact_content_sha256"
        }
    )
    _write_json(
        mod.MAIN_AI_QUALITY_REPORT_DIR
        / f"main_ai_quality_r0_r3_cycle_{source_date}.json",
        report,
    )

    summary = mod.build_next_stage2_checklist(source_date)

    text = Path(summary["path"]).read_text(encoding="utf-8")
    assert "[MainAIQualitySourceGapArtifactContract0824]" in text
    assert (
        "[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0824]" not in text
    )
    assert "source_status=`invalid_workorder_authority`" in text


@pytest.mark.parametrize(
    ("target", "field", "expected_status"),
    [
        ("report", "provider_authority", "invalid_authority"),
        ("diagnostics", "runtime_authority", "invalid_workorder_authority"),
        ("workorder", "order_authority", "invalid_workorder_authority"),
    ],
)
def test_build_next_stage2_checklist_rejects_main_ai_optional_authority_tamper(
    monkeypatch,
    tmp_path,
    target: str,
    field: str,
    expected_status: str,
) -> None:
    _docs, ev_dir, _openai_dir, _swing_dir, _code_dir = _patch_dirs(
        monkeypatch, tmp_path
    )
    source_date = "2026-08-21"
    _write_json(
        ev_dir / f"threshold_cycle_ev_{source_date}.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    report = _main_ai_quality_report(
        source_date, ["RuntimeExecutionReceiptCustodyRepair"]
    )
    if target == "report":
        report[field] = True
    elif target == "diagnostics":
        report["source_gap_diagnostics"][field] = True
    else:
        report["source_only_gap_workorders"][0][field] = True
        report["source_gap_diagnostics"]["workorders"] = report[
            "source_only_gap_workorders"
        ]
    report["artifact_content_sha256"] = mod._canonical_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "artifact_content_sha256"
        }
    )
    _write_json(
        mod.MAIN_AI_QUALITY_REPORT_DIR
        / f"main_ai_quality_r0_r3_cycle_{source_date}.json",
        report,
    )

    summary = mod.build_next_stage2_checklist(source_date)

    text = Path(summary["path"]).read_text(encoding="utf-8")
    assert "[MainAIQualitySourceGapArtifactContract0824]" in text
    assert f"source_status=`{expected_status}`" in text
    assert (
        "[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0824]" not in text
    )


def test_build_next_stage2_checklist_rejects_main_ai_diagnostic_contract_findings(
    monkeypatch, tmp_path
) -> None:
    _docs, ev_dir, _openai_dir, _swing_dir, _code_dir = _patch_dirs(
        monkeypatch, tmp_path
    )
    source_date = "2026-08-21"
    _write_json(
        ev_dir / f"threshold_cycle_ev_{source_date}.json",
        {"runtime_apply": {"runtime_change": False}},
    )
    report = _main_ai_quality_report(
        source_date, ["RuntimeExecutionReceiptCustodyRepair"]
    )
    report["source_gap_diagnostics"]["contract_findings"] = [
        "lifecycle_content_hash_invalid"
    ]
    report["artifact_content_sha256"] = mod._canonical_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "artifact_content_sha256"
        }
    )
    _write_json(
        mod.MAIN_AI_QUALITY_REPORT_DIR
        / f"main_ai_quality_r0_r3_cycle_{source_date}.json",
        report,
    )

    summary = mod.build_next_stage2_checklist(source_date)

    text = Path(summary["path"]).read_text(encoding="utf-8")
    assert "[MainAIQualitySourceGapArtifactContract0824]" in text
    assert "source_status=`invalid_workorders`" in text
    assert (
        "[MainAIQualitySourceGapRuntimeExecutionReceiptCustodyRepair0824]" not in text
    )


def test_build_next_stage2_checklist_surfaces_missing_main_ai_report_after_contract_start(
    monkeypatch, tmp_path
) -> None:
    _docs, ev_dir, _openai_dir, _swing_dir, _code_dir = _patch_dirs(
        monkeypatch, tmp_path
    )
    source_date = "2026-08-21"
    _write_json(
        ev_dir / f"threshold_cycle_ev_{source_date}.json",
        {"runtime_apply": {"runtime_change": False}},
    )

    summary = mod.build_next_stage2_checklist(source_date)

    text = Path(summary["path"]).read_text(encoding="utf-8")
    assert "[MainAIQualitySourceGapArtifactContract0824]" in text
    assert "source_status=`missing_artifact`" in text
