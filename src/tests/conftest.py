from datetime import datetime as _REAL_DATETIME
from pathlib import Path
import tempfile
import os
import sys
import subprocess

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]



def _reject_production_mutation(event, args, roots):
    """Fail before Python writes/replaces/unlinks a production artifact.

    Real paths also protect runtime-release symlinks. This process-wide guard
    remains installed for late workers after fixture teardown. Child commands
    that do not inherit Python hooks require the existing OS-isolated runner.
    """
    paths = []
    if event == 'open':
        path, mode, flags = args
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            paths.append((path, None))
    elif event in {'os.rename', 'os.link'}:
        paths.extend(((args[0], args[2]), (args[1], args[3])))
    elif event == 'os.symlink':
        paths.append((args[1], args[2]))
    elif event in {'os.remove', 'os.rmdir', 'os.mkdir', 'os.chmod', 'os.chown', 'os.utime', 'os.truncate'}:
        index = {'os.remove': 1, 'os.rmdir': 1, 'os.mkdir': 2, 'os.chmod': 2,
                 'os.chown': 3, 'os.utime': 3}.get(event)
        paths.append((args[0], args[index] if index is not None and len(args) > index else None))
    for value, directory in paths:
        if isinstance(value, int):
            value = f'/proc/self/fd/{value}'
        if not isinstance(value, (str, bytes, os.PathLike)):
            continue
        path = Path(os.fsdecode(value))
        if not path.is_absolute() and directory not in (None, -1):
            path = Path(f'/proc/self/fd/{directory}').resolve() / path
        path = path.resolve()
        if any(path == root or path.is_relative_to(root) for root in roots):
            raise PermissionError(f'unit_test_production_write_forbidden:{event}:{path}')


def pytest_configure(config):
    """Never let unit-test fallback workers reach the real HTTP service.

    Configure is also called for conftests discovered after session start.
    Session lifetime matters: a bounded quote worker may outlive its test's
    monkeypatch fixture. Explicit HTTP response mocks still override this
    default; unmocked calls follow the normal transport-failure path.
    """
    common = Path(subprocess.check_output(
        ['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
        cwd=_REPOSITORY_ROOT, text=True, timeout=10).strip()).resolve().parent
    roots = tuple((root / name).resolve() for root in {_REPOSITORY_ROOT, common}
                  for name in ('data', 'logs'))
    sys.addaudithook(lambda event, args: _reject_production_mutation(event, args, roots))
    # Use the existing Linux filesystem boundary for the whole test process.
    # Python hooks alone do not protect native extensions or child commands.
    import ctypes
    from src.engine.infrastructure.startup_validation_isolation import _landlock
    scratch = [Path(tempfile.gettempdir()).resolve(), _REPOSITORY_ROOT / '.pytest_cache']
    if config.option.basetemp:
        scratch.append(Path(config.option.basetemp).resolve())
    for path in scratch:
        if any(path == root or path.is_relative_to(root) or root.is_relative_to(path) for root in roots):
            raise RuntimeError('unit_test_writable_root_overlaps_production')
        path.mkdir(parents=True, exist_ok=True)
    # Multiprocessing regression fixtures use native POSIX semaphores.
    # Production data/logs remain outside this IPC-only writable directory.
    sys.dont_write_bytecode = True
    _landlock(ctypes.CDLL(None, use_errno=True), scratch[0],
              test_roots=tuple(scratch) + (Path('/dev/null'), Path('/dev/shm')))
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
    # This owner creates its default directories at import, before fixtures.
    # Keep that import under the same scratch boundary; never weaken the guard.
    from src.utils import constants
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(constants, "DATA_DIR", root / "data")
        import src.engine.log_archive_service  # noqa: F401


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
    from src.trading.market import transport_epoch
    monkeypatch.setattr(transport_epoch, "DEFAULT_PATH", tmp_path / "runtime/kiwoom_ws_transport_epoch.json")
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
