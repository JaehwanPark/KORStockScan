import pytest


@pytest.fixture(autouse=True)
def isolate_module_logs(tmp_path, monkeypatch):
    import src.utils.logger as logger
    import src.utils.pipeline_event_logger as pipeline_event_logger

    for active_logger in logger._MODULE_LOGGERS.values():
        for handler in list(active_logger.handlers):
            active_logger.removeHandler(handler)
            handler.close()
    logger._MODULE_LOGGERS.clear()

    monkeypatch.setattr(logger, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(logger, "LEGACY_LOGS_DIR", tmp_path / "legacy_logs")

    # Pipeline events are production artifacts during intraday runs. Some state
    # handler tests intentionally exercise real logging paths, so keep JSONL,
    # threshold compact events, and DB upsert buffers inside the pytest temp dir.
    monkeypatch.setattr(pipeline_event_logger, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(pipeline_event_logger, "upsert_pipeline_event_rows", lambda *args, **kwargs: None)
    with pipeline_event_logger._DB_WRITE_LOCK:
        pipeline_event_logger._DB_UPSERT_BUFFER.clear()
        pipeline_event_logger._DB_UPSERT_FIRST_TS.clear()
    pipeline_event_logger._PRODUCER_COMPACTOR = None

    yield

    with pipeline_event_logger._DB_WRITE_LOCK:
        pipeline_event_logger._DB_UPSERT_BUFFER.clear()
        pipeline_event_logger._DB_UPSERT_FIRST_TS.clear()
    pipeline_event_logger._PRODUCER_COMPACTOR = None
    for active_logger in logger._MODULE_LOGGERS.values():
        for handler in list(active_logger.handlers):
            active_logger.removeHandler(handler)
            handler.close()
    logger._MODULE_LOGGERS.clear()


@pytest.fixture
def token():
    pytest.skip("token fixture not configured; skipping inventory API tests")
