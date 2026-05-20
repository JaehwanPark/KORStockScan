import json

from src.engine import plan_rebase_daily_renewal as mod


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_plan_rebase_daily_renewal_builds_bounded_document_mutation_queue(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    runtime_dir = tmp_path / "runtime_approval_summary"
    openai_dir = tmp_path / "openai_ws"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "plan_rebase_daily_renewal"
    root_readme = tmp_path / "README.md"
    docs_readme = tmp_path / "docs" / "README.md"
    threshold_readme = tmp_path / "data" / "threshold_cycle" / "README.md"
    report_readme = tmp_path / "data" / "report" / "README.md"
    runbook = tmp_path / "docs" / "runbook.md"
    plan = tmp_path / "docs" / "plan.md"
    prompt = tmp_path / "docs" / "prompt.md"
    agents = tmp_path / "AGENTS.md"
    document_paths = (
        root_readme,
        docs_readme,
        threshold_readme,
        report_readme,
        runbook,
        plan,
        prompt,
        agents,
    )
    for path in document_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("existing", encoding="utf-8")

    monkeypatch.setattr(mod, "EV_REPORT_DIR", ev_dir)
    monkeypatch.setattr(mod, "RUNTIME_APPROVAL_SUMMARY_DIR", runtime_dir)
    monkeypatch.setattr(mod, "OPENAI_WS_REPORT_DIR", openai_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "PLAN_REBASE_RENEWAL_DIR", out_dir)
    monkeypatch.setattr(mod, "ROOT_README_PATH", root_readme)
    monkeypatch.setattr(mod, "DOCS_README_PATH", docs_readme)
    monkeypatch.setattr(mod, "THRESHOLD_README_PATH", threshold_readme)
    monkeypatch.setattr(mod, "REPORT_README_PATH", report_readme)
    monkeypatch.setattr(mod, "RUNBOOK_PATH", runbook)
    monkeypatch.setattr(
        mod,
        "DOCUMENT_UPDATE_QUEUE",
        [
            {
                "document": "README family",
                "paths": [str(root_readme)],
                "scope": "project_overview",
            },
            {"document": "runbook", "paths": [str(runbook)], "scope": "operations"},
            {
                "document": "Plan Rebase",
                "paths": [str(plan)],
                "scope": "current_snapshot",
            },
            {"document": "prompt", "paths": [str(prompt)], "scope": "source_map"},
            {"document": "AGENTS", "paths": [str(agents)], "scope": "working_snapshot"},
        ],
    )
    monkeypatch.setattr(mod, "PLAN_REBASE_PATH", plan)
    monkeypatch.setattr(mod, "PROMPT_PATH", prompt)
    monkeypatch.setattr(mod, "AGENTS_PATH", agents)

    _write_json(
        ev_dir / "threshold_cycle_ev_2026-05-13.json",
        {
            "runtime_apply": {
                "runtime_change": True,
                "selected_families": [
                    "soft_stop_whipsaw_confirmation",
                    "score65_74_recovery_probe",
                ],
                "runtime_env_file": "data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-13.env",
            }
        },
    )
    _write_json(
        runtime_dir / "runtime_approval_summary_2026-05-13.json",
        {
            "summary": {
                "swing_requested": 2,
                "swing_approved": 0,
                "panic_approval_requested": 1,
            },
            "scalping": [
                {
                    "family": "soft_stop_whipsaw_confirmation",
                    "selected_auto_bounded_live": True,
                },
                {
                    "family": "position_sizing_cap_release",
                    "selected_auto_bounded_live": False,
                    "state": "hold_sample",
                },
            ],
            "panic": [{"family": "panic_entry_freeze_guard", "state": "approval_required"}],
            "warnings": [],
        },
    )
    _write_json(
        openai_dir / "openai_ws_stability_2026-05-13.json",
        {
            "decision": "keep_ws",
            "entry_price_canary_summary": {
                "canary_event_count": 3,
                "transport_observable_count": 3,
                "instrumentation_gap": False,
            },
        },
    )
    _write_json(
        swing_dir / "swing_runtime_approval_2026-05-13.json",
        {"summary": {"requested": 2, "approved": 0}},
    )

    report = mod.build_plan_rebase_daily_renewal("2026-05-13")

    assert report["mode"] == "bounded_document_mutation_queue"
    assert report["runtime_mutation_allowed"] is False
    assert report["document_mutation_allowed"] is True
    assert report["document_mutation_execution_allowed"] is True
    assert report["document_mutation_authority"] == "bounded_downstream_document_worker"
    assert report["document_mutation_self_apply"] is False
    assert report["renewal_state"] == "proposal_ready"
    assert report["document_mutation_order"] == [
        "README",
        "runbook",
        "Plan Rebase",
        "prompt",
        "AGENTS",
    ]
    assert report["document_mutation_passes"] == [
        "pass1_bounded_update",
        "pass2_audit_review",
        "finalize_after_pass2",
    ]
    assert [item["label"] for item in report["document_mutation_pass_contract"]] == [
        "1차 수정(first-pass bounded update)",
        "2차 감리(second-pass audit review)",
        "최종 수정(finalize after second-pass review)",
    ]
    assert report["proposal"]["plan_rebase"]["current_runtime_apply"]["selected_families"] == [
        "soft_stop_whipsaw_confirmation",
        "score65_74_recovery_probe",
    ]
    assert (
        report["proposal"]["plan_rebase"]["open_state_summary"]["swing"][
            "approval_artifact_required"
        ]
        is True
    )
    assert "metric_decision_contract" in report["guardrails"]["forbidden_update_scope"]
    assert report["guardrails"]["archive_history_before_mutation"] is True
    assert (
        report["guardrails"]["abbreviation_policy"]
        == "first_use_korean_english_parallel_notation"
    )
    markdown = (out_dir / "plan_rebase_daily_renewal_2026-05-13.md").read_text(
        encoding="utf-8"
    )
    assert "bounded_document_mutation_queue" in markdown
    assert "document_mutation_allowed: `True`" in markdown
    assert "pass2_audit_review" in markdown
    assert "2차 감리(second-pass audit review)" in markdown
    assert "soft_stop_whipsaw_confirmation" in markdown
    assert root_readme.read_text(encoding="utf-8") == "existing"
    assert docs_readme.read_text(encoding="utf-8") == "existing"
    assert threshold_readme.read_text(encoding="utf-8") == "existing"
    assert report_readme.read_text(encoding="utf-8") == "existing"
    assert runbook.read_text(encoding="utf-8") == "existing"
    assert plan.read_text(encoding="utf-8") == "existing"
    assert prompt.read_text(encoding="utf-8") == "existing"
    assert agents.read_text(encoding="utf-8") == "existing"


def test_plan_rebase_daily_renewal_blocks_when_required_sources_missing(tmp_path, monkeypatch):
    out_dir = tmp_path / "plan_rebase_daily_renewal"
    monkeypatch.setattr(mod, "EV_REPORT_DIR", tmp_path / "missing_ev")
    monkeypatch.setattr(mod, "RUNTIME_APPROVAL_SUMMARY_DIR", tmp_path / "missing_runtime")
    monkeypatch.setattr(mod, "OPENAI_WS_REPORT_DIR", tmp_path / "missing_openai")
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", tmp_path / "missing_swing")
    monkeypatch.setattr(mod, "PLAN_REBASE_RENEWAL_DIR", out_dir)
    monkeypatch.setattr(mod, "ROOT_README_PATH", tmp_path / "missing_root_readme.md")
    monkeypatch.setattr(mod, "DOCS_README_PATH", tmp_path / "missing_docs_readme.md")
    monkeypatch.setattr(mod, "THRESHOLD_README_PATH", tmp_path / "missing_threshold_readme.md")
    monkeypatch.setattr(mod, "REPORT_README_PATH", tmp_path / "missing_report_readme.md")
    monkeypatch.setattr(mod, "RUNBOOK_PATH", tmp_path / "missing_runbook.md")
    monkeypatch.setattr(mod, "PLAN_REBASE_PATH", tmp_path / "missing_plan.md")
    monkeypatch.setattr(mod, "PROMPT_PATH", tmp_path / "missing_prompt.md")
    monkeypatch.setattr(mod, "AGENTS_PATH", tmp_path / "missing_agents.md")

    report = mod.build_plan_rebase_daily_renewal("2026-05-13")

    assert report["renewal_state"] == "blocked_missing_or_warning_sources"
    assert "threshold_cycle_ev_missing" in report["warnings"]
    assert "runtime_approval_summary_missing" in report["warnings"]
    assert report["document_mutation_allowed"] is True
    assert report["document_mutation_execution_allowed"] is False
