from pathlib import Path

from src.engine import log_archive_service as service


def test_monitor_snapshot_roundtrip(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(service, "MONITOR_SNAPSHOT_DIR", snapshot_dir)

    payload = {"date": "2026-04-06", "value": 123}
    path = service.save_monitor_snapshot("trade_review", "2026-04-06", payload)

    assert path == snapshot_dir / "trade_review_2026-04-06.json"
    assert service.load_monitor_snapshot("trade_review", "2026-04-06") == payload


def test_archive_and_replay_daily_log_slice(tmp_path, monkeypatch):
    archive_dir = tmp_path / "log_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(service, "LOG_ARCHIVE_DIR", archive_dir)

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "sniper_state_handlers_info.log"
    rotated_path = logs_dir / "sniper_state_handlers_info.log.1"

    rotated_path.write_text(
        "[2026-04-05 15:30:00] old\n"
        "[2026-04-06 09:10:00] keep [HOLDING_PIPELINE] first\n",
        encoding="utf-8",
    )
    log_path.write_text(
        "[2026-04-06 09:11:00] keep [HOLDING_PIPELINE] second\n"
        "[2026-04-07 09:00:00] future\n",
        encoding="utf-8",
    )

    archived = service.archive_target_date_logs("2026-04-06", [log_path])

    assert len(archived) == 1
    archive_path = archive_dir / "2026-04-06" / "sniper_state_handlers_info.log.gz"
    assert archive_path.exists()

    log_path.unlink()
    rotated_path.unlink()

    lines = service.iter_target_log_lines(
        [log_path],
        target_date="2026-04-06",
        marker="[HOLDING_PIPELINE]",
    )
    assert sorted(lines) == [
        "[2026-04-06 09:10:00] keep [HOLDING_PIPELINE] first",
        "[2026-04-06 09:11:00] keep [HOLDING_PIPELINE] second",
    ]
