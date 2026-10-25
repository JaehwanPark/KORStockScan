import inspect
import ast
import subprocess

import pytest
from pathlib import Path

import src.bot_main as bot_main
from src.engine import kiwoom_sniper_v2


def test_bot_main_restart_flag_consumption_is_owner_guarded():
    source = inspect.getsource(bot_main)
    assert "consume_restart_request(" in source
    assert "samsung_morning_one_share" not in source
    assert "source=unknown_legacy_touch" in source


def test_sniper_engine_restart_flag_claim_requests_cooperative_shutdown():
    source = inspect.getsource(kiwoom_sniper_v2)
    assert "consume_restart_request(" in source
    assert "os.kill(os.getpid(), signal.SIGTERM)" not in source
    assert "request_shutdown()" in inspect.getsource(
        kiwoom_sniper_v2._run_sniper_iterations
    )


def test_restart_script_publishes_request_metadata_atomically():
    source = Path("restart.sh").read_text(encoding="utf-8")

    assert (
        'RESTART_SOURCE="${KORSTOCKSCAN_RESTART_REQUEST_SOURCE:-operator_restart_sh}"'
        in source
    )
    assert 'RESTART_REQUEST_TMP="${RESTART_FLAG}.$$"' in source
    assert 'mv -f "$RESTART_REQUEST_TMP" "$RESTART_FLAG"' in source
    assert "requested_at_utc=" in source
    assert "cleanup_restart_request" in source


def test_restart_script_reloads_stale_supervisor_only_after_child_drain():
    source = Path("restart.sh").read_text(encoding="utf-8")

    drift_check = source.index("Launcher generation drift detected")
    child_drain = source.index('if [ "$elapsed" -ge "$STOP_TIMEOUT_SEC" ]')
    supervisor_reload = source.index(
        'if [ "$RELOAD_SUPERVISOR" = true ]; then', child_drain
    )
    new_pid_wait = source.index("elapsed=0", supervisor_reload)

    assert drift_check < child_drain < supervisor_reload < new_pid_wait
    assert 'tmux kill-session -t "$BOT_TMUX_SESSION"' in source
    assert "Refusing supervisor reload because a bot child is alive" in source
    assert 'if tmux has-session -t "$BOT_TMUX_SESSION"' in source
    assert "confirmed session removal" in source
    assert "router.main_supervisor_command(root)" in source
    assert source.index("MAIN_SUPERVISOR_COMMAND=") < source.index(
        'echo "Requesting graceful'
    )
    assert 'exit "$VERIFY_RC"' in source


def test_restart_script_uses_current_bootstrap_pid_receipt_contract():
    source = Path("restart.sh").read_text(encoding="utf-8")

    assert "src.engine.automation.runtime_policy_bootstrap" in source
    assert "runtime_policy_bootstrap_verify_${APPLICATION_DATE}.json" in source
    assert "--write-verify-artifact" in source
    assert "src.engine.threshold_cycle_preopen_apply" not in source


