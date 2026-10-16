from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_rising_feedback_consumes_post_exclusion_preflight_generation(tmp_path):
    import subprocess

    script = _text("deploy/run_threshold_cycle_postclose.sh")
    rising = script.index('if [ "$RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE"')
    preflight = script.index('if [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT"')
    end = script.index('if [[ "$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION"', max(rising, preflight))
    body = script[min(rising, preflight):end]
    source = tmp_path / "source-generation"
    source.write_text("unfiltered")
    python_stub = tmp_path / "python-stub"
    python_stub.write_text("#!/bin/sh\nexit 1\n")
    python_stub.chmod(0o700)
    prefix = '''set -eu
wait_for_postclose_resources() { :; }
wait_for_report_artifact() { :; }
run_postclose_cmd() {
  case "$*" in
    *src.engine.observation_source_quality_audit*) printf filtered > "$SOURCE_GENERATION" ;;
    *src.engine.monitoring.rising_missed_intraday_feedback*)
      [[ "$(cat "$SOURCE_GENERATION")" == filtered ]] || return 42
      printf feedback_verified
      ;;
    *) return 43 ;;
  esac
}
'''
    result = subprocess.run(
        ["bash", "-c", prefix + body],
        env={
            "PATH": "/usr/bin:/bin",
            "PROJECT_DIR": str(tmp_path),
            "VENV_PY": str(python_stub),
            "TARGET_DATE": "2026-10-16",
            "SOURCE_GENERATION": str(source),
            "POSTCLOSE_RECOVERY_REUSE_MODE": "false",
            "RUN_RISING_MISSED_INTRADAY_FEEDBACK_POSTCLOSE": "true",
            "RUN_OBSERVATION_SOURCE_QUALITY_AUDIT": "true",
        },
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "feedback_verified" in result.stdout


@pytest.mark.parametrize('cost_exit', [0, 47])
def test_cost_source_precedes_fact_and_quantity_generation_without_new_hard_gate(cost_exit):
    import os, subprocess
    script = _text('deploy/run_threshold_cycle_postclose.sh')
    start = script.index('wait_for_postclose_resources "holding_broker_cost_source"')
    end = script.index('# Refresh exact execution-derived facts', start)
    fact = script.index('-m src.engine.strategy_position_performance_report')
    quantity = script.index('-m src.engine.scalping.initial_quantity_policy \\\n')
    assert start < end < fact < quantity
    assert script.count('-m src.engine.lifecycle.broker_cost_source --date "$TARGET_DATE"') == 1
    body = script[start:end]
    command = ('set -e\nwait_for_postclose_resources() { return 0; }\n'
        + 'run_postclose_cmd() { printf "cost-source\\n"; return '+str(cost_exit)+'; }\n'
        + body + '\nprintf "facts-and-quantity-follow\\n"\n')
    result = subprocess.run(['bash', '-c', command], capture_output=True, text=True,
        env={**os.environ, 'VENV_PY': '/unused/python', 'TARGET_DATE': '2026-10-15'})
    assert result.returncode == 0
    assert result.stdout.splitlines() == ['cost-source', 'facts-and-quantity-follow']
    assert ('preserve source gap' in result.stderr) == (cost_exit != 0)


@pytest.mark.parametrize("exit_code", [0, 47])
@pytest.mark.parametrize("shared_mount", [False, True])
def test_entry_split_verification_hook_uses_bounded_child_and_propagates_failure(tmp_path, exit_code, shared_mount):
    import os, subprocess
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    body = "publish_entry_split_verification() {" + script.split(
        "publish_entry_split_verification() {", 1)[1].split("\n}\n", 1)[0] + "\n}\n"
    # Exercise the shell boundary without running the postclose producer or
    # a provider. A failing verification must stop the calling stage.
    command = f'''set -e
run_postclose_cmd() {{ printf '%s\\n' "$@"; return {exit_code}; }}
{body}
publish_entry_split_verification
printf 'continued\\n'
'''
    project = tmp_path / "project with spaces"
    project.mkdir()
    data = tmp_path / "shared data" if shared_mount else project / "data"
    data.mkdir()
    if shared_mount:
        (project / "data").symlink_to(data, target_is_directory=True)
    result = subprocess.run(["bash", "-c", command], capture_output=True, text=True,
        env={**os.environ, "PROJECT_DIR": str(project), "TARGET_DATE": "2026-10-13",
             "VENV_PY": str(project / ".venv/bin/python")})
    assert result.returncode == exit_code
    args = result.stdout.splitlines()
    assert args[:5] == ["env", "PYTHONPATH=.", str(project / ".venv/bin/python"), "-m",
                       "src.engine.scalping.entry_split_monitor_projection"]
    assert args[args.index("--data-root") + 1] == str(data)
    assert args[args.index("--report") + 1] == str(data / "report/entry_split_order_plan/entry_split_order_plan_2026-10-13.json")
    assert args[args.index("--wall-seconds") + 1] == "300"
    assert args[args.index("--memory-mib") + 1] == "4096"
    assert ("continued" in args) == (exit_code == 0)
    assert script.count("  compact_entry_split_report_storage\n  publish_entry_split_verification\n") == 2


def _native_final_resume_fixture(tmp_path):
    import json, hashlib
    script = _text('deploy/run_threshold_cycle_postclose.sh')
    program = script.split("<<'PY_FINAL_RESUME'\n", 1)[1].split('\nPY_FINAL_RESUME', 1)[0]
    namespace = {'__name__': 'native_resume_test'}
    exec(compile(program, 'native_final_resume', 'exec'), namespace)
    day = '2026-10-13'; run = 'native-failed-tower'; commit = 'a' * 40
    report = tmp_path / 'data/report'; directory = report / 'threshold_cycle_postclose_status'
    directory.mkdir(parents=True); (tmp_path / 'logs').mkdir()
    prior = tmp_path / 'prior.json'; prior.write_text(json.dumps(dict(
        schema='postclose_initial_quantity_resume_v1', source_date=day, origin_run_id='original',
        runtime_effect=False, allowed_runtime_apply=False)))
    status = dict(target_date=day, status='failed', reason='command_failed', exit_code=1,
        run_id=run, code_commit=commit, scoped_resume=dict(path=str(prior),
            sha256=hashlib.sha256(prior.read_bytes()).hexdigest(), origin_run_id='original',
            resume_from='initial_quantity'))
    status_path = directory / f'threshold_cycle_postclose_{day}.status.json'
    status_path.write_text(json.dumps(status))
    modules = ('scalping.initial_quantity_policy', 'runtime_approval_summary',
        'observation_source_quality_audit', 'monitoring.intraday_ws_freshness_monitor',
        'pipeline_event_verbosity_report', 'monitoring.rising_missed_classifier_prior')
    metrics = [dict(run_id=run, phase='command', target_date=day, code_commit=commit,
        measurement_complete=True, producer_module='src.engine.' + m, exit_code=0) for m in modules]
    metrics.append(dict(run_id=run, phase='command', producer_module='src.engine.automation.tuning_performance_control_tower', exit_code=1))
    log = tmp_path / 'logs/threshold_cycle_postclose_cron.log'
    log.write_text(''.join('[PERF] ' + json.dumps(m) + '\n' for m in metrics))
    quantity = tmp_path / 'quantity.json'; quantity.write_text('{}')
    snapshot = tmp_path / 'snapshot.json'; snapshot.write_text('{}')
    profile = tmp_path / 'data/config/native_owner_custody.env'; profile.parent.mkdir(); profile.write_text('fixture')
    namespace.update(active_stage_names=lambda d: ('main_machine_policy','summary_handoff'),
        stage_receipt_issues=lambda *a: [],
        verified_postclose_exit_snapshot_manifest=lambda *a, **k: snapshot,
        committed_refresh_stage_path=lambda *a: quantity,
        refresh_quantity_stage_terminal_valid=lambda a: True)
    return namespace, day, status_path, status, log, metrics, prior


def test_final_resume_binds_native_prefix_and_preserves_previous_proof(tmp_path):
    import hashlib
    n, day, path, status, log, metrics, prior = _native_final_resume_fixture(tmp_path)
    proof = n['final_handoff_resume'](tmp_path, day)
    assert proof['origin_status_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert proof['completed_command_receipts'] == metrics[:-1]
    assert proof['prior_scoped_resume'] == status['scoped_resume']
    assert proof['runtime_effect'] is proof['allowed_runtime_apply'] is False


@pytest.mark.parametrize('quantity_valid', [False, True])
def test_final_resume_checklist_failure_requires_repaired_quantity_source(tmp_path, quantity_valid):
    import json
    n, day, path, status, log, metrics, prior = _native_final_resume_fixture(tmp_path)
    status.update(scoped_resume=None, regeneration_scope='normal', reused_steps_receipt=None)
    metrics[-1].update(producer_module='src.engine.build_next_stage2_checklist', exit_code=1)
    path.write_text(json.dumps(status))
    log.write_text(''.join('[PERF] '+json.dumps(m)+'\n' for m in metrics))
    n['refresh_quantity_stage_terminal_valid'] = lambda *a: quantity_valid
    before = path.read_bytes()
    if not quantity_valid:
        with pytest.raises(ValueError, match='final_resume_quantity_stage_invalid'):
            n['final_handoff_resume'](tmp_path, day)
    else:
        proof = n['final_handoff_resume'](tmp_path, day)
        assert proof['completed_command_receipts'] == metrics[:-1]
        assert proof['origin_run_id'] == status['run_id']
        assert proof['prior_scoped_resume'] is None
    assert path.read_bytes() == before


@pytest.mark.parametrize('defect', [None, 'partial', 'reuse', 'wrong_commit', 'missing_command', 'changed_source'])
def test_final_resume_accepts_only_complete_normal_native_run(tmp_path, defect):
    import json
    n, day, path, status, log, metrics, prior = _native_final_resume_fixture(tmp_path)
    status.update(scoped_resume=None, regeneration_scope='normal', reused_steps_receipt=None, exit_code=2)
    metrics[-1].update(producer_module='src.engine.verify_threshold_cycle_postclose_chain', exit_code=2)
    if defect == 'partial': status['regeneration_scope'] = 'all_except_eod'
    if defect == 'reuse': status['reused_steps_receipt'] = {'unverified': True}
    if defect == 'wrong_commit': metrics[0]['code_commit'] = 'b' * 40
    if defect == 'missing_command': metrics.pop(0)
    if defect == 'changed_source': n['stage_receipt_issues'] = lambda *a: ['source_changed']
    path.write_text(json.dumps(status)); log.write_text(''.join('[PERF] '+json.dumps(m)+'\n' for m in metrics))
    if defect is not None:
        with pytest.raises(ValueError, match='final_resume_'):
            n['final_handoff_resume'](tmp_path, day)
        return
    before = path.read_bytes()
    proof = n['final_handoff_resume'](tmp_path, day)
    assert proof['completed_command_receipts'] == metrics[:-1]
    assert proof['prior_scoped_resume'] is None and proof['inherited_command_receipts'] == []
    assert proof['origin_run_id'] == status['run_id'] and path.read_bytes() == before
    assert proof['runtime_effect'] is proof['allowed_runtime_apply'] is False


@pytest.mark.parametrize('defect', ['running','other_failure','prefix_missing','proof_changed','stage_invalid','snapshot_invalid','quantity_invalid'])
def test_final_resume_refuses_incomplete_or_changed_native_prefix(tmp_path, defect):
    import json
    n, day, path, status, log, metrics, prior = _native_final_resume_fixture(tmp_path)
    if defect == 'running': status['status'] = 'running'; path.write_text(json.dumps(status))
    if defect == 'other_failure': metrics[-1]['producer_module'] = 'other'; log.write_text(''.join('[PERF] '+json.dumps(m)+'\n' for m in metrics))
    if defect == 'prefix_missing': metrics[0]['measurement_complete'] = False; log.write_text(''.join('[PERF] '+json.dumps(m)+'\n' for m in metrics))
    if defect == 'proof_changed': prior.write_text('{}')
    if defect == 'stage_invalid': n['stage_receipt_issues'] = lambda *a: ['source_changed']
    if defect == 'snapshot_invalid': n['verified_postclose_exit_snapshot_manifest'] = lambda *a, **k: None
    if defect == 'quantity_invalid': n['refresh_quantity_stage_terminal_valid'] = lambda *a: False
    with pytest.raises(ValueError, match='final_resume_'):
        n['final_handoff_resume'](tmp_path, day)


def test_direct_postclose_loads_native_custody_profile_without_shell_evaluation(tmp_path):
    import os, subprocess, sys
    script = _text('deploy/run_threshold_cycle_postclose.sh')
    block = script[script.index('native_custody_assignments='):script.index('TARGET_DATE="${1:-')]
    package = tmp_path / 'src/engine/infrastructure'; package.mkdir(parents=True)
    (package / 'runtime_release_router.py').write_text(
        "def native_custody_environment(workspace):\n"
        " return {'KORSTOCKSCAN_BROKER_ACCOUNT_KEY': 'attested-account', 'KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH': '/native/journal $(touch unexpected)'}\n")
    env = {**os.environ, 'PROJECT_DIR': str(tmp_path), 'VENV_PY': sys.executable,
        'KORSTOCKSCAN_BROKER_ACCOUNT_KEY': 'wrong-account'}
    result = subprocess.run(['bash', '-c', 'set -e\n'+block+'\nprintf "%s\\n" "$KORSTOCKSCAN_BROKER_ACCOUNT_KEY" "$KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH"'],
        env=env, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ['attested-account', '/native/journal $(touch unexpected)']
    assert not (tmp_path / 'unexpected').exists()


def test_strict_resume_retains_native_ancestry_without_relabelling_commands(tmp_path):
    import json, hashlib
    n, day, path, status, log, metrics, prior = _native_final_resume_fixture(tmp_path)
    origin = status['run_id']; commit = status['code_commit']
    parent = dict(schema='postclose_final_handoff_resume_v1', source_date=day,
        origin_run_id=origin, origin_code_commit=commit, completed_command_receipts=metrics[:-1],
        runtime_effect=False, allowed_runtime_apply=False, prior_scoped_resume=status['scoped_resume'])
    parent_path = tmp_path / 'parent.json'; parent_path.write_text(json.dumps(parent))
    status.update(run_id='next-native-run', code_commit='b'*40, exit_code=2,
        scoped_resume=dict(path=str(parent_path),sha256=hashlib.sha256(parent_path.read_bytes()).hexdigest(),
            origin_run_id=origin,resume_from='final_handoff'))
    path.write_text(json.dumps(status));log.write_text('[PERF] '+json.dumps(dict(
        run_id=status['run_id'],phase='command',producer_module='src.engine.verify_threshold_cycle_postclose_chain',exit_code=2))+'\n')
    proof = n['final_handoff_resume'](tmp_path,day)
    assert proof['completed_command_receipts'] == []
    assert proof['inherited_command_receipts'] == metrics[:-1]
    assert {m['run_id'] for m in proof['inherited_command_receipts']} == {origin}
    prior.write_text('{}')
    with pytest.raises(ValueError,match='final_resume_ancestry_changed'):
        n['final_handoff_resume'](tmp_path,day)


@pytest.mark.parametrize('mutated', [False, True])
def test_storage_compaction_preserves_values_policy_and_original_bytes(tmp_path,monkeypatch,mutated):
    import json, hashlib
    from src.engine.scalping import entry_split_order_plan as native
    script = _text('deploy/run_threshold_cycle_postclose.sh')
    program = script.split("<<'PY_ENTRY_STORAGE'\n",1)[1].split('\nPY_ENTRY_STORAGE',1)[0]
    namespace={'__name__':'storage_test'};exec(compile(program,'entry_storage','exec'),namespace)
    day='2026-06-07';directory=tmp_path/'data/report/entry_split_order_plan';directory.mkdir(parents=True)
    policy_dir=tmp_path/'data/threshold_cycle/entry_split_order_policy';policy_dir.mkdir(parents=True)
    report=dict(schema_version=native.SCHEMA_VERSION,date=day,recommended_policy=dict(policy_version='fixture'),
        literal='  original spaces\n\\\\',values=[None,0,True,'끝'])
    policy=dict(schema_version=native.POLICY_SCHEMA_VERSION,source_date=day,policy_version='fixture')
    report,policy=native.bind_report_policy_generation(report,policy)
    rp=directory/f'entry_split_order_plan_{day}.json';pp=policy_dir/f'entry_split_order_policy_{day}.json'
    original=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=60)+'\n').encode();rp.write_bytes(original)
    policy_raw=json.dumps(policy).encode();pp.write_bytes(policy_raw)
    old_sha=hashlib.sha256(original).hexdigest();receipt=rp.with_name(rp.name+'.reuse-contract.json')
    receipt.write_text(json.dumps(dict(schema='postclose_artifact_reuse_contract_v1',target_date=day,
        artifact_path=str(rp),artifact_sha256=old_sha)))
    compact_size=sum(len(line.strip()) for line in original.splitlines())+1
    monkeypatch.setattr(native,'ENTRY_REPORT_MAX_BYTES',max(compact_size+1,len(original)//2+1))
    if mutated:
        policy['policy_version']='changed';pp.write_text(json.dumps(policy))
        with pytest.raises(ValueError,match='entry_storage_generation_invalid'):
            namespace['compact_entry_storage'](tmp_path,day)
        assert rp.read_bytes()==original
    else:
        result=namespace['compact_entry_storage'](tmp_path,day)
        assert json.loads(rp.read_bytes())==report
        assert pp.read_bytes()==policy_raw
        assert Path(result['original_path']).read_bytes()==original
        assert native.validate_report_policy_generation(json.loads(rp.read_bytes()),policy)[0]
        assert rp.stat().st_size<=native.ENTRY_REPORT_MAX_BYTES
        assert json.loads(receipt.read_text())['artifact_sha256']==hashlib.sha256(rp.read_bytes()).hexdigest()
        assert result['runtime_effect'] is result['allowed_runtime_apply'] is False


def test_postclose_wrapper_retires_common_daily_ev_and_generic_workorder():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    assert "src.engine.daily_threshold_cycle_report" not in script
    assert "src.engine.threshold_cycle_ev_report" not in script
    assert "run_threshold_cycle_calibration.sh" not in script
    assert "src.engine.build_code_improvement_workorder" not in script
    assert "src.engine.runtime_approval_summary" in script
    assert "src.engine.verify_threshold_cycle_postclose_chain" in script
    assert script.count("--require-summary-handoff") >= 2


@pytest.mark.parametrize('reusable,reader,rc,writes', [(0,0,0,False),(1,0,75,False),(1,1,0,True)])
def test_recovery_preserves_preflight_used_by_live_reader(tmp_path,reusable,reader,rc,writes):
    import os,subprocess
    script=_text('deploy/run_threshold_cycle_postclose.sh')
    start=script.index('if [ "$RUN_OBSERVATION_SOURCE_QUALITY_AUDIT" = "true" ]')
    end=script.index('if [[ "$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION"',start)
    python=tmp_path/'python'; marker=tmp_path/'written'
    python.write_text('#!/bin/bash\nif [[ "$*" == *--check-reusable* ]]; then exit "$REUSABLE"; fi\nif [[ "$1" == "-" ]]; then cat >/dev/null; exit "$READER"; fi\nif [[ "$*" == *--write* ]]; then touch "$MARKER"; fi\n')
    python.chmod(0o755)
    prefix='set -e\nwait_for_postclose_resources() { :; }\nrun_postclose_cmd() { "$@"; }\nwait_for_report_artifact() { :; }\n'
    env={**os.environ,'RUN_OBSERVATION_SOURCE_QUALITY_AUDIT':'true','POSTCLOSE_RECOVERY_REUSE_MODE':'true',
        'TARGET_DATE':'2026-10-07','PROJECT_DIR':str(tmp_path),'VENV_PY':str(python),
        'REUSABLE':str(reusable),'READER':str(reader),'MARKER':str(marker)}
    result=subprocess.run(['bash','-c',prefix+script[start:end]],env=env,capture_output=True,text=True)
    assert result.returncode==rc,result.stderr
    assert marker.exists() is writes


def test_reversal_prompt_consumer_is_generated_before_compact_verification():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    consumer = script.index('src.engine.scalping.main_ai_prompt_consumer')
    assert script.rindex('src.engine.runtime_approval_summary') < consumer
    assert consumer < script.index('scope_flag=--main-mechanistic-summary-only')
    assert '--target-date "$TARGET_DATE" --write' in script[consumer:consumer + 160]
    assert 'main_ai_prompt_consumer_${TARGET_DATE}.json' in script[consumer:consumer + 600]


def test_postclose_prepares_isolated_preopen_and_start_requires_day_of_completion():
    controller = _text("deploy/run_postclose_done_controller.sh")
    finalizer = _text("deploy/run_postclose_finalization.sh")
    preopen = _text("deploy/run_threshold_cycle_preopen.sh")
    launcher = _text("src/run_bot.sh")
    assert controller.index('controller_status="$(') < controller.index(
        "src.engine.automation.next_preopen_readiness")
    assert 'controller_status" == "summary_verified"' in controller
    assert controller.index('POSTCLOSE_STAGE_WORKER=1') < controller.index(
        'src.engine.automation.next_preopen_readiness')
    assert "--prepare --source-date \"$TARGET_DATE\"" in controller
    # The detector consumes the prepared controller binding. The reviewed
    # finalizer prepares first, captures the actual detector, then rechecks
    # its final generation; the old reversed-order assertion was stale.
    assert finalizer.index('--prepare --source-date') < finalizer.rindex('if ! run_final_detector; then')
    assert finalizer.rindex('if ! run_final_detector; then') < finalizer.index('capture_final_detector_receipt')
    assert finalizer.index('capture_final_detector_receipt') < finalizer.rindex('capture_finalization_generation')
    assert preopen.index("next_preopen_readiness") < preopen.index(
        "scanner_lookup_attention_policy")
    assert "--verify --target-date \"$TARGET_DATE\" --require-today" in preopen
    assert launcher.index("verify_exact_preopen_completion") < launcher.index(
        "record_threshold_runtime_env_pid_handoff")
    assert 'verify_exact_preopen_completion "$RUNTIME_TARGET_DATE" || exit 1' in launcher


def test_initial_quantity_refresh_runs_before_summary_handoff(monkeypatch, tmp_path):
    from src.engine.automation import postclose_summary_handoff as handoff

    # This ordering contract must not depend on a live policy in ROOT/data.
    monkeypatch.setattr(handoff, '_initial_quantity_refresh_due', lambda *a: True)
    report_dir = tmp_path / 'data/report'

    script = _text("deploy/run_threshold_cycle_postclose.sh")
    producer = script.index('--parent-current "$INITIAL_QUANTITY_CURRENT"')
    terminal = script.index("$INITIAL_QUANTITY_REFRESH_DIR/committed_stage.json")
    summary = script.index("src.engine.runtime_approval_summary", producer)
    assert producer < terminal < summary
    path = handoff.source_paths(report_dir, "2026-09-28", "tower")
    assert "initial_quantity_refresh_stage" in path
    assert path["initial_quantity_refresh_stage"].name == (
        "initial_quantity_refresh_stage_2026-09-28.json")
    # The selected policy's effective lower bound owns the handoff, not a
    # hardcoded rollout date in either producer or consumer.
    assert '"$TARGET_DATE" > "2026-09-27"' not in script
    assert "initial_quantity_refresh_stage" in handoff.source_paths(
        report_dir, "2026-09-27", "tower")
    monkeypatch.setattr(handoff, '_initial_quantity_refresh_due', lambda *a: False)
    assert "initial_quantity_refresh_stage" not in handoff.source_paths(
        report_dir, "2026-09-28", "tower")


def test_async_policy_stages_finish_before_summary_and_checklist_hashing():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    wait = script.index('--stage wait --date "$TARGET_DATE" --timeout-sec 14400')
    summary = script.index('"$VENV_PY" -m src.engine.runtime_approval_summary')
    checklist = script.index("src.engine.build_next_stage2_checklist", summary)
    verifier = script.index("src.engine.verify_threshold_cycle_postclose_chain", checklist)
    assert wait < summary < checklist < verifier
    assert "--stage wait --date \"$TARGET_DATE\" --timeout-sec 14400 || true" not in script


def test_final_audit_cannot_replace_active_machine_preflight():
    script=_text('deploy/run_threshold_cycle_postclose.sh')
    launch=script.index('--stage main_machine_policy --date "$TARGET_DATE" --publication-date')
    wait=script.index('--stage wait --wait-stage main_machine_policy')
    checked=script.index('--stage main_machine_policy --date "$TARGET_DATE" --check',wait)
    final=script.index('--audit-phase final --write')
    assert launch<wait<checked<final
    assert '|| true' not in script[wait:checked]


def test_postclose_status_records_direct_owner_producer_flags():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    for flag in (
        "observation_source_quality_audit",
        "entry_split_order_plan",
        "scale_in_split_order_plan",
        "samsung_machine_entry_tuning",
        "intraday_ws_freshness_finalize",
        "ai_decision_action_outcome_calibration",
    ):
        assert f'"{flag}"' in script


@pytest.mark.parametrize("status", ["running", "succeeded", "failed"])
def test_postclose_status_preserves_active_flags_without_retired_fields(tmp_path, status):
    import json
    import os
    import subprocess
    import sys

    script = _text("deploy/run_threshold_cycle_postclose.sh")
    body = "write_postclose_status() {" + script.split(
        "write_postclose_status() {", 1)[1].split("\nPY\n}", 1)[0] + "\nPY\n}\n"
    path = tmp_path / "status.json"
    path.write_text(json.dumps({"producer_flags": {"low_price_two_leg_tuning": "true"}}))
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("POSTCLOSE_REUSE")}
    env.update(VENV_PY=sys.executable, STATUS_FILE=str(path), TARGET_DATE="2026-10-08",
               POSTCLOSE_RUN_ID="current", POSTCLOSE_CODE_COMMIT="a" * 40,
               RUN_OBSERVATION_SOURCE_QUALITY_AUDIT="source",
               RUN_ENTRY_SPLIT_ORDER_PLAN="entry", RUN_SCALE_IN_SPLIT_ORDER_PLAN="scale",
               RUN_SAMSUNG_MACHINE_ENTRY_TUNING="false",
               RUN_INTRADAY_WS_FRESHNESS_FINALIZE="ws",
               RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION="ai",
               RUN_RISING_MISSED_CLASSIFIER_PRIOR="rising",
               THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_TUNING="true",
               THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_CANDIDATE_RECOMMENDATION="true")
    result = subprocess.run(["bash", "-c", "set -euo pipefail\n" + body +
                             f'write_postclose_status {status} test 0 1'],
                            env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    payload = json.loads(path.read_text())
    assert payload["target_date"] == "2026-10-08" and payload["status"] == status
    flags = payload["producer_flags"]
    assert flags["observation_source_quality_audit"] == "source"
    assert flags["entry_split_order_plan"] == "entry"
    assert flags["scale_in_split_order_plan"] == "scale"
    assert flags["samsung_machine_entry_tuning"] == "false"
    assert flags["intraday_ws_freshness_finalize"] == "ws"
    assert flags["ai_decision_action_outcome_calibration"] == "ai"
    assert flags["rising_missed_classifier_prior"] == "rising"
    assert not any("low_price_two_leg" in key for key in flags)
    assert "LOW_PRICE_TWO_LEG" not in script
    done = script[script.index('emit_postclose_marker "[DONE] threshold-cycle postclose'):]
    assert "low_price_two_leg" not in done


def test_cron_reinstallation_removes_retired_override_and_preserves_unrelated_jobs(tmp_path):
    import os
    import subprocess

    state = tmp_path / "cron.txt"
    state.write_text("5 20 * * 1-5 eod # UPDATE_KOSPI_EOD_2005\n"
                     "10 20 * * 1-5 THRESHOLD_CYCLE_RUN_LOW_PRICE_TWO_LEG_"
                     "CANDIDATE_RECOMMENDATION=false old # THRESHOLD_CYCLE_POSTCLOSE\n"
                     "0 5 * * * finalize # POSTCLOSE_FINALIZATION_0500\n")
    command = tmp_path / "crontab"
    command.write_text('#!/bin/bash\nset -eu\nif [[ "$1" == "-l" ]]; then '
                       'cat "$CRON_STATE"; else cp "$1" "$CRON_STATE"; fi\n')
    command.chmod(0o755)
    env = {**os.environ, "PATH": str(tmp_path) + ":" + os.environ["PATH"],
           "CRON_STATE": str(state), "PROJECT_DIR": str(ROOT)}
    for _ in range(2):
        result = subprocess.run(["bash", str(ROOT / "deploy/install_threshold_cycle_cron.sh")],
                                env=env, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
    text = state.read_text()
    assert "LOW_PRICE_TWO_LEG" not in text
    assert text.count("# THRESHOLD_CYCLE_POSTCLOSE") == 1
    assert text.count("# THRESHOLD_CYCLE_PREOPEN") == 1
    assert "10 20 * * 1-5 THRESHOLD_CYCLE_AI_CORRECTION_PROVIDER=openai" in text
    assert "THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop" in text
    assert "5 20 * * 1-5 eod # UPDATE_KOSPI_EOD_2005\n" in text
    assert "0 5 * * * finalize # POSTCLOSE_FINALIZATION_0500\n" in text


def test_preopen_orders_direct_publishers_before_bootstrap_and_consumers():
    script = _text("deploy/run_threshold_cycle_preopen.sh")
    publishers = [
        "scanner_lookup_attention_policy",
        "mechanistic_entry_runtime_policy",
    ]
    bootstrap = script.index("src.engine.automation.runtime_policy_bootstrap")
    assert all(script.index(name) < bootstrap for name in publishers)
    assert script.index("scanner_lookup_attention_policy") < script.index("--activate-dated-auxiliary") < bootstrap
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
    path = 'runtime_policy_bootstrap_${RUNTIME_TARGET_DATE}.env'
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


@pytest.mark.parametrize('native_rc', [0, 1])
def test_launcher_selector_receipt_requires_native_consumption(tmp_path, native_rc):
    import os, subprocess
    script = _text('src/run_bot.sh')
    start = script.index('    if record_threshold_runtime_env_pid_handoff "$RUNTIME_TARGET_DATE" "$BOT_PID"; then')
    end = script.index('    wait "$BOT_PID"', start)
    project = tmp_path / 'release'; project.mkdir()
    data = tmp_path / 'data'; data.mkdir(); (project / 'data').symlink_to(data)
    source = project / 'src/engine/infrastructure/runtime_release_router.py'
    source.parent.mkdir(parents=True); source.write_text('# selected immutable router fixture\n')
    router = project / '.venv/bin/python'; router.parent.mkdir(parents=True)
    marker = tmp_path / 'recorded'
    router.write_text('''#!/bin/bash
[[ "$1" == -I && "$2" == "$PROJECT_DIR/src/engine/infrastructure/runtime_release_router.py" ]] || exit 2
[[ "$3" == --workspace && "$4" == "$EXPECTED_WORKSPACE" ]] || exit 3
[[ -f "$2" ]] || exit 4
printf "%s\\n" "$*" > "$MARKER"
''')
    router.chmod(0o755)
    prefix = 'set -e\nrecord_threshold_runtime_env_pid_handoff() { return "$NATIVE_RC"; }\n'
    result = subprocess.run(['bash', '-c', prefix + script[start:end]],
        cwd=project / 'src',
        env={**os.environ, 'PROJECT_DIR': str(project), 'MARKER': str(marker),
             'EXPECTED_WORKSPACE': str(tmp_path),
             'RUNTIME_TARGET_DATE': '2026-10-12', 'BOT_PID': '123',
             'KORSTOCKSCAN_RUNTIME_GIT_COMMIT': 'a' * 40, 'NATIVE_RC': str(native_rc)},
        capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert marker.exists() is (native_rc == 0)
    if native_rc == 0:
        assert '--record-pid 123' in marker.read_text()


@pytest.mark.parametrize('failed_stage', ['none', 'bootstrap', 'consume', 'verify'])
def test_launcher_native_receipt_checks_all_stages(tmp_path, failed_stage):
    import os, subprocess
    script = _text('src/run_bot.sh')
    start = script.index('record_threshold_runtime_env_pid_handoff() {')
    end = script.index('\napply_retired_runtime_policy_env()', start)
    work = tmp_path / 'src'; work.mkdir()
    python = tmp_path / '.venv/bin/python'; python.parent.mkdir(parents=True)
    marker = tmp_path / 'stages'
    python.write_text('''#!/bin/bash
stage=verify
[[ "$*" == *runtime_policy_bootstrap* ]] && stage=bootstrap
[[ "$*" == *--consume* ]] && stage=consume
echo "$stage" >> "$MARKER"
[[ "$*" == *"--pid 123"* ]] || exit 2
[[ "$stage" != "$FAILED_STAGE" ]]
''')
    python.chmod(0o755)
    result = subprocess.run(['bash', '-c', script[start:end] +
                             '\nrecord_threshold_runtime_env_pid_handoff 2026-10-12 123\n'],
        cwd=work, env={**os.environ, 'MARKER': str(marker), 'FAILED_STAGE': failed_stage},
        capture_output=True, text=True, timeout=5)
    stages = ['bootstrap', 'consume', 'verify']
    expected = stages if failed_stage == 'none' else stages[:stages.index(failed_stage) + 1]
    assert marker.read_text().splitlines() == expected
    assert result.returncode == (0 if failed_stage == 'none' else 1)


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
    from src.engine.automation.postclose_summary_handoff import stage_commands
    commands = stage_commands('main_auxiliary_policy', '2026-09-21', '2026-09-21')
    assert sum('--execute-compact-candidate' in c for c in commands) == 1
    assert sum('--finalize-compact' in c for c in commands) == 1
    for script in (main, dedicated):
        assert 'main_auxiliary_policy' in script
        assert '--execute-compact-candidate' not in script
    installer = _text("deploy/install_threshold_cycle_cron.sh")
    controller = _text("deploy/run_postclose_done_controller.sh")
    assert "run_ai_entry_setup_paired_replay_postclose.sh" not in installer
    assert "run_ai_entry_setup_paired_replay_postclose.sh" not in controller
    assert "run_runtime_release.sh preopen" in installer
    assert "run_runtime_release.sh postclose" in installer
    assert "run_threshold_cycle_postclose.sh" not in installer


def test_main_machine_evaluation_precedes_compact_and_final_consumers():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    preflight = script.index('--audit-phase preflight --write')
    machine = script.index('--stage main_machine_policy')
    auxiliary = script.index('for stage in legacy_machine_report main_auxiliary_policy')
    assert preflight < machine < auxiliary
    assert 'wait_for_postclose_resources "main_machine_policy"' in script[preflight:machine]
    assert '--launch' in script[machine:auxiliary]
    assert '--stage episode_policy' not in script


def test_failed_cycle_recovery_reuses_main_terminal_without_replaying_machine():
    script = _text("deploy/run_threshold_cycle_postclose.sh")
    assert 'POSTCLOSE_STAGE_RECOVERY_ARGS+=(--recover-closed-target)' in script
    from src.engine.automation.postclose_summary_handoff import stage_commands
    assert stage_commands('main_machine_policy', '2026-09-21', '2026-09-21', recovery=True) == []


def test_final_done_follows_bound_seal_and_no_retired_finalizer_dependencies():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    main = (root / "deploy/run_threshold_cycle_postclose.sh").read_text()
    assert main.index("write_postclose_status producers_completed") < main.index("--seal-main-run") < main.index('[DONE] threshold-cycle postclose')
    finalizer = (root / "deploy/run_postclose_finalization.sh").read_text()
    assert "--require-independent-producers" in finalizer
    assert 'env PYTHONPATH=. POSTCLOSE_STAGE_WORKER=1 \\' in finalizer
    assert 'checks["tuning_artifact"]' not in finalizer
    assert 'checks["controller_artifact"]' not in finalizer
    assert 'checks["dashboard_log"]' not in finalizer
    assert "days <= 1" not in finalizer


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
    args=[sys.executable,"-",str(path),day,"running","started","0","0",""]+["true"]*7
    path.write_text(json.dumps(origin))
    result=subprocess.run(args,input=body,text=True,capture_output=True,env=env)
    assert result.returncode==0,result.stderr
    assert json.loads(path.read_text())["reused_steps_receipt"]["origin_run_id"]=="original"
    retry = json.loads(path.read_text())
    retry['status'] = 'failed'
    path.write_text(json.dumps(retry))
    reused = modules[0]
    inherited = dict(receipt, origin_run_id='retry', origin_code_commit='b'*40,
                     inherited_receipt_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),
                     reused_modules=modules, command_receipts=receipt['command_receipts'])
    next_proof = tmp_path/'reuse-next.json'; next_proof.write_text(json.dumps(inherited))
    next_env = dict(env, POSTCLOSE_REUSE_RECEIPT=str(next_proof),POSTCLOSE_RUN_ID='third')
    result=subprocess.run(args,input=body,text=True,capture_output=True,env=next_env)
    assert result.returncode == 0, result.stderr
    function = 'verified_reused_module() {' + _text('deploy/run_threshold_cycle_postclose.sh').split('verified_reused_module() {',1)[1].split('reusable_completed_artifact() {',1)[0]
    check_env=dict(os.environ, VENV_PY=sys.executable, STATUS_FILE=str(path))
    command=function+'\nverified_reused_module '+reused
    assert subprocess.run(['bash','-c',command],env=check_env,capture_output=True).returncode == 0
    next_proof.write_text('{}')
    assert subprocess.run(['bash','-c',command],env=check_env,capture_output=True).returncode == 2
    retired = 'src.engine.monitoring.low_price_two_leg_expanded_candidate_research'
    rejected = dict(inherited, reused_modules=modules + [retired],
                    command_receipts=receipt['command_receipts'] + [
                        dict(producer_module=retired, run_id='retry', exit_code=0,
                             target_date=day, code_commit='b'*40, measurement_complete=True)])
    next_proof.write_text(json.dumps(rejected))
    before = path.read_bytes()
    result = subprocess.run(args, input=body, text=True, capture_output=True, env=next_env)
    assert result.returncode != 0 and path.read_bytes() == before
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


def test_scoped_final_verification_respects_disabled_machine_schedule():
    script=(Path(__file__).resolve().parents[2]/'deploy/run_threshold_cycle_postclose.sh').read_text()
    final=script[script.index('--stage wait --date'):]
    assert final.index('if [[ "$RUN_AI_DECISION_ACTION_OUTCOME_CALIBRATION"') < final.index('for stage in legacy_machine_report main_auxiliary_policy')
def test_busy_preopen_preserves_exact_current_producer_status(tmp_path):
    import fcntl, os, subprocess
    from pathlib import Path
    project=Path(__file__).resolve().parents[2]
    logs=tmp_path/'logs';logs.mkdir()
    status=tmp_path/'data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-10-12.status.json'
    status.parent.mkdir(parents=True);status.write_bytes(b'{"status":"failed","original_attempt":true}\n')
    before=status.read_bytes()
    with (logs/'runtime_policy_preopen.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=subprocess.run(['bash',str(project/'deploy/run_threshold_cycle_preopen.sh'),'2026-10-12'],
            env={**os.environ,'PROJECT_DIR':str(tmp_path),'VENV_PY':'/must-not-execute'},capture_output=True,text=True,timeout=10)
    assert result.returncode==0 and '[SKIP]' in result.stdout
    assert status.read_bytes()==before
