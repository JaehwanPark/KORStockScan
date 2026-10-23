import gzip
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.utils import pipeline_event_logger as logger_mod


@pytest.mark.parametrize(
    "value, missing",
    [
        (None, True),
        ("", True),
        (" - ", True),
        ("NULL", True),
        (float("nan"), True),
        ("not_evaluated", True),
        ("not_applicable_cap", True),
        (0, False),
        ("0", False),
        (False, False),
        ("inf", False),
        ("unknown", False),
    ],
)
def test_zero_context_missing_preserves_zero_and_nonmissing_tokens(value, missing):
    assert logger_mod.zero_context_value_missing(value) is missing


@pytest.mark.parametrize(
    "states, primary, defaulted",
    [
        ({}, "not_applicable_zero", 0),
        (
            {"qty": "guard_intended_zero", "cap": "not_applicable_zero"},
            "guard_intended_zero",
            0,
        ),
        (
            {
                "qty": "actual_zero",
                "quote": "stale_defaulted_zero",
                "ratio": "missing_defaulted_zero",
            },
            "stale_defaulted_zero",
            2,
        ),
        (
            {"ratio": "missing_defaulted_zero", "quote": "stale_defaulted_zero"},
            "missing_defaulted_zero",
            2,
        ),
    ],
)
def test_zero_context_fields_preserve_order_counts_and_input(
    states, primary, defaulted
):
    before = list(states.items())
    fields = logger_mod.zero_context_observation_fields(
        domain="", blocker=None, states=states
    )
    assert list(states.items()) == before
    assert fields["zero_context_primary_state"] == primary
    assert fields["zero_context_defaulted_zero_field_count"] == defaulted
    assert fields["zero_context_observed"] is bool(states)
    assert fields["zero_context_domain"] == fields["zero_context_blocker"] == "unknown"
    if states:
        assert list(fields)[-len(states) :] == [
            f"zero_context_{key}_state" for key in states
        ]
    else:
        assert len(fields) == 6
    assert fields["zero_context_forbidden_uses"] == (
        "threshold_mutation,provider_route_change,order_price_relaxation,"
        "quantity_or_cap_change,broker_guard_bypass,stale_quote_bypass,"
        "hard_safety_guard_bypass,real_execution_quality_approval"
    )


def _reset_logger_state(monkeypatch):
    logger_mod._flush_producer_summary_at_exit()
    monkeypatch.setattr(logger_mod, "_PRODUCER_COMPACTOR", None)


def test_bounded_queue_normal_load_preserves_raw_and_compact_transitions(tmp_path, monkeypatch):
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(logger_mod, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(logger_mod, 'TRADING_RULES', SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True))
    monkeypatch.setattr(logger_mod, 'log_info', lambda *a, **k: None)
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue = logger_mod.BoundedObservationQueue(executor)
        for i in range(32):
            assert queue.submit(logger_mod.emit_pipeline_event, 'ENTRY_PIPELINE', 'TEST', '005930',
                'entry_async_disposition', fields={'async_disposition_event_id': str(i),
                'async_disposition': 'entry_path_returned', 'metric_role': 'source_quality_gate'})['status'] == 'queued'
        assert queue.close(timeout=5)
    logger_mod.flush_pipeline_event_producer_summary()
    stats = queue.snapshot()
    assert stats['append_confirmed'] == stats['completed'] == 32
    assert stats['failed'] == stats['unavailable'] == stats['pending_bytes'] == 0
    def identities(base):
        return [row['fields']['async_disposition_event_id']
            for path in base.glob('*.jsonl') for line in path.read_text().splitlines()
            if (row := json.loads(line)).get('stage') == 'entry_async_disposition']
    assert sorted(identities(tmp_path/'pipeline_events')) == sorted(map(str, range(32)))
    assert sorted(identities(tmp_path/'threshold_cycle')) == sorted(map(str, range(32)))


@pytest.mark.parametrize("failure", ["construct", "submit"])
def test_summary_failure_never_prevents_raw_or_threshold_companion(
    monkeypatch, tmp_path, failure
):
    from unittest.mock import Mock

    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        logger_mod, "TRADING_RULES", SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True)
    )
    monkeypatch.setattr(logger_mod, "log_error", Mock())
    compactor = Mock()
    compactor.submit.side_effect = OSError("summary unavailable")
    getter = (
        Mock(side_effect=OSError("summary unavailable"))
        if failure == "construct"
        else Mock(return_value=compactor)
    )
    monkeypatch.setattr(logger_mod, "_get_producer_compactor", getter)
    result = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "TEST",
        "005930",
        "blocked_strength_momentum",
        record_id=73,
        fields={"threshold_family": "strength_momentum"},
    )
    assert result["structured_raw_append_attempted"] is True
    assert result["structured_append_succeeded"] is True
    assert result["structured_compact_append_succeeded"] is True
    assert result["structured_append_status"] == "raw_appended_summary_failed"
    assert result["structured_summary_error_type"] == "OSError"
    assert len(list((tmp_path / "pipeline_events").glob("*.jsonl"))) == 1
    assert len(list((tmp_path / "threshold_cycle").glob("*.jsonl"))) == 1


def test_failed_raw_append_does_not_create_summary_evidence(monkeypatch):
    from unittest.mock import Mock

    monkeypatch.setattr(
        logger_mod, "TRADING_RULES", SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True)
    )
    getter = Mock()
    monkeypatch.setattr(logger_mod, "_get_producer_compactor", getter)
    monkeypatch.setattr(
        logger_mod,
        "_append_pipeline_event_jsonl",
        Mock(side_effect=OSError("raw unavailable")),
    )
    monkeypatch.setattr(logger_mod, "log_error", Mock())
    result = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE", "TEST", "005930", "blocked_strength_momentum"
    )
    assert result["structured_append_succeeded"] is False
    getter.assert_not_called()


@pytest.mark.parametrize(
    "stage",
    ["avg_down_route_arbitration_observed", "avg_down_exit_replay_frame_observed"],
)
def test_avg_down_large_replay_inputs_are_structured_only(stage):
    fields = {
        "source_event_id": "source-1",
        "market": "large-market" * 10000,
        "policy_snapshot": "large-policy" * 10000,
        "actual_order_submitted": "False",
    }
    projected = logger_mod._project_fields_for_text(stage, fields)
    assert projected["source_event_id"] == "source-1"
    assert "market" not in projected and "policy_snapshot" not in projected
    assert len(str(projected)) < 500
    assert len(fields["market"]) > 10000


def test_exact_lifecycle_event_uses_logical_trade_date_partition_across_midnight(
    monkeypatch, tmp_path
):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls(2026, 8, 15, 0, 0, 0, 500_000)
            return value if tz is None else value.replace(tzinfo=tz)

    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(logger_mod, "datetime", FixedDateTime)
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )

    payload = logger_mod.emit_pipeline_event(
        "HOLDING_PIPELINE",
        "TEST",
        "005930",
        "position_rebased_after_fill",
        record_id=77,
        fields={
            "main_lifecycle_identity_schema": (
                "main_scalping_lifecycle_pipeline_identity_v1"
            ),
            "main_lifecycle_id": "mlc-" + "a" * 32,
            "main_lifecycle_trade_date": "2026-08-14",
            "main_lifecycle_decision_authority": ("source_only_lifecycle_observation"),
            "main_lifecycle_runtime_effect": False,
            "main_lifecycle_order_authority": False,
            "main_lifecycle_provider_authority": False,
        },
    )

    assert payload["emitted_date"] == "2026-08-15"
    assert payload["storage_partition_date"] == "2026-08-14"
    event_dir = tmp_path / "pipeline_events"
    logical_path = event_dir / "pipeline_events_2026-08-14.jsonl"
    late_path = event_dir / "pipeline_events_2026-08-14.late.jsonl"
    assert not logical_path.exists()
    assert late_path.exists()
    assert not (
        tmp_path / "pipeline_events" / "pipeline_events_2026-08-15.jsonl"
    ).exists()
    assert json.loads(late_path.read_text(encoding="utf-8"))["emitted_date"] == (
        "2026-08-15"
    )


