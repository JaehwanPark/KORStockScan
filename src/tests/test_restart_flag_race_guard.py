import inspect

import src.bot_main as bot_main
from src.engine import kiwoom_sniper_v2


def test_bot_main_restart_flag_unlink_is_race_safe():
    source = inspect.getsource(bot_main)
    assert "RESTART_FLAG_PATH.unlink(missing_ok=True)" in source


def test_sniper_engine_restart_flag_unlink_is_race_safe():
    source = inspect.getsource(kiwoom_sniper_v2)
    assert "RESTART_FLAG_PATH.unlink(missing_ok=True)" in source
