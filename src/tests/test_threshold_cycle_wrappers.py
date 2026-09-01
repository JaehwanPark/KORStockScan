import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


def test_postclose_wrapper_executes_syntax_checked_immutable_snapshot():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert "THRESHOLD_CYCLE_WRAPPER_SNAPSHOT_EXECUTED" in script
    assert 'mktemp "$SCRIPT_DIR/.run_threshold_cycle_postclose.snapshot.' in script
    assert 'cp -- "${BASH_SOURCE[0]}" "$wrapper_snapshot"' in script
    assert 'bash -n "$wrapper_snapshot"' in script
    assert 'exec bash "$wrapper_snapshot" "$@"' in script
    assert 'export THRESHOLD_CYCLE_WRAPPER_SNAPSHOT_PATH="$wrapper_snapshot"' in script
    assert "trap cleanup_wrapper_snapshot EXIT" in script
    assert "terminate_wrapper_children" in script
    assert "trap 'handle_wrapper_signal HUP' HUP" in script
    assert "trap 'handle_wrapper_signal INT' INT" in script
    assert "trap 'handle_wrapper_signal TERM' TERM" in script
    assert 'mark_postclose_failed "$reason" "$exit_code"' in script
    assert 'rm -f -- "$wrapper_snapshot"' in script


def test_postclose_wrapper_syncs_exact_trade_facts_before_daily_calibration():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    sync_idx = script.index("src.engine.strategy_position_performance_report")
    calibration_idx = script.index("src.engine.daily_threshold_cycle_report", sync_idx)
    ev_idx = script.index(
        'run_threshold_cycle_ev_and_wait "pre_workorder"', calibration_idx
    )

    assert sync_idx < calibration_idx < ev_idx
    sync_block = script[
        script.rindex(
            'if [ "$SKIP_DB" != "true" ]; then', 0, sync_idx
        ) : calibration_idx
    ]
    assert "reason=skip_db" in sync_block
    assert "src.engine.strategy_position_performance_report" in sync_block


