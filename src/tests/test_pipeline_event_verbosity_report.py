import gzip
import json
import pytest
from datetime import datetime

from src.engine import pipeline_event_verbosity_report as report_mod
from src.engine.pipeline_event_summary import ProducerSummaryCompactor


@pytest.mark.parametrize(
    "age,expected", [(121, "v2_shadow_pending_flush"), (661, "v2_shadow_flush_timeout")]
)
def test_flush_deadline_respects_supported_long_interval(
    monkeypatch, tmp_path, age, expected
):
    from datetime import timedelta

    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [
        _event(day, at, "scalping_scanner_fast_precheck", record_id=i)
        for i, at in enumerate(["10:00:00", "10:00:01"])
    ]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, rows[:1])
    path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{day}.json"
    )
    manifest = json.loads(path.read_text())
    manifest.update(flush_interval_sec=600, updated_at=f"{day}T10:00:00")
    path.write_text(json.dumps(manifest))
    result = report_mod.build_pipeline_event_verbosity_report(
        day, as_of=datetime(2026, 9, 8, 10, 0, 1) + timedelta(seconds=age)
    )
    assert result["state"] == expected
    assert result["parity"]["flush_allowance_sec"] == 660


@pytest.mark.parametrize("interval", [True, -1, 3601, "600", None])
def test_invalid_flush_interval_cannot_extend_deadline(monkeypatch, tmp_path, interval):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [_event(day, "10:00:00", "scalping_scanner_fast_precheck", record_id=1)]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, rows)
    path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{day}.json"
    )
    manifest = json.loads(path.read_text())
    manifest["flush_interval_sec"] = interval
    path.write_text(json.dumps(manifest))
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["state"] == "producer_manifest_invalid"
    assert result["parity"]["flush_deadline"] is None


def test_report_consumes_exact_completed_publish_timing_without_claiming_improvement(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [_event(day, "10:00:00", "scalping_scanner_fast_precheck", record_id=1)]
    _write_raw(tmp_path, day, rows)
    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path / "pipeline_event_summaries", mode="shadow", flush_sec=3600
    )
    compactor.submit(rows[0])
    compactor.flush()
    result = report_mod.build_pipeline_event_verbosity_report(day)
    timing = result["optimization"]["runtime_observation"]
    assert timing["status"] == "observed_no_comparable_baseline"
    assert timing["last_flush_duration_ms"] > 0
    assert timing["submit_sample_count"] == 1
    assert timing["submit_p99_ms"] >= 0
    assert timing["runtime_latency_improvement"] is None
    path = report_mod.producer_health_path(
        tmp_path / "pipeline_event_summaries", day, timing["writer_pid"]
    )
    health = json.loads(path.read_text())
    health["manifest_sha256"] = "wrong-generation"
    path.write_text(json.dumps(health))
    second = report_mod.build_pipeline_event_verbosity_report(day)
    assert (
        second["optimization"]["runtime_observation"]["status"] == "missing_or_unbound"
    )
    assert second["parity"]["ok"] is True


@pytest.mark.parametrize(
    "changed", ["stock_code", "record_id", "emitted_at", "session", "unprojected_field"]
)
def test_parity_rejects_equal_counts_with_wrong_identity(
    monkeypatch, tmp_path, changed
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    raw = _event(
        day,
        "10:00:00.123456",
        "scalping_scanner_fast_precheck",
        record_id=73,
        fields={"source_quality_gate": "pass"},
    )
    producer = json.loads(json.dumps(raw))
    if changed in {"session", "unprojected_field"}:
        producer["fields"][changed] = "wrong"
    else:
        producer[changed] = (
            f"{day}T10:00:00.234567" if changed == "emitted_at" else "999999"
        )
    _write_raw(tmp_path, day, [raw])
    _write_producer_summary(tmp_path, day, [producer])
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["parity"]["ok"] is False
    assert result["parity"]["identity_ok"] is False
    assert result["parity"]["suppress_eligibility"] is False


def test_completed_mismatch_takes_precedence_over_pending_tail(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [
        _event(day, at, "scalping_scanner_fast_precheck", record_id=i)
        for i, at in enumerate(["09:59:00", "09:59:01", "10:00:00", "10:05:00"])
    ]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, [rows[0], rows[2]])
    path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{day}.json"
    )
    manifest = json.loads(path.read_text())
    manifest["updated_at"] = f"{day}T10:00:30"
    path.write_text(json.dumps(manifest))
    result = report_mod.build_pipeline_event_verbosity_report(
        day, as_of=datetime(2026, 9, 8, 10, 5, 30)
    )
    assert result["parity"]["producer_pending_flush"] is True
    assert result["parity"]["completed_window_mismatch"] is True
    assert result["state"] == "v2_shadow_parity_fail"
    from src.engine.build_code_improvement_workorder import (
        _pipeline_event_verbosity_followup_orders,
    )

    orders = _pipeline_event_verbosity_followup_orders(result)
    assert len(orders) == 1
    assert orders[0]["allowed_runtime_apply"] is False