def test_midnight_lifecycle_append_preserves_existing_gzip_partition(
    monkeypatch, tmp_path
):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls(2026, 8, 15, 0, 0, 0, 500_000)
            return value if tz is None else value.replace(tzinfo=tz)

    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(logger_mod, "datetime", FixedDateTime)
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True)
    gzip_path = event_dir / "pipeline_events_2026-08-14.jsonl.gz"
    with gzip.open(gzip_path, "wt", encoding="utf-8") as handle:
        handle.write('{"existing":true}\n')
    archived_sha256 = hashlib.sha256(gzip_path.read_bytes()).hexdigest()

    logger_mod.emit_pipeline_event(
        "HOLDING_PIPELINE",
        "TEST",
        "005930",
        "position_rebased_after_fill",
        record_id=77,
        fields={
            "main_lifecycle_identity_schema": (
                "main_scalping_lifecycle_pipeline_identity_v1"
            ),
            "main_lifecycle_id": "mlc-" + "b" * 32,
            "main_lifecycle_trade_date": "2026-08-14",
            "main_lifecycle_decision_authority": ("source_only_lifecycle_observation"),
            "main_lifecycle_runtime_effect": False,
            "main_lifecycle_order_authority": False,
            "main_lifecycle_provider_authority": False,
        },
    )

    assert gzip_path.exists()
    assert not (event_dir / "pipeline_events_2026-08-14.jsonl").exists()
    assert hashlib.sha256(gzip_path.read_bytes()).hexdigest() == archived_sha256
    with gzip.open(gzip_path, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    assert rows == [{"existing": True}]
    late_path = event_dir / "pipeline_events_2026-08-14.late.jsonl"
    late_rows = [
        json.loads(line)
        for line in late_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert late_rows[0]["storage_partition_date"] == "2026-08-14"


def test_late_pipeline_event_sidecar_serializes_concurrent_writers(tmp_path):
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    expected = [json.dumps({"sequence": value}) + "\n" for value in range(64)]

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda line: logger_mod._append_late_pipeline_event_jsonl(
                    logical_path,
                    line,
                ),
                expected,
            )
        )

    late_path = tmp_path / "pipeline_events_2026-08-14.late.jsonl"
    observed = [
        json.loads(line)
        for line in late_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert sorted(row["sequence"] for row in observed) == list(range(64))


def test_same_day_pipeline_event_base_serializes_concurrent_writers(tmp_path):
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    expected = [json.dumps({"sequence": value}) + "\n" for value in range(128)]

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(
            executor.map(
                lambda line: logger_mod._append_jsonl(logical_path, line),
                expected,
            )
        )

    observed = [
        json.loads(line)
        for line in logical_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert sorted(row["sequence"] for row in observed) == list(range(128))


def test_existing_base_append_avoids_file_and_parent_fsync(monkeypatch, tmp_path):
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    fsync_calls = []
    monkeypatch.setattr(logger_mod.os, "fsync", fsync_calls.append)

    logger_mod._append_jsonl(logical_path, '{"sequence":1}\n')
    assert len(fsync_calls) == 2

    fsync_calls.clear()
    logger_mod._append_jsonl(logical_path, '{"sequence":2}\n')

    assert fsync_calls == []


def test_late_sidecar_fsyncs_file_and_parent_on_every_append(monkeypatch, tmp_path):
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    fsync_calls = []
    monkeypatch.setattr(logger_mod.os, "fsync", fsync_calls.append)

    logger_mod._append_late_pipeline_event_jsonl(logical_path, '{"sequence":1}\n')
    assert len(fsync_calls) == 2

    fsync_calls.clear()
    logger_mod._append_late_pipeline_event_jsonl(logical_path, '{"sequence":2}\n')

    assert len(fsync_calls) == 2


def test_order_leg_request_existing_hot_path_performs_no_fsync(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "off")
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )
    fsync_calls = []
    monkeypatch.setattr(logger_mod.os, "fsync", fsync_calls.append)

    logger_mod.emit_pipeline_event(
        "BUY_PIPELINE",
        "TEST",
        "005930",
        "order_leg_request",
        fields={"leg_id": "LEG-1"},
    )
    assert len(fsync_calls) == 4

    fsync_calls.clear()
    logger_mod.emit_pipeline_event(
        "BUY_PIPELINE",
        "TEST",
        "005930",
        "order_leg_request",
        fields={"leg_id": "LEG-2"},
    )

    assert fsync_calls == []


def test_emit_pipeline_event_reports_jsonl_disabled_without_append(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=False,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "TEST",
        "005930",
        "order_leg_sent",
        fields={"actual_order_submitted": True},
    )

    assert payload["structured_append_attempted"] is False
    assert payload["structured_append_succeeded"] is False
    assert payload["structured_raw_append_attempted"] is False
    assert payload["structured_append_status"] == "jsonl_disabled"
    assert not (tmp_path / "pipeline_events").exists()


def test_emit_pipeline_event_reports_raw_append_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "off")
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )
    monkeypatch.setattr(
        logger_mod,
        "_append_pipeline_event_jsonl",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("synthetic")),
    )
    monkeypatch.setattr(logger_mod, "log_error", lambda *_args, **_kwargs: None)

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "TEST",
        "005930",
        "order_leg_sent",
        fields={"actual_order_submitted": True},
    )

    assert payload["structured_append_attempted"] is True
    assert payload["structured_raw_append_attempted"] is True
    assert payload["structured_append_succeeded"] is False
    assert payload["structured_append_status"] == "raw_append_failed"
    assert payload["structured_append_error_type"] == "OSError"


