import json
import pytest

from src.engine import buy_funnel_sentinel as buy
from src.engine import holding_exit_sentinel as holding
from src.engine.sentinel_event_cache import update_and_load_cached_event_rows

TARGET_DATE = "2026-05-06"


@pytest.mark.parametrize("actor", ["base_writer", "late_writer", "rotation"])
def test_archive_raw_lease_serializes_actual_native_actors(tmp_path, actor):
    import threading

    from src.engine import sentinel_event_cache as owner
    from src.engine.compress_db_backfilled_files import _gzip_file_with_jsonl_generation_lock
    from src.utils.pipeline_event_logger import _append_pipeline_event_jsonl

    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event("10:00:00", "ai_confirmed")])
    original = raw.read_bytes()
    line = json.dumps(_event("10:01:00", "order_leg_sent")) + "\n"
    entered = threading.Event()
    finished = threading.Event()
    errors = []

    def run():
        entered.set()
        try:
            if actor == "rotation":
                _gzip_file_with_jsonl_generation_lock(raw, dry_run=False)
            else:
                _append_pipeline_event_jsonl(raw, line, late_partition=actor == "late_writer")
        except BaseException as exc:
            errors.append(exc)
        finally:
            finished.set()

    with owner._raw_producer_rotation_lease(raw):
        worker = threading.Thread(target=run, daemon=True)
        worker.start()
        try:
            assert entered.wait(3)
            assert not finished.wait(0.2)
            assert raw.read_bytes() == original
        finally:
            # Release is performed by the outer context even if an assertion fails.
            pass
    worker.join(10)
    assert not worker.is_alive()
    assert finished.is_set()
    assert not errors
    if actor == "rotation":
        assert not raw.exists()
        assert raw.with_name(raw.name + ".gz").exists()
    elif actor == "base_writer":
        assert raw.read_bytes() == original + line.encode()
    else:
        from src.utils.pipeline_event_logger import _late_pipeline_event_path

        assert raw.read_bytes() == original
        assert _late_pipeline_event_path(raw).read_text() == line
        with pytest.raises(ValueError, match="sentinel_archive_late_source_unverified"):
            with owner._raw_producer_rotation_lease(raw):
                pass


def test_native_writer_does_not_share_rotation_generation_lock(tmp_path):
    import threading

    from src.utils.jsonl_io import jsonl_artifact_generation_lock
    from src.utils.pipeline_event_logger import _append_pipeline_event_jsonl

    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event("10:00:00", "ai_confirmed")])
    line = json.dumps(_event("10:01:00", "order_leg_sent")) + "\n"
    done = threading.Event()
    errors = []

    def append():
        try:
            _append_pipeline_event_jsonl(raw, line, late_partition=False)
        except BaseException as exc:
            errors.append(exc)
        finally:
            done.set()

    with jsonl_artifact_generation_lock(raw, exclusive=True):
        worker = threading.Thread(target=append, daemon=True)
        worker.start()
        assert done.wait(5), "native writer unexpectedly shares the rotation lock"
    worker.join(5)
    assert not worker.is_alive() and not errors
    assert raw.read_bytes().endswith(line.encode())


def test_raw_lease_cannot_exclude_uncooperative_direct_append(tmp_path):
    from src.engine import sentinel_event_cache as owner

    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event("10:00:00", "ai_confirmed")])
    with owner._raw_producer_rotation_lease(raw):
        with raw.open("ab") as direct:
            direct.write(b"uncooperative\n")
    assert raw.read_bytes().endswith(b"uncooperative\n")


def test_compact_index_preserves_large_fields_and_only_parses_appends(
    tmp_path, monkeypatch
):
    from pathlib import Path
    from src.engine.monitoring.sentinel_compact_store import CompactFields

    raw = _raw_path(tmp_path)
    text = "original policy evidence 한글 " * 4000
    payload = _event("10:00:00", "ai_confirmed", fields={"large": text, "attempt": "a"})
    _write_lines(raw, [payload, payload])
    calls = []

    def parse(row):
        calls.append(1)
        return row

    args = dict(
        raw_path=raw,
        cache_dir=tmp_path / "cache",
        cache_name="indexed",
        target_date=TARGET_DATE,
        schema_version=1,
        parse_payload=parse,
        compact_index=True,
    )
    first, meta = update_and_load_cached_event_rows(**args)
    assert len(first) == 2 and len(calls) == 2  # Distinct source positions survive.
    assert isinstance(first[0]["fields"], CompactFields)
    assert first[0]["fields"]["large"] == text.strip()
    cache = Path(meta["cache_path"])
    assert (
        cache.with_suffix(".compact.sqlite").stat().st_size < cache.stat().st_size / 2
    )
    real_open = Path.open

    def no_cache_scan(path, mode="r", *a, **kw):
        if path == cache and mode in {"r", "rb"}:
            pytest.fail("unchanged cache body reread")
        return real_open(path, mode, *a, **kw)

    with monkeypatch.context() as m:
        m.setattr(Path, "open", no_cache_scan)
        second, after = update_and_load_cached_event_rows(**args)
    assert len(second) == 2 and len(calls) == 2 and not after["cache_body_rescanned"]
    with raw.open("a") as f:
        f.write(
            json.dumps(_event("10:01:00", "order_leg_sent", fields={"attempt": "a"}))
            + "\n"
        )
    third, after = update_and_load_cached_event_rows(**args)
    assert len(third) == 3 and len(calls) == 3 and not after["cache_body_rescanned"]
    assert third[-1]["stage"] == "order_leg_sent"


def test_compact_index_corruption_fails_then_rebuilds_from_cache(tmp_path):
    import sqlite3
    from pathlib import Path

    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event("10:00:00", "ai_confirmed")])
    args = dict(
        raw_path=raw,
        cache_dir=tmp_path / "cache",
        cache_name="damaged",
        target_date=TARGET_DATE,
        schema_version=1,
        parse_payload=lambda x: x,
        compact_index=True,
    )
    _, meta = update_and_load_cached_event_rows(**args)
    with sqlite3.connect(
        Path(meta["cache_path"]).with_suffix(".compact.sqlite")
    ) as conn:
        conn.execute("UPDATE rows SET body='changed'")
    with pytest.raises(ValueError, match="row_corrupt"):
        update_and_load_cached_event_rows(**args)
    rows, _ = update_and_load_cached_event_rows(**args)
    assert len(rows) == 1 and rows[0]["stage"] == "ai_confirmed"


def test_optional_index_failure_after_append_preserves_native_cursor(
    tmp_path, monkeypatch
):
    from src.engine.monitoring import sentinel_compact_store as store

    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event("10:00:00", "ai_confirmed")])
    args = dict(
        raw_path=raw,
        cache_dir=tmp_path / "cache",
        cache_name="resume",
        target_date=TARGET_DATE,
        schema_version=1,
        parse_payload=lambda x: x,
        compact_index=True,
    )
    update_and_load_cached_event_rows(**args)
    with raw.open("a") as stream:
        stream.write(json.dumps(_event("10:01:00", "budget_pass")) + "\n")

    def fail(*a, **kw):
        raise OSError("index_disk_full")

    with monkeypatch.context() as m:
        m.setattr(store, "indexed_rows", fail)
        with pytest.raises(OSError):
            update_and_load_cached_event_rows(**args)
    rows, meta = update_and_load_cached_event_rows(**args)
    assert len(rows) == 2 and meta["appended_cache_rows"] == 0


