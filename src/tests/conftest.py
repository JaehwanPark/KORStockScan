import pytest


@pytest.fixture(autouse=True)
def isolate_module_logs(tmp_path, monkeypatch):
    import src.utils.logger as logger

    for active_logger in logger._MODULE_LOGGERS.values():
        for handler in list(active_logger.handlers):
            active_logger.removeHandler(handler)
            handler.close()
    logger._MODULE_LOGGERS.clear()

    monkeypatch.setattr(logger, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(logger, "LEGACY_LOGS_DIR", tmp_path / "legacy_logs")

    yield

    for active_logger in logger._MODULE_LOGGERS.values():
        for handler in list(active_logger.handlers):
            active_logger.removeHandler(handler)
            handler.close()
    logger._MODULE_LOGGERS.clear()


@pytest.fixture
def token():
    pytest.skip("token fixture not configured; skipping inventory API tests")
