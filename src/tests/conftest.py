from datetime import datetime as _REAL_DATETIME
from pathlib import Path
import tempfile

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def pytest_configure(config):
    """Never let unit-test fallback workers reach the real HTTP service.

    Configure is also called for conftests discovered after session start.
    Session lifetime matters: a bounded quote worker may outlive its test's
    monkeypatch fixture. Explicit HTTP response mocks still override this
    default; unmocked calls follow the normal transport-failure path.
    """
    import requests
    import src.utils.logger as logger

    def unmocked_http(*_args, **_kwargs):
        raise requests.exceptions.RequestException("unit_test_http_not_mocked")

    requests.sessions.Session.request = unmocked_http
    # Per-test logger patches restore to this isolated session directory,
    # never production logs, including late background-worker completion.
    root = Path(tempfile.mkdtemp(prefix="korstockscan-unit-logs-"))
    logger.LOGS_DIR = root / "logs"
    logger.LEGACY_LOGS_DIR = root / "legacy_logs"


@pytest.fixture(autouse=True)
def isolate_module_logs(tmp_path, monkeypatch):
    from src.engine.ai.hot_path_ai_symbol_budget import (
        DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET,
    )
    from src.engine.scalping import entry_split_order_plan
    from src.engine.scalping.position_peak_ledger import POSITION_PEAK_LEDGER
    import src.engine.sniper_state_handlers as sniper_state_handlers
    import src.engine.sniper_execution_receipts as sniper_execution_receipts
    import src.engine.sniper_s15_fast_track as sniper_s15_fast_track
    import src.utils.logger as logger
    import src.utils.pipeline_event_logger as pipeline_event_logger
    from src.utils.constants import TRADING_RULES as DEFAULT_TRADING_RULES

    for active_logger in tuple(logger._MODULE_LOGGERS.values()):
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
    from src.utils import kiwoom_utils
    monkeypatch.setattr(kiwoom_utils, "DATA_DIR", tmp_path / "data")
    # Probe circuit trips persist across process restarts. Every test must use
    # its own state file, including tests that reach the circuit indirectly.
    monkeypatch.setattr(
        entry_split_order_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "runtime" / "entry_split_probe_runtime_state.json",
    )
    # State-handler tests can persist sim/probe positions even when their
    # broker calls are mocked. Keep those local files out of the running
    # monitor's source population, preserving the default-path session gate.
    sim_state_path = tmp_path / "runtime" / "scalp_live_simulator_state.json"
    monkeypatch.setattr(
        sniper_state_handlers, "DEFAULT_SCALP_SIM_STATE_PATH", sim_state_path
    )
    monkeypatch.setattr(sniper_state_handlers, "SCALP_SIM_STATE_PATH", sim_state_path)
    monkeypatch.setattr(
        sniper_state_handlers,
        "SWING_INTRADAY_PROBE_STATE_PATH",
        tmp_path / "runtime" / "swing_intraday_probe_state.json",
    )
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
    pipeline_event_logger._flush_producer_summary_at_exit()
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

    pipeline_event_logger._flush_producer_summary_at_exit()
    pipeline_event_logger._PRODUCER_COMPACTOR = None
    DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET.reset()
    sniper_state_handlers.datetime = _REAL_DATETIME
    sniper_state_handlers.TRADING_RULES = DEFAULT_TRADING_RULES
    assert _custody_snapshot() == production_custody_snapshot
    for active_logger in tuple(logger._MODULE_LOGGERS.values()):
        for handler in list(active_logger.handlers):
            active_logger.removeHandler(handler)
            handler.close()
    logger._MODULE_LOGGERS.clear()


@pytest.fixture
def token():
    pytest.skip("token fixture not configured; skipping inventory API tests")