@pytest.mark.parametrize("damage", [None, "malformed", "drop", "identity"])
def test_cache_projection_preserves_population_raw_and_failure_evidence(
    tmp_path, damage
):
    raw = _raw_path(tmp_path)
    payload = _event(
        "10:00:00",
        "scalp_entry_action_decision_snapshot",
        fields={
            "source_quality_status": "pass",
            "evaluation_attempt_id": "exact",
            "entry_economic_operating_context": "frozen_code" * 10000,
            "entry_economic_conditional_seed": "frozen_seed" * 10000,
        },
    )
    _write_lines(raw, [payload])
    args = dict(
        raw_path=raw,
        cache_dir=tmp_path / "cache",
        cache_name="projection",
        target_date=TARGET_DATE,
        schema_version=1,
        parse_payload=lambda x: x,
    )
    _, before = update_and_load_cached_event_rows(**args)
    cache = tmp_path / "cache" / ("projection_" + TARGET_DATE + ".jsonl")
    if damage == "malformed":
        with cache.open("a") as f:
            f.write("{malformed}\n")
    frozen_raw, frozen_cache = raw.read_bytes(), cache.read_bytes()

    def project(row):
        if damage == "drop":
            return None
        if damage == "identity":
            return dict(row, stock_code="changed")
        return buy._slim_economic_cache_row(row)

    projected = dict(
        args,
        project_loaded_payload=project,
        cache_projection_version="economic_source_refs_v1",
    )
    if damage in {"drop", "identity"}:
        with pytest.raises(ValueError, match="projection_population_changed"):
            update_and_load_cached_event_rows(**projected)
        assert cache.read_bytes() == frozen_cache
    else:
        rows, after = update_and_load_cached_event_rows(**projected)
        assert len(rows) == 1 and after["raw_offset"] == before["raw_offset"]
        assert rows[0]["fields"] == {
            "source_quality_status": "pass",
            "evaluation_attempt_id": "exact",
        }
        if damage == "malformed":
            assert (
                cache.read_bytes() == frozen_cache
                and after["cache_projection_skip_reason"]
            )
        else:
            assert cache.stat().st_size < len(frozen_cache) / 10
            once = cache.read_bytes()
            update_and_load_cached_event_rows(**projected)
            assert cache.read_bytes() == once
    assert raw.read_bytes() == frozen_raw
    assert not list((tmp_path / "cache").glob(".sentinel-projection-*"))


def test_legacy_economic_cache_without_projection_retains_unverified_inputs():
    row = {
        "stage": "entry_ai_economic_plan_observed",
        "fields": {
            "entry_economic_conditional_seed": "legacy",
            "entry_economic_operating_context": "required",
        },
    }
    assert buy._slim_economic_cache_row(row) is row


def test_maintenance_streaming_does_not_change_report_population(tmp_path):
    raw = _raw_path(tmp_path)
    _write_lines(
        raw,
        [_event("10:00:00", "blocked_ai_score"), _event("10:01:00", "ai_confirmed")],
    )
    args = dict(
        raw_path=raw,
        cache_dir=tmp_path / "cache",
        cache_name="stream",
        target_date=TARGET_DATE,
        schema_version=1,
        parse_payload=lambda x: x,
        project_loaded_payload=buy._slim_economic_cache_row,
        cache_projection_version="economic_source_refs_v1",
    )
    rows, maintenance = update_and_load_cached_event_rows(**args, load_rows=False)
    assert (
        rows == []
        and maintenance["cache_event_count"] == 2
        and maintenance["materialized_event_count"] == 0
    )
    rows, normal = update_and_load_cached_event_rows(**args)
    assert (
        len(rows)
        == normal["cache_event_count"]
        == normal["materialized_event_count"]
        == 2
    )
    assert normal["appended_cache_rows"] == 0


def _event(
    hhmmss: str,
    stage: str,
    *,
    pipeline: str = "ENTRY_PIPELINE",
    record_id: int = 1,
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{TARGET_DATE}T{hhmmss}",
        "emitted_date": TARGET_DATE,
    }


def _raw_path(tmp_path):
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    return event_dir / f"pipeline_events_{TARGET_DATE}.jsonl"


def _write_lines(path, rows: list[dict], *, malformed: bool = False) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        if malformed:
            handle.write("{malformed-json}\n")


def _without_event_load(report: dict) -> dict:
    return {key: value for key, value in report.items() if key != "event_load"}


def test_incremental_cache_parity_for_malformed_partial_unchanged_and_appended_jsonl(
    tmp_path,
):
    raw_path = _raw_path(tmp_path)
    first = {
        "id": 1,
        "source_quality_status": "pass",
        "provenance_source": "pipeline_event",
    }
    partial = {
        "id": 2,
        "source_quality_status": "warning",
        "provenance_source": "partial_then_completed",
    }
    appended = {
        "id": 3,
        "source_quality_status": "pass",
        "provenance_source": "appended",
    }
    with raw_path.open("wb") as handle:
        handle.write(json.dumps(first).encode() + b"\n")
        handle.write(b"{malformed-json}\n")
        handle.write(json.dumps(partial).encode())

    kwargs = {
        "raw_path": raw_path,
        "cache_dir": tmp_path / "cache",
        "cache_name": "parity",
        "target_date": TARGET_DATE,
        "schema_version": 1,
        "parse_payload": lambda payload: payload,
    }
    first_rows, first_meta = update_and_load_cached_event_rows(**kwargs)

    assert first_rows == [first]
    assert first_meta["decode_errors"] == 1
    assert first_meta["appended_cache_rows"] == 1
    assert first_meta["rebuilt"] is True

    with raw_path.open("ab") as handle:
        handle.write(b"\n")
        handle.write(json.dumps(appended).encode() + b"\n")

    appended_rows, appended_meta = update_and_load_cached_event_rows(**kwargs)

    assert appended_rows == [first, partial, appended]
    assert appended_meta["appended_raw_lines"] == 2
    assert appended_meta["appended_cache_rows"] == 2
    assert appended_meta["decode_errors"] == 0
    assert appended_meta["rebuilt"] is False

    unchanged_rows, unchanged_meta = update_and_load_cached_event_rows(**kwargs)

    assert unchanged_rows == appended_rows
    assert unchanged_meta["appended_raw_lines"] == 0
    assert unchanged_meta["appended_cache_rows"] == 0
    assert unchanged_meta["decode_errors"] == 0
    assert unchanged_meta["rebuilt"] is False


def test_incremental_cache_empty_and_missing_raw_fallback(tmp_path):
    raw_path = _raw_path(tmp_path)
    raw_path.touch()
    kwargs = {
        "raw_path": raw_path,
        "cache_dir": tmp_path / "cache",
        "cache_name": "empty",
        "target_date": TARGET_DATE,
        "schema_version": 1,
        "parse_payload": lambda payload: payload,
    }

    empty_rows, empty_meta = update_and_load_cached_event_rows(**kwargs)
    assert empty_rows == []
    assert empty_meta["status"] == "ok"
    assert empty_meta["cache_event_count"] == 0

    raw_path.unlink()
    missing_rows, missing_meta = update_and_load_cached_event_rows(**kwargs)
    assert missing_rows == []
    assert missing_meta["status"] == "raw_missing"
    assert missing_meta["cache_event_count"] == 0


