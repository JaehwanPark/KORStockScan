import gzip
import json
import os

from src.engine import backfill_threshold_cycle_events as mod


def test_backfill_threshold_cycle_events_streams_only_target_stages(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(
        mod,
        "_sample_metrics",
        lambda: {
            "cpu": {"iowait_pct": 0.0},
            "io": {"disk_read_mb_delta": 0.0},
            "memory": {"mem_available_mb": 2048.0},
        },
    )

    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "pipeline_events_2026-04-30.jsonl"
    raw_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_type": "pipeline_event",
                        "stage": "budget_pass",
                        "pipeline": "ENTRY_PIPELINE",
                        "stock_name": "A",
                        "stock_code": "111111",
                        "fields": {"x": "1"},
                        "emitted_at": "2026-04-30T09:00:00",
                        "emitted_date": "2026-04-30",
                    }
                ),
                json.dumps(
                    {
                        "event_type": "pipeline_event",
                        "stage": "sell_completed",
                        "pipeline": "HOLDING_PIPELINE",
                        "stock_name": "B",
                        "stock_code": "222222",
                        "fields": {"y": "2"},
                        "emitted_at": "2026-04-30T09:01:00",
                        "emitted_date": "2026-04-30",
                    }
                ),
                json.dumps(
                    {
                        "event_type": "pipeline_event",
                        "stage": "bad_entry_block_observed",
                        "pipeline": "HOLDING_PIPELINE",
                        "stock_name": "C",
                        "stock_code": "333333",
                        "fields": {"z": "3"},
                        "emitted_at": "2026-04-30T09:02:00",
                        "emitted_date": "2026-04-30",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    summary = mod.backfill_threshold_cycle_events("2026-04-30", overwrite=True)
    assert summary["written"] == 3

    compact_path = (
        tmp_path
        / "threshold_cycle"
        / "date=2026-04-30"
        / "family=entry_mechanical_momentum"
        / "part-000001.jsonl"
    )
    bad_entry_path = (
        tmp_path
        / "threshold_cycle"
        / "date=2026-04-30"
        / "family=bad_entry_block"
        / "part-000001.jsonl"
    )
    action_weight_path = (
        tmp_path
        / "threshold_cycle"
        / "date=2026-04-30"
        / "family=statistical_action_weight"
        / "part-000001.jsonl"
    )
    rows = [
        json.loads(line)
        for path in (compact_path, action_weight_path, bad_entry_path)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [row["stage"] for row in rows] == [
        "budget_pass",
        "sell_completed",
        "bad_entry_block_observed",
    ]


def test_backfill_threshold_cycle_events_rolls_partition_without_pause(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(
        mod,
        "_sample_metrics",
        lambda: {
            "cpu": {"iowait_pct": 0.0},
            "io": {"disk_read_mb_delta": 0.0},
            "memory": {"mem_available_mb": 2048.0},
        },
    )
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "pipeline_events_2026-04-30.jsonl"
    raw_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "event_type": "pipeline_event",
                    "stage": "budget_pass",
                    "fields": {"idx": idx},
                }
            )
            for idx in range(3)
        ),
        encoding="utf-8",
    )

    summary = mod.backfill_threshold_cycle_events(
        "2026-04-30",
        overwrite=True,
        max_output_lines_per_partition=2,
        max_input_lines_per_chunk=10,
    )
    assert summary["completed"] is True
    assert summary["paused_reason"] is None
    assert summary["written"] == 3

    parts = sorted(
        (
            tmp_path
            / "threshold_cycle"
            / "date=2026-04-30"
            / "family=entry_mechanical_momentum"
        ).glob("*.jsonl")
    )
    assert [path.name for path in parts] == ["part-000001.jsonl", "part-000002.jsonl"]
    assert (
        sum(
            1
            for path in parts
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        == 3
    )


def test_backfill_threshold_cycle_events_stops_on_source_truncate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(
        mod,
        "_sample_metrics",
        lambda: {
            "cpu": {"iowait_pct": 0.0},
            "io": {"disk_read_mb_delta": 0.0},
            "memory": {"mem_available_mb": 2048.0},
        },
    )
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "pipeline_events_2026-04-30.jsonl"
    raw_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "event_type": "pipeline_event",
                    "stage": "budget_pass",
                    "fields": {"idx": idx},
                }
            )
            for idx in range(4)
        ),
        encoding="utf-8",
    )
    mod.backfill_threshold_cycle_events(
        "2026-04-30", overwrite=True, max_input_lines_per_chunk=2
    )

    raw_path.write_text(
        json.dumps(
            {
                "event_type": "pipeline_event",
                "stage": "budget_pass",
                "fields": {"idx": 0},
            }
        ),
        encoding="utf-8",
    )

    summary = mod.backfill_threshold_cycle_events("2026-04-30")
    assert summary["status"] == "stopped_source_changed"


