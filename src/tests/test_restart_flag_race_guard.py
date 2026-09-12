import inspect
import ast
import subprocess

import pytest
from pathlib import Path

import src.bot_main as bot_main
from src.engine import kiwoom_sniper_v2


def test_bot_main_restart_flag_consumption_is_owner_guarded():
    source = inspect.getsource(bot_main)
    assert "consume_guarded_restart_request(" in source
    assert "restart_guard_decision(main_bot_pid=os.getpid())" in source
    assert "source=unknown_legacy_touch" in source
    assert "record_scheduled_restart_block(" in source


def test_sniper_engine_restart_flag_claim_terminates_the_whole_process():
    source = inspect.getsource(kiwoom_sniper_v2)
    assert "consume_guarded_restart_request(" in source
    assert "os.kill(os.getpid(), signal.SIGTERM)" in source


def test_restart_script_publishes_request_metadata_atomically():
    source = Path("restart.sh").read_text(encoding="utf-8")

    assert (
        'RESTART_SOURCE="${KORSTOCKSCAN_RESTART_REQUEST_SOURCE:-operator_restart_sh}"'
        in source
    )
    assert 'RESTART_REQUEST_TMP="${RESTART_FLAG}.$$"' in source
    assert 'mv -f "$RESTART_REQUEST_TMP" "$RESTART_FLAG"' in source
    assert "requested_at_utc=" in source
    assert "--action prepare" in source
    assert "--action commit" in source
    assert "--action abort" in source
    assert "SAMSUNG_MAIN_BOT_RESTART_HANDOFF" in source
    assert "cleanup_restart_request" in source
    assert 'kill -0 "$HANDOFF_OLD_PID"' in source
    assert '[ -f "$SAMSUNG_HANDOFF_PLAN" ]' in source


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
    assert "exec ./run_bot.sh" in source
    assert 'exit "$VERIFY_RC"' in source


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
    source = Path("src/run_bot.sh").read_text()
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


def test_launcher_clears_auto_promotion_pins_before_loading_handoff():
    source = Path("src/run_bot.sh").read_text()
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
    "allowed,reason,plan_id,expected_rc",
    [
        (True, "prepared_same_date_pid_handoff", "exact-plan", 0),
        (False, "handoff_plan_expired", "exact-plan", 3),
        (True, "prepared_same_date_pid_handoff", "other-plan", 3),
        (True, "morning_owner_not_active", "exact-plan", 3),
    ],
)
def test_restart_staged_env_requires_exact_prepared_guard(
    monkeypatch, allowed, reason, plan_id, expected_rc
):
    import sys
    from src.trading.samsung_morning_one_share import authority_handoff as handoff

    script = Path("restart.sh").read_text().split("<<'PY_PREPARED_HANDOFF'", 1)[1]
    script = script.split("\n", 1)[1].split("\nPY_PREPARED_HANDOFF", 1)[0]
    monkeypatch.setattr(sys, "argv", ["-", "1234", "exact-plan"])
    calls = []

    def check(**kwargs):
        calls.append(kwargs)
        return {"allowed": allowed, "reason": reason, "plan_id": plan_id}

    monkeypatch.setattr(handoff, "restart_guard_decision", check)
    with pytest.raises(SystemExit) as caught:
        exec(compile(script, "restart_prepared_handoff", "exec"), {})
    assert caught.value.code == expected_rc
    assert calls == [{"main_bot_pid": 1234}]
