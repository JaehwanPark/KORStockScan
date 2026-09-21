from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_postclose_wrapper_retires_common_daily_ev_and_generic_workorder():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    assert "src.engine.daily_threshold_cycle_report" not in script
    assert "src.engine.threshold_cycle_ev_report" not in script
    assert "run_threshold_cycle_calibration.sh" not in script
    assert "src.engine.build_code_improvement_workorder" not in script
    assert "src.engine.runtime_approval_summary" in script
    assert "src.engine.verify_threshold_cycle_postclose_chain" in script
    assert script.count("--require-summary-handoff") >= 2


def test_postclose_status_records_direct_owner_producer_flags():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    for flag in (
        "observation_source_quality_audit",
        "entry_split_order_plan",
        "scale_in_split_order_plan",
        "samsung_machine_entry_tuning",
        "low_price_two_leg_tuning",
        "low_price_two_leg_candidate_recommendation",
        "intraday_ws_freshness_finalize",
        "ai_decision_action_outcome_calibration",
    ):
        assert f'"{flag}"' in script


def test_preopen_orders_direct_publishers_before_bootstrap_and_consumers():
    script = _text("deploy/run_threshold_cycle_preopen.sh")
    publishers = [
        "low_price_two_leg_policy_apply",
        "machine_microstructure_policy_approval",
        "machine_entry_timing_tuning",
        "scanner_lookup_attention_policy",
    ]
    bootstrap = script.index("src.engine.automation.runtime_policy_bootstrap")
    assert all(script.index(name) < bootstrap for name in publishers)
    assert bootstrap < script.index("src.engine.scalping.entry_setup_live_policy")
    assert "--receipt" in script
    assert "src.engine.threshold_cycle_preopen_apply" not in script


def test_preopen_uses_single_lock_and_exact_date_bootstrap():
    script = _text("deploy/run_threshold_cycle_preopen.sh")
    assert "flock -n 9" in script
    assert 'runtime_policy_bootstrap_${TARGET_DATE}.env' in script
    assert "threshold_runtime_env_${TARGET_DATE}" not in script


def test_launcher_fails_closed_on_bootstrap_and_verifies_before_bot():
    script = _text("src/run_bot.sh")
    path = 'runtime_policy_bootstrap_$(TZ=Asia/Seoul date +%F).env'
    assert path in script
    assert "src.engine.automation.runtime_policy_bootstrap" in script
    assert script.index("wait_for_threshold_runtime_env") < script.index("bot_main.py")
    assert script.index("verify_threshold_runtime_env_handoff") < script.index("bot_main.py")
    assert "record_threshold_runtime_env_pid_handoff" in script
    assert script.index(
        'record_threshold_runtime_env_pid_handoff "$RUNTIME_TARGET_DATE" "$BOT_PID"'
    ) > script.index("BOT_PID=$!")
    assert '--verify --target-date "$target_date" --pid "$bot_pid"' in script
    assert "threshold_cycle_preopen_apply" not in script


def test_deleted_common_modules_have_no_wrapper_calls():
    scripts = _text("deploy/run_threshold_cycle_postclose.sh") + _text("deploy/run_threshold_cycle_preopen.sh")
    for name in (
        "daily_threshold_cycle_report",
        "threshold_cycle_ev_report",
        "threshold_cycle_preopen_apply",
        "refresh-machine-evaluation-only",
    ):
        assert name not in scripts


def test_compact_postclose_has_one_direct_evaluator_and_no_phase_coordinator():
    main = _text("deploy/run_threshold_cycle_postclose.sh")
    dedicated = _text("deploy/run_ai_entry_setup_paired_replay_postclose.sh")
    assert "--postclose-phase" not in main + dedicated
    assert "compact_summary_handoff" not in main + dedicated
    for script in (main, dedicated):
        assert script.count("--execute-compact-candidate") == 1
        assert script.count("--finalize-compact") == 1
        assert "src.engine.scalping.entry_setup_paired_replay_batch" in script
    installer = _text("deploy/install_threshold_cycle_cron.sh")
    controller = _text("deploy/run_postclose_done_controller.sh")
    assert "run_ai_entry_setup_paired_replay_postclose.sh" not in installer
    assert "run_ai_entry_setup_paired_replay_postclose.sh" not in controller
    assert "run_runtime_release.sh preopen" in installer
    assert "run_runtime_release.sh postclose" in installer
    assert "run_threshold_cycle_postclose.sh" not in installer


def test_main_machine_evaluation_precedes_compact_and_final_consumers():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    publication = script.index('--publication-date "$POLICY_PUBLICATION_DATE"')
    full = script.rfind(
        "src.engine.scalping.ai_action_outcome_calibration", 0, publication
    )
    compact_execute = script.index("--execute-compact-candidate --write", full)
    compact_finalize = script.index("--finalize-compact --publication-date", compact_execute)
    summary = script.index("src.engine.runtime_approval_summary", compact_finalize)
    checklist = script.index("src.engine.build_next_stage2_checklist", summary)
    strict = script.index("--main-mechanistic-summary-only", checklist)
    assert full < compact_execute < compact_finalize < summary < checklist < strict
    assert "--require-policy-publication" in script[full:compact_execute]