@pytest.mark.parametrize(
    "failures,appears,expected_rc,expected_attempts",
    [
        (0, "none", 0, 1),
        (1, "none", 0, 2),
        (3, "none", 1, 3),
        (1, "session", 1, 1),
        (1, "child", 1, 1),
        (0, "initial_child", 1, 0),
    ],
)
def test_drained_supervisor_retries_only_without_a_session_or_child(
    failures, appears, expected_rc, expected_attempts
):
    source = Path("restart.sh").read_text()
    function = (
        "restart_drained_tmux_supervisor() {"
        + source.split("restart_drained_tmux_supervisor() {", 1)[1].split("\n}\n", 1)[0]
        + "\n}\n"
    )
    script = (
        """
set -eu
failures=$1; appears=$2; attempts=0; session=1; child=0
BOT_TMUX_SESSION=isolated_test; PROJECT_DIR=/unused; MAIN_SUPERVISOR_COMMAND=fixture_command
if [ "$appears" = initial_child ]; then child=1; fi
bot_pids() { if [ "$child" = 1 ]; then echo 999; fi; }
sleep() { :; }
tmux() {
    case "$1" in
        has-session) [ "$session" = 1 ] ;;
        kill-session) session=0; return 1 ;;
        new-session)
            attempts=$((attempts+1))
            if [ "$attempts" -le "$failures" ]; then
                if [ "$appears" = session ]; then session=1; fi
                if [ "$appears" = child ]; then child=1; fi
                return 1
            fi
            session=1; return 0 ;;
        *) return 99 ;;
    esac
}
"""
        + function
        + """
rc=0
restart_drained_tmux_supervisor || rc=$?
echo "RESULT:$rc:$attempts"
"""
    )
    result = subprocess.run(
        ["bash", "-c", script, "test", str(failures), appears],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    assert f"RESULT:{expected_rc}:{expected_attempts}" in result.stdout


def test_release_restart_flag_preserves_shared_symlink_when_claimed(tmp_path):
    source = Path("restart.sh").read_text()
    assert 'RESTART_FLAG="$(realpath -m "$PROJECT_DIR/restart.flag")"' in source
    assert (
        'RESTART_FLAG_PATH = (PROJECT_ROOT / "restart.flag").resolve()'
        in Path("src/utils/constants.py").read_text()
    )
    state = tmp_path / "state"
    release = tmp_path / "release"
    state.mkdir()
    release.mkdir()
    shared = state / "restart.flag"
    linked = release / "restart.flag"
    linked.symlink_to(shared)
    shell_target = subprocess.check_output(
        ["realpath", "-m", str(linked)], text=True
    ).strip()
    assert Path(shell_target) == linked.resolve() == shared
    Path(shell_target).write_text("test request")
    linked.resolve().unlink()
    assert linked.is_symlink() and not shared.exists()


def test_release_source_root_change_requires_drained_supervisor_reload():
    source = Path("restart.sh").read_text()
    gate = source.split("RELOAD_SUPERVISOR=false", 1)[1].split(
        'echo "Requesting graceful bot restart', 1
    )[0]
    assert '[ "$LOADED_SOURCE_ROOT" != "$PROJECT_DIR" ]' in gate
    assert "RELOAD_SUPERVISOR=true" in gate


def test_launcher_clears_intraday_pins_before_loading_dated_authority():
    source = Path("src/engine/infrastructure/main_policy_environment.sh").read_text()
    reset = source.split("reset_runtime_policy_env_before_handoff() {", 1)[1].split(
        "\n}", 1
    )[0]
    path_key = "KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_PATH"
    sha_key = "KORSTOCKSCAN_ENTRY_SETUP_INTRADAY_APPROVAL_SHA256"
    command = (
        f"export {path_key}=yesterday {sha_key}=old_hash\n"
        + reset
        + f'\ntest -z "${{{path_key}+set}}" && test -z "${{{sha_key}+set}}"'
    )
    subprocess.run(["bash", "-c", command], check=True)


def test_launcher_imports_selected_release_despite_inherited_pythonpath(tmp_path):
    import os
    import sys

    selected = tmp_path / "selected"
    previous = tmp_path / "previous"
    for directory, marker in ((selected, "selected"), (previous, "previous")):
        directory.mkdir()
        (directory / "release_binding_probe.py").write_text(f"MARKER = {marker!r}\n")
    source = Path("src/run_bot.sh").read_text()
    body = source.split("export_runtime_source_provenance() {", 1)[1].split("\n}", 1)[0]
    command = (
        "export_runtime_source_provenance() {" + body + "\n}\n"
        'export_runtime_source_provenance\n"$PROBE_PYTHON" -c '
        "'import release_binding_probe; print(release_binding_probe.MARKER)'"
    )
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=tmp_path,
        check=True,
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "PROJECT_DIR": str(selected),
            "PYTHONPATH": str(previous),
            "PROBE_PYTHON": sys.executable,
        },
    )
    assert result.stdout.splitlines()[-1] == "selected"


