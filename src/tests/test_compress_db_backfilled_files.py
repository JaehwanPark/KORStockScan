import json
from datetime import date
from pathlib import Path

import pytest

from src.engine import compress_db_backfilled_files as archive


@pytest.mark.parametrize("fault", [None, "missing", "changed"])
def test_snapshot_archive_resumes_sidecar_after_main_commit(tmp_path, monkeypatch, fault):
    from src.engine.lifecycle.snapshot_archive import generation, read_bytes

    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(archive, "_snapshot_manifest_verifies", lambda *a: True)
    monkeypatch.setattr(archive, "_postclose_source_protection", lambda *a: None)
    main = directory / "trade_review_2026-10-26.json"
    sidecar = main.with_suffix(".completed_projection.json")
    main.write_text('{"source":"original"}')
    sidecar.write_text('{"projection":"unchanged","cost":null}')
    before = generation(sidecar)
    archive._gzip_file(main, dry_run=False)
    if fault == "missing":
        Path(str(main) + ".gz.archive_receipt.json").unlink()
    elif fault == "changed":
        Path(str(main) + ".gz").write_bytes(b"changed")
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", tmp_path / "absent-pipeline")
    result = archive.run(retention_days=1, today=date(2026, 10, 28), dry_run=False)
    assert sidecar.exists() is (fault is not None)
    if fault is None:
        assert result["snapshots"]["compressed"] == 1
        assert generation(sidecar) == before
        assert json.loads(read_bytes(sidecar, maximum=1024))["cost"] is None
        again = archive.run(retention_days=1, today=date(2026, 10, 28), dry_run=False,
                            snapshots_only=True)
        assert again["snapshots"]["compressed"] == 0
    else:
        assert result["errors"]


def test_snapshot_only_cycle_keeps_policy_day_and_other_sources(tmp_path, monkeypatch):
    snapshots = tmp_path / "monitor_snapshots"
    snapshots.mkdir()
    raw = snapshots / "trade_review_2026-10-26.json"
    raw.write_text('{"source":"protected"}')
    pipeline = tmp_path / "pipeline"
    pipeline.mkdir()
    (pipeline / "pipeline_events_2026-10-01.jsonl").write_text('{}\n')
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshots)
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline)
    monkeypatch.setattr(archive, "_postclose_source_protection",
                        lambda *a: "postclose_policy_day_not_elapsed:2026-10-27")
    result = archive.run(retention_days=1, today=date(2026, 10, 27), dry_run=False,
                         snapshot_dates={date(2026, 10, 26)})
    assert result["snapshot_retained_bytes"] == raw.stat().st_size
    assert result["skipped_postclose_protected"] == 1
    assert all(result[k]["scanned"] == 0 for k in
               ("pipeline", "threshold_snapshots", "canonical_context", "pipeline_summaries"))


def test_snapshot_custody_change_at_receipt_keeps_plain_source(tmp_path, monkeypatch):
    import hashlib

    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", tmp_path)
    source = tmp_path / "trade_review_2026-10-26.json"
    source.write_text('{"evidence":"original"}')
    custody = tmp_path / "controller.json"
    custody.write_text('{"generation":"original"}')
    refs = [dict(path=str(custody), sha256=hashlib.sha256(custody.read_bytes()).hexdigest())]
    write = archive.write_json_object_generation_safe
    def changed(*args, **kwargs):
        result = write(*args, **kwargs)
        custody.write_text('{"generation":"successor"}')
        return result
    monkeypatch.setattr(archive, "write_json_object_generation_safe", changed)
    with pytest.raises(ValueError, match="storage_custody_changed_before_removal"):
        archive._gzip_file(source, dry_run=False, custody=refs)
    assert source.read_text() == '{"evidence":"original"}'


