import importlib
import sys


def test_bot_main_import_does_not_install_runtime_side_effects():
    sys.modules.pop("src.bot_main", None)
    preloaded = set(sys.modules)
    before_stdout = sys.stdout
    before_stderr = sys.stderr

    module = importlib.import_module("src.bot_main")

    loaded_by_import = set(sys.modules) - preloaded
    assert sys.stdout is before_stdout
    assert sys.stderr is before_stderr
    assert "src.notify.telegram_manager" not in loaded_by_import
    assert "src.engine.kiwoom_sniper_v2" not in loaded_by_import
    assert callable(module.install_dual_logger)
