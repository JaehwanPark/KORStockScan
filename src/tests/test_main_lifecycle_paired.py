from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from src.engine.scalping import main_lifecycle_journal as journal
from src.engine.scalping import main_lifecycle_paired as paired
from src.engine.scalping.main_lifecycle_journal import (
    append_transition_safe,
    build_transition,
    journal_path,
    mint_main_lifecycle_id,
    pipeline_lifecycle_fields_safe,
    start_scanner_attempt_safe,
    transition_content_sha256,
)
from src.engine.scalping.main_lifecycle_paired import (
    build_daily_report,
    main,
    pipeline_event_path,
    report_path,
)

TARGET_DATE = "2026-08-14"
KST = timezone(timedelta(hours=9))
BASE = datetime(2026, 8, 14, 9, 0, tzinfo=KST)
COST_HASH = "a" * 64
SYMBOL_HASH = "b" * 64


def _identity(attempt_id: str, *, record_id: str = "record-1") -> dict[str, str]:
    stock_code = "005930"
    return {
        "main_lifecycle_id": mint_main_lifecycle_id(
            record_id=record_id,
            stock_code=stock_code,
            attempt_id=attempt_id,
        ),
        "record_id": record_id,
        "stock_code": stock_code,
        "attempt_id": attempt_id,
    }


def _event(
    identity: dict[str, str],
    stage: str,
    second: int,
    *,
    data: dict[str, Any] | None = None,
    depth_observed: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "decision_trace_id": f"trace-{identity['attempt_id']}-{stage}-{second}",
        "bbo_observed": True,
        "depth_observed": depth_observed,
        "cost_artifact_sha256": COST_HASH,
        "cost_artifact_verified": True,
        "symbol_master_sha256": SYMBOL_HASH,
        "symbol_master_verified": True,
    }
    payload.update(data or {})
    return build_transition(
        **identity,
        trade_date=TARGET_DATE,
        stage=stage,
        observed_at=BASE + timedelta(seconds=second),
        venue="KRX",
        session_bucket="regular",
        data=payload,
    )


def _complete_lifecycle(
    attempt_id: str,
    *,
    fill_states: tuple[tuple[str, float], ...] = (("full", 5.0),),
    include_scale: bool = True,
    scale_decision: str = "NO_ADD",
    exit_second: int = 63,
    low_depth_stage: str | None = None,
    label_horizon_sec: int | None = None,
) -> list[dict[str, Any]]:
    identity = _identity(attempt_id, record_id=f"record-{attempt_id}")
    rows = [
        _event(
            identity,
            "scanner",
            0,
            data={
                "session_exposure_start_at": BASE.isoformat(),
                "session_exposure_end_at": (BASE + timedelta(minutes=10)).isoformat(),
            },
            depth_observed=low_depth_stage != "scanner",
        ),
        _event(
            identity,
            "entry_decision",
            1,
            data={"action": "BUY"},
            depth_observed=low_depth_stage != "entry_decision",
        ),
        _event(
            identity,
            "submit",
            2,
            data={
                "requested_qty": sum(quantity for _, quantity in fill_states),
                "actual_broker_order_submitted": True,
                "broker_order_no": f"broker-{attempt_id}",
            },
            depth_observed=low_depth_stage != "submit",
        ),
    ]
    fill_second = 3
    for fill_state, quantity in fill_states:
        fill_data: dict[str, Any] = {
            "fill_state": fill_state,
            "fill_qty": quantity,
            "fill_price": 10_000,
        }
        if label_horizon_sec is not None:
            fill_data["label_horizon_sec"] = label_horizon_sec
        rows.append(
            _event(
                identity,
                "fill",
                fill_second,
                data=fill_data,
                depth_observed=low_depth_stage != "fill",
            )
        )
        fill_second += 1
    rows.append(
        _event(
            identity,
            "holding",
            fill_second,
            data={"action": "HOLD"},
            depth_observed=low_depth_stage != "holding",
        )
    )
    if include_scale:
        rows.append(
            _event(
                identity,
                "scale_in",
                fill_second + 1,
                data={"scale_in_decision": scale_decision},
                depth_observed=low_depth_stage != "scale_in",
            )
        )
    rows.append(
        _event(
            identity,
            "exit",
            exit_second,
            data={
                "exit_qty": sum(quantity for _, quantity in fill_states),
                "exit_price": 10_010,
                "broker_reconciled": True,
                "reconciled_final_exit": True,
                "fees_taxes_krw": 20,
                "slippage_krw": 5,
                "slippage_basis_price": 10_011,
                "slippage_basis_source": "test_exit_decision_price",
                "realized_net_pnl_krw": 25,
            },
            depth_observed=low_depth_stage != "exit",
        )
    )
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _pipeline_event(
    *,
    stock: dict[str, Any],
    pipeline: str,
    source_stage: str,
    second: int,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_fields = dict(fields or {})
    if source_stage == "position_rebased_after_fill":
        source_fields.setdefault("receipt_economics_complete", True)
        source_fields.setdefault("receipt_quantity_contract_complete", True)
        source_fields.setdefault("receipt_unit_fill_consistent", True)
    elif source_stage == "scale_in_executed":
        source_fields.setdefault("receipt_economics_complete", True)
        source_fields.setdefault("receipt_quantity_contract_complete", True)
        source_fields.setdefault("receipt_unit_fill_consistent", True)
    elif source_stage in {
        "sell_partial_fill_progress",
        "nxt_rising_missed_tp1_partial_fill_progress",
        "nxt_rising_missed_tp1_partial_sell_completed",
        "sell_completed",
    }:
        source_fields.setdefault("sell_execution_receipt_economics_complete", True)
        source_fields.setdefault(
            "sell_execution_receipt_quantity_contract_complete", True
        )
        source_fields.setdefault("sell_execution_receipt_unit_fill_consistent", True)
    if source_stage in {
        "position_rebased_after_fill",
        "scale_in_executed",
        "sell_partial_fill_progress",
        "nxt_rising_missed_tp1_partial_fill_progress",
        "nxt_rising_missed_tp1_partial_sell_completed",
        "sell_completed",
    }:
        source_fields.setdefault("broker_execution_provenance_complete", True)
        source_fields.setdefault("broker_execution_time_source", "official_fid_908")
        source_fields.setdefault("broker_execution_time_raw", "090003")
        source_fields.setdefault("broker_actual_execution_venue", "KRX")
        source_fields.setdefault("broker_sor_flag", "N")
        source_fields.setdefault("execution_no", f"EXEC-{second}")
    lifecycle_fields = pipeline_lifecycle_fields_safe(
        stock,
        stock["code"],
        pipeline=pipeline,
        source_stage=source_stage,
        source_fields=source_fields,
        observed_at=BASE + timedelta(seconds=second),
    )
    source_fields.update(lifecycle_fields)
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": source_stage,
        "stock_name": stock.get("name", "TEST"),
        "stock_code": stock["code"],
        "record_id": stock["id"],
        "fields": {key: str(value) for key, value in source_fields.items()},
        # The lifecycle converter must not use these legacy naive timestamps.
        "emitted_at": "2099-01-01T00:00:00",
        "emitted_date": "2099-01-01",
    }