def test_buy_sentinel_raw_cache_report_parity(monkeypatch, tmp_path):
    monkeypatch.setattr(buy, "DATA_DIR", tmp_path)
    raw_path = _raw_path(tmp_path)
    _write_lines(
        raw_path,
        [
            _event("10:03:00", "order_bundle_submitted", record_id=3),
            _event("10:00:00", "ai_confirmed", record_id=1),
            _event(
                "10:01:00",
                "blocked_ai_score",
                record_id=2,
                fields={
                    "score": 66,
                    "source_quality_status": "pass",
                    "provenance_source": "entry_adm",
                    "actual_order_submitted": False,
                },
            ),
        ],
        malformed=True,
    )
    as_of = buy._parse_as_of(TARGET_DATE, "10:05:00")

    raw_report = buy.build_buy_funnel_sentinel_report(TARGET_DATE, as_of=as_of)
    cache_report = buy.build_buy_funnel_sentinel_report(
        TARGET_DATE, as_of=as_of, use_cache=True
    )

    assert _without_event_load(cache_report) == _without_event_load(raw_report)


def test_holding_exit_sentinel_raw_cache_report_parity(monkeypatch, tmp_path):
    monkeypatch.setattr(holding, "DATA_DIR", tmp_path)
    raw_path = _raw_path(tmp_path)
    _write_lines(
        raw_path,
        [
            _event(
                "10:03:00",
                "sell_order_sent",
                pipeline="HOLDING_PIPELINE",
                record_id=3,
                fields={"actual_order_submitted": True},
            ),
            _event(
                "10:00:00",
                "holding_started",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
            ),
            _event(
                "10:01:00",
                "ai_holding_review",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
                fields={
                    "ai_cache": "miss",
                    "source_quality_status": "pass",
                    "provenance_source": "holding_flow",
                },
            ),
            _event(
                "10:02:00",
                "exit_signal",
                pipeline="HOLDING_PIPELINE",
                record_id=1,
            ),
        ],
        malformed=True,
    )
    as_of = holding._parse_as_of(TARGET_DATE, "10:05:00")

    raw_report = holding.build_holding_exit_sentinel_report(TARGET_DATE, as_of=as_of)
    cache_report = holding.build_holding_exit_sentinel_report(
        TARGET_DATE, as_of=as_of, use_cache=True
    )

    assert _without_event_load(cache_report) == _without_event_load(raw_report)


def test_verified_day_facts_cold_warm_append_correction_partial_and_corruption(
    tmp_path,
):
    from src.engine.sentinel_event_cache import load_verified_day_projection

    source = tmp_path / "pipeline_events_2026-09-16.jsonl"
    cache = tmp_path / "cache"
    source.write_text('{"stage":"route","price":100}\n{"stage":"unrelated"}\n')
    parsed = []

    def project(row):
        parsed.append(row)
        return row if row["stage"] == "route" else {"_census": {"irrelevant": 1}}

    def load():
        return load_verified_day_projection(
            raw_path=source,
            cache_dir=cache,
            cache_name="day-facts",
            parser_version="frozen-parser-v1",
            parse_payload=project,
        )

    cold, first = load()
    parsed.clear()
    warm, second = load()
    assert warm == cold and second["raw_scanned"] is False and parsed == []
    assert first["source_sha256"] == second["source_sha256"]
    with source.open("a") as handle:
        handle.write('{"stage":"route","price":101}\n')
    appended, status = load()
    assert [row["price"] for row in appended] == [100, 101] and status[
        "raw_scanned"
    ] is True
    import os

    before = source.stat()
    source.write_text(source.read_text().replace('"price":100', '"price":102'))
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    corrected, status = load()
    assert corrected[0]["price"] == 102 and status["raw_scanned"] is True
    completed = next(cache.glob("*.json")).read_bytes()
    with source.open("a") as handle:
        handle.write('{"stage":"route","price":')
    partial, status = load()
    assert partial == corrected and status["checkpoint_complete"] is False
    assert next(cache.glob("*.json")).read_bytes() == completed
    with source.open("a") as handle:
        handle.write("103}\n")
    recovered, status = load()
    assert recovered[-1]["price"] == 103 and status["checkpoint_complete"] is True
    next(cache.glob("*.json")).write_text(
        '{"body":{"generation":[]},"body_sha256":"bad"}'
    )
    repaired, status = load()
    assert repaired == recovered and status["raw_scanned"] is True
    # Interrupted temporary publication is never a completed checkpoint.
    checkpoint = next(cache.glob("*.json"))
    (cache / (checkpoint.name + ".interrupted.tmp")).write_text('{"body":')
    unchanged, status = load()
    assert unchanged == recovered and status["raw_scanned"] is False
    # A concurrent retry evaluates changed input but does not overwrite the
    # other writer's checkpoint, and subsequent exclusive retry completes it.
    import fcntl

    completed = checkpoint.read_bytes()
    with checkpoint.with_suffix(".lock").open("a") as concurrent:
        fcntl.flock(concurrent, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with source.open("a") as handle:
            handle.write('{"stage":"route","price":104}\n')
        concurrent_rows, status = load()
        assert concurrent_rows[-1]["price"] == 104 and status["raw_scanned"] is True
        assert checkpoint.read_bytes() == completed
    retry, status = load()
    assert retry == concurrent_rows and status["checkpoint_complete"] is True


def test_verified_zero_stage_census_upgrades_cache_without_raw_bootstrap(tmp_path):
    from src.engine.observation_source_quality_audit import _raw_generation

    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event("10:00:00", "ai_confirmed")])
    kwargs = dict(
        raw_path=raw,
        cache_dir=tmp_path / "cache",
        cache_name="proof",
        target_date=TARGET_DATE,
        schema_version=12,
        parse_payload=lambda payload: payload,
    )
    original, _ = update_and_load_cached_event_rows(**kwargs)
    proof = {
        "from_schema": 12,
        "raw_generation": _raw_generation(raw),
        "population_proof": "verified_zero_stage_census",
        "raw_audit_sha256": "a" * 64,
    }
    refreshed, meta = update_and_load_cached_event_rows(
        **{**kwargs, "schema_version": 13}, verified_schema_migration=proof
    )
    assert refreshed == original
    assert meta["rebuilt"] is False
    assert meta["appended_raw_lines"] == 0
    assert meta["schema_version"] == 13
    assert meta["schema_migration_receipt"] == proof
    raw.write_text(raw.read_text() + "{}\n")
    import pytest

    with pytest.raises(ValueError, match="verified_cache_schema_source_changed"):
        update_and_load_cached_event_rows(
            **{**kwargs, "schema_version": 13}, verified_schema_migration=proof
        )


def test_lossless_funnel_preserves_broker_ambiguity_stage(tmp_path):
    payload = _event(
        "10:00:00",
        "order_leg_owner_registry_reconciliation_required",
        fields={"tag": "ENTRY-L1"},
    )
    row = buy._payload_to_cache_row(payload, exclude_summary_stages=True)
    assert row is not None
    assert row["stage"] == "order_leg_owner_registry_reconciliation_required"