def test_launcher_clears_auto_promotion_pins_before_loading_handoff():
    source = Path("src/engine/infrastructure/main_policy_environment.sh").read_text()
    reset = source.split("reset_runtime_policy_env_before_handoff() {", 1)[1].split(
        "\n}", 1
    )[0]
    path_key = "KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_PATH"
    sha_key = "KORSTOCKSCAN_SCALPING_PROMPT_AUTO_PROMOTION_SHA256"
    command = (
        f"export {path_key}=yesterday {sha_key}=old_hash\n"
        + reset
        + f'\ntest -z "${{{path_key}+set}}" && test -z "${{{sha_key}+set}}"'
    )
    subprocess.run(["bash", "-c", command], check=True)


def test_release_mount_resolution_preserves_artifact_no_follow_guard(tmp_path):
    from src.utils.jsonl_io import read_json_object_strict

    release = tmp_path / "release"
    state = tmp_path / "shared-data"
    release.mkdir()
    state.mkdir()
    (release / "data").symlink_to(state)
    (state / "sample.json").write_text('{"valid":true}')
    tree = ast.parse(Path("src/utils/constants.py").read_text())
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "DATA_DIR"
            for target in node.targets
        )
    )
    canonical_data = eval(
        compile(ast.Expression(assignment.value), "constants", "eval"),
        {"PROJECT_ROOT": release},
    )
    assert canonical_data == state
    assert read_json_object_strict(canonical_data / "sample.json") == {"valid": True}
    with pytest.raises(ValueError, match="parent_invalid"):
        read_json_object_strict(release / "data" / "sample.json")


def test_context_promotion_uses_canonical_data_identity():
    from src.engine.scalping import multi_timeframe_context as context
    from src.utils.constants import DATA_DIR

    assert context.PROMOTION_DIR == DATA_DIR / "runtime"
    assert context.RUNTIME_ENV_DIR == DATA_DIR / "threshold_cycle/runtime_env"


