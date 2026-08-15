from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.engine import sniper_execution_receipts as execution_receipts
from src.engine.scalping.main_lifecycle_journal import (
    mint_main_lifecycle_id,
    pipeline_lifecycle_fields_safe,
)
from src.engine.scalping.main_lifecycle_paired import (
    _validated_pipeline_transition,
    build_daily_report,
)

COST_HASH = "a" * 64
SYMBOL_HASH = "b" * 64


def test_broker_receipt_pipeline_preserves_exact_lifecycle_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def capture_event(
        pipeline: str,
        name: str,
        stock_code: str,
        stage: str,
        *,
        record_id: Any,
        fields: dict[str, Any],
    ) -> None:
        captured.update(
            {
                "event_type": "pipeline_event",
                "pipeline": pipeline,
                "stage": stage,
                "stock_name": name,
                "stock_code": stock_code,
                "record_id": record_id,
                "fields": dict(fields),
            }
        )

    monkeypatch.setattr(execution_receipts, "emit_pipeline_event", capture_event)
    monkeypatch.setattr(
        execution_receipts,
        "observe_candidate_transition_safe",
        lambda *args, **kwargs: None,
    )
    stock = {
        "id": 701,
        "code": "005930",
        "name": "SAMSUNG",
        "scanner_generation_id": "scanner-generation-701",
        "effective_venue": "KRX",
        "market_session_bucket": "regular",
        "last_watching_ai_decision_trace_id": "trace-701",
    }
    broker_observed_at = datetime(2026, 8, 14, 10, 1, 2, 345_000)

    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "position_rebased_after_fill",
        candidate_stock=stock,
        observed_at=broker_observed_at,
        fill_quality="FULL_FILL",
        fill_qty=3,
        fill_price=70_000,
        requested_qty=3,
    )

    fields = captured["fields"]
    transition, error, in_scope = _validated_pipeline_transition(
        captured,
        target_date=str(fields["main_lifecycle_trade_date"]),
    )
    assert error is None
    assert in_scope is True
    assert transition is not None
    assert transition["main_lifecycle_id"] == mint_main_lifecycle_id(
        record_id=stock["id"],
        stock_code=stock["code"],
        attempt_id=stock["scanner_generation_id"],
    )
    assert transition["attempt_id"] == stock["scanner_generation_id"]
    assert transition["stage"] == "fill"
    assert transition["data"]["fill_state"] == "full"
    assert transition["data"]["broker_execution_provenance_state"] == "missing"
    assert transition["data"]["broker_execution_official_reference_sha"] == (
        "69642586f7d84ba9fd8a6faf1f1537c7fda6568b"
    )
    assert transition["data"]["decision_trace_id"] == "trace-701"
    assert transition["observed_at"] == broker_observed_at.replace(
        tzinfo=timezone(timedelta(hours=9))
    ).isoformat(timespec="microseconds")
    assert fields["main_lifecycle_runtime_effect"] is False
    assert fields["main_lifecycle_order_authority"] is False
    assert fields["main_lifecycle_provider_authority"] is False

    required_snapshot_keys = {
        "id",
        "scanner_generation_id",
        "effective_venue",
        "market_session_bucket",
        "last_watching_ai_decision_trace_id",
    }
    assert required_snapshot_keys <= set(execution_receipts._BUY_RECEIPT_SNAPSHOT_KEYS)
    assert required_snapshot_keys <= set(execution_receipts._SELL_RECEIPT_SNAPSHOT_KEYS)
    assert required_snapshot_keys <= set(execution_receipts._ADD_RECEIPT_SNAPSHOT_KEYS)


def test_missing_lineage_cannot_retain_caller_supplied_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        execution_receipts,
        "emit_pipeline_event",
        lambda *args, **kwargs: captured.update(kwargs["fields"]),
    )
    monkeypatch.setattr(
        execution_receipts,
        "observe_candidate_transition_safe",
        lambda *args, **kwargs: None,
    )

    execution_receipts._log_holding_pipeline(
        "SAMSUNG",
        "005930",
        701,
        "holding_started",
        candidate_stock={"id": 701, "code": "005930"},
        attempt_id="spoofed-attempt",
        main_lifecycle_id="mlc-00000000000000000000000000000000",
        main_lifecycle_identity_schema=("main_scalping_lifecycle_pipeline_identity_v1"),
        main_lifecycle_runtime_effect=True,
        main_lifecycle_order_authority=True,
        main_lifecycle_provider_authority=True,
    )

    assert "attempt_id" not in captured
    assert "main_lifecycle_id" not in captured
    assert "main_lifecycle_identity_schema" not in captured
    assert "main_lifecycle_runtime_effect" not in captured
    assert "main_lifecycle_order_authority" not in captured
    assert "main_lifecycle_provider_authority" not in captured