def _without_reference_hashes(row: dict[str, Any]) -> dict[str, Any]:
    data = dict(row["data"])
    for key in (
        "cost_artifact_sha256",
        "cost_artifact_verified",
        "symbol_master_sha256",
        "symbol_master_verified",
    ):
        data.pop(key, None)
    return build_transition(
        main_lifecycle_id=row["main_lifecycle_id"],
        record_id=row["record_id"],
        stock_code=row["stock_code"],
        attempt_id=row["attempt_id"],
        trade_date=row["trade_date"],
        stage=row["stage"],
        observed_at=row["observed_at"],
        venue=row["venue"],
        session_bucket=row["session_bucket"],
        data=data,
    )


def _with_reference_hashes(
    row: dict[str, Any], *, cost_hash: str, symbol_hash: str
) -> dict[str, Any]:
    data = dict(row["data"])
    data.update(
        {
            "cost_artifact_sha256": cost_hash,
            "cost_artifact_verified": True,
            "symbol_master_sha256": symbol_hash,
            "symbol_master_verified": True,
        }
    )
    return build_transition(
        main_lifecycle_id=row["main_lifecycle_id"],
        record_id=row["record_id"],
        stock_code=row["stock_code"],
        attempt_id=row["attempt_id"],
        trade_date=row["trade_date"],
        stage=row["stage"],
        observed_at=row["observed_at"],
        venue=row["venue"],
        session_bucket=row["session_bucket"],
        data=data,
    )


def _by_attempt(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["attempt_id"]: row for row in report["rows"]}


def test_cross_attempt_transition_is_rejected_without_join(tmp_path: Path) -> None:
    first = _identity("attempt-a", record_id="record-a")
    second = _identity("attempt-b", record_id="record-b")
    rows = [_event(first, "scanner", 0), _event(second, "scanner", 1)]
    cross_attempt = _event(
        second,
        "fill",
        2,
        data={"fill_state": "full", "fill_qty": 99, "fill_price": 1},
    )
    cross_attempt["main_lifecycle_id"] = first["main_lifecycle_id"]
    digest = transition_content_sha256(cross_attempt)
    cross_attempt["event_id"] = f"mle-{digest[:32]}"
    cross_attempt["transition_content_sha256"] = digest
    rows.append(cross_attempt)
    source = tmp_path / "journal.jsonl"
    _write_jsonl(source, rows)

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["source_invalid_transition_count"] == 1
    assert report["global_source_quality_gate_pass"] is False
    assert len(report["rows"]) == 2
    assert all(row["stage_counts"] == {"scanner": 1} for row in report["rows"])
    assert all(row["promotion_evidence_eligible"] is False for row in report["rows"])


def test_journal_submit_requires_explicit_real_broker_evidence() -> None:
    identity = _identity("submit-authority")

    with pytest.raises(ValueError, match="submit_actual_broker_order_required"):
        _event(identity, "submit", 2, data={"requested_qty": 5})


def test_duplicate_transition_is_gap_and_never_double_counted(
    tmp_path: Path,
) -> None:
    rows = _complete_lifecycle("duplicate")
    fill = next(row for row in rows if row["stage"] == "fill")
    rows.insert(rows.index(fill) + 1, dict(fill))
    source = tmp_path / "journal.jsonl"
    _write_jsonl(source, rows)

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)
    row = report["rows"][0]

    assert row["entry_fill_qty"] == pytest.approx(5)
    assert row["invalid_transition_count"] == 1
    assert "duplicate_transition_event" in row["invalid_transition_reasons"]
    assert report["promotion_ready"] is False


def test_transition_identity_content_conflict_is_source_gap(tmp_path: Path) -> None:
    rows = _complete_lifecycle("event-content-conflict")
    conflict = dict(rows[0])
    conflict["data"] = {**conflict["data"], "reason": "tampered"}
    rows.insert(1, conflict)
    source = tmp_path / "journal.jsonl"
    _write_jsonl(source, rows)

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["source_invalid_transition_count"] == 1
    assert report["promotion_ready"] is False
    assert any(
        example["reason"] == "transition_content_or_lineage_mismatch"
        for example in report["instrumentation_gap_examples"]
    )


def test_entry_phase_cannot_regress_after_holding(tmp_path: Path) -> None:
    attempt_id = "phase-regression"
    identity = _identity(attempt_id, record_id=f"record-{attempt_id}")
    rows = _complete_lifecycle(attempt_id)
    holding_index = next(
        index for index, row in enumerate(rows) if row["stage"] == "holding"
    )
    rows[holding_index + 1 : holding_index + 1] = [
        _event(
            identity,
            "submit",
            4.25,
            data={
                "requested_qty": 5,
                "actual_broker_order_submitted": True,
                "broker_order_no": "late-submit",
            },
        ),
        _event(identity, "scanner", 4.5),
    ]
    source = tmp_path / "journal.jsonl"
    _write_jsonl(source, rows)

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)
    row = report["rows"][0]

    assert "submit_after_fill_phase" in row["invalid_transition_reasons"]
    assert "scanner_after_entry_phase" in row["invalid_transition_reasons"]
    assert report["promotion_ready"] is False