def test_postclose_wrapper_snapshot_is_removed_when_child_fails(tmp_path):
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    preamble = script[: script.index('PROJECT_DIR="${PROJECT_DIR:-')]
    wrapper = tmp_path / "run_threshold_cycle_postclose.sh"
    wrapper.write_text(preamble + "\nexit 9\n", encoding="utf-8")
    wrapper.chmod(0o700)

    result = subprocess.run(
        ["bash", str(wrapper)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 9
    assert list(tmp_path.glob(".run_threshold_cycle_postclose.snapshot.*.sh")) == []


def test_postclose_wrapper_snapshot_exec_keeps_one_pid_and_cleans_on_term(tmp_path):
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    preamble = script[: script.index('PROJECT_DIR="${PROJECT_DIR:-')]
    wrapper = tmp_path / "run_threshold_cycle_postclose.sh"
    pid_path = tmp_path / "executed.pid"
    child_pid_path = tmp_path / "child.pid"
    wrapper.write_text(
        preamble
        + f'\nprintf "%s" "$$" > "{pid_path}"\n'
        + "( trap 'exit 0' TERM; while :; do :; done ) &\n"
        + f'child_pid=$!\nprintf "%s" "$child_pid" > "{child_pid_path}"\n'
        + 'wait "$child_pid"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o700)

    process = subprocess.Popen(
        ["bash", str(wrapper)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "THRESHOLD_CYCLE_SIGNAL_GRACE_SEC": "1"},
    )
    try:
        for _attempt in range(200):
            if pid_path.exists() and child_pid_path.exists():
                break
            time.sleep(0.01)
        assert pid_path.exists()
        assert child_pid_path.exists()
        assert int(pid_path.read_text(encoding="utf-8")) == process.pid
        child_pid = int(child_pid_path.read_text(encoding="utf-8"))
        process.terminate()
        assert process.wait(timeout=5) == 143
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    assert list(tmp_path.glob(".run_threshold_cycle_postclose.snapshot.*.sh")) == []


@pytest.mark.parametrize(
    ("signal_number", "expected_return_code", "expected_reason"),
    [
        (signal.SIGHUP, 129, "hangup"),
        (signal.SIGINT, 130, "interrupted"),
        (signal.SIGTERM, 143, "terminated"),
    ],
)
def test_postclose_wrapper_terminates_foreground_process_group_on_signal(
    tmp_path, signal_number, expected_return_code, expected_reason
):
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    preamble = script[: script.index('PROJECT_DIR="${PROJECT_DIR:-')]
    function_start = script.index("run_postclose_cmd() {")
    function_end = script.index("\n}\n", function_start) + 3
    run_function = script[function_start:function_end]
    child_pid_path = tmp_path / "foreground.pid"
    grandchild_pid_path = tmp_path / "grandchild.pid"
    failure_marker_path = tmp_path / "failure-marker"
    restart_marker_path = tmp_path / "restart-marker"
    child_script = tmp_path / "ignore-signals.sh"
    child_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "trap '' HUP INT TERM",
                f'printf "%s" "$$" > "{child_pid_path}"',
                "( trap '' HUP INT TERM; while :; do :; done ) &",
                "grandchild_pid=$!",
                f'printf "%s" "$grandchild_pid" > "{grandchild_pid_path}"',
                'wait "$grandchild_pid"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    child_script.chmod(0o700)
    wrapper = tmp_path / "run_threshold_cycle_postclose.sh"
    wrapper.write_text(
        preamble
        + "\nPOSTCLOSE_NICE_LEVEL=0\n"
        + "POSTCLOSE_IONICE_CLASS=-1\n"
        + 'POSTCLOSE_IONICE_LEVEL=0\nPOSTCLOSE_CPU_AFFINITY=""\n'
        + f'VENV_PY="{sys.executable}"\n'
        + f'mark_postclose_failed() {{ printf "%s:%s" "$1" "$2" > "{failure_marker_path}"; }}\n'
        + f'restart_postclose_bot_if_requested() {{ : > "{restart_marker_path}"; }}\n'
        + "POSTCLOSE_OPERATING=true\n"
        + run_function
        + f'\nrun_postclose_cmd bash "{child_script}"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o700)

    process = subprocess.Popen(
        ["bash", str(wrapper)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "THRESHOLD_CYCLE_SIGNAL_GRACE_SEC": "1"},
    )
    try:
        for _attempt in range(300):
            if child_pid_path.exists() and grandchild_pid_path.exists():
                break
            time.sleep(0.01)
        assert child_pid_path.exists()
        assert grandchild_pid_path.exists()
        child_pid = int(child_pid_path.read_text(encoding="utf-8"))
        grandchild_pid = int(grandchild_pid_path.read_text(encoding="utf-8"))
        process.send_signal(signal_number)
        assert process.wait(timeout=5) == expected_return_code
        assert failure_marker_path.read_text(encoding="utf-8") == (
            f"{expected_reason}:{expected_return_code}"
        )
        assert restart_marker_path.exists()
        for terminated_pid in (child_pid, grandchild_pid):
            for _attempt in range(200):
                try:
                    os.kill(terminated_pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.01)
            else:
                pytest.fail(f"signalled descendant still alive: {terminated_pid}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    assert list(tmp_path.glob(".run_threshold_cycle_postclose.snapshot.*.sh")) == []


def test_postclose_group_runner_accepts_fast_success_and_fails_closed_without_setsid(
    tmp_path,
):
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    function_start = script.index("run_postclose_cmd() {")
    function_end = script.index("\n}\n", function_start) + 3
    run_function = script[function_start:function_end]
    common = (
        "POSTCLOSE_NICE_LEVEL=0\n"
        "POSTCLOSE_IONICE_CLASS=-1\n"
        "POSTCLOSE_IONICE_LEVEL=0\n"
        'POSTCLOSE_CPU_AFFINITY=""\n'
        f'VENV_PY="{sys.executable}"\n'
        "POSTCLOSE_GROUP_STARTING=false\n"
        'POSTCLOSE_PENDING_SIGNAL=""\n'
        'ACTIVE_POSTCLOSE_PID=""\n'
        'ACTIVE_POSTCLOSE_PGID=""\n'
    )
    fast_wrapper = tmp_path / "fast-command.sh"
    fast_wrapper.write_text(
        "#!/usr/bin/env bash\nset -Eeuo pipefail\n"
        + common
        + run_function
        + "\nfor _attempt in {1..20}; do run_postclose_cmd true; done\n"
        + "run_postclose_cmd bash -c "
        + "'IFS= read -r value; [ \"$value\" = payload ]' <<< payload\n",
        encoding="utf-8",
    )
    fast_result = subprocess.run(
        ["/bin/bash", str(fast_wrapper)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert fast_result.returncode == 0, fast_result.stderr

    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()
    no_setsid_wrapper = tmp_path / "no-setsid.sh"
    no_setsid_wrapper.write_text(
        "#!/usr/bin/env bash\nset -u\n"
        + common
        + run_function
        + "\nrun_postclose_cmd true\n",
        encoding="utf-8",
    )
    no_setsid_result = subprocess.run(
        ["/bin/bash", str(no_setsid_wrapper)],
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PATH": str(empty_path)},
    )
    assert no_setsid_result.returncode == 127
    assert "process-group isolation unavailable" in no_setsid_result.stderr


@pytest.mark.parametrize(
    ("signal_number", "expected_return_code"),
    [(signal.SIGHUP, 129), (signal.SIGINT, 130), (signal.SIGTERM, 143)],
)
def test_postclose_signal_during_group_startup_is_delivered_after_verification(
    tmp_path, signal_number, expected_return_code
):
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    preamble = script[: script.index('PROJECT_DIR="${PROJECT_DIR:-')]
    function_start = script.index("run_postclose_cmd() {")
    function_end = script.index("\n}\n", function_start) + 3
    run_function = script[function_start:function_end]
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ps_started = tmp_path / "ps-started"
    fake_ps = fake_bin / "ps"
    fake_ps.write_text(
        "#!/usr/bin/env bash\n"
        + f': > "{ps_started}"\n'
        + 'sleep 0.4\nexec /usr/bin/ps "$@"\n',
        encoding="utf-8",
    )
    fake_ps.chmod(0o700)
    child_started = tmp_path / "child-started"
    child_script = tmp_path / "child.sh"
    child_script.write_text(
        "#!/usr/bin/env bash\n" + f': > "{child_started}"\n' + "while :; do :; done\n",
        encoding="utf-8",
    )
    child_script.chmod(0o700)
    wrapper = tmp_path / "startup-signal.sh"
    wrapper.write_text(
        preamble
        + "\nPOSTCLOSE_NICE_LEVEL=0\nPOSTCLOSE_IONICE_CLASS=-1\n"
        + 'POSTCLOSE_IONICE_LEVEL=0\nPOSTCLOSE_CPU_AFFINITY=""\n'
        + f'VENV_PY="{sys.executable}"\n'
        + run_function
        + f'\nrun_postclose_cmd bash "{child_script}"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o700)

    process = subprocess.Popen(
        ["bash", str(wrapper)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            **os.environ,
            "PATH": f"{fake_bin}:{os.environ['PATH']}",
            "THRESHOLD_CYCLE_SIGNAL_GRACE_SEC": "1",
        },
    )
    try:
        for _attempt in range(200):
            if ps_started.exists():
                break
            time.sleep(0.01)
        assert ps_started.exists()
        process.send_signal(signal_number)
        assert process.wait(timeout=5) == expected_return_code
        assert not child_started.exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_postclose_long_commands_are_not_run_inside_command_substitutions():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" '
        "-m src.engine.backfill_threshold_cycle_events" in script
    )
    assert '> "$BACKFILL_OUTPUT_TEMP"' in script
    assert 'out="$(\n    run_postclose_cmd' not in script
    assert "$(automation_trigger_decision" not in script
    assert "AUTOMATION_TRIGGER_DECISION_RESULT" in script
    assert 'pgrep -P "$$"' not in script


@pytest.mark.parametrize(
    ("exit_mode", "expected_rc"),
    [("normal", 0), ("failure", 7), ("signal", 143)],
)
def test_postclose_per_run_trigger_cache_is_removed_on_exit(
    tmp_path, exit_mode, expected_rc
):
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    function_start = script.index("cleanup_threshold_cycle_snapshot_temp() {")
    function_end = script.index("\n}\n", function_start) + 3
    cleanup_function = script[function_start:function_end]
    marker = tmp_path / "automation-trigger.cached"
    marker.write_text("", encoding="utf-8")
    wrapper = tmp_path / "cleanup-trigger-cache.sh"
    wrapper.write_text(
        "#!/usr/bin/env bash\nset -Eeuo pipefail\n"
        + 'SNAPSHOT_TEMP_PATH=""\nBACKFILL_OUTPUT_TEMP=""\n'
        + 'AUTOMATION_TRIGGER_DECISION_OUTPUT_TEMP=""\n'
        + f'AUTOMATION_TRIGGER_DECISION_CACHE_MARKER="{marker}"\n'
        + "cleanup_wrapper_snapshot() { :; }\n"
        + cleanup_function
        + "\ntrap cleanup_threshold_cycle_snapshot_temp EXIT\n"
        + (
            "exit 0\n"
            if exit_mode == "normal"
            else (
                "trap 'exit 143' TERM\nkill -TERM \"$$\"\n"
                if exit_mode == "signal"
                else "exit 7\n"
            )
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["/bin/bash", str(wrapper)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == expected_rc
    assert not marker.exists()


def test_postclose_daily_ev_receives_disabled_report_scope():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert 'EV_SCOPE_ARGS=("${POSTCLOSE_SWING_SCOPE_ARGS[@]}")' in script
    assert "--disabled-source codebase_performance_workorder" in script
    assert "--disabled-source time_window_regime_counterfactual" in script
    assert "--disabled-source producer_gap_discovery" in script
    assert "--disabled-source stage_hook_workorder_discovery" in script
    assert "--disabled-source stage_hook_runtime_scaffold" in script
    assert '--date "$TARGET_DATE" "${EV_SCOPE_ARGS[@]}"' in script


def test_postclose_large_reports_use_compact_stdout_and_verified_refresh():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'src.engine.scalp_entry_action_decision_matrix --date "$TARGET_DATE" --print-summary'
        in script
    )
    assert (
        'src.engine.lifecycle_bucket_discovery --date "$TARGET_DATE" --print-summary'
        in script
    )
    assert (
        'src.engine.latency_classifier_recommendation "${latency_args[@]}" --print-summary'
        in script
    )
    assert "pipeline_verbosity_inputs=(" in script
    assert '"$PROJECT_DIR/src/engine/pipeline_event_summary.py"' in script
    assert '"$PROJECT_DIR/src/engine/pipeline_event_verbosity_report.py"' in script
    assert 'json_is_valid "$pipeline_verbosity_json"' in script
    assert (
        'skip_triggered_step "pipeline_event_verbosity" "verified_artifacts_fresher_than_inputs"'
        in script
    )


def test_postclose_trigger_decision_respects_disabled_runtime_policy():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT="${RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT:-false}"'
        in script
    )
    assert (
        'THRESHOLD_CYCLE_RUN_PRODUCER_GAP_DISCOVERY="${RUN_PRODUCER_GAP_DISCOVERY:-false}"'
        in script
    )
    assert (
        'THRESHOLD_CYCLE_RUN_STAGE_HOOK_RUNTIME_SCAFFOLD="${RUN_STAGE_HOOK_RUNTIME_SCAFFOLD:-false}"'
        in script
    )
    assert '[ "$decision" = "skip" ] || [ "$decision" = "disabled_success" ]' in script


def test_postclose_failed_run_reuses_only_valid_same_target_heavy_artifacts():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'REUSE_COMPLETED_REPORT_STEPS="${THRESHOLD_CYCLE_REUSE_COMPLETED_REPORT_STEPS:-true}"'
        in script
    )
    assert 'str(payload.get("status") or "").lower() == "failed"' in script
    assert 'str(payload.get("target_date") or "") == target_date' in script
    assert "reusable_completed_artifact()" in script
    assert "source_mtime > artifact_mtime" in script
    assert "completed_artifact_checkpoint" in script
    assert 'expected_report_type != "-"' in script
    assert "source_quality_blocked" in script
    assert "scalping_avg_down_recovery_calibration" in script
    assert "one_share_threshold_opportunity" in script
    assert "one_share_ai_review_reusable" in script
    assert 'review.get("status") == "parsed"' in script
    assert 'review.get("provider") == expected_provider' in script


def test_claude_pattern_lab_wrapper_requires_explicit_target_date():
    env = dict(os.environ)
    env.pop("ANALYSIS_START_DATE", None)
    env.pop("ANALYSIS_END_DATE", None)
    result = subprocess.run(
        ["bash", "analysis/claude_scalping_pattern_lab/run_all.sh"],
        cwd=".",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "target date is required" in result.stderr


def test_postclose_wrapper_runs_pattern_labs_before_automation_and_ev_report():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    claude_idx = script.index("analysis/claude_scalping_pattern_lab/run_all.sh")
    automation_idx = script.index("src.engine.scalping_pattern_lab_automation")
    currentness_idx = script.index("src.engine.pattern_lab_currentness_audit")
    ai_review_idx = script.index("src.engine.pattern_lab_ai_review")
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert (
        'ANALYSIS_START_DATE="$PATTERN_LAB_START_DATE" ANALYSIS_END_DATE="$TARGET_DATE"'
        in script
    )
    assert (
        'PATTERN_LAB_START_DATE="${PATTERN_LAB_ANALYSIS_START_DATE:-${KORSTOCKSCAN_CLEAN_TUNING_BASELINE_DATE:-2026-06-05}}"'
        in script
    )
    assert "analysis/gemini_scalping_pattern_lab/run.sh" not in script
    assert "retired_from_automatic_execution" in script
    assert claude_idx < automation_idx
    assert automation_idx < currentness_idx < ai_review_idx < ev_idx
    assert (
        'RUN_PATTERN_LAB_CURRENTNESS_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_CURRENTNESS_AUDIT:-true}"'
        in script
    )
    assert (
        'RUN_PATTERN_LAB_AI_REVIEW="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_AI_REVIEW:-true}"'
        in script
    )
    assert (
        'PATTERN_LAB_AI_REVIEW_PROVIDER="${KORSTOCKSCAN_PATTERN_LAB_AI_REVIEW_PROVIDER:-openai}"'
        in script
    )


def test_postclose_wrapper_runs_daily_low_price_candidate_recommendation_and_admin_notice():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION="${THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION:-true}"'
        in script
    )
    tuning_idx = script.index("-m src.engine.monitoring.low_price_two_leg_tuning")
    recommendation_idx = script.index(
        "-m src.engine.monitoring.low_price_two_leg_expanded_candidate_research"
    )
    assert tuning_idx < recommendation_idx
    assert '--target-date "$TARGET_DATE"' in script[recommendation_idx:]
    assert "--write" in script[recommendation_idx:]
    assert "--notify" in script[recommendation_idx:]
    assert (
        'wait_for_postclose_resources "low_price_two_leg_candidate_recommendation"'
        in script
    )
    assert "low_price_candidate_recommendation_reusable()" in script
    assert "CandidateRecommendationNotifier._valid_report(payload)" in script
    assert "REPORT_SCHEMA," in script
    assert 'payload.get("schema") == REPORT_SCHEMA' in script
    assert (
        '"recommendations_ready",\n        "no_qualified_candidate",\n'
        '        "partial_source_quality",\n'
        '        "source_quality_blocked",'
    ) in script
    assert (
        '"$PROJECT_DIR/src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py"'
        in script
    )
    assert (
        '&& low_price_candidate_recommendation_reusable "$candidate_recommendation_json"'
        in script
    )
    assert 'in {"sent", "duplicate", "sent_state_persist_failed"}' in script
    assert '"low_price_two_leg_candidate_recommendation"' in script
    assert (
        "low_price_two_leg_candidate_recommendation=$RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION"
        in script
    )


def test_postclose_wrapper_runs_machine_microstructure_after_dynamic_machine_reports():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION="${THRESHOLD_CYCLE_RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION:-true}"'
        in script
    )
    tuning_idx = script.index("-m src.engine.monitoring.low_price_two_leg_tuning")
    expansion_idx = script.index(
        "-m src.engine.monitoring.low_price_two_leg_expanded_candidate_research"
    )
    attribution_idx = script.index(
        "-m src.engine.monitoring.machine_microstructure_attribution"
    )
    weakness_hysteresis_idx = script.index(
        "-m src.engine.automation.market_weakness_hysteresis_tuning"
    )
    entry_timing_idx = script.index(
        "-m src.engine.automation.machine_entry_timing_tuning"
    )
    assert (
        tuning_idx
        < expansion_idx
        < attribution_idx
        < weakness_hysteresis_idx
        < entry_timing_idx
    )
    assert 'wait_for_postclose_resources "machine_microstructure_attribution"' in script
    assert "machine_microstructure_attribution_${TARGET_DATE}.json" in script
    assert (
        'RUN_MACHINE_MICROSTRUCTURE_POLICY_APPROVAL="${THRESHOLD_CYCLE_RUN_MACHINE_MICROSTRUCTURE_POLICY_APPROVAL:-true}"'
        in script
    )
    approval_idx = script.index(
        "-m src.engine.automation.machine_microstructure_policy_approval"
    )
    assert entry_timing_idx < approval_idx
    assert "--phase postclose" in script
    assert (
        "machine_microstructure_policy_approval_postclose_${TARGET_DATE}.json" in script
    )
    assert "[STATUS] machine_microstructure_policy_approval" in script
    assert "runtime_effect=false" in script
    assert (
        "machine_microstructure_attribution=$RUN_MACHINE_MICROSTRUCTURE_ATTRIBUTION"
        in script
    )

    widget_expansion_service = Path(
        "deploy/systemd/korstockscan-widget-expansion-recommendation.service"
    ).read_text(encoding="utf-8")
    assert widget_expansion_service.count("ExecStart=") == 1
    assert (
        "ExecStart=/home/ubuntu/KORStockScan/deploy/"
        "run_machine_microstructure_final_refresh.sh" in widget_expansion_service
    )
    assert "KORSTOCKSCAN_WIDGET_EXPANSION_TELEGRAM_ENABLED=true" in (
        widget_expansion_service
    )

    final_refresh = Path(
        "deploy/run_machine_microstructure_final_refresh.sh"
    ).read_text(encoding="utf-8")
    # Match the child commands, not the earlier Python import used only to
    # resolve the completed-machine target date.
    expansion_refresh_idx = final_refresh.index(
        '"$PYTHON_BIN" -m '
        "src.engine.monitoring.widget_collector_expansion_recommendation"
    )
    attribution_refresh_idx = final_refresh.index(
        '"$PYTHON_BIN" -m src.engine.monitoring.machine_microstructure_attribution'
    )
    weakness_hysteresis_refresh_idx = final_refresh.index(
        '"$PYTHON_BIN" -m src.engine.automation.market_weakness_hysteresis_tuning'
    )
    entry_timing_refresh_idx = final_refresh.index(
        '"$PYTHON_BIN" -m src.engine.automation.machine_entry_timing_tuning'
    )
    approval_refresh_idx = final_refresh.index(
        '"$PYTHON_BIN" -m src.engine.automation.machine_microstructure_policy_approval'
    )
    checklist_refresh_idx = final_refresh.index(
        '"$PYTHON_BIN" -m src.engine.build_next_stage2_checklist'
    )
    assert (
        expansion_refresh_idx
        < attribution_refresh_idx
        < weakness_hysteresis_refresh_idx
        < entry_timing_refresh_idx
        < approval_refresh_idx
        < checklist_refresh_idx
    )
    assert "--source-wait-sec 900" in final_refresh
    assert "--source-poll-sec 30" in final_refresh
    assert "--notify-objective-followups" in final_refresh
    assert "--completed-machine-source-date" in final_refresh


def _run_machine_microstructure_final_refresh(
    tmp_path,
    *,
    expansion_rc=0,
    attribution_rc=0,
    weakness_hysteresis_rc=0,
    entry_timing_rc=0,
    policy_rc=0,
    builder_rc=0,
    target_date_rc=0,
    completed_target_date="2026-08-14",
):
    fake_python = tmp_path / "fake-python"
    call_log = tmp_path / "calls.log"
    fake_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                'case "$*" in',
                '  *"resolve_completed_machine_target_date"*)',
                '    printf "%s\\n" "${FAKE_COMPLETED_TARGET_DATE-2026-08-14}"',
                '    exit "${FAKE_TARGET_DATE_RC:-0}" ;;',
                "esac",
                'printf "%s\\n" "$*" >> "$FINAL_REFRESH_CALL_LOG"',
                'case "$*" in',
                '  *"widget_collector_expansion_recommendation"*)',
                '    exit "${FAKE_EXPANSION_RC:-0}" ;;',
                '  *"machine_microstructure_attribution"*)',
                '    exit "${FAKE_ATTRIBUTION_RC:-0}" ;;',
                '  *"market_weakness_hysteresis_tuning"*)',
                '    exit "${FAKE_WEAKNESS_HYSTERESIS_RC:-0}" ;;',
                '  *"machine_entry_timing_tuning"*)',
                '    exit "${FAKE_ENTRY_TIMING_RC:-0}" ;;',
                '  *"machine_microstructure_policy_approval"*)',
                '    exit "${FAKE_POLICY_RC:-0}" ;;',
                '  *"build_next_stage2_checklist"*)',
                '    exit "${FAKE_BUILDER_RC:-0}" ;;',
                "esac",
                "exit 99",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    env = {
        **os.environ,
        "KORSTOCKSCAN_PROJECT_DIR": str(Path.cwd()),
        "KORSTOCKSCAN_PYTHON_BIN": str(fake_python),
        "FINAL_REFRESH_CALL_LOG": str(call_log),
        "FAKE_EXPANSION_RC": str(expansion_rc),
        "FAKE_ATTRIBUTION_RC": str(attribution_rc),
        "FAKE_WEAKNESS_HYSTERESIS_RC": str(weakness_hysteresis_rc),
        "FAKE_ENTRY_TIMING_RC": str(entry_timing_rc),
        "FAKE_POLICY_RC": str(policy_rc),
        "FAKE_BUILDER_RC": str(builder_rc),
        "FAKE_COMPLETED_TARGET_DATE": completed_target_date,
        "FAKE_TARGET_DATE_RC": str(target_date_rc),
    }

    result = subprocess.run(
        ["deploy/run_machine_microstructure_final_refresh.sh"],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )
    calls = (
        call_log.read_text(encoding="utf-8").splitlines() if call_log.exists() else []
    )
    return result, calls


def test_machine_microstructure_final_refresh_success_order_and_flags(tmp_path):
    result, calls = _run_machine_microstructure_final_refresh(tmp_path)

    assert result.returncode == 0
    assert len(calls) == 6
    assert "widget_collector_expansion_recommendation" in calls[0]
    assert "--target-date 2026-08-14" in calls[0]
    assert "--write --notify --source-wait-sec 900 --source-poll-sec 30" in calls[0]
    assert "machine_microstructure_attribution" in calls[1]
    assert "--target-date 2026-08-14" in calls[1]
    assert "--write --print-summary" in calls[1]
    assert "market_weakness_hysteresis_tuning" in calls[2]
    assert "--target-date 2026-08-14" in calls[2]
    assert "--write --print-summary" in calls[2]
    assert "machine_entry_timing_tuning" in calls[3]
    assert "--target-date 2026-08-14" in calls[3]
    assert "--write --print-summary" in calls[3]
    assert "machine_microstructure_policy_approval" in calls[4]
    assert "--target-date 2026-08-14" in calls[4]
    assert "--notify-objective-followups" in calls[4]
    assert "build_next_stage2_checklist" in calls[5]
    assert "--completed-machine-source-date 2026-08-14" in calls[5]
    assert (
        "expansion_rc=0 attribution_rc=0 weakness_hysteresis_rc=0 "
        "entry_timing_rc=0 policy_rc=0 builder_rc=0" in (result.stderr)
    )


def test_machine_microstructure_final_refresh_fails_before_children_when_date_resolution_fails(
    tmp_path,
):
    result, calls = _run_machine_microstructure_final_refresh(
        tmp_path,
        target_date_rc=6,
        completed_target_date="",
    )

    assert result.returncode == 6
    assert calls == []
    assert "target_date=unresolved target_date_rc=6" in result.stderr


@pytest.mark.parametrize(
    ("expansion_rc", "attribution_rc", "policy_rc", "expected_rc"),
    [
        (5, 0, 0, 5),
        (5, 4, 0, 4),
        (5, 4, 3, 3),
    ],
)
def test_machine_microstructure_final_refresh_continues_after_upstream_failure(
    tmp_path,
    expansion_rc,
    attribution_rc,
    policy_rc,
    expected_rc,
):
    result, calls = _run_machine_microstructure_final_refresh(
        tmp_path,
        expansion_rc=expansion_rc,
        attribution_rc=attribution_rc,
        policy_rc=policy_rc,
    )

    assert result.returncode == expected_rc
    assert len(calls) == (4 if attribution_rc else 6)
    assert "widget_collector_expansion_recommendation" in calls[0]
    assert "machine_microstructure_attribution" in calls[1]
    if attribution_rc:
        assert "machine_microstructure_policy_approval" in calls[2]
        assert "build_next_stage2_checklist" in calls[3]
    else:
        assert "market_weakness_hysteresis_tuning" in calls[2]
        assert "machine_entry_timing_tuning" in calls[3]
        assert "machine_microstructure_policy_approval" in calls[4]
        assert "build_next_stage2_checklist" in calls[5]


def test_machine_microstructure_final_refresh_prioritizes_builder_failure(tmp_path):
    result, calls = _run_machine_microstructure_final_refresh(
        tmp_path,
        expansion_rc=5,
        attribution_rc=4,
        policy_rc=3,
        builder_rc=7,
    )

    assert result.returncode == 7
    assert len(calls) == 4
    assert (
        "expansion_rc=5 attribution_rc=4 weakness_hysteresis_rc=0 "
        "entry_timing_rc=0 policy_rc=3 builder_rc=7" in (result.stderr)
    )


def test_machine_microstructure_final_refresh_surfaces_entry_timing_failure(tmp_path):
    result, calls = _run_machine_microstructure_final_refresh(
        tmp_path,
        entry_timing_rc=8,
    )

    assert result.returncode == 8
    assert len(calls) == 6
    assert "machine_entry_timing_tuning" in calls[3]
    assert "entry_timing_rc=8" in result.stderr


def test_machine_microstructure_final_refresh_surfaces_weakness_hysteresis_failure(
    tmp_path,
):
    result, calls = _run_machine_microstructure_final_refresh(
        tmp_path,
        weakness_hysteresis_rc=9,
        entry_timing_rc=8,
    )

    assert result.returncode == 9
    assert len(calls) == 6
    assert "market_weakness_hysteresis_tuning" in calls[2]
    assert "machine_entry_timing_tuning" in calls[3]
    assert "weakness_hysteresis_rc=9" in result.stderr


def test_scalp_sim_overnight_preclose_wrapper_uses_live_openai_without_bedrock_lite_shadow():
    script = Path("deploy/run_scalp_sim_overnight_preclose.sh").read_text(
        encoding="utf-8"
    )

    assert "PYTHONPATH=." in script
    assert (
        'src.engine.scalp_sim_overnight --date "$TARGET_DATE" --live-openai' in script
    )
    assert "--report-only" not in script
    assert "KORSTOCKSCAN_BEDROCK_NOVA_LITE_SHADOW_ENABLED" not in script
    assert "KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=off" in script


def test_threshold_cycle_postclose_recovers_late_scalp_sim_positions_with_openai():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    report_only = 'src.engine.scalp_sim_overnight --date "$TARGET_DATE" --report-only'
    late_recovery = 'src.engine.scalp_sim_overnight --date "$TARGET_DATE" --live-openai'
    assert report_only in script
    assert late_recovery in script
    assert script.index(report_only) < script.index(late_recovery)
    assert '"active_undecided_count"' in script
    assert "provider=openai runtime_effect=false" in script
    assert "KORSTOCKSCAN_OPENAI_TRANSPORT_MODE" in script
    assert "KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED" in script
    assert "KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=off" in script


def test_threshold_cycle_cron_installs_scalp_sim_overnight_preclose_once():
    script = Path("deploy/install_threshold_cycle_cron.sh").read_text(encoding="utf-8")

    assert "SCALP_SIM_OVERNIGHT_PRECLOSE" in script
    assert "10 15 * * 1-5" in script
    assert "deploy/run_scalp_sim_overnight_preclose.sh" in script
    assert "!/SCALP_SIM_OVERNIGHT_PRECLOSE/" in script
    assert "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false" in script


def test_postclose_done_controller_wrapper_runs_controller_and_skips_codex_runner_by_default():
    script = Path("deploy/run_postclose_done_controller.sh").read_text(encoding="utf-8")

    controller_idx = script.index("src.engine.automation.postclose_done_controller")
    entry_setup_idx = script.index(
        'runner_path="$PROJECT_DIR/deploy/run_ai_entry_setup_paired_replay_postclose.sh"'
    )
    codex_idx = script.index("src.engine.automation.codex_workorder_runner")

    assert "[START] postclose_done_controller" in script
    assert "[DONE] postclose_done_controller" in script
    assert "--allow-wrapper-rerun" in script
    assert "--predecessor-timeout-sec" in script
    assert "POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_TIMEOUT_SEC" in script
    assert "POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_TIMEOUT_SEC:-43200" in script
    assert "$PROJECT_DIR/venv/Scripts/python.exe" in script
    assert 'RUN_CODEX="${POSTCLOSE_DONE_CONTROLLER_RUN_CODEX:-false}"' in script
    assert "POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL_POLICY" in script
    assert (
        'CODEX_MODEL_POLICY="${POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL_POLICY:-credit_min}"'
        in script
    )
    assert "POSTCLOSE_DONE_CONTROLLER_CODEX_MODEL" in script
    assert "POSTCLOSE_DONE_CONTROLLER_CODEX_EFFORT" in script
    assert "POSTCLOSE_DONE_CONTROLLER_CODEX_BATCH_SIZE" in script
    assert "POSTCLOSE_DONE_CONTROLLER_AUTO_PUSH_MAIN" in script
    assert "POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED" in script
    assert (
        'REQUIRE_CODEX_COMPLETED="${POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED:-false}"'
        in script
    )
    assert "--model-policy" in script
    assert "--model" in script
    assert "--effort" in script
    assert "--auto-push-main" in script
    assert "--no-auto-push-main" in script
    assert "--require-codex-completed" in script
    assert (
        "codex_workorder_runner disabled while strict completion is required"
        not in script
    )
    assert 'VENV_PY="python"' in script
    assert "controller_report=" in script
    assert "controller_status" in script
    assert "[SKIP] codex_workorder_runner" in script
    assert "disabled_by_default" in script
    assert "[WARN] codex_workorder_runner" not in script
    assert 'codex_status" != "completed"' in script
    assert controller_idx < entry_setup_idx < codex_idx


def test_postclose_done_controller_retriggers_late_entry_setup_follower_idempotently():
    script = Path("deploy/run_postclose_done_controller.sh").read_text(encoding="utf-8")

    assert (
        'RUN_ENTRY_SETUP_REPLAY_FOLLOWUP="${POSTCLOSE_DONE_CONTROLLER_RUN_ENTRY_SETUP_REPLAY_FOLLOWUP:-true}"'
        in script
    )
    assert (
        'ENTRY_SETUP_REPLAY_FOLLOWUP_WAIT_SEC="${POSTCLOSE_DONE_CONTROLLER_ENTRY_SETUP_REPLAY_FOLLOWUP_WAIT_SEC:-0}"'
        in script
    )
    assert (
        'ENTRY_SETUP_REPLAY_ACTIVE_WAIT_SEC="${POSTCLOSE_DONE_CONTROLLER_ENTRY_SETUP_REPLAY_ACTIVE_WAIT_SEC:-3600}"'
        in script
    )
    assert (
        'ENTRY_SETUP_REPLAY_ACTIVE_POLL_SEC="${POSTCLOSE_DONE_CONTROLLER_ENTRY_SETUP_REPLAY_ACTIVE_POLL_SEC:-15}"'
        in script
    )
    assert 'controller_status" != "done"' in script
    assert 'date -d "${TARGET_DATE} 21:05:00"' in script
    assert "awaiting_fixed_2105_trigger" in script
    assert 'batch.get("status") != "completed_offline_only"' in script
    assert 'candidate.get("source_date") != target_date' in script
    assert "candidate_path.resolve() != expected_candidate_path.resolve()" in script
    assert (
        'candidate.get("effective_date_policy") != "first_available_krx_preopen_v1"'
        in script
    )
    assert 'candidate.get("preopen_candidate_cutoff_kst") != "07:35:00"' in script
    assert "candidate_contract_hash_missing_or_invalid" in script
    assert (
        'candidate.get("artifact_sha256") != candidate_ref.get("artifact_sha256")'
        in script
    )
    assert "terminal_ready:validated_batch_and_candidate" in script
    assert 'while ! flock -n "$lock_path" -c true' in script
    assert "active_runner_timeout" in script
    assert (
        'AI_ENTRY_SETUP_REPLAY_PREDECESSOR_WAIT_SEC="$ENTRY_SETUP_REPLAY_FOLLOWUP_WAIT_SEC"'
        in script
    )
    assert "nonterminal_after_runner" in script
    assert "[FAIL] ai_entry_setup_replay_followup" in script
    assert "run_bot.sh" not in script
    assert "systemctl restart" not in script


def test_postclose_done_controller_entry_setup_terminal_validator(tmp_path: Path):
    script = Path("deploy/run_postclose_done_controller.sh").read_text(encoding="utf-8")
    function_start = script.index("entry_setup_replay_followup_state()")
    heredoc_start = script.index("<<'PY'\n", function_start) + len("<<'PY'\n")
    heredoc_end = script.index("\nPY\n", heredoc_start)
    validator = script[heredoc_start:heredoc_end]

    target_date = "2026-08-25"
    candidate_path = (
        tmp_path
        / "data"
        / "threshold_cycle"
        / "bounded_live_candidates"
        / f"entry_setup_v2_14_bounded_live_candidate_{target_date}.json"
    )
    candidate_path.parent.mkdir(parents=True)
    candidate = {
        "source_date": target_date,
        "status": "bounded_exploration_apply_ready",
        "effective_date": "2026-08-27",
        "effective_date_policy": "first_available_krx_preopen_v1",
        "preopen_candidate_cutoff_kst": "07:35:00",
        "candidate_contract_sha256": "c" * 64,
    }
    candidate["artifact_sha256"] = hashlib.sha256(
        json.dumps(
            candidate,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    batch_path = (
        tmp_path
        / "data"
        / "report"
        / "ai_entry_setup_paired_replay_batch"
        / f"ai_entry_setup_paired_replay_batch_{target_date}.json"
    )
    batch_path.parent.mkdir(parents=True)
    batch = {
        "target_date": target_date,
        "status": "completed_offline_only",
        "krx_bounded_live_candidate": {
            "path": str(candidate_path),
            "status": candidate["status"],
            "effective_date": candidate["effective_date"],
            "artifact_sha256": candidate["artifact_sha256"],
        },
    }
    batch_path.write_text(json.dumps(batch), encoding="utf-8")

    def validate() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-", str(tmp_path), target_date, str(batch_path)],
            input=validator,
            text=True,
            capture_output=True,
            check=False,
        )

    result = validate()
    assert result.returncode == 0
    assert result.stdout.strip() == "terminal_ready:validated_batch_and_candidate"

    candidate["blocking_reasons"] = ["tampered_without_hash_refresh"]
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    result = validate()
    assert result.returncode == 0
    assert result.stdout.strip() == (
        "retry_required:candidate_artifact_self_hash_mismatch"
    )

    candidate.pop("blocking_reasons")
    candidate["artifact_sha256"] = hashlib.sha256(
        json.dumps(
            {
                key: value
                for key, value in candidate.items()
                if key != "artifact_sha256"
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    batch["krx_bounded_live_candidate"]["artifact_sha256"] = "stale-batch-hash"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    result = validate()
    assert result.returncode == 0
    assert result.stdout.strip() == "retry_required:candidate_hash_mismatch"

    batch["status"] = "running"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    result = validate()
    assert result.returncode == 0
    assert result.stdout.strip() == "retry_required:batch_status_running"


def test_postclose_done_controller_cron_installs_2010_once():
    script = Path("deploy/install_postclose_done_controller_cron.sh").read_text(
        encoding="utf-8"
    )

    assert "POSTCLOSE_DONE_CONTROLLER" in script
    assert "10 20 * * 1-5" in script
    assert "40 21 * * 1-5" not in script
    assert "deploy/run_postclose_done_controller.sh" in script


def test_postclose_wrapper_keeps_swing_postclose_off_until_operator_override():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    simulation_idx = script.index(
        'deploy/run_swing_daily_simulation_report.sh" "$TARGET_DATE"'
    )
    simulation_wait_idx = script.index(
        '"$PROJECT_DIR/data/report/swing_daily_simulation/swing_daily_simulation_${TARGET_DATE}.json"'
    )
    discovery_idx = script.index("src.engine.swing_strategy_discovery_sim")
    label_idx = script.index("src.engine.swing_strategy_discovery_label_builder")
    discovery_ev_idx = script.index("src.engine.swing_strategy_discovery_ev_report")
    swing_ldm_idx = script.index("src.engine.swing_lifecycle_decision_matrix")
    swing_bucket_idx = script.index("src.engine.swing_lifecycle_bucket_discovery")
    audit_idx = script.index("src.engine.swing_lifecycle_audit")
    resource_idx = script.index('wait_for_postclose_resources "swing_lifecycle_audit"')

    assert simulation_idx < audit_idx
    assert (
        simulation_idx
        < simulation_wait_idx
        < discovery_idx
        < label_idx
        < discovery_ev_idx
        < swing_ldm_idx
        < swing_bucket_idx
        < audit_idx
    )
    assert resource_idx < audit_idx
    assert (
        'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.swing_lifecycle_audit'
        in script
    )
    assert (
        'SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-openai}"'
        in script
    )
    assert (
        'RUN_SWING_POSTCLOSE="${THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE:-false}"' in script
    )
    assert (
        'RUN_SWING_STRATEGY_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_STRATEGY_DISCOVERY:-true}"'
        in script
    )
    assert (
        'RUN_SWING_LIFECYCLE_MATRIX="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_MATRIX:-$RUN_SWING_STRATEGY_DISCOVERY}"'
        in script
    )
    assert (
        'RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY="${THRESHOLD_CYCLE_RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY:-$RUN_SWING_LIFECYCLE_MATRIX}"'
        in script
    )
    assert "RUN_SWING_LIFECYCLE_AUDIT=false" in script
    assert "RUN_SWING_STRATEGY_DISCOVERY=false" in script
    assert "RUN_SWING_LIFECYCLE_MATRIX=false" in script
    assert "RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY=false" in script
    assert "RUN_DEEPSEEK_SWING_LAB=false" in script
    assert "RUN_SWING_PATTERN_LAB_AUTOMATION=false" in script
    assert "--disabled-stage swing_lifecycle" in script
    assert "--disabled-stage swing_strategy_discovery" in script
    assert "--disabled-stage swing_lifecycle_matrix" in script
    assert "--disabled-stage swing_lifecycle_bucket_discovery" in script


def test_swing_postclose_cron_installers_require_explicit_operator_override():
    dry_run_installer = Path("deploy/install_swing_live_dry_run_cron.sh").read_text(
        encoding="utf-8"
    )
    retrain_installer = Path("deploy/install_swing_model_retrain_cron.sh").read_text(
        encoding="utf-8"
    )

    for script in (dry_run_installer, retrain_installer):
        assert (
            'OPERATOR_OVERRIDE="${KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE:-false}"'
            in script
        )
        assert (
            '[[ "$OPERATOR_OVERRIDE" == "true" || "$OPERATOR_OVERRIDE" == "1" ]]'
            in script
        )


def test_swing_ldm_rolling_backfill_waits_for_postclose_and_skips_holidays():
    script = Path("deploy/run_swing_ldm_rolling_backfill_once.sh").read_text(
        encoding="utf-8"
    )

    assert "threshold_cycle_postclose_${POSTCLOSE_DATE}.status.json" in script
    assert 'if [ "$status" = "succeeded" ]; then' in script
    assert (
        "2026-05-18 2026-05-19 2026-05-20 2026-05-21 2026-05-22 2026-05-26 2026-05-27 2026-05-28 2026-05-29 2026-06-01"
        in script
    )
    assert "2026-05-23" not in script
    assert "2026-05-24" not in script
    assert "2026-05-25" not in script
    assert "2026-05-30" not in script
    assert "2026-05-31" not in script
    assert "src.engine.swing_lifecycle_decision_matrix" in script
    assert "src.engine.swing_lifecycle_bucket_discovery --date" in script
    assert "--ai-provider openai" in script
    assert "src.engine.swing_lifecycle_audit --date" in script
    assert "--ai-review-provider openai" in script


def test_postclose_wrapper_includes_valid_bottom_rebound_source_for_swing_discovery():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    contract_idx = script.index("bottom_rebound_source_contract_ok()")
    source_path_idx = script.index(
        "swing_bottom_rebound_candidate_source_${TARGET_DATE}.json"
    )
    include_idx = script.index("--include-bottom-rebound-source")
    fallback_idx = script.index("safe_pool_only=true")
    discovery_idx = script.index("src.engine.swing_strategy_discovery_sim")

    assert contract_idx < source_path_idx < discovery_idx
    assert discovery_idx < include_idx
    assert source_path_idx < fallback_idx
    assert "bottom_rebound_source_contract=pass" in script
    assert "bottom_rebound_source_contract=missing_or_invalid" in script
    assert (
        'payload.get("report_type") == "swing_bottom_rebound_candidate_source"'
        in script
    )
    assert 'payload.get("runtime_effect") is False' in script
    assert 'payload.get("broker_order_forbidden") is True' in script
    assert 'payload.get("allowed_runtime_apply") is False' in script


def test_swing_live_dry_run_defaults_ai_review_provider_to_none():
    script = Path("deploy/run_swing_live_dry_run_report.sh").read_text(encoding="utf-8")

    assert (
        'SWING_THRESHOLD_AI_REVIEW_PROVIDER="${SWING_THRESHOLD_AI_REVIEW_PROVIDER:-none}"'
        in script
    )
    assert '--ai-review-provider "$SWING_THRESHOLD_AI_REVIEW_PROVIDER"' in script


def test_postclose_wrapper_runs_threshold_ev_before_and_after_workorder():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    sim_post_sell_idx = script.index("src.engine.sniper_post_sell_feedback")
    assert "--materialize-monitor-snapshot" in script
    rising_missed_feedback_idx = script.index(
        "src.engine.monitoring.rising_missed_intraday_feedback"
    )
    rising_missed_scout_idx = script.index(
        "src.engine.monitoring.rising_missed_scout_workorder"
    )
    scalping_pyramid_feedback_idx = script.index(
        "src.engine.monitoring.scalping_pyramid_intraday_feedback"
    )
    scalping_pyramid_calibration_idx = script.index(
        "src.engine.monitoring.scalping_pyramid_quality_calibration"
    )
    scalping_avg_down_recovery_idx = script.index(
        "src.engine.monitoring.scalping_avg_down_recovery_calibration"
    )
    one_share_threshold_idx = script.index(
        "src.engine.monitoring.one_share_threshold_opportunity"
    )
    entry_adm_idx = script.index("src.engine.scalp_entry_action_decision_matrix")
    entry_ai_gate_idx = script.index("src.engine.scalping.entry_ai_gate_backtest")
    microstructure_idx = script.index(
        "src.engine.scalping.microstructure_reaction_context"
    )
    observation_preflight_idx = script.index("observation_source_quality_preflight")
    scale_in_cf_idx = script.index(
        "src.engine.lifecycle.scale_in_incremental_counterfactual"
    )
    lifecycle_matrix_idx = script.index("src.engine.lifecycle_decision_matrix")
    context_attribution_idx = script.index(
        'src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode attribution'
    )
    context_idx = script.index(
        'src.engine.lifecycle_ai_context --date "$TARGET_DATE" --mode context'
    )
    assert (
        scalping_pyramid_feedback_idx
        < observation_preflight_idx
        < scalping_pyramid_calibration_idx
        < scalping_avg_down_recovery_idx
    )
    assert observation_preflight_idx < scale_in_cf_idx < lifecycle_matrix_idx
    assert (
        rising_missed_feedback_idx
        < rising_missed_scout_idx
        < scalping_pyramid_feedback_idx
        < scalping_pyramid_calibration_idx
        < scalping_avg_down_recovery_idx
        < one_share_threshold_idx
        < entry_adm_idx
    )
    discovery_idx = script.index("src.engine.lifecycle_bucket_discovery")
    bridge_idx = script.index("src.engine.runtime_apply_bridge")
    verbosity_idx = script.index("src.engine.pipeline_event_verbosity_report")
    observation_audit_idx = script.index(
        "src.engine.observation_source_quality_audit", verbosity_idx
    )
    assert (
        'src.engine.observation_source_quality_audit --target-date "$TARGET_DATE" --write --print-summary'
        in script
    )
    perf_source_idx = script.index("src.engine.codebase_performance_workorder_report")
    action_outcome_calibration_idx = script.index(
        "src.engine.scalping.ai_action_outcome_calibration"
    )
    time_window_idx = script.index(
        "src.engine.automation.time_window_regime_counterfactual"
    )
    assert action_outcome_calibration_idx < time_window_idx
    producer_gap_source_idx = script.index(
        "src.engine.automation.producer_gap_source_bundle"
    )
    producer_gap_idx = script.index("src.engine.automation.producer_gap_discovery")
    stage_hook_idx = script.index(
        "src.engine.automation.stage_hook_workorder_discovery"
    )
    stage_hook_scaffold_idx = script.index(
        "src.engine.automation.stage_hook_runtime_scaffold"
    )
    pre_ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')
    workorder_idx = script.index("src.engine.build_code_improvement_workorder")
    post_ev_idx = script.index(
        'run_threshold_cycle_ev_and_wait "post_workorder_refresh"'
    )
    propagation_idx = script.index("src.engine.pattern_lab_propagation_audit")
    ai_review_source_refresh_idx = script.index("--refresh-source-provenance")
    post_propagation_ev_idx = script.index(
        'run_threshold_cycle_ev_and_wait "post_propagation_audit_refresh"'
    )
    runtime_summary_idx = script.index("src.engine.runtime_approval_summary")
    runtime_gap_idx = script.index("src.engine.runtime_apply_gap_audit")
    conversion_lane_idx = script.index("src.engine.automation.conversion_lane")
    assert "CONVERSION_LANE_SWING_ARGS+=(--exclude-swing)" in script
    rising_missed_prior_idx = script.index(
        "src.engine.monitoring.rising_missed_classifier_prior"
    )
    scalp_sim_prior_refresh_idx = script.index(
        '"scalp_sim_auto_approval_control_tower_prior_refresh"'
    )
    post_conversion_workorder_idx = script.index(
        "code_improvement_workorder_post_conversion_lane"
    )
    checklist_command = (
        'src.engine.build_next_stage2_checklist --source-date "$TARGET_DATE"'
    )
    next_checklist_idx = script.index(checklist_command)
    pending_verify_idx = script.index(
        "src.engine.verify_threshold_cycle_postclose_chain"
    )
    final_verify_idx = script.index(
        "src.engine.verify_threshold_cycle_postclose_chain",
        pending_verify_idx + 1,
    )
    final_next_checklist_idx = script.rindex(checklist_command)
    tuning_control_idx = script.index(
        "src.engine.automation.tuning_performance_control_tower"
    )

    assert (
        sim_post_sell_idx
        < rising_missed_feedback_idx
        < rising_missed_scout_idx
        < scalping_pyramid_feedback_idx
        < observation_preflight_idx
        < scalping_pyramid_calibration_idx
        < scalping_avg_down_recovery_idx
        < entry_adm_idx
        < entry_ai_gate_idx
        < microstructure_idx
        < lifecycle_matrix_idx
        < context_attribution_idx
        < context_idx
        < discovery_idx
        < bridge_idx
        < verbosity_idx
        < observation_audit_idx
        < action_outcome_calibration_idx
        < perf_source_idx
        < time_window_idx
        < producer_gap_source_idx
        < producer_gap_idx
        < stage_hook_idx
        < stage_hook_scaffold_idx
        < pre_ev_idx
        < workorder_idx
        < post_ev_idx
        < propagation_idx
        < ai_review_source_refresh_idx
        < post_propagation_ev_idx
        < runtime_summary_idx
        < runtime_gap_idx
        < conversion_lane_idx
        < rising_missed_prior_idx
        < scalp_sim_prior_refresh_idx
        < post_conversion_workorder_idx
        < next_checklist_idx
        < final_next_checklist_idx
        < pending_verify_idx
        < final_verify_idx
        < tuning_control_idx
    )
    assert (
        'RUN_PATTERN_LAB_PROPAGATION_AUDIT="${THRESHOLD_CYCLE_RUN_PATTERN_LAB_PROPAGATION_AUDIT:-true}"'
        in script
    )
    assert (
        'RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL="${THRESHOLD_CYCLE_RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL:-false}"'
        in script
    )
    assert (
        'RUN_PRODUCER_GAP_DISCOVERY="${THRESHOLD_CYCLE_RUN_PRODUCER_GAP_DISCOVERY:-false}"'
        in script
    )
    assert (
        'RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE="${THRESHOLD_CYCLE_RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE:-true}"'
        in script
    )
    assert '[[ -n "${THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT:-}" ]]' in script
    assert (
        'RUN_LIMIT_DOWN_WATCH_REPORT="$THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT"'
        in script
    )
    assert "RUN_LIMIT_DOWN_WATCH_REPORT=true" in script
    assert '|| -s "$LIMIT_DOWN_WATCH_CANDIDATE_SOURCE"' not in script
    assert "RUN_LIMIT_DOWN_WATCH_REPORT=false" not in script
    assert "src.engine.monitoring.limit_down_watch_report" in script
    assert (
        '"$PROJECT_DIR/data/report/limit_down_watch/limit_down_watch_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/limit_down_watch/limit_down_watch_${TARGET_DATE}.md"'
        in script
    )
    assert (
        'RUN_RISING_MISSED_SCOUT_WORKORDER="${THRESHOLD_CYCLE_RUN_RISING_MISSED_SCOUT_WORKORDER:-true}"'
        in script
    )
    assert (
        'RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE="${THRESHOLD_CYCLE_RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE:-true}"'
        in script
    )
    assert (
        'RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION="${THRESHOLD_CYCLE_RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION:-true}"'
        in script
    )
    assert (
        'RUN_RISING_MISSED_CLASSIFIER_PRIOR="${THRESHOLD_CYCLE_RUN_RISING_MISSED_CLASSIFIER_PRIOR:-true}"'
        in script
    )
    assert (
        'RUN_STAGE_HOOK_WORKORDER_DISCOVERY="${THRESHOLD_CYCLE_RUN_STAGE_HOOK_WORKORDER_DISCOVERY:-false}"'
        in script
    )
    assert (
        'RUN_STAGE_HOOK_RUNTIME_SCAFFOLD="${THRESHOLD_CYCLE_RUN_STAGE_HOOK_RUNTIME_SCAFFOLD:-false}"'
        in script
    )
    assert (
        'RUN_SCALP_ENTRY_ADM="${THRESHOLD_CYCLE_RUN_SCALP_ENTRY_ADM:-true}"' in script
    )
    assert (
        'RUN_ENTRY_AI_GATE_BACKTEST="${THRESHOLD_CYCLE_RUN_ENTRY_AI_GATE_BACKTEST:-true}"'
        in script
    )
    assert (
        'RUN_MICROSTRUCTURE_REACTION_CONTEXT="${THRESHOLD_CYCLE_RUN_MICROSTRUCTURE_REACTION_CONTEXT:-true}"'
        in script
    )
    assert (
        'RUN_LIFECYCLE_DECISION_MATRIX="${THRESHOLD_CYCLE_RUN_LIFECYCLE_DECISION_MATRIX:-true}"'
        in script
    )
    assert (
        'RUN_LIFECYCLE_AI_CONTEXT="${THRESHOLD_CYCLE_RUN_LIFECYCLE_AI_CONTEXT:-true}"'
        in script
    )
    assert (
        'RUN_LIFECYCLE_BUCKET_DISCOVERY="${THRESHOLD_CYCLE_RUN_LIFECYCLE_BUCKET_DISCOVERY:-$RUN_LIFECYCLE_DECISION_MATRIX}"'
        in script
    )
    assert (
        'RUN_RUNTIME_APPLY_BRIDGE="${THRESHOLD_CYCLE_RUN_RUNTIME_APPLY_BRIDGE:-$RUN_LIFECYCLE_BUCKET_DISCOVERY}"'
        in script
    )
    assert (
        'RUN_TUNING_PERFORMANCE_CONTROL_TOWER="${THRESHOLD_CYCLE_RUN_TUNING_PERFORMANCE_CONTROL_TOWER:-true}"'
        in script
    )
    assert "lifecycle_ai_context=$RUN_LIFECYCLE_AI_CONTEXT" in script
    assert "lifecycle_bucket_discovery=$RUN_LIFECYCLE_BUCKET_DISCOVERY" in script
    assert "runtime_apply_bridge=$RUN_RUNTIME_APPLY_BRIDGE" in script
    assert (
        "tuning_performance_control_tower=$RUN_TUNING_PERFORMANCE_CONTROL_TOWER"
        in script
    )
    assert "entry_ai_gate_backtest=$RUN_ENTRY_AI_GATE_BACKTEST" in script
    assert "ai_score_optimization_backtest" not in script
    assert (
        "time_window_regime_counterfactual=$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL"
        in script
    )
    assert "producer_gap_discovery=$RUN_PRODUCER_GAP_DISCOVERY" in script
    assert (
        "stage_hook_workorder_discovery=$RUN_STAGE_HOOK_WORKORDER_DISCOVERY" in script
    )
    assert "stage_hook_runtime_scaffold=$RUN_STAGE_HOOK_RUNTIME_SCAFFOLD" in script
    assert "swing_lifecycle_matrix=$RUN_SWING_LIFECYCLE_MATRIX" in script
    assert (
        "swing_lifecycle_bucket_discovery=$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY"
        in script
    )
    assert (
        "microstructure_reaction_context=$RUN_MICROSTRUCTURE_REACTION_CONTEXT" in script
    )
    assert (
        "ai_decision_action_outcome_calibration="
        "$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION" in script
    )
    assert "optional microstructure_reaction_context failed" in script
    assert "optional microstructure_reaction_context artifact wait failed" in script


def test_postclose_wrapper_materializes_daily_exact_quality_chain_before_calibration():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'RUN_AI_DECISION_QUALITY_DAILY_MATERIALIZATION="${THRESHOLD_CYCLE_RUN_AI_DECISION_QUALITY_DAILY_MATERIALIZATION:-true}"'
        in script
    )
    materialization_idx = script.index("src.engine.scalping.ai_decision_quality")
    calibration_idx = script.index("src.engine.scalping.ai_action_outcome_calibration")
    materialization_block = script[materialization_idx:calibration_idx]

    assert materialization_idx < calibration_idx
    assert "--mode postclose" in materialization_block
    assert "--write" in materialization_block
    assert "--execute-candidate" not in materialization_block
    for artifact in (
        "ai_decision_quality_control_${TARGET_DATE}.json",
        "ai_decision_outcome_labels_${TARGET_DATE}.json",
        "ai_decision_quality_baseline_${TARGET_DATE}.json",
        "ai_prompt_paired_replay_${TARGET_DATE}.json",
        "entry_candidate_lifecycle_state_${TARGET_DATE}.json",
    ):
        assert artifact in materialization_block
    assert (
        "ai_decision_quality_daily_materialization="
        "$RUN_AI_DECISION_QUALITY_DAILY_MATERIALIZATION" in script
    )


def test_postclose_wrapper_runs_bounded_main_ai_quality_r0_r3_after_exact_chain():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'RUN_MAIN_AI_QUALITY_R0_R3="${THRESHOLD_CYCLE_RUN_MAIN_AI_QUALITY_R0_R3:-true}"'
        in script
    )
    assert (
        'MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY="${THRESHOLD_CYCLE_MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY:-true}"'
        in script
    )
    assert (
        'MAIN_AI_QUALITY_DAILY_ATTEMPT_CAP="${THRESHOLD_CYCLE_MAIN_AI_QUALITY_DAILY_ATTEMPT_CAP:-390}"'
        in script
    )
    assert (
        'MAIN_AI_QUALITY_PARENT_CAP="${THRESHOLD_CYCLE_MAIN_AI_QUALITY_PARENT_CAP:-130}"'
        in script
    )
    assert (
        'MAIN_AI_QUALITY_DAILY_USD_CAP="${THRESHOLD_CYCLE_MAIN_AI_QUALITY_DAILY_USD_CAP:-1.0}"'
        in script
    )
    exact_index = script.index("-m src.engine.scalping.ai_decision_quality")
    cycle_index = script.index(
        "-m src.engine.scalping.micro_reversion.ai_quality_cycle"
    )
    runtime_family_index = script.index(
        "-m src.engine.automation.main_ai_quality_runtime_family"
    )
    calibration_index = script.index(
        "-m src.engine.scalping.ai_action_outcome_calibration"
    )
    assert exact_index < cycle_index < runtime_family_index < calibration_index
    assert (
        'RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY="${THRESHOLD_CYCLE_RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY:-true}"'
        in script
    )
    runtime_family_block = script[runtime_family_index:calibration_index]
    assert "--phase postclose" in runtime_family_block
    assert '--target-date "$TARGET_DATE"' in runtime_family_block
    assert "--write" in runtime_family_block
    assert "blocked_fail_closed" in runtime_family_block
    assert "runtime_effect=false actual_order_submitted=false" in runtime_family_block
    cycle_block_start = script.rindex(
        'if [ "$RUN_MAIN_AI_QUALITY_R0_R3" = "true" ]',
        0,
        cycle_index,
    )
    cycle_block_end = script.index(
        'if [ "$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION" = "true" ]',
        cycle_index,
    )
    cycle_block = script[cycle_block_start:cycle_block_end]
    assert "--execute-provider-replay" in cycle_block
    assert "--daily-attempt-cap" in cycle_block
    assert "--daily-usd-cap" in cycle_block
    assert "--parent-cap" in cycle_block
    assert "main_ai_quality_rc=0" in cycle_block
    assert "runtime_effect=false actual_order_submitted=false" in cycle_block
    assert "if ! wait_for_json_artifact" in cycle_block
    assert 'main_ai_quality_failure_reason="artifact_missing_or_invalid"' in cycle_block


@pytest.mark.parametrize(
    (
        "resource_rc",
        "command_rc",
        "artifact_rc",
        "expected_reason",
        "expect_cycle_call",
        "expect_artifact_wait",
    ),
    [
        (17, 0, 0, "resource_wait_failed", False, False),
        (0, 23, 0, "cycle_command_failed_or_deferred", True, False),
        (0, 0, 1, "artifact_missing_or_invalid", True, True),
    ],
)
def test_postclose_wrapper_isolates_main_ai_quality_failures(
    resource_rc,
    command_rc,
    artifact_rc,
    expected_reason,
    expect_cycle_call,
    expect_artifact_wait,
):
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    start = script.index('if [ "$RUN_MAIN_AI_QUALITY_R0_R3" = "true" ]')
    end = script.index('if [ "$RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY" = "true" ]', start)
    cycle_block = script[start:end]
    harness = "\n".join(
        [
            """
set -Eeuo pipefail
RUN_MAIN_AI_QUALITY_R0_R3=true
MAIN_AI_QUALITY_EXECUTE_PROVIDER_REPLAY=true
MAIN_AI_QUALITY_DAILY_ATTEMPT_CAP=12
MAIN_AI_QUALITY_DAILY_USD_CAP=1
MAIN_AI_QUALITY_PARENT_CAP=1
TARGET_DATE=2026-08-14
PROJECT_DIR=/tmp/korstockscan-wrapper-test
VENV_PY=/tmp/unused-python
""",
            f"RESOURCE_RC={resource_rc}",
            f"COMMAND_RC={command_rc}",
            f"ARTIFACT_RC={artifact_rc}",
            """
wait_for_postclose_resources() { return "$RESOURCE_RC"; }
run_postclose_cmd() { echo cycle_called; return "$COMMAND_RC"; }
wait_for_json_artifact() { echo artifact_waited; return "$ARTIFACT_RC"; }
emit_postclose_marker() { echo "$1"; }
""",
            cycle_block,
            """
echo unrelated_postclose_continues
""",
        ]
    )

    result = subprocess.run(
        ["bash", "-c", harness],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert f"reason={expected_reason}" in result.stdout
    assert "unrelated_postclose_continues" in result.stdout
    assert ("cycle_called" in result.stdout) is expect_cycle_call
    assert ("artifact_waited" in result.stdout) is expect_artifact_wait


def test_postclose_wrapper_isolates_bounded_runtime_family_failure() -> None:
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")
    start = script.index('if [ "$RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY" = "true" ]')
    end = script.index(
        'if [ "$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION" = "true" ]', start
    )
    family_block = script[start:end]
    harness = "\n".join(
        [
            """
set -Eeuo pipefail
RUN_MAIN_AI_QUALITY_RUNTIME_FAMILY=true
TARGET_DATE=2026-08-14
VENV_PY=/tmp/unused-python
run_postclose_cmd() { echo family_called; return 31; }
emit_postclose_marker() { echo "$1"; }
""",
            family_block,
            "echo unrelated_postclose_continues",
        ]
    )

    result = subprocess.run(
        ["bash", "-c", harness], text=True, capture_output=True, check=False
    )

    assert result.returncode == 0
    assert "family_called" in result.stdout
    assert "status=blocked_fail_closed" in result.stdout
    assert "runtime_effect=false actual_order_submitted=false" in result.stdout
    assert "unrelated_postclose_continues" in result.stdout


def test_entry_setup_paired_replay_has_separate_late_offline_cron():
    installer = Path("deploy/install_threshold_cycle_cron.sh").read_text(
        encoding="utf-8"
    )
    runner = Path("deploy/run_ai_entry_setup_paired_replay_postclose.sh").read_text(
        encoding="utf-8"
    )

    assert "5 21 * * 1-5" in installer
    assert "AI_ENTRY_SETUP_PAIRED_REPLAY_POSTCLOSE" in installer
    assert "run_ai_entry_setup_paired_replay_postclose.sh" in installer
    assert "src.engine.scalping.entry_setup_paired_replay_batch" in runner
    assert "--max-new-requests-per-cohort" in runner
    assert "--candidate-workers" in runner
    assert "--write" in runner
    assert "AI_ENTRY_SETUP_REPLAY_MAX_ATTEMPTS" in runner
    assert 'MAX_ATTEMPTS="${AI_ENTRY_SETUP_REPLAY_MAX_ATTEMPTS:-3}"' in runner
    assert 'if [ "$batch_rc" -eq 3 ]' in runner
    assert "AI_ENTRY_SETUP_REPLAY_PREDECESSOR_WAIT_SEC:-43200" in runner
    assert "predecessor bounded wait exhausted" in runner
    assert "sleep 15" in runner
    assert "run_bot.sh" not in runner
    assert "tmux" not in runner


def test_postclose_wrapper_treats_producer_gap_fail_closed_as_report_artifact():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    producer_gap_idx = script.index("src.engine.automation.producer_gap_discovery")
    nonfatal_idx = script.index(
        "producer gap discovery returned fail-closed report (non-fatal)"
    )
    artifact_idx = script.index(
        '"$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.json"'
    )
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert producer_gap_idx < nonfatal_idx < artifact_idx < ev_idx
    assert "downstream verification will consume artifact" in script


def test_postclose_wrapper_treats_stage_hook_fail_closed_as_report_artifact():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    producer_gap_idx = script.index("src.engine.automation.producer_gap_discovery")
    stage_hook_idx = script.index(
        "src.engine.automation.stage_hook_workorder_discovery"
    )
    nonfatal_idx = script.index(
        "stage hook workorder discovery returned fail-closed report (non-fatal)"
    )
    artifact_idx = script.index(
        '"$PROJECT_DIR/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_${TARGET_DATE}.json"'
    )
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert producer_gap_idx < stage_hook_idx < nonfatal_idx < artifact_idx < ev_idx
    assert "downstream verification will consume artifact" in script


def test_postclose_wrapper_runs_stage_hook_scaffold_before_workorder_ev():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    stage_hook_idx = script.index(
        "src.engine.automation.stage_hook_workorder_discovery"
    )
    scaffold_idx = script.index("src.engine.automation.stage_hook_runtime_scaffold")
    nonfatal_idx = script.index(
        "stage hook runtime scaffold returned fail-closed report (non-fatal)"
    )
    artifact_idx = script.index(
        '"$PROJECT_DIR/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_${TARGET_DATE}.json"'
    )
    ev_idx = script.index('run_threshold_cycle_ev_and_wait "pre_workorder"')

    assert stage_hook_idx < scaffold_idx < nonfatal_idx < artifact_idx < ev_idx


def test_postclose_wrapper_refreshes_market_breadth_before_panic_sell_report():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    breadth_idx = script.index("src.engine.market_panic_breadth_collector")
    breadth_wait_idx = script.index("market_panic_breadth_postclose")
    panic_sell_idx = script.index("src.engine.panic_sell_defense_report")

    assert (
        'RUN_MARKET_PANIC_BREADTH_REPORT="${THRESHOLD_CYCLE_RUN_MARKET_PANIC_BREADTH_REPORT:-true}"'
        in script
    )
    assert breadth_idx < breadth_wait_idx < panic_sell_idx
    assert "market_panic_breadth=$RUN_MARKET_PANIC_BREADTH_REPORT" in script


def test_panic_intraday_wrapper_separates_panic_and_market_weakness_alerts():
    script = Path("deploy/run_panic_sell_defense_intraday.sh").read_text(
        encoding="utf-8"
    )

    panic_idx = script.index("--kind panic_sell")
    weakness_idx = script.index("--kind market_weakness")

    assert panic_idx < weakness_idx
    assert (
        'MARKET_WEAKNESS_NOTIFY_AUDIENCE="${PANIC_MARKET_WEAKNESS_NOTIFY_AUDIENCE:-admin}"'
        in script
    )
    assert (
        'MARKET_WEAKNESS_NOTIFY_ENABLED="${PANIC_MARKET_WEAKNESS_NOTIFY_ENABLED:-true}"'
        in script
    )
    assert (
        'MARKET_WEAKNESS_STATE_FILE="${PANIC_MARKET_WEAKNESS_STATE_FILE:-$PROJECT_DIR/tmp/market_weakness_observer_state.json}"'
        in script
    )
    assert "weakness_notify_cmd+=(--observe-only)" in script
    assert script.count('--state-file "$NOTIFY_STATE_FILE"') == 1
    assert script.count('--state-file "$MARKET_WEAKNESS_STATE_FILE"') == 1


def test_postclose_wrapper_waits_for_prerequisite_artifacts_before_downstream_steps():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert 'ARTIFACT_WAIT_SEC="${THRESHOLD_CYCLE_ARTIFACT_WAIT_SEC:-600}"' in script
    assert (
        'AI_CORRECTION_MAX_ATTEMPTS="${THRESHOLD_CYCLE_AI_CORRECTION_MAX_ATTEMPTS:-2}"'
        in script
    )
    assert (
        'AI_CORRECTION_RETRY_DELAY_SEC="${THRESHOLD_CYCLE_AI_CORRECTION_RETRY_DELAY_SEC:-20}"'
        in script
    )
    assert (
        'AI_CORRECTION_REUSE_IF_VALID="${THRESHOLD_CYCLE_REUSE_AI_REVIEW_IF_VALID:-true}"'
        in script
    )
    assert "--reuse-ai-review-if-valid" in script
    assert "wait_for_json_artifact()" in script
    assert "wait_for_report_artifact()" in script
    assert "threshold_cycle_ai_review_status()" in script
    assert "next_stage2_checklist_path()" in script
    assert (
        '"$PROJECT_DIR/data/report/code_improvement_workorder/code_improvement_workorder_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/pattern_lab_ai_review/pattern_lab_ai_review_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/time_window_regime_counterfactual/time_window_regime_counterfactual_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/producer_gap_discovery/producer_gap_discovery_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/stage_hook_workorder_discovery/stage_hook_workorder_discovery_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/stage_hook_runtime_scaffold/stage_hook_runtime_scaffold_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_${TARGET_DATE}.json"'
        in script
    )
    action_outcome_calibration_idx = script.index(
        "src.engine.scalping.ai_action_outcome_calibration"
    )
    assert action_outcome_calibration_idx >= 0
    assert (
        '"$PROJECT_DIR/data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/entry_ai_gate_backtest/entry_ai_gate_backtest_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/scalping_pyramid_quality_calibration/scalping_pyramid_quality_calibration_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/scalping_avg_down_recovery_calibration/scalping_avg_down_recovery_calibration_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/rising_missed_classifier_prior/rising_missed_classifier_prior_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/one_share_threshold_opportunity/one_share_threshold_opportunity_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/runtime_apply_bridge/runtime_apply_bridge_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/runtime_approval_summary/runtime_approval_summary_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/tuning_performance_control_tower/tuning_performance_control_tower_${TARGET_DATE}.json"'
        in script
    )
    assert (
        '"$PROJECT_DIR/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_${TARGET_DATE}.json"'
        in script
    )
    assert (
        'wait_for_file_artifact "$(next_stage2_checklist_path)" "next_stage2_checklist"'
        in script
    )
    assert "src.engine.verify_threshold_cycle_postclose_chain" in script
    assert "--allow-pending-done-marker" in script
    assert (
        'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.verify_threshold_cycle_postclose_chain'
        in script
    )
    assert (
        'run_threshold_cycle_ev_and_wait "post_conversion_lane_workorder_refresh"'
        in script
    )
    final_ev_index = script.index(
        'run_threshold_cycle_ev_and_wait "final_consumer_refresh"'
    )
    final_workorder_index = script.index(
        '"code_improvement_workorder_final_source_refresh"', final_ev_index
    )
    final_runtime_index = script.index(
        '"runtime_approval_summary_final_refresh"', final_workorder_index
    )
    final_checklist_index = script.index(
        '"next_stage2_checklist_final_refresh"', final_runtime_index
    )
    pending_verify_index = script.index(
        'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m '
        "src.engine.verify_threshold_cycle_postclose_chain",
        final_checklist_index,
    )
    assert (
        final_ev_index
        < final_workorder_index
        < final_runtime_index
        < final_checklist_index
        < pending_verify_index
    )
    assert "runtime_approval_summary_post_conversion_lane_workorder" in script
    assert (
        '"$PROJECT_DIR/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json"'
        in script
    )
    assert "pattern_lab_currentness_audit=$RUN_PATTERN_LAB_CURRENTNESS_AUDIT" in script
    assert "pattern_lab_ai_review=$RUN_PATTERN_LAB_AI_REVIEW" in script
    assert "pattern_lab_ai_review_provider=$PATTERN_LAB_AI_REVIEW_PROVIDER" in script
    assert (
        "time_window_regime_counterfactual=$RUN_TIME_WINDOW_REGIME_COUNTERFACTUAL"
        in script
    )
    assert "producer_gap_discovery=$RUN_PRODUCER_GAP_DISCOVERY" in script
    assert (
        "producer_gap_discovery_ai_provider=$PRODUCER_GAP_DISCOVERY_AI_PROVIDER"
        in script
    )
    assert "--rolling-sim-scan" in script
    assert "pattern_lab_propagation_audit=$RUN_PATTERN_LAB_PROPAGATION_AUDIT" in script
    assert "scalp_entry_adm=$RUN_SCALP_ENTRY_ADM" in script
    assert "entry_ai_gate_backtest=$RUN_ENTRY_AI_GATE_BACKTEST" in script
    assert "tight_stop_entry_companion_report" not in script
    assert "scalp_sim_ai_deferred_review" not in script
    assert "THRESHOLD_CYCLE_RUN_QUOTE_CONSISTENCY_REPORT" not in script
    assert "src.engine.monitoring.quote_consistency_report" not in script
    assert "quote_consistency_report=$RUN_QUOTE_CONSISTENCY_REPORT" not in script
    assert "THRESHOLD_CYCLE_RUN_INTRADAY_WS_FRESHNESS_MONITOR" not in script
    assert "THRESHOLD_CYCLE_RUN_INTRADAY_WS_FRESHNESS_FINALIZE" in script
    assert "intraday_ws_freshness_finalize" in script
    assert '--symbol-master-path "$intraday_ws_symbol_master"' in script
    assert (
        'wait_for_json_artifact "$intraday_ws_symbol_master" '
        '"intraday_ws_freshness_symbol_master"'
        not in script
    )
    assert script.index("intraday_ws_freshness_finalize") < script.index(
        'run_threshold_cycle_ev_and_wait "pre_workorder"'
    )
    assert "ai_score_optimization_backtest" not in script
    assert (
        "rising_missed_intraday_feedback_postclose=$RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE"
        in script
    )
    assert "limit_down_watch_report=$RUN_LIMIT_DOWN_WATCH_REPORT" in script
    assert "rising_missed_scout_workorder=$RUN_RISING_MISSED_SCOUT_WORKORDER" in script
    assert "rising_missed_normal_buy_bridge_candidate_discovery" not in script
    assert "rising_missed_first_touch_calibration" not in script
    assert (
        "scalping_pyramid_intraday_feedback_postclose=$RUN_SCALPING_PYRAMID_INTRADAY_FEEDBACK_POSTCLOSE"
        in script
    )
    assert (
        "scalping_pyramid_quality_calibration=$RUN_SCALPING_PYRAMID_QUALITY_CALIBRATION"
        in script
    )
    assert (
        "scalping_avg_down_recovery_calibration=$RUN_SCALPING_AVG_DOWN_RECOVERY_CALIBRATION"
        in script
    )
    assert (
        "rising_missed_classifier_prior=$RUN_RISING_MISSED_CLASSIFIER_PRIOR" in script
    )
    assert (
        "one_share_threshold_opportunity=$RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY" in script
    )
    assert (
        "one_share_threshold_opportunity_ai_provider=$ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER"
        in script
    )
    assert "lifecycle_decision_matrix=$RUN_LIFECYCLE_DECISION_MATRIX" in script
    assert "lifecycle_bucket_discovery=$RUN_LIFECYCLE_BUCKET_DISCOVERY" in script
    assert "runtime_apply_bridge=$RUN_RUNTIME_APPLY_BRIDGE" in script
    assert (
        "tuning_performance_control_tower=$RUN_TUNING_PERFORMANCE_CONTROL_TOWER"
        in script
    )
    assert "runtime_apply_gap_audit=true" in script
    assert "swing_lifecycle_matrix=$RUN_SWING_LIFECYCLE_MATRIX" in script
    assert (
        "swing_lifecycle_bucket_discovery=$RUN_SWING_LIFECYCLE_BUCKET_DISCOVERY"
        in script
    )
    assert (
        'SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER="${KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER:-$SWING_THRESHOLD_AI_REVIEW_PROVIDER}"'
        in script
    )
    assert '--ai-provider "$SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER"' in script
    assert (
        "swing_lifecycle_bucket_discovery_ai_provider=$SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER"
        in script
    )
    assert "ai correction retry target_date=$TARGET_DATE" in script
    assert "ai correction final unavailable" in script


def test_stage2_ops_cron_installs_pyramid_intraday_feedback_5min():
    script = Path("deploy/install_stage2_ops_cron.sh").read_text(encoding="utf-8")

    assert "SCALPING_PYRAMID_INTRADAY_FEEDBACK_5MIN" in script
    assert "deploy/run_scalping_pyramid_intraday_feedback.sh" in script
    assert "!/SCALPING_PYRAMID_INTRADAY_FEEDBACK_5MIN/" in script


def test_stage2_ops_cron_extends_ws_freshness_monitor_into_nxt_open():
    script = Path("deploy/install_stage2_ops_cron.sh").read_text(encoding="utf-8")

    assert (
        "*/5 16-18 * * 1-5 "
        "$PROJECT_DIR/deploy/run_intraday_ws_freshness_monitor.sh" in script
    )
    assert (
        "0,5,10,15,20 19 * * 1-5 "
        "$PROJECT_DIR/deploy/run_intraday_ws_freshness_monitor.sh" in script
    )
    assert "!/INTRADAY_WS_FRESHNESS_MONITOR_5MIN/" in script
    assert "!/INTRADAY_WS_FRESHNESS_MONITOR_NXT_5MIN/" in script


def test_stage2_ops_cron_owns_main_sentinels_through_nxt_session():
    script = Path("deploy/install_stage2_ops_cron.sh").read_text(encoding="utf-8")

    assert "!/BUY_FUNNEL_SENTINEL_/" in script
    assert "!/HOLDING_EXIT_SENTINEL_/" in script
    assert (
        "*/5 16-18 * * 1-5 "
        "$PROJECT_DIR/deploy/run_buy_funnel_sentinel_intraday.sh" in script
    )
    assert (
        "0-20/5 19 * * 1-5 "
        "$PROJECT_DIR/deploy/run_buy_funnel_sentinel_intraday.sh" in script
    )
    assert (
        "*/5 16-18 * * 1-5 "
        "$PROJECT_DIR/deploy/run_holding_exit_sentinel_intraday.sh" in script
    )
    assert (
        "0-20/5 19 * * 1-5 "
        "$PROJECT_DIR/deploy/run_holding_exit_sentinel_intraday.sh" in script
    )
    assert "BUY_FUNNEL_SENTINEL_NXT_1600_1855" in script
    assert "HOLDING_EXIT_SENTINEL_NXT_1600_1855" in script


def test_market_opportunity_census_wrapper_and_installer_are_source_only():
    wrapper = Path("deploy/run_market_opportunity_census_intraday.sh").read_text(
        encoding="utf-8"
    )
    installer = Path("deploy/install_market_opportunity_census_cron.sh").read_text(
        encoding="utf-8"
    )

    assert "--capture-only" in wrapper
    assert "--panels all,liquid_common" in wrapper
    assert 'venues="NXT"' in wrapper
    assert 'venues="KRX,NXT"' in wrapper
    assert "0915|1200|1515|1945" in wrapper
    assert "ionice -c2 -n7 nice -n 15" in wrapper
    assert "runtime_effect=false" in wrapper
    assert "MARKET_OPPORTUNITY_CENSUS_NXT_PREMARKET_5MIN" in installer
    assert "MARKET_OPPORTUNITY_CENSUS_KRX_NXT_5MIN" in installer
    assert "MARKET_OPPORTUNITY_CENSUS_KRX_NXT_CLOSE_5MIN" in installer
    assert "MARKET_OPPORTUNITY_CENSUS_NXT_TRANSITION_5MIN" in installer
    assert "MARKET_OPPORTUNITY_CENSUS_NXT_AFTERMARKET_5MIN" in installer
    assert "awk '!/MARKET_OPPORTUNITY_CENSUS_/'" in installer
    assert "SYSTEM_TIMEZONE" in installer
    assert '"Asia/Seoul"' in installer
    assert '"runtime_effect": False' in installer
    assert '"allowed_runtime_apply": False' in installer
    assert '"actual_order_submitted": False' in installer
    assert '"broker_order_forbidden": True' in installer


def test_stage2_ops_cron_uses_light_snapshot_at_noon():
    script = Path("deploy/install_stage2_ops_cron.sh").read_text(encoding="utf-8")

    noon_line = next(
        line
        for line in script.splitlines()
        if line.startswith("0 12 ") and "RUN_MONITOR_SNAPSHOT_1200" in line
    )
    assert "run_monitor_snapshot_incremental_cron.sh" in noon_line
    assert "MONITOR_SNAPSHOT_START_JITTER_SEC=0" in noon_line
    assert "run_monitor_snapshot_cron.sh" not in noon_line


def test_monitor_snapshot_resource_exit_is_not_immediately_retried():
    script = Path("deploy/run_monitor_snapshot_safe.sh").read_text(encoding="utf-8")

    assert "124|130|137|143) non_retryable_resource_exit=1" in script
    assert '"MemoryError"' in script
    assert '"$non_retryable_resource_exit" -ne 1' in script
    assert "stopped without retry after resource/external exit" in script
    assert "monitor_snapshot_stage_(start|complete)" in script
    assert script.count('write_completion_artifact "" "$output_file" "$$"') == 2
    assert script.index('"MemoryError"') < script.index('rm -f "$attempt_output"')


def test_growing_pipeline_wrappers_bound_cadence_and_cpu_affinity():
    expectations = {
        "deploy/run_rising_missed_intraday_feedback.sh": (
            "RISING_MISSED_INTRADAY_FEEDBACK_COOLDOWN_SEC:-1500",
            "RISING_MISSED_INTRADAY_FEEDBACK_CPU_AFFINITY",
        ),
        "deploy/run_scalping_pyramid_intraday_feedback.sh": (
            "SCALPING_PYRAMID_INTRADAY_FEEDBACK_COOLDOWN_SEC:-720",
            "SCALPING_PYRAMID_INTRADAY_FEEDBACK_CPU_AFFINITY",
        ),
        "deploy/run_intraday_ws_freshness_monitor.sh": (
            "INTRADAY_WS_FRESHNESS_MONITOR_COOLDOWN_SEC:-720",
            "INTRADAY_WS_FRESHNESS_MONITOR_CPU_AFFINITY",
        ),
    }
    for path, (cooldown_contract, affinity_contract) in expectations.items():
        script = Path(path).read_text(encoding="utf-8")
        assert cooldown_contract in script
        assert "korstockscan_default_cpu_affinity monitor" in script
        assert affinity_contract in script
        assert 'taskset -c "$CPU_AFFINITY"' in script
        if "intraday_feedback.sh" in path:
            assert "KORSTOCKSCAN_INTRADAY_HEAVY_ANALYSIS_LOCK_FILE" in script
            assert "flock -n 8" in script
    ws_script = Path("deploy/run_intraday_ws_freshness_monitor.sh").read_text(
        encoding="utf-8"
    )
    assert "INTRADAY_WS_FRESHNESS_MONITOR_INCREMENTAL_STATE_PATH" in ws_script
    assert '--incremental-state-path "$INCREMENTAL_STATE_PATH"' in ws_script


def test_postclose_wrapper_marks_availability_guard_pause_as_fail():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert 'MAX_ITERATIONS="${THRESHOLD_CYCLE_MAX_ITERATIONS:-320}"' in script
    assert "[PAUSED] threshold-cycle postclose" in script
    assert "[FAIL] threshold-cycle postclose" in script
    assert "paused_by_availability_guard" in script
    assert "for line in reversed(sys.stdin.read().splitlines())" in script
    assert "backfill summary JSON object missing from stdout" in script
    assert 'completed="$(printf \'%s\' "$summary_json"' in script
    assert 'if [ "${completed:-false}" != "true" ]; then' in script
    assert "compact collection incomplete" in script
    assert 'failure_reason="compact_collection_incomplete:${status:-unknown}"' in script
    assert 'write_postclose_status failed "$failure_reason" 2 1' in script


def test_postclose_wrapper_reuses_existing_snapshot_when_checkpoint_exists():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'CHECKPOINT_PATH="$PROJECT_DIR/data/threshold_cycle/checkpoints/${TARGET_DATE}.json"'
        in script
    )
    assert 'MAX_CPU_BUSY_PCT="${THRESHOLD_CYCLE_MAX_CPU_BUSY_PCT:-95}"' in script
    assert '-name "pipeline_events_${TARGET_DATE}_*.jsonl.gz"' in script
    assert '--max-cpu-busy-pct "$MAX_CPU_BUSY_PCT"' in script
    assert '[ -f "$CHECKPOINT_PATH" ] && [ -n "$EXISTING_SNAPSHOT_PATH" ]' in script
    assert (
        'echo "[threshold-cycle] reusing immutable snapshot source=$EXISTING_SNAPSHOT_PATH checkpoint=$CHECKPOINT_PATH"'
        in script
    )
    assert '[ "${REUSE_EXISTING_SNAPSHOT:-false}" != "true" ]' in script
    assert (
        'SNAPSHOT_PATH="$SNAPSHOT_DIR/pipeline_events_${TARGET_DATE}_${SNAPSHOT_TS}.jsonl.gz"'
        in script
    )
    assert (
        'run_postclose_cmd gzip -1 -c -- "$RAW_SOURCE" > "$SNAPSHOT_TEMP_PATH"'
        in script
    )
    assert 'mv -- "$SNAPSHOT_TEMP_PATH" "$SNAPSHOT_PATH"' in script
    assert 'cp --reflink=auto "$RAW_SOURCE" "$SNAPSHOT_PATH"' not in script
    assert "cleanup_threshold_cycle_snapshot_temp()" in script
    assert "removing orphan snapshot without checkpoint" in script


def test_postclose_wrapper_resource_guards_heavy_steps():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'POSTCLOSE_RESOURCE_GUARD="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_GUARD:-true}"'
        in script
    )
    assert (
        'POSTCLOSE_NICE_LEVEL="${THRESHOLD_CYCLE_POSTCLOSE_NICE_LEVEL:-10}"' in script
    )
    assert (
        'POSTCLOSE_IONICE_LEVEL="${THRESHOLD_CYCLE_POSTCLOSE_IONICE_LEVEL:-7}"'
        in script
    )
    assert (
        'POSTCLOSE_MIN_SWAP_FREE_MB="${THRESHOLD_CYCLE_POSTCLOSE_MIN_SWAP_FREE_MB:-256}"'
        in script
    )
    assert (
        'POSTCLOSE_MAX_SAMPLE_AGE_SEC="${THRESHOLD_CYCLE_POSTCLOSE_MAX_SAMPLE_AGE_SEC:-180}"'
        in script
    )
    assert 'POSTCLOSE_MAX_LOAD1="${THRESHOLD_CYCLE_POSTCLOSE_MAX_LOAD1:-64}"' in script
    assert (
        'POSTCLOSE_BOT_ACTION="${THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION:-none}"' in script
    )
    assert (
        'COMPACT_AVAILABILITY_WAIT_SEC="${THRESHOLD_CYCLE_COMPACT_AVAILABILITY_WAIT_SEC:-900}"'
        in script
    )
    assert "run_postclose_cmd()" in script
    assert "mark_postclose_failed()" in script
    assert "stop_postclose_bot_if_requested()" in script
    assert "restart_postclose_bot_if_requested()" in script
    assert "stopping bot for postclose resource isolation" in script
    assert "restarting bot after postclose" in script
    assert "starting bot after postclose" in script
    assert "reason=restart_action_requested" in script
    assert "wait_for_postclose_resources()" in script
    assert "refresh_postclose_resource_sample_if_stale()" in script
    assert (
        'POSTCLOSE_RESOURCE_AUTO_REFRESH_SAMPLER="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_AUTO_REFRESH_SAMPLER:-true}"'
        in script
    )
    assert (
        'POSTCLOSE_RESOURCE_SAMPLER_CMD="${THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_SAMPLER_CMD:-$PROJECT_DIR/deploy/run_system_metric_sampler_cron.sh}"'
        in script
    )
    assert 'item.startswith("sample_age_sec=")' in script
    assert 'item in {"sampler_missing", "sampler_empty"}' in script
    assert "resource sampler refreshed" in script
    assert "resource sampler refresh failed" in script
    assert "sample_age_sec=" in script
    assert "swap_free_mb=" in script
    assert "cpu_busy_pct=" in script
    assert "load1=" in script
    assert "sampler_missing" in script
    assert "availability guard wait" in script
    assert 'wait_for_postclose_resources "daily_threshold_cycle_report"' in script
    assert 'wait_for_postclose_resources "swing_lifecycle_audit"' in script
    assert 'wait_for_postclose_resources "gemini_scalping_pattern_lab"' not in script
    assert 'wait_for_postclose_resources "threshold_cycle_ev_${pass_label}"' in script
    assert (
        'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.backfill_threshold_cycle_events'
        in script
    )
    assert (
        'run_postclose_cmd env PYTHONPATH=. "$VENV_PY" -m src.engine.daily_threshold_cycle_report'
        in script
    )


def test_manual_calibration_wrapper_limits_resource_pressure():
    script = Path("deploy/run_threshold_cycle_calibration.sh").read_text(
        encoding="utf-8"
    )
    installer = Path("deploy/install_threshold_cycle_cron.sh").read_text(
        encoding="utf-8"
    )

    assert 'RUN_PHASE="${THRESHOLD_CYCLE_CALIBRATION_PHASE:-postclose}"' in script
    assert (
        'CALIBRATION_TIMEOUT_SEC="${THRESHOLD_CYCLE_CALIBRATION_TIMEOUT_SEC:-600}"'
        in script
    )
    assert (
        'LOCK_FILE="${THRESHOLD_CYCLE_CALIBRATION_LOCK_FILE:-$PROJECT_DIR/tmp/threshold_cycle_calibration_${RUN_PHASE}.lock}"'
        in script
    )
    assert 'IONICE_LEVEL="${THRESHOLD_CYCLE_CALIBRATION_IONICE_LEVEL:-7}"' in script
    assert 'NICE_LEVEL="${THRESHOLD_CYCLE_CALIBRATION_NICE_LEVEL:-12}"' in script
    assert "flock -n 9" in script
    assert 'timeout --kill-after=30s "$CALIBRATION_TIMEOUT_SEC"' in script
    assert "5 12 * * 1-5" not in installer
    assert "deploy/run_threshold_cycle_calibration.sh" not in installer
    assert "threshold_cycle_calibration_intraday_cron.log" not in installer


def test_threshold_cycle_cron_stops_bot_for_postclose_without_restart():
    script = Path("deploy/install_threshold_cycle_cron.sh").read_text(encoding="utf-8")

    assert "THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop" in script
    assert "THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=restart" not in script
    assert "THRESHOLD_CYCLE_POSTCLOSE" in script


def test_postclose_wrapper_cleans_up_snapshot_duplicates_with_retention():
    script = Path("deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    assert (
        'SNAPSHOT_RETENTION_DAYS="${THRESHOLD_CYCLE_SNAPSHOT_RETENTION_DAYS:-7}"'
        in script
    )
    assert "cleanup_threshold_cycle_snapshots()" in script
    assert (
        'cleanup_threshold_cycle_snapshots "$SNAPSHOT_DIR" "$SNAPSHOT_RETENTION_DAYS"'
        in script
    )
    assert (
        "pipeline_events_(\\d{4}-\\d{2}-\\d{2})_(\\d{8}_\\d{6})\\.jsonl(?:\\.gz)?$"
        in script
    )
    assert "retention_days={retention_days}" in script
    assert "removed_bytes={removed_bytes}" in script


def test_tuning_monitoring_wrapper_skips_pattern_labs_by_default():
    script = Path("deploy/run_tuning_monitoring_postclose.sh").read_text(
        encoding="utf-8"
    )

    assert 'RUN_PATTERN_LABS="${TUNING_MONITORING_RUN_PATTERN_LABS:-false}"' in script
    assert "canonical_runner=THRESHOLD_CYCLE_POSTCLOSE" in script
    assert (
        'if [[ "$RUN_PATTERN_LABS" == "1" || "$RUN_PATTERN_LABS" == "true" ]]' in script
    )
    assert "analysis/gemini_scalping_pattern_lab/run.sh" not in script
    assert (
        'record_step "gemini_scalping_pattern_lab" "skipped" 0 0 "retired_from_automatic_execution"'
        in script
    )
    assert (
        'RUN_VERIFIED_ARCHIVE="${TUNING_MONITORING_RUN_VERIFIED_ARCHIVE:-true}"'
        in script
    )
    parquet_idx = script.index('"build_parquet_pipeline_events"')
    archive_idx = script.index('"compress_verified_dashboard_sources"')
    assert parquet_idx < archive_idx
    assert "src.engine.compress_db_backfilled_files" in script
    assert '--date "$TARGET_DATE"' in script


def test_calibration_wrapper_retries_and_fails_unavailable_ai_correction():
    script = Path("deploy/run_threshold_cycle_calibration.sh").read_text(
        encoding="utf-8"
    )

    assert (
        'AI_CORRECTION_MAX_ATTEMPTS="${THRESHOLD_CYCLE_AI_CORRECTION_MAX_ATTEMPTS:-2}"'
        in script
    )
    assert (
        'AI_CORRECTION_RETRY_DELAY_SEC="${THRESHOLD_CYCLE_AI_CORRECTION_RETRY_DELAY_SEC:-20}"'
        in script
    )
    assert (
        'AI_CORRECTION_REUSE_IF_VALID="${THRESHOLD_CYCLE_REUSE_AI_REVIEW_IF_VALID:-true}"'
        in script
    )
    assert "--reuse-ai-review-if-valid" in script
    assert "threshold_cycle_ai_review_status()" in script
    assert "ai correction retry target_date=$TARGET_DATE phase=$RUN_PHASE" in script
    assert (
        "ai correction final unavailable target_date=$TARGET_DATE phase=$RUN_PHASE"
        in script
    )
    assert "exit 1" in script


def test_tuning_monitoring_waits_for_threshold_postclose_done_by_default():
    script = Path("deploy/run_tuning_monitoring_postclose.sh").read_text(
        encoding="utf-8"
    )

    assert (
        'REQUIRE_THRESHOLD_POSTCLOSE_DONE="${TUNING_MONITORING_REQUIRE_THRESHOLD_POSTCLOSE_DONE:-true}"'
        in script
    )
    assert "wait_for_threshold_postclose_done" in script
    assert "threshold_postclose_terminal_marker" in script
    assert "reason=threshold_cycle_postclose_not_done" in script
    assert "reason=threshold_cycle_postclose_failed waited=${waited}s" in script
    assert "predecessor failed; waiting for recovery" in script
    failed_start = script.index("failed)")
    failed_branch = script[failed_start : script.index("        ;;", failed_start)]
    assert 'if [[ "$waited" -ge "$PREDECESSOR_WAIT_SEC" ]]' in failed_branch
    assert "reason=threshold_cycle_postclose_failed waited=${waited}s" in failed_branch
    assert "predecessor failed; waiting for recovery" in failed_branch
    assert "TUNING_MONITORING_PREDECESSOR_WAIT_SEC:-43200" in script


def test_run_bot_waits_for_threshold_runtime_env_before_launching_bot():
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    assert "unset KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED" in script
    assert script.index("unset KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED") < script.index(
        'if [ -f "$THRESHOLD_RUNTIME_ENV" ]'
    )
    assert script.rindex("unset KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED") > script.index(
        "verify_threshold_runtime_env_handoff"
    )

    assert "wait_for_threshold_runtime_env" in script
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_REQUIRED" in script
    assert "KORSTOCKSCAN_THRESHOLD_RUNTIME_ENV_BOOTSTRAP" in script
    assert "./deploy/run_threshold_cycle_preopen.sh" in script
    assert "threshold runtime env 미생성으로 봇 기동 중단" in script
    assert script.index(
        'wait_for_threshold_runtime_env "$THRESHOLD_RUNTIME_ENV"'
    ) < script.index("../.venv/bin/python bot_main.py")
    assert "operator_runtime_overrides.env" in script
    assert script.index(
        'OPERATOR_RUNTIME_OVERRIDES="../data/threshold_cycle/runtime_env/operator_runtime_overrides.env"'
    ) > script.index('. "$THRESHOLD_RUNTIME_ENV"')
    assert script.index('. "$OPERATOR_RUNTIME_OVERRIDES"') < script.index(
        "../.venv/bin/python bot_main.py"
    )
    assert "operator_runtime_overrides_${RUNTIME_TARGET_DATE}.env" in script
    assert "KORSTOCKSCAN_OPENAI_HOLDING_SCORE_MODEL=gpt-5.4-nano" in script
    assert (
        'export KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED="${KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED:-true}"'
        in script
    )
    assert "KORSTOCKSCAN_OPENAI_HOLDING_FLOW_MODEL=gpt-5.4-mini" in script
    assert "KORSTOCKSCAN_OPENAI_HOLDING_FLOW_TIMEOUT_MS=15000" in script
    assert (
        "KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=holding_flow" in script
    )
    assert "KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_FAMILY=lite_v2" in script
    assert "KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE=off" in script
    assert script.index('. "$DATED_OPERATOR_RUNTIME_OVERRIDES"') < script.index(
        'renew_enabled_dated_runtime_overrides "$RUNTIME_TARGET_DATE"'
    )
    assert script.index(
        'renew_enabled_dated_runtime_overrides "$RUNTIME_TARGET_DATE"'
    ) < script.index('disable_expired_dated_runtime_overrides "$RUNTIME_TARGET_DATE"')
    assert script.index(
        'disable_expired_dated_runtime_overrides "$RUNTIME_TARGET_DATE"'
    ) < script.index('record_enabled_dated_runtime_provenance "$RUNTIME_TARGET_DATE"')
    assert "renew_enabled_dated_runtime_overrides" in script
    assert "apply_authoritative_ai_context_promotion" in script
    assert "--mode runtime-env-exports" in script
    assert script.index(
        'apply_authoritative_ai_context_promotion "$RUNTIME_TARGET_DATE"'
    ) > script.index('disable_expired_dated_runtime_overrides "$RUNTIME_TARGET_DATE"')
    assert script.index(
        'apply_authoritative_ai_context_promotion "$RUNTIME_TARGET_DATE"'
    ) < script.index('verify_threshold_runtime_env_handoff "$RUNTIME_TARGET_DATE"')
    assert "disable_expired_dated_runtime_overrides" in script
    assert "reset_runtime_policy_env_before_handoff" in script
    assert script.index("reset_runtime_policy_env_before_handoff") < script.index(
        '. "$THRESHOLD_RUNTIME_ENV"'
    )
    assert 'disable_expired_dated_runtime_overrides "$RUNTIME_TARGET_DATE"' in script
    assert "verify_threshold_runtime_env_handoff" in script
    assert "KORSTOCKSCAN_INVEST_RATIO_SCALPING_MAX=0.25" in script
    assert "central" in script and "five-tier allocator" in script
    assert script.index(
        'verify_threshold_runtime_env_handoff "$RUNTIME_TARGET_DATE"'
    ) > script.index('disable_expired_dated_runtime_overrides "$RUNTIME_TARGET_DATE"')
    assert script.index(
        'verify_threshold_runtime_env_handoff "$RUNTIME_TARGET_DATE"'
    ) < script.index("../.venv/bin/python bot_main.py")
    assert "export_runtime_source_provenance" in script
    assert 'git -C "$PROJECT_DIR" rev-parse --verify HEAD' in script
    assert (
        'git -C "$PROJECT_DIR" status --porcelain --untracked-files=normal -- src deploy'
        in script
    )
    assert 'export KORSTOCKSCAN_RUNTIME_GIT_COMMIT="$commit"' in script
    assert (
        "export KORSTOCKSCAN_RUNTIME_LAUNCHER_GIT_COMMIT="
        '"$LAUNCHER_SOURCE_GIT_COMMIT"' in script
    )
    assert (
        "export KORSTOCKSCAN_RUNTIME_LAUNCHER_RUN_BOT_SHA256="
        '"$LAUNCHER_SOURCE_RUN_BOT_SHA256"' in script
    )
    assert (
        "export KORSTOCKSCAN_RUNTIME_LAUNCHER_LOADED_AT_KST="
        '"$LAUNCHER_SOURCE_LOADED_AT_KST"' in script
    )
    assert 'sha256sum "${BASH_SOURCE[0]}"' in script
    assert "readonly LAUNCHER_SOURCE_GIT_COMMIT" in script
    assert "readonly LAUNCHER_SOURCE_RUN_BOT_SHA256" in script
    assert 'export KORSTOCKSCAN_RUNTIME_SOURCE_ROOT="$PROJECT_DIR"' in script
    assert 'export KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY="$source_dirty"' in script
    assert "KORSTOCKSCAN_RUNTIME_STARTED_AT_KST" in script
    verify_call_index = script.index(
        'verify_threshold_runtime_env_handoff "$RUNTIME_TARGET_DATE" || exit 1'
    )
    retired_unset_index = script.rindex("unset KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED")
    provenance_export_index = script.index(
        "export_runtime_source_provenance", verify_call_index
    )
    assert verify_call_index < retired_unset_index < provenance_export_index
    assert (
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED:KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE:"
        in script
    )
    assert (
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED:"
        "KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE:"
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED" in script
    )
    assert (
        "KORSTOCKSCAN_NXT_RISING_MISSED_PARTIAL_FILL_REPRICE_ENABLED:"
        "KORSTOCKSCAN_NXT_RISING_MISSED_PARTIAL_FILL_REPRICE_ACTIVE_DATE:" in script
    )
    assert (
        "KORSTOCKSCAN_NXT_RISING_MISSED_TP1_CONTEXT_REFRESH_ENABLED:"
        "KORSTOCKSCAN_NXT_RISING_MISSED_TP1_CONTEXT_REFRESH_ACTIVE_DATE:"
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED" in script
    )
    assert (
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_REST_FALLBACK_ENABLED:"
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_REST_FALLBACK_ACTIVE_DATE:"
        "KORSTOCKSCAN_RISING_MISSED_NXT_POST_BLOCK_SAMPLER_ENABLED" in script
    )
    assert (
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED:KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE:"
        in script
    )
    assert (
        "KORSTOCKSCAN_RISING_MISSED_NXT_PRICE_JUMP_RECOVERY_ENABLED:"
        "KORSTOCKSCAN_RISING_MISSED_NXT_PRICE_JUMP_RECOVERY_ACTIVE_DATE:"
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED" in script
    )
    assert (
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ENABLED:KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_ACTIVE_DATE:"
        in script
    )
    assert (
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED:"
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE" not in script
    )
    assert "unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED" in script
    assert (
        "unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE"
        in script
    )
    assert (
        "unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC"
        in script
    )
    assert "unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC" in script
    assert (
        "unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS"
        in script
    )
    assert (
        script.count(
            "unset KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED"
        )
        == 2
    )
    assert (
        "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_ENABLED:KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_ACTIVE_DATE:"
        in script
    )
    assert (
        "KORSTOCKSCAN_SCALP_TRAILING_LOSS_CONVERSION_RECHECK_ENABLED:"
        "KORSTOCKSCAN_SCALP_TRAILING_LOSS_CONVERSION_RECHECK_ACTIVE_DATE:" in script
    )
    assert script.index(
        'BOT_CPU_AFFINITY="${KORSTOCKSCAN_BOT_CPU_AFFINITY:-$DEFAULT_BOT_CPU_AFFINITY}"'
    ) > script.index('. "$OPERATOR_RUNTIME_OVERRIDES"')


def test_run_bot_auto_renews_allowlisted_override_without_renewing_removed_family():
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    function_block = script[
        script.index("korstockscan_env_true()") : script.index(
            "disable_expired_dated_runtime_overrides()"
        )
    ]
    result = subprocess.run(
        [
            "bash",
            "-c",
            function_block + """
export KORSTOCKSCAN_DATED_RUNTIME_AUTO_RENEW_ENABLED=true
export KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED=true
export KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE=2026-07-30
export KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED=true
export KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ACTIVE_DATE=2026-07-30
export KORSTOCKSCAN_REMOVED_FAMILY_ENABLED=true
export KORSTOCKSCAN_REMOVED_FAMILY_ACTIVE_DATE=2026-07-30
export KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED=true
unset KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ACTIVE_DATE
export KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED=true
unset KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE
renew_enabled_dated_runtime_overrides 2026-07-31 >/dev/null
record_enabled_dated_runtime_provenance 2026-07-31 >/dev/null
printf '%s|%s|%s|%s|%s|%s|%s|%s|%s\\n' \
  "$KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE" \
  "$KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ACTIVE_DATE" \
  "$KORSTOCKSCAN_REMOVED_FAMILY_ENABLED" \
  "$KORSTOCKSCAN_REMOVED_FAMILY_ACTIVE_DATE" \
  "$KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ACTIVE_DATE" \
  "$KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE" \
  "$KORSTOCKSCAN_DATED_RUNTIME_AUTO_RENEW_ACTIVE_COUNT" \
  "$KORSTOCKSCAN_DATED_RUNTIME_AUTO_RENEW_RENEWED_KEYS" \
  "$KORSTOCKSCAN_DATED_RUNTIME_AUTO_RENEW_ACTIVE_DATE_PROVENANCE"
""",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    parts = result.stdout.strip().split("|")
    assert parts[:7] == [
        "2026-07-31",
        "2026-07-31",
        "true",
        "2026-07-30",
        "2026-07-31",
        "2026-07-31",
        "4",
    ]
    assert parts[7].split(",") == [
        "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED",
        "KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED",
        "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED",
        "KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED",
    ]
    provenance = parts[8].split(",")
    assert (
        "KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED:2026-07-31:"
        "source=launcher_auto_renew"
    ) in provenance
    assert (
        "KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED:2026-07-31:"
        "source=launcher_auto_renew"
    ) in provenance
    assert all("missing" not in item for item in provenance)


def test_run_bot_dated_auto_renew_registry_matches_handoff_verifier_registry():
    import re

    from src.engine.threshold_cycle_preopen_apply import DATED_RUNTIME_OVERRIDE_SPECS

    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    registry_block = script[
        script.index("DATED_RUNTIME_AUTO_RENEW_SPECS=(") : script.index(
            "\n)\n\nrenew_enabled_dated_runtime_overrides"
        )
    ]
    shell_specs = set(re.findall(r'"([^":]+):([^"\n]+)"', registry_block))
    verifier_specs = {
        (spec["enabled_key"], spec["active_date_key"])
        for spec in DATED_RUNTIME_OVERRIDE_SPECS
        if spec.get("auto_renew") is not False
    }

    assert len(shell_specs) == 22
    assert shell_specs == verifier_specs


def test_run_bot_winner_recovery_is_reset_and_not_auto_renewed():
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    renewal_registry = script[
        script.index("DATED_RUNTIME_AUTO_RENEW_SPECS=(") : script.index(
            "\n)\n\nrenew_enabled_dated_runtime_overrides"
        )
    ]
    reset_block = script[
        script.index("reset_runtime_policy_env_before_handoff()") : script.index(
            "\n}\n\n# 무한 루프 시작",
            script.index("reset_runtime_policy_env_before_handoff()"),
        )
    ]
    expired_block = script[
        script.index("disable_expired_dated_runtime_overrides()") : script.index(
            "\n}\n\nverify_threshold_runtime_env_handoff",
            script.index("disable_expired_dated_runtime_overrides()"),
        )
    ]

    assert "SCALP_POST_PROBE_WINNER_RECOVERY" not in renewal_registry
    for suffix in (
        "ENABLED",
        "ACTIVE_DATE",
        "KRX_ENABLED",
        "NXT_ENABLED",
        "PREMARKET_ENABLED",
    ):
        assert (
            f"unset KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_{suffix}"
            in reset_block
        )
    assert (
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ENABLED:"
        "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_ACTIVE_DATE:"
    ) in expired_block


def test_run_bot_does_not_auto_renew_without_explicit_operator_authority():
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    function_block = script[
        script.index("korstockscan_env_true()") : script.index(
            "disable_expired_dated_runtime_overrides()"
        )
    ]
    result = subprocess.run(
        [
            "bash",
            "-c",
            function_block + """
export KORSTOCKSCAN_DATED_RUNTIME_AUTO_RENEW_ENABLED=false
export KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED=true
export KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE=2026-07-30
renew_enabled_dated_runtime_overrides 2026-07-31 >/dev/null
printf '%s\\n' "$KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE"
""",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == "2026-07-30"


def test_run_bot_expiry_uses_tp1_source_gap_relief_own_active_date():
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    function_block = script[
        script.index("korstockscan_env_true()") : script.index(
            "verify_threshold_runtime_env_handoff()"
        )
    ]
    result = subprocess.run(
        [
            "bash",
            "-c",
            function_block + """
export KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED=true
export KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE=2026-08-03
export KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED=true
export KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ACTIVE_DATE=2026-08-02
disable_expired_dated_runtime_overrides 2026-08-03 >/dev/null
printf '%s|%s\n' \
  "$KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED" \
  "$KORSTOCKSCAN_RISING_MISSED_TP1_SOURCE_GAP_RELIEF_ENABLED"
""",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == "true|false"


def test_run_bot_preserves_existing_daily_entry_split_contract_and_disables_expired_guard(
    tmp_path,
):
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    function_block = script[
        script.index("korstockscan_env_true()") : script.index(
            "verify_threshold_runtime_env_handoff()"
        )
    ]
    policy_path = tmp_path / "entry_split_policy.json"
    policy_path.write_text("{}\n", encoding="utf-8")
    result = subprocess.run(
        [
            "bash",
            "-c",
            function_block + f"""
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED=true
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_ACTIVE_DATE=DAILY
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE={policy_path}
export KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED=true
unset KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE
export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=true
export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE=DAILY
export KORSTOCKSCAN_NXT_RISING_MISSED_TP1_PARTIAL_RUNNER_ENABLED=true
export KORSTOCKSCAN_NXT_RISING_MISSED_TP1_PARTIAL_RUNNER_ACTIVE_DATE=2026-07-30
disable_expired_dated_runtime_overrides 2026-08-03 >/dev/null
printf '%s|%s|%s\n' \
  "$KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED" \
  "$KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED" \
  "$KORSTOCKSCAN_NXT_RISING_MISSED_TP1_PARTIAL_RUNNER_ENABLED"
""",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == "true|true|false"


def test_run_bot_daily_entry_split_contract_satisfies_probe_policy_dependency(
    tmp_path,
):
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    function_block = script[
        script.index("korstockscan_env_true()") : script.index(
            "verify_threshold_runtime_env_handoff()"
        )
    ]
    policy_path = tmp_path / "entry_split_policy.json"
    policy_path.write_text("{}\n", encoding="utf-8")
    result = subprocess.run(
        [
            "bash",
            "-c",
            function_block + f"""
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED=true
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_ACTIVE_DATE=DAILY
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE={policy_path}
export KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED=false
unset KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE
export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=true
export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE=DAILY
disable_expired_dated_runtime_overrides 2026-08-25 >/dev/null
printf '%s|%s\n' \
  "$KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED" \
  "$KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED"
""",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == "false|true"


def test_run_bot_disables_daily_entry_split_when_baseline_policy_is_missing(tmp_path):
    script = Path("src/run_bot.sh").read_text(encoding="utf-8")
    function_block = script[
        script.index("korstockscan_env_true()") : script.index(
            "verify_threshold_runtime_env_handoff()"
        )
    ]
    missing_policy_path = tmp_path / "missing.json"
    result = subprocess.run(
        [
            "bash",
            "-c",
            function_block + f"""
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED=true
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_ACTIVE_DATE=DAILY
export KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE={missing_policy_path}
export KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED=true
unset KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE
export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=true
export KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE=DAILY
disable_expired_dated_runtime_overrides 2026-08-03 >/dev/null
printf '%s|%s\n' \
  "$KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED" \
  "$KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED"
""",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip() == "false|false"


def test_preopen_wrapper_uses_lock_to_avoid_duplicate_bootstrap_run():
    script = Path("deploy/run_threshold_cycle_preopen.sh").read_text(encoding="utf-8")

    assert "threshold_cycle_preopen.lock" in script
    assert "flock -n 9" in script
    assert "threshold-cycle preopen already running" in script
    assert "src.engine.automation.machine_microstructure_policy_approval" in script
    assert "--phase preopen" in script
    assert "runtime_apply_unchanged=true" in script
    approval_index = script.index(
        "src.engine.automation.machine_microstructure_policy_approval"
    )
    runtime_family_index = script.index(
        "src.engine.automation.main_ai_quality_runtime_family"
    )
    assert approval_index < runtime_family_index
    runtime_family_block = script[runtime_family_index:]
    assert "--phase preopen" in runtime_family_block
    assert '--target-date "$TARGET_DATE"' in runtime_family_block
    assert "--write" in runtime_family_block
    assert "exact_candidate_or_standing_intent_not_ready=true" in (runtime_family_block)


def test_preopen_wrapper_treats_operator_lock_ready_manifest_as_succeeded():
    script = Path("deploy/run_threshold_cycle_preopen.sh").read_text(encoding="utf-8")

    assert "MANIFEST_CAPTURE_FILE" in script
    assert "handle_preopen_apply_result" in script
    assert "operator_runtime_env_lock_ready_missing_source_report" in script
    assert "operator_runtime_env_lock_preserved_missing_source_report" in script
    assert "runtime_env_handoff_verification" in script
    assert "extract_manifest_json" in script
    assert "src.engine.scalping.entry_setup_live_policy" in script
    assert '--target-date "$TARGET_DATE"' in script
    assert (
        '--runtime-env-file "$PROJECT_DIR/data/threshold_cycle/runtime_env/threshold_runtime_env_${TARGET_DATE}.env"'
        in script
    )
    assert (
        '--operator-env-file "$PROJECT_DIR/data/threshold_cycle/runtime_env/operator_runtime_overrides.env"'
        in script
    )
    assert (
        '--dated-operator-env-file "$PROJECT_DIR/data/threshold_cycle/runtime_env/operator_runtime_overrides_${TARGET_DATE}.env"'
        in script
    )
    assert '"entry_setup_live_policy_status"' in script
    assert '"entry_setup_live_policy_blocking_reasons"' in script
    assert "--write" in script


def test_preopen_wrapper_smoke_allows_operator_lock_runtime_env_without_source_report(
    tmp_path,
):
    project = tmp_path / "project"
    date = "2026-06-20"
    apply_dir = project / "data/threshold_cycle/apply_plans"
    runtime_dir = project / "data/threshold_cycle/runtime_env"
    engine_dir = project / "src/engine"
    scalping_dir = engine_dir / "scalping"
    apply_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    engine_dir.mkdir(parents=True)
    scalping_dir.mkdir(parents=True)
    (project / "src/__init__.py").write_text("", encoding="utf-8")
    (engine_dir / "__init__.py").write_text("", encoding="utf-8")
    (scalping_dir / "__init__.py").write_text("", encoding="utf-8")
    (scalping_dir / "entry_setup_live_policy.py").write_text(
        "import json\n"
        "import sys\n"
        "date = sys.argv[sys.argv.index('--target-date') + 1]\n"
        "print(json.dumps({'target_date': date, 'status': 'inactive_fallback_v2_13'}))\n",
        encoding="utf-8",
    )
    (engine_dir / "threshold_cycle_preopen_apply.py").write_text(
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "def main():\n"
        "    date = sys.argv[sys.argv.index('--date') + 1]\n"
        "    runtime_dir = Path('data/threshold_cycle/runtime_env')\n"
        "    runtime_dir.mkdir(parents=True, exist_ok=True)\n"
        "    env_path = runtime_dir / f'threshold_runtime_env_{date}.env'\n"
        "    json_path = runtime_dir / f'threshold_runtime_env_{date}.json'\n"
        "    env_path.write_text('export A=1\\n', encoding='utf-8')\n"
        "    json_path.write_text(json.dumps({'target_date': date, 'report_type': 'threshold_runtime_env'}), encoding='utf-8')\n"
        "    print('provider initialization banner')\n"
        "    print(json.dumps({\n"
        "        'target_date': date,\n"
        "        'status': 'operator_runtime_env_lock_ready_missing_source_report',\n"
        "        'runtime_change': True,\n"
        "        'runtime_env_file': str(env_path),\n"
        "        'runtime_env_handoff_verification': {'status': 'pass'},\n"
        "    }, ensure_ascii=False))\n"
        "    return 2\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n",
        encoding="utf-8",
    )
    (apply_dir / f"threshold_apply_{date}.json").write_text(
        json.dumps({"target_date": date}), encoding="utf-8"
    )

    env = {
        **os.environ,
        "PROJECT_DIR": str(project),
        "VENV_PY": "python3",
    }
    result = subprocess.run(
        ["bash", "deploy/run_threshold_cycle_preopen.sh", date],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "[DONE] threshold-cycle preopen" in result.stdout
    status = json.loads(
        (
            project
            / f"data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.status.json"
        ).read_text(encoding="utf-8")
    )
    assert status["status"] == "succeeded"
    assert (
        status["reason"] == "operator_runtime_env_lock_preserved_missing_source_report"
    )
    assert status["runtime_env_exists"] is True
    assert status["runtime_env_manifest_exists"] is True
    manifest = json.loads(
        (
            project
            / f"data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["status"] == "operator_runtime_env_lock_ready_missing_source_report"


def test_preopen_wrapper_failure_closes_status_and_writes_fail_marker(tmp_path):
    project = tmp_path / "project"
    date = "2026-09-01"
    engine_dir = project / "src/engine"
    engine_dir.mkdir(parents=True)
    (project / "src/__init__.py").write_text("", encoding="utf-8")
    (engine_dir / "__init__.py").write_text("", encoding="utf-8")
    (engine_dir / "threshold_cycle_preopen_apply.py").write_text(
        "import json\n"
        "print(json.dumps({\n"
        "    'status': 'auto_bounded_live_ready',\n"
        "    'runtime_change': True,\n"
        "    'runtime_env_handoff_verification': {'status': 'fail'},\n"
        "}))\n"
        "raise SystemExit(1)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", "deploy/run_threshold_cycle_preopen.sh", date],
        cwd=Path.cwd(),
        env={**os.environ, "PROJECT_DIR": str(project), "VENV_PY": "python3"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1, result.stdout
    assert (
        f"[FAIL] threshold-cycle preopen target_date={date} "
        "reason=command_failed exit_code=1"
    ) in result.stdout
    status = json.loads(
        (
            project
            / f"data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.status.json"
        ).read_text(encoding="utf-8")
    )
    assert status["status"] == "failed"
    assert status["reason"] == "command_failed"
    assert status["exit_code"] == 1
    assert status["finished_at"] == status["updated_at"]


def test_opening_rotation_tuning_and_preopen_apply_are_retired():
    postclose = Path("deploy/run_threshold_cycle_postclose.sh").read_text(
        encoding="utf-8"
    )
    preopen = Path("deploy/run_threshold_cycle_preopen.sh").read_text(encoding="utf-8")

    assert "THRESHOLD_CYCLE_RUN_OPENING_ROTATION_PROFILE_TUNING" not in postclose
    assert "-m src.engine.scalping.opening_rotation_tuning" not in postclose
    assert 'RUN_OPENING_ROTATION_PROFILE_TUNING="retired"' in postclose
    assert "-m src.engine.scalping.opening_rotation_tuning" not in preopen
