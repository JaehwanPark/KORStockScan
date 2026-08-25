import inspect
from pathlib import Path

import src.bot_main as bot_main
from src.engine import kiwoom_sniper_v2


def test_bot_main_restart_flag_unlink_is_race_safe():
    source = inspect.getsource(bot_main)
    assert "RESTART_FLAG_PATH.unlink(missing_ok=True)" in source
    assert "source=unknown_legacy_touch" in source
    assert "RESTART_FLAG_PATH.read_text" in source


def test_sniper_engine_restart_flag_unlink_is_race_safe():
    source = inspect.getsource(kiwoom_sniper_v2)
    assert "RESTART_FLAG_PATH.unlink(missing_ok=True)" in source


def test_restart_script_publishes_request_metadata_atomically():
    source = Path("restart.sh").read_text(encoding="utf-8")

    assert (
        'RESTART_SOURCE="${KORSTOCKSCAN_RESTART_REQUEST_SOURCE:-operator_restart_sh}"'
        in source
    )
    assert 'RESTART_REQUEST_TMP="${RESTART_FLAG}.$$"' in source
    assert 'mv -f "$RESTART_REQUEST_TMP" "$RESTART_FLAG"' in source
    assert "requested_at_utc=" in source


def test_restart_script_reloads_stale_supervisor_only_after_child_drain():
    source = Path("restart.sh").read_text(encoding="utf-8")

    drift_check = source.index("Launcher generation drift detected")
    child_drain = source.index('if [ "$elapsed" -ge "$STOP_TIMEOUT_SEC" ]')
    supervisor_reload = source.index(
        'if [ "$RELOAD_SUPERVISOR" = true ]; then', child_drain
    )
    new_pid_wait = source.index('elapsed=0', supervisor_reload)

    assert drift_check < child_drain < supervisor_reload < new_pid_wait
    assert 'tmux kill-session -t "$BOT_TMUX_SESSION"' in source
    assert "Refusing supervisor reload because a bot child is alive" in source
    assert 'if tmux has-session -t "$BOT_TMUX_SESSION"' in source
    assert "confirmed session removal" in source
    assert 'exec ./run_bot.sh' in source
    assert 'exit "$VERIFY_RC"' in source