def test_pipeline_and_journal_rows_never_complete_each_other(
    tmp_path: Path,
) -> None:
    stock = {
        "id": 706,
        "name": "TEST",
        "code": "005930",
        "scanner_generation_id": "005930:SCANPROM-706:r1",
        "effective_venue": "KRX",
        "market_session_bucket": "regular",
    }
    identity = _identity(stock["scanner_generation_id"], record_id="706")
    journal_tail = _complete_lifecycle(stock["scanner_generation_id"])[1:]
    journal_tail = [
        build_transition(
            main_lifecycle_id=identity["main_lifecycle_id"],
            record_id=identity["record_id"],
            stock_code=identity["stock_code"],
            attempt_id=identity["attempt_id"],
            trade_date=row["trade_date"],
            stage=row["stage"],
            observed_at=row["observed_at"],
            venue="KRX",
            session_bucket="regular",
            data=row["data"],
        )
        for row in journal_tail
    ]
    source = tmp_path / "mixed.jsonl"
    _write_jsonl(
        source,
        [
            _pipeline_event(
                stock=stock,
                pipeline="ENTRY_PIPELINE",
                source_stage="scalping_scanner_fast_precheck",
                second=0,
                fields={"bbo_observed": True, "depth_observed": True},
            ),
            *journal_tail,
        ],
    )

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["source_kind"] == "mixed_pipeline_and_transition_journal"
    assert report["mixed_source_row_count"] == len(journal_tail)
    assert report["rows"][0]["stage_counts"] == {"scanner": 1}
    assert "mixed_transition_source_kinds_forbidden" in report[
        "global_source_quality_gate_blockers"
    ]
    assert report["promotion_ready"] is False


def test_no_add_is_distinct_from_missing_scale_in(tmp_path: Path) -> None:
    source = tmp_path / "journal.jsonl"
    _write_jsonl(
        source,
        [
            *_complete_lifecycle("explicit-no-add"),
            *_complete_lifecycle("missing", include_scale=False),
        ],
    )

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)
    rows = _by_attempt(report)

    assert rows["explicit-no-add"]["scale_in_decisions"] == ["NO_ADD"]
    assert rows["explicit-no-add"]["scale_in_contract_state"] == "explicit"
    assert rows["explicit-no-add"]["row_source_quality_gate_pass"] is True
    assert rows["explicit-no-add"]["promotion_evidence_eligible"] is False
    assert rows["missing"]["scale_in_decisions"] == []
    assert rows["missing"]["scale_in_contract_state"] == "missing"
    assert "scale_in_decision_missing" in rows["missing"]["promotion_blockers"]
    assert rows["missing"]["promotion_evidence_eligible"] is False
    assert report["promotion_ready"] is False


def test_partial_and_full_fill_cohorts_are_not_merged(tmp_path: Path) -> None:
    source = tmp_path / "journal.jsonl"
    _write_jsonl(
        source,
        [
            *_complete_lifecycle(
                "partial-then-full",
                fill_states=(("partial", 2.0), ("full", 3.0)),
            ),
            *_complete_lifecycle(
                "partial-only",
                fill_states=(("partial", 5.0),),
            ),
        ],
    )

    rows = _by_attempt(build_daily_report(TARGET_DATE, source_path=source, write=False))

    assert rows["partial-then-full"]["fill_completion_class"] == "partial_then_full"
    assert rows["partial-then-full"]["partial_fill_event_count"] == 1
    assert rows["partial-then-full"]["full_fill_event_count"] == 1
    assert rows["partial-only"]["fill_completion_class"] == "partial_only"
    assert rows["partial-only"]["partial_fill_event_count"] == 1
    assert rows["partial-only"]["full_fill_event_count"] == 0
    assert rows["partial-only"]["terminal_state"] == "FINAL_EXIT_RECONCILED"


def test_one_exposure_sample_has_null_duration_and_rate(tmp_path: Path) -> None:
    identity = _identity("one-sample")
    source = tmp_path / "journal.jsonl"
    _write_jsonl(source, [_event(identity, "scanner", 0)])

    row = build_daily_report(TARGET_DATE, source_path=source, write=False)["rows"][0]

    assert row["session_exposure_sec"] is None
    assert row["lifecycle_rate_per_exposure_hour"] is None


def test_repeated_scanner_rows_are_not_implicit_exposure_heartbeats(
    tmp_path: Path,
) -> None:
    identity = _identity("scanner-not-heartbeat")
    source = tmp_path / "journal.jsonl"
    _write_jsonl(
        source,
        [
            _event(identity, "scanner", 0),
            _event(identity, "scanner", 30),
        ],
    )

    row = build_daily_report(TARGET_DATE, source_path=source, write=False)["rows"][0]

    assert row["session_exposure_sec"] is None
    assert row["lifecycle_rate_per_exposure_hour"] is None


def test_actual_duration_uses_fill_and_exit_not_label_horizon(tmp_path: Path) -> None:
    source = tmp_path / "journal.jsonl"
    rows = _complete_lifecycle(
        "actual-duration",
        exit_second=93,
        label_horizon_sec=3_600,
    )
    _write_jsonl(source, rows)

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)
    row = report["rows"][0]

    assert all("label_horizon_sec" not in event["data"] for event in rows)
    assert row["actual_holding_duration_sec"] == pytest.approx(90.0)
    assert row["duration_source"] == "actual_first_fill_to_reconciled_final_exit"
    assert row["label_horizon_used"] is False
    assert row["capital_time_krw_hours"] > 0


def test_any_promotion_gate_failure_yields_no_promotion_ready(tmp_path: Path) -> None:
    source = tmp_path / "journal.jsonl"
    _write_jsonl(
        source,
        _complete_lifecycle("depth-gap", low_depth_stage="holding"),
    )

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)
    row = report["rows"][0]

    assert row["depth_coverage_pct"] < 90.0
    assert "depth_coverage_below_90pct" in row["promotion_blockers"]
    assert row["promotion_evidence_eligible"] is False
    assert report["promotion_ready"] is False
    assert report["promotion_ready_lifecycle_ids"] == []


