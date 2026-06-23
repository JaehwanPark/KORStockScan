import importlib
import inspect
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


def test_morning_recommendation_broadcast_scheduler_is_removed():
    module = importlib.import_module("src.bot_main")
    source = inspect.getsource(module)

    assert not hasattr(module, "broadcast_today_picks_job")
    assert "morning_report_sent" not in source
    assert "now.hour == 8 and now.minute == 50" not in source
    assert "AI KOSPI 종목추천 리포트" not in source
    assert "초단타(SCALP) 포착 대기열" not in source