def test_pipeline_event_base_completes_short_writes(monkeypatch, tmp_path):
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    original_write = logger_mod.os.write

    def short_write(descriptor, payload):
        chunk_size = max(1, len(payload) // 3)
        return original_write(descriptor, payload[:chunk_size])

    monkeypatch.setattr(logger_mod.os, "write", short_write)
    expected = json.dumps({"message": "가" * 128}, ensure_ascii=False) + "\n"

    logger_mod._append_jsonl(logical_path, expected)

    assert logical_path.read_text(encoding="utf-8") == expected


def test_pipeline_event_base_rejects_invalid_utf8_before_mutation(tmp_path):
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"

    with pytest.raises(UnicodeEncodeError):
        logger_mod._append_jsonl(logical_path, "\ud800\n")

    assert not logical_path.exists()
    assert not logger_mod._pipeline_event_partition_lock_path(logical_path).exists()


def test_pipeline_event_base_rejects_symlink_without_touching_target(tmp_path):
    target = tmp_path / "outside.jsonl"
    target.write_text('{"preserve":true}\n', encoding="utf-8")
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    logical_path.symlink_to(target)

    with pytest.raises(OSError):
        logger_mod._append_jsonl(logical_path, '{"redirected":true}\n')

    assert target.read_text(encoding="utf-8") == '{"preserve":true}\n'


def test_pipeline_event_base_rejects_non_regular_target_without_blocking(tmp_path):
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    os.mkfifo(logical_path)

    with pytest.raises(OSError):
        logger_mod._append_jsonl(logical_path, '{"redirected":true}\n')


def test_pipeline_event_base_and_late_reject_shared_lock_symlink(tmp_path):
    logical_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    lock_target = tmp_path / "outside.lock"
    lock_target.write_text("preserve", encoding="utf-8")
    lock_path = logger_mod._pipeline_event_partition_lock_path(logical_path)
    lock_path.symlink_to(lock_target)

    with pytest.raises(OSError):
        logger_mod._append_jsonl(logical_path, '{"base":true}\n')
    with pytest.raises(OSError):
        logger_mod._append_late_pipeline_event_jsonl(
            logical_path,
            '{"late":true}\n',
        )

    assert lock_target.read_text(encoding="utf-8") == "preserve"
    assert not logical_path.exists()
    assert not logger_mod._late_pipeline_event_path(logical_path).exists()


def test_pipeline_event_writer_pins_parent_directory_across_path_swap(
    monkeypatch,
    tmp_path,
):
    original_dir = tmp_path / "events"
    outside_dir = tmp_path / "outside"
    saved_dir = tmp_path / "events.saved"
    original_dir.mkdir()
    outside_dir.mkdir()
    logical_path = original_dir / "pipeline_events_2026-08-14.jsonl"
    original_prepare = logger_mod._prepare_jsonl_parent
    swapped = False

    def prepare_then_swap(path):
        nonlocal swapped
        descriptor = original_prepare(path)
        if not swapped:
            original_dir.rename(saved_dir)
            original_dir.symlink_to(outside_dir, target_is_directory=True)
            swapped = True
        return descriptor

    monkeypatch.setattr(logger_mod, "_prepare_jsonl_parent", prepare_then_swap)

    logger_mod._append_jsonl(logical_path, '{"pinned":true}\n')

    assert (saved_dir / logical_path.name).read_text(encoding="utf-8") == (
        '{"pinned":true}\n'
    )
    assert not (outside_dir / logical_path.name).exists()


def test_append_revalidates_existing_parent_without_repeated_mkdir(monkeypatch, tmp_path):
    from pathlib import Path
    from src.engine.automation.main_trailing_source_store import _database
    # Main prepares its index before collection. This regression exercises
    # the same warm append boundary while preserving native raw-parent checks.
    prepared=tmp_path/'pipeline_events/pipeline_events_2026-10-10.jsonl'
    with _database(tmp_path,prepared,writer=True):pass
    original = Path.mkdir
    created = []

    def mkdir(path, *args, **kwargs):
        created.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'mkdir', mkdir)
    monkeypatch.setattr(logger_mod, 'DATA_DIR', tmp_path)
    path = logger_mod._event_path('2026-10-10')
    assert not created
    logger_mod._append_jsonl(path, '{"first":true}\n')
    assert created == [path.parent]
    logger_mod._append_jsonl(path, '{"second":true}\n')
    assert created == [path.parent]
    # A warm writer still validates a replaced parent on its next append.
    saved = tmp_path / 'saved'
    path.parent.rename(saved)
    path.parent.symlink_to(saved, target_is_directory=True)
    with pytest.raises(OSError, match='not a real directory'):
        logger_mod._append_jsonl(path, '{"redirected":true}\n')
    assert (saved / path.name).read_text() == '{"first":true}\n{"second":true}\n'