def test_final_done_follows_bound_seal_and_no_retired_finalizer_dependencies():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    main = (root / "deploy/run_threshold_cycle_postclose.sh").read_text()
    assert main.index("write_postclose_status producers_completed") < main.index("--seal-main-run") < main.index('[DONE] threshold-cycle postclose')
    finalizer = (root / "deploy/run_postclose_finalization.sh").read_text()
    assert "--require-independent-producers" in finalizer
    assert 'checks["tuning_artifact"]' not in finalizer
    assert 'checks["controller_artifact"]' not in finalizer
    assert 'checks["dashboard_log"]' not in finalizer
    assert "days <= 1" not in finalizer


def test_historical_machine_recovery_disables_current_account_cost_and_notifications():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    script = (root / "deploy/run_machine_microstructure_final_refresh.sh").read_text()
    assert '"$RECOVERY_MODE" != "true" ]]; then\n  "$PYTHON_BIN" -m src.engine.monitoring.research_native_capacity_source' in script
    for setting in ('notify_args=()', 'policy_notify_args=()', 'cost_args=()'):
        assert setting in script
    assert '--phase finished --exit-code "$rc"' in script
    assert script.index('--phase wait-inputs') < script.index('--phase started')
    assert script.index('if ((expansion_rc != 0))') < script.index('attribution_rc=0')
    service = _text("deploy/systemd/korstockscan-machine-microstructure-final-refresh.service")
    assert "Restart=no" in service
    assert "TimeoutStartSec=57600" in service


def test_main_retry_adoption_preserves_origin_and_rejects_changed_bytes(tmp_path):
    import hashlib, json, os, subprocess, sys
    body=_text("deploy/run_threshold_cycle_postclose.sh").split('write_postclose_status() {',1)[1].split("<<'PY'\n",1)[1].split("\nPY\n}",1)[0]
    day="2026-09-17"; sha="a"*40
    path=tmp_path/"status.json"; source=tmp_path/"source.json"
    source.write_text('{"value":1}')
    stat=source.stat(); digest=hashlib.sha256(source.read_bytes()).hexdigest()
    modules=["src.engine.sniper_post_sell_feedback","src.engine.monitoring.rising_missed_intraday_feedback"]
    origin=dict(target_date=day,run_id="original",code_commit=sha,status="failed")
    receipt=dict(target_date=day,origin_run_id="original",origin_code_commit=sha,reused_modules=modules,
        command_receipts=[dict(producer_module=m,run_id="original",exit_code=0,target_date=day,code_commit=sha,measurement_complete=True) for m in modules],
        artifacts=[dict(path=str(source),sha256=digest)],code_dependencies=[dict(path=str(source),sha256=digest)],
        source_generations=[dict(path=str(source),generation=[stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns])])
    proof=tmp_path/"reuse.json";proof.write_text(json.dumps(receipt))
    env=dict(os.environ,POSTCLOSE_REUSE_RECEIPT=str(proof),POSTCLOSE_RUN_ID="retry",POSTCLOSE_CODE_COMMIT="b"*40)
    args=[sys.executable,"-",str(path),day,"running","started","0","0",""]+["true"]*9
    path.write_text(json.dumps(origin))
    result=subprocess.run(args,input=body,text=True,capture_output=True,env=env)
    assert result.returncode==0,result.stderr
    assert json.loads(path.read_text())["reused_steps_receipt"]["origin_run_id"]=="original"
    retry = json.loads(path.read_text())
    retry['status'] = 'failed'
    path.write_text(json.dumps(retry))
    low = 'src.engine.monitoring.low_price_two_leg_expanded_candidate_research'
    inherited = dict(receipt, origin_run_id='retry', origin_code_commit='b'*40,
                     inherited_receipt_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),
                     reused_modules=modules+[low], command_receipts=receipt['command_receipts']+[
                         dict(producer_module=low,run_id='retry',exit_code=0,target_date=day,code_commit='b'*40,measurement_complete=True)])
    next_proof = tmp_path/'reuse-next.json'; next_proof.write_text(json.dumps(inherited))
    next_env = dict(env, POSTCLOSE_REUSE_RECEIPT=str(next_proof),POSTCLOSE_RUN_ID='third')
    result=subprocess.run(args,input=body,text=True,capture_output=True,env=next_env)
    assert result.returncode == 0, result.stderr
    function = 'verified_reused_module() {' + _text('deploy/run_threshold_cycle_postclose.sh').split('verified_reused_module() {',1)[1].split('reusable_completed_artifact() {',1)[0]
    check_env=dict(os.environ, VENV_PY=sys.executable, STATUS_FILE=str(path))
    command=function+'\nverified_reused_module '+low
    assert subprocess.run(['bash','-c',command],env=check_env,capture_output=True).returncode == 0
    next_proof.write_text('{}')
    assert subprocess.run(['bash','-c',command],env=check_env,capture_output=True).returncode == 2
    path.write_text(json.dumps(origin));source.write_text('{"value":2}')
    result=subprocess.run(args,input=body,text=True,capture_output=True,env=env)
    assert result.returncode!=0 and json.loads(path.read_text())==origin


