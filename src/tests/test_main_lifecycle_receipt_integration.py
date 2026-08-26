from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.engine import sniper_execution_receipts as execution_receipts
from src.engine import sniper_state_handlers as state_handlers
from src.engine import sniper_sync
from src.engine.scalping.main_lifecycle_journal import (
    BROKER_EXECUTION_RECEIVE_TIME_SOURCE,
    mint_main_lifecycle_id,
    pipeline_lifecycle_fields_safe,
)
from src.engine.scalping.main_lifecycle_paired import (
    SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES,
    _validated_pipeline_transition,
    build_daily_report,
)

COST_HASH = "a" * 64
SYMBOL_HASH = "b" * 64


def _exact_buy_execution_stock(
    *,
    order_no: str = "0000123",
    execution_no: str = "0000001",
    code: str = "005930",
    order_qty: int = 2,
    cumulative_qty: int = 1,
    received_at: str = "2026-08-14T10:01:02.345000+09:00",
    occurred_at: str = "2026-08-14T10:01:02.000000+09:00",
) -> dict[str, Any]:
    remaining_qty = order_qty - cumulative_qty
    return {
        "id": 701,
        "name": "SAMSUNG",
        "code": code,
        "main_lifecycle_broker_raw_envelope_schema": (
            "kiwoom_websocket_order_execution_00_values_v1"
        ),
        "main_lifecycle_broker_raw_source_type": "00",
        "broker_execution_received_at": received_at,
        "broker_execution_receive_time_source": BROKER_EXECUTION_RECEIVE_TIME_SOURCE,
        "broker_execution_observed_at": occurred_at,
        "broker_execution_time_source": "official_fid_908",
        "broker_actual_execution_venue": "KRX",
        "broker_actual_execution_venue_source": "official_fid_2134_2135",
        "broker_actual_exchange_code": "1",
        "broker_actual_exchange_name": "KRX",
        "broker_sor_flag": "N",
        "9203": order_no,
        "9001": code,
        "913": "체결",
        "900": str(order_qty),
        "902": str(remaining_qty),
        "903": str(cumulative_qty * 10_000),
        "905": "+매수",
        "907": "2",
        "908": datetime.fromisoformat(occurred_at).strftime("%H%M%S"),
        "909": execution_no,
        "910": "10000",
        "911": str(cumulative_qty),
        "914": "10000",
        "915": str(cumulative_qty),
        "2134": "1",
        "2135": "KRX",
        "2136": "N",
    }


def _exact_sell_execution_stock(
    *,
    order_no: str = "0000456",
    execution_no: str = "0000002",
    code: str = "005930",
    order_qty: int = 2,
    cumulative_qty: int = 1,
    received_at: str = "2026-08-14T10:01:02.345000+09:00",
    occurred_at: str = "2026-08-14T10:01:02.000000+09:00",
    intended_route: str = "SOR",
    intended_effective_venue: str = "KRX",
) -> dict[str, Any]:
    stock = _exact_buy_execution_stock(
        order_no=order_no,
        execution_no=execution_no,
        code=code,
        order_qty=order_qty,
        cumulative_qty=cumulative_qty,
        received_at=received_at,
        occurred_at=occurred_at,
    )
    stock.update(
        {
            "status": "SELL_ORDERED",
            "buy_qty": order_qty,
            "905": "-매도",
            "907": "1",
        }
    )
    if intended_route == "SOR":
        stock.update(
            {
                "broker_actual_execution_venue": "UNKNOWN",
                "broker_actual_execution_venue_source": (
                    "official_exchange_fields_ambiguous_or_missing"
                ),
                "broker_actual_exchange_code": "0",
                "broker_actual_exchange_name": "SOR",
                "broker_sor_flag": "Y",
                "2134": "0",
                "2135": "SOR",
                "2136": "Y",
            }
        )
    else:
        venue_code = "2" if intended_route == "NXT" else "1"
        stock.update(
            {
                "broker_actual_execution_venue": intended_route,
                "broker_actual_exchange_code": venue_code,
                "broker_actual_exchange_name": intended_route,
                "broker_sor_flag": "N",
                "2134": venue_code,
                "2135": intended_route,
                "2136": "N",
            }
        )
    started_at = datetime.fromisoformat(received_at).timestamp() - 0.2
    stock.update(
        state_handlers._new_sell_submit_context_fields(
            stock,
            code,
            requested_qty=order_qty,
            started_at=started_at,
            intended_route=intended_route,
            intended_effective_venue=intended_effective_venue,
            intended_session_bucket="krx_regular",
        )
    )
    return stock


def _valid_submit_event_payload(
    stock: dict[str, Any],
    *,
    marker_key: str,
    order_no: str = "0000123",
    requested_qty: int = 2,
) -> dict[str, Any]:
    pipeline, source_stage = {
        "_entry_lifecycle_submit_telemetry_committed_by_order_no": (
            "ENTRY_PIPELINE",
            "order_leg_sent",
        ),
        "_scale_in_lifecycle_submit_telemetry_committed_by_order_no": (
            "HOLDING_PIPELINE",
            "scale_in_order_leg_submitted",
        ),
    }[marker_key]
    source_fields: dict[str, Any] = {
        "qty": requested_qty,
        "requested_qty": requested_qty,
        "submitted_qty": requested_qty,
        "broker_order_no": order_no,
        "broker_order_no_list": order_no,
        "broker_order_qty_list": f"{order_no}:{requested_qty}",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "lifecycle_submission_leg_contract": "exact_broker_order_leg_v1",
        "lifecycle_submission_time_source": (
            "pipeline_emit_after_broker_success_response"
        ),
    }
    source_fields.update(
        pipeline_lifecycle_fields_safe(
            stock,
            stock["code"],
            pipeline=pipeline,
            source_stage=source_stage,
            source_fields=source_fields,
            observed_at="2026-08-14T10:01:01.000000+09:00",
        )
    )
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": source_stage,
        "stock_name": stock["name"],
        "stock_code": stock["code"],
        "record_id": stock["id"],
        "fields": {key: str(value) for key, value in source_fields.items()},
        "structured_append_succeeded": True,
        "structured_append_status": "raw_appended",
    }


def test_late_replacement_cancel_calls_broker_only_for_fresh_intent(monkeypatch):
    from src.engine import kiwoom_orders

    stock = _exact_sell_execution_stock(order_no="0000456", order_qty=2)
    stock["sell_odno"] = "0000456"
    assert execution_receipts.persist_pending_sell_submit_custody(stock)
    cancel_calls = []
    monkeypatch.setattr(execution_receipts, "KIWOOM_TOKEN", "TOKEN")
    monkeypatch.setattr(
        kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: cancel_calls.append(kwargs)
        or {
            "return_code": "0",
            "ord_no": "0000999",
            "base_orig_ord_no": "0000456",
            "cncl_qty": "2",
            "broker_route_attempted": True,
            "effective_dmst_stex_tp": "SOR",
            "cancel_request_api_id": "kt10003",
            "cancel_request_code": "005930",
            "cancel_request_orig_ord_no": "0000456",
            "cancel_request_qty": "0",
            "cancel_request_route": "SOR",
            "cancel_request_bound": True,
        },
    )

    assert execution_receipts._cancel_replacement_sell_once(
        stock,
        code="005930",
        order_no="0000456",
    )
    assert execution_receipts._cancel_replacement_sell_once(
        stock,
        code="005930",
        order_no="0000456",
    )

    assert len(cancel_calls) == 1
    assert cancel_calls[0]["orig_ord_no"] == "0000456"
    assert execution_receipts.pending_sell_cancel_ack_exact(
        stock,
        code="005930",
        order_no="0000456",
    )


@pytest.mark.parametrize(
    "marker_key",
    [
        "_entry_lifecycle_submit_telemetry_committed_by_order_no",
        "_scale_in_lifecycle_submit_telemetry_committed_by_order_no",
    ],
    ids=["entry", "scale_in"],
)
def test_failed_submit_row_keeps_receipt_predecessor_fallback_alive(
    monkeypatch: pytest.MonkeyPatch,
    marker_key: str,
) -> None:
    stock = _exact_buy_execution_stock()
    committed = state_handlers._record_lifecycle_submit_telemetry_if_raw_appended(
        stock,
        marker_key=marker_key,
        order_no="0000123",
        requested_qty=2,
        observed_at="2026-08-14T10:01:01.000000+09:00",
        decision_trace_id="trace-701",
        event_payload={
            "structured_append_succeeded": False,
            "structured_append_status": "raw_append_failed",
        },
    )

    assert committed is False
    assert marker_key not in stock
    assert (
        execution_receipts._lifecycle_submit_telemetry_committed(
            stock,
            marker_key=marker_key,
            order_no="0000123",
            requested_qty=2,
        )
        is False
    )
    monkeypatch.setattr(
        execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: {
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        },
    )
    assert (
        execution_receipts._emit_execution_receipt_submission_custody(
            target_stock=stock,
            target_id=701,
            code="005930",
            stage="entry_execution_receipt_submission_custody",
            order_no="0000123",
            execution_no="0000001",
            requested_qty=2,
        )
        is True
    )