def test_unmapped_receipt_stage_preserves_existing_attempt_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        execution_receipts,
        "emit_pipeline_event",
        lambda *args, **kwargs: captured.update(kwargs["fields"]),
    )

    execution_receipts._log_holding_pipeline(
        "SAMSUNG",
        "005930",
        701,
        "unmapped_receipt_diagnostic",
        candidate_stock={"id": 701, "code": "005930"},
        attempt_id="existing-receipt-attempt",
        main_lifecycle_id="spoofed",
    )

    assert captured["attempt_id"] == "existing-receipt-attempt"
    assert "main_lifecycle_id" not in captured


def test_exit_economics_uses_exact_decision_price_or_omits_slippage() -> None:
    fields = execution_receipts._main_lifecycle_exit_economics_fields(
        {"exit_decision_executable_sell_price": 10_010},
        buy_price=10_000,
        sell_price=10_005,
        sell_qty=4,
        realized_net_pnl_krw=12,
    )
    assert fields == {
        "main_lifecycle_fees_taxes_krw": 8.0,
        "main_lifecycle_realized_net_pnl_krw": 12,
        "main_lifecycle_slippage_krw": 20.0,
        "main_lifecycle_slippage_basis_price": 10_010.0,
        "main_lifecycle_slippage_basis_source": ("exit_decision_executable_sell_price"),
    }

    no_basis = execution_receipts._main_lifecycle_exit_economics_fields(
        {},
        buy_price=10_000,
        sell_price=10_005,
        sell_qty=4,
        realized_net_pnl_krw=12,
    )
    assert "main_lifecycle_slippage_krw" not in no_basis