def test_emit_pipeline_event_writes_text_and_jsonl(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=True,
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(
        logger_mod,
        "log_info",
        lambda msg, send_telegram=False: emitted_messages.append(msg),
    )

    payload = logger_mod.emit_pipeline_event(
        "HOLDING_PIPELINE",
        "테스트종목",
        "123456",
        "bad_entry_block_observed",
        record_id=77,
        fields={"reason": "time stop", "profit_rate": "+0.5"},
    )

    assert payload["structured_append_succeeded"] is True
    assert payload["structured_append_status"] == "raw_appended"
    assert payload["structured_compaction_suppressed"] is False
    assert emitted_messages
    assert emitted_messages[0].startswith(
        "[HOLDING_PIPELINE] 테스트종목(123456) stage=bad_entry_block_observed"
    )
    assert "id=77" in emitted_messages[0]
    assert "reason=time|stop" in emitted_messages[0]

    out_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    assert out_path.exists()
    rows = [
        json.loads(line)
        for line in out_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows and rows[0]["schema_version"] == 3
    assert rows[0]["pipeline"] == "HOLDING_PIPELINE"
    assert rows[0]["record_id"] == 77
    assert rows[0]["fields"]["reason"] == "time stop"
    assert "structured_append_succeeded" not in rows[0]

    compact_path = (
        tmp_path
        / "threshold_cycle"
        / f"threshold_events_{payload['emitted_date']}.jsonl"
    )
    assert compact_path.exists()
    compact_rows = [
        json.loads(line)
        for line in compact_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert compact_rows and compact_rows[0]["event_type"] == "threshold_cycle_event"
    assert compact_rows[0]["stage"] == "bad_entry_block_observed"


def test_emit_pipeline_event_suppresses_default_text_info_but_keeps_jsonl(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(
        logger_mod,
        "log_info",
        lambda msg, send_telegram=False: emitted_messages.append(msg),
    )

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "blocked_strength_momentum",
        record_id=77,
        fields={"reason": "below_strength_base", "ai_score": "50"},
    )

    assert emitted_messages == []
    out_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    rows = [
        json.loads(line)
        for line in out_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows and rows[0]["stage"] == "blocked_strength_momentum"
    assert rows[0]["text_payload"].startswith("[ENTRY_PIPELINE] 테스트종목(123456)")
    assert rows[0]["fields"]["reason"] == "below_strength_base"


def test_scanner_high_volume_text_payload_is_compact_but_fields_are_lossless(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=(),
        ),
    )
    fields = {"reason": "same_state", "actual_order_submitted": "False"}
    fields.update({f"diagnostic_{index}": f"value_{index}" for index in range(30)})

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "scalping_scanner_fast_precheck",
        fields=fields,
    )

    assert payload["fields"] == fields
    assert "reason=same_state" in payload["text_payload"]
    assert "diagnostic_29=value_29" not in payload["text_payload"]
    assert "text_field_projection=diagnostic_compact_v1" in payload["text_payload"]
    assert "full_field_count=32" in payload["text_payload"]
    assert "omitted_field_count=30" in payload["text_payload"]

    out_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    raw_row = json.loads(out_path.read_text(encoding="utf-8").strip())
    assert raw_row["fields"] == fields
    assert len(raw_row["text_payload"]) < len(
        " ".join(f"{key}={value}" for key, value in fields.items())
    )


def test_emit_pipeline_event_allowlist_keeps_operational_text_info(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=("order_bundle_submitted",),
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(
        logger_mod,
        "log_info",
        lambda msg, send_telegram=False: emitted_messages.append(msg),
    )

    logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "order_bundle_submitted",
        fields={"actual_order_submitted": "True"},
    )

    assert len(emitted_messages) == 1
    assert "stage=order_bundle_submitted" in emitted_messages[0]


def test_emit_pipeline_event_suppresses_non_real_order_text_info(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=("order_bundle_submitted",),
        ),
    )

    emitted_messages = []
    monkeypatch.setattr(
        logger_mod,
        "log_info",
        lambda msg, send_telegram=False: emitted_messages.append(msg),
    )

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "order_bundle_submitted",
        fields={"actual_order_submitted": "False", "simulated_order": "True"},
    )

    assert emitted_messages == []
    out_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    rows = [
        json.loads(line)
        for line in out_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows and rows[0]["stage"] == "order_bundle_submitted"
    assert rows[0]["fields"]["actual_order_submitted"] == "False"


def test_emit_pipeline_event_writes_reversal_add_gate_blocked_to_compact_stream(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)

    payload = logger_mod.emit_pipeline_event(
        "HOLDING_PIPELINE",
        "테스트종목",
        "123456",
        "reversal_add_gate_blocked",
        record_id=78,
        fields={"gate_reason": "position_at_cap"},
    )

    compact_path = (
        tmp_path
        / "threshold_cycle"
        / f"threshold_events_{payload['emitted_date']}.jsonl"
    )
    compact_rows = [
        json.loads(line)
        for line in compact_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert compact_rows and compact_rows[0]["stage"] == "reversal_add_gate_blocked"


def test_emit_pipeline_event_accepts_dynamic_threshold_family(monkeypatch, tmp_path):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "new_threshold_probe",
        fields={"threshold_family": "entry_new_probe", "value": "1"},
    )

    compact_path = (
        tmp_path
        / "threshold_cycle"
        / f"threshold_events_{payload['emitted_date']}.jsonl"
    )
    compact_rows = [
        json.loads(line)
        for line in compact_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert compact_rows and compact_rows[0]["stage"] == "new_threshold_probe"
    assert compact_rows[0]["family"] == "entry_new_probe"


def test_emit_pipeline_event_shadow_compaction_keeps_raw_and_writes_producer_summary(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "shadow")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", "0")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_SAMPLE_PER_BUCKET", "6")
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)
    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "blocked_strength_momentum",
        record_id=77,
        fields={"reason": "below_strength_base", "buy_ratio": "0.42"},
    )
    logger_mod.flush_pipeline_event_producer_summary(payload["emitted_date"])

    raw_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    raw_rows = [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(raw_rows) == 1
    assert raw_rows[0]["stage"] == "blocked_strength_momentum"
    summary_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_{payload['emitted_date']}.jsonl"
    )
    summary_rows = [
        json.loads(line)
        for line in summary_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert summary_rows and summary_rows[0]["event_count"] == 1
    assert (
        summary_rows[0]["reason_label"]
        == "blocked_strength_momentum:below_strength_base"
    )
    manifest_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{payload['emitted_date']}.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["mode"] == "shadow"
    assert manifest["raw_suppression_enabled"] is False
    assert manifest["sample_per_bucket"] == 6
    assert manifest["coverage_first_event_at"] == payload["emitted_at"]
    assert manifest["coverage_last_event_at"] == payload["emitted_at"]


def test_shadow_compaction_aggregates_identical_high_volume_observation_state(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "shadow")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", "60")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_SAMPLE_PER_BUCKET", "2")
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)
    fields = {
        "fast_precheck_result": "defer",
        "fast_precheck_reason": "waiting_heavy_eval",
        "source_quality_gate": "pass",
        "actual_order_submitted": "False",
        **{f"redundant_context_{index}": str(index) for index in range(30)},
    }
    emitted = [
        logger_mod.emit_pipeline_event(
            "ENTRY_PIPELINE",
            "테스트종목",
            "123456",
            "scalping_scanner_fast_precheck",
            record_id=77,
            fields=fields,
        )
        for _ in range(4)
    ]
    first = emitted[0]
    logger_mod.flush_pipeline_event_producer_summary(first["emitted_date"])

    raw_path = (
        tmp_path / "pipeline_events" / f"pipeline_events_{first['emitted_date']}.jsonl"
    )
    raw_rows = [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(raw_rows) == 4
    assert all(row["fields"] == fields for row in raw_rows)

    summary_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_{first['emitted_date']}.jsonl"
    )
    summary_rows = [
        json.loads(line)
        for line in summary_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(summary_rows) == 1
    assert summary_rows[0]["stage"] == "scalping_scanner_fast_precheck"
    assert summary_rows[0]["event_count"] == 4
    assert summary_rows[0]["summary_detail_level"] == "counts_identity_v2"
    assert len(summary_rows[0]["evidence_hash_sum"]) == 64
    assert "sample_events" not in summary_rows[0]
    assert "field_presence_counts" not in summary_rows[0]

    manifest_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{first['emitted_date']}.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["mode"] == "shadow"
    assert manifest["raw_suppression_enabled"] is False
    assert manifest["suppressed_count"] == 0
    assert manifest["lossless_preserved_count"] == 4


def test_emit_pipeline_event_default_compaction_is_shadow_report_only(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", "0")
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)
    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "blocked_overbought",
        record_id=77,
        fields={"reason": "near_day_high"},
    )
    logger_mod.flush_pipeline_event_producer_summary(payload["emitted_date"])

    raw_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    summary_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_{payload['emitted_date']}.jsonl"
    )
    manifest_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{payload['emitted_date']}.json"
    )
    raw_rows = [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert raw_rows and raw_rows[0]["stage"] == "blocked_overbought"
    assert summary_path.exists()
    assert manifest["mode"] == "shadow"
    assert manifest["runtime_effect"] is False
    assert manifest["raw_suppression_enabled"] is False


def test_emit_pipeline_event_suppress_mode_preserves_lossless_allowlist(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "suppress")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", "0")
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)
    suppressed = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "strength_momentum_observed",
        record_id=1,
        fields={"reason": "near_day_high"},
    )
    preserved = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "blocked_overbought",
        record_id=2,
        fields={"reason": "near_day_high"},
    )
    logger_mod.flush_pipeline_event_producer_summary(preserved["emitted_date"])

    assert suppressed["structured_append_succeeded"] is True
    assert suppressed["structured_raw_append_attempted"] is True
    assert suppressed["structured_compaction_suppressed"] is False
    assert suppressed["structured_append_status"] == "raw_appended"
    assert preserved["structured_append_succeeded"] is True
    assert preserved["structured_append_status"] == "raw_appended"

    raw_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{preserved['emitted_date']}.jsonl"
    )
    raw_rows = [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [row["record_id"] for row in raw_rows] == [1, 2]
    summary_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_{preserved['emitted_date']}.jsonl"
    )
    summary_rows = [
        json.loads(line)
        for line in summary_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert sum(int(row["event_count"]) for row in summary_rows) == 2
    manifest_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{preserved['emitted_date']}.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["raw_suppression_enabled"] is False
    assert manifest["requested_mode"] == "suppress"
    assert manifest["mode"] == "shadow"
    assert manifest["suppressed_count"] == 0
    assert manifest["lossless_preserved_count"] == 1


def test_suppress_mode_preserves_high_volume_source_quality_observation(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "suppress")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", "0")
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)
    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "rising_missed_nxt_post_block_price_sample",
        fields={
            "source_quality_gate": "pass",
            "actual_order_submitted": "False",
            "broker_order_forbidden": "True",
        },
    )
    logger_mod.flush_pipeline_event_producer_summary(payload["emitted_date"])

    raw_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    raw_rows = [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(raw_rows) == 1
    assert raw_rows[0]["fields"]["source_quality_gate"] == "pass"

    manifest_path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{payload['emitted_date']}.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["raw_suppression_enabled"] is False
    assert manifest["suppressed_count"] == 0
    assert manifest["lossless_preserved_count"] == 1


def test_emit_pipeline_event_compacts_submit_stage_threshold_stream(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)
    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "order_bundle_submitted",
        record_id=77,
        fields={
            "actual_order_submitted": "True",
            "threshold_family": "latency_classifier_runtime_profile",
            "order_price": "10000",
            "submitted_order_price": "10000",
            "microstructure_reaction_context_status": "ok",
            "microstructure_reaction_context_hash": "abc123",
            "ka10003_buy_dominance_observation_source_counts": "{'1030_1031_split': 2}",
            "ka10003_buy_dominance_observation_trade_value_source_counts": "{'1313': 1}",
            "ka10003_buy_dominance_observation_inside_spread_count": "1",
            "ka10003_buy_dominance_observation_split_vs_15_mismatch_count": "1",
            "v_pw_source": "ka10046_rest_fallback",
            "v_pw_runtime_support_usable": "False",
            "ka10046_strength_source": "ka10046_rest_strength_trend",
            "ka10046_strength_rest_received_ts_ms": "1780000001000",
            "market_data_signed_tape_state": "sell_dominated",
            "market_data_signed_tape_sample_count": "3",
            "market_data_rest_signed_tape_pressure_usable": "False",
            "rest_signed_trade_ticks": "[{'signed_trade_volume': '-100', 'rest_signed_tape_source': 'ka10084'}]",
            "latency_true_ofi_direct_canary_signed_tape_sample_count": "3",
            "latency_true_ofi_direct_canary_signed_tape_sell_dominated": "True",
            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume": "-250",
            "latency_true_ofi_direct_canary_tape_block_reason": "signed_tape_sell_dominated",
            **{f"extra_field_{idx}": str(idx) for idx in range(50)},
        },
    )

    raw_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    raw_rows = [
        json.loads(line)
        for line in raw_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert "extra_field_49" in raw_rows[0]["fields"]

    compact_path = (
        tmp_path
        / "threshold_cycle"
        / f"threshold_events_{payload['emitted_date']}.jsonl"
    )
    compact_rows = [
        json.loads(line)
        for line in compact_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    compact_fields = compact_rows[0]["fields"]
    # Broker terminal conservation now requires this execution stage losslessly.
    assert compact_fields == raw_rows[0]["fields"]
    assert compact_fields["extra_field_49"] == "49"
    assert (
        compact_fields["ka10003_buy_dominance_observation_source_counts"]
        == "{'1030_1031_split': 2}"
    )
    assert (
        compact_fields["ka10003_buy_dominance_observation_trade_value_source_counts"]
        == "{'1313': 1}"
    )
    assert (
        compact_fields["ka10003_buy_dominance_observation_inside_spread_count"] == "1"
    )
    assert (
        compact_fields["ka10003_buy_dominance_observation_split_vs_15_mismatch_count"]
        == "1"
    )
    assert compact_fields["v_pw_source"] == "ka10046_rest_fallback"
    assert compact_fields["v_pw_runtime_support_usable"] == "False"
    assert compact_fields["ka10046_strength_source"] == "ka10046_rest_strength_trend"
    assert compact_fields["ka10046_strength_rest_received_ts_ms"] == "1780000001000"
    assert compact_fields["market_data_signed_tape_state"] == "sell_dominated"
    assert compact_fields["market_data_signed_tape_sample_count"] == "3"
    assert compact_fields["market_data_rest_signed_tape_pressure_usable"] == "False"
    assert (
        compact_fields["rest_signed_trade_ticks"]
        == "[{'signed_trade_volume': '-100', 'rest_signed_tape_source': 'ka10084'}]"
    )
    assert (
        compact_fields["latency_true_ofi_direct_canary_signed_tape_sample_count"] == "3"
    )
    assert (
        compact_fields["latency_true_ofi_direct_canary_signed_tape_sell_dominated"]
        == "True"
    )
    assert (
        compact_fields["latency_true_ofi_direct_canary_signed_tape_net_buy_volume"]
        == "-250"
    )
    assert (
        compact_fields["latency_true_ofi_direct_canary_tape_block_reason"]
        == "signed_tape_sell_dominated"
    )
    assert "extra_field_49" in compact_fields


def test_emit_pipeline_event_compacts_high_volume_threshold_stream_losslessly(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "shadow")
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: None)
    fields = {
        "threshold_family": "rising_missed_tp1_selector",
        "decision_authority": "source_only_candidate_to_submit_safety_projection",
        "actual_order_submitted": "False",
        "broker_order_forbidden": "True",
        "rising_missed_tp1_evaluation_id": "eval-1",
        "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
        "rising_missed_tp1_counterfactual_submit_safety_action": "RECHECK_REQUIRED",
        "rising_missed_tp1_counterfactual_submit_safety_risks": "depth_support_weak",
        "effective_venue": "NXT",
        "venue_resolution": "explicit_nxt",
        **{f"redundant_context_{idx}": str(idx) for idx in range(160)},
    }

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "rising_missed_tp1_counterfactual_submit_safety",
        fields=fields,
    )

    raw_path = (
        tmp_path
        / "pipeline_events"
        / f"pipeline_events_{payload['emitted_date']}.jsonl"
    )
    raw_fields = json.loads(raw_path.read_text(encoding="utf-8"))["fields"]
    assert raw_fields == fields

    compact_path = (
        tmp_path
        / "threshold_cycle"
        / f"threshold_events_{payload['emitted_date']}.jsonl"
    )
    compact_fields = json.loads(compact_path.read_text(encoding="utf-8"))["fields"]
    assert compact_fields["field_projection"] == "high_volume_compact_v1"
    assert compact_fields["full_fields_hash"]
    assert compact_fields["rising_missed_tp1_evaluation_id"] == "eval-1"
    assert (
        compact_fields["rising_missed_tp1_counterfactual_submit_safety_action"]
        == "RECHECK_REQUIRED"
    )
    assert compact_fields["effective_venue"] == "NXT"
    assert "redundant_context_159" not in compact_fields