def test_slippage_basis_must_cover_every_executed_exit_share(
    tmp_path: Path,
) -> None:
    rows = _complete_lifecycle("missing-slippage-basis")
    final = rows[-1]
    final_data = dict(final["data"])
    final_data.pop("slippage_basis_price")
    final_data.pop("slippage_basis_source")
    rows[-1] = build_transition(
        main_lifecycle_id=final["main_lifecycle_id"],
        record_id=final["record_id"],
        stock_code=final["stock_code"],
        attempt_id=final["attempt_id"],
        trade_date=final["trade_date"],
        stage=final["stage"],
        observed_at=final["observed_at"],
        venue=final["venue"],
        session_bucket=final["session_bucket"],
        data=final_data,
    )
    source = tmp_path / "journal.jsonl"
    _write_jsonl(source, rows)

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)
    row = report["rows"][0]

    assert "slippage_basis_exit_qty_coverage_incomplete" in row[
        "promotion_blockers"
    ]
    assert report["promotion_ready"] is False


def test_raw_fallback_without_explicit_id_is_instrumentation_gap_only(
    tmp_path: Path,
) -> None:
    source = tmp_path / "journal.jsonl"
    fallback = tmp_path / "raw.jsonl"
    _write_jsonl(source, _complete_lifecycle("fallback-gap"))
    _write_jsonl(fallback, [{"stock_code": "005930", "decision": "BUY"}])

    report = build_daily_report(
        TARGET_DATE,
        source_path=source,
        raw_fallback_path=fallback,
        write=False,
    )

    assert report["raw_fallback_census"]["missing_main_lifecycle_id_count"] == 1
    assert report["raw_fallback_census"]["join_policy"] == "never_join_raw_fallback"
    assert report["instrumentation_gap_count"] == 1
    assert report["promotion_ready"] is False
    assert report["rows"][0]["promotion_evidence_eligible"] is False


def test_terminal_no_fill_and_held_are_separate_right_censor_states(
    tmp_path: Path,
) -> None:
    no_fill = _identity("no-fill", record_id="record-no-fill")
    held_rows = _complete_lifecycle("held")[:-1]
    source = tmp_path / "journal.jsonl"
    _write_jsonl(
        source,
        [
            _event(no_fill, "scanner", 0),
            _event(
                no_fill,
                "entry_decision",
                1,
                data={"terminal_no_fill": True, "terminal_reason": "WAIT"},
            ),
            *held_rows,
        ],
    )

    rows = _by_attempt(build_daily_report(TARGET_DATE, source_path=source, write=False))

    assert rows["no-fill"]["terminal_state"] == "TERMINAL_NO_FILL"
    assert rows["no-fill"]["right_censored"] is False
    assert rows["held"]["terminal_state"] == "HELD"
    assert rows["held"]["right_censored"] is True
    assert rows["held"]["actual_holding_duration_sec"] is None


def test_streaming_scan_keeps_no_transition_buffer(tmp_path: Path) -> None:
    identity = _identity("streaming")
    source = tmp_path / "journal.jsonl"
    with source.open("w", encoding="utf-8") as handle:
        for second in range(3_000):
            row = _event(
                identity,
                "scanner",
                second,
                data={"heartbeat": True},
            )
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["source_raw_census"]["json_object_count"] == 3_000
    assert report["rows"][0]["transition_count"] == 3_000
    assert report["rows"][0]["session_exposure_sec"] == pytest.approx(2_999.0)
    assert report["streaming_memory_contract"]["source_scan_count"] == 1
    assert report["streaming_memory_contract"]["source_rows_retained"] == 0
    assert report["streaming_memory_contract"]["transition_buffers_retained"] == 0


def test_unique_lifecycle_cardinality_is_bounded_and_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(paired, "MAX_LIFECYCLE_ACCUMULATORS", 2)
    source = tmp_path / "journal.jsonl"
    _write_jsonl(
        source,
        [
            _event(_identity(f"bounded-{index}"), "scanner", index)
            for index in range(3)
        ],
    )

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["lifecycle_count"] == 2
    assert report["lifecycle_accumulator_overflow_row_count"] == 1
    assert report["streaming_memory_contract"]["accumulator_limit"] == 2
    assert "lifecycle_accumulator_limit_exceeded" in report[
        "global_source_quality_gate_blockers"
    ]
    assert report["promotion_ready"] is False


def test_transition_identity_cardinality_is_globally_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(paired, "MAX_TRANSITION_EVENT_IDENTITIES", 2)
    identity = _identity("event-bound")
    source = tmp_path / "journal.jsonl"
    _write_jsonl(
        source,
        [_event(identity, "scanner", second) for second in range(3)],
    )

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)
    row = report["rows"][0]

    assert row["transition_count"] == 2
    assert report["transition_event_identity_overflow_row_count"] == 1
    assert report["streaming_memory_contract"][
        "retained_transition_event_identity_count"
    ] == 2
    assert "global_transition_event_identity_limit_exceeded" in row[
        "invalid_transition_reasons"
    ]
    assert "global_transition_event_identity_limit_exceeded" in report[
        "global_source_quality_gate_blockers"
    ]
    assert report["promotion_ready"] is False