def test_expired_tail_creates_repair_workorder(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [
        _event(day, at, "scalping_scanner_fast_precheck", record_id=i)
        for i, at in enumerate(["10:00:00", "10:05:00"])
    ]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, rows[:1])
    path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{day}.json"
    )
    manifest = json.loads(path.read_text())
    manifest["updated_at"] = f"{day}T10:00:30"
    path.write_text(json.dumps(manifest))
    result = report_mod.build_pipeline_event_verbosity_report(
        day, as_of=datetime(2026, 9, 8, 10, 7, 1)
    )
    assert result["state"] == "v2_shadow_flush_timeout"
    from src.engine.build_code_improvement_workorder import (
        _pipeline_event_verbosity_followup_orders,
    )

    assert len(_pipeline_event_verbosity_followup_orders(result)) == 1


def test_lossless_only_has_no_suppression_waiting_queue(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [
        _event(
            day,
            "10:00:00.123456",
            "scalping_scanner_fast_precheck",
            record_id=73,
            fields={"source_quality_gate": "pass"},
        )
    ]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, rows)
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["state"] == "no_suppressible_events"
    assert result["raw_stream"]["potential_suppressible_bytes"] == 0
    assert result["parity"]["ok"] is True
    assert result["optimization"]["raw_reduction_bytes"] == 0
    assert result["optimization"]["runtime_latency_improvement"] is None


def test_legacy_counts_are_not_identity_approval(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [_event(day, "10:00:00", "scalping_scanner_fast_precheck", record_id=73)]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, rows)
    path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_{day}.jsonl"
    )
    row = json.loads(path.read_text())
    row.pop("identity_contract")
    row.pop("evidence_hash_sum")
    row["schema_version"] = 1
    path.write_text(json.dumps(row) + "\n")
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["state"] == "legacy_identity_evidence_missing"
    assert result["parity"]["ok"] is False


def test_report_rejects_manifest_count_mismatch(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [_event(day, "10:00:00", "scalping_scanner_fast_precheck", record_id=73)]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, rows)
    path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_manifest_{day}.json"
    )
    data = json.loads(path.read_text())
    data["summary_event_count"] = 2
    path.write_text(json.dumps(data))
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["state"] == "producer_manifest_invalid"
    assert result["parity"]["ok"] is False


@pytest.mark.parametrize(
    "state,reusable",
    [
        ("v2_shadow_pending_flush", False),
        ("source_snapshot_changed", False),
        ("no_suppressible_events", True),
        ("v2_shadow_flush_timeout", True),
    ],
)
def test_only_stable_exact_date_schema_can_be_reused(
    monkeypatch, tmp_path, state, reusable
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    path = report_mod.report_paths(day)[0]
    path.parent.mkdir(parents=True)
    payload = {
        "schema_version": 2,
        "report_type": "pipeline_event_verbosity",
        "target_date": day,
        "state": state,
        "policy": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "raw_suppression_enabled": False,
        },
    }
    path.write_text(json.dumps(payload))
    assert report_mod.report_is_reusable(day) is reusable
    payload["target_date"] = "2026-09-07"
    path.write_text(json.dumps(payload))
    assert report_mod.report_is_reusable(day) is False


def test_parity_supports_different_flush_partitions(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [
        _event(day, "10:00:00", "scalping_scanner_fast_precheck", record_id=i)
        for i in range(20)
    ]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, list(reversed(rows)))
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["parity"]["identity_ok"] is True
    assert result["parity"]["ok"] is True


