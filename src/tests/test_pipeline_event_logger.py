import json
from types import SimpleNamespace

from src.utils import pipeline_event_logger as logger_mod


def _reset_logger_state(monkeypatch):
    monkeypatch.setattr(logger_mod, "_PRODUCER_COMPACTOR", None)


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
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    payload = logger_mod.emit_pipeline_event(
        "HOLDING_PIPELINE",
        "테스트종목",
        "123456",
        "bad_entry_block_observed",
        record_id=77,
        fields={"reason": "time stop", "profit_rate": "+0.5"},
    )

    assert emitted_messages
    assert emitted_messages[0].startswith("[HOLDING_PIPELINE] 테스트종목(123456) stage=bad_entry_block_observed")
    assert "id=77" in emitted_messages[0]
    assert "reason=time|stop" in emitted_messages[0]

    out_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    assert out_path.exists()
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and rows[0]["schema_version"] == 3
    assert rows[0]["pipeline"] == "HOLDING_PIPELINE"
    assert rows[0]["record_id"] == 77
    assert rows[0]["fields"]["reason"] == "time stop"

    compact_path = tmp_path / "threshold_cycle" / f"threshold_events_{payload['emitted_date']}.jsonl"
    assert compact_path.exists()
    compact_rows = [json.loads(line) for line in compact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert compact_rows and compact_rows[0]["event_type"] == "threshold_cycle_event"
    assert compact_rows[0]["stage"] == "bad_entry_block_observed"


def test_emit_pipeline_event_suppresses_default_text_info_but_keeps_jsonl(monkeypatch, tmp_path):
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
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "blocked_strength_momentum",
        record_id=77,
        fields={"reason": "below_strength_base", "ai_score": "50"},
    )

    assert emitted_messages == []
    out_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and rows[0]["stage"] == "blocked_strength_momentum"
    assert rows[0]["text_payload"].startswith("[ENTRY_PIPELINE] 테스트종목(123456)")
    assert rows[0]["fields"]["reason"] == "below_strength_base"


def test_emit_pipeline_event_allowlist_keeps_operational_text_info(monkeypatch, tmp_path):
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
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

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
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "order_bundle_submitted",
        fields={"actual_order_submitted": "False", "simulated_order": "True"},
    )

    assert emitted_messages == []
    out_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows and rows[0]["stage"] == "order_bundle_submitted"
    assert rows[0]["fields"]["actual_order_submitted"] == "False"


def test_emit_pipeline_event_writes_reversal_add_gate_blocked_to_compact_stream(monkeypatch, tmp_path):
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

    compact_path = tmp_path / "threshold_cycle" / f"threshold_events_{payload['emitted_date']}.jsonl"
    compact_rows = [json.loads(line) for line in compact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
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

    compact_path = tmp_path / "threshold_cycle" / f"threshold_events_{payload['emitted_date']}.jsonl"
    compact_rows = [json.loads(line) for line in compact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert compact_rows and compact_rows[0]["stage"] == "new_threshold_probe"
    assert compact_rows[0]["family"] == "entry_new_probe"


def test_emit_pipeline_event_shadow_compaction_keeps_raw_and_writes_producer_summary(monkeypatch, tmp_path):
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

    raw_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(raw_rows) == 1
    assert raw_rows[0]["stage"] == "blocked_strength_momentum"
    summary_path = tmp_path / "pipeline_event_summaries" / f"pipeline_event_producer_summary_{payload['emitted_date']}.jsonl"
    summary_rows = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert summary_rows and summary_rows[0]["event_count"] == 1
    assert summary_rows[0]["reason_label"] == "blocked_strength_momentum:below_strength_base"
    manifest_path = tmp_path / "pipeline_event_summaries" / f"pipeline_event_producer_summary_manifest_{payload['emitted_date']}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["mode"] == "shadow"
    assert manifest["raw_suppression_enabled"] is False
    assert manifest["sample_per_bucket"] == 6


def test_emit_pipeline_event_default_compaction_is_shadow_report_only(monkeypatch, tmp_path):
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

    raw_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    summary_path = tmp_path / "pipeline_event_summaries" / f"pipeline_event_producer_summary_{payload['emitted_date']}.jsonl"
    manifest_path = tmp_path / "pipeline_event_summaries" / f"pipeline_event_producer_summary_manifest_{payload['emitted_date']}.json"
    raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert raw_rows and raw_rows[0]["stage"] == "blocked_overbought"
    assert summary_path.exists()
    assert manifest["mode"] == "shadow"
    assert manifest["runtime_effect"] is False
    assert manifest["raw_suppression_enabled"] is False


def test_emit_pipeline_event_suppress_mode_preserves_lossless_allowlist(monkeypatch, tmp_path):
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

    raw_path = tmp_path / "pipeline_events" / f"pipeline_events_{preserved['emitted_date']}.jsonl"
    raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["record_id"] for row in raw_rows] == [2]
    summary_path = tmp_path / "pipeline_event_summaries" / f"pipeline_event_producer_summary_{preserved['emitted_date']}.jsonl"
    summary_rows = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert sum(int(row["event_count"]) for row in summary_rows) == 2
    manifest_path = tmp_path / "pipeline_event_summaries" / f"pipeline_event_producer_summary_manifest_{preserved['emitted_date']}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["raw_suppression_enabled"] is True
    assert manifest["suppressed_count"] == 1
    assert manifest["lossless_preserved_count"] == 1


def test_emit_pipeline_event_compacts_submit_stage_threshold_stream(monkeypatch, tmp_path):
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
            **{f"extra_field_{idx}": str(idx) for idx in range(50)},
        },
    )

    raw_path = tmp_path / "pipeline_events" / f"pipeline_events_{payload['emitted_date']}.jsonl"
    raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert "extra_field_49" in raw_rows[0]["fields"]

    compact_path = tmp_path / "threshold_cycle" / f"threshold_events_{payload['emitted_date']}.jsonl"
    compact_rows = [json.loads(line) for line in compact_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    compact_fields = compact_rows[0]["fields"]
    assert compact_fields["field_projection"] == "submit_compact_v1"
    assert int(compact_fields["full_field_count"]) > len(compact_fields)
    assert int(compact_fields["omitted_field_count"]) > 0
    assert "extra_field_49" not in compact_fields


def test_emit_pipeline_event_keeps_id_in_submit_stage_text_payload(monkeypatch, tmp_path):
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
    monkeypatch.setattr(logger_mod, "log_info", lambda msg, send_telegram=False: emitted_messages.append(msg))

    payload = logger_mod.emit_pipeline_event(
        "ENTRY_PIPELINE",
        "테스트종목",
        "123456",
        "order_bundle_submitted",
        record_id=77,
        fields={**{f"extra_field_{idx}": str(idx) for idx in range(50)}, "actual_order_submitted": "True"},
    )

    assert "id=77" in payload["text_payload"]
