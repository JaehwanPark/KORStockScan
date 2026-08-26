import json

from src.engine.automation import postclose_done_controller as mod


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_succeeded_status(report_dir, target_date="2026-06-03"):
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / f"threshold_cycle_postclose_{target_date}.status.json",
        {"status": "succeeded"},
    )


def _pass_verification(target_date="2026-06-03"):
    return {
        "status": "pass",
        "latest_done_marker": f"[DONE] threshold-cycle postclose target_date={target_date}",
    }


def _passable_artifact_status():
    return [{"label": "threshold_cycle_ev", "exists": True, "json_valid": True}]


def test_postclose_done_controller_does_not_require_codex_runner_by_default(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        _pass_verification(),
    )
    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "done"
    assert report["require_codex_completed"] is False
    assert report["codex_workorder_runner_status"] == "missing"
    assert not any("codex_workorder_runner" in " ".join(cmd) for cmd in calls)


def _tail_passable_artifact_status():
    return [
        {"label": "threshold_cycle_ev", "exists": True, "json_valid": True},
        {"label": "runtime_apply_gap_audit", "exists": True, "json_valid": True},
        {"label": "key_lineage_ledger", "exists": True, "json_valid": True},
        {"label": "conversion_lane", "exists": True, "json_valid": True},
        {"label": "code_improvement_workorder", "exists": True, "json_valid": True},
    ]


def _artifact_status_with_optional_absent():
    return [
        {"label": "threshold_cycle_ev", "exists": True, "json_valid": True},
        {"label": "conversion_lane", "exists": False, "size_bytes": 0},
    ]