def test_forward_guard_stage_extension_preserves_prefix_without_replay(tmp_path):
    from src.engine.observation_source_quality_audit import _raw_generation

    raw = _raw_path(tmp_path)
    _write_lines(
        raw,
        [
            _event("10:00:00", "ai_confirmed"),
            _event("10:01:00", "real_weak_pullback_entry_block"),
        ],
    )
    args = dict(
        raw_path=raw,
        cache_dir=tmp_path / "cache",
        cache_name="forward",
        target_date=TARGET_DATE,
        schema_version=15,
        parse_payload=lambda r: r if r["stage"] == "ai_confirmed" else None,
    )
    original, old = update_and_load_cached_event_rows(**args)
    proof = {
        "from_schema": 15,
        "to_schema": 17,
        "raw_offset": old["raw_offset"],
        "raw_generation": _raw_generation(raw),
        "population_proof": "forward_only_stage_extension",
        "historical_stage_coverage": "not_backfilled_before_raw_offset",
    }
    with raw.open("a") as f:
        f.write(json.dumps(_event("10:02:00", "real_weak_pullback_entry_block")) + "\n")
    parsed = []

    def parse(row):
        parsed.append(row)
        return row

    rows, meta = update_and_load_cached_event_rows(
        **{**args, "schema_version": 17, "parse_payload": parse},
        verified_schema_migration=proof,
    )
    assert rows[: len(original)] == original and len(rows) == 2
    assert len(parsed) == 1 and parsed[0]["emitted_at"].endswith("10:02:00")
    assert not meta["rebuilt"] and meta["schema_migration_receipt"] == proof
    assert meta["appended_raw_lines"] == 1
    _, later = update_and_load_cached_event_rows(
        **{**args, "schema_version": 17, "parse_payload": parse}
    )
    assert (
        later["schema_migration_receipt"]["historical_stage_coverage"]
        == "not_backfilled_before_raw_offset"
    )


def test_forward_guard_stage_extension_rejects_replaced_source(tmp_path):
    import pytest
    from src.engine.observation_source_quality_audit import _raw_generation

    raw = _raw_path(tmp_path)
    _write_lines(raw, [_event("10:00:00", "ai_confirmed")])
    args = dict(
        raw_path=raw,
        cache_dir=tmp_path / "cache",
        cache_name="forward",
        target_date=TARGET_DATE,
        schema_version=15,
        parse_payload=lambda row: row,
    )
    _, old = update_and_load_cached_event_rows(**args)
    proof = {
        "from_schema": 15,
        "to_schema": 17,
        "raw_offset": old["raw_offset"],
        "raw_generation": _raw_generation(raw),
        "population_proof": "forward_only_stage_extension",
        "historical_stage_coverage": "not_backfilled_before_raw_offset",
    }
    raw.unlink()
    _write_lines(raw, [_event("10:02:00", "ai_confirmed")])
    with pytest.raises(ValueError, match="forward_cache_schema_source_changed"):
        update_and_load_cached_event_rows(
            **{**args, "schema_version": 17}, verified_schema_migration=proof
        )


def test_guard_stages_survive_both_sentinel_cache_modes():
    for stage in [
        "pre_submit_weak_context_late_entry_guard_block",
        "real_weak_pullback_entry_block",
    ]:
        for lossless in [False, True]:
            payload = _event(
                "10:00:00", stage, fields={"reason": "quality_guard_block"}
            )
            assert (
                buy._payload_to_cache_row(payload, exclude_summary_stages=lossless)[
                    "stage"
                ]
                == stage
            )


def test_bounded_cache_decoder_preserves_json_semantics_and_container_isolation():
    from src.engine.sentinel_event_cache import _cache_object_decoder

    decoder = _cache_object_decoder()
    text = '{"same_field_name":{"action":"WAIT","code":"005930","missing":null,"number":1.25,"enabled":false,"rows":[1,2]},"unicode":"한글","dup":1,"dup":2}'
    first = json.loads(text, object_pairs_hook=decoder)
    second = json.loads(text, object_pairs_hook=decoder)
    assert first == second == json.loads(text)
    assert next(iter(first)) is next(iter(second))
    assert first["same_field_name"]["action"] is second["same_field_name"]["action"]
    assert first["same_field_name"] is not second["same_field_name"]
    assert first["same_field_name"]["rows"] is not second["same_field_name"]["rows"]
    first["same_field_name"]["rows"].append(3)
    assert second["same_field_name"]["rows"] == [1, 2]
    # Unique data cannot make the per-read pool unbounded or change any value.
    for index in range(10000):
        expected = {
            f"unique_field_{index}": f"unique_value_{index}",
            "long": "x" * 1000,
        }
        assert json.loads(json.dumps(expected), object_pairs_hook=decoder) == expected


def test_native_liquidity_stage_migration_preserves_prefix_without_replay(
    tmp_path, monkeypatch
):
    from pathlib import Path

    raw = _raw_path(tmp_path)
    _write_lines(
        raw,
        [
            _event("10:00:00", "ai_confirmed"),
            _event("10:01:00", "pre_submit_liquidity_guard_block"),
        ],
    )
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(buy, "_event_cache_dir", lambda: cache_dir)
    args = dict(
        raw_path=raw,
        cache_dir=cache_dir,
        cache_name=buy.EVENT_CACHE_NAME,
        target_date=TARGET_DATE,
        schema_version=20,
        parse_payload=lambda r: (
            buy._payload_to_cache_row(r, exclude_summary_stages=True)
            if r["stage"] != "pre_submit_liquidity_guard_block"
            else None
        ),
    )
    original, old = update_and_load_cached_event_rows(**args)
    prefix = Path(old["cache_path"]).read_bytes()
    with raw.open("a") as stream:
        stream.write(
            json.dumps(_event("10:02:00", "pre_submit_liquidity_guard_block")) + "\n"
        )
    proof = buy._previous_cache_schema_proof(TARGET_DATE, raw, 20)
    assert proof["newly_admitted_stages"] == ["pre_submit_liquidity_guard_block"]
    parsed = []

    def parse(row):
        parsed.append(row)
        return buy._payload_to_cache_row(row, exclude_summary_stages=True)

    rows, meta = update_and_load_cached_event_rows(
        **{
            **args,
            "schema_version": buy.LOSSLESS_EVENT_CACHE_SCHEMA_VERSION,
            "parse_payload": parse,
        },
        verified_schema_migration=proof,
    )
    assert rows[: len(original)] == original and len(rows) == len(original) + 1
    assert len(parsed) == 1 and rows[-1]["stage"] == "pre_submit_liquidity_guard_block"
    assert Path(old["cache_path"]).read_bytes().startswith(prefix)
    assert not meta["rebuilt"] and meta["appended_raw_lines"] == 1
    assert (
        meta["schema_migration_receipt"]["historical_stage_coverage"]
        == "not_backfilled_before_raw_offset"
    )