@pytest.mark.parametrize(
    "marker_key",
    [
        "_entry_lifecycle_submit_telemetry_committed_by_order_no",
        "_scale_in_lifecycle_submit_telemetry_committed_by_order_no",
    ],
    ids=["entry", "scale_in"],
)
def test_successful_submit_row_commits_exact_receipt_suppression_marker(
    marker_key: str,
) -> None:
    stock = {
        **_exact_buy_execution_stock(),
        "scanner_promotion_id": "SCANPROM-005930-1787000000000",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }

    committed = state_handlers._record_lifecycle_submit_telemetry_if_raw_appended(
        stock,
        marker_key=marker_key,
        order_no="0000123",
        requested_qty=2,
        observed_at="2026-08-14T10:01:01.000000+09:00",
        decision_trace_id="trace-701",
        event_payload=_valid_submit_event_payload(stock, marker_key=marker_key),
    )

    assert committed is True
    assert (
        execution_receipts._lifecycle_submit_telemetry_committed(
            stock,
            marker_key=marker_key,
            order_no="0000123",
            requested_qty=2,
        )
        is True
    )
    assert stock[marker_key]["0000123"]["decision_trace_id"] == "trace-701"


def test_invalid_appended_submit_row_does_not_suppress_receipt_custody() -> None:
    marker_key = "_entry_lifecycle_submit_telemetry_committed_by_order_no"
    stock = {
        **_exact_buy_execution_stock(),
        "scanner_promotion_id": "SCANPROM-005930-1787000000000",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    event_payload = _valid_submit_event_payload(stock, marker_key=marker_key)
    event_payload["fields"]["main_lifecycle_id"] = "mlc-" + "0" * 32

    committed = state_handlers._record_lifecycle_submit_telemetry_if_raw_appended(
        stock,
        marker_key=marker_key,
        order_no="0000123",
        requested_qty=2,
        observed_at="2026-08-14T10:01:01.000000+09:00",
        decision_trace_id="trace-701",
        event_payload=event_payload,
    )

    assert committed is False
    assert marker_key not in stock


@pytest.mark.parametrize(
    ("event_payload", "expected"),
    [
        (
            {
                "structured_append_succeeded": True,
                "structured_append_status": "raw_appended",
            },
            True,
        ),
        (
            {
                "structured_append_succeeded": False,
                "structured_append_status": "jsonl_disabled",
            },
            False,
        ),
        (
            {
                "structured_append_succeeded": False,
                "structured_append_status": "raw_suppressed_by_compaction",
            },
            False,
        ),
        (
            {
                "structured_append_succeeded": False,
                "structured_append_status": "raw_append_failed",
            },
            False,
        ),
    ],
    ids=["raw_appended", "jsonl_disabled", "compaction_suppressed", "failed"],
)
def test_receipt_submission_custody_flag_matches_physical_raw_append(
    monkeypatch: pytest.MonkeyPatch,
    event_payload: dict[str, Any],
    expected: bool,
) -> None:
    monkeypatch.setattr(
        execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: event_payload,
    )

    emitted = execution_receipts._emit_execution_receipt_submission_custody(
        target_stock={
            **_exact_buy_execution_stock(),
        },
        target_id=701,
        code="005930",
        stage="entry_execution_receipt_submission_custody",
        order_no="0000123",
        execution_no="0000001",
        requested_qty=2,
    )

    assert emitted is expected


def test_receipt_submission_custody_orders_by_packet_ingress_and_retains_fid908_bound(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    events: list[dict[str, Any]] = []
    stock = {
        **_exact_buy_execution_stock(),
        "scanner_promotion_id": "SCANPROM-005930-1787000000000",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }

    def capture_event(
        pipeline: str,
        name: str,
        stock_code: str,
        stage: str,
        *,
        record_id: Any,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
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
        return {
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    monkeypatch.setattr(execution_receipts, "emit_pipeline_event", capture_event)
    monkeypatch.setattr(
        execution_receipts,
        "observe_candidate_transition_safe",
        lambda *args, **kwargs: None,
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

    append_source_stage(
        "ENTRY_PIPELINE",
        "scalping_scanner_fast_precheck",
        datetime.fromisoformat("2026-08-14T10:01:01.000000+09:00"),
        bbo_observed=True,
        depth_observed=True,
    )
    append_source_stage(
        "ENTRY_PIPELINE",
        "ai_confirmed",
        datetime.fromisoformat("2026-08-14T10:01:02.200000+09:00"),
        action="BUY",
        bbo_observed=True,
        depth_observed=True,
    )

    assert execution_receipts._emit_execution_receipt_submission_custody(
        target_stock=stock,
        target_id=701,
        code="005930",
        stage="entry_execution_receipt_submission_custody",
        order_no="0000123",
        execution_no="0000001",
        requested_qty=2,
    )
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "position_rebased_after_fill",
        candidate_stock=stock,
        observed_at=datetime.fromisoformat(stock["broker_execution_observed_at"]),
        fill_quality="PARTIAL_FILL",
        fill_qty=1,
        fill_price=10_000,
        requested_qty=2,
        **execution_receipts._broker_execution_provenance_fields(stock),
    )
    # The broker-response logger may resume only after the receipt thread has
    # already appended custody and fill.  Its exact ordinary submit row must
    # corroborate the receipt-bound order instead of invalidating the cycle as
    # a submit-after-fill transition.
    append_source_stage(
        "ENTRY_PIPELINE",
        "order_leg_sent",
        datetime.fromisoformat("2026-08-14T10:01:02.250000+09:00"),
        qty=2,
        requested_qty=2,
        submitted_qty=2,
        broker_order_no="0000123",
        broker_order_no_list="0000123",
        broker_order_qty_list="0000123:2",
        actual_order_submitted=True,
        broker_order_forbidden=False,
        lifecycle_submission_leg_contract="exact_broker_order_leg_v1",
        lifecycle_submission_time_source=(
            "pipeline_emit_after_broker_success_response"
        ),
        ai_decision_trace_id="trace-701",
        effective_venue="KRX",
        market_session_bucket="krx_regular",
    )

    assert [event["stage"] for event in events] == [
        "scalping_scanner_fast_precheck",
        "ai_confirmed",
        "entry_execution_receipt_submission_custody",
        "position_rebased_after_fill",
        "order_leg_sent",
    ]
    submit_fields = events[2]["fields"]
    fill_fields = events[3]["fields"]
    assert submit_fields["main_lifecycle_observed_at"] == (
        "2026-08-14T10:01:02.345000+09:00"
    )
    assert fill_fields["main_lifecycle_observed_at"] == (
        "2026-08-14T10:01:02.345000+09:00"
    )
    assert submit_fields["submission_causal_upper_bound_at"] == (
        "2026-08-14T10:01:02.000000+09:00"
    )
    assert submit_fields["submission_causal_upper_bound_source"] == ("official_fid_908")
    assert submit_fields["lifecycle_submission_ordering_clock"] == (
        "broker_execution_received_at"
    )
    transition, error, in_scope = _validated_pipeline_transition(
        events[2], target_date="2026-08-14"
    )
    assert error is None
    assert in_scope is True
    assert transition is not None
    assert transition["stage"] == "submit"
    assert transition["data"]["submission_custody_binding_schema"] == (
        "broker_execution_inferred_submission_binding_v1"
    )
    assert transition["data"]["submission_custody_broker_execution_no"] == ("0000001")
    late_submit, late_error, late_in_scope = _validated_pipeline_transition(
        events[4], target_date="2026-08-14"
    )
    assert late_error is None
    assert late_in_scope is True
    assert late_submit is not None
    assert late_submit["data"]["decision_trace_id"] == "trace-701"

    source = tmp_path / "same_second_receipt_custody.jsonl"
    source.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in events),
        encoding="utf-8",
    )
    report = build_daily_report(
        "2026-08-14",
        source_path=source,
        reviewed_cost_profile_sha256=COST_HASH,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256=SYMBOL_HASH,
        symbol_master_artifact_verified=True,
        write=False,
    )
    assert report["source_invalid_transition_count"] == 0
    assert report["broker_submission_custody_order_count"] == 1
    assert report["broker_submission_custody_pending_order_count"] == 0
    assert report["real_submitted_lifecycle_count"] == 1
    assert len(report["rows"]) == 1
    row = report["rows"][0]
    assert row["lifecycle_population_scope"] == "real_submitted"
    assert row["broker_submission_custody_order_count"] == 1
    assert row["broker_submission_custody_pending_order_count"] == 0
    assert "trace-701" in row["decision_trace_ids"]
    trace_contexts = [
        context
        for context in row["decision_trace_context_path"]
        if context["decision_trace_id"] == "trace-701"
    ]
    assert [context["stage"] for context in trace_contexts] == ["submit"]
    assert trace_contexts[0]["transition_count"] == 1
    assert "lifecycle_timestamp_regression" not in row["invalid_transition_reasons"]
    assert "fill_before_submit" not in row["invalid_transition_reasons"]
    assert "submit_after_fill_phase" not in row["invalid_transition_reasons"]


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("9203", "0000999"),
        ("9001", "000660"),
        ("909", "0000009"),
        ("900", "3"),
        ("902", "0"),
        ("907", "1"),
        ("broker_execution_receive_time_source", "handler_dispatch_fallback"),
    ],
)
def test_receipt_submission_custody_fails_closed_on_raw_binding_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    invalid_value: str,
) -> None:
    stock = _exact_buy_execution_stock()
    stock[field] = invalid_value
    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(
        execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: emitted.append(kwargs),
    )

    assert not execution_receipts._emit_execution_receipt_submission_custody(
        target_stock=stock,
        target_id=701,
        code="005930",
        stage="entry_execution_receipt_submission_custody",
        order_no="0000123",
        execution_no="0000001",
        requested_qty=2,
    )
    assert emitted == []


