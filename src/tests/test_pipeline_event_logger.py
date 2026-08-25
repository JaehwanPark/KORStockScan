import gzip
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.utils import pipeline_event_logger as logger_mod


def _reset_logger_state(monkeypatch):
    monkeypatch.setattr(logger_mod, "_PRODUCER_COMPACTOR", None)


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
    assert manifest["coverage_first_event_at"] == payload["emitted_at"][:19]
    assert manifest["coverage_last_event_at"] == payload["emitted_at"][:19]


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
    assert summary_rows[0]["sample_raw_offsets"] == [1, 4]
    assert (
        summary_rows[0]["sample_events"][0]["fields"]["summary_field_projection"]
        == "high_volume_diagnostic_v1"
    )
    assert "fast_precheck_result" in summary_rows[0]["field_presence_counts"]
    assert "source_quality_gate" in summary_rows[0]["field_presence_counts"]

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
        "blocked_overbought",
        record_id=1,
        fields={"reason": "near_day_high"},
    )
    preserved = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "blocked_overbought",
        record_id=2,
        fields={"reason": "near_day_high", "actual_order_submitted": "true"},
    )
    logger_mod.flush_pipeline_event_producer_summary(preserved["emitted_date"])

    assert suppressed["structured_append_succeeded"] is False
    assert suppressed["structured_raw_append_attempted"] is False
    assert suppressed["structured_compaction_suppressed"] is True
    assert suppressed["structured_append_status"] == "raw_suppressed_by_compaction"
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
    assert [row["record_id"] for row in raw_rows] == [2]
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
    assert manifest["raw_suppression_enabled"] is True
    assert manifest["suppressed_count"] == 1
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
    assert manifest["raw_suppression_enabled"] is True
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
    assert compact_fields["field_projection"] == "submit_compact_v1"
    assert int(compact_fields["full_field_count"]) > len(compact_fields)
    assert int(compact_fields["omitted_field_count"]) > 0
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
    assert "extra_field_49" not in compact_fields


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