@pytest.mark.parametrize("damage", [None, "raw", "raw_rotation", "schema", "gzip", "receipt", "legacy", "interrupted", "unlink_failure", "pending_raw_changed", "pending_gzip_changed", "intent_changed", "unrelated_holding", "reviewed_issuer"])
def test_new_closed_archive_roundtrip_and_late_source_fail_closed(tmp_path, monkeypatch, damage):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from pathlib import Path
    from src.engine import sentinel_event_cache as owner
    from src.engine.automation import postclose_done_controller, next_preopen_readiness
    from src.engine.infrastructure import log_retention

    data = tmp_path / "data"
    data.mkdir()
    day = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    raw = data / "pipeline.jsonl"
    row = _event("10:00:00", "ai_confirmed", fields={"attempt": "exact"})
    _write_lines(raw, [row, row])
    args = dict(raw_path=raw, cache_dir=data / "runtime/sentinel_event_cache",
                cache_name="buy_funnel_sentinel_events", target_date=day,
                schema_version=1, parse_payload=lambda x: x, compact_index=True)
    before, meta = owner.update_and_load_cached_event_rows(**args)
    cache = Path(meta["cache_path"])
    original = cache.read_bytes()
    monkeypatch.setattr(postclose_done_controller, "done_terminal_receipt_issues", lambda *a, **kw: [])
    monkeypatch.setattr(next_preopen_readiness, "target_after_postclose", lambda *a, **kw: day)
    monkeypatch.setattr(log_retention, "DocumentReferences", lambda *_: type("Docs", (), {"require_unreferenced": lambda self, names: None})())
    monkeypatch.setattr(log_retention, "open_owned_inodes", lambda: set())
    if damage == "unrelated_holding":
        history = data / "report/holding_exit_sentinel/historical_resolutions"
        history.mkdir(parents=True)
        (history / "existing.json").write_text("original holding evidence")
    if damage == "legacy":
        meta_path = cache.with_suffix(".meta.json")
        legacy = json.loads(meta_path.read_bytes())
        del legacy["closed_archive_contract"]
        meta_path.write_text(json.dumps(legacy))
        with pytest.raises(ValueError, match="sentinel_archive_source_unverified"):
            owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
        assert cache.read_bytes() == original
        return
    if damage == "interrupted":
        real_link = owner.os.link
        calls = []
        def interrupted_link(*args, **kwargs):
            calls.append(args)
            if str(args[1]).endswith(".archive.json"):
                raise OSError("simulated receipt publication failure")
            return real_link(*args, **kwargs)
        with monkeypatch.context() as context:
            context.setattr(owner.os, "link", interrupted_link)
            with pytest.raises(OSError, match="receipt publication failure"):
                owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
        assert cache.read_bytes() == original
        assert Path(str(cache) + ".gz").exists()
        owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
        assert not cache.exists()
        assert len(owner.update_and_load_cached_event_rows(**args)[0]) == 2
        return
    if damage in {"unlink_failure", "pending_raw_changed", "pending_gzip_changed", "intent_changed"}:
        real_unlink = Path.unlink
        def interrupted_unlink(path, *args, **kwargs):
            if path == cache:
                raise OSError("simulated plain unlink failure")
            return real_unlink(path, *args, **kwargs)
        with monkeypatch.context() as context:
            context.setattr(Path, "unlink", interrupted_unlink)
            with pytest.raises(OSError, match="plain unlink failure"):
                owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
        assert cache.read_bytes() == original
        assert Path(str(cache) + ".archive.json").exists()
        if damage == "pending_raw_changed":
            raw.write_bytes(raw.read_bytes() + b'{}\n')
            with pytest.raises(ValueError, match="sentinel_archive_raw_or_schema_changed"):
                owner.update_and_load_cached_event_rows(**args)
            with pytest.raises(ValueError, match="sentinel_archive_source_unverified"):
                owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
            assert cache.read_bytes() == original
            return
        if damage == "pending_gzip_changed":
            archive = Path(str(cache) + ".gz")
            archive.write_bytes(archive.read_bytes() + b"changed")
            with pytest.raises(ValueError, match="sentinel_archive_generation_changed"):
                owner.update_and_load_cached_event_rows(**args)
            with pytest.raises(ValueError, match="sentinel_archive_existing_generation"):
                owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
            assert cache.read_bytes() == original
            return
        if damage == "intent_changed":
            Path(str(cache) + ".archive-intent.json").write_text("{}")
            with pytest.raises(ValueError, match="sentinel_archive_intent_changed"):
                owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
            assert cache.read_bytes() == original
            return
        rows, _ = owner.update_and_load_cached_event_rows(**args)
        assert len(rows) == 2
        assert cache.read_bytes() == original
        owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
        assert not cache.exists()
        return
    issued = owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
    assert not cache.exists()
    archive = Path(str(cache) + ".gz")
    with __import__("gzip").open(archive, "rb") as stream:
        assert stream.read() == original
    if damage == "reviewed_issuer":
        from src.engine.monitoring import sentinel_compact_store as store
        receipt_path = Path(str(cache) + ".archive.json")
        body = json.loads(receipt_path.read_bytes())
        body["issuer_code_sha256"] = "a" * 64
        body.pop("receipt_sha256")
        body["receipt_sha256"] = __import__("hashlib").sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        receipt_path.write_text(json.dumps(body))
        meta = json.loads(cache.with_suffix(".meta.json").read_bytes())
        with pytest.raises(ValueError, match="sentinel_archive_receipt_invalid"):
            owner.archived_cache_binding(cache, meta)
        monkeypatch.setattr(store, "REVIEWED_ARCHIVE_ISSUERS", frozenset({"a" * 64}))
        binding = owner.archived_cache_binding(cache, meta)
        assert binding["logical_sha256"] == body["logical_sha256"]
        body["issuer_code_sha256"] = "b" * 64
        body.pop("receipt_sha256")
        body["receipt_sha256"] = __import__("hashlib").sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        receipt_path.write_text(json.dumps(body))
        with pytest.raises(ValueError, match="sentinel_archive_receipt_invalid"):
            owner.archived_cache_binding(cache, meta)
        return
    if damage is None:
        before_archive = archive.stat()
        before_receipt = Path(str(cache) + ".archive.json").read_bytes()
        repeated = owner.archive_closed_cache(data, args["cache_name"], day, now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
        assert repeated == issued and archive.stat() == before_archive
        assert Path(str(cache) + ".archive.json").read_bytes() == before_receipt
    if damage == "raw":
        raw.write_text(raw.read_text() + json.dumps(row) + "\\n")
    elif damage == "raw_rotation":
        import gzip
        rotated = Path(str(raw) + ".gz")
        rotated.write_bytes(gzip.compress(raw.read_bytes(), mtime=0))
        raw.unlink()
        args["raw_path"] = rotated
    elif damage == "schema":
        args["schema_version"] += 1
    elif damage == "gzip":
        archive.write_bytes(archive.read_bytes() + b"changed")
    elif damage == "receipt":
        Path(str(cache) + ".archive.json").write_text("{}")
    if damage and damage != "unrelated_holding":
        with pytest.raises((ValueError, OSError, KeyError)):
            owner.update_and_load_cached_event_rows(**args)
    else:
        after, receipt = owner.update_and_load_cached_event_rows(**args)
        assert [dict(row["fields"]) for row in after] == [dict(row["fields"]) for row in before]
        assert len(after) == 2 and receipt["archive_binding"]["logical_size"] == len(original)
        if damage == "unrelated_holding":
            assert (history / "existing.json").read_text() == "original holding evidence"
    assert not cache.exists() and archive.exists()


def test_archived_holding_actual_summary_consumer_and_tamper(tmp_path, monkeypatch):
    from datetime import datetime, timedelta
    from pathlib import Path
    from zoneinfo import ZoneInfo
    from src.engine import sentinel_event_cache as owner
    from src.engine.automation import postclose_done_controller, next_preopen_readiness
    from src.engine.infrastructure import log_retention

    data = tmp_path / "data"
    raw_dir = data / "pipeline_events"
    raw_dir.mkdir(parents=True)
    day = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    row = _event("10:00:00", "holding_started", pipeline="HOLDING_PIPELINE",
                 fields={"profit_rate": "2.3", "opaque_context": "kept in full"})
    row.update(emitted_at=f"{day}T10:00:00", emitted_date=day)
    _write_lines(raw_dir / f"pipeline_events_{day}.jsonl", [row])
    monkeypatch.setattr(holding, "DATA_DIR", data)
    before = holding.load_pipeline_events(day, use_cache=True, summary_only=True)
    assert len(before) == 1
    monkeypatch.setattr(postclose_done_controller, "done_terminal_receipt_issues", lambda *a, **kw: [])
    monkeypatch.setattr(next_preopen_readiness, "target_after_postclose", lambda *a, **kw: day)
    monkeypatch.setattr(log_retention, "DocumentReferences", lambda *_: type("Docs", (), {"require_unreferenced": lambda self, names: None})())
    monkeypatch.setattr(log_retention, "open_owned_inodes", lambda: set())
    owner.archive_closed_cache(data, holding.EVENT_CACHE_NAME, day,
                               now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
    assert holding.load_pipeline_events(day, use_cache=True, summary_only=True) == before
    full = holding.load_pipeline_events(day, use_cache=True)
    assert full[0].fields["opaque_context"] == "kept in full"
    # Exercise the native raw-archive reader with a sealed exact old source
    # generation; no source inode is invented for the new gzip.
    from src.engine import compress_db_backfilled_files as raw_archiver
    from src.engine.automation import main_trailing_source_store as trailing

    raw = raw_dir / f"pipeline_events_{day}.jsonl"
    assert trailing.build_step(data, raw)["complete"]
    assert raw_archiver._gzip_file_with_jsonl_generation_lock(raw, dry_run=False)[0]
    raw_gzip = Path(str(raw) + ".gz")
    receipt_path = Path(str(raw_gzip) + ".archive_receipt.json")
    native_receipt = receipt_path.read_bytes()
    assert holding.load_pipeline_events(day, use_cache=True, summary_only=True) == before
    receipt_path.write_text("{}")
    with pytest.raises(ValueError):
        holding.load_pipeline_events(day, use_cache=True, summary_only=True)
    receipt_path.write_bytes(native_receipt)
    from src.utils.pipeline_event_logger import _append_late_pipeline_event_jsonl, _late_pipeline_event_path

    _append_late_pipeline_event_jsonl(raw, '{}\n')
    with pytest.raises(ValueError, match="sentinel_archive_late_source_unverified"):
        holding.load_pipeline_events(day, use_cache=True, summary_only=True)
    _late_pipeline_event_path(raw).unlink()
    archive = data / "runtime/sentinel_event_cache" / f"{holding.EVENT_CACHE_NAME}_{day}.jsonl.gz"
    archive.write_bytes(archive.read_bytes() + b"changed")
    with pytest.raises(ValueError):
        holding.load_pipeline_events(day, use_cache=True, summary_only=True)
    raw_gzip.rename(raw_gzip.with_name(raw_gzip.name + ".preserved"))
    with pytest.raises(ValueError, match="sentinel_archive_raw_missing"):
        holding.load_pipeline_events(day, use_cache=True, summary_only=True)


@pytest.mark.parametrize("foreign_link", [False, True])
def test_archive_sigkill_after_link_recovers_only_owned_temporary(tmp_path, monkeypatch, foreign_link):
    import os
    import signal
    from datetime import datetime, timedelta
    from pathlib import Path
    from zoneinfo import ZoneInfo
    from src.engine import sentinel_event_cache as owner
    from src.engine.automation import next_preopen_readiness, postclose_done_controller
    from src.engine.infrastructure import log_retention

    data = tmp_path / "data"
    day = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    raw = data / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    raw.parent.mkdir(parents=True)
    row = _event("10:00:00", "ai_confirmed")
    row.update(emitted_at=f"{day}T10:00:00", emitted_date=day)
    _write_lines(raw, [row])
    args = dict(raw_path=raw, cache_dir=data / "runtime/sentinel_event_cache",
                cache_name="buy_funnel_sentinel_events", target_date=day,
                schema_version=1, parse_payload=lambda x: x, compact_index=True)
    expected_rows, meta = owner.update_and_load_cached_event_rows(**args)
    cache = Path(meta["cache_path"])
    original = cache.read_bytes()
    archive = Path(str(cache) + ".gz")
    monkeypatch.setattr(postclose_done_controller, "done_terminal_receipt_issues", lambda *a, **kw: [])
    monkeypatch.setattr(next_preopen_readiness, "target_after_postclose", lambda *a, **kw: day)
    monkeypatch.setattr(log_retention, "DocumentReferences", lambda *_: type("Docs", (), {"require_unreferenced": lambda self, names: None})())
    monkeypatch.setattr(log_retention, "open_owned_inodes", lambda: set())
    now = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2)
    child = os.fork()
    if child == 0:
        native_link = os.link
        def die_after_archive_link(source, destination, *args, **kwargs):
            native_link(source, destination, *args, **kwargs)
            if Path(destination) == archive:
                os.kill(os.getpid(), signal.SIGKILL)
        os.link = die_after_archive_link
        try:
            owner.archive_closed_cache(data, args["cache_name"], day, now=now)
        except BaseException:
            import traceback
            traceback.print_exc()
        finally:
            os._exit(1)
    _, status = os.waitpid(child, 0)
    assert os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGKILL
    assert cache.read_bytes() == original and archive.stat().st_nlink == 2
    if foreign_link:
        os.link(archive, cache.parent / "foreign-link")
        with pytest.raises(ValueError, match="sentinel_archive_temporary_link_unverified"):
            owner.archive_closed_cache(data, args["cache_name"], day, now=now)
        assert cache.read_bytes() == original and archive.stat().st_nlink == 3
    else:
        owner.archive_closed_cache(data, args["cache_name"], day, now=now)
        assert not cache.exists() and archive.stat().st_nlink == 1
        rows, _ = owner.update_and_load_cached_event_rows(**args)
        assert rows == expected_rows


@pytest.mark.parametrize("history", ["claimed", "unrelated", "invalid", "locked", "raw_writer_locked", "raw_rotation_locked", "late_source"])
def test_archiver_preserves_only_exact_native_holding_history(tmp_path, monkeypatch, history):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from src.engine import sentinel_event_cache as owner
    from src.engine.automation import postclose_done_controller, next_preopen_readiness
    from src.engine.infrastructure import log_retention
    from src.engine.scalping.entry_split_monitor_projection import _digest

    data = tmp_path / "data"
    raw_dir = data / "pipeline_events"
    raw_dir.mkdir(parents=True)
    day = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    row = _event("10:00:00", "holding_started", pipeline="HOLDING_PIPELINE")
    row.update(emitted_at=f"{day}T10:00:00", emitted_date=day)
    raw = raw_dir / f"pipeline_events_{day}.jsonl"
    _write_lines(raw, [row])
    monkeypatch.setattr(holding, "DATA_DIR", data)
    holding.load_pipeline_events(day, use_cache=True, summary_only=True)
    cache = data / "runtime/sentinel_event_cache" / f"{holding.EVENT_CACHE_NAME}_{day}.jsonl"
    before = cache.read_bytes()
    directory = data / "report/holding_exit_sentinel/historical_resolutions"
    directory.mkdir(parents=True)
    history_day = day if history == "claimed" else "2026-10-01"
    ref = str(data / "runtime/sentinel_event_cache" / f"holding_exit_sentinel_events_{history_day}.jsonl")
    receipt = dict(schema="holding_historical_resolution_receipt_v1", sources={ref: None},
                   resolution={"source_date": history_day}, code={}, accepted_position_ids=[],
                   report_sha256="0" * 64)
    receipt["receipt_sha256"] = _digest(receipt)
    if history == "invalid":
        receipt["receipt_sha256"] = "0" * 64
    evidence = directory / "original.json"
    evidence.write_text(json.dumps(receipt))
    old_receipt = evidence.read_bytes()
    monkeypatch.setattr(postclose_done_controller, "done_terminal_receipt_issues", lambda *a, **kw: [])
    monkeypatch.setattr(next_preopen_readiness, "target_after_postclose", lambda *a, **kw: day)
    monkeypatch.setattr(log_retention, "DocumentReferences", lambda *_: type("Docs", (), {"require_unreferenced": lambda self, names: None})())
    monkeypatch.setattr(log_retention, "open_owned_inodes", lambda: set())
    now = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2)
    if history == "locked":
        import fcntl
        with (directory.parent / ".historical_resolution.lock").open("a") as active:
            fcntl.flock(active, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with pytest.raises(BlockingIOError):
                owner.archive_closed_cache(data, holding.EVENT_CACHE_NAME, day, now=now)
        assert cache.read_bytes() == before
    elif history == "raw_writer_locked":
        import fcntl
        from src.utils.pipeline_event_logger import _pipeline_event_partition_lock_path

        with _pipeline_event_partition_lock_path(raw).open("a") as active:
            fcntl.flock(active, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with pytest.raises(BlockingIOError):
                owner.archive_closed_cache(data, holding.EVENT_CACHE_NAME, day, now=now)
        assert cache.read_bytes() == before
    elif history == "raw_rotation_locked":
        from src.utils.jsonl_io import jsonl_artifact_generation_lock

        with jsonl_artifact_generation_lock(raw, exclusive=True, blocking=False):
            with pytest.raises(OSError, match="jsonl_generation_lock_busy"):
                owner.archive_closed_cache(data, holding.EVENT_CACHE_NAME, day, now=now)
        assert cache.read_bytes() == before
    elif history == "late_source":
        from src.utils.pipeline_event_logger import _append_late_pipeline_event_jsonl

        _append_late_pipeline_event_jsonl(raw, '{}\n')
        with pytest.raises(ValueError, match="sentinel_archive_late_source_unverified"):
            owner.archive_closed_cache(data, holding.EVENT_CACHE_NAME, day, now=now)
        assert cache.read_bytes() == before
    elif history == "unrelated":
        owner.archive_closed_cache(data, holding.EVENT_CACHE_NAME, day, now=now)
        assert not cache.exists()
    else:
        with pytest.raises(ValueError, match="historical_resolution"):
            owner.archive_closed_cache(data, holding.EVENT_CACHE_NAME, day, now=now)
        assert cache.read_bytes() == before
    assert evidence.read_bytes() == old_receipt


def test_archived_entry_actual_flow_report_and_receipt_tamper(tmp_path, monkeypatch):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from pathlib import Path
    from src.engine import sentinel_event_cache as owner
    from src.engine.automation import postclose_done_controller, next_preopen_readiness
    from src.engine.infrastructure import log_retention
    from src.engine.monitoring import intraday_entry_flow_report as flow

    data = tmp_path / "data"
    data.mkdir()
    day = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    row = _event("10:00:00", "ai_confirmed", fields={"scanner_promotion_id": "exact"})
    row.update(emitted_at=f"{day}T10:00:00", emitted_date=day)
    raw = data / "pipeline.jsonl"
    _write_lines(raw, [row])
    _, meta = owner.update_and_load_cached_event_rows(
        raw_path=raw, cache_dir=data / "runtime/sentinel_event_cache",
        cache_name="buy_funnel_sentinel_events", target_date=day,
        schema_version=1, parse_payload=lambda x: x, compact_index=True)
    cache = Path(meta["cache_path"])
    monkeypatch.setattr(flow, "PROJECT_ROOT", tmp_path)
    diagnostic = tmp_path / "diagnostic.json"
    diagnostic.write_text("{}")
    opts = dict(target_date=day, diagnostic_path=diagnostic, generated_at="fixed")
    before = flow.build_report(**opts)
    monkeypatch.setattr(postclose_done_controller, "done_terminal_receipt_issues", lambda *a, **kw: [])
    monkeypatch.setattr(next_preopen_readiness, "target_after_postclose", lambda *a, **kw: day)
    monkeypatch.setattr(log_retention, "DocumentReferences", lambda *_: type("Docs", (), {"require_unreferenced": lambda self, names: None})())
    monkeypatch.setattr(log_retention, "open_owned_inodes", lambda: set())
    owner.archive_closed_cache(data, "buy_funnel_sentinel_events", day,
                               now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
    after = flow.build_report(**opts)
    assert after.pop("source_events").endswith(".jsonl.gz")
    before.pop("source_events")
    assert before == after
    raw.rename(raw.with_name(raw.name + ".preserved"))
    with pytest.raises(FileNotFoundError):
        flow.build_report(**opts)
    with pytest.raises(ValueError, match="sentinel_archive_raw_missing"):
        owner.update_and_load_cached_event_rows(
            raw_path=raw, cache_dir=cache.parent,
            cache_name="buy_funnel_sentinel_events", target_date=day,
            schema_version=1, parse_payload=lambda x: x, compact_index=True)
    monkeypatch.setattr(buy, "DATA_DIR", data)
    with pytest.raises(ValueError, match="sentinel_archive_raw_missing"):
        buy.load_pipeline_events(day, use_cache=True)
    Path(str(cache) + ".archive.json").write_text("{}")
    with pytest.raises(ValueError, match="sentinel_archive_generation_unverified"):
        flow.build_report(**opts)


def test_large_archive_entry_flow_cli_without_digest_session(tmp_path, monkeypatch):
    import base64
    import os
    import tempfile
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from src.engine import sentinel_event_cache as owner
    from src.engine.automation import postclose_done_controller, next_preopen_readiness
    from src.engine.infrastructure import log_retention, validation_digest_session
    from src.engine.monitoring import intraday_entry_flow_report as flow

    assert validation_digest_session.ACTIVE.get() is None
    with tempfile.TemporaryDirectory(prefix="large-archive-cli-", dir=tmp_path) as temporary:
        root = __import__("pathlib").Path(temporary)
        data = root / "data"
        data.mkdir()
        day = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
        random_text = base64.b64encode(os.urandom(34 * 1024 * 1024)).decode("ascii")
        row = _event("10:00:00", "ai_confirmed", fields={"large_payload": random_text})
        row.update(emitted_at=f"{day}T10:00:00", emitted_date=day)
        raw = data / "pipeline.jsonl"
        _write_lines(raw, [row])
        _, meta = owner.update_and_load_cached_event_rows(
            raw_path=raw, cache_dir=data / "runtime/sentinel_event_cache",
            cache_name="buy_funnel_sentinel_events", target_date=day,
            schema_version=1, parse_payload=lambda x: x, compact_index=False,
            load_rows=False)
        cache = __import__("pathlib").Path(meta["cache_path"])
        monkeypatch.setattr(postclose_done_controller, "done_terminal_receipt_issues", lambda *a, **kw: [])
        monkeypatch.setattr(next_preopen_readiness, "target_after_postclose", lambda *a, **kw: day)
        monkeypatch.setattr(log_retention, "DocumentReferences", lambda *_: type("Docs", (), {"require_unreferenced": lambda self, names: None})())
        monkeypatch.setattr(log_retention, "open_owned_inodes", lambda: set())
        owner.archive_closed_cache(data, "buy_funnel_sentinel_events", day,
                                   now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
        archive = __import__("pathlib").Path(str(cache) + ".gz")
        assert archive.stat().st_size > 32 * 1024 * 1024
        monkeypatch.setattr(flow, "PROJECT_ROOT", root)
        assert flow.main(["--target-date", day, "--output-md", str(root / "out.md"),
                          "--output-csv", str(root / "out.csv")]) == 0
        assert (root / "out.md").exists()
        from src.engine.automation import main_trailing_completed_store, main_trailing_source_store
        from src.engine.monitoring import sentinel_compact_store

        monkeypatch.setattr(main_trailing_completed_store, "admit_window", lambda *_: None)
        receipt_path = __import__("pathlib").Path(str(cache) + ".archive.json")
        original_receipt = receipt_path.read_bytes()
        receipt = json.loads(original_receipt)
        binding = {key: receipt[key] for key in ("source_generation", "logical_sha256", "logical_size", "archive_sha256", "archive_generation")}
        # Without issuer admission the unproven physical read exceeds budget.
        with main_trailing_source_store.native_input_session(data, day):
            with pytest.raises(validation_digest_session.ValidationDeferred, match="native_source_read_budget_exceeded"):
                with sentinel_compact_store._verified_archive(cache, binding):
                    pass
        # The native receipt reader admits the exact issued generation.
        with main_trailing_source_store.native_input_session(data, day) as session:
            assert flow.build_report(target_date=day)["source_events"].endswith(".jsonl.gz")
            assert session.native_read_budget["remaining"] == 32 * 1024 * 1024
            assert session.stats["admitted_native_proofs"] > 0
        import hashlib
        receipt["issuer_code_sha256"] = "0" * 64
        receipt.pop("receipt_sha256")
        receipt["receipt_sha256"] = hashlib.sha256(json.dumps(receipt, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        receipt_path.write_text(json.dumps(receipt))
        with main_trailing_source_store.native_input_session(data, day):
            with pytest.raises(ValueError, match="sentinel_archive_generation_unverified"):
                flow.build_report(target_date=day)
        receipt_path.write_bytes(original_receipt)
        with archive.open("ab") as changed:
            changed.write(b"changed")
        with main_trailing_source_store.native_input_session(data, day):
            with pytest.raises(ValueError, match="sentinel_archive_generation_unverified"):
                flow.build_report(target_date=day)


@pytest.mark.parametrize("consumer", ["buy", "holding"])
def test_large_archive_native_sentinel_reader_without_digest_session(tmp_path, monkeypatch, consumer):
    import base64
    import os
    import tempfile
    from datetime import datetime, timedelta
    from pathlib import Path
    from zoneinfo import ZoneInfo
    from src.engine import sentinel_event_cache as owner
    from src.engine.automation import postclose_done_controller, next_preopen_readiness
    from src.engine.infrastructure import log_retention, validation_digest_session

    assert validation_digest_session.ACTIVE.get() is None
    with tempfile.TemporaryDirectory(prefix="large-sentinel-reader-", dir=tmp_path) as temporary:
        data = Path(temporary) / "data"
        raw_dir = data / "pipeline_events"
        raw_dir.mkdir(parents=True)
        day = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
        random_text = base64.b64encode(os.urandom(34 * 1024 * 1024)).decode("ascii")
        module = buy if consumer == "buy" else holding
        stage = "ai_confirmed" if consumer == "buy" else "holding_started"
        pipeline = "ENTRY_PIPELINE" if consumer == "buy" else "HOLDING_PIPELINE"
        row = _event("10:00:00", stage, pipeline=pipeline, fields={"large_payload": random_text})
        row.update(emitted_at=f"{day}T10:00:00", emitted_date=day)
        raw = raw_dir / f"pipeline_events_{day}.jsonl"
        _write_lines(raw, [row])
        monkeypatch.setattr(module, "DATA_DIR", data)
        options = {"summary_only": True} if consumer == "holding" else {}
        before = module.load_pipeline_events(day, use_cache=True, **options)
        assert len(before) == 1
        if consumer == "buy":
            from src.engine.monitoring import sentinel_source_window

            sentinel_source_window.prepare(data)
            lower = datetime.now(ZoneInfo("Asia/Seoul"))
        monkeypatch.setattr(postclose_done_controller, "done_terminal_receipt_issues", lambda *a, **kw: [])
        monkeypatch.setattr(next_preopen_readiness, "target_after_postclose", lambda *a, **kw: day)
        monkeypatch.setattr(log_retention, "DocumentReferences", lambda *_: type("Docs", (), {"require_unreferenced": lambda self, names: None})())
        monkeypatch.setattr(log_retention, "open_owned_inodes", lambda: set())
        owner.archive_closed_cache(data, module.EVENT_CACHE_NAME, day,
                                   now=datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(days=2))
        cache = data / "runtime/sentinel_event_cache" / f"{module.EVENT_CACHE_NAME}_{day}.jsonl"
        assert Path(str(cache) + ".gz").stat().st_size > 32 * 1024 * 1024
        after = module.load_pipeline_events(day, use_cache=True, **options)
        assert after == before
        if consumer == "buy":
            _, window_receipt = sentinel_source_window.read(
                data, lower + timedelta(seconds=1), lower_epoch=lower.timestamp())
            assert window_receipt["window_covered"] is True
            assert window_receipt["cache_archive_binding"]["archive_generation"][2] > 32 * 1024 * 1024
        from src.engine.automation import main_trailing_completed_store, main_trailing_source_store
        monkeypatch.setattr(main_trailing_completed_store, "admit_window", lambda *_: None)
        with main_trailing_source_store.native_input_session(data, day) as session:
            assert module.load_pipeline_events(day, use_cache=True, **options) == before
            if consumer == "buy":
                _, native_window = sentinel_source_window.read(
                    data, lower + timedelta(seconds=1), lower_epoch=lower.timestamp())
                assert native_window["window_covered"] is True
            assert session.native_read_budget["remaining"] == 32 * 1024 * 1024