def test_pipeline_event_compaction_defaults_bound_summary_overhead(monkeypatch):
    monkeypatch.delenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", raising=False)
    monkeypatch.delenv("PIPELINE_EVENT_COMPACTION_SAMPLE_PER_BUCKET", raising=False)
    monkeypatch.setattr(logger_mod, "TRADING_RULES", SimpleNamespace())

    assert logger_mod._compaction_flush_sec() == 60
    assert logger_mod._compaction_sample_per_bucket() == 2


def test_pipeline_event_compaction_sample_setting_is_bounded(monkeypatch, tmp_path):
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_SAMPLE_PER_BUCKET", "99")
    compactor = logger_mod.ProducerSummaryCompactor(
        summary_dir=tmp_path,
        mode="shadow",
        sample_per_bucket=logger_mod._compaction_sample_per_bucket(),
    )

    assert compactor.sample_per_bucket == 6


def test_emit_pipeline_event_keeps_id_in_submit_stage_text_payload(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    _reset_logger_state(monkeypatch)
    monkeypatch.delenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", raising=False)
    monkeypatch.setattr(
        logger_mod,
        "TRADING_RULES",
        SimpleNamespace(
            PIPELINE_EVENT_JSONL_ENABLED=True,
            PIPELINE_EVENT_SCHEMA_VERSION=3,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False,
        ),
    )
    emitted_messages = []
    monkeypatch.setattr(
        logger_mod,
        "log_info",
        lambda msg, send_telegram=False: emitted_messages.append(msg),
    )

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "order_bundle_submitted",
        record_id=77,
        fields={
            **{f"extra_field_{idx}": str(idx) for idx in range(50)},
            "actual_order_submitted": "True",
        },
    )

    assert "id=77" in payload["text_payload"]


