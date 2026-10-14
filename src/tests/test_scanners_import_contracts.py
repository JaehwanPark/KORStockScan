import importlib
import sys
from datetime import time
from pathlib import Path


def test_final_ensemble_scanner_import_does_not_start_telegram_manager():
    sys.modules.pop("src.scanners.final_ensemble_scanner", None)
    sys.modules.pop("src.notify.telegram_manager", None)

    importlib.import_module("src.scanners.final_ensemble_scanner")

    assert "src.notify.telegram_manager" not in sys.modules


def test_final_ensemble_scanner_has_no_start_of_day_ai_report_path():
    source = Path("src/scanners/final_ensemble_scanner.py").read_text()

    forbidden_fragments = [
        "START_OF_DAY_REPORT",
        "오늘의 AI 리포트",
        "AI 수석 브리핑",
        "analyze_scanner_results",
        "MacroBriefingBuilder",
        "GPTSniperEngine",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_telegram_manager_has_no_start_of_day_ai_report_handler():
    source = Path("src/notify/telegram_manager.py").read_text()

    assert "START_OF_DAY_REPORT" not in source
    assert "오늘의 AI 리포트" not in source


def test_retired_news_scanner_has_no_startup_database_or_dependency_surface():
    from src.database import models
    from src.database.db_manager import DBManager

    root = Path(__file__).resolve().parents[2]
    assert importlib.util.find_spec("src.scanners.crisis_monitor") is None
    assert "crisis_monitor" not in (root / "src/bot_main.py").read_text()
    assert "macro_alerts" not in models.Base.metadata.tables
    assert not hasattr(models, "MacroAlert")
    assert not hasattr(DBManager, "save_macro_alert")
    assert not hasattr(DBManager, "get_recent_risk_count")
    requirements = (root / "requirements.txt").read_text().splitlines()
    assert "feedparser" not in requirements
    assert "deep-translator" not in requirements


def test_scalping_scanner_discovery_time_uses_scalping_buy_window(monkeypatch):
    sys.modules.pop("src.scanners.scalping_scanner", None)

    module = importlib.import_module("src.scanners.scalping_scanner")
    monkeypatch.setattr(
        module,
        "is_scalping_buy_time_allowed",
        lambda now_time: time(8, 5) <= now_time <= time(8, 40)
        or time(9, 5) <= now_time <= time(15, 20)
        or time(16, 0) <= now_time <= time(19, 20),
    )

    assert module._is_scanner_discovery_time(time(8, 4, 59)) is False
    assert module._is_scanner_discovery_time(time(8, 5)) is True
    assert module._is_scanner_discovery_time(time(8, 41)) is False
    assert module._is_scanner_discovery_time(time(9, 5)) is True
    assert module._is_scanner_discovery_time(time(15, 20)) is True
    assert module._is_scanner_discovery_time(time(15, 20, 1)) is False
    assert module._is_scanner_discovery_time(time(16, 0)) is True
    assert module._is_scanner_discovery_time(time(19, 20)) is True
    assert module._is_scanner_discovery_time(time(19, 20, 1)) is False


def test_scalping_scanner_discovery_ignores_legacy_open_close_env(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SCANNER_DISCOVERY_OPEN_TIME", "08:00:00")
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_SCANNER_DISCOVERY_CLOSE_TIME", "19:45:00")
    sys.modules.pop("src.scanners.scalping_scanner", None)

    module = importlib.import_module("src.scanners.scalping_scanner")
    monkeypatch.setattr(
        module, "is_scalping_buy_time_allowed", lambda now_time: now_time == time(9, 5)
    )

    assert module._is_scanner_discovery_time(time(8, 0)) is False
    assert module._is_scanner_discovery_time(time(9, 5)) is True