def test_current_receipt_rows_preserve_lifecycle_but_fail_close_raw_fill_gap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    events: list[dict[str, Any]] = []
    stock = {
        "id": 801,
        "code": "005930",
        "name": "SAMSUNG",
        "scanner_generation_id": "scanner-generation-801",
        "effective_venue": "KRX",
        "market_session_bucket": "regular",
        "last_watching_ai_decision_trace_id": "trace-801",
    }
    kst = timezone(timedelta(hours=9))
    started_at = datetime(2026, 8, 15, 9, 0, tzinfo=kst)

    def capture_event(
        pipeline: str,
        name: str,
        stock_code: str,
        stage: str,
        *,
        record_id: Any,
        fields: dict[str, Any],
    ) -> None:
        events.append(
            {
                "event_type": "pipeline_event",
                "pipeline": pipeline,
                "stage": stage,
                "stock_name": name,
                "stock_code": stock_code,
                "record_id": record_id,
                "fields": dict(fields),
            }
        )

    def append_source_stage(
        pipeline: str,
        stage: str,
        observed_at: datetime,
        **source_fields: Any,
    ) -> None:
        fields = dict(source_fields)
        fields.update(
            pipeline_lifecycle_fields_safe(
                stock,
                stock["code"],
                pipeline=pipeline,
                source_stage=stage,
                source_fields=fields,
                observed_at=observed_at,
            )
        )
        capture_event(
            pipeline,
            stock["name"],
            stock["code"],
            stage,
            record_id=stock["id"],
            fields=fields,
        )

    monkeypatch.setattr(execution_receipts, "emit_pipeline_event", capture_event)
    monkeypatch.setattr(
        execution_receipts,
        "observe_candidate_transition_safe",
        lambda *args, **kwargs: None,
    )

    common_market = {"bbo_observed": True, "depth_observed": True}
    append_source_stage(
        "ENTRY_PIPELINE",
        "scalping_scanner_fast_precheck",
        started_at,
        **common_market,
    )
    append_source_stage(
        "ENTRY_PIPELINE",
        "ai_confirmed",
        started_at + timedelta(seconds=1),
        action="BUY",
        **common_market,
    )
    append_source_stage(
        "ENTRY_PIPELINE",
        "order_bundle_submitted",
        started_at + timedelta(seconds=2),
        actual_order_submitted=True,
        broker_order_no="0000801",
        requested_qty=1,
        **common_market,
    )
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "position_rebased_after_fill",
        candidate_stock=stock,
        observed_at=(started_at + timedelta(seconds=3)).replace(tzinfo=None),
        fill_quality="FULL_FILL",
        fill_qty=1,
        fill_price=10_000,
        requested_qty=1,
    )
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "holding_started",
        candidate_stock=stock,
        observed_at=(started_at + timedelta(seconds=4)).replace(tzinfo=None),
    )
    append_source_stage(
        "HOLDING_PIPELINE",
        "stat_action_decision_snapshot",
        started_at + timedelta(seconds=5),
        chosen_action="hold_wait",
        **common_market,
    )
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "sell_completed",
        candidate_stock=stock,
        observed_at=(started_at + timedelta(seconds=10)).replace(tzinfo=None),
        sell_price=10_010,
        sell_qty=1,
        main_lifecycle_exit_qty=1,
        main_lifecycle_exit_price=10_010,
        main_lifecycle_broker_reconciled=True,
        main_lifecycle_reconciled_final_exit=True,
        main_lifecycle_fees_taxes_krw=3,
        main_lifecycle_slippage_krw=1,
        main_lifecycle_slippage_basis_price=10_011,
        main_lifecycle_slippage_basis_source="test_exit_decision_price",
        main_lifecycle_realized_net_pnl_krw=6,
    )

    source = tmp_path / "pipeline.jsonl"
    source.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in events),
        encoding="utf-8",
    )
    report = build_daily_report(
        "2026-08-15",
        source_path=source,
        reviewed_cost_profile_sha256=COST_HASH,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256=SYMBOL_HASH,
        symbol_master_artifact_verified=True,
        write=False,
    )

    assert report["source_invalid_transition_count"] == 0
    assert report["promotion_ready"] is False
    assert len(report["rows"]) == 1
    row = report["rows"][0]
    assert row["terminal_state"] == "FINAL_EXIT_RECONCILED"
    assert row["actual_holding_duration_sec"] == 7.0
    assert row["session_exposure_sec"] == 10.0
    assert row["fees_taxes_krw"] == 3.0
    assert row["slippage_krw"] == 1.0
    assert row["realized_net_pnl_krw"] == 6.0
    assert row["broker_execution_provenance_state_counts"] == {"missing": 2}
    assert row["broker_execution_provenance_gap_count"] == 2
    assert row["broker_execution_provenance_gap_reasons"] == [
        "official_broker_execution_raw_fields_missing"
    ]
    assert row["broker_execution_entry_covered_qty"] == 0.0
    assert row["broker_execution_exit_covered_qty"] == 0.0
    assert "broker_execution_raw_provenance_gap" in row["promotion_blockers"]
    assert "broker_execution_entry_qty_coverage_incomplete" in row["promotion_blockers"]
    assert "broker_execution_exit_qty_coverage_incomplete" in row["promotion_blockers"]
    assert row["promotion_evidence_eligible"] is False
    assert report["promotion_evidence_eligible_count"] == 0
    assert report["runtime_authority"] is False
    assert report["order_authority"] is False
    assert report["provider_authority"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["runtime_effect"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    assert row["runtime_authority"] is False
    assert row["order_authority"] is False
    assert row["provider_authority"] is False
    assert row["allowed_runtime_apply"] is False


def test_partial_exit_and_runner_preserve_capital_time_and_leg_slippage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    events: list[dict[str, Any]] = []
    kst = timezone(timedelta(hours=9))
    started_at = datetime(2026, 8, 15, 9, 0, tzinfo=kst)
    stock = {
        "id": 901,
        "code": "005930",
        "name": "SAMSUNG",
        "strategy": "SCALPING",
        "scanner_generation_id": "scanner-generation-901",
        "effective_venue": "KRX",
        "market_session_bucket": "regular",
        "last_watching_ai_decision_trace_id": "trace-901",
        "buy_price": 10_000,
        "buy_qty": 10,
        "nxt_rising_missed_tp1_partial_requested_qty": 4,
        "nxt_rising_missed_tp1_partial_filled_qty": 0,
        "nxt_rising_missed_tp1_partial_fill_amount": 0,
        "nxt_rising_missed_tp1_partial_original_qty": 10,
        "sell_target_price": 10_025,
        "exit_decision_executable_sell_price": 10_015,
    }
    record = SimpleNamespace(
        buy_price=10_000.0,
        buy_qty=10,
        position_tag=None,
        stock_name="SAMSUNG",
    )

    class _Query:
        def filter_by(self, **_kwargs: Any) -> _Query:
            return self

        def first(self) -> Any:
            return record

    class _Session:
        def __enter__(self) -> _Session:
            return self

        def __exit__(self, *_args: Any) -> None:
            return None

        def query(self, *_args: Any) -> _Query:
            return _Query()

        def flush(self) -> None:
            return None

        def commit(self) -> None:
            return None

    class _DB:
        def get_session(self) -> _Session:
            return _Session()

    def capture_event(
        pipeline: str,
        name: str,
        stock_code: str,
        stage: str,
        *,
        record_id: Any,
        fields: dict[str, Any],
    ) -> None:
        events.append(
            {
                "event_type": "pipeline_event",
                "pipeline": pipeline,
                "stage": stage,
                "stock_name": name,
                "stock_code": stock_code,
                "record_id": record_id,
                "fields": dict(fields),
            }
        )

    def append_source_stage(
        pipeline: str,
        stage: str,
        observed_at: datetime,
        **source_fields: Any,
    ) -> None:
        fields = dict(source_fields)
        fields.update(
            pipeline_lifecycle_fields_safe(
                stock,
                stock["code"],
                pipeline=pipeline,
                source_stage=stage,
                source_fields=fields,
                observed_at=observed_at,
            )
        )
        capture_event(
            pipeline,
            stock["name"],
            stock["code"],
            stage,
            record_id=stock["id"],
            fields=fields,
        )

    monkeypatch.setattr(execution_receipts, "DB", _DB())
    monkeypatch.setattr(execution_receipts, "event_bus", None)
    monkeypatch.setattr(execution_receipts, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(execution_receipts, "highest_prices", {})
    monkeypatch.setattr(execution_receipts, "_get_fast_state", lambda _code: None)
    monkeypatch.setattr(
        execution_receipts,
        "_resolve_sell_execution_context",
        lambda *_args: (record, 10_000.0, 0.0, "SCALPING", False),
    )
    monkeypatch.setattr(execution_receipts, "emit_pipeline_event", capture_event)
    monkeypatch.setattr(
        execution_receipts,
        "observe_candidate_transition_safe",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        execution_receipts,
        "_publish_sell_execution_message",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(execution_receipts, "_scalp_exit_completed_callback", None)

    common_market = {"bbo_observed": True, "depth_observed": True}
    append_source_stage(
        "ENTRY_PIPELINE",
        "scalping_scanner_fast_precheck",
        started_at,
        **common_market,
    )
    append_source_stage(
        "ENTRY_PIPELINE",
        "ai_confirmed",
        started_at + timedelta(seconds=1),
        action="BUY",
        **common_market,
    )
    append_source_stage(
        "ENTRY_PIPELINE",
        "order_bundle_submitted",
        started_at + timedelta(seconds=2),
        actual_order_submitted=True,
        broker_order_no="0000901",
        requested_qty=10,
        **common_market,
    )
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "position_rebased_after_fill",
        candidate_stock=stock,
        observed_at=(started_at + timedelta(seconds=3)).replace(tzinfo=None),
        fill_quality="FULL_FILL",
        fill_qty=10,
        fill_price=10_000,
        requested_qty=10,
    )
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "holding_started",
        candidate_stock=stock,
        observed_at=(started_at + timedelta(seconds=4)).replace(tzinfo=None),
    )
    append_source_stage(
        "HOLDING_PIPELINE",
        "stat_action_decision_snapshot",
        started_at + timedelta(seconds=5),
        chosen_action="hold_wait",
        **common_market,
    )

    execution_receipts._handle_nxt_rising_missed_tp1_partial_sell_execution(
        target_id=stock["id"],
        target_stock=stock,
        code=stock["code"],
        order_no="PARTIAL-901",
        exec_price=10_020,
        exec_qty=2,
        order_qty=4,
        remaining_qty=2,
        cumulative_exec_amount=20_040,
        execution_no="PARTIAL-E1",
        unit_exec_price=10_020,
        unit_exec_qty=2,
        now=(started_at + timedelta(seconds=6)).replace(tzinfo=None),
        safe_buy_price=10_000,
    )
    # DB preserves the original position basis until the final exact receipt;
    # the durable receipt ledger owns the runner quantity meanwhile.
    assert record.buy_qty == 10
    assert stock["buy_qty"] == 8
    execution_receipts._handle_nxt_rising_missed_tp1_partial_sell_execution(
        target_id=stock["id"],
        target_stock=stock,
        code=stock["code"],
        order_no="PARTIAL-901",
        exec_price=10_020,
        exec_qty=4,
        order_qty=4,
        remaining_qty=0,
        cumulative_exec_amount=40_080,
        execution_no="PARTIAL-E2",
        unit_exec_price=10_020,
        unit_exec_qty=2,
        now=(started_at + timedelta(seconds=7)).replace(tzinfo=None),
        safe_buy_price=10_000,
    )
    assert record.buy_qty == 10
    assert stock["buy_qty"] == 6

    stock["status"] = "SELL_ORDERED"
    stock["sell_odno"] = "RUNNER-901"
    execution_receipts.handle_real_execution(
        {
            "code": stock["code"],
            "type": "SELL",
            "order_no": "RUNNER-901",
            "price": 10_010,
            "qty": 6,
            "order_qty": 6,
            "remaining_qty": 0,
            "cumulative_exec_amount": 60_060,
            "execution_no": "RUNNER-E1",
            "unit_exec_price": 10_010,
            "unit_exec_qty": 6,
            "broker_execution_time_raw": "090010",
            "actual_execution_venue": "KRX",
            "actual_exchange_code": "1",
            "actual_exchange_name": "KRX",
            "sor_flag": "N",
        }
    )

    source = tmp_path / "partial_runner_pipeline.jsonl"
    source.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in events),
        encoding="utf-8",
    )
    report = build_daily_report(
        "2026-08-15",
        source_path=source,
        reviewed_cost_profile_sha256=COST_HASH,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256=SYMBOL_HASH,
        symbol_master_artifact_verified=True,
        write=False,
    )

    assert report["source_invalid_transition_count"] == 0
    assert report["promotion_ready"] is False
    row = report["rows"][0]
    assert row["terminal_state"] == "FINAL_EXIT_RECONCILED"
    assert row["actual_holding_duration_sec"] == 7.0
    assert row["session_exposure_sec"] == 10.0
    assert row["exit_qty"] == 10.0
    assert row["open_qty_at_censor"] == 0.0
    assert row["exit_execution_leg_count"] == 3
    assert row["exit_vwap_price"] == pytest.approx(10_014.0)
    assert row["slippage_basis_covered_qty"] == 10.0
    assert row["slippage_basis_source_covered_qty"] == 10.0
    assert row["slippage_basis_sources"] == [
        "nxt_rising_missed_tp1_partial_sell_target_price",
        "exit_decision_executable_sell_price",
    ]
    assert row["slippage_basis_vwap_price"] == pytest.approx(10_019.0)
    assert row["slippage_krw"] == pytest.approx(50.0)
    assert row["capital_time_krw_hours"] == pytest.approx(155.5555555556)
    assert row["economics_covered_exit_qty"] == {
        "fees_taxes_krw": 10.0,
        "realized_net_pnl_krw": 10.0,
        "slippage_krw": 10.0,
    }
    assert row["broker_execution_provenance_state_counts"] == {"missing": 4}
    assert row["broker_execution_provenance_gap_count"] == 4
    assert row["broker_execution_entry_covered_qty"] == 0.0
    assert row["broker_execution_exit_covered_qty"] == 0.0
    assert row["promotion_evidence_eligible"] is False
    assert report["promotion_evidence_eligible_count"] == 0
