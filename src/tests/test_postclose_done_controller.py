import json

from src.engine.automation import postclose_done_controller as mod


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_succeeded_status(report_dir, target_date="2026-06-03"):
    _write_json(
        report_dir / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target_date}.status.json",
        {"status": "succeeded"},
    )


def test_postclose_done_controller_passes_without_recovery(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json",
        {"status": "pass"},
    )
    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "done"
    assert report["final_verifier_status"] == "pass"
    assert len(calls) == 1
    assert report["actions"] == []


def test_postclose_done_controller_uses_project_venv_candidates(monkeypatch, tmp_path):
    venv_python = tmp_path / "venv" / "Scripts" / "python.exe"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        mod,
        "PYTHON_CANDIDATES",
        (
            tmp_path / ".venv" / "bin" / "python",
            venv_python,
        ),
    )

    assert mod._python_bin() == str(venv_python)


def test_postclose_done_controller_refreshes_recoverable_sources(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json"
    _write_json(
        verification,
        {
            "status": "fail",
            "missing_downstream_links": ["threshold_cycle_ev_sources_workorder"],
            "stale_downstream_links": ["runtime_approval_summary_stale_before_threshold_cycle_ev"],
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if "runtime_approval_summary" in " ".join(cmd):
            _write_json(verification, {"status": "pass"})
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=3,
        command_runner=fake_runner,
    )

    joined = "\n".join(" ".join(cmd) for cmd in calls)
    assert report["status"] == "done"
    assert "threshold_cycle_ev_report" in joined
    assert "runtime_approval_summary" in joined
    assert any(item["action"] == "refresh_code_improvement_workorder" for item in report["actions"])


def test_postclose_done_controller_reruns_wrapper_when_allowed(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json"
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_done_marker_missing"]},
        },
    )
    calls = []
    envs = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        envs.append(env or {})
        if cmd and cmd[0] == "bash":
            _write_json(verification, {"status": "pass"})
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert any(cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls)
    assert any(env.get("THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION") == "stop" for env in envs)


def test_postclose_done_controller_reruns_wrapper_for_fail_marker(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json"
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if cmd and cmd[0] == "bash":
            _write_json(verification, {"status": "pass"})
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert any(cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls)


def test_postclose_done_controller_does_not_rerun_wrapper_for_unclassified_warning(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json",
        {"status": "warning"},
    )
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )
    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "blocked_unclassified_verifier_status"
    assert report["blocked_reasons"] == ["verifier_status=warning"]
    assert not any(cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls)


def test_postclose_done_controller_accepts_done_marker_with_known_warning(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "handoff_warnings": ["active_sim_priority_preopen_handoff_pending"],
        },
    )
    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "done"
    assert report["final_verifier_status"] == "warning"
    assert report["blocked_reasons"] == []
    assert not any(cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls)


def test_postclose_done_controller_blocks_done_when_codex_runner_incomplete_is_required(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json",
        {"status": "pass"},
    )
    _write_json(
        report_dir / "codex_workorder_runner" / "codex_workorder_runner_2026-06-03.json",
        {"status": "blocked_uncompleted_implementation"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        require_codex_completed=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_uncompleted_implementation"
    assert report["codex_workorder_runner_status"] == "blocked_uncompleted_implementation"
    assert report["blocked_reasons"] == [
        "codex_workorder_runner_not_completed:blocked_uncompleted_implementation"
    ]


def test_postclose_done_controller_accepts_done_when_required_codex_runner_completed(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json",
        {"status": "pass"},
    )
    _write_json(
        report_dir / "codex_workorder_runner" / "codex_workorder_runner_2026-06-03.json",
        {"status": "completed"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        require_codex_completed=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "done"
    assert report["codex_workorder_runner_completed"] is True


def test_postclose_done_controller_blocks_done_marker_with_unknown_warning(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "handoff_warnings": ["source_generation_needs_review"],
        },
    )
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_recoverable_action_failed"
    assert report["blocked_reasons"] == ["source_generation_needs_review"]


def test_postclose_done_controller_blocks_non_recoverable(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json",
        {"status": "fail", "missing_downstream_links": ["provider_route_change_required"]},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_non_recoverable"
    assert report["actions"] == []


def test_postclose_done_controller_waits_for_running_predecessor_without_spending_recovery_attempts(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    status_path = report_dir / "threshold_cycle_postclose_status" / "threshold_cycle_postclose_2026-06-03.status.json"
    verification = report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json"
    _write_json(status_path, {"status": "running"})
    _write_json(verification, {"status": "pass"})
    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)
        _write_json(status_path, {"status": "succeeded"})

    monkeypatch.setattr(mod.time, "sleep", fake_sleep)
    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        predecessor_wait_sec=1,
        predecessor_timeout_sec=999,
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "done"
    assert sleep_calls == [1]
    assert len(calls) == 1
    assert [item["verifier_status"] for item in report["attempts"]] == ["predecessor_running", "pass"]


def test_postclose_done_controller_waits_for_missing_predecessor_status_without_spending_recovery_attempts(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    status_path = report_dir / "threshold_cycle_postclose_status" / "threshold_cycle_postclose_2026-06-03.status.json"
    verification = report_dir / "threshold_cycle_postclose_verification" / "threshold_cycle_postclose_verification_2026-06-03.json"
    _write_json(verification, {"status": "pass"})
    sleep_calls = []

    def fake_sleep(seconds):
        sleep_calls.append(seconds)
        _write_json(status_path, {"status": "succeeded"})

    monkeypatch.setattr(mod.time, "sleep", fake_sleep)
    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        predecessor_wait_sec=1,
        predecessor_timeout_sec=999,
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "done"
    assert sleep_calls == [1]
    assert len(calls) == 1
    assert [item["verifier_status"] for item in report["attempts"]] == ["predecessor_status_missing", "pass"]
