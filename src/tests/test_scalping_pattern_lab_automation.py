import json

from src.engine import scalping_pattern_lab_automation as mod


def _write_lab_outputs(root, lab, *, fresh=True, backlog=None, opportunities=None, priority=None):
    lab_dir = root / f"{lab}_lab"
    out = lab_dir / "outputs"
    out.mkdir(parents=True)
    run_date = "2026-05-08" if fresh else "2026-05-07"
    coverage_end = "2026-05-08" if fresh else "2026-05-07"
    (out / "run_manifest.json").write_text(
        json.dumps({"run_at": f"{run_date}T18:00:00", "history_coverage_end": coverage_end}),
        encoding="utf-8",
    )
    (out / "ev_analysis_result.json").write_text(
        json.dumps(
            {
                "ev_backlog": backlog or [],
                "opportunity_cost": opportunities or [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (out / "tuning_observability_summary.json").write_text(
        json.dumps({"priority_findings": priority or []}, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "final_review_report_for_lead_ai.md").write_text("# final\n", encoding="utf-8")
    return lab_dir


def test_pattern_lab_automation_builds_consensus_orders_and_family_candidates(tmp_path, monkeypatch):
    gemini_dir = _write_lab_outputs(
        tmp_path,
        "gemini",
        backlog=[
            {"title": "AI threshold miss EV 회수 조건 점검", "기대효과": "missed EV 회수", "검증지표": "blocked"},
            {"title": "overbought gate miss EV 회수 조건 점검", "기대효과": "missed EV 회수"},
        ],
        priority=[{"label": "Gatekeeper latency high", "judgment": "경고", "why": "p95 high"}],
    )
    claude_dir = _write_lab_outputs(
        tmp_path,
        "claude",
        backlog=[
            {"title": "AI threshold miss EV 회수 조건 점검", "기대효과": "missed EV 회수"},
            {"title": "overbought gate miss EV 회수 조건 점검", "기대효과": "missed EV 회수"},
        ],
        priority=[{"label": "Gatekeeper latency high", "judgment": "경고", "why": "p95 high"}],
    )
    monkeypatch.setattr(mod, "GEMINI_LAB_DIR", gemini_dir)
    monkeypatch.setattr(mod, "CLAUDE_LAB_DIR", claude_dir)
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "report")

    report = mod.build_scalping_pattern_lab_automation_report("2026-05-08")

    assert report["runtime_effect"] is False
    assert report["runtime_mutation_allowed"] is False
    assert report["decision_authority"] == "pattern_lab_analysis_workorder_source_only"
    assert report["lab_freshness"]["gemini"]["fresh"] is True
    assert report["lab_freshness"]["claude"]["fresh"] is True
    assert any(item["mapped_family"] == "score65_74_recovery_probe" for item in report["consensus_findings"])
    assert any(item["target_subsystem"] == "runtime_instrumentation" for item in report["code_improvement_orders"])
    orders_by_id = {item["order_id"]: item for item in report["code_improvement_orders"]}
    threshold_order = orders_by_id["order_ai_threshold_miss_ev_회수_조건_점검"]
    assert threshold_order["route"] == "existing_family"
    assert threshold_order["mapped_family"] == "score65_74_recovery_probe"
    assert threshold_order["improvement_type"] == "threshold_family_input"
    assert all(item["allowed_runtime_apply"] is False for item in report["code_improvement_orders"])
    assert report["auto_family_candidates"]
    assert report["auto_family_candidates"][0]["runtime_effect"] is False
    assert report["auto_family_candidates"][0]["allowed_runtime_apply"] is False
    assert report["ev_report_summary"]["consensus_count"] >= 2
    assert report["ev_report_summary"]["code_improvement_order_count"] >= 2


def test_pattern_lab_automation_routes_stale_lab_to_rejected_and_solo_order(tmp_path, monkeypatch):
    gemini_dir = _write_lab_outputs(
        tmp_path,
        "gemini",
        fresh=True,
        backlog=[{"title": "split-entry rebase 수량 정합성 shadow 감사", "기대효과": "정합성 개선"}],
    )
    claude_dir = _write_lab_outputs(
        tmp_path,
        "claude",
        fresh=False,
        backlog=[{"title": "split-entry rebase 수량 정합성 shadow 감사", "기대효과": "정합성 개선"}],
    )
    monkeypatch.setattr(mod, "GEMINI_LAB_DIR", gemini_dir)
    monkeypatch.setattr(mod, "CLAUDE_LAB_DIR", claude_dir)
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "report")

    report = mod.build_scalping_pattern_lab_automation_report("2026-05-08")

    assert report["lab_freshness"]["gemini"]["fresh"] is True
    assert report["lab_freshness"]["claude"]["fresh"] is False
    assert report["rejected_findings"][0]["lab"] == "claude"
    assert report["consensus_findings"] == []
    assert report["solo_findings"][0]["confidence"] == "solo"
    assert report["code_improvement_orders"][0]["runtime_effect"] is False