def test_snapshot_daily_age_uses_kst_calendar_even_on_utc_host(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    import sys

    class Clock:
        @staticmethod
        def now(zone):
            assert str(zone) == "Asia/Seoul"
            return datetime(2026, 10, 27, 21, 25, tzinfo=timezone.utc).astimezone(zone)
    monkeypatch.setattr(archive, "datetime", Clock)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", tmp_path / "absent-snapshots")
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", tmp_path / "absent-pipeline")
    monkeypatch.setattr(sys, "argv", ["archive", "--snapshots-only", "--dry-run"])
    original = archive.run
    def run(**kwargs):
        assert kwargs["today"] == date(2026, 10, 28)
        assert kwargs["snapshots_only"] is True
        # Empty isolated roots are supplied by the normal fixture.
        return original(**kwargs)
    monkeypatch.setattr(archive, "run", run)
    assert archive.main() == 0


@pytest.fixture(autouse=True)
def _isolate_new_archive_roots(tmp_path, monkeypatch):
    canonical_dir = tmp_path / "optional" / "canonical"
    summary_dir = tmp_path / "optional" / "summaries"
    threshold_dir = tmp_path / "optional" / "threshold_cycle"
    snapshot_dir = threshold_dir / "snapshots"
    for path in (canonical_dir, summary_dir, snapshot_dir):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        archive, "POSTCLOSE_STATUS_DIR", tmp_path / "optional" / "postclose_status"
    )
    monkeypatch.setattr(
        archive,
        "POSTCLOSE_CONTROLLER_DIR",
        tmp_path / "optional" / "postclose_controller",
    )
    monkeypatch.setattr(archive, "CANONICAL_CONTEXT_DIR", canonical_dir)
    monkeypatch.setattr(archive, "PIPELINE_SUMMARY_DIR", summary_dir)
    monkeypatch.setattr(archive, "THRESHOLD_CYCLE_DIR", threshold_dir)
    monkeypatch.setattr(archive, "THRESHOLD_SNAPSHOT_DIR", snapshot_dir)