def test_backfill_threshold_cycle_events_stops_on_source_mtime_mismatch(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(
        mod,
        "_sample_metrics",
        lambda: {
            "cpu": {"iowait_pct": 0.0},
            "io": {"disk_read_mb_delta": 0.0},
            "memory": {"mem_available_mb": 2048.0},
        },
    )
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "pipeline_events_2026-04-30.jsonl"
    raw_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "event_type": "pipeline_event",
                    "stage": "budget_pass",
                    "fields": {"idx": idx},
                }
            )
            for idx in range(4)
        ),
        encoding="utf-8",
    )
    mod.backfill_threshold_cycle_events(
        "2026-04-30", overwrite=True, max_input_lines_per_chunk=2
    )
    stat = raw_path.stat()
    os.utime(raw_path, (stat.st_atime + 10, stat.st_mtime + 10))

    summary = mod.backfill_threshold_cycle_events("2026-04-30")
    assert summary["status"] == "stopped_source_changed"


def test_backfill_threshold_cycle_events_can_read_immutable_source_snapshot(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(
        mod,
        "_sample_metrics",
        lambda: {
            "cpu": {"iowait_pct": 0.0},
            "io": {"disk_read_mb_delta": 0.0},
            "memory": {"mem_available_mb": 2048.0},
        },
    )
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    live_path = raw_dir / "pipeline_events_2026-04-30.jsonl"
    live_path.write_text(
        json.dumps(
            {
                "event_type": "pipeline_event",
                "stage": "budget_pass",
                "fields": {"idx": "live"},
            }
        ),
        encoding="utf-8",
    )
    snapshot_path = tmp_path / "snapshot.jsonl"
    snapshot_path.write_text(
        json.dumps(
            {
                "event_type": "pipeline_event",
                "stage": "sell_completed",
                "fields": {"idx": "snapshot"},
            }
        ),
        encoding="utf-8",
    )

    summary = mod.backfill_threshold_cycle_events(
        "2026-04-30", source_path=snapshot_path, overwrite=True
    )

    assert summary["completed"] is True
    checkpoint = json.loads(
        (tmp_path / "threshold_cycle" / "checkpoints" / "2026-04-30.json").read_text(
            encoding="utf-8"
        )
    )
    assert checkpoint["source_path"] == str(snapshot_path.resolve())
    action_weight_path = (
        tmp_path
        / "threshold_cycle"
        / "date=2026-04-30"
        / "family=statistical_action_weight"
        / "part-000001.jsonl"
    )
    row = json.loads(action_weight_path.read_text(encoding="utf-8").strip())
    assert row["stage"] == "sell_completed"


def test_backfill_threshold_cycle_events_streams_gzip_snapshot_with_smaller_chunk(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(mod, "DEFAULT_MAX_COMPRESSED_INPUT_LINES_PER_CHUNK", 5)
    monkeypatch.setattr(
        mod,
        "_sample_metrics",
        lambda: {
            "cpu": {"iowait_pct": 0.0, "cpu_busy_pct": 0.0},
            "io": {"disk_read_mb_delta": 0.0},
            "memory": {"mem_available_mb": 2048.0},
        },
    )
    snapshot_path = tmp_path / "snapshot.jsonl.gz"
    with gzip.open(snapshot_path, "wt", encoding="utf-8") as handle:
        for idx in range(6):
            handle.write(
                json.dumps(
                    {
                        "event_type": "pipeline_event",
                        "stage": "budget_pass",
                        "fields": {"idx": idx},
                    }
                )
                + "\n"
            )

    first = mod.backfill_threshold_cycle_events(
        "2026-04-30",
        source_path=snapshot_path,
        overwrite=True,
        max_input_lines_per_chunk=10_000,
    )
    second = mod.backfill_threshold_cycle_events(
        "2026-04-30",
        source_path=snapshot_path,
        max_input_lines_per_chunk=10_000,
    )

    assert first["source_compressed"] is True
    assert (
        first["effective_max_input_lines_per_chunk"]
        == mod.DEFAULT_MAX_COMPRESSED_INPUT_LINES_PER_CHUNK
    )
    assert first["status"] == "paused_by_chunk_limit"
    assert first["written"] == mod.DEFAULT_MAX_COMPRESSED_INPUT_LINES_PER_CHUNK
    assert second["completed"] is True
    assert second["written_total"] == 6


def test_backfill_threshold_cycle_events_pauses_on_cpu_busy_guard(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    samples = iter(
        [
            {
                "cpu": {"iowait_pct": 0.0, "cpu_busy_pct": 0.0},
                "io": {"disk_read_mb_delta": 0.0},
                "memory": {"mem_available_mb": 2048.0},
            },
            {
                "cpu": {"iowait_pct": 0.0, "cpu_busy_pct": 96.0},
                "io": {"disk_read_mb_delta": 0.0},
                "memory": {"mem_available_mb": 2048.0},
            },
        ]
    )
    monkeypatch.setattr(mod, "_sample_metrics", lambda: next(samples))
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "pipeline_events_2026-04-30.jsonl").write_text(
        json.dumps(
            {"event_type": "pipeline_event", "stage": "budget_pass", "fields": {}}
        ),
        encoding="utf-8",
    )

    summary = mod.backfill_threshold_cycle_events(
        "2026-04-30", overwrite=True, max_cpu_busy_pct=95.0
    )

    assert summary["status"] == "paused_by_availability_guard"
    assert summary["paused_reason"] == "cpu_busy_pct>=95"


def test_backfill_threshold_cycle_events_pauses_on_system_metric_guard(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    samples = iter(
        [
            {
                "cpu": {"iowait_pct": 0.0},
                "io": {"disk_read_mb_delta": 0.0},
                "memory": {"mem_available_mb": 2048.0},
            },
            {
                "cpu": {"iowait_pct": 21.0},
                "io": {"disk_read_mb_delta": 0.0},
                "memory": {"mem_available_mb": 2048.0},
            },
        ]
    )
    monkeypatch.setattr(mod, "_sample_metrics", lambda: next(samples))
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "pipeline_events_2026-04-30.jsonl").write_text(
        json.dumps(
            {"event_type": "pipeline_event", "stage": "budget_pass", "fields": {}}
        ),
        encoding="utf-8",
    )

    summary = mod.backfill_threshold_cycle_events("2026-04-30", overwrite=True)
    assert summary["status"] == "paused_by_availability_guard"
    assert summary["paused_reason"] == "iowait_pct>=20"


def test_backfill_threshold_cycle_events_completed_checkpoint_skips_metric_guard(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    samples = iter(
        [
            {
                "cpu": {"iowait_pct": 0.0},
                "io": {"disk_read_mb_delta": 0.0},
                "memory": {"mem_available_mb": 2048.0},
            },
            {
                "cpu": {"iowait_pct": 0.0},
                "io": {"disk_read_mb_delta": 256.0},
                "memory": {"mem_available_mb": 2048.0},
            },
        ]
    )
    monkeypatch.setattr(mod, "_sample_metrics", lambda: next(samples))
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "pipeline_events_2026-04-30.jsonl"
    raw_path.write_text(
        json.dumps(
            {"event_type": "pipeline_event", "stage": "budget_pass", "fields": {}}
        ),
        encoding="utf-8",
    )

    first = mod.backfill_threshold_cycle_events("2026-04-30", overwrite=True)
    assert first["status"] == "paused_by_availability_guard"
    assert first["byte_offset"] == first["source_size"]

    summary = mod.backfill_threshold_cycle_events("2026-04-30")
    assert summary["status"] == "completed"
    assert summary["completed"] is True
    assert summary["processed"] == 0
    assert summary["paused_reason"] is None


def test_backfill_threshold_cycle_events_accepts_dynamic_threshold_family(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    monkeypatch.setattr(
        mod,
        "_sample_metrics",
        lambda: {
            "cpu": {"iowait_pct": 0.0},
            "io": {"disk_read_mb_delta": 0.0},
            "memory": {"mem_available_mb": 2048.0},
        },
    )
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "pipeline_events_2026-04-30.jsonl").write_text(
        json.dumps(
            {
                "event_type": "pipeline_event",
                "stage": "future_threshold_stage",
                "fields": {"threshold_family": "future_family"},
            }
        ),
        encoding="utf-8",
    )

    summary = mod.backfill_threshold_cycle_events("2026-04-30", overwrite=True)

    assert summary["written"] == 1
    path = (
        tmp_path
        / "threshold_cycle"
        / "date=2026-04-30"
        / "family=future_family"
        / "part-000001.jsonl"
    )
    row = json.loads(path.read_text(encoding="utf-8").strip())
    assert row["stage"] == "future_threshold_stage"
    assert row["family"] == "future_family"
