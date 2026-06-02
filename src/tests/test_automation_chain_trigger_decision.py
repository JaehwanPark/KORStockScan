import json
import os
from pathlib import Path

from src.engine.automation import automation_chain_trigger_decision as mod


def _write_json(path: Path, payload: dict, mtime: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    os.utime(path, (mtime, mtime))


def _write_text(path: Path, text: str, mtime: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def _patch_roots(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "data" / "report" / mod.REPORT_TYPE)


def test_missing_source_fails_open_to_run(tmp_path, monkeypatch):
    _patch_roots(tmp_path, monkeypatch)

    report = mod.build_report("2026-06-02", scope="workorder_branch", env={})
    decision = report["decisions"][0]

    assert decision["step_id"] == "workorder_branch"
    assert decision["decision"] == "run"
    assert decision["source_missing"] is True
    assert "source_missing_or_unreadable" in decision["trigger_reasons"]
    assert decision["runtime_effect"] is False
    assert decision["allowed_runtime_apply"] is False
    assert "runtime_threshold_apply" in decision["forbidden_uses"]


def test_fresh_output_and_no_drift_skips_workorder_branch(tmp_path, monkeypatch):
    _patch_roots(tmp_path, monkeypatch)
    target = "2026-06-02"
    source_paths = [
        tmp_path / "data/report/threshold_cycle_ev" / f"threshold_cycle_ev_{target}.json",
        tmp_path / "data/report/threshold_cycle_ev" / f"threshold_cycle_ev_{target}.md",
        tmp_path / "data/report/producer_gap_discovery" / f"producer_gap_discovery_{target}.json",
        tmp_path / "data/report/producer_gap_discovery" / f"producer_gap_discovery_{target}.md",
        tmp_path / "data/report/stage_hook_workorder_discovery" / f"stage_hook_workorder_discovery_{target}.json",
        tmp_path / "data/report/stage_hook_workorder_discovery" / f"stage_hook_workorder_discovery_{target}.md",
        tmp_path / "data/report/pattern_lab_currentness_audit" / f"pattern_lab_currentness_audit_{target}.json",
        tmp_path / "data/report/pattern_lab_currentness_audit" / f"pattern_lab_currentness_audit_{target}.md",
        tmp_path / "data/report/pattern_lab_ai_review" / f"pattern_lab_ai_review_{target}.json",
        tmp_path / "data/report/pattern_lab_ai_review" / f"pattern_lab_ai_review_{target}.md",
    ]
    for path in source_paths:
        if path.suffix == ".json":
            _write_json(path, {"status": "pass"}, 100)
        else:
            _write_text(path, "# report\n", 100)
    _write_json(
        tmp_path / "data/report/code_improvement_workorder" / f"code_improvement_workorder_{target}.json",
        {"status": "pass"},
        200,
    )
    _write_text(
        tmp_path / "docs/code-improvement-workorders" / f"code_improvement_workorder_{target}.md",
        "# workorder\n",
        200,
    )

    report = mod.build_report(target, scope="workorder_branch", env={})
    decision = report["decisions"][0]

    assert decision["decision"] == "skip"
    assert decision["trigger_reasons"] == ["fresh_outputs_no_trigger"]


def test_force_env_overrides_fresh_skip(tmp_path, monkeypatch):
    _patch_roots(tmp_path, monkeypatch)
    target = "2026-06-02"
    spec = mod.StepSpec(
        step_id="workorder_branch",
        scope="workorder_branch",
        output_paths=("out.json", "out.md"),
        source_paths=("source.json", "source.md"),
        force_env="THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH",
        description="test",
    )
    _write_json(tmp_path / "out.json", {"status": "pass"}, 200)
    _write_text(tmp_path / "out.md", "# out\n", 200)
    _write_json(tmp_path / "source.json", {"status": "pass"}, 100)
    _write_text(tmp_path / "source.md", "# source\n", 100)

    decision = mod.evaluate_step(spec, env={"THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH": "true"})

    assert target
    assert decision["decision"] == "run"
    assert decision["force_override"] is True
    assert "force_override" in decision["trigger_reasons"]


def test_lifecycle_window_drift_signal_runs_even_when_outputs_are_fresh(tmp_path, monkeypatch):
    _patch_roots(tmp_path, monkeypatch)
    spec = mod.StepSpec(
        step_id="lifecycle_window_mtd",
        scope="lifecycle_windows",
        output_paths=("window.json", "window.md"),
        source_paths=("daily.json", "daily.md"),
        force_env="THRESHOLD_CYCLE_FORCE_LIFECYCLE_BUCKET_WINDOWS",
        description="test",
    )
    _write_json(tmp_path / "window.json", {"status": "pass"}, 200)
    _write_text(tmp_path / "window.md", "# window\n", 200)
    _write_json(tmp_path / "daily.json", {"promotion_candidates": [{"id": "bucket"}]}, 100)
    _write_text(tmp_path / "daily.md", "# daily\n", 100)

    decision = mod.evaluate_step(spec, env={})

    assert decision["decision"] == "run"
    assert "upstream_drift_signal" in decision["trigger_reasons"]


def test_lifecycle_window_specs_only_depend_on_pre_window_sources():
    specs = [item for item in mod._step_specs("2026-06-02") if item.scope == "lifecycle_windows"]

    assert specs
    assert all("runtime_apply_bridge" not in " ".join(item.source_paths) for item in specs)


def test_cli_step_prints_decision_and_writes_contract(tmp_path, monkeypatch, capsys):
    _patch_roots(tmp_path, monkeypatch)

    rc = mod.main(["--date", "2026-06-02", "--scope", "workorder_branch", "--step", "workorder_branch", "--write"])
    captured = capsys.readouterr()

    assert rc == 0
    assert captured.out.strip() == "run"
    json_path = tmp_path / "data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-06-02.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["runtime_effect"] is False
    assert payload["allowed_runtime_apply"] is False
    assert payload["decisions"][0]["forbidden_uses"]