@pytest.mark.parametrize("bad_line", ["not-json\n", "[]\n", '{"incomplete":'])
def test_invalid_raw_never_becomes_no_suppressible_success(
    monkeypatch, tmp_path, bad_line
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    _write_raw(tmp_path, day, [])
    path = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    path.write_text(bad_line)
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["state"] == "source_quality_blocked"
    assert result["parity"]["ok"] is False
    assert result["optimization"]["state"] != "no_suppressible_events"


def test_empty_raw_with_producer_evidence_is_not_valid_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    _write_raw(tmp_path, day, [])
    _write_producer_summary(
        tmp_path,
        day,
        [_event(day, "10:00:00", "scalping_scanner_fast_precheck", record_id=1)],
    )
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["parity"]["ok"] is False
    assert result["state"] != "v2_shadow_no_eligible_events"


def test_same_size_raw_rewrite_invalidates_parity_cache(monkeypatch, tmp_path):
    import os

    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [_event(day, "10:00:00", "scalping_scanner_fast_precheck", record_id=1)]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, rows)
    assert report_mod.build_pipeline_event_verbosity_report(day)["parity"]["ok"] is True
    path = tmp_path / "pipeline_events" / f"pipeline_events_{day}.jsonl"
    stat = path.stat()
    rows[0]["stock_code"] = "999999"
    _write_raw(tmp_path, day, rows)
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
    assert path.stat().st_size == stat.st_size
    assert (
        report_mod.build_pipeline_event_verbosity_report(day)["parity"]["ok"] is False
    )


def test_historical_suppress_workorder_cannot_reopen_raw_discard():
    from src.engine.build_code_improvement_workorder import (
        _pipeline_event_verbosity_followup_orders,
    )

    assert (
        _pipeline_event_verbosity_followup_orders(
            {
                "state": "suppress_candidate",
                "recommended_workorder_state": "open_suppress_guard_order",
            }
        )
        == []
    )


@pytest.mark.parametrize("corruption", ["malformed_json", "missing_new_digest"])
def test_corrupt_summary_is_not_silently_accepted(monkeypatch, tmp_path, corruption):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    day = "2026-09-08"
    rows = [_event(day, "10:00:00", "scalping_scanner_fast_precheck", record_id=1)]
    _write_raw(tmp_path, day, rows)
    _write_producer_summary(tmp_path, day, rows)
    path = (
        tmp_path
        / "pipeline_event_summaries"
        / f"pipeline_event_producer_summary_{day}.jsonl"
    )
    if corruption == "malformed_json":
        with path.open("a") as handle:
            handle.write("not-json\n")
    else:
        data = json.loads(path.read_text())
        data.pop("evidence_hash_sum")
        path.write_text(json.dumps(data) + "\n")
    result = report_mod.build_pipeline_event_verbosity_report(day)
    assert result["state"] == "producer_summary_invalid"
    assert result["parity"]["ok"] is False
    assert result["recommended_workorder_state"] == "repair_source_contract"


def _event(
    target_date: str,
    hhmmss: str,
    stage: str,
    *,
    record_id: int,
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": "000001",
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{target_date}T{hhmmss}",
        "emitted_date": target_date,
        "text_payload": "-",
    }


def _write_raw(tmp_path, target_date: str, rows: list[dict]) -> None:
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    with (raw_dir / f"pipeline_events_{target_date}.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_producer_summary(tmp_path, target_date: str, rows: list[dict]) -> None:
    compactor = ProducerSummaryCompactor(
        summary_dir=tmp_path / "pipeline_event_summaries",
        mode="shadow",
        flush_sec=0,
    )
    for row in rows:
        compactor.submit(row)
    compactor.flush(target_date=target_date)


def _gzip_replace(path) -> None:
    gz_path = path.with_name(path.name + ".gz")
    with path.open("rb") as source, gzip.open(gz_path, "wb") as target:
        target.write(source.read())
    path.unlink()


def test_pipeline_event_verbosity_report_detects_missing_shadow(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_raw(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "blocked_strength_momentum",
                record_id=1,
                fields={"reason": "below_strength_base"},
            )
        ],
    )

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "v2_shadow_missing"
    assert report["recommended_workorder_state"] == "open_shadow_order"
    assert report["raw_stream"]["high_volume_line_count"] == 1
    assert report["policy"]["runtime_effect"] is False