@pytest.mark.parametrize(
    "claimant", ["src/bot_main.py", "src/engine/kiwoom_sniper_v2.py"]
)
def test_restart_claimant_closes_real_epoch_before_process_exit(tmp_path, claimant):
    import json
    import os
    import sys

    tree = ast.parse(Path(claimant).read_text())
    branch = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and ast.unparse(node.test) == "RESTART_FLAG_PATH.exists()"
    )
    branch_source = ast.unparse(branch)
    # Execute the actual claim branch in an isolated process, with real request
    # coordination, collector, writer, WS cleanup and native final consumer.
    script = """
import json, os, signal, sys, threading, time
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime
from src.engine.infrastructure import restart_requests as R
from src.engine.scalping.micro_reversion import canary_monitor as C
from src.engine.scalping.micro_reversion.forward_collector import ForwardObservationCollector, ForwardCollectorConfig
from src.engine.scalping.micro_reversion.observation_adapter import ObserverFeatureFlags
from src.engine.kiwoom_websocket import KiwoomWSManager
from src.tests.test_micro_reversion_forward_collector import _snapshot
from src.engine.scalping.continuous_reversal_source import _source_quality_receipt
root = Path(sys.argv[1]); branch = sys.argv[2]; claimant = sys.argv[3]
c = ForwardObservationCollector(flags=ObserverFeatureFlags(observer_enabled=True, path_capture_enabled=True),
    config=ForwardCollectorConfig(output_root=root/'data/observations/scalp_micro_reversion_forward'))
c.start()
c.observe_kiwoom_0b('000001', _snapshot(), realtime_type='0B')
for _ in range(65): c.observe_kiwoom_0b('000001', _snapshot(exchange_time='invalid'), realtime_type='0B')
manager = KiwoomWSManager('offline-token'); manager._micro_reversion_forward_collector = c
latest = root/'data/runtime/scalp_micro_reversion_forward_collector/latest.json'
manager._persist_micro_reversion_canary_snapshot = lambda: C.write_canary_runtime_snapshot(
    c.runtime_snapshot().as_dict(), output_path=latest, now=datetime.fromisoformat('2026-08-08T20:00:00+09:00'))
flag = root/'restart.flag'; flag.write_text('source=offline-restart-test')
scope = dict(os=os, time=time, signal=signal, RESTART_FLAG_PATH=flag,
    consume_restart_request=lambda path, **kw: R.consume_restart_request(path, lock_path=root/'claim.lock', **kw),
    request_shutdown=R.request_shutdown, event_bus=SimpleNamespace(publish=lambda *a: None),
    _sn_whb=lambda *a, **kw: None, log_error=lambda *a: None)
program = compile('while True:\\n' + ''.join('    '+line+'\\n' for line in branch.splitlines()), '<native restart branch>', 'exec')
def await_request():
    deadline = time.monotonic() + 5
    while not R.shutdown_requested() and time.monotonic() < deadline: time.sleep(.005)
    assert R.shutdown_requested()
def engine():
    try:
        if claimant.endswith('kiwoom_sniper_v2.py'): exec(program, scope)
        else: await_request()
    finally:
        assert manager.stop() is True
thread = threading.Thread(target=engine); thread.start()
if claimant.endswith('bot_main.py'): exec(program, scope)
else: await_request()
# Summary drain is unrelated I/O; it must execute only after immutable close.
def summary():
    assert not thread.is_alive()
    assert _source_quality_receipt(root/'data', '2026-08-08')['eligible']
    (root/'closed-before-exit').write_text('verified')
sys.modules['src.utils.pipeline_event_logger'] = SimpleNamespace(drain_pipeline_event_summary_before_termination=summary)
R.finish_main_shutdown(thread)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), branch_source, claimant],
        capture_output=True,
        text=True,
        timeout=15,
        env={**os.environ, "PYTHONPATH": str(Path.cwd())},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "closed-before-exit").read_text() == "verified"
    assert (
        len(
            list(
                (
                    tmp_path
                    / "data/runtime/scalp_micro_reversion_forward_collector/closed"
                ).glob("*.json")
            )
        )
        == 1
    )


@pytest.mark.parametrize("configuration", ["valid", "missing", "empty", "insecure"])
def test_restart_database_command_is_prepared_before_drain(
    tmp_path, monkeypatch, configuration
):
    import os
    import shutil
    import sys
    from src.engine.infrastructure import runtime_release_router as router

    release = tmp_path / "release"
    target = release / "src/engine/infrastructure/runtime_release_router.py"
    target.parent.mkdir(parents=True)
    shutil.copy2(router.__file__, target)
    constants = release / "src/utils/constants.py"
    constants.parent.mkdir(parents=True)
    shutil.copy2(Path("src/utils/constants.py"), constants)
    retirement = release / "src/engine/lifecycle/retirement.py"
    retirement.parent.mkdir(parents=True)
    shutil.copy2(Path("src/engine/lifecycle/retirement.py"), retirement)
    monkeypatch.delenv("KORSTOCKSCAN_POSTGRES_URL", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_POSTGRES_URL_FILE", raising=False)
    monkeypatch.setenv("KORSTOCKSCAN_REQUIRE_POSTGRES_URL", "1")
    if configuration != "missing":
        secret = tmp_path / "protected-db"
        secret.write_text("" if configuration == "empty" else "fixture-private-value")
        secret.chmod(0o644 if configuration == "insecure" else 0o600)
        monkeypatch.setenv("KORSTOCKSCAN_POSTGRES_URL_FILE", str(secret))
    source = Path("restart.sh").read_text()
    prepare = source.split('MAIN_SUPERVISOR_COMMAND="$(', 1)[1].split(
        '\necho "Requesting graceful bot restart', 1
    )[0]
    script = (
        'set -eu\nMAIN_SUPERVISOR_COMMAND="$('
        + prepare
        + '\nprintf "%s\\n" "$MAIN_SUPERVISOR_COMMAND"\n'
    )
    result = subprocess.run(
        ["bash", "-c", script],
        env={**os.environ, "PROJECT_DIR": str(release), "VENV_PY": sys.executable},
        capture_output=True,
        text=True,
    )
    if configuration == "valid":
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == router.main_supervisor_command(release)
    else:
        assert result.returncode != 0
        expected = {
            "missing": "native_main_database_file_configuration_required",
            "empty": "native_main_database_file_invalid",
            "insecure": "native_main_database_file_invalid",
        }[configuration]
        assert expected in result.stderr
        assert "fixture-private-value" not in result.stderr + result.stdout