def test_gzip_raw_hash_atomic_output_and_cli_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "journal.jsonl.gz"
    with gzip.open(source, "wt", encoding="utf-8") as handle:
        for row in _complete_lifecycle("gzip"):
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    expected_raw_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "report.json"

    exit_code = main(
        [
            "--date",
            TARGET_DATE,
            "--journal",
            str(source),
            "--output",
            str(output),
            "--write",
        ]
    )

    assert exit_code == 0
    cli_result = json.loads(capsys.readouterr().out)
    assert cli_result["schema"] == "main_scalping_lifecycle_paired_cli_result_v1"
    assert cli_result["output_path"] == str(output)
    assert "rows" not in cli_result
    stored = json.loads(output.read_text(encoding="utf-8"))
    assert stored["source_raw_sha256"] == expected_raw_hash
    assert stored["source_raw_census"]["source_is_gzip"] is True
    assert stored["content_sha256"] == stored["report_content_sha256"]
    unhashed = {
        key: value
        for key, value in stored.items()
        if key
        not in {
            "artifact_content_sha256",
            "content_sha256",
            "report_content_sha256",
        }
    }
    expected_content_hash = hashlib.sha256(
        json.dumps(
            unhashed,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    assert stored["content_sha256"] == expected_content_hash
    artifact_unhashed = {
        key: value for key, value in stored.items() if key != "artifact_content_sha256"
    }
    expected_artifact_hash = hashlib.sha256(
        json.dumps(
            artifact_unhashed,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    assert stored["artifact_content_sha256"] == expected_artifact_hash
    assert report_path(TARGET_DATE).name == (
        "main_scalping_lifecycle_paired_2026-08-14.json"
    )
    assert journal_path(TARGET_DATE).name == "main_lifecycle_journal_2026-08-14.jsonl"


def test_postclose_reference_hashes_bind_rows_without_live_hash_fields(
    tmp_path: Path,
) -> None:
    source = tmp_path / "journal.jsonl"
    _write_jsonl(
        source,
        [_without_reference_hashes(row) for row in _complete_lifecycle("references")],
    )

    report = build_daily_report(
        TARGET_DATE,
        source_path=source,
        reviewed_cost_profile_sha256=COST_HASH,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256=SYMBOL_HASH,
        symbol_master_artifact_verified=True,
        write=False,
    )
    row = report["rows"][0]

    assert row["reviewed_cost_profile_sha256"] == COST_HASH
    assert row["symbol_master_artifact_sha256"] == SYMBOL_HASH
    assert row["promotion_evidence_eligible"] is True
    assert report["promotion_ready"] is True


def test_corrupt_gzip_materializes_blocked_census_instead_of_raising(
    tmp_path: Path,
) -> None:
    source = tmp_path / "journal.jsonl.gz"
    raw = b"not-a-gzip-stream\n"
    source.write_bytes(raw)

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["source_raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert report["source_raw_census"]["source_read_error"] == "BadGzipFile"
    assert (
        "transition_journal_read_error" in report["global_source_quality_gate_blockers"]
    )
    assert report["promotion_ready"] is False


def test_journal_public_write_api_is_fail_open(tmp_path: Path) -> None:
    assert (
        append_transition_safe(
            main_lifecycle_id="invalid",
            record_id="record",
            stock_code="005930",
            attempt_id="attempt",
            trade_date=TARGET_DATE,
            stage="scanner",
            output_path=tmp_path / "journal.jsonl",
        )
        is False
    )
    assert (
        start_scanner_attempt_safe(
            record_id="record",
            stock_code="bad",
            attempt_id="attempt",
            trade_date=TARGET_DATE,
            output_path=tmp_path / "journal.jsonl",
        )
        is None
    )


def test_scanner_identity_survives_telemetry_write_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_write(*args: Any, **kwargs: Any) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr(journal, "_append_jsonl", fail_write)

    context = start_scanner_attempt_safe(
        record_id="record-write-failure",
        stock_code="005930",
        attempt_id="attempt-write-failure",
        trade_date=TARGET_DATE,
        observed_at=BASE,
    )

    assert context is not None
    assert context["main_lifecycle_id"] == mint_main_lifecycle_id(
        record_id="record-write-failure",
        stock_code="005930",
        attempt_id="attempt-write-failure",
    )


def test_cross_lifecycle_reference_hash_conflict_blocks_daily_promotion(
    tmp_path: Path,
) -> None:
    first = _complete_lifecycle("reference-a")
    second = [
        _with_reference_hashes(row, cost_hash="c" * 64, symbol_hash="d" * 64)
        for row in _complete_lifecycle("reference-b")
    ]
    source = tmp_path / "journal.jsonl"
    _write_jsonl(source, [*first, *second])

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["reviewed_cost_profile_sha256"] is None
    assert report["symbol_master_artifact_sha256"] is None
    assert report["promotion_ready"] is False
    assert report["promotion_evidence_eligible_count"] == 0
    assert (
        "reviewed_cost_profile_hash_conflict_across_lifecycles"
        in report["global_source_quality_gate_blockers"]
    )
    assert (
        "symbol_master_artifact_hash_conflict_across_lifecycles"
        in report["global_source_quality_gate_blockers"]
    )
    assert all(
        "daily_source_quality_gate_failed" in row["promotion_blockers"]
        for row in report["rows"]
    )


def test_pipeline_source_materializes_only_strict_explicit_identity_rows(
    tmp_path: Path,
) -> None:
    stock = {
        "id": 701,
        "name": "TEST",
        "code": "005930",
        "scanner_generation_id": "005930:SCANPROM-701:r1",
        "effective_venue": "KRX",
        "market_session_bucket": "regular",
        "last_watching_ai_decision_trace_id": "trace-pipeline-701",
    }
    events = [
        _pipeline_event(
            stock=stock,
            pipeline="ENTRY_PIPELINE",
            source_stage="scalping_scanner_fast_precheck",
            second=0,
            fields={"bbo_observed": True, "depth_observed": True},
        ),
        _pipeline_event(
            stock=stock,
            pipeline="ENTRY_PIPELINE",
            source_stage="ai_confirmed",
            second=1,
            fields={"action": "BUY", "bbo_observed": True, "depth_observed": True},
        ),
        _pipeline_event(
            stock=stock,
            pipeline="ENTRY_PIPELINE",
            source_stage="order_bundle_submitted",
            second=2,
            fields={
                "actual_order_submitted": True,
                "broker_order_no": "broker-701",
                "requested_qty": 5,
                "bbo_observed": True,
                "depth_observed": True,
            },
        ),
        _pipeline_event(
            stock=stock,
            pipeline="HOLDING_PIPELINE",
            source_stage="position_rebased_after_fill",
            second=3,
            fields={
                "fill_quality": "FULL_FILL",
                "fill_qty": 5,
                "fill_price": 10_000,
                "requested_qty": 5,
                "bbo_observed": True,
                "depth_observed": True,
            },
        ),
        _pipeline_event(
            stock=stock,
            pipeline="HOLDING_PIPELINE",
            source_stage="holding_started",
            second=4,
            fields={"bbo_observed": True, "depth_observed": True},
        ),
        _pipeline_event(
            stock=stock,
            pipeline="HOLDING_PIPELINE",
            source_stage="stat_action_decision_snapshot",
            second=5,
            fields={
                "chosen_action": "hold_wait",
                "bbo_observed": True,
                "depth_observed": True,
            },
        ),
        _pipeline_event(
            stock=stock,
            pipeline="HOLDING_PIPELINE",
            source_stage="sell_completed",
            second=63,
            fields={
                "sell_qty": 5,
                "sell_price": 10_010,
                "bbo_observed": True,
                "depth_observed": True,
            },
        ),
    ]
    final_fields = events[-1]["fields"]
    final_fields.update(
        {
            "main_lifecycle_exit_qty": "5",
            "main_lifecycle_exit_price": "10010",
            "main_lifecycle_reconciled_final_exit": "True",
            "main_lifecycle_broker_reconciled": "True",
            "main_lifecycle_fees_taxes_krw": "20",
            "main_lifecycle_slippage_krw": "5",
            "main_lifecycle_slippage_basis_price": "10011",
            "main_lifecycle_slippage_basis_source": "test_exit_decision_price",
            "main_lifecycle_realized_net_pnl_krw": "25",
        }
    )
    source = tmp_path / "pipeline_events.jsonl"
    _write_jsonl(source, events)

    report = build_daily_report(
        TARGET_DATE,
        source_path=source,
        reviewed_cost_profile_sha256=COST_HASH,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256=SYMBOL_HASH,
        symbol_master_artifact_verified=True,
        write=False,
    )

    assert report["source_kind"] == "pipeline_events_explicit_id_only"
    assert report["pipeline_lifecycle_mapped_row_count"] == 7
    assert report["pipeline_lifecycle_accepted_row_count"] == 7
    assert report["pipeline_lifecycle_instrumentation_gap_count"] == 0
    assert report["promotion_ready"] is True
    assert report["rows"][0]["attempt_id"] == stock["scanner_generation_id"]
    assert report["rows"][0]["actual_holding_duration_sec"] == pytest.approx(60)
    assert report["rows"][0]["scale_in_decisions"] == ["NO_ADD"]
    assert report["rows"][0]["market_observation_expected_count"] == 4
    assert report["rows"][0]["bbo_coverage_pct"] == pytest.approx(100)
    assert report["rows"][0]["depth_coverage_pct"] == pytest.approx(100)


def test_mapped_pipeline_row_without_id_is_gap_and_never_joined(
    tmp_path: Path,
) -> None:
    source = tmp_path / "pipeline_events.jsonl"
    _write_jsonl(
        source,
        [
            {
                "event_type": "pipeline_event",
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_code": "005930",
                "record_id": 702,
                "fields": {"action": "BUY"},
                "emitted_at": BASE.isoformat(),
                "emitted_date": TARGET_DATE,
            }
        ],
    )

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["rows"] == []
    assert report["pipeline_lifecycle_missing_identity_count"] == 1
    assert report["pipeline_lifecycle_instrumentation_gap_count"] == 1
    assert "pipeline_lifecycle_instrumentation_gap" in report[
        "global_source_quality_gate_blockers"
    ]
    assert report["promotion_ready"] is False


def test_pipeline_never_falls_back_to_legacy_timestamp_or_stage_claim(
    tmp_path: Path,
) -> None:
    stock = {
        "id": 703,
        "code": "005930",
        "scanner_generation_id": "005930:SCANPROM-703:r1",
    }
    missing_timestamp = _pipeline_event(
        stock=stock,
        pipeline="ENTRY_PIPELINE",
        source_stage="scalping_scanner_fast_precheck",
        second=0,
    )
    missing_timestamp["fields"].pop("main_lifecycle_observed_at")
    spoofed_stage = _pipeline_event(
        stock=stock,
        pipeline="ENTRY_PIPELINE",
        source_stage="ai_confirmed",
        second=1,
        fields={"action": "BUY"},
    )
    spoofed_stage["fields"]["main_lifecycle_stage"] = "fill"
    source = tmp_path / "pipeline_events.jsonl"
    _write_jsonl(source, [missing_timestamp, spoofed_stage])

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["rows"] == []
    reasons = {
        example["reason"] for example in report["instrumentation_gap_examples"]
    }
    assert "pipeline_lifecycle_explicit_timestamp_invalid" in reasons
    assert "pipeline_lifecycle_stage_mapping_mismatch" in reasons
    assert report["promotion_ready"] is False


def test_execution_exit_requires_exact_qty_price_and_basis_source(
    tmp_path: Path,
) -> None:
    events: list[dict[str, Any]] = []
    mutations = (
        ("missing-exact-qty", "main_lifecycle_exit_qty", None),
        ("zero-exact-price", "main_lifecycle_exit_price", "0"),
        ("missing-basis-source", "main_lifecycle_slippage_basis_source", None),
    )
    for offset, (attempt_suffix, field_name, replacement) in enumerate(mutations):
        stock = {
            "id": 710 + offset,
            "code": "005930",
            "scanner_generation_id": f"005930:SCANPROM-71{offset}:r1-{attempt_suffix}",
        }
        event = _pipeline_event(
            stock=stock,
            pipeline="HOLDING_PIPELINE",
            source_stage="sell_completed",
            second=60 + offset,
            fields={
                # Legacy aggregate fields must never repair an invalid exact leg.
                "sell_qty": 10,
                "sold_qty": 10,
                "sell_price": 10_014,
                "main_lifecycle_exit_qty": 6,
                "main_lifecycle_exit_price": 10_010,
                "main_lifecycle_reconciled_final_exit": True,
                "main_lifecycle_broker_reconciled": True,
                "main_lifecycle_fees_taxes_krw": 10,
                "main_lifecycle_slippage_krw": 30,
                "main_lifecycle_slippage_basis_price": 10_015,
                "main_lifecycle_slippage_basis_source": "runner_decision_price",
                "main_lifecycle_realized_net_pnl_krw": 20,
            },
        )
        if replacement is None:
            event["fields"].pop(field_name)
        else:
            event["fields"][field_name] = replacement
        events.append(event)

    source = tmp_path / "pipeline_events.jsonl"
    _write_jsonl(source, events)

    report = build_daily_report(TARGET_DATE, source_path=source, write=False)

    assert report["rows"] == []
    assert report["pipeline_lifecycle_mapped_row_count"] == 3
    assert report["pipeline_lifecycle_accepted_row_count"] == 0
    assert report["pipeline_lifecycle_instrumentation_gap_count"] == 3
    reasons = {
        example["reason"] for example in report["instrumentation_gap_examples"]
    }
    assert reasons == {
        "pipeline_execution_exit_exact_price_or_qty_missing",
        "pipeline_execution_exit_exact_price_or_qty_invalid",
        "pipeline_slippage_basis_pair_incomplete",
    }
    assert report["promotion_ready"] is False


def test_standard_sell_partial_fill_materializes_as_exact_nonterminal_exit_leg() -> None:
    data, reason = paired._pipeline_transition_data(
        lifecycle_stage="exit",
        source_stage="sell_partial_fill_progress",
        fields={
            "main_lifecycle_exit_qty": 2,
            "main_lifecycle_exit_price": 10_010,
            "main_lifecycle_broker_reconciled": False,
            "main_lifecycle_reconciled_final_exit": False,
            "main_lifecycle_realized_net_pnl_krw": 14,
            "main_lifecycle_fees_taxes_krw": 6,
            "sell_receipt_economics_complete": True,
            "sell_receipt_quantity_contract_complete": True,
            "sell_receipt_unit_fill_consistent": True,
            "broker_execution_provenance_complete": True,
            "broker_execution_time_source": "official_fid_908",
            "broker_execution_time_raw": "090003",
            "broker_actual_execution_venue": "KRX",
            "broker_sor_flag": "N",
            "execution_no": "SELL-PARTIAL-1",
        },
    )

    assert reason is None
    assert data is not None
    assert data["exit_qty"] == 2
    assert data["exit_price"] == 10_010
    assert "reconciled_final_exit" not in data
    assert data["realized_net_pnl_krw"] == 14
    assert data["fees_taxes_krw"] == 6


@pytest.mark.parametrize(
    ("lifecycle_stage", "source_stage", "fields", "expected_reason"),
    (
        (
            "fill",
            "position_rebased_after_fill",
            {
                "fill_state": "partial",
                "fill_qty": 2,
                "fill_price": 10_000,
                "receipt_economics_complete": False,
            },
            "pipeline_fill_receipt_economics_incomplete",
        ),
        (
            "scale_in",
            "scale_in_executed",
            {
                "actual_order_submitted": True,
                "fill_qty": 2,
                "fill_price": 10_000,
                "receipt_economics_complete": True,
                "receipt_quantity_contract_complete": False,
            },
            "pipeline_scale_in_receipt_quantity_contract_incomplete",
        ),
        (
            "exit",
            "sell_completed",
            {
                "main_lifecycle_exit_qty": 2,
                "main_lifecycle_exit_price": 10_000,
                "sell_execution_receipt_economics_complete": True,
                "sell_execution_receipt_quantity_contract_complete": True,
                "sell_execution_receipt_unit_fill_consistent": False,
            },
            "pipeline_exit_receipt_unit_fill_inconsistent",
        ),
        (
            "exit",
            "nxt_rising_missed_tp1_partial_sell_completed",
            {
                "main_lifecycle_exit_qty": 2,
                "main_lifecycle_exit_price": 10_000,
                "broker_execution_provenance_complete": True,
            },
            "pipeline_exit_receipt_economics_contract_missing",
        ),
        (
            "exit",
            "sell_completed",
            {
                "main_lifecycle_exit_qty": 2,
                "main_lifecycle_exit_price": 10_000,
                "sell_execution_receipt_economics_complete": True,
                "sell_execution_receipt_quantity_contract_complete": True,
                "sell_execution_receipt_unit_fill_consistent": True,
                "broker_execution_provenance_complete": False,
            },
            "pipeline_exit_broker_execution_provenance_incomplete",
        ),
        (
            "fill",
            "position_rebased_after_fill",
            {
                "fill_state": "full",
                "fill_qty": 2,
                "fill_price": 10_000,
                "receipt_economics_complete": True,
                "receipt_quantity_contract_complete": True,
                "receipt_unit_fill_consistent": True,
                "broker_execution_provenance_complete": True,
                "broker_execution_time_source": "local_receive_time_fallback",
                "broker_actual_execution_venue": "KRX",
            },
            "pipeline_fill_broker_execution_time_source_invalid",
        ),
        (
            "exit",
            "sell_completed",
            {
                "main_lifecycle_exit_qty": 2,
                "main_lifecycle_exit_price": 10_000,
                "sell_execution_receipt_economics_complete": True,
                "sell_execution_receipt_quantity_contract_complete": True,
                "sell_execution_receipt_unit_fill_consistent": True,
                "broker_execution_provenance_complete": True,
                "broker_execution_time_source": "official_fid_908",
                "broker_execution_time_raw": "101530",
                "broker_actual_execution_venue": "KRX",
            },
            "pipeline_exit_broker_execution_number_missing",
        ),
        (
            "scale_in",
            "scale_in_executed",
            {
                "actual_order_submitted": True,
                "fill_qty": 2,
                "fill_price": 10_000,
                "receipt_economics_complete": True,
                "receipt_quantity_contract_complete": True,
                "receipt_unit_fill_consistent": True,
                "broker_execution_provenance_complete": True,
                "broker_execution_time_source": "official_fid_908",
                "broker_actual_execution_venue": "UNKNOWN",
            },
            "pipeline_scale_in_broker_execution_actual_venue_invalid",
        ),
    ),
)
def test_execution_receipt_quality_contracts_fail_closed(
    lifecycle_stage, source_stage, fields, expected_reason
) -> None:
    data, reason = paired._pipeline_transition_data(
        lifecycle_stage=lifecycle_stage,
        source_stage=source_stage,
        fields=fields,
    )

    assert data is None
    assert reason == expected_reason


def test_live_entry_and_holding_loggers_inject_exact_id_without_journal_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.engine import sniper_state_handlers as state_handlers

    emitted: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    monkeypatch.setattr(
        state_handlers,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    monkeypatch.setattr(
        state_handlers, "_remember_scanner_terminal_block", lambda *_args: None
    )
    monkeypatch.setattr(
        state_handlers, "observe_candidate_transition_safe", lambda *_args: None
    )
    monkeypatch.setattr(
        state_handlers,
        "_maybe_register_rising_missed_nxt_downstream_block_sampler",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        journal,
        "_append_jsonl",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("synchronous lifecycle journal write is forbidden")
        ),
    )
    stock = {
        "id": 704,
        "name": "TEST",
        "code": "005930",
        "strategy": "SCALPING",
        "scanner_generation_id": "005930:SCANPROM-704:r1",
        "effective_venue": "KRX",
        "market_session_bucket": "regular",
        "last_watching_ai_decision_trace_id": "trace-live-704",
    }

    state_handlers._log_entry_pipeline(
        stock,
        "005930",
        "ai_confirmed",
        action="BUY",
        main_lifecycle_id="spoofed",
        attempt_id="spoofed",
    )
    state_handlers._log_holding_pipeline(
        stock,
        "005930",
        "stat_action_decision_snapshot",
        chosen_action="hold_wait",
    )

    assert len(emitted) == 2
    entry_fields = emitted[0][1]["fields"]
    holding_fields = emitted[1][1]["fields"]
    expected_id = mint_main_lifecycle_id(
        record_id=stock["id"],
        stock_code=stock["code"],
        attempt_id=stock["scanner_generation_id"],
    )
    assert entry_fields["main_lifecycle_id"] == expected_id
    assert holding_fields["main_lifecycle_id"] == expected_id
    assert entry_fields["attempt_id"] == stock["scanner_generation_id"]
    assert holding_fields["attempt_id"] == stock["scanner_generation_id"]
    assert entry_fields["main_lifecycle_stage"] == "entry_decision"
    assert holding_fields["main_lifecycle_stage"] == "scale_in"
    assert entry_fields["main_lifecycle_runtime_effect"] is False
    assert holding_fields["main_lifecycle_order_authority"] is False
    assert holding_fields["main_lifecycle_heartbeat"] is True
    assert "_main_lifecycle" not in " ".join(stock)


def test_unmapped_live_pipeline_stages_preserve_existing_attempt_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.engine import sniper_state_handlers as state_handlers

    emitted: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    monkeypatch.setattr(
        state_handlers,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    monkeypatch.setattr(
        state_handlers, "_remember_scanner_terminal_block", lambda *_args: None
    )
    monkeypatch.setattr(
        state_handlers, "observe_candidate_transition_safe", lambda *_args: None
    )
    monkeypatch.setattr(
        state_handlers,
        "_maybe_register_rising_missed_nxt_downstream_block_sampler",
        lambda *_args: None,
    )
    stock = {"id": 705, "name": "TEST", "code": "005930"}

    state_handlers._log_entry_pipeline(
        stock,
        "005930",
        "unmapped_entry_diagnostic",
        attempt_id="existing-entry-attempt",
        main_lifecycle_id="spoofed",
    )
    state_handlers._log_holding_pipeline(
        stock,
        "005930",
        "unmapped_holding_diagnostic",
        attempt_id="existing-holding-attempt",
        main_lifecycle_id="spoofed",
    )

    assert emitted[0][1]["fields"]["attempt_id"] == "existing-entry-attempt"
    assert emitted[1][1]["fields"]["attempt_id"] == "existing-holding-attempt"
    assert "main_lifecycle_id" not in emitted[0][1]["fields"]
    assert "main_lifecycle_id" not in emitted[1][1]["fields"]


def test_pipeline_heartbeat_is_generated_only_for_exposure_stages() -> None:
    stock = {
        "id": 707,
        "code": "005930",
        "scanner_generation_id": "005930:SCANPROM-707:r1",
    }

    holding = pipeline_lifecycle_fields_safe(
        stock,
        "005930",
        pipeline="HOLDING_PIPELINE",
        source_stage="ai_holding_review",
        source_fields={},
        observed_at=BASE,
    )
    exit_observation = pipeline_lifecycle_fields_safe(
        stock,
        "005930",
        pipeline="HOLDING_PIPELINE",
        source_stage="sell_order_sent",
        source_fields={},
        observed_at=BASE,
    )
    scanner = pipeline_lifecycle_fields_safe(
        stock,
        "005930",
        pipeline="ENTRY_PIPELINE",
        source_stage="scalping_scanner_fast_precheck",
        source_fields={},
        observed_at=BASE,
    )

    assert holding["main_lifecycle_heartbeat"] is True
    assert exit_observation["main_lifecycle_heartbeat"] is True
    assert scanner["main_lifecycle_heartbeat"] is False


def test_default_pipeline_source_path_is_daily_and_not_sync_journal() -> None:
    assert pipeline_event_path(TARGET_DATE).name == (
        "pipeline_events_2026-08-14.jsonl"
    )


def test_missing_scanner_generation_fails_open_without_hot_path_error_log(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(journal, "log_error", errors.append)

    fields = pipeline_lifecycle_fields_safe(
        {"id": 705, "code": "005930"},
        "005930",
        pipeline="ENTRY_PIPELINE",
        source_stage="scalping_scanner_fast_precheck",
        observed_at=BASE,
    )

    assert fields == {}
    assert errors == []