def test_explicit_conditional_exit_seals_failure_once(tmp_path):
    import subprocess
    script = _text('deploy/run_threshold_cycle_postclose.sh')
    function = script.split('finish_postclose_wrapper() {', 1)[1].split("\ntrap ", 1)[0]
    for exit_code, recorded, expected in [(1, 'false', 'failed:1\ncleanup\n'),
                                           (1, 'true', 'cleanup\n'),
                                           (0, 'false', 'cleanup\n')]:
        body = f'''POSTCLOSE_OPERATING=true
POSTCLOSE_FAILURE_RECORDED={recorded}
mark_postclose_failed() {{ echo "failed:$2"; }}
restart_postclose_bot_if_requested() {{ :; }}
cleanup_threshold_cycle_snapshot_temp() {{ echo cleanup; }}
finish_postclose_wrapper() {{{function}
trap 'finish_postclose_wrapper "$?"' EXIT
if true; then exit {exit_code}; fi
'''
        result = subprocess.run(['bash', '-c', body], capture_output=True, text=True)
        assert result.returncode == exit_code
        assert result.stdout == expected


def test_verbosity_source_binding_is_defined_for_plain_and_compressed(tmp_path):
    import os
    import subprocess
    script = _text('deploy/run_threshold_cycle_postclose.sh')
    block = script[script.index('  pipeline_raw_source='):script.index('  pipeline_producer_summary=')]
    folder = tmp_path/'data/pipeline_events'; folder.mkdir(parents=True)
    source = folder/'pipeline_events_2026-09-17.jsonl'
    for compressed in (False, True):
        path = source.with_suffix('.jsonl.gz') if compressed else source
        path.write_bytes(b'fixture')
        result = subprocess.run(['bash','-c', 'set -u\n' + block + '\nprintf "%s" "${pipeline_verbosity_inputs[0]}"'],
                                env={**os.environ,'PROJECT_DIR':str(tmp_path),'TARGET_DATE':'2026-09-17'}, capture_output=True,text=True)
        assert result.returncode == 0 and result.stdout == str(path)
        path.unlink()


@pytest.mark.parametrize("name", ["run_rising_missed_intraday_feedback.sh", "run_market_opportunity_census_intraday.sh"])
def test_source_producer_wrapper_routes_canonical_to_selected_release(tmp_path, name):
    import os
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    workspace, release = tmp_path / "workspace", tmp_path / "release"
    for directory in (workspace / "deploy", workspace / ".venv/bin", workspace / "data/runtime", workspace / "src/engine/infrastructure", release / "deploy"):
        directory.mkdir(parents=True)
    (workspace / "deploy" / name).write_text((root / "deploy" / name).read_text())
    (workspace / ".venv/bin/python").symlink_to(sys.executable)
    (workspace / "data/runtime/runtime_release_selection.json").write_text("{}")
    (workspace / "src/engine/infrastructure/runtime_release_router.py").write_text(
        "from pathlib import Path\ndef selected_release(workspace): return Path(" + repr(str(release)) + "), {}\n")
    (release / "deploy" / name).write_text('printf "%s" "$1"\n')
    env = {k:v for k,v in os.environ.items() if k != "PROJECT_DIR"}
    result = subprocess.run(["bash", str(workspace / "deploy" / name), "2026-09-17"], env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "2026-09-17"


def test_machine_refresh_updates_direct_summary_before_checklist():
    script = (Path(__file__).resolve().parents[2] / "deploy/run_machine_microstructure_final_refresh.sh").read_text()
    assert script.index("-m src.engine.runtime_approval_summary") < script.index("-m src.engine.build_next_stage2_checklist")
    assert "if ((builder_rc == 0)); then" in script


def test_machine_refresh_binds_publication_before_waiting():
    script = (Path(__file__).resolve().parents[2] / "deploy/run_machine_microstructure_final_refresh.sh").read_text()
    assert 'POSTCLOSE_POLICY_PUBLICATION_DATE:-$completed_target_date' in script
    assert 'export POSTCLOSE_PREPARED_EFFECTIVE_DATE=' in script
    assert script.index('export POSTCLOSE_POLICY_PUBLICATION_DATE=') < script.index('--phase wait-inputs')