def test_snapshot_manifest_verifies_existing_snapshot(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    target_date = date(2026, 4, 22)

    snapshot_path = snapshot_dir / "trade_review_2026-04-22.json"
    snapshot_path.write_text("{}", encoding="utf-8")
    manifest_path = manifest_dir / "monitor_snapshot_manifest_2026-04-22_full.json"
    manifest_path.write_text(
        json.dumps(
            {
                "target_date": "2026-04-22",
                "profile": "full",
                "snapshot_paths": {"trade_review": str(snapshot_path)},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

    assert archive._snapshot_manifest_verifies("trade_review", target_date) is True


def test_run_uses_snapshot_manifest_without_db_fallback(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = snapshot_dir / "trade_review_2026-04-22.json"
    snapshot_path.write_text("{}", encoding="utf-8")
    (manifest_dir / "monitor_snapshot_manifest_2026-04-22_full.json").write_text(
        json.dumps(
            {
                "target_date": "2026-04-22",
                "profile": "full",
                "snapshot_paths": {"trade_review": str(snapshot_path)},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=True)

    assert stats["snapshots"]["scanned"] == 1
    assert stats["snapshots"]["verified"] == 1
    assert stats["snapshots"]["compressed"] == 1
    assert stats["skipped_unverified"] == 0


@pytest.mark.parametrize("dry_run", [False, True])
def test_archive_preserves_native_holding_policy_source_handoff(
    tmp_path, monkeypatch, dry_run
):
    import hashlib
    from src.engine.scalping import holding_path_vote_policy as policy
    from src.engine.scalping.holding_path_vote_replay import (
        summarize_holding_path_votes,
    )
    from src.engine.automation import postclose_summary_handoff as summary

    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    pipeline = tmp_path / "pipeline"
    pipeline.mkdir()
    source_date = "2026-10-08"
    target_date = "2026-10-12"
    replay = summarize_holding_path_votes(
        [], load_events=lambda _: [], model="gpt-5.4-nano"
    )
    observation = dict(
        date=source_date,
        holding_path_vote_replay=replay,
        completed_population_quality=dict(
            complete=False,
            db_completed_main_ids=[],
            strict_completed_position_ids=[],
            source_gap_ids=[],
            excluded_all_reasons={},
            source_gap_dates=[],
        ),
    )
    path = directory / f"holding_exit_observation_{source_date}.json"
    original = json.dumps(observation).encode()
    path.write_bytes(original)
    bundle = policy.create_bundle(
        source_date=source_date,
        target_date=target_date,
        source_report_sha256=hashlib.sha256(original).hexdigest(),
        replay=replay,
        source_quality=policy.source_quality_from_observation(observation),
    )
    summary_path = (
        tmp_path
        / "report/runtime_approval_summary"
        / f"runtime_approval_summary_{source_date}.json"
    )
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(
        json.dumps(
            dict(
                holding_path_vote_policy=dict(
                    status=policy.publication_status(bundle),
                    source_date=source_date,
                    target_date=target_date,
                    bundle_sha256=bundle["bundle_sha256"],
                    policy_set_sha256=bundle["policy_set_sha256"],
                    source_report_sha256=bundle["source_report_sha256"],
                    cell_count=len(bundle["cells"]),
                )
            )
        )
    )
    monkeypatch.setattr(summary, "stage_receipt_issues", lambda *a, **kw: [])
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline)
    monkeypatch.setattr(archive, "_postclose_source_protection", lambda *a: None)
    monkeypatch.setattr(archive, "_snapshot_manifest_verifies", lambda *a: True)
    policy.verify_source_handoff(tmp_path, bundle)
    stats = archive.run(retention_days=1, today=date(2026, 10, 16), dry_run=dry_run)
    policy.verify_source_handoff(tmp_path, bundle)
    from src.engine.lifecycle.snapshot_archive import read_bytes

    assert read_bytes(path, maximum=1024 * 1024) == original
    assert path.exists() is dry_run
    assert path.with_suffix(".json.gz").exists() is not dry_run
    assert stats["retained_holding_policy_source_count"] == 0
    assert stats["snapshots"]["compressed"] == 1


def test_archive_preserves_frozen_trade_window_identity(tmp_path, monkeypatch):
    from src.engine import log_archive_service as snapshots
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle.holding_window_generation import (
        capture_window,
        verify_window,
    )

    directory = tmp_path / "report/monitor_snapshots"
    directory.mkdir(parents=True)
    pipeline = tmp_path / "pipeline"
    pipeline.mkdir()
    monkeypatch.setattr(snapshots, "MONITOR_SNAPSHOT_DIR", directory)
    day = "2026-10-08"
    payload = dict(
        date=day,
        metrics={"canonical_completed_trades": 0},
        meta={"snapshot_profile": "postclose_exit", "sell_completed_event_ids": []},
        sections={
            "completed_trade_projection": [],
            "open_scalp_position_projection": [],
        },
    )
    payload["meta"]["completed_census_manifest"] = completed_census_manifest(payload)
    path = snapshots.save_monitor_snapshot("trade_review", day, payload)
    window = capture_window(tmp_path, [day])
    assert window["dependencies"][day]["status"] == "valid_empty"
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", directory)
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline)
    monkeypatch.setattr(archive, "_postclose_source_protection", lambda *a: None)
    monkeypatch.setattr(archive, "_snapshot_manifest_verifies", lambda *a: True)
    stats = archive.run(retention_days=1, today=date(2026, 10, 16), dry_run=False)
    verify_window(tmp_path, window)
    from src.engine.holding_exit_observation_report import (
        _verified_trade_review_projection,
    )

    assert (
        _verified_trade_review_projection(
            path.with_suffix(".json.gz"), day, data_root=tmp_path
        )
        is not None
    )
    assert not path.exists() and path.with_suffix(".json.gz").exists()
    assert not path.with_suffix(".completed_projection.json").exists()
    assert stats["retained_trade_window_source_count"] == 0
    assert stats["snapshots"]["compressed"] == 2


def test_run_does_not_compress_manifested_corrupt_snapshot(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True)
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True)
    snapshot_path = snapshot_dir / "missed_entry_counterfactual_2026-04-22.json"
    snapshot_path.write_text('{"full_rows":[', encoding="utf-8")
    (manifest_dir / "monitor_snapshot_manifest_2026-04-22_full.json").write_text(
        json.dumps(
            {
                "target_date": "2026-04-22",
                "profile": "full",
                "snapshot_paths": {"missed_entry_counterfactual": str(snapshot_path)},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=False)

    assert stats["snapshots"]["compressed"] == 0
    assert stats["skipped_unverified"] == 1
    assert snapshot_path.exists()
    assert not snapshot_path.with_suffix(".json.gz").exists()
    assert stats["errors"] == [
        "snapshot:missed_entry_counterfactual_2026-04-22.json:"
        "invalid_json_boundary_not_compressed"
    ]


def test_run_compresses_pipeline_events_only_after_parquet_verification(
    tmp_path, monkeypatch
):
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    monitor_snapshot_dir = tmp_path / "monitor_snapshots"
    monitor_snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = monitor_snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    parquet_partition = (
        tmp_path / "analytics" / "parquet" / "pipeline_events" / "date=2026-04-22"
    )
    parquet_partition.mkdir(parents=True, exist_ok=True)
    (parquet_partition / "part-000001.parquet").write_bytes(b"parquet-placeholder")
    raw_path = pipeline_dir / "pipeline_events_2026-04-22.jsonl"
    raw_path.write_text('{"stage":"sample"}\n', encoding="utf-8")

    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", monitor_snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(
        archive, "ANALYTICS_PARQUET_DIR", tmp_path / "analytics" / "parquet"
    )

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=True)

    assert stats["pipeline"]["scanned"] == 1
    assert stats["pipeline"]["verified"] == 1
    assert stats["pipeline"]["compressed"] == 1
    assert stats["pipeline"]["saved_bytes"] == raw_path.stat().st_size
    assert raw_path.with_name(f".{raw_path.name}.generation.lock").is_file()


def test_run_skips_pipeline_events_without_parquet_verification(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    monitor_snapshot_dir = tmp_path / "monitor_snapshots"
    monitor_snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = monitor_snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (pipeline_dir / "pipeline_events_2026-04-22.jsonl").write_text(
        '{"stage":"sample"}\n', encoding="utf-8"
    )

    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", monitor_snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(
        archive, "ANALYTICS_PARQUET_DIR", tmp_path / "analytics" / "parquet"
    )

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=True)

    assert stats["pipeline"]["scanned"] == 1
    assert stats["pipeline"]["verified"] == 0
    assert stats["pipeline"]["compressed"] == 0
    assert stats["skipped_unverified"] == 1


def test_run_compresses_verified_threshold_snapshots(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    monitor_snapshot_dir = tmp_path / "monitor_snapshots"
    monitor_snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = monitor_snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    threshold_dir = tmp_path / "threshold_cycle"
    threshold_snapshot_dir = threshold_dir / "snapshots"
    threshold_snapshot_dir.mkdir(parents=True, exist_ok=True)
    backfill_dir = (
        threshold_dir / "date=2026-04-22" / "family=score65_74_recovery_probe"
    )
    backfill_dir.mkdir(parents=True, exist_ok=True)

    snapshot = (
        threshold_snapshot_dir / "pipeline_events_2026-04-22_20260422_161001.jsonl"
    )
    snapshot.write_text('{"stage":"sample"}\n', encoding="utf-8")
    (backfill_dir / "part-000001.jsonl").write_text(
        '{"stage":"sample"}\n', encoding="utf-8"
    )

    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", monitor_snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(archive, "THRESHOLD_CYCLE_DIR", threshold_dir)
    monkeypatch.setattr(archive, "THRESHOLD_SNAPSHOT_DIR", threshold_snapshot_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=True)

    assert stats["threshold_snapshots"]["scanned"] == 1
    assert stats["threshold_snapshots"]["verified"] == 1
    assert stats["threshold_snapshots"]["compressed"] == 1
    assert stats["threshold_snapshots"]["saved_bytes"] == snapshot.stat().st_size


def test_run_compresses_canonical_context_and_streaming_consumer_reads_gzip(
    tmp_path, monkeypatch
):
    from src.engine.scalping import entry_context_intraday_probe as consumer

    canonical_dir = tmp_path / "canonical"
    canonical_dir.mkdir()
    raw_path = canonical_dir / "ai_canonical_context_candidates_2026-04-22.jsonl"
    row = {
        "schema": "ai_canonical_context_candidate_v1",
        "candidate_id": "candidate-1",
    }
    raw_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        archive, "POSTCLOSE_STATUS_DIR", tmp_path / "optional" / "postclose_status"
    )
    monkeypatch.setattr(
        archive,
        "POSTCLOSE_CONTROLLER_DIR",
        tmp_path / "optional" / "postclose_controller",
    )
    monkeypatch.setattr(archive, "CANONICAL_CONTEXT_DIR", canonical_dir)
    monkeypatch.setattr(consumer, "CONTEXT_CANDIDATE_DIR", canonical_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=False)

    gzip_path = raw_path.with_suffix(".jsonl.gz")
    assert not raw_path.exists()
    assert gzip_path.exists()
    assert stats["canonical_context"]["rows"] == 1
    assert list(consumer._load_context_candidates("2026-04-22")) == [row]


def test_run_compresses_manifested_producer_summary_and_consumer_reads_gzip(
    tmp_path, monkeypatch
):
    from src.engine import pipeline_event_summary as consumer

    summary_dir = tmp_path / "summaries"
    summary_dir.mkdir()
    raw_path = summary_dir / "pipeline_event_producer_summary_2026-04-22.jsonl"
    row = {"producer": "entry", "event_count": 3}
    raw_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    manifest_path = (
        summary_dir / "pipeline_event_producer_summary_manifest_2026-04-22.json"
    )
    manifest_path.write_text(
        json.dumps(
            {
                "summary_path": str(raw_path),
                "summary_row_count": 1,
                "runtime_effect": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(archive, "PIPELINE_SUMMARY_DIR", summary_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=False)

    assert stats["pipeline_summaries"]["rows"] == 1
    assert consumer._load_summary_rows(raw_path) == [row]


def test_run_keeps_incomplete_threshold_partition_plain(tmp_path, monkeypatch):
    threshold_dir = tmp_path / "threshold_cycle"
    family_dir = threshold_dir / "date=2026-04-22" / "family=sample"
    family_dir.mkdir(parents=True)
    raw_path = family_dir / "part-000001.jsonl"
    raw_path.write_text('{"family":"sample"}\n', encoding="utf-8")
    monkeypatch.setattr(archive, "THRESHOLD_CYCLE_DIR", threshold_dir)
    monkeypatch.setattr(archive, "THRESHOLD_SNAPSHOT_DIR", threshold_dir / "snapshots")

    stats = archive.run(retention_days=1, today=date(2026, 5, 23), dry_run=False)

    assert stats["threshold_partitions"]["compressed"] == 0
    assert stats["skipped_unverified"] == 1
    assert raw_path.exists()
    assert not raw_path.with_suffix(".jsonl.gz").exists()


def test_threshold_partition_expected_rows_uses_full_prior_part_and_tail_count():
    checkpoint = {"partitions": {"sample": {"part": 2, "line_count": 17}}}
    family_dir = archive.THRESHOLD_CYCLE_DIR / "family=sample"

    assert (
        archive._threshold_partition_expected_rows(
            checkpoint, family_dir / "part-000001.jsonl"
        )
        == archive.THRESHOLD_PARTITION_MAX_ROWS
    )
    assert (
        archive._threshold_partition_expected_rows(
            checkpoint, family_dir / "part-000002.jsonl"
        )
        == 17
    )


@pytest.mark.parametrize("native_state", ["running", "failed", "succeeded"])
def test_archive_preserves_postclose_inputs_through_next_policy_day(
    tmp_path, monkeypatch, native_state
):
    day = date(2026, 10, 2)
    pipeline = tmp_path / "pipeline"
    snapshots = tmp_path / "snapshots"
    pipeline.mkdir()
    snapshots.mkdir()
    raw = pipeline / "pipeline_events_2026-10-02.jsonl"
    snapshot = snapshots / "holding_exit_observation_2026-10-02.json"
    raw.write_text("{}\n")
    snapshot.write_text("{}")
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    (
        archive.POSTCLOSE_STATUS_DIR
        / "threshold_cycle_postclose_2026-10-02.status.json"
    ).write_text(
        json.dumps(
            {"target_date": day.isoformat(), "status": native_state, "exit_code": 0}
        )
    )
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshots)
    monkeypatch.setattr(
        archive,
        "_parquet_partition_exists",
        lambda *a: pytest.fail("protected source cannot reach ingestion/archive"),
    )
    for when in (day, date(2026, 10, 6)):
        result = archive.run(retention_days=0, today=when, dry_run=False)
        assert result["skipped_postclose_protected"] == 2
        assert (
            result["pipeline"]["compressed"] == result["snapshots"]["compressed"] == 0
        )
        assert raw.read_text() == "{}\n" and snapshot.read_text() == "{}"


def test_archive_requires_whole_controller_after_policy_day(monkeypatch):
    from src.engine.automation import postclose_done_controller as controller

    monkeypatch.setattr(controller, "done_terminal_receipt_issues", lambda *a, **kw: [])
    day = date(2026, 10, 2)
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    archive.POSTCLOSE_CONTROLLER_DIR.mkdir(parents=True)
    (
        archive.POSTCLOSE_STATUS_DIR
        / "threshold_cycle_postclose_2026-10-02.status.json"
    ).write_text(
        json.dumps(
            {"target_date": day.isoformat(), "status": "succeeded", "exit_code": 0}
        )
    )
    path = (
        archive.POSTCLOSE_CONTROLLER_DIR / "postclose_done_controller_2026-10-02.json"
    )
    for state, whole in [("summary_verified", False), ("done", False), ("done", True)]:
        path.write_text(
            json.dumps(
                {
                    "date": day.isoformat(),
                    "status": state,
                    "whole_native_chain_done_claimed": whole,
                }
            )
        )
        reason = archive._postclose_source_protection(day, date(2026, 10, 7))
        assert (reason is None) is (state == "done" and whole)


@pytest.mark.parametrize(
    "payload",
    ["{", "[]", '{"target_date": "2026-09-30", "status": "succeeded", "exit_code": 0}'],
)
def test_archive_invalid_native_custody_receipt_fails_closed(payload):
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    (
        archive.POSTCLOSE_STATUS_DIR
        / "threshold_cycle_postclose_2026-10-02.status.json"
    ).write_text(payload)
    assert (
        archive._postclose_source_protection(date(2026, 10, 2), date(2026, 10, 7))
        is not None
    )


def test_archive_rejects_unverified_controller_done_claim(monkeypatch):
    from src.engine.automation import postclose_done_controller as controller

    monkeypatch.setattr(
        controller,
        "done_terminal_receipt_issues",
        lambda *a, **kw: ["controller_verification_attempt_missing_or_invalid"],
    )
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    archive.POSTCLOSE_CONTROLLER_DIR.mkdir(parents=True)
    (
        archive.POSTCLOSE_STATUS_DIR
        / "threshold_cycle_postclose_2026-10-02.status.json"
    ).write_text(
        json.dumps({"target_date": "2026-10-02", "status": "succeeded", "exit_code": 0})
    )
    (
        archive.POSTCLOSE_CONTROLLER_DIR / "postclose_done_controller_2026-10-02.json"
    ).write_text(
        json.dumps(
            {
                "date": "2026-10-02",
                "status": "done",
                "whole_native_chain_done_claimed": True,
            }
        )
    )
    assert (
        archive._postclose_source_protection(date(2026, 10, 2), date(2026, 10, 7))
        == "postclose_controller_receipt_invalid"
    )


def test_archive_broken_native_status_symlink_fails_closed(tmp_path):
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    (
        archive.POSTCLOSE_STATUS_DIR
        / "threshold_cycle_postclose_2026-10-02.status.json"
    ).symlink_to(tmp_path / "missing_status")
    assert (
        archive._postclose_source_protection(date(2026, 10, 2), date(2026, 10, 7))
        == "postclose_status_untrusted"
    )


@pytest.mark.parametrize(
    "defect",
    [None, "snapshot_changed", "strict_changed", "other_failure", "policy_day"],
)
def test_historical_storage_uses_original_receipt_and_checklist_without_resealing(
    tmp_path, monkeypatch, defect
):
    import hashlib
    from src.engine.automation import postclose_done_controller as controller

    monkeypatch.setattr(archive, "DATA_DIR", tmp_path)
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    archive.POSTCLOSE_CONTROLLER_DIR.mkdir(parents=True)
    (
        archive.POSTCLOSE_STATUS_DIR
        / "threshold_cycle_postclose_2026-10-02.status.json"
    ).write_text(
        json.dumps(dict(target_date="2026-10-02", status="succeeded", exit_code=0))
    )
    raw = b"original checklist\r\n"
    sha = hashlib.sha256(raw).hexdigest()
    snap = tmp_path / "runtime/policy_bootstrap/historical_checklists" / f"{sha}.md"
    snap.parent.mkdir(parents=True)
    snap.write_bytes(raw)
    strict = tmp_path / "strict.json"
    strict.write_text(json.dumps(dict(generation_binding=dict(checklist_sha256=sha))))
    path = (
        archive.POSTCLOSE_CONTROLLER_DIR / "postclose_done_controller_2026-10-02.json"
    )
    path.write_text(
        json.dumps(
            dict(
                date="2026-10-02",
                status="done",
                whole_native_chain_done_claimed=True,
                verification_attempt_path=str(strict),
                verification_attempt_sha256=hashlib.sha256(
                    strict.read_bytes()
                ).hexdigest(),
            )
        )
    )
    original = {p: p.read_bytes() for p in (path, strict, snap)}
    calls = []

    def verify(*a, **kw):
        calls.append(kw)
        if defect == "other_failure":
            return ["strict_stage_set_stale"]
        return (
            []
            if kw.get("checklist_snapshot") == snap
            else ["strict_checklist_generation_stale"]
        )

    monkeypatch.setattr(controller, "done_terminal_receipt_issues", verify)
    if defect == "snapshot_changed":
        snap.write_text("changed")
    if defect == "strict_changed":
        strict.write_text("{}")
    reason = archive._postclose_source_protection(
        date(2026, 10, 2), date(2026, 10, 6 if defect == "policy_day" else 7)
    )
    assert (reason is None) == (defect is None)
    if defect is None:
        assert len(calls) == 2 and all(kw["generation_only"] for kw in calls)
        assert all(p.read_bytes() == raw for p, raw in original.items())


def test_pipeline_custody_change_preserves_plain_original(tmp_path):
    import hashlib

    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    original = b'{"source":"original"}\r\n' * 100
    path.write_bytes(original)
    receipt = tmp_path / "strict.json"
    receipt.write_text("changed")
    with pytest.raises(ValueError, match="storage_custody_changed"):
        archive._gzip_file(
            path,
            dry_run=False,
            custody=[
                dict(path=str(receipt), sha256=hashlib.sha256(b"original").hexdigest())
            ],
        )
    assert path.read_bytes() == original
    assert not path.with_suffix(".jsonl.gz").exists()


def test_pipeline_archive_seal_binds_full_crc_proof_to_exact_ctime_generation(tmp_path):
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256

    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    original = b'{"source":"original"}\r\n' * 100
    path.write_bytes(original)
    assert archive._gzip_file(path, dry_run=False)[0] is True
    compressed = Path(str(path) + ".gz")
    receipt = json.loads(Path(str(compressed) + ".archive_receipt.json").read_bytes())
    assert receipt["verification_contract"] == "logical_sha256_size_crc_to_eof_v1"
    assert receipt["archive_generation"]["ctime_ns"] == compressed.stat().st_ctime_ns
    assert receipt["artifact_content_sha256"] == content_sha256(
        {k: v for k, v in receipt.items() if k != "artifact_content_sha256"}
    )
    assert receipt["logical_size_bytes"] == len(original)


def test_pipeline_archive_crc_failure_preserves_original_and_does_not_publish_proof(
    tmp_path, monkeypatch
):
    import gzip
    import os

    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    original = b'{"source":"original"}\n' * 100
    path.write_bytes(original)
    native = os.replace

    def corrupt_after_rename(src, dst, *args, **kwargs):
        value = native(src, dst, *args, **kwargs)
        if Path(dst) == Path(str(path) + ".gz"):
            target = Path(dst)
            stamp = target.stat().st_mtime_ns
            data = bytearray(target.read_bytes())
            data[-8] ^= 1
            target.write_bytes(data)
            os.utime(target, ns=(stamp, stamp))
        return value

    monkeypatch.setattr(os, "replace", corrupt_after_rename)
    with pytest.raises(gzip.BadGzipFile):
        archive._gzip_file(path, dry_run=False)
    assert path.read_bytes() == original
    assert not Path(str(path) + ".gz.archive_receipt.json").exists()
    assert not Path(str(path) + ".gz").exists()
    failed = list(tmp_path.glob("*.gz.failed.*"))
    assert len(failed) == 1
    monkeypatch.setattr(os, "replace", native)
    assert archive._gzip_file(path, dry_run=False)[0] is True
    assert not path.exists() and failed[0].exists()


def test_pipeline_archive_mutation_during_receipt_write_preserves_plain(
    tmp_path, monkeypatch
):
    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    original = b'{"source":"original"}\n' * 100
    path.write_bytes(original)
    native = archive.write_json_object_generation_safe

    def changed(destination, payload, **kwargs):
        native(destination, payload, **kwargs)
        with Path(str(path) + ".gz").open("ab") as stream:
            stream.write(b"changed")

    monkeypatch.setattr(archive, "write_json_object_generation_safe", changed)
    with pytest.raises(ValueError, match="archive_generation_changed_before_removal"):
        archive._gzip_file(path, dry_run=False)
    assert path.read_bytes() == original
    assert not Path(str(path) + ".gz").exists()
    assert not Path(str(path) + ".gz.archive_receipt.json").exists()
    assert len(list(tmp_path.glob("*.gz.failed.*"))) == 1
    assert len(list(tmp_path.glob("*.archive_receipt.json.failed.*"))) == 1
    monkeypatch.setattr(archive, "write_json_object_generation_safe", native)
    assert archive._gzip_file(path, dry_run=False)[0] is True


@pytest.mark.parametrize("write_completed", [False, True])
def test_pipeline_archive_receipt_failure_preserves_failed_attempt_and_retry_succeeds(
    tmp_path, monkeypatch, write_completed
):
    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    original = b'{"source":"original"}\n' * 100
    path.write_bytes(original)
    native = archive.write_json_object_generation_safe

    def failed(destination, payload, **kwargs):
        if write_completed:
            native(destination, payload, **kwargs)
        raise OSError("receipt publication failed")

    monkeypatch.setattr(archive, "write_json_object_generation_safe", failed)
    with pytest.raises(OSError, match="receipt publication failed"):
        archive._gzip_file(path, dry_run=False)
    assert path.read_bytes() == original and not Path(str(path) + ".gz").exists()
    assert not Path(str(path) + ".gz.archive_receipt.json").exists()
    assert len(list(tmp_path.glob("*.gz.failed.*"))) == 1
    assert len(list(tmp_path.glob("*.archive_receipt.json.failed.*"))) == int(
        write_completed
    )
    monkeypatch.setattr(archive, "write_json_object_generation_safe", native)
    assert archive._gzip_file(path, dry_run=False)[0] is True


def test_pipeline_archive_failure_does_not_move_foreign_replacement_inode(
    tmp_path, monkeypatch
):
    import os

    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    original = b'{"source":"original"}\n' * 100
    path.write_bytes(original)
    archived = Path(str(path) + ".gz")
    foreign = tmp_path / "foreign"
    foreign.write_bytes(b"foreign archive bytes")
    native = archive.write_json_object_generation_safe

    def replaced(destination, payload, **kwargs):
        native(destination, payload, **kwargs)
        os.replace(foreign, archived)
        raise OSError("foreign replacement occurred")

    monkeypatch.setattr(archive, "write_json_object_generation_safe", replaced)
    with pytest.raises(OSError, match="foreign replacement occurred"):
        archive._gzip_file(path, dry_run=False)
    assert archived.read_bytes() == b"foreign archive bytes"
    assert not list(tmp_path.glob("*.gz.failed.*"))
    assert path.read_bytes() == original


def test_pipeline_archive_does_not_adopt_foreign_inode_immediately_after_rename(
    tmp_path, monkeypatch
):
    import os

    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    original = b'{"source":"original"}\n' * 100
    path.write_bytes(original)
    archived = Path(str(path) + ".gz")
    foreign = tmp_path / "foreign"
    foreign.write_bytes(b"foreign archive bytes")
    native = os.replace

    def replaced(src, dst, *args, **kwargs):
        result = native(src, dst, *args, **kwargs)
        if Path(dst) == archived:
            native(foreign, archived)
        return result

    monkeypatch.setattr(os, "replace", replaced)
    with pytest.raises(ValueError, match="foreign_generation_after_rename"):
        archive._gzip_file(path, dry_run=False)
    assert archived.read_bytes() == b"foreign archive bytes"
    assert not list(tmp_path.glob("*.gz.failed.*"))
    assert not Path(str(archived) + ".archive_receipt.json").exists()
    assert path.read_bytes() == original


def test_archive_preserves_orphan_original_receipt_instead_of_rewriting(tmp_path):
    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    original = b'{"source":"original"}\n'
    path.write_bytes(original)
    receipt = Path(str(path) + ".gz.archive_receipt.json")
    receipt.write_bytes(b'{"original_failed_evidence":true}\n')
    before = receipt.read_bytes()
    with pytest.raises(ValueError, match="orphan_receipt_preserved"):
        archive._gzip_file(path, dry_run=False)
    assert path.read_bytes() == original and receipt.read_bytes() == before
    assert not Path(str(path) + ".gz").exists()


def test_archive_commit_has_no_late_stat_failure_after_plain_removal(
    tmp_path, monkeypatch
):
    path = tmp_path / "pipeline_events_2026-10-08.jsonl"
    path.write_bytes(b'{"source":"original"}\n' * 100)
    compressed = Path(str(path) + ".gz")
    native = Path.stat

    def guarded(file, *args, **kwargs):
        if file == compressed and not path.exists():
            pytest.fail("archive stat after original removal")
        return native(file, *args, **kwargs)

    with monkeypatch.context() as finalization:
        finalization.setattr(Path, "stat", guarded)
        assert archive._gzip_file(path, dry_run=False)[0] is True
    assert compressed.exists() and not path.exists()


def test_pipeline_date_scope_preserves_other_families(tmp_path, monkeypatch):
    pipeline = tmp_path / "pipeline"
    pipeline.mkdir()
    snapshots = tmp_path / "snapshots"
    snapshots.mkdir()
    selected = pipeline / "pipeline_events_2026-10-08.jsonl"
    other = pipeline / "pipeline_events_2026-10-12.jsonl"
    today = pipeline / "pipeline_events_2026-10-16.jsonl"
    for p in (selected, other, today):
        p.write_text('{"source":"original"}\n' * 100)
    snapshot = snapshots / "trade_review_2026-10-08.json"
    snapshot.write_text("{}")
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshots)
    monkeypatch.setattr(archive, "_parquet_partition_exists", lambda *args: True)
    stats = archive.run(
        retention_days=0,
        today=date(2026, 10, 16),
        dry_run=False,
        pipeline_dates={date(2026, 10, 8), date(2026, 10, 16)},
    )
    assert stats["pipeline"]["compressed"] == 1 and not stats["errors"]
    assert (
        not selected.exists()
        and other.exists()
        and today.exists()
        and snapshot.exists()
    )
    assert (
        stats["postclose_protection_reasons"]["2026-10-16"]
        == "current_or_future_source_date"
    )
    receipt = json.loads(
        selected.with_suffix(".jsonl.gz.archive_receipt.json").read_bytes()
    )
    assert receipt["logical_size_bytes"] == other.stat().st_size
    assert (
        stats["pipeline"]["saved_bytes"]
        == other.stat().st_size - selected.with_suffix(".jsonl.gz").stat().st_size
    )
