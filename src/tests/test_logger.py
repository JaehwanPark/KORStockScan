from __future__ import annotations

import logging
import multiprocessing

from src.utils.logger import ProcessSafeRotatingFileHandler


def _write_shared_log(path: str, worker: int, count: int) -> None:
    logger = logging.getLogger(f"process-safe-module-log-{worker}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = ProcessSafeRotatingFileHandler(
        path,
        maxBytes=256,
        backupCount=128,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    try:
        for index in range(count):
            logger.info("worker=%s index=%s", worker, index)
            assert handler.stream is None
    finally:
        logger.removeHandler(handler)
        handler.close()


def test_process_safe_rotating_handler_preserves_concurrent_records(tmp_path):
    log_path = tmp_path / "logs" / "shared_info.log"
    log_path.parent.mkdir(parents=True)
    worker_count = 4
    record_count = 60
    context = multiprocessing.get_context("fork")
    workers = [
        context.Process(
            target=_write_shared_log,
            args=(str(log_path), worker, record_count),
        )
        for worker in range(worker_count)
    ]

    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=20)
        assert worker.exitcode == 0

    paths = [log_path, *sorted(log_path.parent.glob("shared_info.log.*"))]
    rows = []
    for path in paths:
        if path.is_file():
            rows.extend(path.read_text(encoding="utf-8").splitlines())

    expected = {
        f"worker={worker} index={index}"
        for worker in range(worker_count)
        for index in range(record_count)
    }
    assert len(rows) == len(expected)
    assert set(rows) == expected
    assert not any(path.name.endswith(".lock") for path in paths)


def test_process_safe_rotating_handler_rejects_symlink_lock(tmp_path):
    log_path = tmp_path / "logs" / "shared_info.log"
    handler = ProcessSafeRotatingFileHandler(
        log_path,
        maxBytes=256,
        backupCount=2,
        encoding="utf-8",
    )
    protected = tmp_path / "protected"
    protected.write_text("unchanged", encoding="utf-8")
    handler._process_lock_path.symlink_to(protected)

    try:
        handler.emit(
            logging.LogRecord("test", logging.INFO, __file__, 1, "blocked", (), None)
        )
    finally:
        handler.close()

    assert protected.read_text(encoding="utf-8") == "unchanged"
    assert not log_path.exists()
