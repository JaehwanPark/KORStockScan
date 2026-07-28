from datetime import datetime as _REAL_DATETIME

import pytest


@pytest.fixture(autouse=True)
def isolate_module_logs(tmp_path, monkeypatch):
    from src.engine.ai.hot_path_ai_symbol_budget import (
        DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET,
    )
    from src.engine.scalping.position_peak_ledger import POSITION_PEAK_LEDGER
    import src.engine.sniper_state_handlers as sniper_state_handlers
    import src.utils.logger as logger
    import src.utils.pipeline_event_logger as pipeline_event_logger
    from src.utils.constants import TRADING_RULES as DEFAULT_TRADING_RULES

    for active_logger in logger._MODULE_LOGGERS.values():
        for handler in list(active_logger.handlers):
            active_logger.removeHandler(handler)
            handler.close()
    logger._MODULE_LOGGERS.clear()

    monkeypatch.setattr(logger, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(logger, "LEGACY_LOGS_DIR", tmp_path / "legacy_logs")

    # Pipeline events are production artifacts during intraday runs. Some state
    # handler tests intentionally exercise real logging paths, so keep JSONL and
    # threshold compact events inside the pytest temp dir.
    monkeypatch.setattr(pipeline_event_logger, "DATA_DIR", tmp_path / "data")
    pipeline_event_logger._PRODUCER_COMPACTOR = None
    DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET.reset()
    # A number of legacy state-handler tests replace these module globals
    # directly instead of using monkeypatch. Reset them at both boundaries so
    # the next test never inherits a historical market clock or runtime rule.
    sniper_state_handlers.datetime = _REAL_DATETIME
    sniper_state_handlers.TRADING_RULES = DEFAULT_TRADING_RULES
    monkeypatch.setattr(
        POSITION_PEAK_LEDGER,
        "path",
        tmp_path / "runtime" / "scalp_position_peak_state.json",
    )

    yield

    pipeline_event_logger._PRODUCER_COMPACTOR = None
    DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET.reset()
    sniper_state_handlers.datetime = _REAL_DATETIME
    sniper_state_handlers.TRADING_RULES = DEFAULT_TRADING_RULES
    for active_logger in logger._MODULE_LOGGERS.values():
        for handler in list(active_logger.handlers):
            active_logger.removeHandler(handler)
            handler.close()
    logger._MODULE_LOGGERS.clear()


@pytest.fixture
def token():
    pytest.skip("token fixture not configured; skipping inventory API tests")