@pytest.mark.parametrize("stage", ["entry_execution_sizing_plan", "order_leg_sent", "order_bundle_submitted",
    "entry_cancel_wait_submission","entry_order_cancel_confirmed"])
def test_compact_execution_contract_survives_large_field_count(stage):
    fields = {f"extra_{i}": str(i) for i in range(80)}
    fields.update(entry_execution_sizing_plan_id="parent", entry_execution_sizing_plan_sha256="a" * 64,
        entry_price_plan_sha256="b" * 64, entry_opportunity_replay_seed="{frozen}", broker_order_no="007")
    compact = logger_mod._project_fields_for_compact_stream(stage, fields)
    for key in ("entry_execution_sizing_plan_id", "entry_execution_sizing_plan_sha256",
                "entry_price_plan_sha256", "entry_opportunity_replay_seed", "broker_order_no"):
        assert compact[key] == fields[key]


def test_execution_producer_family_projection_has_reconciled_census(monkeypatch, tmp_path):
    from src.engine.scalping import entry_split_order_plan as owner
    from src.engine.pipeline_event_summary import execution_projection_identity
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(logger_mod, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(owner, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(logger_mod, 'TRADING_RULES', SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True,
        PIPELINE_EVENT_SCHEMA_VERSION=3, PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False))
    monkeypatch.setattr(logger_mod, 'log_info', lambda *a, **k: None)
    event = logger_mod.emit_pipeline_event('ENTRY_PIPELINE','TEST','005930',
        'entry_ai_economic_source_gap', record_id=1, fields={'evaluation_attempt_id':'pre-ai-1',
        'entry_economic_source_blocker':'exact_broker_capacity_missing',
        **{f'field-{i}':str(i) for i in range(80)}})
    day = event['emitted_date']
    logger_mod.flush_pipeline_event_producer_summary(day)
    flat = tmp_path / 'threshold_cycle' / f'threshold_events_{day}.jsonl'
    # A growing unrelated flat stream must not force a raw scan.
    with flat.open('r+b') as handle: handle.truncate(65*1024*1024)
    rows, contract = owner._bounded_execution_projection(day)
    assert len(rows) == 1
    assert rows[0]['fields']['field-79'] == '79'
    assert contract['producer_census']['identity_conservation_holds'] is True
    assert contract['full_population_coverage_verified'] is True
    assert contract['flat_compact_included'] is False
    part = next((tmp_path / 'threshold_cycle' / f'date={day}' / 'family=dynamic_entry_price_resolver').glob('part-execution-*'))
    tampered = json.loads(part.read_text());tampered['fields']['evaluation_attempt_id']='changed'
    part.write_text(json.dumps(tampered)+'\n')
    with pytest.raises(ValueError, match='content_identity_mismatch'):
        owner._bounded_execution_projection(day)
    # Even a correctly resealed projection cannot alter the original producer census.
    tampered['execution_source_event_sha256'] = execution_projection_identity(tampered)
    part.write_text(json.dumps(tampered)+'\n')
    _, bad = owner._bounded_execution_projection(day)
    assert bad['status'] == 'source_gap'
    logger_mod._flush_producer_summary_at_exit()
    monkeypatch.setattr(logger_mod,'_PRODUCER_COMPACTOR',None)


def test_restart_drain_closes_loaded_observers_before_summary(monkeypatch):
    import sys
    calls = []
    monkeypatch.setitem(sys.modules, 'src.engine.kiwoom_sniper_v2', SimpleNamespace(
        close_observation_sources=lambda: calls.append('observations') or True))
    monkeypatch.setattr(logger_mod, '_PRODUCER_COMPACTOR', SimpleNamespace(
        enable_termination_drain=lambda: calls.append('synchronous'),
        flush=lambda: calls.append('summary')))
    monkeypatch.setattr(logger_mod, '_RETIRING_COMPACTORS', [])
    monkeypatch.setattr(logger_mod, '_TERMINATION_DRAIN_ACTIVE', False)
    logger_mod.drain_pipeline_event_summary_before_termination()
    assert calls == ['observations', 'synchronous', 'summary']


def test_summary_drain_does_not_import_an_unstarted_engine(monkeypatch):
    import sys
    monkeypatch.delitem(sys.modules, 'src.engine.kiwoom_sniper_v2', raising=False)
    calls = []
    monkeypatch.setattr(logger_mod, '_PRODUCER_COMPACTOR', SimpleNamespace(
        enable_termination_drain=lambda: None, flush=lambda: calls.append('summary')))
    monkeypatch.setattr(logger_mod, '_RETIRING_COMPACTORS', [])
    monkeypatch.setattr(logger_mod, '_TERMINATION_DRAIN_ACTIVE', False)
    logger_mod.drain_pipeline_event_summary_before_termination()
    assert calls == ['summary']
    assert 'src.engine.kiwoom_sniper_v2' not in sys.modules


@pytest.mark.parametrize('fault', ['missing', 'raise'])
def test_restart_observation_failure_remains_visible_and_summary_still_drains(monkeypatch, fault):
    import sys
    calls = []
    def fail():
        raise OSError('fixture')
    monkeypatch.setitem(sys.modules, 'src.engine.kiwoom_sniper_v2', SimpleNamespace(
        **({'close_observation_sources': fail} if fault == 'raise' else {})))
    monkeypatch.setattr(logger_mod, 'log_error', lambda value: calls.append(value))
    monkeypatch.setattr(logger_mod, '_PRODUCER_COMPACTOR', SimpleNamespace(
        enable_termination_drain=lambda: None, flush=lambda: calls.append('summary')))
    monkeypatch.setattr(logger_mod, '_RETIRING_COMPACTORS', [])
    monkeypatch.setattr(logger_mod, '_TERMINATION_DRAIN_ACTIVE', False)
    logger_mod.drain_pipeline_event_summary_before_termination()
    assert len(calls) == 2 and 'SOURCE_OBSERVATION_SHUTDOWN' in calls[0]
    assert calls[-1] == 'summary'


def test_graceful_sigterm_drain_preserves_admitted_rows(tmp_path):
    """Controlled child only; no trading process, signal handler or orders."""
    import subprocess
    import sys
    from pathlib import Path
    for drained in (False, True):
        directory = tmp_path / str(drained)
        script = f'''
import ast, os, signal, sys
sys.addaudithook(lambda event,args: (_ for _ in ()).throw(RuntimeError('child_network_forbidden'))
    if event in ('socket.connect','socket.getaddrinfo','socket.sendto') else None)
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from src.utils import pipeline_event_logger as logger
from src.engine.scalping import pre_submit_delay_observation as observer
logger.DATA_DIR = Path({str(directory)!r})
os.environ["PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE"] = "shadow"
os.environ["PIPELINE_EVENT_COMPACTION_FLUSH_SEC"] = "3600"
logger.emit_pipeline_event("ENTRY_PIPELINE", "TEST", "005930", "scalping_scanner_fast_precheck", record_id=1)
queue = logger.BoundedObservationQueue(ThreadPoolExecutor(max_workers=1))
observer.configure_sink(queue.submit)
for identity in ('first', 'second'):
    observer.register('005930', dict(id=identity, committed_at_epoch=1, remaining_sec=[120,180],
        decision_source_sha256='a'*64), commit=dict(delay_intent_id=identity, decision_source_sha256='a'*64))
# Execute the actual cleanup function without importing Main's DB/WS startup.
tree = ast.parse(Path('src/engine/kiwoom_sniper_v2.py').read_text())
native = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name=='close_observation_sources')
context = dict(_SCANNER_OBSERVATION_QUEUE=queue, log_error=print)
exec(compile(ast.Module(body=[native],type_ignores=[]),'native-cleanup','exec'),context)
sys.modules['src.engine.kiwoom_sniper_v2'] = SimpleNamespace(close_observation_sources=context['close_observation_sources'])
if {drained!r}:
    logger.drain_pipeline_event_summary_before_termination()
os.kill(os.getpid(), signal.SIGTERM)
'''
        result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).parents[2], capture_output=True, timeout=15)
        assert result.returncode == -15
        raw = [json.loads(line) for p in directory.glob("pipeline_events/*.jsonl")
               for line in p.read_text().splitlines()]
        if drained:
            assert len(raw) == 5, result.stdout + result.stderr
        else:
            assert 1 <= len(raw) <= 3  # Enqueue alone cannot promise raw append.
        terminals = [row for row in raw if row['stage']=='pre_submit_delay_intent_terminal']
        assert len(terminals) == (2 if drained else 0)
        for row in terminals:
            assert row['fields']['observation_only']=='True'
            assert row['fields']['actual_order_submitted']=='False'
            assert row['fields']['broker_order_forbidden']=='True'
        paths = list(directory.glob("pipeline_event_summaries/pipeline_event_producer_summary_*.jsonl"))
        assert bool(paths) is drained
        if drained:
            assert sum(json.loads(line)["event_count"] for p in paths for line in p.read_text().splitlines()) == 5
    # Self-SIGTERM was removed: Main joins the engine's real collector finally
    # before the existing summary drain. End-to-end branches live in the restart
    # race suite; this test keeps only its original summary-loss demonstration.