def test_pipeline_event_verbosity_report_does_not_require_shadow_without_eligible_events(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_raw(
        tmp_path,
        "2026-05-06",
        [
            _event(
                "2026-05-06",
                "10:00:00",
                "unrelated_low_volume_stage",
                record_id=1,
            )
        ],
    )

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "v2_shadow_no_eligible_events"
    assert report["recommended_workorder_state"] == "observe_no_eligible_events"
    assert report["parity"]["ok"] is True
    assert report["parity"]["no_eligible_events"] is True
    assert report["producer_summary"]["exists"] is False


def test_pipeline_event_verbosity_report_parity_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "2026-05-06",
            "10:00:00",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_strength_base"},
        ),
        _event(
            "2026-05-06",
            "10:00:01",
            "blocked_overbought",
            record_id=2,
            fields={"reason": "near_day_high"},
        ),
        _event(
            "2026-05-06",
            "10:00:02",
            "scalping_scanner_fast_precheck",
            record_id=3,
            fields={
                "fast_precheck_result": "defer",
                "fast_precheck_reason": "waiting_heavy_eval",
                "source_quality_gate": "pass",
            },
        ),
    ]
    _write_raw(tmp_path, "2026-05-06", rows)
    _write_producer_summary(tmp_path, "2026-05-06", rows)

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "no_suppressible_events"
    assert report["parity"]["ok"] is True
    assert report["parity"]["stage_diff"] == {}
    assert report["parity"]["blocker_diff"] == {}
    assert report["producer_summary"]["manifest_mode"] == "shadow"
    assert (
        report["producer_summary"]["stage_counts"]["scalping_scanner_fast_precheck"]
        == 1
    )


