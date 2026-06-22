import importlib
import sys
from datetime import time


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


def test_scalping_scanner_discovery_window_includes_nxt_by_default(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_SCANNER_DISCOVERY_OPEN_TIME", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SCALP_SCANNER_DISCOVERY_CLOSE_TIME", raising=False)
    sys.modules.pop("src.scanners.scalping_scanner", None)

    module = importlib.import_module("src.scanners.scalping_scanner")

    assert module._is_scanner_discovery_time(time(7, 59)) is False
    assert module._is_scanner_discovery_time(time(8, 0)) is True
    assert module._is_scanner_discovery_time(time(17, 30)) is True
    assert module._is_scanner_discovery_time(time(19, 45)) is True
    assert module._is_scanner_discovery_time(time(19, 46)) is False


def test_scalping_scanner_discovery_window_can_be_operator_capped(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SCANNER_DISCOVERY_CLOSE_TIME", "15:00:00")
    sys.modules.pop("src.scanners.scalping_scanner", None)

    module = importlib.import_module("src.scanners.scalping_scanner")

    assert module._is_scanner_discovery_time(time(14, 59)) is True
    assert module._is_scanner_discovery_time(time(17, 30)) is False
