import importlib
import sys


def test_final_ensemble_scanner_import_does_not_start_telegram_manager():
    sys.modules.pop("src.scanners.final_ensemble_scanner", None)
    sys.modules.pop("src.notify.telegram_manager", None)

    importlib.import_module("src.scanners.final_ensemble_scanner")

    assert "src.notify.telegram_manager" not in sys.modules


def test_crisis_monitor_import_keeps_runtime_dependencies_lazy():
    sys.modules.pop("src.scanners.crisis_monitor", None)

    module = importlib.import_module("src.scanners.crisis_monitor")

    assert not hasattr(module, "db_manager")
    assert not hasattr(module, "event_bus")
