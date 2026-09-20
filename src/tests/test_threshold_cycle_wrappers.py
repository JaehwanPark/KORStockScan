from pathlib import Path

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
    path.write_text(json.dumps(origin));source.write_text('{"value":2}')
    result=subprocess.run(args,input=body,text=True,capture_output=True,env=env)
    assert result.returncode!=0 and json.loads(path.read_text())==origin