def test_postclose_done_controller_passes_without_recovery(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        _pass_verification(),
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


def test_postclose_done_controller_does_not_accept_pass_without_done_marker(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {"status": "pass"},
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_unclassified_verifier_status"
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


def test_controller_verify_actions_inherit_disabled_stage_profile():
    verification = {
        "execution_profile": {
            "flags": {
                "swing_lifecycle": False,
                "swing_strategy_discovery": False,
                "swing_lifecycle_matrix": False,
                "swing_lifecycle_bucket_discovery": False,
                "deepseek_swing_lab": False,
            },
            "disabled_stage_flags": [
                "swing_lifecycle",
                "swing_strategy_discovery",
                "swing_lifecycle_matrix",
                "swing_lifecycle_bucket_discovery",
                "deepseek_swing_lab",
                "not_a_verifier_stage",
            ],
        }
    }

    verify_command = mod._build_verify_action("2026-06-03", verification).command
    pending_command = mod._build_pending_verify_action(
        "2026-06-03", verification
    ).command

    assert verify_command is not None
    assert pending_command is not None
    expected_stages = [
        "swing_lifecycle",
        "swing_strategy_discovery",
        "swing_lifecycle_matrix",
        "swing_lifecycle_bucket_discovery",
        "deepseek_swing_lab",
    ]

    def disabled_stages(command):
        return [
            command[index + 1]
            for index, token in enumerate(command[:-1])
            if token == "--disabled-stage"
        ]

    assert disabled_stages(verify_command) == expected_stages
    assert disabled_stages(pending_command) == expected_stages
    assert "not_a_verifier_stage" not in verify_command


def test_tail_repair_actions_preserve_wrapper_scope(monkeypatch):
    for env_name in (
        "THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT",
        "THRESHOLD_CYCLE_RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL",
        "THRESHOLD_CYCLE_RUN_PRODUCER_GAP_DISCOVERY",
        "THRESHOLD_CYCLE_RUN_STAGE_HOOK_WORKORDER_DISCOVERY",
        "THRESHOLD_CYCLE_RUN_STAGE_HOOK_RUNTIME_SCAFFOLD",
    ):
        monkeypatch.delenv(env_name, raising=False)
    verification = {
        "execution_profile": {
            "flags": {
                "swing_lifecycle": False,
                "swing_strategy_discovery": False,
                "swing_lifecycle_matrix": False,
                "swing_lifecycle_bucket_discovery": False,
                "deepseek_swing_lab": False,
            }
        }
    }

    actions = mod._tail_stage_repair_actions(
        "2026-06-03", "verify_threshold_cycle_postclose_chain", verification
    )
    commands = {
        action.action: action.command
        for action in actions
        if action.command is not None
    }

    assert "--exclude-swing" in commands["refresh_pattern_lab_currentness_audit"]
    assert "--exclude-swing" in commands["refresh_pattern_lab_propagation_audit"]
    assert "--exclude-swing" in commands["refresh_code_improvement_workorder"]
    assert "--exclude-swing" in commands["refresh_threshold_cycle_ev"]
    assert "--disabled-source" in commands["refresh_threshold_cycle_ev"]
    assert "--exclude-swing" in commands["refresh_runtime_approval_summary"]
    assert "--producer-gap-disabled" in commands["refresh_runtime_approval_summary"]
    assert "--exclude-swing" in commands["refresh_runtime_apply_gap_audit"]


def test_postclose_done_controller_refreshes_recoverable_sources(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "missing_downstream_links": ["threshold_cycle_ev_sources_workorder"],
            "stale_downstream_links": [
                "runtime_approval_summary_stale_before_threshold_cycle_ev"
            ],
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if "runtime_approval_summary" in " ".join(cmd):
            _write_json(verification, _pass_verification())
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
    assert any(
        item["action"] == "refresh_code_improvement_workorder"
        for item in report["actions"]
    )
    action_names = [item["action"] for item in report["actions"]]
    assert action_names.index("refresh_threshold_cycle_ev") < action_names.index(
        "refresh_code_improvement_workorder"
    ) < action_names.index("refresh_runtime_approval_summary")


def test_generic_fingerprint_repair_refreshes_ev_before_final_workorder():
    actions = mod._recovery_actions(
        "2026-08-25",
        {
            "source_generation_warnings": [
                "code_improvement_workorder_source_fingerprint_sha256_mismatch:threshold_cycle_ev"
            ]
        },
        allow_wrapper_rerun=False,
    )

    assert [action.action for action in actions] == [
        "refresh_threshold_cycle_ev",
        "refresh_code_improvement_workorder",
        "refresh_runtime_approval_summary",
    ]


def test_runtime_gap_stale_does_not_mask_fingerprint_repair():
    actions = mod._recovery_actions(
        "2026-08-25",
        {
            "stale_downstream_links": [
                "runtime_apply_gap_audit_stale_before_threshold_preopen_apply"
            ],
            "source_generation_warnings": [
                "code_improvement_workorder_source_fingerprint_sha256_mismatch:threshold_cycle_ev"
            ],
            "conversion_kpi": {
                "warnings": ["active_or_hypothesis_preopen_handoff_pending"]
            },
        },
        allow_wrapper_rerun=False,
    )

    assert [action.action for action in actions] == [
        "refresh_runtime_apply_gap_audit",
        "refresh_threshold_cycle_ev",
        "refresh_code_improvement_workorder",
        "refresh_runtime_approval_summary",
    ]


def test_postclose_done_controller_repairs_ev_workorder_stale_link_without_full_wrapper_rerun(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "stale_downstream_links": [
                "threshold_cycle_ev_stale_before_code_improvement_workorder"
            ],
            "execution_profile": {
                "flags": {
                    "swing_lifecycle": False,
                    "swing_strategy_discovery": False,
                    "swing_lifecycle_matrix": False,
                    "swing_lifecycle_bucket_discovery": False,
                }
            },
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if "verify_threshold_cycle_postclose_chain" in " ".join(cmd) and len(calls) > 1:
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    joined = "\n".join(" ".join(cmd) for cmd in calls)
    assert report["status"] == "done"
    assert "strategy_position_performance_report" in joined
    assert "daily_threshold_cycle_report" in joined
    assert "--ai-correction-provider openai" in joined
    assert "--reuse-ai-review-if-valid" in joined
    assert "threshold_cycle_ev_report" in joined
    assert "build_code_improvement_workorder" in joined
    assert any(
        "src.engine.build_code_improvement_workorder" in " ".join(cmd)
        and "--exclude-swing" in cmd
        for cmd in calls
    )
    assert "runtime_approval_summary" in joined
    action_names = [item["action"] for item in report["actions"]]
    assert action_names == [
        "sync_exact_trade_performance_facts",
        "refresh_daily_threshold_cycle_report",
        "refresh_threshold_cycle_ev",
        "refresh_pattern_lab_currentness_audit",
        "refresh_pattern_lab_propagation_audit",
        "refresh_code_improvement_workorder",
        "refresh_threshold_cycle_ev",
        "refresh_code_improvement_workorder_final",
        "refresh_runtime_approval_summary",
        "refresh_next_stage2_checklist",
        "refresh_next_preopen_apply",
        "refresh_runtime_apply_gap_audit",
        "verify_postclose_chain",
    ]
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert report["full_wrapper_rerun_used"] is False
    assert (
        report["root_cause"]
        == "threshold_cycle_ev_stale_before_code_improvement_workorder"
    )
    assert report["selected_recovery_action"] == "sync_exact_trade_performance_facts"


def test_ev_trade_count_mismatch_uses_exact_fact_then_calibration_recovery():
    actions = mod._recovery_actions(
        "2026-08-25",
        {
            "handoff_warnings": [
                "threshold_cycle_ev_trade_review_calibration_count_mismatch"
            ]
        },
        allow_wrapper_rerun=False,
    )

    assert [action.action for action in actions[:3]] == [
        "sync_exact_trade_performance_facts",
        "refresh_daily_threshold_cycle_report",
        "refresh_threshold_cycle_ev",
    ]


def test_postclose_done_controller_reconciles_done_marker_without_full_wrapper_rerun(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(
        mod,
        "POSTCLOSE_LOG_PATH",
        tmp_path / "logs" / "threshold_cycle_postclose_cron.log",
    )
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_done_marker_missing"]},
            "artifact_status": _passable_artifact_status(),
        },
    )
    calls = []
    envs = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        envs.append(env or {})
        if "verify_threshold_cycle_postclose_chain" in " ".join(cmd) and len(calls) > 1:
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert any(item["action"] == "marker_reconciliation" for item in report["actions"])
    assert not any(
        env.get("THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION") == "stop" for env in envs
    )
    assert report["full_wrapper_rerun_used"] is False
    marker_text = mod.POSTCLOSE_LOG_PATH.read_text(encoding="utf-8")
    assert "recovery_action=marker_reconciliation" in marker_text
    assert "daily_ev=true" not in marker_text
    assert "runtime_approval_summary=true" not in marker_text


def test_postclose_done_controller_reconciles_fail_marker_without_full_wrapper_rerun(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(
        mod,
        "POSTCLOSE_LOG_PATH",
        tmp_path / "logs" / "threshold_cycle_postclose_cron.log",
    )
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "artifact_status": _passable_artifact_status(),
            "execution_profile": {
                "flags": {
                    "daily_ev": True,
                    "swing_lifecycle": False,
                }
            },
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if "verify_threshold_cycle_postclose_chain" in " ".join(cmd) and len(calls) > 1:
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert any(item["action"] == "marker_reconciliation" for item in report["actions"])
    assert report["full_wrapper_rerun_used"] is False
    assert report["selected_recovery_action"] == "marker_reconciliation"
    marker_text = mod.POSTCLOSE_LOG_PATH.read_text(encoding="utf-8")
    assert "daily_ev=true" in marker_text
    assert "swing_lifecycle=false" in marker_text


def test_postclose_done_controller_reconciles_repaired_failed_status_without_full_wrapper_rerun(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    log_path = tmp_path / "logs" / "threshold_cycle_postclose_cron.log"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(mod, "POSTCLOSE_LOG_PATH", log_path)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json",
        {"status": "failed", "reason": "command_failed"},
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-06-03 started_at=2026-06-03T18:00:00+0900",
                "[DONE] threshold-cycle postclose target_date=2026-06-03 finished_at=2026-06-03T18:09:00+0900",
                "[FAIL] threshold-cycle postclose target_date=2026-06-03 reason=command_failed failed_at=2026-06-03T18:10:00+0900",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "artifact_status": _passable_artifact_status(),
            "handoff_warnings": [
                "active_sim_priority_preopen_handoff_pending",
                "lifecycle_bucket_confirmation_windows_not_target",
                "lifecycle_bucket_discovery_rolling10d_parent_granularity_not_target",
            ],
            "conversion_kpi": {
                "status": "warning",
                "warnings": ["active_or_hypothesis_preopen_handoff_pending"],
            },
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        joined = " ".join(cmd)
        if (
            "verify_threshold_cycle_postclose_chain" in joined
            and "--allow-pending-done-marker" in cmd
        ):
            _write_json(
                verification,
                {
                    "status": "warning",
                    "predecessor_integrity": {
                        "log_issues": ["postclose_fail_marker_present"]
                    },
                    "artifact_status": _passable_artifact_status(),
                    "handoff_warnings": [
                        "active_sim_priority_preopen_handoff_pending",
                        "lifecycle_bucket_confirmation_windows_not_target",
                        "lifecycle_bucket_discovery_rolling10d_parent_granularity_not_target",
                    ],
                    "conversion_kpi": {
                        "status": "warning",
                        "warnings": ["active_or_hypothesis_preopen_handoff_pending"],
                    },
                },
            )
        elif "verify_threshold_cycle_postclose_chain" in joined:
            status_payload = json.loads(
                (
                    report_dir
                    / "threshold_cycle_postclose_status"
                    / "threshold_cycle_postclose_2026-06-03.status.json"
                ).read_text(encoding="utf-8")
            )
            if status_payload.get("status") == "succeeded":
                _write_json(
                    verification,
                    {
                        "status": "warning",
                        "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03 recovery_action=tail_repair_done_reconciliation",
                        "predecessor_integrity": {"log_issues": []},
                        "artifact_status": _passable_artifact_status(),
                        "handoff_warnings": [
                            "active_sim_priority_preopen_handoff_pending",
                            "lifecycle_bucket_confirmation_windows_not_target",
                            "lifecycle_bucket_discovery_rolling10d_parent_granularity_not_target",
                        ],
                        "conversion_kpi": {
                            "status": "warning",
                            "warnings": [
                                "active_or_hypothesis_preopen_handoff_pending"
                            ],
                        },
                    },
                )
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert any(
        item["action"] == "tail_repair_done_reconciliation"
        for item in report["actions"]
    )
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert report["full_wrapper_rerun_used"] is False


def test_postclose_done_controller_repairs_failed_tail_stage_without_full_wrapper_rerun(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    log_path = tmp_path / "logs" / "threshold_cycle_postclose_cron.log"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(mod, "POSTCLOSE_LOG_PATH", log_path)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json",
        {"status": "failed", "reason": "command_failed"},
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-06-03 started_at=2026-06-03T18:00:00+0900",
                "[threshold-cycle] artifact ready label=runtime_apply_gap_audit path=/tmp/a waited=0s json_valid=true",
                "[threshold-cycle] resource guard pass label=key_lineage_ledger status=ok",
                "taskset: failed command was killed",
                "[FAIL] threshold-cycle postclose target_date=2026-06-03 reason=command_failed failed_at=2026-06-03T18:10:00+0900",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "artifact_status": _tail_passable_artifact_status(),
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        joined = " ".join(cmd)
        if (
            "verify_threshold_cycle_postclose_chain" in joined
            and "--allow-pending-done-marker" in cmd
        ):
            _write_json(
                verification,
                {
                    "status": "pass_with_pending_done_marker",
                    "predecessor_integrity": {
                        "log_issues": ["postclose_fail_marker_present"]
                    },
                    "artifact_status": _tail_passable_artifact_status(),
                },
            )
        elif "verify_threshold_cycle_postclose_chain" in joined:
            status_payload = json.loads(
                (
                    report_dir
                    / "threshold_cycle_postclose_status"
                    / "threshold_cycle_postclose_2026-06-03.status.json"
                ).read_text(encoding="utf-8")
            )
            if status_payload.get("status") == "succeeded":
                _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    joined_calls = "\n".join(" ".join(cmd) for cmd in calls)
    assert report["status"] == "done"
    assert "src.engine.automation.key_lineage_ledger" in joined_calls
    assert "src.engine.automation.conversion_lane" in joined_calls
    assert "src.engine.build_code_improvement_workorder" in joined_calls
    assert "src.engine.build_next_stage2_checklist" in joined_calls
    assert "src.engine.automation.tuning_performance_control_tower" in joined_calls
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert any(
        item["action"] == "tail_repair_done_reconciliation"
        for item in report["actions"]
    )
    assert report["selected_recovery_action"] == "refresh_key_lineage_ledger"
    assert report["latest_failed_tail_stage"] == "key_lineage_ledger"
    assert report["tail_stage_minimal_repair_supported"] is True
    assert report["full_wrapper_rerun_used"] is False
    assert any(
        "src.engine.build_code_improvement_workorder" in " ".join(cmd)
        and "--max-orders" in cmd
        and "12" in cmd
        for cmd in calls
    )
    assert "recovery_action=tail_repair_done_reconciliation" in log_path.read_text(
        encoding="utf-8"
    )


def test_postclose_done_controller_tail_repair_can_skip_tuning_performance_control_tower(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    log_path = tmp_path / "logs" / "threshold_cycle_postclose_cron.log"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(mod, "POSTCLOSE_LOG_PATH", log_path)
    monkeypatch.setenv("THRESHOLD_CYCLE_RUN_TUNING_PERFORMANCE_CONTROL_TOWER", "false")
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json",
        {"status": "failed", "reason": "command_failed"},
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-06-03 started_at=2026-06-03T18:00:00+0900",
                "[threshold-cycle] resource guard pass label=key_lineage_ledger status=ok",
                "[FAIL] threshold-cycle postclose target_date=2026-06-03 reason=command_failed failed_at=2026-06-03T18:10:00+0900",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "artifact_status": _tail_passable_artifact_status(),
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        joined = " ".join(cmd)
        if (
            "verify_threshold_cycle_postclose_chain" in joined
            and "--allow-pending-done-marker" in cmd
        ):
            _write_json(
                verification,
                {
                    "status": "pass_with_pending_done_marker",
                    "predecessor_integrity": {
                        "log_issues": ["postclose_fail_marker_present"]
                    },
                    "artifact_status": _tail_passable_artifact_status(),
                },
            )
        elif "verify_threshold_cycle_postclose_chain" in joined:
            status_payload = json.loads(
                (
                    report_dir
                    / "threshold_cycle_postclose_status"
                    / "threshold_cycle_postclose_2026-06-03.status.json"
                ).read_text(encoding="utf-8")
            )
            if status_payload.get("status") == "succeeded":
                _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    joined_calls = "\n".join(" ".join(cmd) for cmd in calls)
    assert report["status"] == "done"
    assert "src.engine.automation.tuning_performance_control_tower" not in joined_calls
    assert report["full_wrapper_rerun_used"] is False


def test_postclose_done_controller_tail_repair_uses_workorder_max_orders_env(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    log_path = tmp_path / "logs" / "threshold_cycle_postclose_cron.log"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(mod, "POSTCLOSE_LOG_PATH", log_path)
    monkeypatch.setenv("CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS", "7")
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json",
        {"status": "failed", "reason": "command_failed"},
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-06-03 started_at=2026-06-03T18:00:00+0900",
                "[threshold-cycle] resource guard pass label=key_lineage_ledger status=ok",
                "[FAIL] threshold-cycle postclose target_date=2026-06-03 reason=command_failed failed_at=2026-06-03T18:10:00+0900",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "artifact_status": _tail_passable_artifact_status(),
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        joined = " ".join(cmd)
        if (
            "verify_threshold_cycle_postclose_chain" in joined
            and "--allow-pending-done-marker" in cmd
        ):
            _write_json(
                verification,
                {
                    "status": "pass_with_pending_done_marker",
                    "predecessor_integrity": {
                        "log_issues": ["postclose_fail_marker_present"]
                    },
                    "artifact_status": _tail_passable_artifact_status(),
                },
            )
        elif "verify_threshold_cycle_postclose_chain" in joined:
            status_payload = json.loads(
                (
                    report_dir
                    / "threshold_cycle_postclose_status"
                    / "threshold_cycle_postclose_2026-06-03.status.json"
                ).read_text(encoding="utf-8")
            )
            if status_payload.get("status") == "succeeded":
                _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert any(
        "src.engine.build_code_improvement_workorder" in " ".join(cmd)
        and "--max-orders" in cmd
        and "7" in cmd
        for cmd in calls
    )


def test_tail_stage_repair_actions_refresh_final_ev_after_workorder():
    actions = mod._tail_stage_repair_actions(
        "2026-06-03",
        "key_lineage_ledger",
        {
            "execution_profile": {
                "flags": {
                    "swing_lifecycle": False,
                    "swing_strategy_discovery": False,
                    "swing_lifecycle_matrix": False,
                    "swing_lifecycle_bucket_discovery": False,
                }
            }
        },
    )
    action_names = [item.action for item in actions]

    assert action_names.index(
        "refresh_code_improvement_workorder"
    ) < action_names.index("refresh_threshold_cycle_ev")
    assert action_names.index("refresh_threshold_cycle_ev") < action_names.index(
        "refresh_runtime_approval_summary"
    )
    assert all(
        "--exclude-swing" in (item.command or [])
        for item in actions
        if item.action == "refresh_code_improvement_workorder"
    )


def test_postclose_done_controller_tail_repair_requires_artifact_status_before_done_reconciliation(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    log_path = tmp_path / "logs" / "threshold_cycle_postclose_cron.log"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(mod, "POSTCLOSE_LOG_PATH", log_path)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json",
        {"status": "failed", "reason": "command_failed"},
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-06-03 started_at=2026-06-03T18:00:00+0900",
                "[threshold-cycle] resource guard pass label=key_lineage_ledger status=ok",
                "[FAIL] threshold-cycle postclose target_date=2026-06-03 reason=command_failed failed_at=2026-06-03T18:10:00+0900",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "artifact_status": _tail_passable_artifact_status(),
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if (
            "verify_threshold_cycle_postclose_chain" in " ".join(cmd)
            and "--allow-pending-done-marker" in cmd
        ):
            _write_json(
                verification,
                {
                    "status": "pass_with_pending_done_marker",
                    "predecessor_integrity": {
                        "log_issues": ["postclose_fail_marker_present"]
                    },
                },
            )
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "blocked_recoverable_action_failed"
    assert report["blocked_reasons"] == ["tail_repair_done_reconciliation_failed"]
    assert not any(
        "[DONE] threshold-cycle postclose" in line
        for line in log_path.read_text(encoding="utf-8").splitlines()
    )


def test_postclose_done_controller_uses_previous_supported_tail_stage_after_bad_full_rerun(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    log_path = tmp_path / "logs" / "threshold_cycle_postclose_cron.log"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(mod, "POSTCLOSE_LOG_PATH", log_path)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json",
        {"status": "failed", "reason": "command_failed"},
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-06-03 started_at=2026-06-03T18:00:00+0900",
                "[threshold-cycle] resource guard pass label=key_lineage_ledger status=ok",
                "[FAIL] threshold-cycle postclose target_date=2026-06-03 reason=command_failed failed_at=2026-06-03T18:10:00+0900",
                "[START] threshold-cycle postclose target_date=2026-06-03 started_at=2026-06-03T18:15:00+0900",
                "[threshold-cycle] resource guard timeout label=scalp_entry_action_decision_matrix waited=300s status=low_swap",
                "[FAIL] threshold-cycle postclose target_date=2026-06-03 reason=command_failed failed_at=2026-06-03T18:20:00+0900",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "artifact_status": _tail_passable_artifact_status(),
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        joined = " ".join(cmd)
        if (
            "verify_threshold_cycle_postclose_chain" in joined
            and "--allow-pending-done-marker" in cmd
        ):
            _write_json(
                verification,
                {
                    "status": "pass_with_pending_done_marker",
                    "predecessor_integrity": {
                        "log_issues": ["postclose_fail_marker_present"]
                    },
                    "artifact_status": _tail_passable_artifact_status(),
                },
            )
        elif "verify_threshold_cycle_postclose_chain" in joined:
            status_payload = json.loads(
                (
                    report_dir
                    / "threshold_cycle_postclose_status"
                    / "threshold_cycle_postclose_2026-06-03.status.json"
                ).read_text(encoding="utf-8")
            )
            if status_payload.get("status") == "succeeded":
                _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert report["latest_failed_tail_stage"] == "key_lineage_ledger"
    assert report["full_wrapper_rerun_used"] is False
    assert any(
        "src.engine.automation.key_lineage_ledger" in " ".join(cmd) for cmd in calls
    )
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )


def test_postclose_done_controller_prefers_full_rerun_for_required_artifact_missing_over_tail_repair(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    log_path = tmp_path / "logs" / "threshold_cycle_postclose_cron.log"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(mod, "POSTCLOSE_LOG_PATH", log_path)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json",
        {"status": "failed", "reason": "command_failed"},
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        "\n".join(
            [
                "[START] threshold-cycle postclose target_date=2026-06-03 started_at=2026-06-03T18:00:00+0900",
                "[threshold-cycle] resource guard pass label=key_lineage_ledger status=ok",
                "[FAIL] threshold-cycle postclose target_date=2026-06-03 reason=command_failed failed_at=2026-06-03T18:10:00+0900",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "missing_required_artifacts": ["threshold_cycle_ev"],
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"]:
            _write_json(
                report_dir
                / "threshold_cycle_postclose_status"
                / "threshold_cycle_postclose_2026-06-03.status.json",
                {"status": "succeeded"},
            )
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert report["full_wrapper_rerun_used"] is True
    assert report["selected_recovery_action"] == "rerun_threshold_cycle_postclose"
    assert any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert not any(
        "src.engine.automation.key_lineage_ledger" in " ".join(cmd) for cmd in calls
    )


def test_postclose_done_controller_allows_marker_reconciliation_with_optional_absent_artifact(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(
        mod,
        "POSTCLOSE_LOG_PATH",
        tmp_path / "logs" / "threshold_cycle_postclose_cron.log",
    )
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_done_marker_missing"]},
            "artifact_status": _artifact_status_with_optional_absent(),
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if "verify_threshold_cycle_postclose_chain" in " ".join(cmd) and len(calls) > 1:
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert any(item["action"] == "marker_reconciliation" for item in report["actions"])
    assert report["full_wrapper_rerun_used"] is False


def test_postclose_done_controller_does_not_select_marker_reconciliation_when_status_not_succeeded(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_json(
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json",
        {"status": "failed"},
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
        },
    )
    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "exhausted_recoverable_actions"
    assert not any(
        item["action"] == "marker_reconciliation" for item in report["actions"]
    )


def test_postclose_done_controller_does_not_select_marker_reconciliation_without_artifact_status(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(
        mod,
        "POSTCLOSE_LOG_PATH",
        tmp_path / "logs" / "threshold_cycle_postclose_cron.log",
    )
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_done_marker_missing"]},
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_recoverable_action_failed"
    assert not any(
        item["action"] == "marker_reconciliation" for item in report["actions"]
    )
    assert not mod.POSTCLOSE_LOG_PATH.exists()


def test_postclose_done_controller_does_not_select_marker_reconciliation_with_malformed_artifact_status(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(
        mod,
        "POSTCLOSE_LOG_PATH",
        tmp_path / "logs" / "threshold_cycle_postclose_cron.log",
    )
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_done_marker_missing"]},
            "artifact_status": [
                {"label": "threshold_cycle_ev", "exists": True, "json_valid": True},
                {},
            ],
        },
    )
    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "exhausted_recoverable_actions"
    assert not any(
        item["action"] == "marker_reconciliation" for item in report["actions"]
    )
    assert not mod.POSTCLOSE_LOG_PATH.exists()


def test_postclose_done_controller_does_not_select_marker_reconciliation_with_unknown_warning(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(
        mod,
        "POSTCLOSE_LOG_PATH",
        tmp_path / "logs" / "threshold_cycle_postclose_cron.log",
    )
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_done_marker_missing"]},
            "handoff_warnings": ["source_generation_needs_review"],
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_recoverable_action_failed"
    assert not any(
        item["action"] == "marker_reconciliation" for item in report["actions"]
    )
    assert not mod.POSTCLOSE_LOG_PATH.exists()


def test_postclose_done_controller_does_not_select_marker_reconciliation_with_conversion_kpi_fail(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(
        mod,
        "POSTCLOSE_LOG_PATH",
        tmp_path / "logs" / "threshold_cycle_postclose_cron.log",
    )
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_done_marker_missing"]},
            "conversion_kpi": {
                "status": "fail",
                "issues": ["active_or_hypothesis_catalog_missing"],
            },
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_recoverable_action_failed"
    assert "active_or_hypothesis_catalog_missing" in report["blocked_reasons"]
    assert not any(
        item["action"] == "marker_reconciliation" for item in report["actions"]
    )
    assert not mod.POSTCLOSE_LOG_PATH.exists()


def test_postclose_done_controller_does_not_select_marker_reconciliation_with_missing_workorder_snapshot(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    monkeypatch.setattr(
        mod,
        "POSTCLOSE_LOG_PATH",
        tmp_path / "logs" / "threshold_cycle_postclose_cron.log",
    )
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
            "workorder_snapshot": {"status": "missing_snapshot_identity"},
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_recoverable_action_failed"
    assert "workorder_snapshot_missing_snapshot_identity" in report["blocked_reasons"]
    assert not any(
        item["action"] == "marker_reconciliation" for item in report["actions"]
    )
    assert not mod.POSTCLOSE_LOG_PATH.exists()


def test_postclose_done_controller_blocks_done_with_unknown_conversion_kpi_warning(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "conversion_kpi": {
                "status": "warning",
                "warnings": ["conversion_lane_no_candidates"],
            },
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_recoverable_action_failed"
    assert report["blocked_reasons"] == ["conversion_lane_no_candidates"]


def test_postclose_done_controller_accepts_next_preopen_handoff_conversion_warning(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "handoff_warnings": ["active_sim_priority_preopen_handoff_pending"],
            "conversion_kpi": {
                "status": "warning",
                "warnings": ["active_or_hypothesis_preopen_handoff_pending"],
            },
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "done"
    assert report["final_verifier_status"] == "warning"
    assert report["blocked_reasons"] == []


def test_postclose_done_controller_accepts_report_only_followup_warnings(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "artifact_status": _passable_artifact_status(),
            "handoff_warnings": [
                "active_sim_priority_stale_seed_alias_consumed",
                "lifecycle_bucket_discovery_mtd_parent_granularity_not_target",
                "lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target",
                "limit_down_watch_candidate_source_invalid",
                "limit_down_watch_candidate_source_quality_blocked",
                "limit_down_watch_event_source_invalid",
                "limit_down_watch_source_blocked",
                "swing_active_arm_priority_preopen_handoff_pending",
                "swing_active_arm_priority_runtime_observation_missing",
                "swing_lifecycle_bucket_discovery:ai_two_pass_review_fail_closed_sim_auto_blocked",
                "swing_lifecycle_bucket_discovery:ai_two_pass_review_missing_fail_closed",
                "swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_required_source_only",
                "swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_sim_auto_blocked",
                "swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_fail_closed",
                "swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_source_only",
            ],
            "conversion_kpi": {
                "status": "warning",
                "warnings": ["active_or_hypothesis_not_instrumented"],
            },
        },
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "done"
    assert report["final_verifier_status"] == "warning"
    assert report["blocked_reasons"] == []


def test_postclose_done_controller_accepts_active_priority_natural_absence_warning(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "artifact_status": _passable_artifact_status(),
            "handoff_warnings": [
                "active_sim_priority_preopen_handoff_pending",
                "active_sim_priority_runtime_observation_missing",
            ],
            "active_sim_priority_handoff": {
                "status": "warning",
                "missing": [],
                "warnings": [
                    "active_sim_priority_preopen_handoff_pending",
                    "active_sim_priority_runtime_observation_missing",
                ],
                "active_priority_match_absence_diagnosis": {
                    "status": "warning",
                    "diagnosis": "catalog_handoff_ok_natural_absence",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            },
        },
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "done"
    assert report["blocked_reasons"] == []


def test_postclose_done_controller_repairs_active_priority_handoff_by_refreshing_next_preopen_apply(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "handoff_warnings": ["active_sim_priority_handoff_missing"],
            "active_sim_priority_handoff": {
                "status": "fail",
                "missing": ["active_sim_priority_preopen_handoff_missing"],
            },
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        joined = " ".join(cmd)
        if (
            "verify_threshold_cycle_postclose_chain" in joined
            and "--allow-pending-done-marker" in cmd
        ):
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    joined = "\n".join(" ".join(cmd) for cmd in calls)
    assert report["status"] == "done"
    assert "threshold_cycle_preopen_apply" in joined
    assert "--date 2026-06-04" in joined
    assert "--source-date 2026-06-03" in joined
    assert "runtime_apply_gap_audit" in joined
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )


def test_next_preopen_apply_uses_next_krx_trading_day_after_friday():
    action = mod._build_next_preopen_apply_action("2026-07-24")

    assert action.command is not None
    assert "--date" in action.command
    assert action.command[action.command.index("--date") + 1] == "2026-07-27"
    assert action.command[action.command.index("--source-date") + 1] == "2026-07-24"


def test_postclose_done_controller_accepts_missing_next_preopen_apply_as_optional(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "handoff_warnings": ["active_sim_priority_preopen_handoff_pending"],
            "conversion_kpi": {
                "status": "warning",
                "warnings": ["active_or_hypothesis_preopen_handoff_pending"],
            },
            "artifact_status": [
                {"label": "threshold_cycle_ev", "exists": True, "json_valid": True},
                {
                    "label": "threshold_preopen_apply_next",
                    "exists": False,
                    "json_valid": False,
                },
            ],
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "done"
    assert report["blocked_reasons"] == []


def test_postclose_done_controller_reruns_wrapper_only_for_missing_start_marker(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "predecessor_integrity": {"log_issues": ["postclose_start_marker_missing"]},
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if cmd and cmd[0] == "bash":
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert report["full_wrapper_rerun_used"] is True


def test_postclose_done_controller_reruns_wrapper_for_required_artifact_missing(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "missing_required_artifacts": ["threshold_cycle_ev"],
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if cmd and cmd[0] == "bash":
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert report["full_wrapper_rerun_used"] is True


def test_postclose_done_controller_reruns_wrapper_for_invalid_json_artifact(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(
        verification,
        {
            "status": "fail",
            "artifact_status": [
                {"label": "threshold_cycle_ev", "exists": True, "json_valid": False}
            ],
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if cmd and cmd[0] == "bash":
            _write_json(verification, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        allow_wrapper_rerun=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )
    assert report["full_wrapper_rerun_used"] is True


def test_postclose_done_controller_does_not_rerun_wrapper_for_unclassified_warning(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {"status": "warning"},
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
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
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )


def test_postclose_done_controller_accepts_done_marker_with_known_warning(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
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
    assert not any(
        cmd[:2] == ["bash", "deploy/run_threshold_cycle_postclose.sh"] for cmd in calls
    )


def test_disabled_artifact_inventory_does_not_trigger_wrapper_rerun():
    verification = {
        "missing_required_artifacts": [],
        "artifact_status": [
            {
                "label": "swing_daily_simulation",
                "exists": False,
                "json_valid": False,
            }
        ],
    }

    assert mod._verification_artifacts_passable(verification) is True
    assert mod._has_invalid_artifact_status(verification) is False


def test_limit_down_no_observation_is_done_acceptable_warning():
    assert {
        "limit_down_watch_ordered_path_not_observed",
        "limit_down_watch_observer_activation_not_observed",
        "limit_down_watch_operator_live_conversion_approval_required",
        "limit_down_watch_separate_preopen_apply_ready",
    }.issubset(mod.DONE_ACCEPTABLE_WARNING_ISSUES)


def test_postclose_done_controller_blocks_done_when_codex_runner_incomplete_is_required(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        _pass_verification(),
    )
    _write_json(
        report_dir
        / "codex_workorder_runner"
        / "codex_workorder_runner_2026-06-03.json",
        {"status": "blocked_uncompleted_implementation"},
    )

    calls = []

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        require_codex_completed=True,
        command_runner=lambda cmd, env=None: calls.append(cmd) or 0,
    )

    assert report["status"] == "blocked_uncompleted_implementation"
    assert (
        report["codex_workorder_runner_status"] == "blocked_uncompleted_implementation"
    )
    assert report["codex_workorder_runner_two_pass_status"] == "missing"
    assert report["blocked_reasons"] == [
        "codex_workorder_runner_not_completed:blocked_uncompleted_implementation:missing"
    ]
    assert any("codex_workorder_runner" in " ".join(cmd) for cmd in calls)


def test_postclose_done_controller_accepts_done_when_required_codex_runner_completed(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        _pass_verification(),
    )
    _write_json(
        report_dir
        / "codex_workorder_runner"
        / "codex_workorder_runner_2026-06-03.json",
        {"status": "completed", "two_pass_status": "pass2_not_required"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        require_codex_completed=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "done"
    assert report["codex_workorder_runner_completed"] is True


def test_postclose_done_controller_reruns_completed_runner_for_latest_generation(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        _pass_verification(),
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g2"},
    )
    runner_path = (
        report_dir / "codex_workorder_runner" / "codex_workorder_runner_2026-06-03.json"
    )
    _write_json(
        runner_path,
        {
            "status": "completed",
            "two_pass_status": "pass2_not_required",
            "source_generation_id": "g1",
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if "codex_workorder_runner" in " ".join(cmd):
            _write_json(
                runner_path,
                {
                    "status": "completed",
                    "two_pass_status": "pass2_not_required",
                    "source_generation_id": "g2",
                },
            )
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        require_codex_completed=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert report["workorder_generation_id"] == "g2"
    assert report["codex_workorder_runner_source_generation_id"] == "g2"
    assert report["codex_workorder_runner_completed"] is True
    assert any("codex_workorder_runner" in " ".join(cmd) for cmd in calls)


def test_postclose_done_controller_rejects_completed_runner_without_two_pass_terminal_status(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        _pass_verification(),
    )
    _write_json(
        report_dir
        / "codex_workorder_runner"
        / "codex_workorder_runner_2026-06-03.json",
        {"status": "completed", "two_pass_status": "blocked_regeneration_failed"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        require_codex_completed=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_uncompleted_implementation"
    assert report["codex_workorder_runner_completed"] is False
    assert report["blocked_reasons"] == [
        "codex_workorder_runner_not_completed:completed:blocked_regeneration_failed"
    ]


def test_postclose_done_controller_runs_codex_runner_recovery_until_two_pass_completed(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        _pass_verification(),
    )
    runner_path = (
        report_dir / "codex_workorder_runner" / "codex_workorder_runner_2026-06-03.json"
    )
    _write_json(
        runner_path,
        {
            "status": "blocked_regeneration_failed",
            "two_pass_status": "blocked_regeneration_failed",
        },
    )
    calls = []

    def fake_runner(cmd, env=None):
        calls.append(cmd)
        if "codex_workorder_runner" in " ".join(cmd):
            _write_json(
                runner_path,
                {"status": "completed", "two_pass_status": "pass2_completed"},
            )
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=2,
        require_codex_completed=True,
        command_runner=fake_runner,
    )

    assert report["status"] == "done"
    assert report["codex_workorder_runner_completed"] is True
    assert any("codex_workorder_runner" in " ".join(cmd) for cmd in calls)


def test_postclose_done_controller_blocks_done_marker_with_unknown_warning(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "handoff_warnings": ["source_generation_needs_review"],
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
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


def test_postclose_done_controller_allows_real_sample_unused_followup_warning(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "warning",
            "latest_done_marker": "[DONE] threshold-cycle postclose target_date=2026-06-03",
            "handoff_warnings": [
                "real_sample_unused_by_postclose_decision",
                "active_sim_priority_preopen_handoff_pending",
            ],
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-06-03.json",
        {"generation_id": "g1"},
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        allow_wrapper_rerun=True,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "done"
    assert report["final_verifier_status"] == "warning"
    assert report["blocked_reasons"] == []
    assert report["actions"] == []


def test_postclose_done_controller_blocks_non_recoverable(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "fail",
            "missing_downstream_links": ["provider_route_change_required"],
        },
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_non_recoverable"
    assert report["actions"] == []


def test_postclose_done_controller_classifies_structural_source_quality_gap(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "fail",
            "source_quality_hard_block": {
                "status": "pass",
                "hard_blocking_contract_gap_count": 1,
                "hard_blocking_stages": ["partial_fill_reconciled"],
            },
        },
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_structural_contract_gap"
    assert report["requires_code_fix"] is True
    assert report["requires_policy_lineage_fix"] is False
    assert report["structural_blockers"] == [
        "requires_code_fix:source_quality_hard_contract_gap"
    ]
    assert report["structural_next_actions"] == [
        "fix_source_quality_metric_contract_and_rerun_postclose_audit"
    ]
    md_path = (
        report_dir
        / "postclose_done_controller"
        / "postclose_done_controller_2026-06-03.md"
    )
    assert "Structural Blockers" in md_path.read_text(encoding="utf-8")


def test_postclose_done_controller_classifies_active_priority_lineage_gap(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        {
            "status": "fail",
            "active_sim_priority_handoff": {
                "status": "fail",
                "missing": ["active_sim_priority_inactive_key_consumed"],
                "inactive_consumed_ids": ["active_seed_old"],
            },
            "predecessor_integrity": {
                "log_issues": ["active_sim_priority_handoff_missing"]
            },
        },
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_structural_contract_gap"
    assert report["requires_code_fix"] is False
    assert report["requires_policy_lineage_fix"] is True
    assert (
        "requires_policy_lineage_fix:active_sim_priority_inactive_key_consumed"
        in report["structural_blockers"]
    )
    assert (
        "requires_policy_lineage_fix:active_sim_priority_handoff_missing"
        in report["structural_blockers"]
    )
    assert report["structural_next_actions"] == [
        "fix_active_sim_priority_seed_lineage_and_verify_no_inactive_runtime_key"
    ]


def test_postclose_done_controller_waits_for_running_predecessor_without_spending_recovery_attempts(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    status_path = (
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json"
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(status_path, {"status": "running"})
    _write_json(verification, _pass_verification())
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
    assert [item["verifier_status"] for item in report["attempts"]] == [
        "predecessor_running",
        "pass",
    ]


def test_postclose_done_controller_waits_for_missing_predecessor_status_without_spending_recovery_attempts(
    monkeypatch,
    tmp_path,
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    status_path = (
        report_dir
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-06-03.status.json"
    )
    verification = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    _write_json(verification, _pass_verification())
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
    assert [item["verifier_status"] for item in report["attempts"]] == [
        "predecessor_status_missing",
        "pass",
    ]
