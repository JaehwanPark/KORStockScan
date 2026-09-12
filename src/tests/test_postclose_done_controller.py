import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.engine.automation import postclose_done_controller as mod


def test_summary_only_recovery_does_not_regenerate_ev_or_runtime(monkeypatch):
    monkeypatch.setattr(mod, "_latest_failed_tail_stage", lambda target: None)
    verification = {
        "status": "fail",
        "missing_downstream_links": [
            "postclose_summary_handoff:tower:source_generation_mismatch"
        ],
        "execution_profile": {
            "flags": {
                "tuning_performance_control_tower": True,
                "next_stage2_checklist": True,
            }
        },
    }
    actions = mod._recovery_actions(
        "2026-09-07", verification, allow_wrapper_rerun=False
    )
    assert [a.action for a in actions] == [
        "verify_pre_summary_chain",
        "refresh_tuning_performance_control_tower",
        "refresh_next_stage2_checklist",
        "verify_postclose_chain",
    ]
    assert "--require-summary-handoff" not in actions[0].command
    assert "--allow-pending-done-marker" not in actions[0].command
    assert "--require-summary-handoff" in actions[-1].command
    assert (
        "--require-summary-handoff"
        in mod._build_verify_action("2026-09-07", verification).command
    )


def test_checklist_only_recovery_does_not_rewrite_tower(monkeypatch):
    monkeypatch.setattr(mod, "_latest_failed_tail_stage", lambda target: None)
    verification = {
        "missing_downstream_links": [
            "postclose_summary_handoff:checklist:source_generation_mismatch"
        ]
    }
    actions = mod._recovery_actions(
        "2026-09-07", verification, allow_wrapper_rerun=False
    )
    assert [a.action for a in actions] == [
        "refresh_next_stage2_checklist",
        "verify_postclose_chain",
    ]


def test_failed_verifier_cannot_reuse_previous_success(monkeypatch, tmp_path):
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
    report = mod.build_postclose_done_controller(
        "2026-06-03", command_runner=lambda cmd, env=None: 7
    )
    assert report["status"] != "done"
    assert report["blocked_reasons"] == [
        "verifier_command_failed_with_success_artifact:7"
    ]
    assert report["actions"] == []


def test_summary_recovery_closes_strictly_within_last_attempt(monkeypatch, tmp_path):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    path = (
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json"
    )
    strict_calls = []

    def runner(cmd, env=None):
        if "src.engine.verify_threshold_cycle_postclose_chain" in cmd:
            if "--require-summary-handoff" in cmd:
                strict_calls.append(cmd)
                if len(strict_calls) == 1:
                    _write_json(
                        path,
                        {
                            "status": "fail",
                            "missing_downstream_links": [
                                "postclose_summary_handoff:tower:source_generation_mismatch"
                            ],
                        },
                    )
                    return 2
            _write_json(path, _pass_verification())
        return 0

    report = mod.build_postclose_done_controller(
        "2026-06-03", max_attempts=1, command_runner=runner, summary_handoff_only=True
    )
    assert report["status"] == "done"
    assert len(strict_calls) == 2
    assert report["actions"][-1]["action"] == "verify_postclose_chain"
    assert report["summary_handoff_only"] is True


@pytest.mark.parametrize("flag", ["allow_wrapper_rerun", "require_codex_completed"])
def test_summary_only_mode_cannot_gain_execution_authority(flag):
    with pytest.raises(ValueError, match="forbids_wrapper_and_codex"):
        mod.build_postclose_done_controller(
            "2026-09-09", summary_handoff_only=True, **{flag: True}
        )


