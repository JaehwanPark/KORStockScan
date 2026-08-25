from datetime import datetime as _REAL_DATETIME
from pathlib import Path

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def isolate_module_logs(tmp_path, monkeypatch):
    from src.engine.ai.hot_path_ai_symbol_budget import (
        DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET,
    )
    from src.engine.scalping.position_peak_ledger import POSITION_PEAK_LEDGER
    import src.engine.sniper_state_handlers as sniper_state_handlers
    import src.engine.sniper_execution_receipts as sniper_execution_receipts
    import src.engine.sniper_s15_fast_track as sniper_s15_fast_track
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
    production_custody_roots = (
        _REPOSITORY_ROOT / "data/runtime/sell_receipt_recovery",
        _REPOSITORY_ROOT / "data/runtime/s15_fast_custody",
    )

    def _custody_snapshot():
        snapshot = {}
        for root in production_custody_roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    stat = path.stat()
                    snapshot[str(path)] = (stat.st_size, stat.st_mtime_ns)
        return snapshot

    production_custody_snapshot = _custody_snapshot()
    monkeypatch.setattr(
        sniper_execution_receipts,
        "SELL_RECEIPT_RECOVERY_DIR",
        tmp_path / "runtime" / "sell_receipt_recovery",
    )
    sniper_execution_receipts._SELL_RECEIPT_RECOVERY_LAST_PRUNE_AT = 0.0
    monkeypatch.setattr(
        sniper_s15_fast_track,
        "S15_CUSTODY_DIR",
        tmp_path / "runtime" / "s15_fast_custody",
    )
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
    assert _custody_snapshot() == production_custody_snapshot
    for active_logger in logger._MODULE_LOGGERS.values():
        for handler in list(active_logger.handlers):
            active_logger.removeHandler(handler)
            handler.close()
    logger._MODULE_LOGGERS.clear()


@pytest.fixture
def token():
    pytest.skip("token fixture not configured; skipping inventory API tests")