def test_restart_drain_keeps_late_scanner_rows_bound_to_first_stage(monkeypatch, tmp_path):
    from src.engine.automation import postclose_summary_handoff as handoff

    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(logger_mod, "_RETIRING_COMPACTORS", [])
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path / "data")
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "shadow")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", "3600")
    fields = {"scanner_promotion_id": "fixture-promotion", "broker_order_forbidden": True}
    first = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE", "fixture", "122350", "scalping_scanner_fast_precheck",
        record_id=47859, fields=fields,
    )
    day = first["emitted_date"]
    logger_mod.drain_pipeline_event_summary_before_termination()
    late = [
        logger_mod.emit_pipeline_event(
            "ENTRY_PIPELINE", "fixture", "122350", stage,
            record_id=47859, fields=fields,
        )
        for stage in (
            "scalping_scanner_promotion_latency_trace",
            "scalping_scanner_heavy_eval_lag",
            "scalping_scanner_heavy_eval_completion",
        )
    ]
    assert all(row["structured_append_succeeded"] for row in late)

    monkeypatch.setattr(handoff, "stage_commands", lambda *args, **kwargs: [["fixture"]])
    monkeypatch.setattr(handoff, "_stage_code", lambda *args, **kwargs: "fixture-code")
    monkeypatch.setattr(handoff, "stage_artifacts", lambda *args, **kwargs: {})
    monkeypatch.setattr(handoff, "_safe_stage_output_issues", lambda *args: [])
    report_dir = tmp_path / "data" / "report"
    calls = []
    receipt = handoff.run_stage(
        "pre_submit_delay", day, report_dir=report_dir, project=tmp_path,
        runner=lambda *args, **kwargs: calls.append(args) or 0,
    )
    assert receipt["status"] == "succeeded", receipt
    assert len(calls) == 1
    assert not handoff.stage_receipt_issues(
        report_dir, day, "pre_submit_delay", code_hash="fixture-code"
    )
    from src.engine.scalping.pre_submit_delay_tuning import family_source_ledger_path
    ledger = json.loads(family_source_ledger_path(tmp_path / "data", day).read_text())
    assert sum(part["raw_count"] for part in ledger["raw_parts"]) == 4
    if ledger['schema']=='pre_submit_delay_family_source_ledger_v2':
        # Scanner timing is summary telemetry; v2 selects only committed
        # same-intent delay observations into its economic source ledger.
        assert ledger['raw_event_id_n']==0
        assert ledger['matched_event_ids_ref']['count']==0
        assert ledger['raw_only_event_count']==ledger['compact_only_event_count']==0
        from src.engine.pipeline_event_summary import producer_summary_paths,load_summary_rows
        summary_path,_=producer_summary_paths(tmp_path/'data/pipeline_event_summaries',day)
        stages={row['stage']:row['event_count'] for row in load_summary_rows(summary_path,strict=True)}
        assert stages=={row['stage']:1 for row in [first,*late]}
    else:
        assert ledger["summary_diagnostic"]["raw_summary_gap_by_stage"] == {}

    logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE", "fixture", "122350", "scalping_scanner_fast_precheck",
        record_id=47860, fields=fields,
    )
    issues = handoff.stage_receipt_issues(report_dir, day, "pre_submit_delay", code_hash="fixture-code")
    # Native v2 detects the changed partition inside its lineage validator;
    # legacy ledgers expose the same rejection through raw generation checks.
    assert set(issues) & {"pre_submit_delay:raw_generation_changed",
                          "pre_submit_delay:family_source_ledger_missing_or_invalid"}
    logger_mod._flush_producer_summary_at_exit()


def test_mode_handover_keeps_old_compactor_for_shutdown_drain(monkeypatch, tmp_path):
    import threading
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(logger_mod, "_RETIRING_COMPACTORS", [])
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "shadow")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", "3600")
    old = logger_mod._get_producer_compactor()
    entered, release = threading.Event(), threading.Event()
    publish = old._publish
    def delayed(*args):
        entered.set()
        assert release.wait(3)
        return publish(*args)
    monkeypatch.setattr(old, "_publish", delayed)
    payload = logger_mod.emit_pipeline_event("ENTRY_PIPELINE", "TEST", "005930", "scalping_scanner_fast_precheck", record_id=1)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "off")
    try:
        assert logger_mod._get_producer_compactor() is None
        assert entered.wait(1)
        assert old in logger_mod._RETIRING_COMPACTORS
    finally:
        release.set()
        logger_mod.drain_pipeline_event_summary_before_termination()
    assert logger_mod._RETIRING_COMPACTORS == []
    paths = list((tmp_path / "pipeline_event_summaries").glob("pipeline_event_producer_summary_*.jsonl"))
    assert sum(json.loads(line)["event_count"] for path in paths for line in path.read_text().splitlines()) == 1