def test_exit_receipt_submission_custody_accepts_exact_integrated_sor_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(
        execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: (
            emitted.append(kwargs)
            or {
                "structured_append_succeeded": True,
                "structured_append_status": "raw_appended",
            }
        ),
    )
    stock = _exact_sell_execution_stock()

    assert execution_receipts._emit_execution_receipt_submission_custody(
        target_stock=stock,
        target_id=701,
        code="005930",
        stage="exit_execution_receipt_submission_custody",
        order_no="0000456",
        execution_no="0000002",
        requested_qty=2,
    )
    assert emitted[0]["submission_custody_broker_order_qty"] == 2
    assert emitted[0]["submission_custody_broker_cumulative_qty"] == 1
    assert emitted[0]["submission_custody_broker_remaining_qty"] == 1
    assert emitted[0]["submission_custody_broker_unit_qty"] == 1
    assert emitted[0]["effective_venue"] == "KRX"


def test_exit_receipt_submission_custody_materializes_as_exit_submit_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    stock = _exact_sell_execution_stock()
    stock.update(
        {
            "scanner_promotion_id": "SCANPROM-005930-1787000000000",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        }
    )

    def capture_event(
        pipeline: str,
        name: str,
        stock_code: str,
        stage: str,
        *,
        record_id: Any,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
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
        return {
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    monkeypatch.setattr(execution_receipts, "emit_pipeline_event", capture_event)
    monkeypatch.setattr(
        execution_receipts,
        "observe_candidate_transition_safe",
        lambda *args, **kwargs: None,
    )

    assert execution_receipts._emit_execution_receipt_submission_custody(
        target_stock=stock,
        target_id=701,
        code="005930",
        stage="exit_execution_receipt_submission_custody",
        order_no="0000456",
        execution_no="0000002",
        requested_qty=2,
    )
    transition, error, in_scope = _validated_pipeline_transition(
        captured,
        target_date="2026-08-14",
    )
    assert error is None
    assert in_scope is True
    assert transition is not None
    assert transition["stage"] == "exit"
    assert transition["data"]["actual_broker_order_submitted"] is True
    assert transition["data"]["broker_order_no"] == "0000456"
    assert transition["data"]["requested_qty"] == 2
    assert transition["data"]["submission_custody_broker_execution_no"] == ("0000002")


@pytest.mark.parametrize(
    "leg_contract",
    [None, "exact_broker_order_leg_v1"],
    ids=["missing_contract", "wrong_bundle_contract"],
)
def test_sell_order_sent_cannot_spoof_exit_receipt_custody(
    leg_contract: str | None,
) -> None:
    stock = {
        **_exact_sell_execution_stock(),
        "scanner_promotion_id": "SCANPROM-005930-1787000000000",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    fields: dict[str, Any] = {
        "qty": 2,
        "ord_no": "0000456",
        "actual_order_submitted": True,
        "submission_custody_binding_schema": (
            "broker_execution_inferred_submission_binding_v1"
        ),
        "submission_custody_broker_order_no": "0000456",
    }
    if leg_contract is not None:
        fields["lifecycle_submission_leg_contract"] = leg_contract
    fields.update(
        pipeline_lifecycle_fields_safe(
            stock,
            stock["code"],
            pipeline="HOLDING_PIPELINE",
            source_stage="sell_order_sent",
            source_fields=fields,
            observed_at="2026-08-14T10:01:02.500000+09:00",
        )
    )
    transition, error, in_scope = _validated_pipeline_transition(
        {
            "event_type": "pipeline_event",
            "pipeline": "HOLDING_PIPELINE",
            "stage": "sell_order_sent",
            "stock_name": stock["name"],
            "stock_code": stock["code"],
            "record_id": stock["id"],
            "fields": fields,
        },
        target_date="2026-08-14",
    )
    assert transition is None
    assert error == "pipeline_submission_custody_stage_invalid"
    assert in_scope is True


@pytest.mark.parametrize(
    "claim_field",
    SUBMISSION_CUSTODY_CLAIM_FIELD_NAMES,
)
def test_sell_order_sent_rejects_every_custody_claim_field(
    claim_field: str,
) -> None:
    stock = {
        **_exact_sell_execution_stock(),
        "scanner_promotion_id": "SCANPROM-005930-1787000000000",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    fields: dict[str, Any] = {
        "qty": 2,
        "requested_qty": 2,
        "submitted_qty": 2,
        "ord_no": "0000456",
        "broker_order_no": "0000456",
        "broker_order_no_list": "0000456",
        "broker_order_qty_list": "0000456:2",
        "actual_order_submitted": True,
        "lifecycle_submission_leg_contract": ("exact_broker_single_order_leg_v1"),
        claim_field: {"unhashable": True},
    }
    fields.update(
        pipeline_lifecycle_fields_safe(
            stock,
            stock["code"],
            pipeline="HOLDING_PIPELINE",
            source_stage="sell_order_sent",
            source_fields=fields,
            observed_at="2026-08-14T10:01:02.500000+09:00",
        )
    )

    transition, error, in_scope = _validated_pipeline_transition(
        {
            "event_type": "pipeline_event",
            "pipeline": "HOLDING_PIPELINE",
            "stage": "sell_order_sent",
            "stock_name": stock["name"],
            "stock_code": stock["code"],
            "record_id": stock["id"],
            "fields": fields,
        },
        target_date="2026-08-14",
    )
    assert transition is None
    assert error == "pipeline_submission_custody_stage_invalid"
    assert in_scope is True


def test_exit_receipt_custody_partial_final_then_late_submit_reconciles(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    events: list[dict[str, Any]] = []
    kst = timezone(timedelta(hours=9))
    base = datetime(2026, 8, 14, 10, 0, tzinfo=kst)
    stock = {
        **_exact_sell_execution_stock(
            order_qty=2,
            cumulative_qty=1,
            received_at=(base + timedelta(seconds=10, milliseconds=345)).isoformat(),
            occurred_at=(base + timedelta(seconds=10)).isoformat(),
        ),
        "id": 701,
        "scanner_promotion_id": "SCANPROM-005930-1787000000000",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
        "buy_price": 10_000,
        "buy_qty": 2,
    }

    def capture_event(
        pipeline: str,
        name: str,
        stock_code: str,
        stage: str,
        *,
        record_id: Any,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
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
        return {
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    def append_stage(
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

    append_stage(
        "ENTRY_PIPELINE",
        "scalping_scanner_fast_precheck",
        base,
        bbo_observed=True,
        depth_observed=True,
    )
    append_stage(
        "ENTRY_PIPELINE",
        "ai_confirmed",
        base + timedelta(seconds=1),
        action="BUY",
        bbo_observed=True,
        depth_observed=True,
    )
    append_stage(
        "ENTRY_PIPELINE",
        "order_leg_sent",
        base + timedelta(seconds=2),
        qty=2,
        requested_qty=2,
        submitted_qty=2,
        broker_order_no="0000123",
        broker_order_no_list="0000123",
        broker_order_qty_list="0000123:2",
        actual_order_submitted=True,
        lifecycle_submission_leg_contract="exact_broker_order_leg_v1",
        lifecycle_submission_time_source="pipeline_emit_after_broker_success_response",
    )
    append_stage(
        "ENTRY_PIPELINE",
        "order_bundle_submitted",
        base + timedelta(seconds=2, milliseconds=100),
        qty=2,
        requested_qty=2,
        submitted_qty=2,
        broker_order_no="0000123",
        broker_order_no_list="0000123",
        broker_order_qty_list="0000123:2",
        actual_order_submitted=True,
        lifecycle_submission_summary_only=True,
        submitted_leg_count=1,
    )
    entry_receipt = _exact_buy_execution_stock(
        order_no="0000123",
        execution_no="0000001",
        order_qty=2,
        cumulative_qty=2,
        received_at=(base + timedelta(seconds=3, milliseconds=100)).isoformat(),
        occurred_at=(base + timedelta(seconds=3)).isoformat(),
    )
    stock.update(entry_receipt)
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "position_rebased_after_fill",
        candidate_stock=stock,
        observed_at=base + timedelta(seconds=3, milliseconds=100),
        fill_quality="FULL_FILL",
        fill_qty=2,
        fill_price=10_000,
        requested_qty=2,
        **execution_receipts._broker_execution_provenance_fields(stock),
    )
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "holding_started",
        candidate_stock=stock,
        observed_at=base + timedelta(seconds=4),
    )

    exit_receipt = _exact_sell_execution_stock(
        order_qty=2,
        cumulative_qty=1,
        received_at=(base + timedelta(seconds=10, milliseconds=345)).isoformat(),
        occurred_at=(base + timedelta(seconds=10)).isoformat(),
    )
    stock.update(exit_receipt)
    assert execution_receipts._bind_pending_sell_execution_receipt(
        target_stock=stock,
        target_id=stock["id"],
        code=stock["code"],
        order_no="0000456",
        execution_no="0000002",
    )
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "sell_partial_fill_progress",
        candidate_stock=stock,
        observed_at=base + timedelta(seconds=10, milliseconds=345),
        main_lifecycle_exit_qty=1,
        main_lifecycle_exit_price=10_000,
        main_lifecycle_broker_reconciled=False,
        main_lifecycle_reconciled_final_exit=False,
        **execution_receipts._broker_execution_provenance_fields(stock),
        **execution_receipts._sell_execution_provenance_fields(stock),
    )

    final_receipt = _exact_sell_execution_stock(
        execution_no="0000003",
        order_qty=2,
        cumulative_qty=2,
        received_at=(base + timedelta(seconds=11, milliseconds=200)).isoformat(),
        occurred_at=(base + timedelta(seconds=11)).isoformat(),
    )
    final_receipt["915"] = "1"
    stock.update(final_receipt)
    execution_receipts._log_holding_pipeline(
        stock["name"],
        stock["code"],
        stock["id"],
        "sell_completed",
        candidate_stock=stock,
        observed_at=base + timedelta(seconds=11, milliseconds=200),
        main_lifecycle_exit_qty=1,
        main_lifecycle_exit_price=10_000,
        main_lifecycle_broker_reconciled=True,
        main_lifecycle_reconciled_final_exit=True,
        **execution_receipts._broker_execution_provenance_fields(stock),
        **execution_receipts._sell_execution_provenance_fields(stock),
    )
    append_stage(
        "HOLDING_PIPELINE",
        "sell_order_sent",
        base + timedelta(seconds=11, milliseconds=500),
        qty=2,
        requested_qty=2,
        submitted_qty=2,
        ord_no="0000456",
        broker_order_no="0000456",
        broker_order_no_list="0000456",
        broker_order_qty_list="0000456:2",
        actual_order_submitted=True,
        lifecycle_submission_leg_contract="exact_broker_single_order_leg_v1",
        lifecycle_submission_time_source="pipeline_emit_after_broker_success_response",
        effective_venue="KRX",
        market_session_bucket="krx_regular",
    )

    source = tmp_path / "exit_fill_before_submit.jsonl"
    source.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in events),
        encoding="utf-8",
    )
    report = build_daily_report(
        "2026-08-14",
        source_path=source,
        reviewed_cost_profile_sha256=COST_HASH,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256=SYMBOL_HASH,
        symbol_master_artifact_verified=True,
        write=False,
    )
    assert report["source_invalid_transition_count"] == 0
    assert len(report["rows"]) == 1
    row = report["rows"][0]
    assert row["terminal_state"] == "FINAL_EXIT_RECONCILED", {
        key: row.get(key)
        for key in (
            "invalid_transition_reasons",
            "broker_execution_provenance_state_counts",
            "broker_execution_provenance_gap_reasons",
            "broker_execution_order_progress_conflict_count",
            "broker_execution_submission_link_conflict_count",
            "exit_qty",
        )
    }
    assert row["broker_submission_custody_order_count"] == 1
    assert row["broker_submission_custody_pending_order_count"] == 0
    assert row["broker_submission_self_summarizing_contract_phases"] == ["exit"]
    assert row["broker_submission_summary_missing_phases"] == []
    assert row["broker_execution_submission_link_conflict_count"] == 0
    assert row["exit_qty"] == 2
    assert (
        "broker_submission_replay_context_conflict"
        not in row["invalid_transition_reasons"]
    )
    assert not any(
        str(blocker).startswith("broker_submission_summary_missing:")
        for blocker in row["promotion_blockers"]
    )


@pytest.mark.parametrize("execution_no", ["0", "1" * 21])
def test_exit_receipt_submission_custody_rejects_noncanonical_execution_no(
    monkeypatch: pytest.MonkeyPatch,
    execution_no: str,
) -> None:
    stock = _exact_sell_execution_stock(execution_no=execution_no)
    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(
        execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: emitted.append(kwargs),
    )

    assert not execution_receipts._emit_execution_receipt_submission_custody(
        target_stock=stock,
        target_id=stock["id"],
        code=stock["code"],
        stage="exit_execution_receipt_submission_custody",
        order_no="0000456",
        execution_no=execution_no,
        requested_qty=2,
    )
    assert emitted == []


def test_entry_bundle_cannot_use_exit_single_order_self_summary_contract() -> None:
    stock = _exact_buy_execution_stock()
    stock.update(
        {
            "scanner_promotion_id": "SCANPROM-005930-1787000000000",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        }
    )
    source_fields: dict[str, Any] = {
        "qty": 2,
        "requested_qty": 2,
        "submitted_qty": 2,
        "broker_order_no": "0000123",
        "broker_order_no_list": "0000123",
        "broker_order_qty_list": "0000123:2",
        "actual_order_submitted": True,
        "lifecycle_submission_leg_contract": ("exact_broker_single_order_leg_v1"),
    }
    source_fields.update(
        pipeline_lifecycle_fields_safe(
            stock,
            stock["code"],
            pipeline="ENTRY_PIPELINE",
            source_stage="order_bundle_submitted",
            source_fields=source_fields,
            observed_at="2026-08-14T10:01:01.000000+09:00",
        )
    )
    transition, error, in_scope = _validated_pipeline_transition(
        {
            "event_type": "pipeline_event",
            "pipeline": "ENTRY_PIPELINE",
            "stage": "order_bundle_submitted",
            "stock_name": stock["name"],
            "stock_code": stock["code"],
            "record_id": stock["id"],
            "fields": source_fields,
        },
        target_date="2026-08-14",
    )

    assert in_scope is True
    assert transition is None
    assert error == "pipeline_single_order_leg_contract_count_invalid"


@pytest.mark.parametrize(
    ("contract", "order_nos", "qty_list", "expected_scope", "expected_error"),
    [
        (
            None,
            "0000456",
            "0000456:2",
            True,
            "pipeline_sell_submit_contract_invalid",
        ),
        (
            "exact_broker_order_leg_v1",
            "0000456",
            "0000456:2",
            True,
            "pipeline_sell_submit_contract_invalid",
        ),
        (
            "exact_broker_single_order_leg_v1",
            "0000456,0000457",
            "0000456:1,0000457:1",
            True,
            "pipeline_single_order_leg_contract_count_invalid",
        ),
    ],
    ids=["missing", "bundle_contract", "multiple_orders"],
)
def test_sell_order_sent_requires_exact_single_order_contract(
    contract: str | None,
    order_nos: str,
    qty_list: str,
    expected_scope: bool,
    expected_error: str | None,
) -> None:
    stock = _exact_sell_execution_stock()
    stock.update(
        {
            "scanner_promotion_id": "SCANPROM-005930-1787000000000",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        }
    )
    source_fields: dict[str, Any] = {
        "qty": 2,
        "requested_qty": 2,
        "submitted_qty": 2,
        "broker_order_no": order_nos.split(",")[0],
        "broker_order_no_list": order_nos,
        "broker_order_qty_list": qty_list,
        "actual_order_submitted": True,
    }
    if contract is not None:
        source_fields["lifecycle_submission_leg_contract"] = contract
    source_fields.update(
        pipeline_lifecycle_fields_safe(
            stock,
            stock["code"],
            pipeline="HOLDING_PIPELINE",
            source_stage="sell_order_sent",
            source_fields=source_fields,
            observed_at="2026-08-14T10:01:01.000000+09:00",
        )
    )

    transition, error, in_scope = _validated_pipeline_transition(
        {
            "event_type": "pipeline_event",
            "pipeline": "HOLDING_PIPELINE",
            "stage": "sell_order_sent",
            "stock_name": stock["name"],
            "stock_code": stock["code"],
            "record_id": stock["id"],
            "fields": source_fields,
        },
        target_date="2026-08-14",
    )

    assert in_scope is expected_scope
    assert transition is None
    assert error == expected_error


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("committed", "receipt_proved"),
        ("append_gap", "receipt_proved_custody_gap"),
        ("response_conflict", "receipt_proof_response_order_conflict"),
        ("stale_generation", "stale_or_intervened"),
    ],
)
def test_sell_submit_response_race_classifier_is_exact(
    case: str,
    expected: str,
) -> None:
    stock: dict[str, Any] = {
        "id": 701,
        "code": "005930",
    }
    context = state_handlers._new_sell_submit_context_fields(
        stock,
        stock["code"],
        requested_qty=2,
        started_at=1_787_000_000.25,
        intended_route="SOR",
        intended_effective_venue="KRX",
        intended_session_bucket="krx_regular",
    )
    stock.update(context)
    generation = context["sell_submit_generation"]
    context_sha256 = context["sell_submit_context_sha256"]
    response_order_no = "0000456"
    if case != "stale_generation":
        stock["_sell_submit_receipt_proof"] = {
            "schema": "sell_submit_receipt_proof_v1",
            "generation": generation,
            "submit_context_sha256": context_sha256,
            "target_id": stock["id"],
            "code": stock["code"],
            "requested_qty": 2,
            "order_no": "0000456",
            "custody_emitted": case != "append_gap",
        }
    else:
        stock["sell_submit_generation"] = "intervening-generation"
    if case == "response_conflict":
        response_order_no = "0000999"

    assert (
        state_handlers._sell_submit_response_race_state(
            stock,
            generation=generation,
            context_sha256=context_sha256,
            requested_qty=2,
            response_order_no=response_order_no,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("response", "expected_state", "expected_order_no"),
    [
        ({"return_code": 0, "ord_no": "0000456"}, "success", "0000456"),
        ({"return_code": "0", "ord_no": "0000456"}, "success", "0000456"),
        ({"return_code": -1}, "definitive_reject", ""),
        ({"return_code": "-1"}, "definitive_reject", ""),
        ({"return_code": False, "ord_no": "0000456"}, "ambiguous", "0000456"),
        ({"return_code": "ERROR"}, "ambiguous", ""),
        (
            {
                "rt_cd": "-1",
                "err_msg": "매도가능수량 부족",
                "non_fatal_no_qty": True,
            },
            "ambiguous",
            "",
        ),
        (
            {"rt_cd": "-1", "err_msg": "매도가능수량 부족"},
            "ambiguous",
            "",
        ),
        (
            {"rt_cd": "-1", "err_msg": "일반 주문 거절"},
            "definitive_reject",
            "",
        ),
        ({"return_code": 0}, "ambiguous", ""),
        (None, "ambiguous", ""),
        (True, "ambiguous", ""),
    ],
)
def test_sell_submit_response_classifier_requires_explicit_numeric_ack(
    response: Any,
    expected_state: str,
    expected_order_no: str,
) -> None:
    result = state_handlers._classify_sell_submit_response(response)

    assert result["state"] == expected_state
    assert result["order_no"] == expected_order_no


def test_sell_submit_custody_append_gap_retries_from_durable_receipt_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stock = _exact_sell_execution_stock()
    assert execution_receipts.persist_pending_sell_submit_custody(stock)
    attempts: list[str] = []

    def append_custody(*args, **kwargs):
        del args
        attempts.append(str(kwargs.get("broker_order_no") or ""))
        if len(attempts) == 1:
            return None
        return {
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    monkeypatch.setattr(
        execution_receipts,
        "_log_holding_pipeline",
        append_custody,
    )
    assert not execution_receipts._bind_pending_sell_execution_receipt(
        target_stock=stock,
        target_id=stock["id"],
        code=stock["code"],
        order_no="0000456",
        execution_no="0000002",
    )
    stock[execution_receipts._SELL_EXECUTION_RECEIPT_STATE_KEY] = {
        "position_qty": 2,
        "aggregate_cumulative_qty": 1,
        "remaining_qty": 1,
        "final": False,
    }
    assert execution_receipts._persist_sell_receipt_recovery_or_interlock(
        stock,
        code=stock["code"],
        reason="test_append_gap_successor",
    )
    assert execution_receipts._sell_pending_submit_path(stock["id"]).exists()
    persisted_state, reason = execution_receipts.load_sell_receipt_recovery(
        target_id=stock["id"],
        code=stock["code"],
        position_qty=2,
        broker_remaining_qty=1,
    )
    assert reason == "journal_exact_match"
    assert isinstance(persisted_state, dict)
    assert (
        persisted_state["pending_submit_custody_retry_snapshot"][
            "_sell_submit_receipt_proof"
        ]["custody_emitted"]
        is False
    )

    original_retry = execution_receipts.retry_pending_sell_execution_receipt_custody
    monkeypatch.setattr(
        execution_receipts,
        "retry_pending_sell_execution_receipt_custody",
        lambda target: False,
    )
    blocked_restart = {
        "id": stock["id"],
        "code": stock["code"],
        "name": stock["name"],
        "buy_qty": 2,
        "buy_price": 10_000,
    }
    blocked_state, blocked_reason = sniper_sync._restore_sell_receipt_recovery(
        target_stock=blocked_restart,
        record=SimpleNamespace(id=stock["id"], buy_qty=2, scale_in_locked=True),
        code=stock["code"],
        broker_remaining_qty=1,
    )
    assert isinstance(blocked_state, dict)
    assert "submit_custody_append_retry_deferred" in blocked_reason
    assert blocked_restart["status"] == "SELL_ORDERED"
    assert blocked_restart["sell_cancel_reconciliation_required"] is True
    assert blocked_restart["sell_cancel_reconciliation_source"] == (
        "submit_custody_append_retry_deferred"
    )
    monkeypatch.setattr(
        execution_receipts,
        "retry_pending_sell_execution_receipt_custody",
        original_retry,
    )

    restarted = {
        "id": stock["id"],
        "code": stock["code"],
        "name": stock["name"],
        "buy_price": 10_000,
        execution_receipts._SELL_EXECUTION_RECEIPT_STATE_KEY: persisted_state,
    }
    assert execution_receipts.retry_pending_sell_execution_receipt_custody(restarted)
    assert len(attempts) == 2
    assert restarted["_sell_submit_receipt_proof"]["custody_emitted"] is True
    assert not execution_receipts._sell_pending_submit_path(stock["id"]).exists()
    rewritten_state, rewritten_reason = execution_receipts.load_sell_receipt_recovery(
        target_id=stock["id"],
        code=stock["code"],
        position_qty=2,
        broker_remaining_qty=1,
    )
    assert rewritten_reason == "journal_exact_match"
    assert isinstance(rewritten_state, dict)
    assert "pending_submit_custody_retry_snapshot" not in rewritten_state


def test_final_sell_receipt_never_commits_db_while_submit_custody_retry_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stock = _exact_sell_execution_stock(order_qty=1, cumulative_qty=1)
    stock.update(
        {
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 10_000,
            "exit_receipt_submission_custody_retry_required": True,
        }
    )
    db_calls: list[int] = []
    monkeypatch.setattr(
        execution_receipts,
        "_queue_sell_lifecycle_outbox_leg",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        execution_receipts,
        "_update_db_for_sell",
        lambda *args, **kwargs: db_calls.append(1) or True,
    )

    execution_receipts._finalize_standard_sell_execution(
        target_id=stock["id"],
        exec_price=10_100,
        now=datetime.fromisoformat(stock["broker_execution_received_at"]),
        target_stock=stock,
        strategy="SCALPING",
        is_scalp_revive=False,
        code=stock["code"],
        sell_receipt={
            "status": "final",
            "final": True,
            "expected_qty": 1,
            "cumulative_qty": 1,
            "cumulative_amount": 10_100,
            "cumulative_net_pnl_krw": 90.0,
            "incremental_qty": 1,
            "incremental_price": 10_100.0,
            "incremental_net_pnl_krw": 90.0,
            "economics_complete": True,
            "quantity_contract_complete": True,
            "unit_fill_consistent": True,
            "execution_no": "0000002",
        },
        order_no="0000456",
        safe_buy_price=10_000.0,
    )

    assert db_calls == []
    assert stock["status"] == "SELL_ORDERED"
    assert (
        stock[execution_receipts._SELL_EXECUTION_RECEIPT_STATE_KEY][
            "final_pending_db_commit"
        ]
        is True
    )


def test_partial_residual_submit_uses_original_db_owner_and_is_fresh_only() -> None:
    record = SimpleNamespace(
        id=701,
        stock_code="005930",
        buy_qty=10,
        status="HOLDING",
        scale_in_locked=True,
    )

    class Query:
        def __init__(self, row):
            self.row = row
            self.filters: dict[str, Any] = {}

        def filter_by(self, **kwargs):
            self.filters.update(kwargs)
            return self

        def filter(self, *args, **kwargs):
            del args, kwargs
            return self

        def update(self, values):
            if self.row is None:
                return 0
            if any(
                getattr(self.row, key, None) != value
                for key, value in self.filters.items()
            ):
                return 0
            if "status" not in self.filters and self.row.status != "HOLDING":
                return 0
            for key, value in values.items():
                setattr(self.row, key, value)
            return 1

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def query(self, *args, **kwargs):
            del args, kwargs
            return Query(record)

    class DB:
        @staticmethod
        def get_session():
            return Session()

    stock = {
        "id": 701,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "buy_qty": 6,
        execution_receipts._SELL_EXECUTION_RECEIPT_STATE_KEY: {
            "position_qty": 10,
            "aggregate_cumulative_qty": 4,
            "remaining_qty": 6,
            "final": False,
        },
    }
    stock.update(
        state_handlers._new_sell_submit_context_fields(
            stock,
            stock["code"],
            requested_qty=6,
            started_at=datetime.now(timezone(timedelta(hours=9))).timestamp(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )

    assert stock["sell_submit_owner_position_qty"] == 10
    assert state_handlers._persist_sell_submit_pre_call_boundary(
        stock,
        stock["code"],
        target_id=stock["id"],
        db=DB(),
    )
    assert record.status == "SELL_ORDERED"
    restored, reason = execution_receipts.load_pending_sell_submit_custody(
        target_id=701,
        code="005930",
        position_qty=10,
    )
    assert reason == "pending_submit_journal_exact_match"
    assert restored["sell_submit_owner_position_qty"] == 10
    assert restored["sell_submit_requested_qty"] == 6

    # Reentry with the already-fsynced generation is reconciliation-only and
    # cannot become a second broker-call authority.
    assert not state_handlers._persist_sell_submit_pre_call_boundary(
        stock,
        stock["code"],
        target_id=stock["id"],
        db=DB(),
    )
    assert record.status == "SELL_ORDERED"


def test_sell_submit_pre_call_boundary_requires_exact_db_owner() -> None:
    stock = {"id": 701, "code": "005930", "buy_qty": 1, "status": "HOLDING"}
    stock.update(
        state_handlers._new_sell_submit_context_fields(
            stock,
            stock["code"],
            requested_qty=1,
            started_at=datetime.now(timezone(timedelta(hours=9))).timestamp(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )

    assert not state_handlers._persist_sell_submit_pre_call_boundary(
        stock,
        stock["code"],
        target_id=stock["id"],
        db=None,
    )
    assert not execution_receipts._sell_pending_submit_path(stock["id"]).exists()
    assert stock["sell_cancel_reconciliation_required"] is True


def test_definitive_reject_terminal_outcome_recovers_crash_after_db_rollback() -> None:
    record = SimpleNamespace(
        id=702,
        stock_code="005930",
        buy_qty=3,
        status="SELL_ORDERED",
        scale_in_locked=True,
    )

    class Query:
        def __init__(self) -> None:
            self.filters: dict[str, Any] = {}

        def filter_by(self, **kwargs):
            self.filters.update(kwargs)
            return self

        def update(self, values):
            if any(
                getattr(record, key, None) != value
                for key, value in self.filters.items()
            ):
                return 0
            for key, value in values.items():
                setattr(record, key, value)
            return 1

        def first(self):
            if any(
                getattr(record, key, None) != value
                for key, value in self.filters.items()
            ):
                return None
            return record

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def query(self, *_args, **_kwargs):
            return Query()

    class DB:
        @staticmethod
        def get_session():
            return Session()

    stock = {
        "id": 702,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "SELL_ORDERED",
        "buy_qty": 3,
    }
    stock.update(
        state_handlers._new_sell_submit_context_fields(
            stock,
            stock["code"],
            requested_qty=3,
            started_at=datetime.now(timezone(timedelta(hours=9))).timestamp(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    generation = stock["sell_submit_generation"]
    assert execution_receipts.persist_pending_sell_submit_custody(stock)
    assert execution_receipts.persist_pending_sell_definitive_reject_outcome(
        stock,
        generation=generation,
    )

    # Crash point: DB rollback committed, but the common journal was not yet
    # unlinked. A fresh runtime target must finish this exact generation.
    record.status = "HOLDING"
    restored_fields, reason = execution_receipts.load_pending_sell_submit_custody(
        target_id=record.id,
        code=record.stock_code,
        position_qty=record.buy_qty,
    )
    assert reason == "pending_submit_journal_exact_match"
    restarted = {
        "id": record.id,
        "code": record.stock_code,
        "name": "SAMSUNG",
        "status": "HOLDING",
        "buy_qty": record.buy_qty,
        **restored_fields,
    }

    assert state_handlers._finish_definitive_sell_reject_boundary(
        restarted,
        record.stock_code,
        target_id=record.id,
        generation=generation,
        db=DB(),
    )
    assert record.status == "HOLDING"
    assert restarted["status"] == "HOLDING"
    assert "sell_submit_generation" not in restarted
    assert not execution_receipts._sell_pending_submit_path(record.id).exists()


@pytest.mark.parametrize("persist_ack", [True, False])
def test_cancel_terminal_outcome_recovers_crash_after_db_holding(
    persist_ack: bool,
) -> None:
    record = SimpleNamespace(
        id=703,
        stock_code="005930",
        buy_qty=3,
        status="SELL_ORDERED",
        scale_in_locked=True,
    )

    class Query:
        def __init__(self) -> None:
            self.filters: dict[str, Any] = {}

        def filter_by(self, **kwargs):
            self.filters.update(kwargs)
            return self

        def update(self, values):
            if any(
                getattr(record, key, None) != value
                for key, value in self.filters.items()
            ):
                return 0
            for key, value in values.items():
                setattr(record, key, value)
            return 1

        def first(self):
            if any(
                getattr(record, key, None) != value
                for key, value in self.filters.items()
            ):
                return None
            return record

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            del exc_type, exc, tb
            return False

        def query(self, *_args, **_kwargs):
            return Query()

    class DB:
        @staticmethod
        def get_session():
            return Session()

    stock = {
        "id": record.id,
        "code": record.stock_code,
        "name": "SAMSUNG",
        "status": "SELL_ORDERED",
        "buy_qty": record.buy_qty,
        "sell_odno": "0000456",
    }
    stock.update(
        state_handlers._new_sell_submit_context_fields(
            stock,
            stock["code"],
            requested_qty=3,
            started_at=datetime.now(timezone(timedelta(hours=9))).timestamp(),
            intended_route="SOR",
            intended_effective_venue="KRX",
            intended_session_bucket="krx_regular",
        )
    )
    generation = stock["sell_submit_generation"]
    assert execution_receipts.persist_pending_sell_submit_custody(stock)
    assert execution_receipts.persist_pending_sell_cancel_intent_custody(
        stock,
        order_no="0000456",
        broker_route="SOR",
    )
    if persist_ack:
        assert execution_receipts.persist_pending_sell_cancel_ack_custody(
            stock,
            order_no="0000456",
            cancel_response={
                "return_code": "0",
                "ord_no": "0000999",
                "base_orig_ord_no": "0000400",
                "cncl_qty": "3",
                "broker_route_attempted": True,
                "effective_dmst_stex_tp": "SOR",
                "cancel_request_api_id": "kt10003",
                "cancel_request_code": "005930",
                "cancel_request_orig_ord_no": "0000456",
                "cancel_request_qty": "0",
                "cancel_request_route": "SOR",
                "cancel_request_bound": True,
            },
        )
    stock["sell_reconciled_remaining_qty"] = 3
    assert execution_receipts.persist_pending_sell_cancel_terminal_outcome(
        stock,
        generation=generation,
        order_no="0000456",
        broker_remaining_qty=3,
        reconciliation_source="kt00018_position_found",
    )
    assert stock["sell_submit_terminal_outcome_kind"] == (
        "cancel_ack_terminal_absence_reconciled"
        if persist_ack
        else "cancel_intent_terminal_absence_reconciled"
    )

    # Crash point: exact DB HOLDING committed while the terminal generation
    # remains fsynced. Startup may finish only this generation.
    record.status = "HOLDING"
    restored_fields, reason = execution_receipts.load_pending_sell_submit_custody(
        target_id=record.id,
        code=record.stock_code,
        position_qty=record.buy_qty,
    )
    assert reason == "pending_submit_journal_exact_match"
    restarted = {
        "id": record.id,
        "code": record.stock_code,
        "name": "SAMSUNG",
        "status": "HOLDING",
        "buy_qty": record.buy_qty,
        "sell_odno": "0000456",
        **restored_fields,
    }

    assert state_handlers._finish_cancel_terminal_outcome_after_db_holding(
        restarted,
        record.stock_code,
        target_id=record.id,
        generation=generation,
        db=DB(),
    )
    assert record.status == "HOLDING"
    assert restarted["status"] == "HOLDING"
    assert "sell_submit_generation" not in restarted
    assert not execution_receipts._sell_pending_submit_path(record.id).exists()


@pytest.mark.parametrize(
    ("mutator", "case"),
    [
        (lambda stock: stock.update({"900": "3"}), "order_qty"),
        (lambda stock: stock.update({"911": "2"}), "cumulative_qty"),
        (lambda stock: stock.update({"902": "0"}), "remaining_qty"),
        (lambda stock: stock.update({"915": "2"}), "unit_qty"),
        (lambda stock: stock.update({"909": "9999999"}), "execution_no"),
        (lambda stock: stock.update({"907": "2"}), "side"),
        (
            lambda stock: stock.update(
                {"broker_execution_receive_time_source": "handler_dispatch_fallback"}
            ),
            "receive_clock",
        ),
        (
            lambda stock: stock.update({"sell_submit_generation": "wrong-generation"}),
            "generation_hash",
        ),
        (
            lambda stock: stock.update(
                {
                    "broker_execution_observed_at": (
                        "2026-08-14T10:01:01.000000+09:00"
                    ),
                    "908": "100101",
                }
            ),
            "old_fid908",
        ),
        (
            lambda stock: stock.update(
                {
                    "2135": "NXT",
                    "broker_actual_exchange_name": "NXT",
                }
            ),
            "sor_triplet_conflict",
        ),
        (
            lambda stock: stock.update(
                {
                    "sell_submit_intended_route": "NXT",
                    "sell_submit_intended_effective_venue": "NXT",
                }
            ),
            "route_context_hash",
        ),
    ],
    ids=[
        "order_qty",
        "cumulative_qty",
        "remaining_qty",
        "unit_qty",
        "execution_no",
        "side",
        "receive_clock",
        "generation_hash",
        "old_fid908",
        "sor_triplet_conflict",
        "route_context_hash",
    ],
)
def test_exit_receipt_submission_custody_rejects_raw_or_context_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    mutator,
    case: str,
) -> None:
    del case
    stock = _exact_sell_execution_stock()
    mutator(stock)
    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(
        execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: emitted.append(kwargs),
    )

    assert not execution_receipts._emit_execution_receipt_submission_custody(
        target_stock=stock,
        target_id=701,
        code="005930",
        stage="exit_execution_receipt_submission_custody",
        order_no="0000456",
        execution_no="0000002",
        requested_qty=2,
    )
    assert emitted == []


@pytest.mark.parametrize(
    "case",
    ["order_qty", "order_no", "session", "sor_triplet"],
)
def test_invalid_exit_receipt_never_binds_or_clears_pending_submit(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    stock = _exact_sell_execution_stock()
    bind_order_no = "0000456"
    if case == "order_qty":
        stock["900"] = "3"
    elif case == "order_no":
        bind_order_no = "0000999"
    elif case == "session":
        stock.update(
            state_handlers._new_sell_submit_context_fields(
                stock,
                stock["code"],
                requested_qty=2,
                started_at=(
                    datetime.fromisoformat(
                        stock["broker_execution_received_at"]
                    ).timestamp()
                    - 0.2
                ),
                intended_route="SOR",
                intended_effective_venue="KRX",
                intended_session_bucket="nxt_entry_window",
            )
        )
    else:
        stock.update(
            {
                "2135": "NXT",
                "broker_actual_exchange_name": "NXT",
            }
        )
    generation = stock["sell_submit_generation"]
    requested_qty = stock["sell_submit_requested_qty"]
    started_at = stock["sell_submit_started_at"]
    monkeypatch.setattr(
        execution_receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: pytest.fail("invalid custody must not emit"),
    )

    assert not execution_receipts._bind_pending_sell_execution_receipt(
        target_stock=stock,
        target_id=stock["id"],
        code=stock["code"],
        order_no=bind_order_no,
        execution_no="0000002",
    )
    assert stock["sell_submit_pending"] is True
    assert stock["sell_submit_generation"] == generation
    assert stock["sell_submit_requested_qty"] == requested_qty
    assert stock["sell_submit_started_at"] == started_at
    assert "sell_odno" not in stock
    assert "_sell_submit_receipt_proof" not in stock


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
    ) -> dict[str, Any]:
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
        return {
            "pipeline": pipeline,
            "stage": stage,
            "stock_name": name,
            "stock_code": stock_code,
            "record_id": record_id,
            "fields": {str(key): str(value) for key, value in fields.items()},
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

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
        "scanner_promotion_id": "SCANPROM-005930-1787000000000",
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
        attempt_id=stock["scanner_promotion_id"],
    )
    assert transition["attempt_id"] == stock["scanner_promotion_id"]
    assert transition["stage"] == "fill"
    assert transition["data"]["fill_state"] == "full"
    assert transition["data"]["broker_execution_provenance_state"] == "missing"
    assert transition["data"]["broker_execution_official_reference_sha"] == (
        "69642586f7d84ba9fd8a6faf1f1537c7fda6568b"
    )
    # Receipt rows must not inherit a stale position-level entry trace.  The
    # live receipt handler passes the immutable order-bound trace explicitly
    # when the per-order submit marker exists.
    assert "decision_trace_id" not in transition["data"]
    assert transition["observed_at"] == broker_observed_at.replace(
        tzinfo=timezone(timedelta(hours=9))
    ).isoformat(timespec="microseconds")
    assert fields["main_lifecycle_runtime_effect"] is False
    assert fields["main_lifecycle_order_authority"] is False
    assert fields["main_lifecycle_provider_authority"] is False

    required_snapshot_keys = {
        "id",
        "scanner_promotion_id",
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
    ) -> dict[str, Any]:
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
        return {
            "pipeline": pipeline,
            "stage": stage,
            "stock_name": name,
            "stock_code": stock_code,
            "record_id": record_id,
            "fields": {str(key): str(value) for key, value in fields.items()},
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

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
    assert row["actual_holding_duration_sec"] is None
    assert row["duration_source"] is None
    assert "official_first_fill_to_final_exit_duration_required" in (
        row["promotion_blockers"]
    )
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


def test_prior_day_carry_in_preserves_exact_nxt_exit_receipt_without_entry_fill(
    tmp_path: Path,
) -> None:
    events: list[dict[str, Any]] = []
    kst = timezone(timedelta(hours=9))
    carry_entry_at = datetime(2026, 8, 25, 15, 10, tzinfo=kst)
    holding_at = datetime(2026, 8, 26, 7, 55, tzinfo=kst)
    exit_submit_at = datetime(2026, 8, 26, 8, 5, tzinfo=kst)
    exit_received_at = datetime(2026, 8, 26, 8, 5, 1, tzinfo=kst)
    exit_occurred_at = datetime(2026, 8, 26, 8, 5, 0, tzinfo=kst)
    stock = {
        "id": 1001,
        "code": "225570",
        "name": "CARRY",
        "scanner_generation_id": "carry-attempt-1001",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
        "buy_time": carry_entry_at,
    }

    def append_stage(stage: str, observed_at: datetime, **source_fields: Any) -> None:
        fields = dict(source_fields)
        fields.update(
            pipeline_lifecycle_fields_safe(
                stock,
                stock["code"],
                pipeline="HOLDING_PIPELINE",
                source_stage=stage,
                source_fields=fields,
                observed_at=observed_at,
            )
        )
        events.append(
            {
                "event_type": "pipeline_event",
                "pipeline": "HOLDING_PIPELINE",
                "stage": stage,
                "stock_name": stock["name"],
                "stock_code": stock["code"],
                "record_id": stock["id"],
                "fields": fields,
            }
        )

    append_stage(
        "holding_started",
        holding_at,
        pipeline_lifecycle_population_scope="real_record_bound",
        holding_context_venue="KRX",
        holding_context_session="krx_regular",
        bbo_observed=True,
        depth_observed=True,
    )
    append_stage(
        "sell_order_sent",
        exit_submit_at,
        pipeline_lifecycle_population_scope="real_record_bound",
        holding_context_venue="NXT",
        holding_context_session="nxt_premarket",
        qty=1,
        requested_qty=1,
        submitted_qty=1,
        broker_order_no="0001566",
        broker_order_no_list="0001566",
        broker_order_qty_list="0001566:1",
        actual_order_submitted=True,
        lifecycle_submission_leg_contract="exact_broker_single_order_leg_v1",
        lifecycle_submission_time_source=(
            "pipeline_emit_after_broker_success_response"
        ),
    )
    receipt = _exact_sell_execution_stock(
        order_no="0001566",
        execution_no="0000008",
        code=stock["code"],
        order_qty=1,
        cumulative_qty=1,
        received_at=exit_received_at.isoformat(),
        occurred_at=exit_occurred_at.isoformat(),
        intended_route="NXT",
        intended_effective_venue="NXT",
    )
    receipt.update(
        {
            "903": "10380",
            "910": "10380",
            "914": "10380",
            "pipeline_lifecycle_population_scope": "real_record_bound",
            "holding_context_venue": "NXT",
            "holding_context_session": "nxt_premarket",
            "main_lifecycle_exit_qty": 1,
            "main_lifecycle_exit_price": 10_380,
            "main_lifecycle_broker_reconciled": True,
            "main_lifecycle_reconciled_final_exit": True,
            "main_lifecycle_fees_taxes_krw": 3,
            "main_lifecycle_slippage_krw": 1,
            "main_lifecycle_slippage_basis_price": 10_380,
            "main_lifecycle_slippage_basis_source": "exact_exit_receipt",
            "main_lifecycle_realized_net_pnl_krw": 10,
        }
    )
    append_stage("sell_completed", exit_received_at, **receipt)

    source = tmp_path / "carry-pipeline.jsonl"
    source.write_text(
        "".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in events),
        encoding="utf-8",
    )
    report = build_daily_report(
        "2026-08-26",
        source_path=source,
        reviewed_cost_profile_sha256=COST_HASH,
        reviewed_cost_profile_verified=True,
        symbol_master_artifact_sha256=SYMBOL_HASH,
        symbol_master_artifact_verified=True,
        write=False,
    )

    assert report["source_invalid_transition_count"] == 0
    assert report["custody_carry_lifecycle_count"] == 1
    assert report["custody_carry_final_exit_reconciled_count"] == 1
    row = report["rows"][0]
    assert row["terminal_state"] == "CUSTODY_CARRY_FINAL_EXIT_RECONCILED"
    assert row["lifecycle_origin"] == "preexisting_position_custody"
    assert row["carry_in_entry_source"] == "stock.buy_time"
    assert row["entry_fill_qty"] == 0.0
    assert row["broker_execution_unique_count"] == 1
    assert row["broker_execution_exit_covered_qty"] == 1.0
    assert row["exit_qty"] == 1.0
    assert row["promotion_evidence_eligible"] is False
    assert (
        "custody_carry_in_entry_lifecycle_non_promotable" in row["promotion_blockers"]
    )


def test_partial_exit_and_runner_preserve_capital_time_and_leg_slippage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    events: list[dict[str, Any]] = []
    kst = timezone(timedelta(hours=9))
    started_at = datetime(2026, 8, 15, 9, 0, tzinfo=kst)

    original_broker_execution_context = execution_receipts._broker_execution_context
    monkeypatch.setattr(
        execution_receipts,
        "_broker_execution_context",
        lambda exec_data, *, received_at: original_broker_execution_context(
            {
                **exec_data,
                "broker_execution_received_at": (
                    started_at + timedelta(seconds=10)
                ).isoformat(),
                "broker_execution_receive_time_source": (
                    BROKER_EXECUTION_RECEIVE_TIME_SOURCE
                ),
            },
            received_at=started_at + timedelta(seconds=10),
        ),
    )
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
    ) -> dict[str, Any]:
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
        return {
            "pipeline": pipeline,
            "stage": stage,
            "stock_name": name,
            "stock_code": stock_code,
            "record_id": record_id,
            "fields": {str(key): str(value) for key, value in fields.items()},
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

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
    monkeypatch.setattr(execution_receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
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
    append_source_stage(
        "HOLDING_PIPELINE",
        "sell_order_sent",
        started_at + timedelta(seconds=5, milliseconds=100),
        qty=4,
        requested_qty=4,
        submitted_qty=4,
        ord_no="0000902",
        broker_order_no="0000902",
        broker_order_no_list="0000902",
        broker_order_qty_list="0000902:4",
        actual_order_submitted=True,
        lifecycle_submission_leg_contract="exact_broker_single_order_leg_v1",
        lifecycle_submission_time_source=(
            "pipeline_emit_after_broker_success_response"
        ),
        effective_venue="NXT",
        market_session_bucket="nxt_aftermarket",
    )

    execution_receipts._handle_nxt_rising_missed_tp1_partial_sell_execution(
        target_id=stock["id"],
        target_stock=stock,
        code=stock["code"],
        order_no="0000902",
        exec_price=10_020,
        exec_qty=2,
        order_qty=4,
        remaining_qty=2,
        cumulative_exec_amount=20_040,
        execution_no="0000002",
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
        order_no="0000902",
        exec_price=10_020,
        exec_qty=4,
        order_qty=4,
        remaining_qty=0,
        cumulative_exec_amount=40_080,
        execution_no="0000003",
        unit_exec_price=10_020,
        unit_exec_qty=2,
        now=(started_at + timedelta(seconds=7)).replace(tzinfo=None),
        safe_buy_price=10_000,
    )
    assert record.buy_qty == 10
    assert stock["buy_qty"] == 6

    append_source_stage(
        "HOLDING_PIPELINE",
        "sell_order_sent",
        started_at + timedelta(seconds=8),
        qty=6,
        requested_qty=6,
        submitted_qty=6,
        ord_no="0000903",
        broker_order_no="0000903",
        broker_order_no_list="0000903",
        broker_order_qty_list="0000903:6",
        actual_order_submitted=True,
        lifecycle_submission_leg_contract="exact_broker_single_order_leg_v1",
        lifecycle_submission_time_source=(
            "pipeline_emit_after_broker_success_response"
        ),
        effective_venue="KRX",
        market_session_bucket="krx_regular",
    )
    stock["status"] = "SELL_ORDERED"
    stock["sell_odno"] = "0000903"
    execution_receipts.handle_real_execution(
        {
            "code": stock["code"],
            "type": "SELL",
            "order_no": "0000903",
            "price": 10_010,
            "qty": 6,
            "order_qty": 6,
            "remaining_qty": 0,
            "cumulative_exec_amount": 60_060,
            "execution_no": "0000004",
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
    assert row["actual_holding_duration_sec"] is None
    assert row["duration_source"] is None
    assert "official_first_fill_to_final_exit_duration_required" in (
        row["promotion_blockers"]
    )
    assert row["session_exposure_sec"] == 10.0
    assert row["exit_qty"] == 10.0
    assert row["open_qty_at_censor"] == 0.0
    assert row["exit_execution_leg_count"] == 3
    assert row["broker_execution_submission_link_conflict_count"] == 0
    assert row["broker_submission_self_summarizing_contract_phases"] == ["exit"]
    assert row["broker_submission_summary_missing_phases"] == []
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