def test_pipeline_event_verbosity_report_parity_pass_with_gzip_sources(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    rows = [
        _event(
            "2026-05-06",
            "10:00:00",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_strength_base"},
        )
    ]
    _write_raw(tmp_path, "2026-05-06", rows)
    _write_producer_summary(tmp_path, "2026-05-06", rows)
    _gzip_replace(tmp_path / "pipeline_events" / "pipeline_events_2026-05-06.jsonl")
    _gzip_replace(
        tmp_path
        / "pipeline_event_summaries"
        / "pipeline_event_producer_summary_2026-05-06.jsonl"
    )

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "no_suppressible_events"
    assert report["producer_summary"]["exists"] is True
    assert report["producer_summary"]["path"].endswith(".jsonl.gz")
    assert (
        report["raw_stream"]["raw_storage_size_bytes"]
        == (tmp_path / "pipeline_events" / "pipeline_events_2026-05-06.jsonl.gz")
        .stat()
        .st_size
    )
    assert report["raw_stream"]["raw_size_bytes"] > 0
    assert report["raw_stream"]["high_volume_byte_share_pct"] <= 100.0


def test_pipeline_event_verbosity_raw_size_includes_non_json_lines(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    raw_dir = tmp_path / "pipeline_events"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "pipeline_events_2026-05-06.jsonl"
    event = _event(
        "2026-05-06",
        "10:00:00",
        "blocked_strength_momentum",
        record_id=1,
        fields={"reason": "below_strength_base"},
    )
    raw_path.write_text(
        "\n".join(
            [
                json.dumps(event, ensure_ascii=False),
                "",
                "not-json",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["raw_stream"]["raw_size_bytes"] == raw_path.stat().st_size
    assert report["raw_stream"]["raw_line_count"] == 2
    assert report["raw_stream"]["high_volume_line_count"] == 1


def test_pipeline_event_verbosity_report_parity_fail(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    raw_rows = [
        _event(
            "2026-05-06",
            "10:00:00",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_strength_base"},
        ),
        _event(
            "2026-05-06",
            "10:00:01",
            "blocked_strength_momentum",
            record_id=2,
            fields={"reason": "below_window_buy_value"},
        ),
    ]
    _write_raw(tmp_path, "2026-05-06", raw_rows)
    _write_producer_summary(tmp_path, "2026-05-06", raw_rows[:1])

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "v2_shadow_parity_fail"
    assert report["recommended_workorder_state"] == "block_suppress_and_fix_shadow"
    assert report["parity"]["ok"] is False
    assert "blocked_strength_momentum" in report["parity"]["stage_diff"]


def test_pipeline_event_verbosity_report_marks_pending_flush_when_raw_tail_is_newer(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    raw_rows = [
        _event(
            "2026-05-06",
            "10:00:00",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_strength_base"},
        ),
        _event(
            "2026-05-06",
            "10:05:00",
            "blocked_strength_momentum",
            record_id=2,
            fields={"reason": "below_window_buy_value"},
        ),
    ]
    _write_raw(tmp_path, "2026-05-06", raw_rows)
    _write_producer_summary(tmp_path, "2026-05-06", raw_rows[:1])
    manifest_path = (
        tmp_path
        / "pipeline_event_summaries"
        / "pipeline_event_producer_summary_manifest_2026-05-06.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["updated_at"] = "2026-05-06T10:00:30"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = report_mod.build_pipeline_event_verbosity_report(
        "2026-05-06", as_of=datetime(2026, 5, 6, 10, 5, 30)
    )

    assert report["state"] == "v2_shadow_pending_flush"
    assert report["recommended_workorder_state"] == "observe_pending_next_flush"
    assert report["parity"]["producer_pending_flush"] is True


def test_pipeline_event_verbosity_compares_only_completed_common_minutes(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    shared_row = _event(
        "2026-05-06",
        "09:59:30",
        "blocked_strength_momentum",
        record_id=1,
        fields={"reason": "below_strength_base"},
    )
    producer_current_minute = _event(
        "2026-05-06",
        "10:00:10",
        "blocked_strength_momentum",
        record_id=2,
        fields={"reason": "below_strength_base"},
    )
    raw_tail = _event(
        "2026-05-06",
        "10:05:00",
        "blocked_strength_momentum",
        record_id=3,
        fields={"reason": "below_window_buy_value"},
    )
    _write_raw(tmp_path, "2026-05-06", [shared_row, producer_current_minute, raw_tail])
    _write_producer_summary(
        tmp_path, "2026-05-06", [shared_row, producer_current_minute]
    )
    manifest_path = (
        tmp_path
        / "pipeline_event_summaries"
        / "pipeline_event_producer_summary_manifest_2026-05-06.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["updated_at"] = "2026-05-06T10:00:20"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = report_mod.build_pipeline_event_verbosity_report(
        "2026-05-06", as_of=datetime(2026, 5, 6, 10, 5, 30)
    )

    assert report["state"] == "v2_shadow_pending_flush"
    assert report["parity"]["ok"] is False
    assert report["parity"]["common_watermark_ok"] is True
    assert report["parity"]["comparison_watermark"] == "2026-05-06T10:00:00+09:00"
    assert report["parity"]["comparison_raw_derived_event_count"] == 1
    assert report["parity"]["comparison_producer_event_count"] == 1
    assert report["parity"]["raw_tail_excluded_event_count"] == 2


def test_pipeline_event_verbosity_report_separates_partial_day_coverage(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    raw_rows = [
        _event(
            "2026-05-06",
            "09:00:00",
            "blocked_strength_momentum",
            record_id=1,
            fields={"reason": "below_strength_base"},
        ),
        _event(
            "2026-05-06",
            "10:00:00",
            "blocked_strength_momentum",
            record_id=2,
            fields={"reason": "below_window_buy_value"},
        ),
    ]
    _write_raw(tmp_path, "2026-05-06", raw_rows)
    _write_producer_summary(tmp_path, "2026-05-06", raw_rows[1:])

    report = report_mod.build_pipeline_event_verbosity_report("2026-05-06")

    assert report["state"] == "v2_shadow_partial_coverage"
    assert report["recommended_workorder_state"] == "repair_source_contract"
    assert report["parity"]["producer_start_complete"] is False
    assert report["parity"]["producer_pending_flush"] is False
    assert report["parity"]["suppress_eligibility"] is False