def test_repeated_failed_handover_has_two_bounded_owners(monkeypatch, tmp_path):
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(logger_mod, "_RETIRING_COMPACTORS", [])
    monkeypatch.setattr(logger_mod, "DATA_DIR", tmp_path)
    monkeypatch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "shadow")
    monkeypatch.setenv("PIPELINE_EVENT_COMPACTION_FLUSH_SEC", "3600")
    old = logger_mod._get_producer_compactor()
    logger_mod.emit_pipeline_event("ENTRY_PIPELINE", "TEST", "005930", "scalping_scanner_fast_precheck", record_id=1)
    with monkeypatch.context() as patch:
        # Hold actual admitted buffers across asynchronous handover failure.
        patch.setattr(old, "close", lambda **kwargs: None)
        patch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "suppress")
        current = logger_mod._get_producer_compactor()
        logger_mod.emit_pipeline_event("ENTRY_PIPELINE", "TEST", "005930", "scalping_scanner_fast_precheck", record_id=2)
        patch.setattr(current, "close", lambda **kwargs: None)
        for mode in ("off", "shadow", "off", "shadow"):
            patch.setenv("PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", mode)
            assert logger_mod._get_producer_compactor() is None
            assert logger_mod._RETIRING_COMPACTORS == [old]
            assert logger_mod._PRODUCER_COMPACTOR is current
    logger_mod.drain_pipeline_event_summary_before_termination()
    assert not old._groups and not current._groups


def test_delay_category_reserves_capacity_and_drain_yields_to_existing_executor():
    import threading
    entered,released=threading.Event(),threading.Event()
    order=[]
    def append(identity):
        if identity==0:
            entered.set();assert released.wait(5)
        order.append(identity)
        return {'structured_append_succeeded':True}
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue=logger_mod.BoundedObservationQueue(executor,max_items=32,max_bytes=128*1024)
        assert queue.submit(append,0,observation_category='pre_submit_delay')['status']=='queued'
        assert entered.wait(5)
        for n in range(1,8):
            assert queue.submit(append,n,observation_category='pre_submit_delay')['status']=='queued'
        assert queue.submit(append,8,observation_category='pre_submit_delay')['status']=='unavailable'
        for n in range(8,32):
            assert queue.submit(append,n)['status']=='queued'
        urgent=executor.submit(lambda:order.append('main'))
        released.set();assert queue.close(timeout=5);urgent.result(timeout=5)
    assert order.index('main')<=8
    assert sorted(v for v in order if isinstance(v,int))==list(range(32))
    stats=queue.snapshot()
    assert stats['append_confirmed']==32 and stats['failed']==stats['pending_bytes']==0


def test_main_stop_source_keeps_one_structured_body_and_text_reference():
    from src.utils.pipeline_event_logger import _project_fields_for_text, _project_fields_for_compact_stream
    fields={'main_stop_source':'{"source":"full"}','position_key':'record:1','stop_source_sha256':'a'*64}
    assert _project_fields_for_compact_stream('main_stop_source',fields)==fields
    diagnostic=_project_fields_for_text('main_stop_source',fields)
    assert 'main_stop_source' not in diagnostic and diagnostic['stop_source_sha256']=='a'*64


def test_append_outcomes_conserve_completed_and_bound_owner_diagnostics():
    def confirmed(): return {'structured_append_succeeded': True}
    def skipped(): return {'status': 'intentionally_not_written', 'reason': 'throttled'}
    def absent(): return None
    def failed(): return {'structured_append_succeeded': False}
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue = logger_mod.BoundedObservationQueue(executor)
        for callback in (confirmed, skipped, absent, failed):
            assert queue.submit(callback)['status'] == 'queued'
        assert queue.close(timeout=3)
    stats = queue.snapshot()
    assert stats['completed'] == stats['append_confirmed'] + stats['intentionally_not_written'] + stats['append_unobservable'] == 3
    assert stats['queued'] == stats['completed'] + stats['append_failed'] + stats['pending_items'] == 4
    assert stats['failed'] == 1 and len(stats['outcomes_by_owner']) == 4


def test_trailing_queue_freezes_inputs_reserves_capacity_and_reports_writer_failure(monkeypatch):
    from src.engine.scalping.universal_trailing_replay import decode_quote
    from src.tests.test_main_all_scope_trailing import quote
    class Executor:
        def __init__(self): self.jobs=[]
        def submit(self, callback): self.jobs.append(callback)
        def drain(self):
            while self.jobs: self.jobs.pop(0)()
    executor = Executor()
    queue = logger_mod.BoundedObservationQueue(executor, max_items=32, max_bytes=128*1024)
    monkeypatch.setattr(logger_mod, '_TRAILING_OBSERVATION_SINK', queue.submit)
    saved=[]
    def emit(*args, **kwargs):
        saved.append(kwargs)
        return dict(structured_append_succeeded=len(saved) != 299)
    monkeypatch.setattr(logger_mod,'emit_pipeline_event',emit)
    raw = quote(1,'2026-10-08T09:00:01')
    for start in range(0,320,4):
        for seq in range(start+1,start+5):
            fields=dict(universal_trailing_quote=raw, event_sequence=seq, evaluation_at_epoch=raw['known_at'])
            result=logger_mod.enqueue_trailing_observation('Test','123456',7,fields)
            assert result == dict(status='queued',structured_append_succeeded=False)
            fields['event_sequence'] = -1
        assert logger_mod.enqueue_trailing_observation('Test','123456',7,fields)['status']=='unavailable'
        # Exhausting trailing's reservation never consumes Main-stop's slot.
        assert queue.submit(lambda:dict(structured_append_succeeded=True),observation_category='main_stop')['status']=='queued'
        assert not saved or len(saved)==start
        executor.drain()
    assert [r['fields']['event_sequence'] for r in saved]==list(range(1,321))
    assert all(decode_quote(r['fields']['universal_trailing_quote'])==raw for r in saved)
    text_fields=logger_mod._project_fields_for_text('scalp_trailing_input_transition', saved[-1]['fields'])
    assert 'universal_trailing_quote' not in text_fields
    assert text_fields['universal_trailing_quote_source_sha256']==raw['source_sha256']
    assert logger_mod._project_fields_for_compact_stream('scalp_trailing_input_transition', saved[-1]['fields'])==saved[-1]['fields']
    assert all(r['observed_at_epoch']==raw['known_at'] for r in saved)
    assert queue.close(timeout=0)
    stats=queue.snapshot()
    assert stats['append_failed']==1 and stats['pending_items']==stats['pending_bytes']==0
    assert stats['peak_items']==5 and stats['peak_bytes']<queue.max_bytes
    assert logger_mod.enqueue_trailing_observation('Test','123456',7,fields)['status']=='unavailable'
    monkeypatch.setattr(logger_mod,'_TRAILING_OBSERVATION_SINK',None)
    assert logger_mod.enqueue_trailing_observation('Test','123456',7,fields)['reason']=='trailing_observation_sink_missing'