def test_summary_only_mode_rejects_upstream_repairs_before_running_any(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-03.json",
        {"status": "fail", "missing_downstream_links": ["upstream_missing"]},
    )
    monkeypatch.setattr(
        mod,
        "_recovery_actions",
        lambda *args, **kwargs: [
            mod.RecoveryAction(
                "refresh_next_stage2_checklist", ["allowed_but_incomplete"], "fixture"
            ),
            mod.RecoveryAction(
                "refresh_code_improvement_workorder_final", ["forbidden"], "fixture"
            ),
        ],
    )
    calls = []

    def runner(cmd, env=None):
        calls.append(cmd)
        return 2

    result = mod.build_postclose_done_controller(
        "2026-06-03", command_runner=runner, summary_handoff_only=True
    )
    assert result["status"] != "done"
    assert result["blocked_reasons"] == [
        "summary_handoff_only_requires_upstream_repair"
    ]
    assert len(calls) == 1  # Initial strict verifier only; no partial recovery.


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _entry_setup_followup_state(project_dir, target_date):
    script_path = Path(__file__).resolve().parents[2] / "deploy/run_postclose_done_controller.sh"
    script = script_path.read_text(encoding="utf-8")
    function_start = script.index("entry_setup_replay_followup_state() {")
    python_start = script.index("import hashlib", function_start)
    python_end = script.index("\nPY\n}", python_start)
    inline_validator = script[python_start:python_end]
    batch_path = (
        project_dir
        / "data/report/ai_entry_setup_paired_replay_batch"
        / f"ai_entry_setup_paired_replay_batch_{target_date}.json"
    )
    result = subprocess.run(
        [sys.executable, "-", str(project_dir), target_date, str(batch_path)],
        input=inline_validator,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _write_entry_setup_followup_consumer(project_dir, target_date):
    consumer = {
        "schema": "main_ai_prompt_consumer_v1",
        "target_date": target_date,
        "status": "ready_source_only_consumer_closure",
        "unclassified_request_path_count": 0,
        "terminal_request_path_contract_invalid_count": 0,
        "entry_followup_terminal_ready": True,
        "runtime_effect": False,
        "runtime_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "performance_evidence": {"runtime_prompt_update_allowed": False},
        "request_paths": {
            "entry_base": {"path_status": "connected_and_hash_bound", "cohorts": []},
            "holding_base": {"path_status": "connected_and_hash_bound", "cohorts": []},
            "optional_micro_enriched_2x2": {
                "path_status": "connected_and_hash_bound",
                "cells": [],
            },
        },
    }
    consumer["artifact_content_sha256"] = hashlib.sha256(
        json.dumps(
            consumer,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    _write_json(
        project_dir
        / "data/report/main_ai_prompt_consumer"
        / f"main_ai_prompt_consumer_{target_date}.json",
        consumer,
    )


def _entry_replay_cohort(key, version, venue, session, route, authority, **extra):
    return {
        "cohort_key": key,
        "cohort_key_version": version,
        "effective_venue": venue,
        "session_bucket": session,
        "market_data_route": route,
        "authority_state": authority,
        **extra,
    }


def _write_entry_setup_followup_batch(project_dir, target_date, payload):
    _write_json(
        project_dir
        / "data/report/ai_entry_setup_paired_replay_batch"
        / f"ai_entry_setup_paired_replay_batch_{target_date}.json",
        payload,
    )


def test_entry_setup_followup_accepts_legacy_batch_without_versioned_contract(tmp_path):
    target_date = "2026-09-12"
    _write_entry_setup_followup_consumer(tmp_path, target_date)
    nxt_path = (
        tmp_path
        / "data/threshold_cycle/bounded_live_candidates"
        / f"entry_setup_v2_14_bounded_live_candidate_{target_date}_nxt_nxt_aftermarket.json"
    )
    nxt = {
        "source_date": target_date,
        "effective_venue": "NXT",
        "session_bucket": "NXT_AFTERMARKET",
        "status": "blocked",
        "effective_date": "2026-09-15",
        "effective_date_policy": "first_available_krx_preopen_v1",
        "preopen_candidate_cutoff_kst": "07:35:00",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    nxt["artifact_sha256"] = hashlib.sha256(
        json.dumps(
            nxt,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    _write_json(nxt_path, nxt)
    _write_entry_setup_followup_batch(
        tmp_path,
        target_date,
        {
            "target_date": target_date,
            "status": "completed_offline_only",
            "cohorts": [],
            "bounded_live_cohort_contract": "exact_cohort_candidates_v1",
            "bounded_live_candidates_by_cohort": {
                "KRX/KRX_REGULAR": None,
                "NXT/NXT_AFTERMARKET": {
                    "path": str(nxt_path.relative_to(tmp_path)),
                    "artifact_sha256": nxt["artifact_sha256"],
                    "artifact_status": "blocked",
                    "effective_date": nxt["effective_date"],
                    "allowed_runtime_apply": False,
                },
            },
            "krx_bounded_live_candidate": None,
        },
    )

    assert _entry_setup_followup_state(tmp_path, target_date) == (
        "terminal_ready:validated_batch_and_main_ai_consumer_no_krx_candidate"
    )


def test_entry_setup_followup_accepts_versioned_dual_aftermarket_observe_only(tmp_path):
    target_date = "2026-09-12"
    _write_entry_setup_followup_consumer(tmp_path, target_date)
    expected = [
        _entry_replay_cohort(
            "KRX/KRX_REGULAR", "v1", "KRX", "KRX_REGULAR", "KRX", "SOURCE_ONLY"
        ),
        _entry_replay_cohort(
            "NXT/NXT_AFTERMARKET",
            "v1",
            "NXT",
            "NXT_AFTERMARKET",
            "NXT",
            "SOURCE_ONLY",
        ),
        _entry_replay_cohort(
            "INTEGRATED/KRX_NXT_AFTERMARKET",
            "v2",
            "INTEGRATED",
            "KRX_NXT_AFTERMARKET",
            "SOR",
            "OBSERVE_ONLY",
        ),
    ]
    cohorts = [
        {**expected[0], "status": "completed_offline_only"},
        {**expected[1], "status": "completed_offline_only"},
        {
            **expected[2],
            "status": "completed_observe_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "candidate_contract_sha256": None,
        },
    ]
    _write_entry_setup_followup_batch(
        tmp_path,
        target_date,
        {
            "target_date": target_date,
            "status": "completed_offline_only",
            "cohort_contract": {
                "schema": "entry_replay_cohort_contract_v1",
                "contract_version": "v2",
                "expected_cohorts_by_contract_version": {"v2": expected},
            },
            "cohorts": cohorts,
            "krx_bounded_live_candidate": None,
        },
    )

    assert _entry_setup_followup_state(tmp_path, target_date) == (
        "terminal_ready:validated_batch_and_main_ai_consumer_no_krx_candidate"
    )


def test_entry_setup_followup_rejects_dual_aftermarket_live_authority(tmp_path):
    target_date = "2026-09-12"
    _write_entry_setup_followup_consumer(tmp_path, target_date)
    dual = _entry_replay_cohort(
        "INTEGRATED/KRX_NXT_AFTERMARKET",
        "v2",
        "INTEGRATED",
        "KRX_NXT_AFTERMARKET",
        "SOR",
        "LIVE_APPROVED",
    )
    _write_entry_setup_followup_batch(
        tmp_path,
        target_date,
        {
            "target_date": target_date,
            "status": "completed_offline_only",
            "cohort_contract": {
                "schema": "entry_replay_cohort_contract_v1",
                "contract_version": "v2",
                "expected_cohorts_by_contract_version": {"v2": [dual]},
            },
            "cohorts": [
                {
                    **dual,
                    "status": "completed_observe_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "candidate_contract_sha256": None,
                }
            ],
            "krx_bounded_live_candidate": None,
        },
    )

    assert _entry_setup_followup_state(tmp_path, target_date) == (
        "retry_required:dual_aftermarket_live_authority_forbidden"
    )


def test_entry_setup_followup_rejects_nxt_candidate_hash_reused_for_dual_aftermarket(tmp_path):
    target_date = "2026-09-12"
    _write_entry_setup_followup_consumer(tmp_path, target_date)
    dual = _entry_replay_cohort(
        "INTEGRATED/KRX_NXT_AFTERMARKET",
        "v2",
        "INTEGRATED",
        "KRX_NXT_AFTERMARKET",
        "SOR",
        "OBSERVE_ONLY",
    )
    _write_entry_setup_followup_batch(
        tmp_path,
        target_date,
        {
            "target_date": target_date,
            "status": "completed_offline_only",
            "cohort_contract": {
                "schema": "entry_replay_cohort_contract_v1",
                "contract_version": "v2",
                "expected_cohorts_by_contract_version": {"v2": [dual]},
            },
            "cohorts": [
                {
                    **dual,
                    "status": "completed_observe_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "candidate_contract_sha256": "a" * 64,
                }
            ],
            "krx_bounded_live_candidate": None,
        },
    )

    assert _entry_setup_followup_state(tmp_path, target_date) == (
        "retry_required:dual_aftermarket_live_candidate_forbidden"
    )


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
    assert (
        action_names.index("refresh_threshold_cycle_ev")
        < action_names.index("refresh_code_improvement_workorder")
        < action_names.index("refresh_runtime_approval_summary")
    )


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


def test_tail_repair_refreshes_only_hash_stale_machine_sources_before_consumers():
    verification = {
        "samsung_machine_entry_postclose": {
            "issues": ["tuning_source_quality_hash_mismatch"]
        },
        "low_price_two_leg_postclose": {
            "issues": ["policy_candidate_candidate_source_quality_hash_mismatch"]
        },
    }
    actions = mod._tail_stage_repair_actions(
        "2026-09-08", "verify_threshold_cycle_postclose_chain", verification
    )
    names = [a.action for a in actions]
    assert names[:2] == [
        "refresh_samsung_machine_entry_tuning",
        "refresh_low_price_two_leg_tuning",
    ]
    assert names.index("refresh_low_price_two_leg_tuning") < names.index(
        "refresh_code_improvement_workorder"
    )
    for action in actions[:2]:
        assert action.command[-3:] == ["--target-date", "2026-09-08", "--print-summary"]
        assert "--auto-apply" not in action.command
    assert not any(
        "expanded_candidate_research" in " ".join(a.command or []) for a in actions
    )
    verification["samsung_machine_entry_postclose"]["issues"] = []
    verification["low_price_two_leg_postclose"]["issues"] = ["unrelated_contract_gap"]
    actions = mod._tail_stage_repair_actions(
        "2026-09-08", "verify_threshold_cycle_postclose_chain", verification
    )
    assert not any(a.action in names[:2] for a in actions)


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
    monkeypatch.setattr(mod, "POSTCLOSE_LOG_PATH", tmp_path / "postclose.log")
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
            _write_json(
                verification,
                {
                    **_pass_verification(),
                    "artifact_status": _passable_artifact_status(),
                },
            )
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


def test_postclose_done_controller_does_not_hide_machine_structural_shortage(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = _pass_verification()
    verification["machine_entry_timing_postclose"] = {
        "status": "pass",
        "waiting_resolution_status": "requires_structural_repair",
        "shortage_id": (
            "machine_entry_timing:all_exact_scopes:entry_confirmation_delay"
        ),
        "shortage_next_action": "repair_exact_entry_anchor_market_join_and_rerun",
    }
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        verification,
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "blocked_structural_contract_gap"
    assert report["final_verifier_status"] == "pass"
    assert report["structural_blockers"] == [
        "requires_code_fix:machine_entry_timing:all_exact_scopes:"
        "entry_confirmation_delay"
    ]
    assert report["structural_next_actions"] == [
        "repair_exact_entry_anchor_market_join_and_rerun"
    ]
    assert report["requires_code_fix"] is True


def test_machine_structural_action_preserves_allowlisted_repair_action():
    actions = mod._structural_next_actions(
        [
            "requires_code_fix:machine_entry_timing:all_exact_scopes:"
            "entry_confirmation_delay"
        ],
        {
            "machine_entry_timing_postclose": {
                "shortage_next_action": (
                    "repair_exact_entry_anchor_market_join_and_rerun"
                )
            }
        },
    )

    assert actions == ["repair_exact_entry_anchor_market_join_and_rerun"]


def test_postclose_done_controller_closes_immutable_receipt_quarantine(
    monkeypatch, tmp_path
):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report_dir / "postclose_done_controller")
    _write_succeeded_status(report_dir)
    verification = _pass_verification()
    verification["machine_entry_timing_postclose"] = {
        "status": "pass",
        "waiting_resolution_status": "terminal_source_date_quarantine",
        "source_date_quarantined": True,
        "shortage_id": (
            "machine_entry_timing:all_exact_scopes:entry_confirmation_delay"
        ),
        "shortage_next_action": (
            "quarantine_exact_source_date_and_verify_next_runtime_receipt"
        ),
    }
    _write_json(
        report_dir
        / "threshold_cycle_postclose_verification"
        / "threshold_cycle_postclose_verification_2026-06-03.json",
        verification,
    )

    report = mod.build_postclose_done_controller(
        "2026-06-03",
        max_attempts=1,
        command_runner=lambda cmd, env=None: 0,
    )

    assert report["status"] == "done"
    assert report["structural_blockers"] == []
    assert report["requires_code_fix"] is False
    assert report["machine_entry_timing_source_date_quarantined"] is True
    assert report["machine_entry_timing_quarantine_next_action"] == (
        "quarantine_exact_source_date_and_verify_next_runtime_receipt"
    )
    assert report["root_cause"] == (
        "machine_entry_timing_exact_source_date_quarantined"
    )


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


def _diagnostic_warning_verification():
    return {
        "status": "warning",
        "missing_required_artifacts": [],
        "artifact_status": _passable_artifact_status(),
        "predecessor_integrity": {"log_issues": ["postclose_fail_marker_present"]},
        "handoff_warnings": ["microstructure_diagnostic:warning"],
        "microstructure_diagnostic_handoff": {
            "status": "warning",
            "issues": [],
            "expected_order_ids": ["native-order"],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "conversion_kpi": {
            "status": "warning",
            "issues": [],
            "warnings": ["conversion_lane_no_candidates"],
            "conversion_lane_summary": {
                "conversion_candidate_count": 0,
                "buy_funnel_source_present": True,
                "key_lineage_blocker_count": 0,
            },
        },
    }


def test_verified_diagnostic_warning_and_empty_conversion_can_close_tail(monkeypatch):
    verification = _diagnostic_warning_verification()
    assert mod._can_finalize_tail_repair(verification) is True
    monkeypatch.setattr(mod, "_postclose_status_succeeded", lambda _: True)
    verification["latest_done_marker"] = (
        "[DONE] threshold-cycle postclose target_date=2026-09-07"
    )
    verification["predecessor_integrity"]["log_issues"] = []
    assert (
        mod._is_done_verifier_status(
            "2026-09-07", verification, mod._flatten_issues(verification)
        )
        is True
    )


def test_diagnostic_warning_without_verified_non_authority_handoff_stays_blocked():
    for field, value in [
        ("issues", ["missing_order"]),
        ("runtime_effect", True),
        ("allowed_runtime_apply", True),
        ("expected_order_ids", []),
    ]:
        verification = _diagnostic_warning_verification()
        verification["microstructure_diagnostic_handoff"][field] = value
        assert mod._can_finalize_tail_repair(verification) is False
    verification = _diagnostic_warning_verification()
    del verification["microstructure_diagnostic_handoff"]
    assert mod._can_finalize_tail_repair(verification) is False


def test_empty_conversion_warning_does_not_mask_missing_source_or_lineage_gap():
    for field, value in [
        ("conversion_candidate_count", 1),
        ("conversion_candidate_count", False),
        ("buy_funnel_source_present", False),
        ("key_lineage_blocker_count", 1),
    ]:
        verification = _diagnostic_warning_verification()
        verification["conversion_kpi"]["conversion_lane_summary"][field] = value
        assert mod._can_finalize_tail_repair(verification) is False
    verification = _diagnostic_warning_verification()
    verification["conversion_kpi"]["issues"] = ["source_contract_missing"]
    assert mod._can_finalize_tail_repair(verification) is False
