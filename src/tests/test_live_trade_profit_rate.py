from dataclasses import replace
from datetime import datetime, timedelta, timezone
import threading

import pytest

import src.engine.sniper_execution_receipts as receipts
import src.engine.sniper_s15_fast_track as s15
import src.engine.sniper_sync as sniper_sync
import src.engine.sniper_state_handlers as state_handlers
from src.engine.scalping.main_lifecycle_journal import (
    build_broker_execution_provenance,
    pipeline_lifecycle_fields_safe,
)
from src.engine.scalping import main_lifecycle_paired as paired
from src.engine.trade_profit import (
    calculate_net_profit_rate,
    calculate_net_realized_pnl,
)
from src.utils.constants import TRADING_RULES as CONFIG


class _Bus:
    def __init__(self):
        self.events = []

    def publish(self, topic, payload):
        self.events.append((topic, payload))


class _ReceiptSession:
    def __init__(self, record):
        self.record = record

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.record

    def update(self, values):
        for key, value in values.items():
            setattr(self.record, key, value)
        return 1

    def flush(self):
        return None

    def commit(self):
        return None


class _ReceiptDB:
    def __init__(self, record):
        self.record = record

    def get_session(self):
        return _ReceiptSession(self.record)


def _completed_sell_receipt_fields(
    *, buy_price: float, sell_price: float, qty: int
) -> dict:
    realized_net_pnl_krw = calculate_net_realized_pnl(buy_price, sell_price, qty)
    return {
        "sell_execution_expected_qty": qty,
        "sell_execution_cumulative_qty": qty,
        "sell_execution_cumulative_amount": int(sell_price * qty),
        "sell_execution_cumulative_net_pnl_krw": realized_net_pnl_krw,
        "sell_execution_final_leg_qty": qty,
        "sell_execution_final_leg_price": sell_price,
        "sell_execution_final_leg_net_pnl_krw": realized_net_pnl_krw,
        "sell_execution_receipt_economics_complete": True,
    }


def _install_successful_sell_lifecycle_outbox(monkeypatch, logged):
    """Capture a lifecycle append while satisfying the durable ack boundary."""

    def _capture(*args, **kwargs):
        logged.append((args[3], kwargs))
        return {
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    monkeypatch.setattr(receipts, "_log_holding_pipeline", _capture)
    monkeypatch.setattr(
        receipts,
        "_sell_lifecycle_outbox_event_contract_valid",
        lambda **_kwargs: True,
    )


def test_sell_lifecycle_outbox_ack_requires_every_durable_field_exact(
    monkeypatch,
):
    observed_at = datetime(
        2026, 8, 26, 9, 0, 3, 250_000, tzinfo=timezone(timedelta(hours=9))
    )
    leg = receipts._build_sell_lifecycle_outbox_leg(
        {
            "id": 7,
            "code": "123456",
            "name": "EXACT",
            "scanner_promotion_id": "promotion-7",
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        code="123456",
        target_id=7,
        now=observed_at,
        stage="sell_partial_fill_progress",
        event_fields={
            "cumulative_sell_qty": 2,
            "remaining_sell_qty": 8,
            "main_lifecycle_exit_qty": 2,
            "main_lifecycle_exit_price": 10_010.0,
            "main_lifecycle_broker_reconciled": False,
            "main_lifecycle_reconciled_final_exit": False,
            "main_lifecycle_realized_net_pnl_krw": 12.34,
            "broker_execution_no": "0000001",
            "broker_execution_identity": "bex-exact-1",
            "broker_execution_provenance_state": "complete",
            "909": "0000001",
            "actual_order_submitted": True,
            "broker_order_forbidden": False,
            "runtime_effect": True,
        },
    )
    tamper = {"field": None}

    def _emit(pipeline, name, code, stage, *, record_id=None, fields=None):
        normalized = {str(key): str(value) for key, value in (fields or {}).items()}
        if tamper["field"]:
            normalized[str(tamper["field"])] = "tampered"
        return {
            "pipeline": pipeline,
            "stage": stage,
            "stock_name": name,
            "stock_code": code,
            "record_id": record_id,
            "fields": normalized,
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    monkeypatch.setattr(receipts, "emit_pipeline_event", _emit)

    assert receipts._emit_standard_sell_partial_lifecycle_outbox_leg(leg) is True
    for changed_field in (
        "cumulative_sell_qty",
        "main_lifecycle_realized_net_pnl_krw",
        "909",
    ):
        tamper["field"] = changed_field
        assert receipts._emit_standard_sell_partial_lifecycle_outbox_leg(leg) is False


@pytest.mark.parametrize(
    "receive_source",
    ["websocket_packet_ingress", "handler_dispatch_fallback"],
)
def test_sell_lifecycle_outbox_ack_uses_receive_clock_and_retains_fid908(
    monkeypatch,
    receive_source,
):
    occurred_at = datetime(
        2026, 8, 26, 9, 0, 3, tzinfo=timezone(timedelta(hours=9))
    )
    received_at = occurred_at + timedelta(milliseconds=250)
    stock = {
        "id": 7,
        "code": "123456",
        "name": "CLOCK",
        "scanner_promotion_id": "promotion-7",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
        "broker_execution_time_raw": "090003",
        "broker_execution_time_source": "official_fid_908",
        "broker_execution_received_at": received_at.isoformat(),
        "broker_execution_receive_time_source": receive_source,
        "broker_execution_observed_at": occurred_at.isoformat(),
        "broker_actual_execution_venue": "KRX",
        "broker_actual_execution_venue_source": "official_fid_2134_2135",
        "broker_actual_exchange_code": "1",
        "broker_actual_exchange_name": "KRX",
        "broker_sor_flag": "N",
        "main_lifecycle_broker_raw_envelope_schema": (
            "kiwoom_websocket_order_execution_00_values_v1"
        ),
        "main_lifecycle_broker_raw_source_type": "00",
        "9203": "0000007",
        "9001": "123456",
        "913": "체결",
        "900": "10",
        "902": "8",
        "903": "20020",
        "905": "-매도",
        "907": "1",
        "908": "090003",
        "909": "1",
        "910": "10010",
        "911": "2",
        "914": "10010",
        "915": "2",
        "919": "",
        "2134": "1",
        "2135": "KRX",
        "2136": "N",
    }
    leg = receipts._standard_sell_partial_lifecycle_outbox_leg(
        stock,
        code="123456",
        target_id=7,
        now=occurred_at,
        receipt={
            "order_no": "0000007",
            "execution_no": "1",
            "incremental_price": 10_010,
            "incremental_qty": 2,
            "cumulative_qty": 2,
            "remaining_qty": 8,
            "incremental_net_pnl_krw": calculate_net_realized_pnl(
                10_000, 10_010, 2
            ),
            "economics_complete": True,
            "quantity_contract_complete": True,
            "unit_fill_consistent": True,
            "unit_qty_matches_delta": True,
        },
        buy_price=10_000,
    )
    captured = {}

    def _emit(pipeline, name, code, stage, *, record_id=None, fields=None):
        normalized = {str(key): str(value) for key, value in (fields or {}).items()}
        captured.update(normalized)
        return {
            "pipeline": pipeline,
            "stage": stage,
            "stock_name": name,
            "stock_code": code,
            "record_id": record_id,
            "fields": normalized,
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    monkeypatch.setattr(receipts, "emit_pipeline_event", _emit)

    assert leg["observed_at"] == received_at.isoformat(timespec="microseconds")
    assert receipts._emit_standard_sell_partial_lifecycle_outbox_leg(leg) is True
    assert captured["main_lifecycle_observed_at"] == received_at.isoformat(
        timespec="microseconds"
    )
    assert captured["main_lifecycle_execution_occurred_at"] == occurred_at.isoformat(
        timespec="microseconds"
    )
    assert captured["main_lifecycle_execution_receive_time_source"] == receive_source
    assert captured["main_lifecycle_ordering_time_source"] == (
        "broker_execution_received_at"
    )
    assert captured["908"] == "090003"


def test_sell_lifecycle_outbox_malformed_pending_state_fails_closed(monkeypatch):
    stock = {
        "id": 7,
        "code": "123456",
        "name": "MALFORMED",
        receipts._SELL_EXECUTION_RECEIPT_STATE_KEY: {
            "position_qty": 10,
            "aggregate_cumulative_qty": 2,
            receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY: [],
        },
    }
    monkeypatch.setattr(
        receipts, "_persist_sell_receipt_recovery_or_interlock", lambda *a, **k: True
    )

    assert receipts.replay_pending_sell_partial_lifecycle_outbox(stock) is False
    assert receipts._sell_lifecycle_outbox_pending(stock) is True
    assert stock["sell_partial_lifecycle_outbox_invalid"] is True
    assert stock["sell_receipt_durability_blocked"] is True


def test_sell_lifecycle_outbox_replays_same_second_legs_by_cumulative_qty(
    monkeypatch,
):
    observed_at = datetime(
        2026, 8, 26, 9, 0, 3, 250_000, tzinfo=timezone(timedelta(hours=9))
    )
    stock = {"id": 7, "code": "123456", "name": "ORDERED"}
    legs = []
    for cumulative_qty, stage in (
        (4, "sell_partial_fill_progress"),
        (10, "sell_completed"),
        (2, "sell_partial_fill_progress"),
    ):
        legs.append(
            receipts._build_sell_lifecycle_outbox_leg(
                stock,
                code="123456",
                target_id=7,
                now=observed_at,
                stage=stage,
                event_fields={
                    "cumulative_sell_qty": cumulative_qty,
                    "remaining_sell_qty": max(0, 10 - cumulative_qty),
                    "main_lifecycle_exit_qty": 2,
                    "main_lifecycle_exit_price": 10_010.0,
                    "main_lifecycle_broker_reconciled": stage == "sell_completed",
                    "main_lifecycle_reconciled_final_exit": stage
                    == "sell_completed",
                },
            )
        )
    stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY] = {
        "position_qty": 10,
        "aggregate_cumulative_qty": 10,
        "final": True,
        "final_pending_db_commit": True,
        receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY: {
            leg["leg_sha256"]: leg for leg in legs
        },
    }
    emitted = []
    monkeypatch.setattr(
        receipts,
        "_emit_standard_sell_partial_lifecycle_outbox_leg",
        lambda leg: emitted.append(
            leg["event_fields"]["cumulative_sell_qty"]
        )
        or True,
    )
    monkeypatch.setattr(
        receipts, "_persist_sell_receipt_recovery_or_interlock", lambda *a, **k: True
    )

    assert receipts.replay_pending_sell_partial_lifecycle_outbox(stock) is True
    assert emitted == [2, 4, 10]
    assert receipts._sell_lifecycle_outbox_pending(stock) is False


def test_final_sell_outbox_recovers_in_process_after_transient_append_failure(
    monkeypatch,
    tmp_path,
):
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "buy_qty": 1,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
        },
    )()
    stock = {
        "id": 7,
        "code": "123456",
        "name": "RECOVER",
        "status": "SELL_ORDERED",
        "buy_price": 10_000.0,
        "buy_qty": 1,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "promotion-7",
    }
    append_available = {"value": False}
    attempted_hashes = []

    def _emit(leg):
        attempted_hashes.append(leg["leg_sha256"])
        return append_available["value"]

    lock = threading.RLock()
    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(receipts, "_STATE_LOCK", lock)
    monkeypatch.setattr(receipts, "event_bus", _Bus())
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(
        receipts.POSITION_PEAK_LEDGER, "remove_for_stock", lambda _stock: None
    )
    monkeypatch.setattr(
        receipts, "move_orders_to_terminal", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **_kwargs: {})
    monkeypatch.setattr(receipts, "_scalp_exit_completed_callback", None)
    monkeypatch.setattr(
        receipts, "_smoothing_non_revive_post_sell_register_callback", None
    )
    monkeypatch.setattr(
        receipts, "_emit_standard_sell_partial_lifecycle_outbox_leg", _emit
    )
    monkeypatch.setattr(sniper_sync, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(sniper_sync, "STATE_LOCK", lock)

    receipts._finalize_standard_sell_execution(
        target_id=7,
        exec_price=10_100,
        now=datetime(
            2026, 8, 26, 9, 10, tzinfo=timezone(timedelta(hours=9))
        ),
        target_stock=stock,
        strategy="SCALPING",
        is_scalp_revive=False,
        code="123456",
        sell_receipt={
            "status": "final",
            "final": True,
            "expected_qty": 1,
            "cumulative_qty": 1,
            "cumulative_amount": 10_100,
            "cumulative_net_pnl_krw": calculate_net_realized_pnl(
                10_000, 10_100, 1
            ),
            "incremental_qty": 1,
            "incremental_price": 10_100,
            "incremental_net_pnl_krw": calculate_net_realized_pnl(
                10_000, 10_100, 1
            ),
            "economics_complete": True,
            "quantity_contract_complete": True,
            "unit_fill_consistent": True,
            "execution_no": "E1",
        },
        order_no="S1",
        safe_buy_price=10_000.0,
    )

    assert record.status == "COMPLETED"
    assert stock["status"] == "SELL_ORDERED"
    assert stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY][
        "final_pending_db_commit"
    ] is True
    assert (tmp_path / "7.json").exists()

    append_available["value"] = True
    result = sniper_sync._retry_pending_final_sell_receipts_in_process()

    assert result == {"scanned": 1, "recovered": 1, "deferred": 0}
    assert stock["status"] == "COMPLETED"
    assert receipts._SELL_EXECUTION_RECEIPT_STATE_KEY not in stock
    assert "sell_cancel_reconciliation_required" not in stock
    assert not (tmp_path / "7.json").exists()
    assert len(attempted_hashes) == 2
    assert len(set(attempted_hashes)) == 1


@pytest.mark.parametrize("recovery_mode", ["periodic", "restart"])
def test_nxt_tp1_outbox_recovers_progress_and_completion_before_runner_release(
    monkeypatch,
    tmp_path,
    recovery_mode,
):
    record = type(
        "Record",
        (),
        {
            "id": 7,
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "status": "SELL_ORDERED",
            "scale_in_locked": True,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
        },
    )()
    stock = {
        "id": 7,
        "code": "123456",
        "name": "TP1",
        "status": "SELL_ORDERED",
        "buy_price": 10_000.0,
        "buy_qty": 10,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "promotion-7",
        "sell_odno": "0000701",
        "pending_sell_msg": "TP1 partial",
        "nxt_rising_missed_tp1_partial_pending": True,
        "nxt_rising_missed_tp1_partial_requested_qty": 4,
        "nxt_rising_missed_tp1_partial_filled_qty": 0,
        "nxt_rising_missed_tp1_partial_fill_amount": 0,
        "nxt_rising_missed_tp1_partial_original_qty": 10,
    }
    append_available = {"value": False}
    successfully_emitted = []

    def _emit(leg):
        if not append_available["value"]:
            return False
        successfully_emitted.append(leg["stage"])
        return True

    lock = threading.RLock()
    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(receipts, "_STATE_LOCK", lock)
    monkeypatch.setattr(receipts, "event_bus", _Bus())
    monkeypatch.setattr(
        receipts,
        "_emit_standard_sell_partial_lifecycle_outbox_leg",
        _emit,
    )
    monkeypatch.setattr(sniper_sync, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(sniper_sync, "STATE_LOCK", lock)

    receipts._handle_nxt_rising_missed_tp1_partial_sell_execution(
        target_id=7,
        target_stock=stock,
        code="123456",
        order_no="0000701",
        exec_price=10_010,
        exec_qty=2,
        now=datetime(
            2026, 8, 26, 17, 0, 3, tzinfo=timezone(timedelta(hours=9))
        ),
        safe_buy_price=10_000,
        order_qty=4,
        remaining_qty=2,
        cumulative_exec_amount=20_020,
        execution_no="1",
        unit_exec_price=10_010,
        unit_exec_qty=2,
    )
    receipts._handle_nxt_rising_missed_tp1_partial_sell_execution(
        target_id=7,
        target_stock=stock,
        code="123456",
        order_no="0000701",
        exec_price=10_020,
        exec_qty=4,
        now=datetime(
            2026, 8, 26, 17, 0, 4, tzinfo=timezone(timedelta(hours=9))
        ),
        safe_buy_price=10_000,
        order_qty=4,
        remaining_qty=0,
        cumulative_exec_amount=40_060,
        execution_no="2",
        unit_exec_price=10_020,
        unit_exec_qty=2,
    )

    state = stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY]
    assert record.status == "SELL_ORDERED"
    assert stock["status"] == "SELL_ORDERED"
    assert state[receipts._NXT_TP1_COMPLETION_RELEASE_PENDING_KEY] is True
    assert len(state[receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY]) == 2
    assert (tmp_path / "7.json").exists()
    append_available["value"] = True

    if recovery_mode == "periodic":
        stock.update(
            {
                "sell_cancel_reconciliation_required": True,
                "sell_cancel_reconciliation_source": (
                    "sell_lifecycle_outbox_recovery_pending"
                ),
                "sell_cancel_reconciliation_retry_at": 9_999.0,
            }
        )
        result = sniper_sync._retry_pending_final_sell_receipts_in_process()
        assert result == {"scanned": 1, "recovered": 1, "deferred": 0}
        recovered_target = stock
    else:
        recovered_target = {
            "id": 7,
            "code": "123456",
            "name": "TP1",
            "status": "SELL_ORDERED",
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "scanner_promotion_id": "promotion-7",
            "sell_cancel_reconciliation_required": True,
            "sell_cancel_reconciliation_source": (
                "sell_lifecycle_outbox_recovery_failed:RuntimeError"
            ),
            "sell_cancel_reconciliation_retry_at": 9_999.0,
        }
        monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [recovered_target])
        restored_state, reason = sniper_sync._restore_sell_receipt_recovery(
            target_stock=recovered_target,
            record=record,
            code="123456",
            broker_remaining_qty=6,
        )
        assert reason == "journal_exact_match"
        assert restored_state is not None

    assert successfully_emitted == [
        "nxt_rising_missed_tp1_partial_fill_progress",
        "nxt_rising_missed_tp1_partial_sell_completed",
    ]
    assert record.status == "HOLDING"
    assert recovered_target["status"] == "HOLDING"
    assert recovered_target["buy_qty"] == 6
    assert recovered_target["nxt_rising_missed_tp1_partial_pending"] is False
    assert recovered_target["nxt_rising_missed_tp1_partial_applied"] is True
    assert "sell_cancel_reconciliation_required" not in recovered_target
    assert "sell_cancel_reconciliation_source" not in recovered_target
    assert "sell_cancel_reconciliation_retry_at" not in recovered_target
    recovered_state = recovered_target[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY]
    assert receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY not in recovered_state
    assert receipts._NXT_TP1_COMPLETION_RELEASE_PENDING_KEY not in recovered_state
    journal_state, journal_reason = receipts.load_sell_receipt_recovery(
        target_id=7,
        code="123456",
        position_qty=10,
        broker_remaining_qty=6,
    )
    assert journal_reason == "journal_exact_match"
    assert receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY not in journal_state
    assert receipts._NXT_TP1_COMPLETION_RELEASE_PENDING_KEY not in journal_state


@pytest.mark.parametrize(
    (
        "cumulative_qty",
        "remaining_qty",
        "cumulative_amount",
        "unit_qty",
        "broker_remaining_qty",
        "expected_stage",
    ),
    [
        (2, 2, 20_020, 2, 8, "nxt_rising_missed_tp1_partial_fill_progress"),
        (4, 0, 40_040, 4, 6, "nxt_rising_missed_tp1_partial_sell_completed"),
    ],
)
def test_nxt_tp1_outbox_is_fsynced_before_db_interlock(
    monkeypatch,
    tmp_path,
    cumulative_qty,
    remaining_qty,
    cumulative_amount,
    unit_qty,
    broker_remaining_qty,
    expected_stage,
):
    stock = {
        "id": 7,
        "code": "123456",
        "name": "TP1-CRASH-WINDOW",
        "status": "SELL_ORDERED",
        "buy_price": 10_000.0,
        "buy_qty": 10,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "promotion-7",
        "sell_odno": "0000701",
        "nxt_rising_missed_tp1_partial_pending": True,
        "nxt_rising_missed_tp1_partial_requested_qty": 4,
        "nxt_rising_missed_tp1_partial_filled_qty": 0,
        "nxt_rising_missed_tp1_partial_fill_amount": 0,
        "nxt_rising_missed_tp1_partial_original_qty": 10,
    }
    observations = []

    class _CrashAfterOutboxDB:
        def get_session(self):
            state = stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY]
            observations.append(
                (
                    (tmp_path / "7.json").exists(),
                    bool(state.get(receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY)),
                )
            )
            raise RuntimeError("simulated_db_boundary_crash")

    monkeypatch.setattr(receipts, "DB", _CrashAfterOutboxDB())
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(receipts, "_STATE_LOCK", threading.RLock())
    monkeypatch.setattr(receipts, "event_bus", _Bus())
    monkeypatch.setattr(
        receipts,
        "_emit_standard_sell_partial_lifecycle_outbox_leg",
        lambda leg: False,
    )

    receipts._handle_nxt_rising_missed_tp1_partial_sell_execution(
        target_id=7,
        target_stock=stock,
        code="123456",
        order_no="0000701",
        exec_price=10_010,
        exec_qty=cumulative_qty,
        now=datetime(
            2026, 8, 26, 17, 0, 3, tzinfo=timezone(timedelta(hours=9))
        ),
        safe_buy_price=10_000,
        order_qty=4,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_amount,
        execution_no="1",
        unit_exec_price=10_010,
        unit_exec_qty=unit_qty,
    )

    assert observations == [(True, True)]
    journal_state, reason = receipts.load_sell_receipt_recovery(
        target_id=7,
        code="123456",
        position_qty=10,
        broker_remaining_qty=broker_remaining_qty,
    )
    assert reason == "journal_exact_match"
    pending_legs = journal_state[receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY]
    assert len(pending_legs) == 1
    assert next(iter(pending_legs.values()))["stage"] == expected_stage


def test_late_prior_terminal_fill_waits_for_replacement_order_absence(
    monkeypatch,
    tmp_path,
):
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
        },
    )()
    stock = {
        "id": 7,
        "code": "123456",
        "name": "REPLACED",
        "status": "SELL_ORDERED",
        "buy_price": 10_000.0,
        "buy_qty": 10,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "promotion-7",
    }
    first = receipts._resolve_sell_execution_receipt(
        stock,
        order_no="S1",
        exec_price=10_010,
        cumulative_exec_qty=2,
        expected_position_qty=10,
        buy_price=10_000,
        order_qty=10,
        remaining_qty=8,
        cumulative_exec_amount=20_020,
        execution_no="E1",
        unit_exec_price=10_010,
        unit_exec_qty=2,
    )
    assert first["status"] == "partial"
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    rotated = state_handlers._rotate_cancelled_sell_receipt_ledger(
        stock,
        orig_ord_no="S1",
        broker_qty=8,
    )
    assert rotated["reconciled"] is True
    state = dict(stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY])
    state.update(
        {
            "order_no": "S2",
            "expected_qty": 8,
            "cumulative_qty": 0,
            "cumulative_amount": 0,
            "remaining_qty": 8,
            "executions_by_no": {},
        }
    )
    stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY] = state

    terminal = receipts._resolve_sell_execution_receipt(
        stock,
        order_no="S1",
        exec_price=10_100,
        cumulative_exec_qty=10,
        expected_position_qty=10,
        buy_price=10_000,
        order_qty=10,
        remaining_qty=0,
        cumulative_exec_amount=100_820,
        execution_no="E2",
        unit_exec_price=10_100,
        unit_exec_qty=8,
    )
    assert terminal["status"] == "replacement_terminal_reconcile_required"
    terminal_state = dict(stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY])
    assert terminal_state["replacement_order_no"] == "S2"
    stock.update(
        {
            "broker_execution_received_at": datetime(
                2026,
                8,
                26,
                9,
                20,
                1,
                tzinfo=timezone(timedelta(hours=9)),
            ).isoformat(),
            "broker_execution_receive_time_source": "websocket_packet_ingress",
            "broker_execution_time_raw": "092000",
            "broker_execution_time_source": "official_fid_908",
            "broker_execution_observed_at": datetime(
                2026,
                8,
                26,
                9,
                20,
                tzinfo=timezone(timedelta(hours=9)),
            ).isoformat(),
            "909": "E2",
            "9203": "S1",
        }
    )
    provenance_snapshot = receipts._normalized_receipt_snapshot(
        receipts._receipt_snapshot(stock, receipts._SELL_RECEIPT_SNAPSHOT_KEYS)
    )
    terminal_state.update(
        {
            "replacement_terminal_receipt": terminal,
            "replacement_terminal_finalize_context": {
                "target_id": 7,
                "code": "123456",
                "now_iso": datetime(
                    2026,
                    8,
                    26,
                    9,
                    20,
                    tzinfo=timezone(timedelta(hours=9)),
                ).isoformat(),
                "safe_buy_price": 10_000.0,
                "strategy": "SCALPING",
                "is_scalp_revive": False,
                "order_no": "S1",
            },
            "replacement_terminal_provenance_snapshot": provenance_snapshot,
            "replacement_terminal_provenance_snapshot_sha256": (
                receipts._receipt_snapshot_sha256(provenance_snapshot)
            ),
        }
    )
    terminal_state[
        receipts._REPLACEMENT_TERMINAL_RECONCILIATION_GENERATION_KEY
    ] = receipts._replacement_terminal_reconciliation_generation_sha256(
        terminal_state
    )
    stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY] = terminal_state

    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(receipts, "event_bus", _Bus())
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(
        receipts.POSITION_PEAK_LEDGER, "remove_for_stock", lambda _stock: None
    )
    monkeypatch.setattr(
        receipts, "move_orders_to_terminal", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **_kwargs: {})
    monkeypatch.setattr(receipts, "_scalp_exit_completed_callback", None)
    monkeypatch.setattr(
        receipts, "_smoothing_non_revive_post_sell_register_callback", None
    )
    logged = []
    _install_successful_sell_lifecycle_outbox(monkeypatch, logged)

    # A cancel acknowledgement alone is not terminal proof for the replacement.
    assert receipts.finalize_replacement_terminal_sell_receipt(stock) is False
    assert record.status == "SELL_ORDERED"
    # An intervening mutable receipt must not replace the terminal packet.
    stock["909"] = "MUTATED"
    tampered_state = dict(stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY])
    tampered_context = dict(tampered_state["replacement_terminal_finalize_context"])
    tampered_context["target_id"] = 8
    tampered_state["replacement_terminal_finalize_context"] = tampered_context
    tampered_state["replacement_terminal_absence_confirmed"] = True
    stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY] = tampered_state
    assert receipts.finalize_replacement_terminal_sell_receipt(stock) is False

    # Restore the checksum-bound generation and apply only the mutable absence
    # proof.  Later mutations on the shared stock cannot alter its snapshot.
    terminal_state = dict(stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY])
    terminal_state["replacement_terminal_finalize_context"] = {
        "target_id": 7,
        "code": "123456",
        "now_iso": datetime(
            2026,
            8,
            26,
            9,
            20,
            tzinfo=timezone(timedelta(hours=9)),
        ).isoformat(),
        "safe_buy_price": 10_000.0,
        "strategy": "SCALPING",
        "is_scalp_revive": False,
        "order_no": "S1",
    }
    terminal_state["replacement_terminal_absence_confirmed"] = True
    stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY] = terminal_state

    assert receipts.finalize_replacement_terminal_sell_receipt(stock) is True
    assert record.status == "COMPLETED"
    assert stock["status"] == "COMPLETED"
    assert [stage for stage, _fields in logged] == ["sell_completed"]
    assert logged[0][1]["909"] == "E2"
    assert "sell_cancel_reconciliation_required" not in stock


def test_replacement_terminal_absence_query_never_overwrites_newer_receipt(
    monkeypatch,
):
    def _terminal_state(order_no, receipt_marker):
        provenance = {"id": 7, "code": "123456", "909": receipt_marker}
        state = {
            "position_qty": 10,
            "aggregate_cumulative_qty": 10,
            "remaining_qty": 0,
            "replacement_order_no": order_no,
            "replacement_terminal_reconciliation_required": True,
            "replacement_terminal_receipt": {
                "cumulative_qty": 10,
                "economics_complete": True,
                "quantity_contract_complete": True,
                "marker": receipt_marker,
            },
            "replacement_terminal_finalize_context": {
                "target_id": 7,
                "code": "123456",
                "now_iso": "2026-08-26T09:20:00+09:00",
            },
            "replacement_terminal_provenance_snapshot": provenance,
            "replacement_terminal_provenance_snapshot_sha256": (
                receipts._receipt_snapshot_sha256(provenance)
            ),
        }
        state[
            receipts._REPLACEMENT_TERMINAL_RECONCILIATION_GENERATION_KEY
        ] = receipts._replacement_terminal_reconciliation_generation_sha256(state)
        return state

    old_state = _terminal_state("REPLACEMENT-OLD", "OLD")
    new_state = _terminal_state("REPLACEMENT-NEW", "NEW")
    new_state[receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY] = {
        "newer-leg": {"stage": "sell_completed"}
    }
    stock = {
        "id": 7,
        "code": "123456",
        "name": "RACE",
        "status": "SELL_ORDERED",
        "sell_cancel_reconciliation_required": True,
        "sell_cancel_reconciliation_retry_at": 0.0,
        receipts._SELL_EXECUTION_RECEIPT_STATE_KEY: old_state,
    }
    monkeypatch.setattr(
        state_handlers,
        "_broker_position_qty_for_sell_reconciliation",
        lambda code, stock: (0, "kt00018_all_venues_position_absent"),
    )

    def _absence_query(code, order_no):
        assert order_no == "REPLACEMENT-OLD"
        # Model a WS receipt arriving while the ka10075 request is blocked.
        stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY] = new_state
        return True, "ka10075_terminal_absence_confirmed"

    monkeypatch.setattr(
        state_handlers, "_sell_order_terminal_absence_confirmed", _absence_query
    )
    persist_calls = []
    finalize_calls = []
    monkeypatch.setattr(
        receipts,
        "_persist_sell_receipt_recovery_or_interlock",
        lambda *args, **kwargs: persist_calls.append((args, kwargs)) or True,
    )
    monkeypatch.setattr(
        receipts,
        "finalize_replacement_terminal_sell_receipt",
        lambda *args, **kwargs: finalize_calls.append((args, kwargs)) or True,
    )
    monkeypatch.setattr(state_handlers, "log_error", lambda *args, **kwargs: None)

    assert (
        state_handlers._sell_cancel_reconciliation_blocks_holding(
            stock, "123456", now_ts=1_000.0
        )
        is True
    )

    retained = stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY]
    assert retained is new_state
    assert retained["replacement_order_no"] == "REPLACEMENT-NEW"
    assert retained["replacement_terminal_receipt"]["marker"] == "NEW"
    assert receipts._SELL_PARTIAL_LIFECYCLE_OUTBOX_KEY in retained
    assert "replacement_terminal_absence_confirmed" not in retained
    assert persist_calls == []
    assert finalize_calls == []


def test_scalp_revive_recovers_crash_after_precommit_watch_id_fsync(
    monkeypatch,
    tmp_path,
):
    old_record = type(
        "Record",
        (),
        {
            "id": 7,
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "stock_name": "REVIVE",
            "stock_code": "123456",
            "prob": 0.8,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
        },
    )()

    class _ReviveCrashDB:
        def __init__(self):
            self.crash = True
            self.records = {7: old_record}
            self.next_watch_id = 99

        def get_session(self):
            owner = self

            class _Session:
                def __init__(self):
                    self.query_id = None
                    self.added = None

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def query(self, *_args, **_kwargs):
                    return self

                def filter_by(self, **kwargs):
                    self.query_id = int(kwargs.get("id") or 0)
                    return self

                def first(self):
                    return owner.records.get(self.query_id)

                def add(self, added):
                    self.added = added

                def flush(self):
                    if self.added is not None:
                        self.added.id = owner.next_watch_id

                def rollback(self):
                    old_record.status = "SELL_ORDERED"
                    old_record.sell_price = 0
                    old_record.sell_time = None

                def commit(self):
                    if owner.crash:
                        self.rollback()
                        raise RuntimeError("crash_after_precommit_journal")
                    if self.added is not None:
                        owner.records[int(self.added.id)] = self.added

            return _Session()

    stock = {
        "id": 7,
        "code": "123456",
        "name": "REVIVE",
        "status": "SELL_ORDERED",
        "buy_price": 10_000.0,
        "buy_qty": 10,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "promotion-7",
    }
    db = _ReviveCrashDB()
    logged = []
    monkeypatch.setattr(receipts, "DB", db)
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(receipts, "event_bus", _Bus())
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(
        receipts.POSITION_PEAK_LEDGER, "remove_for_stock", lambda _stock: None
    )
    monkeypatch.setattr(
        receipts, "move_orders_to_terminal", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **_kwargs: {})
    _install_successful_sell_lifecycle_outbox(monkeypatch, logged)
    final_receipt = {
        "status": "final",
        "final": True,
        "expected_qty": 10,
        "cumulative_qty": 10,
        "cumulative_amount": 101_000,
        "cumulative_net_pnl_krw": calculate_net_realized_pnl(
            10_000, 10_100, 10
        ),
        "incremental_qty": 10,
        "incremental_price": 10_100,
        "incremental_net_pnl_krw": calculate_net_realized_pnl(
            10_000, 10_100, 10
        ),
        "economics_complete": True,
        "quantity_contract_complete": True,
        "unit_fill_consistent": True,
        "execution_no": "E1",
    }

    assert (
        receipts._handle_scalp_revive_sell_execution(
            target_id=7,
            target_stock=stock,
            code="123456",
            exec_price=10_100,
            exec_qty=10,
            now=datetime(
                2026, 8, 26, 9, 30, tzinfo=timezone(timedelta(hours=9))
            ),
            profit_rate=0.0,
            safe_buy_price=10_000,
            strategy="SCALPING",
            sell_receipt=final_receipt,
            order_no="S1",
        )
        is False
    )
    state = stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY]
    assert state["finalization_new_watch_id"] == 99
    assert old_record.status == "SELL_ORDERED"
    assert 99 not in db.records
    assert (tmp_path / "7.json").exists()

    db.crash = False
    db.next_watch_id = 100
    assert receipts.recover_final_sell_receipt(stock) is True

    assert old_record.status == "COMPLETED"
    assert db.records[100].status == "WATCHING"
    assert stock["id"] == 100
    assert stock["status"] == "WATCHING"
    assert [stage for stage, _fields in logged] == ["sell_completed"]
    assert not (tmp_path / "7.json").exists()


def test_sell_execution_message_relabels_pending_stop_loss_when_realized_profit():
    bus = _Bus()
    receipts.event_bus = bus

    receipts._publish_sell_execution_message(
        name="데브시스터즈",
        pending_msg=(
            "📉 [손절 주문] **[데브시스터즈]** 매도 전송\n"
            "사유: `🛑 하드스탑 도달 (-5.0%) [AI: 50]`\n"
            "현재가 기준 수익: `-5.75%` (고점: -0.2%)"
        ),
        audience="VIP_ALL",
        exec_price=18630,
        profit_rate=1.35,
    )

    assert len(bus.events) == 1
    _, payload = bus.events[0]
    assert "[익절 완료]" in payload["message"]
    assert "🎊 [익절 완료]" in payload["message"]
    assert "📉 [익절 완료]" not in payload["message"]
    assert "[손절 완료]" not in payload["message"]
    assert "청산 신호: `🛑 하드스탑 도달 (-5.0%) [AI: 50]`" in payload["message"]
    assert "실현 결과: `익절 확정`" in payload["message"]
    assert "사유: `🛑 하드스탑 도달" not in payload["message"]
    assert "신호 당시 평가손익: `-5.75%`" in payload["message"]
    assert "현재가 기준 수익" not in payload["message"]
    assert "확정 수익률: `+1.35%`" in payload["message"]


def test_sell_execution_notification_failure_never_reopens_committed_custody(
    monkeypatch,
):
    class FailingBus:
        def publish(self, *_args, **_kwargs):
            raise RuntimeError("notification unavailable")

    errors = []
    monkeypatch.setattr(receipts, "event_bus", FailingBus())
    monkeypatch.setattr(receipts, "log_error", errors.append)

    receipts._publish_sell_execution_message(
        name="TEST",
        pending_msg="",
        audience="ADMIN_ONLY",
        exec_price=10_100,
        profit_rate=0.5,
    )

    assert errors
    assert "SELL_COMPLETION_NOTIFICATION_FAILED" in errors[0]


def test_sell_context_uses_exact_one_share_entry_receipt_when_db_price_is_stale():
    record = type(
        "Record",
        (),
        {
            "buy_price": 5_110.0,
            "buy_qty": 1,
            "strategy": "SCALPING",
            "position_tag": "DEFAULT",
        },
    )()
    receipts.DB = _ReceiptDB(record)
    stock = {
        "buy_price": 5_040.0,
        "buy_qty": 1,
        "last_entry_receipt_economics_complete": True,
        "last_entry_receipt_execution_no": "0000042",
        "scale_in_filled_qty": 0,
    }

    context = receipts._resolve_sell_execution_context(
        34620,
        stock,
        5_070,
        datetime(2026, 8, 24, 10, 30).time(),
    )

    assert context is not None
    assert context[1] == 5_040.0
    assert stock["sell_buy_price_reconciled_from_entry_receipt"] is True
    assert stock["sell_buy_price_reconcile_db_price"] == 5_110.0


def test_sell_context_keeps_db_price_without_exact_entry_receipt_contract():
    record = type(
        "Record",
        (),
        {
            "buy_price": 5_110.0,
            "buy_qty": 1,
            "strategy": "SCALPING",
            "position_tag": "DEFAULT",
        },
    )()
    receipts.DB = _ReceiptDB(record)
    stock = {
        "buy_price": 5_040.0,
        "buy_qty": 1,
        "last_entry_receipt_economics_complete": False,
        "last_entry_receipt_execution_no": "0000042",
        "scale_in_filled_qty": 0,
    }

    context = receipts._resolve_sell_execution_context(
        34620,
        stock,
        5_070,
        datetime(2026, 8, 24, 10, 30).time(),
    )

    assert context is not None
    assert context[1] == 5_110.0
    assert "sell_buy_price_reconciled_from_entry_receipt" not in stock


def test_sell_commit_reconciles_stale_db_price_from_exact_entry_receipt(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "buy_price": 5_110.0,
            "buy_qty": 1,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "position_tag": "DEFAULT",
        },
    )()
    receipts.DB = _ReceiptDB(record)
    receipts.event_bus = _Bus()
    logged = {}
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: logged.update(kwargs),
    )
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **kwargs: {})
    monkeypatch.setattr(
        receipts, "_scalp_exit_completed_callback", lambda *args, **kwargs: True
    )
    snapshot = {
        "code": "003530",
        "name": "한화투자증권",
        "buy_price": 5_040.0,
        "buy_qty": 1,
        "last_entry_receipt_economics_complete": True,
        "last_entry_receipt_execution_no": "0000042",
        "sell_buy_price_reconciled_from_entry_receipt": True,
        "sell_buy_price_reconcile_db_price": 5_110.0,
        "sell_buy_price_reconcile_reason": (
            "exact_one_share_entry_receipt_precedes_async_db_buy_update"
        ),
        **_completed_sell_receipt_fields(buy_price=5_040.0, sell_price=5_070.0, qty=1),
    }

    committed = receipts._update_db_for_sell(
        34620,
        5_070,
        datetime(2026, 8, 24, 10, 30),
        snapshot,
        "SCALPING",
        False,
    )

    assert committed is True
    assert record.buy_price == 5_040.0
    assert record.profit_rate == pytest.approx(18 / 5_040 * 100)
    # DB commit is no longer a second lifecycle producer.  The durable final
    # outbox owns the only canonical sell_completed row.
    assert logged == {}
    assert snapshot["buy_price"] == 5_040.0
    assert snapshot["sell_buy_price_reconciled_from_entry_receipt"] is True


def test_broker_execution_time_requires_exact_hhmmss_and_preserves_timezone():
    received_at = datetime(2026, 8, 18, 9, 10, tzinfo=timezone(timedelta(hours=9)))

    observed_at, fields = receipts._broker_execution_context(
        {
            "broker_execution_time_raw": "090003",
            "actual_execution_venue": "KRX",
            "broker_execution_received_at": received_at.isoformat(),
            "broker_execution_receive_time_source": ("websocket_packet_ingress"),
        },
        received_at=received_at,
    )
    fallback_at, fallback_fields = receipts._broker_execution_context(
        {
            "broker_execution_time_raw": "0900031",
            "actual_execution_venue": "KRX",
        },
        received_at=received_at,
    )

    assert observed_at.isoformat() == "2026-08-18T09:00:03+09:00"
    assert fields["broker_execution_time_source"] == "official_fid_908"
    assert fields["broker_execution_receive_time_source"] == (
        "websocket_packet_ingress"
    )
    assert fields["broker_execution_provenance_complete"] is True
    assert fallback_at == received_at
    assert fallback_fields["broker_execution_time_source"] == (
        "local_receive_time_fallback"
    )
    assert fallback_fields["broker_execution_receive_time_source"] == (
        "handler_dispatch_fallback"
    )
    assert fallback_fields["broker_execution_provenance_complete"] is False


def test_entry_receipt_submit_trace_rejects_oversized_value_without_truncation():
    marker_key = "_entry_lifecycle_submit_telemetry_committed_by_order_no"
    order_no = "1234567"
    max_length = receipts.MAIN_LIFECYCLE_MAX_DATA_STRING_LENGTH
    stock = {
        marker_key: {
            order_no: {
                "qty": 1,
                "decision_trace_id": "x" * max_length,
            }
        }
    }

    assert (
        receipts._lifecycle_submit_trace_id(
            stock,
            marker_key=marker_key,
            order_no=order_no,
        )
        == "x" * max_length
    )

    stock[marker_key][order_no]["decision_trace_id"] = "x" * (max_length + 1)
    assert (
        receipts._lifecycle_submit_trace_id(
            stock,
            marker_key=marker_key,
            order_no=order_no,
        )
        == ""
    )


def test_broker_execution_context_carries_exact_raw_proof_without_hybrid_reuse():
    received_at = datetime(2026, 8, 20, 9, 1, tzinfo=timezone(timedelta(hours=9)))
    raw_fields = {
        "main_lifecycle_broker_raw_envelope_schema": (
            "kiwoom_websocket_order_execution_00_values_v1"
        ),
        "main_lifecycle_broker_raw_source_type": "00",
        "9203": "0000018",
        "9001": "005930",
        "913": "체결",
        "900": "10",
        "902": "8",
        "903": "121400",
        "905": "+매수",
        "907": "2",
        "908": "090003",
        "909": "0000001",
        "910": "60700",
        "911": "2",
        "914": "60700",
        "915": "2",
        "2134": "1",
        "2135": "KRX",
        "2136": "N",
    }
    _, fields = receipts._broker_execution_context(
        {
            **raw_fields,
            "broker_execution_time_raw": "090003",
            "actual_execution_venue": "KRX",
        },
        received_at=received_at,
    )

    target_stock = {}
    target_stock.update(fields)
    carried_fields = receipts._broker_execution_provenance_fields(target_stock)
    proof = build_broker_execution_provenance(
        carried_fields,
        expected_qty=2,
        expected_price=60_700,
        expected_stock_code="005930",
        expected_side="BUY",
        lifecycle_venue="KRX",
    )
    assert proof["broker_execution_provenance_state"] == "complete"
    assert carried_fields["909"] == "0000001"

    _, missing_fields = receipts._broker_execution_context(
        {
            "broker_execution_time_raw": "090004",
            "actual_execution_venue": "KRX",
        },
        received_at=received_at,
    )
    assert all(missing_fields[key] is None for key in raw_fields)
    missing_proof = build_broker_execution_provenance(
        missing_fields,
        expected_qty=2,
        expected_price=60_700,
        expected_stock_code="005930",
        expected_side="BUY",
        lifecycle_venue="KRX",
    )
    assert missing_proof["broker_execution_provenance_state"] == "missing"


def test_execution_cancel_or_unknown_side_never_enters_buy_sell_custody(monkeypatch):
    matches = []
    monkeypatch.setattr(
        receipts,
        "_find_execution_target",
        lambda *args, **kwargs: matches.append((args, kwargs)) or None,
    )
    monkeypatch.setattr(receipts, "_get_fast_state", lambda _code: None)
    monkeypatch.setattr(receipts, "log_error", lambda _message: None)

    for exec_type in ("BUY_CANCEL", "SELL_CANCEL", "UNKNOWN"):
        receipts.handle_real_execution(
            {
                "code": "005930",
                "type": exec_type,
                "order_no": "O1",
                "price": 70_000,
                "qty": 1,
            }
        )

    assert matches == []


class _SyncSession:
    def __init__(self, active_records, pending_records, history_records=None):
        self._active_records = active_records
        self._pending_records = pending_records
        self._history_records = history_records or []
        self._mode = None
        self._stock_code = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        self._mode = None
        self._stock_code = None
        return self

    def filter(self, *args, **kwargs):
        self._mode = "active"
        return self

    def filter_by(self, **kwargs):
        self._mode = kwargs.get("status")
        self._stock_code = kwargs.get("stock_code")
        return self

    def all(self):
        if self._stock_code is not None:
            return [
                record
                for record in self._history_records
                if getattr(record, "stock_code", None) == self._stock_code
            ]
        if self._mode == "BUY_ORDERED":
            return list(self._pending_records)
        return list(self._active_records)

    def add(self, record):
        self._history_records.append(record)

    def flush(self):
        for idx, record in enumerate(self._history_records, start=1):
            if getattr(record, "id", None) is None:
                record.id = 9000 + idx

    def refresh(self, record, *, with_for_update=False):
        return None

    def commit(self):
        return None


class _SyncDB:
    def __init__(self, active_records, pending_records=None, history_records=None):
        self._session = _SyncSession(
            active_records, pending_records or [], history_records or []
        )

    def get_session(self):
        return self._session

    def get_latest_is_nxt(self, code):
        return False

    def get_latest_marcap(self, code):
        return 0


class _FailingSyncDB(_SyncDB):
    def get_session(self):
        session = super().get_session()

        class _FailingSession:
            def __enter__(self_inner):
                return session.__enter__()

            def __exit__(self_inner, exc_type, exc, tb):
                session.__exit__(exc_type, exc, tb)
                raise RuntimeError("commit failed")

        return _FailingSession()


class _S15Session:
    def __init__(self, record=None):
        self.record = record
        self.added = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return self

    def filter_by(self, **kwargs):
        return self

    def first(self):
        return self.record

    def add(self, record):
        self.record = record
        self.added = record


class _S15DB:
    def __init__(self, session):
        self._session = session

    def get_session(self):
        return self._session


class _DummyLock:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


class _StateQuery:
    def __init__(self, record):
        self.record = record

    def filter_by(self, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.record

    def update(self, values):
        if self.record is not None:
            for key, value in values.items():
                setattr(self.record, key, value)
        return 1


class _StateSession:
    def __init__(self, record):
        self.record = record

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, *args, **kwargs):
        return _StateQuery(self.record)


class _StateDB:
    def __init__(self, record):
        self.record = record

    def get_session(self):
        return _StateSession(self.record)

    def get_latest_is_nxt(self, _code):
        return False


def test_trade_profit_helper_accounts_for_costs():
    assert calculate_net_profit_rate(100000, 100100) == -0.13
    assert calculate_net_profit_rate(14320, 14420) == 0.47


def test_trailing_continuation_lineage_is_snapshotted_then_reset():
    stock = {
        "scalp_trailing_continuation_recheck_consumed_id": "scr-runtime-7",
        "scalp_trailing_continuation_recheck_consumed_position_key": (
            "runtime:123456:position-7"
        ),
    }

    fields = receipts._trailing_continuation_receipt_fields(stock)

    assert fields == {
        "trailing_continuation_recheck_id": "scr-runtime-7",
        "trailing_continuation_position_key": "runtime:123456:position-7",
    }
    assert all(key in receipts._SELL_RECEIPT_SNAPSHOT_KEYS for key in stock)
    assert all(key in receipts._SELL_COMPLETE_RESET_KEYS for key in stock)
    assert (
        "scalp_trailing_continuation_runtime_position_token"
        in receipts._SELL_COMPLETE_RESET_KEYS
    )
    assert "smoothing_source_only_path_journals" in receipts._SELL_COMPLETE_RESET_KEYS
    assert "smoothing_source_only_path_journals" not in receipts._SELL_REVIVE_RESET_KEYS


def test_scalp_revive_preserves_active_post_sell_smoothing_journal(monkeypatch):
    journal_state = {
        "schema_version": "smoothing_source_only_path_journal_v1",
        "arms": {"sj-1": {"arm_id": "sj-1"}},
    }
    stock = {
        "name": "TEST",
        "smoothing_source_only_path_journals": journal_state,
        "nxt_rising_missed_tp1_partial_pending": True,
        "nxt_rising_missed_tp1_partial_applied": True,
        "nxt_rising_missed_tp1_partial_requested_qty": 5,
        "nxt_rising_missed_tp1_partial_filled_qty": 3,
        "nxt_rising_missed_tp1_partial_fill_amount": 30_300,
        "nxt_rising_missed_tp1_partial_executions_by_no": {"E1": {}},
    }

    monkeypatch.setattr(
        receipts.POSITION_PEAK_LEDGER, "remove_for_stock", lambda _stock: None
    )
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(
        receipts, "move_orders_to_terminal", lambda *_args, **_kwargs: None
    )
    receipts._apply_scalp_revive_memory_state(
        target_stock=stock,
        code="123456",
        new_watch_id=8,
        revived_position_tag="SCANNER",
        revived_at_ts=1000.0,
    )

    assert stock["status"] == "WATCHING"
    assert stock["smoothing_source_only_path_journals"] is journal_state
    assert not any(key in stock for key in receipts._NXT_TP1_PARTIAL_RESET_KEYS)


def test_non_revive_sell_registers_smoothing_journal_before_runtime_reset(
    monkeypatch, tmp_path
):
    journal_state = {
        "schema_version": "smoothing_source_only_path_journal_v1",
        "arms": {"sj-1": {"arm_id": "sj-1"}},
    }
    stock = {
        "id": 7,
        "name": "TEST",
        "code": "123456",
        "smoothing_source_only_path_journals": journal_state,
    }
    registered = []
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "buy_qty": 1,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
        },
    )()
    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    monkeypatch.setattr(
        receipts.POSITION_PEAK_LEDGER, "remove_for_stock", lambda _stock: None
    )
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(
        receipts, "move_orders_to_terminal", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        receipts,
        "_smoothing_non_revive_post_sell_register_callback",
        lambda target, code, *, now_ts: (
            registered.append(
                (target["smoothing_source_only_path_journals"], code, now_ts)
            )
            or {
                "registered": True,
                "status": "registered",
                "active_arm_count": 1,
                "expires_at_epoch": now_ts + 90,
            }
        ),
    )
    monkeypatch.setattr(
        receipts.threading,
        "Thread",
        lambda **_kwargs: type("DeferredThread", (), {"start": lambda _self: None})(),
    )
    logged = []
    _install_successful_sell_lifecycle_outbox(monkeypatch, logged)

    receipts._finalize_standard_sell_execution(
        target_id=7,
        exec_price=10_000,
        now=datetime(2026, 8, 10, 15, 31, 0),
        target_stock=stock,
        strategy="SCALPING",
        is_scalp_revive=False,
        code="123456",
        sell_receipt={
            "status": "final",
            "final": True,
            "expected_qty": 1,
            "cumulative_qty": 1,
            "cumulative_amount": 10_000,
            "cumulative_net_pnl_krw": 0,
            "incremental_qty": 1,
            "incremental_price": 10_000,
            "incremental_net_pnl_krw": 0,
            "economics_complete": True,
        },
        order_no="sell-1",
        safe_buy_price=10_000.0,
    )

    assert registered[0][0] is journal_state
    assert registered[0][1] == "123456"
    assert stock["status"] == "COMPLETED"
    assert "smoothing_source_only_path_journals" not in stock
    assert [stage for stage, _fields in logged] == ["sell_completed"]


def test_sell_receipt_persists_net_profit_rate(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "buy_price": 100000.0,
            "buy_qty": 1,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
        },
    )()

    receipts.DB = _ReceiptDB(record)
    receipts.event_bus = _Bus()
    logged = {}
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: logged.update(kwargs),
    )

    receipts._update_db_for_sell(
        7,
        100100,
        datetime(2026, 4, 7, 9, 0, 0),
        {
            "code": "123456",
            "name": "TEST",
            "msg_audience": "ADMIN_ONLY",
            **_completed_sell_receipt_fields(
                buy_price=100000.0, sell_price=100100, qty=1
            ),
        },
        "SCALPING",
        False,
    )

    assert record.status == "COMPLETED"
    assert record.sell_price == 100100
    assert record.profit_rate == -0.13
    assert logged == {}
    assert receipts.event_bus.events
    _, payload = receipts.event_bus.events[-1]
    assert "-0.13%" in payload["message"]


def test_standard_sell_waits_for_full_cumulative_receipt_and_emits_exact_legs(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
        },
    )()
    stock = {
        "id": 7,
        "code": "123456",
        "name": "PARTIAL",
        "status": "SELL_ORDERED",
        "sell_odno": "0000701",
        "buy_price": 10_000.0,
        "buy_qty": 10,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        # The entry happened on KRX; the SELL receipt below must own the exit
        # venue/session instead of inheriting these entry dimensions.
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
        "last_sell_execution_broker_route": "SOR",
        "last_sell_execution_broker_route_resolution": "submit_response",
        "last_sell_execution_cohort": "KRX",
        "last_sell_execution_session_bucket": "krx_regular",
    }
    logged = []

    class _ImmediateThread:
        def __init__(self, *, target, args, daemon):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(receipts, "event_bus", _Bus())
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(receipts, "_get_fast_state", lambda _code: None)
    monkeypatch.setattr(
        receipts,
        "_resolve_sell_execution_context",
        lambda *_args: (record, 10_000.0, 0.0, "SCALPING", False),
    )
    monkeypatch.setattr(receipts.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(
        receipts.POSITION_PEAK_LEDGER, "remove_for_stock", lambda _stock: None
    )
    monkeypatch.setattr(
        receipts, "move_orders_to_terminal", lambda *_args, **_kwargs: None
    )
    def _capture_successful_outbox(*args, **kwargs):
        logged.append((args[3], kwargs))
        return {
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        }

    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        _capture_successful_outbox,
    )
    monkeypatch.setattr(
        receipts,
        "_sell_lifecycle_outbox_event_contract_valid",
        lambda **_kwargs: True,
    )
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **_kwargs: {})
    monkeypatch.setattr(receipts, "_scalp_exit_completed_callback", None)
    monkeypatch.setattr(
        receipts, "_smoothing_non_revive_post_sell_register_callback", None
    )

    partial = {
        "code": "123456",
        "type": "SELL",
        "order_no": "0000701",
        "price": 10_010,
        "qty": 2,
        "order_qty": 10,
        "remaining_qty": 8,
        "cumulative_exec_amount": 20_020,
        "execution_no": "0000001",
        "unit_exec_price": 10_010,
        "unit_exec_qty": 2,
        "broker_execution_time_raw": "180003",
        "broker_execution_received_at": "2026-08-25T18:00:03.250000+09:00",
        "broker_execution_receive_time_source": "websocket_packet_ingress",
        "actual_execution_venue": "NXT",
        "actual_exchange_code": "2",
        "actual_exchange_name": "NXT",
        "sor_flag": "Y",
        "main_lifecycle_broker_raw_envelope_schema": (
            "kiwoom_websocket_order_execution_00_values_v1"
        ),
        "main_lifecycle_broker_raw_source_type": "00",
        "9203": "0000701",
        "9001": "123456",
        "913": "체결",
        "900": "10",
        "902": "8",
        "903": "20020",
        "905": "-매도",
        "907": "1",
        "908": "180003",
        "909": "0000001",
        "910": "10010",
        "911": "2",
        "914": "10010",
        "915": "2",
        "2134": "2",
        "2135": "NXT",
        "2136": "Y",
    }
    receipts.handle_real_execution(partial)
    receipts.handle_real_execution(partial)

    assert stock["status"] == "SELL_ORDERED"
    assert record.status == "SELL_ORDERED"
    assert [stage for stage, _fields in logged] == ["sell_partial_fill_progress"]
    receipt_state = stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY]
    assert receipt_state["cumulative_qty"] == 2
    assert receipt_state["remaining_qty"] == 8
    partial_fields = logged[0][1]
    assert partial_fields["main_lifecycle_exit_qty"] == 2
    assert partial_fields["main_lifecycle_exit_price"] == 10_010
    assert partial_fields["main_lifecycle_reconciled_final_exit"] is False
    assert partial_fields["effective_venue"] == "NXT"
    assert partial_fields["exit_effective_venue"] == "NXT"
    assert partial_fields["market_session_bucket"] == "nxt_entry_window"
    assert partial_fields["exit_market_session_bucket"] == "nxt_entry_window"
    assert partial_fields["exit_market_session_time_source"] == (
        "websocket_packet_ingress"
    )
    assert partial_fields["broker_route"] == "SOR"

    receipts.handle_real_execution(
        {
            "code": "123456",
            "type": "SELL",
            "order_no": "0000701",
            "price": 10_020,
            "qty": 10,
            "order_qty": 10,
            "remaining_qty": 0,
            "cumulative_exec_amount": 100_180,
            "execution_no": "0000002",
            "unit_exec_price": 10_020,
            "unit_exec_qty": 8,
            "broker_execution_time_raw": "180004",
            "broker_execution_received_at": "2026-08-25T18:00:04.350000+09:00",
            "broker_execution_receive_time_source": "websocket_packet_ingress",
            "actual_execution_venue": "NXT",
            "actual_exchange_code": "2",
            "actual_exchange_name": "NXT",
            "sor_flag": "Y",
            "main_lifecycle_broker_raw_envelope_schema": (
                "kiwoom_websocket_order_execution_00_values_v1"
            ),
            "main_lifecycle_broker_raw_source_type": "00",
            "9203": "0000701",
            "9001": "123456",
            "913": "체결",
            "900": "10",
            "902": "0",
            "903": "100180",
            "905": "-매도",
            "907": "1",
            "908": "180004",
            "909": "0000002",
            "910": "10020",
            "911": "10",
            "914": "10020",
            "915": "8",
            "2134": "2",
            "2135": "NXT",
            "2136": "Y",
        }
    )

    expected_net = calculate_net_realized_pnl(10_000, 10_010, 2) + (
        calculate_net_realized_pnl(10_000, 10_020, 8)
    )
    assert stock["status"] == "COMPLETED"
    assert record.status == "COMPLETED"
    assert record.sell_price == 10_018
    assert record.profit_rate == pytest.approx(expected_net / 100_000 * 100)
    assert [stage for stage, _fields in logged] == [
        "sell_partial_fill_progress",
        "sell_completed",
    ]
    final_fields = logged[-1][1]
    assert final_fields["main_lifecycle_exit_qty"] == 8
    assert final_fields["main_lifecycle_exit_price"] == 10_020
    assert final_fields["main_lifecycle_reconciled_final_exit"] is True
    assert final_fields["main_lifecycle_broker_reconciled"] is True
    assert final_fields["effective_venue"] == "NXT"
    assert final_fields["exit_effective_venue"] == "NXT"
    assert final_fields["market_session_bucket"] == "nxt_entry_window"
    assert final_fields["exit_market_session_bucket"] == "nxt_entry_window"
    assert final_fields["exit_market_session_time_source"] == (
        "websocket_packet_ingress"
    )
    assert final_fields["broker_route"] == "SOR"

    # Exercise the real SELL producer payload through the canonical consumer.
    # The long-lived position still carries its KRX entry context, but the
    # receipt-local NXT venue/session must win for this exit transition.
    lifecycle_stock = {
        "id": 7,
        "code": "123456",
        "name": "PARTIAL",
        "scanner_promotion_id": "SCANPROM-123456-1787000000000",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    lifecycle_source_fields = {
        key: value
        for key, value in final_fields.items()
        if key not in {"candidate_stock", "observed_at"}
    }
    lifecycle_source_fields.update(
        pipeline_lifecycle_fields_safe(
            lifecycle_stock,
            lifecycle_stock["code"],
            pipeline="HOLDING_PIPELINE",
            source_stage="sell_completed",
            source_fields=lifecycle_source_fields,
            observed_at=final_fields["observed_at"],
        )
    )
    transition, error, in_scope = paired._validated_pipeline_transition(
        {
            "event_type": "pipeline_event",
            "pipeline": "HOLDING_PIPELINE",
            "stage": "sell_completed",
            "stock_name": lifecycle_stock["name"],
            "stock_code": lifecycle_stock["code"],
            "record_id": lifecycle_stock["id"],
            "fields": lifecycle_source_fields,
        },
        target_date="2026-08-25",
    )
    assert error is None
    assert in_scope is True
    assert transition is not None
    assert lifecycle_stock["effective_venue"] == "KRX"
    assert lifecycle_stock["market_session_bucket"] == "krx_regular"
    assert transition["venue"] == "NXT"
    assert transition["session_bucket"] == "nxt_entry_window"
    assert transition["data"].get("broker_execution_actual_venue") == "NXT", (
        transition["data"]
    )


def test_final_cumulative_sell_closes_custody_but_keeps_unit_gap_source_only(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
        },
    )()
    stock = {
        "id": 71,
        "code": "123456",
        "name": "DROPPED_LEGS",
        "status": "SELL_ORDERED",
        "sell_odno": "SELL-FINAL",
        "buy_price": 10_000.0,
        "buy_qty": 10,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
    }
    logged = []

    class _ImmediateThread:
        def __init__(self, *, target, args, daemon):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(receipts, "event_bus", _Bus())
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(receipts, "_get_fast_state", lambda _code: None)
    monkeypatch.setattr(
        receipts,
        "_resolve_sell_execution_context",
        lambda *_args: (record, 10_000.0, 0.0, "SCALPING", False),
    )
    monkeypatch.setattr(receipts.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(
        receipts.POSITION_PEAK_LEDGER, "remove_for_stock", lambda _stock: None
    )
    monkeypatch.setattr(
        receipts, "move_orders_to_terminal", lambda *_args, **_kwargs: None
    )
    _install_successful_sell_lifecycle_outbox(monkeypatch, logged)
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **_kwargs: {})
    monkeypatch.setattr(receipts, "_scalp_exit_completed_callback", None)
    monkeypatch.setattr(
        receipts, "_smoothing_non_revive_post_sell_register_callback", None
    )

    receipts.handle_real_execution(
        {
            "code": "123456",
            "type": "SELL",
            "order_no": "SELL-FINAL",
            "price": 10_010,
            "qty": 10,
            "order_qty": 10,
            "remaining_qty": 0,
            "cumulative_exec_amount": 100_100,
            "execution_no": "E-FINAL",
            "unit_exec_price": 10_010,
            # FID 915 is the last execution leg, not the missed cumulative legs.
            "unit_exec_qty": 2,
            "broker_execution_time_raw": "090003",
            "actual_execution_venue": "KRX",
            "actual_exchange_code": "1",
            "actual_exchange_name": "KRX",
            "sor_flag": "N",
        }
    )

    assert stock["status"] == "COMPLETED"
    assert record.status == "COMPLETED"
    assert record.sell_price == 10_010
    assert [stage for stage, _ in logged] == ["sell_completed"]
    final_fields = logged[0][1]
    assert final_fields["main_lifecycle_reconciled_final_exit"] is True
    assert final_fields["sell_execution_receipt_unit_fill_consistent"] is False
    data, reason = paired._pipeline_transition_data(
        lifecycle_stage="exit",
        source_stage="sell_completed",
        lifecycle_stock_code="123456",
        lifecycle_venue="KRX",
        lifecycle_observed_at="2026-08-25T09:00:03+09:00",
        lifecycle_trade_date="2026-08-25",
        fields=final_fields,
    )
    assert data is not None
    assert reason is None
    assert data["broker_execution_provenance_state"] == "missing"


def test_sell_receipt_cancel_retry_carries_position_economics_exactly(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
        },
    )()
    stock = {
        "id": 7,
        "code": "123456",
        "name": "RETRY",
        "status": "SELL_ORDERED",
        "sell_odno": "SELL-1",
        "buy_price": 10_000.0,
        "buy_qty": 10,
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
    }
    logged = []

    class _ImmediateThread:
        def __init__(self, *, target, args, daemon):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(receipts, "event_bus", _Bus())
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    monkeypatch.setattr(receipts, "highest_prices", {})
    monkeypatch.setattr(receipts, "_get_fast_state", lambda _code: None)
    monkeypatch.setattr(
        receipts,
        "_resolve_sell_execution_context",
        lambda *_args: (record, 10_000.0, 0.0, "SCALPING", False),
    )
    monkeypatch.setattr(receipts.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(
        receipts.POSITION_PEAK_LEDGER, "remove_for_stock", lambda _stock: None
    )
    monkeypatch.setattr(
        receipts, "move_orders_to_terminal", lambda *_args, **_kwargs: None
    )
    _install_successful_sell_lifecycle_outbox(monkeypatch, logged)
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **_kwargs: {})
    monkeypatch.setattr(receipts, "_scalp_exit_completed_callback", None)
    monkeypatch.setattr(
        receipts, "_smoothing_non_revive_post_sell_register_callback", None
    )

    receipts.handle_real_execution(
        {
            "code": "123456",
            "type": "SELL",
            "order_no": "SELL-1",
            "price": 10_010,
            "qty": 2,
            "order_qty": 10,
            "remaining_qty": 8,
            "cumulative_exec_amount": 20_020,
            "execution_no": "E-1",
            "unit_exec_price": 10_010,
            "unit_exec_qty": 2,
        }
    )
    reconciliation = state_handlers._rotate_cancelled_sell_receipt_ledger(
        stock,
        orig_ord_no="SELL-1",
        broker_qty=8,
    )
    assert reconciliation == {
        "required": True,
        "reconciled": True,
        "reason": "cancelled_partial_carried",
        "remaining_qty": 8,
    }
    assert stock["sell_reconciled_remaining_qty"] == 8

    # A late duplicate from the cancelled order is terminal and cannot emit a
    # second lifecycle leg or mutate the carried position economics.
    receipts.handle_real_execution(
        {
            "code": "123456",
            "type": "SELL",
            "order_no": "SELL-1",
            "price": 10_010,
            "qty": 2,
            "order_qty": 10,
            "remaining_qty": 8,
            "cumulative_exec_amount": 20_020,
            "execution_no": "E-1",
            "unit_exec_price": 10_010,
            "unit_exec_qty": 2,
        }
    )
    assert [stage for stage, _fields in logged] == ["sell_partial_fill_progress"]

    stock["status"] = "SELL_ORDERED"
    stock["sell_odno"] = "SELL-2"
    receipts.handle_real_execution(
        {
            "code": "123456",
            "type": "SELL",
            "order_no": "SELL-2",
            "price": 10_020,
            "qty": 8,
            "order_qty": 8,
            "remaining_qty": 0,
            "cumulative_exec_amount": 80_160,
            "execution_no": "E-2",
            "unit_exec_price": 10_020,
            "unit_exec_qty": 8,
        }
    )

    expected_net = calculate_net_realized_pnl(10_000, 10_018, 10)
    assert stock["status"] == "COMPLETED"
    assert record.status == "COMPLETED"
    assert record.sell_price == 10_018
    assert record.profit_rate == pytest.approx(expected_net / 100_000 * 100)
    assert [stage for stage, _fields in logged] == [
        "sell_partial_fill_progress",
        "sell_completed",
    ]
    assert [fields["main_lifecycle_exit_qty"] for _stage, fields in logged] == [
        2,
        8,
    ]
    assert (
        sum(fields["main_lifecycle_realized_net_pnl_krw"] for _stage, fields in logged)
        == expected_net
    )


def test_sell_receipt_modeled_pnl_is_packet_split_invariant():
    single_stock = {"name": "SINGLE"}
    single = receipts._resolve_sell_execution_receipt(
        single_stock,
        order_no="SINGLE-1",
        exec_price=9_000,
        cumulative_exec_qty=2,
        expected_position_qty=2,
        buy_price=9_000,
        order_qty=2,
        remaining_qty=0,
        cumulative_exec_amount=18_000,
        execution_no="E-2",
        unit_exec_price=9_000,
        unit_exec_qty=2,
    )

    split_stock = {"name": "SPLIT"}
    first = receipts._resolve_sell_execution_receipt(
        split_stock,
        order_no="SPLIT-1",
        exec_price=9_000,
        cumulative_exec_qty=1,
        expected_position_qty=2,
        buy_price=9_000,
        order_qty=2,
        remaining_qty=1,
        cumulative_exec_amount=9_000,
        execution_no="E-1",
        unit_exec_price=9_000,
        unit_exec_qty=1,
    )
    second = receipts._resolve_sell_execution_receipt(
        split_stock,
        order_no="SPLIT-1",
        exec_price=9_000,
        cumulative_exec_qty=2,
        expected_position_qty=2,
        buy_price=9_000,
        order_qty=2,
        remaining_qty=0,
        cumulative_exec_amount=18_000,
        execution_no="E-2",
        unit_exec_price=9_000,
        unit_exec_qty=1,
    )

    assert single["status"] == second["status"] == "final"
    assert single["cumulative_net_pnl_krw"] == second["cumulative_net_pnl_krw"]
    assert (
        first["incremental_net_pnl_krw"] + second["incremental_net_pnl_krw"]
        == single["cumulative_net_pnl_krw"]
    )


def test_sell_retry_cancel_without_new_fill_uses_carried_remaining_qty():
    stock = {
        "name": "RETRY-CANCEL",
        "buy_qty": 10,
        receipts._SELL_EXECUTION_RECEIPT_STATE_KEY: {
            "order_no": "",
            "position_qty": 10,
            "expected_qty": 0,
            "cumulative_qty": 0,
            "cumulative_amount": 0,
            "carried_qty": 2,
            "carried_amount": 20_020,
            "carried_net_pnl_krw": -26,
            "prior_orders": {
                "SELL-1": {
                    "expected_qty": 10,
                    "cumulative_qty": 2,
                    "cumulative_amount": 20_020,
                    "remaining_qty": 8,
                }
            },
        },
    }

    reconciliation = state_handlers._rotate_cancelled_sell_receipt_ledger(
        stock,
        orig_ord_no="SELL-2",
        broker_qty=8,
    )

    assert reconciliation == {
        "required": False,
        "reconciled": True,
        "reason": "no_partial_fill",
        "remaining_qty": 8,
    }
    assert stock["sell_reconciled_remaining_qty"] == 8


def test_sell_receipt_remaining_conflict_fails_closed_without_state_mutation():
    stock = {"name": "CONFLICT"}

    receipt = receipts._resolve_sell_execution_receipt(
        stock,
        order_no="SELL-1",
        exec_price=10_010,
        cumulative_exec_qty=2,
        expected_position_qty=10,
        buy_price=10_000,
        order_qty=10,
        remaining_qty=0,
        cumulative_exec_amount=20_020,
        execution_no="E-1",
        unit_exec_price=10_010,
        unit_exec_qty=2,
    )

    assert receipt == {
        "status": "invalid",
        "reason": "sell_receipt_remaining_quantity_conflict",
    }
    assert receipts._SELL_EXECUTION_RECEIPT_STATE_KEY not in stock


def test_scalp_sell_receipt_reconciles_rising_missed_reentry_context(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "buy_price": 100000.0,
            "buy_qty": 1,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
        },
    )()
    calls = []
    receipts.DB = _ReceiptDB(record)
    receipts.event_bus = _Bus()
    monkeypatch.setattr(receipts, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **kwargs: {})
    monkeypatch.setattr(
        receipts,
        "_scalp_exit_completed_callback",
        lambda code, **kwargs: calls.append((code, kwargs)),
    )
    completed_at = datetime(2026, 7, 31, 10, 24, 32)

    receipts._update_db_for_sell(
        7,
        100500,
        completed_at,
        {
            "code": "096770",
            "name": "SK innovation",
            "msg_audience": "ADMIN_ONLY",
            "last_exit_rule": "scalp_trailing_take_profit",
            **_completed_sell_receipt_fields(
                buy_price=100000.0, sell_price=100500, qty=1
            ),
        },
        "SCALPING",
        False,
    )

    assert len(calls) == 1
    code, kwargs = calls[0]
    assert code == "096770"
    assert kwargs["profit_rate"] == record.profit_rate
    assert kwargs["exit_price"] == 100500
    assert kwargs["exit_rule"] == "scalp_trailing_take_profit"
    assert kwargs["completed_at"] == completed_at.timestamp()


def test_scalp_sell_commit_failure_never_releases_reentry(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "buy_price": 100000.0,
            "buy_qty": 1,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "position_tag": "DEFAULT",
        },
    )()
    calls = []

    class FailingReceiptDB(_ReceiptDB):
        def get_session(self):
            session = _ReceiptSession(self.record)

            def fail_commit():
                raise RuntimeError("commit failed")

            session.commit = fail_commit
            return session

    receipts.DB = FailingReceiptDB(record)
    receipts.event_bus = _Bus()
    monkeypatch.setattr(receipts, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **kwargs: {})
    monkeypatch.setattr(
        receipts,
        "_scalp_exit_completed_callback",
        lambda code, **kwargs: calls.append((code, kwargs)),
    )

    committed = receipts._update_db_for_sell(
        7,
        100500,
        datetime(2026, 7, 31, 10, 24, 32),
        {
            "code": "096770",
            "name": "SK innovation",
            "msg_audience": "ADMIN_ONLY",
            **_completed_sell_receipt_fields(
                buy_price=100000.0, sell_price=100500, qty=1
            ),
        },
        "SCALPING",
        False,
    )

    assert committed is False
    assert calls == []


def test_scalp_revive_sell_receipt_declares_real_execution_contract(
    monkeypatch, tmp_path
):
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "stock_name": "TEST",
            "prob": 0.8,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
        },
    )()

    class _ReviveSession(_ReceiptSession):
        def add(self, added):
            added.id = 99

        def flush(self):
            return None

    class _ReviveDB:
        def get_session(self):
            return _ReviveSession(record)

    logged = []
    stock = {
        "id": 7,
        "code": "123456",
        "name": "TEST",
        "buy_price": 10_000.0,
        "buy_qty": 10,
        "position_tag": "SCANNER",
        "nxt_rising_missed_tp1_partial_filled_qty": 4,
        "nxt_rising_missed_tp1_partial_fill_amount": 40_480,
    }
    monkeypatch.setattr(receipts, "DB", _ReviveDB())
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [stock])
    _install_successful_sell_lifecycle_outbox(monkeypatch, logged)
    monkeypatch.setattr(
        receipts, "_publish_sell_execution_message", lambda **kwargs: None
    )
    monkeypatch.setattr(receipts, "record_post_sell_candidate", lambda **kwargs: {})
    monkeypatch.setattr(
        receipts, "_apply_scalp_revive_memory_state", lambda **kwargs: None
    )

    handled = receipts._handle_scalp_revive_sell_execution(
        target_id=7,
        target_stock=stock,
        code="123456",
        exec_price=10_100,
        exec_qty=3,
        now=datetime(2026, 7, 23, 10, 0, 0),
        profit_rate=0.77,
        safe_buy_price=10_000,
        strategy="SCALPING",
        sell_receipt={
            "status": "final",
            "final": True,
            "cumulative_qty": 10,
            "cumulative_amount": 101_080,
            "cumulative_net_pnl_krw": calculate_net_realized_pnl(10_000, 10_108, 10),
            "incremental_qty": 6,
            "incremental_price": 10_100,
            "incremental_net_pnl_krw": calculate_net_realized_pnl(10_000, 10_108, 10)
            - calculate_net_realized_pnl(10_000, 10_120, 4),
            "economics_complete": True,
        },
    )

    assert handled is True
    assert [stage for stage, _fields in logged] == ["sell_completed"]
    logged_fields = logged[0][1]
    assert logged_fields["actual_order_submitted"] is True
    assert logged_fields["broker_order_forbidden"] is False
    assert logged_fields["metric_role"] == "execution_quality_real_only"
    assert logged_fields["decision_authority"] == "broker_sell_fill_observation_only"
    assert logged_fields["window_policy"] == "same_position_cycle_broker_fill"
    assert logged_fields["sample_floor"] == "1_confirmed_broker_sell_fill"
    assert (
        logged_fields["primary_decision_metric"]
        == "confirmed_sell_fill_price_and_profit_rate"
    )
    assert logged_fields["sell_price"] == 10_108
    assert logged_fields["sell_qty"] == 10
    assert record.buy_qty == 10
    assert logged_fields["buy_price"] == 10_000
    assert logged_fields["buy_qty"] == 10
    assert logged_fields["realized_pnl_krw"] == calculate_net_realized_pnl(
        10_000, 10_108, 10
    )
    assert logged_fields["realized_pnl_krw_source"] == (
        "broker_fill_prices_fee_aware"
    )
    assert logged_fields["main_lifecycle_broker_reconciled"] is True
    assert logged_fields["main_lifecycle_reconciled_final_exit"] is True
    final_leg_net_pnl = calculate_net_realized_pnl(
        10_000, 10_108, 10
    ) - calculate_net_realized_pnl(10_000, 10_120, 4)
    assert logged_fields["main_lifecycle_realized_net_pnl_krw"] == final_leg_net_pnl
    assert logged_fields["main_lifecycle_fees_taxes_krw"] == (
        600 - final_leg_net_pnl
    )


def test_sell_receipt_propagates_scale_in_counterfactual_diagnostics(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "buy_price": 100000.0,
            "buy_qty": 20,
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
        },
    )()

    receipts.DB = _ReceiptDB(record)
    receipts.event_bus = _Bus()
    logged = {}
    post_sell_calls = []

    def _capture_log(*args, **kwargs):
        logged["args"] = args
        logged["kwargs"] = kwargs

    def _capture_post_sell(**kwargs):
        post_sell_calls.append(kwargs)
        return {"post_sell_id": "TEST"}

    monkeypatch.setattr(receipts, "_log_holding_pipeline", _capture_log)
    monkeypatch.setattr(receipts, "record_post_sell_candidate", _capture_post_sell)

    receipt_snapshot = {
        "code": "123456",
        "name": "TEST",
        "msg_audience": "ADMIN_ONLY",
        "pre_add_avg_price": 97000.0,
        "post_add_avg_price": 100000.0,
        "pre_add_qty": 10,
        "post_add_qty": 20,
        "last_exit_rule": "protect_trailing_stop",
        "scalp_trailing_continuation_recheck_consumed_id": "scr-runtime-7",
        "scalp_trailing_continuation_recheck_consumed_position_key": (
            "runtime:123456:position-7"
        ),
        **_completed_sell_receipt_fields(buy_price=100000.0, sell_price=100100, qty=20),
    }

    receipts._update_db_for_sell(
        7,
        100100,
        datetime(2026, 4, 7, 9, 0, 0),
        receipt_snapshot,
        "SCALPING",
        False,
    )

    assert receipt_snapshot[
        "no_scale_in_counterfactual_profit_pct"
    ] == calculate_net_profit_rate(97000.0, 100100)
    assert receipt_snapshot["scale_in_incremental_realized_delta_pct"] == round(
        record.profit_rate - receipt_snapshot["no_scale_in_counterfactual_profit_pct"],
        4,
    )
    # The DB transaction no longer emits a second sell_completed row.
    assert logged == {}
    assert len(post_sell_calls) == 1
    assert (
        post_sell_calls[0]["stock"]["no_scale_in_counterfactual_profit_pct"]
        == receipt_snapshot["no_scale_in_counterfactual_profit_pct"]
    )
    assert (
        post_sell_calls[0]["stock"]["scale_in_incremental_realized_delta_pct"]
        == receipt_snapshot["scale_in_incremental_realized_delta_pct"]
    )


def test_opening_rotation_sell_receipt_keeps_tag_and_realized_pnl(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "buy_qty": 400,
            "position_tag": "OPENING_ROTATION_1PCT",
            "status": "SELL_ORDERED",
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
        },
    )()
    receipts.DB = _ReceiptDB(record)
    receipts.event_bus = _Bus()
    logged = {}
    post_sell_calls = []
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: logged.update(kwargs),
    )
    monkeypatch.setattr(
        receipts,
        "record_post_sell_candidate",
        lambda **kwargs: post_sell_calls.append(kwargs) or {"post_sell_id": "TEST"},
    )
    snapshot = {
        "code": "123456",
        "name": "TEST",
        "msg_audience": "ADMIN_ONLY",
        "position_tag": "OPENING_ROTATION_1PCT",
        "strategy": "SCALPING",
        "opening_rotation_entry_time_bucket": "09:00-09:30",
        "opening_rotation_window_version": "opening_rotation_0910_1500_v1",
        **_completed_sell_receipt_fields(
            buy_price=10_000.0, sell_price=10_150, qty=400
        ),
    }

    receipts._update_db_for_sell(
        7,
        10_150,
        datetime(2026, 7, 20, 9, 11, 0),
        snapshot,
        "SCALPING",
        False,
    )

    assert logged == {}
    assert post_sell_calls[0]["stock"]["position_tag"] == "OPENING_ROTATION_1PCT"
    assert post_sell_calls[0]["stock"]["realized_pnl_krw"] > 30_000
    assert post_sell_calls[0]["stock"]["actual_order_submitted"] is True
    assert post_sell_calls[0]["stock"]["broker_order_forbidden"] is False


def test_opening_rotation_intraday_sell_does_not_revive_same_symbol():
    record = type(
        "Record",
        (),
        {
            "buy_price": 10_000.0,
            "strategy": "SCALPING",
            "position_tag": "OPENING_ROTATION_1PCT",
        },
    )()
    receipts.DB = _ReceiptDB(record)

    context = receipts._resolve_sell_execution_context(
        7,
        {
            "strategy": "SCALPING",
            "position_tag": "OPENING_ROTATION_1PCT",
        },
        10_150,
        datetime(2026, 7, 20, 9, 30).time(),
    )

    assert context is not None
    assert context[-1] is False


def test_periodic_account_sync_does_not_invent_pnl_for_missing_sell_receipt(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "stock_code": "123456",
            "stock_name": "TEST",
            "status": "SELL_ORDERED",
            "buy_price": 100000.0,
            "buy_qty": 1,
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [
        {"code": "123456", "status": "SELL_ORDERED", "sell_target_price": 100100}
    ]
    sniper_sync.HIGHEST_PRICES = {"123456": 100500}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [],
    )
    removals = []

    def fake_remove_manual_control_exclusion_code(code, *, reason):
        removals.append({"code": code, "reason": reason})
        return type(
            "Removal",
            (),
            {
                "removed": True,
                "code": code,
                "source": "manual_control_excluded_codes.txt",
                "reason": f"manual_control_exclusion_removed:{reason}",
            },
        )()

    monkeypatch.setattr(
        sniper_sync,
        "remove_manual_control_exclusion_code",
        fake_remove_manual_control_exclusion_code,
    )
    emitted = []
    monkeypatch.setattr(
        sniper_sync,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    sniper_sync.periodic_account_sync()

    assert record.status == "COMPLETED"
    assert record.sell_price is None
    assert record.profit_rate is None
    assert sniper_sync.ACTIVE_TARGETS == []
    assert "123456" not in sniper_sync.HIGHEST_PRICES
    assert len(emitted) == 1
    assert emitted[0][0][3] == "sell_completion_reconciliation_gap"
    fields = emitted[0][1]["fields"]
    assert fields["reconciliation_result"] == (
        "broker_holding_absent_fill_receipt_missing"
    )
    assert fields["prior_sell_submission_observed"] is True
    assert fields["sell_target_price_observed"] == 100100
    assert fields["sell_target_price_forbidden_for_pnl"] is True
    assert "EV" in fields["forbidden_uses"]
    assert removals == [
        {
            "code": "123456",
            "reason": "periodic_sync_completed_no_broker_holding",
        }
    ]


def test_periodic_account_sync_blocks_partial_venue_custody_snapshot(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "id": 991,
            "rec_date": datetime(2026, 8, 15).date(),
            "stock_code": "123456",
            "stock_name": "TEST",
            "status": "HOLDING",
            "strategy": "SCALPING",
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "buy_time": datetime(2026, 8, 15, 9, 0),
            "sell_time": None,
            "scale_in_locked": False,
        },
    )()
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [
        {"id": 991, "code": "123456", "status": "HOLDING", "buy_qty": 10}
    ]
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([{"code": "123456", "qty": 0}], {"KRX"}),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: ([], {"request_succeeded": True}),
    )

    sniper_sync.periodic_account_sync()

    assert record.status == "HOLDING"
    assert record.buy_qty == 10
    assert sniper_sync.ACTIVE_TARGETS[0]["buy_qty"] == 10


def test_periodic_account_sync_defers_s15_quantity_change_to_durable_recovery(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "id": 996,
            "rec_date": datetime(2026, 8, 15).date(),
            "stock_code": "123456",
            "stock_name": "S15",
            "status": "HOLDING",
            "strategy": "S15_FAST",
            "buy_price": 10_000.0,
            "buy_qty": 10,
            "buy_time": datetime(2026, 8, 15, 9, 0),
            "sell_time": None,
            "scale_in_locked": True,
        },
    )()
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [
        {"id": 996, "code": "123456", "status": "HOLDING", "buy_qty": 10}
    ]
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "123456", "qty": 8, "buy_price": 10_000}],
            {"KRX", "NXT"},
        ),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: ([], {"request_succeeded": True}),
    )

    sniper_sync.periodic_account_sync()

    assert record.buy_qty == 10
    assert sniper_sync.ACTIVE_TARGETS[0]["buy_qty"] == 10
    assert sniper_sync.ACTIVE_TARGETS[0]["s15_custody_recovery_required"] is True
    assert sniper_sync.ACTIVE_TARGETS[0]["broker_holding_qty"] == 8


def test_periodic_account_sync_never_clones_symbol_aggregate_inventory(monkeypatch):
    records = [
        type(
            "Record",
            (),
            {
                "id": record_id,
                "rec_date": datetime(2026, 8, 15).date(),
                "stock_code": "123456",
                "stock_name": f"TEST-{record_id}",
                "status": "HOLDING",
                "strategy": "SCALPING",
                "buy_price": 10_000.0,
                "buy_qty": 10,
                "buy_time": datetime(2026, 8, 15, 9, 0),
                "sell_time": None,
                "scale_in_locked": False,
            },
        )()
        for record_id in (992, 993)
    ]
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB(records, [])
    sniper_sync.ACTIVE_TARGETS = [
        {"id": item.id, "code": "123456", "status": "HOLDING", "buy_qty": 10}
        for item in records
    ]
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "123456", "qty": 20, "buy_price": 10_000}],
            {"KRX", "NXT"},
        ),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: ([], {"request_succeeded": True}),
    )

    sniper_sync.periodic_account_sync()

    assert [record.buy_qty for record in records] == [10, 10]
    assert all(record.scale_in_locked for record in records)
    assert all(
        target["broker_symbol_allocation_conflict"] is True
        for target in sniper_sync.ACTIVE_TARGETS
    )


def test_periodic_account_sync_counts_pending_buy_as_symbol_custody_owner(monkeypatch):
    records = [
        type(
            "Record",
            (),
            {
                "id": 994,
                "rec_date": datetime(2026, 8, 15).date(),
                "stock_code": "123456",
                "stock_name": "HELD",
                "status": "HOLDING",
                "strategy": "SCALPING",
                "buy_price": 10_000.0,
                "buy_qty": 10,
                "buy_time": datetime(2026, 8, 15, 9, 0),
                "sell_time": None,
                "scale_in_locked": False,
            },
        )(),
        type(
            "Record",
            (),
            {
                "id": 995,
                "rec_date": datetime(2026, 8, 15).date(),
                "stock_code": "123456",
                "stock_name": "PENDING",
                "status": "BUY_ORDERED",
                "strategy": "SCALPING",
                "buy_price": 10_050.0,
                "buy_qty": 2,
                "buy_time": datetime(2026, 8, 15, 9, 1),
                "sell_time": None,
                "scale_in_locked": False,
            },
        )(),
    ]
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB(records, [])
    sniper_sync.ACTIVE_TARGETS = [
        {
            "id": item.id,
            "code": "123456",
            "status": item.status,
            "buy_qty": item.buy_qty,
        }
        for item in records
    ]
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "123456", "qty": 12, "buy_price": 10_008}],
            {"KRX", "NXT"},
        ),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: ([], {"request_succeeded": True}),
    )

    sniper_sync.periodic_account_sync()

    assert records[0].buy_qty == 10
    assert records[1].buy_qty == 2
    assert records[0].scale_in_locked is True
    assert all(
        target["broker_symbol_allocation_conflict"] is True
        for target in sniper_sync.ACTIVE_TARGETS
    )


def test_periodic_account_sync_does_not_overwrite_concurrent_sell_receipt(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "stock_code": "123456",
            "stock_name": "TEST",
            "status": "HOLDING",
            "buy_price": 100000.0,
            "buy_qty": 1,
            "sell_price": None,
            "sell_time": None,
            "profit_rate": None,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.KIWOOM_TOKEN = "token"
    db = _SyncDB([record], [])
    sniper_sync.DB = db
    sniper_sync.ACTIVE_TARGETS = [{"code": "123456", "status": "HOLDING"}]
    sniper_sync.HIGHEST_PRICES = {"123456": 101000}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [],
    )

    refresh_calls = []

    def complete_during_refresh(current, *, with_for_update=False):
        refresh_calls.append(with_for_update)
        current.status = "COMPLETED"
        current.sell_price = 101000
        current.sell_time = datetime(2026, 7, 28, 19, 38, 49)
        current.profit_rate = 0.76

    db._session.refresh = complete_during_refresh
    emitted = []
    monkeypatch.setattr(
        sniper_sync,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    sniper_sync.periodic_account_sync()

    assert refresh_calls == [True]
    assert record.status == "COMPLETED"
    assert record.sell_price == 101000
    assert record.sell_time == datetime(2026, 7, 28, 19, 38, 49)
    assert record.profit_rate == 0.76
    assert emitted == []


def test_periodic_account_sync_quarantines_prebaseline_scalping_ghost(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "id": 1,
            "rec_date": datetime(2026, 3, 17).date(),
            "stock_code": "412350",
            "stock_name": "레이저쎌",
            "status": "HOLDING",
            "strategy": "SCALPING",
            "buy_price": 10010.0,
            "buy_qty": 1,
            "buy_time": datetime(2026, 3, 17, 10, 0),
            "sell_price": None,
            "sell_time": None,
            "profit_rate": None,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [{"id": 1, "code": "412350", "status": "HOLDING"}]
    sniper_sync.HIGHEST_PRICES = {"412350": 10100}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([], {"KRX", "NXT"}),
    )
    emitted = []
    monkeypatch.setattr(
        sniper_sync,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    removals = []
    monkeypatch.setattr(
        sniper_sync,
        "_remove_manual_control_exclusion_for_completed_holding",
        lambda code, *, reason: removals.append((code, reason)),
    )

    sniper_sync.periodic_account_sync()

    assert record.status == "EXPIRED"
    assert sniper_sync.ACTIVE_TARGETS[0]["status"] == "EXPIRED"
    assert (
        sniper_sync.ACTIVE_TARGETS[0]["prebaseline_scalping_ghost_quarantined"] is True
    )
    assert "412350" not in sniper_sync.HIGHEST_PRICES
    assert emitted == []
    assert removals == [
        ("412350", "periodic_sync_prebaseline_scalping_ghost_quarantined")
    ]


def test_prebaseline_scalping_record_is_not_quarantined_when_broker_holds_it():
    record = type(
        "Record",
        (),
        {
            "id": 1,
            "rec_date": datetime(2026, 3, 17).date(),
            "stock_code": "412350",
            "stock_name": "레이저쎌",
            "status": "HOLDING",
            "strategy": "SCALPING",
        },
    )()

    assert (
        sniper_sync._quarantine_prebaseline_scalping_ghost(
            record,
            real_codes={"412350": {"qty": 1}},
            broker_absence_verified=True,
            source="test",
        )
        is False
    )
    assert record.status == "HOLDING"


def test_prebaseline_rec_date_with_recent_buy_time_is_not_quarantined():
    record = type(
        "Record",
        (),
        {
            "id": 1,
            "rec_date": datetime(2026, 3, 17).date(),
            "stock_code": "412350",
            "stock_name": "레이저쎌",
            "status": "HOLDING",
            "strategy": "SCALPING",
            "buy_time": datetime(2026, 7, 20, 10, 0),
        },
    )()

    assert (
        sniper_sync._quarantine_prebaseline_scalping_ghost(
            record,
            real_codes={},
            broker_absence_verified=True,
            source="test",
        )
        is False
    )
    assert record.status == "HOLDING"


def test_prebaseline_scalping_record_is_not_quarantined_without_exchange_proof():
    record = type(
        "Record",
        (),
        {
            "id": 1,
            "rec_date": datetime(2026, 3, 17).date(),
            "stock_code": "412350",
            "stock_name": "레이저쎌",
            "status": "HOLDING",
            "strategy": "SCALPING",
        },
    )()

    assert (
        sniper_sync._quarantine_prebaseline_scalping_ghost(
            record,
            real_codes={},
            broker_absence_verified=False,
            source="test",
        )
        is False
    )
    assert record.status == "HOLDING"


def test_prebaseline_scalping_buy_order_is_not_quarantined_as_missing_holding():
    record = type(
        "Record",
        (),
        {
            "id": 1,
            "rec_date": datetime(2026, 3, 17).date(),
            "stock_code": "412350",
            "stock_name": "레이저쎌",
            "status": "BUY_ORDERED",
            "strategy": "SCALPING",
        },
    )()

    assert (
        sniper_sync._quarantine_prebaseline_scalping_ghost(
            record,
            real_codes={},
            broker_absence_verified=True,
            source="test",
        )
        is False
    )
    assert record.status == "BUY_ORDERED"


def test_periodic_account_sync_recovers_unique_exact_sell_execution(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "id": 22758,
            "stock_code": "096770",
            "stock_name": "SK이노베이션",
            "status": "SELL_ORDERED",
            "buy_price": 132100.0,
            "buy_qty": 1,
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": None,
            "scale_in_locked": False,
        },
    )()
    target = {
        "id": 22758,
        "code": "096770",
        "status": "SELL_ORDERED",
        "sell_odno": "0015635",
        "sell_target_price": 132000,
    }
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [target]
    sniper_sync.HIGHEST_PRICES = {"096770": 135000}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [
            {
                "trade_date": datetime.now().strftime("%Y%m%d"),
                "code": "096770",
                "side": "매도",
                "qty": 1,
                "unit_price": 132250,
                "seq": "1",
            }
        ],
    )
    monkeypatch.setattr(
        sniper_sync,
        "remove_manual_control_exclusion_code",
        lambda code, **kwargs: type(
            "Removal",
            (),
            {
                "removed": False,
                "code": code,
                "source": "manual_control_excluded_codes.txt",
                "reason": "not_present",
            },
        )(),
    )
    emitted = []
    monkeypatch.setattr(
        sniper_sync,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    sniper_sync.periodic_account_sync()

    assert record.status == "COMPLETED"
    assert record.sell_price == 132250
    assert record.profit_rate == calculate_net_profit_rate(132100, 132250)
    assert target["sell_completion_reconciliation_state"] == (
        "broker_execution_snapshot_recovered"
    )
    assert target["sell_price"] == 132250
    assert emitted[0][0][3] == "sell_completed"
    exact_fields = emitted[0][1]["fields"]
    assert exact_fields["execution_match_count"] == 1
    assert exact_fields["actual_order_submitted"] is True
    assert exact_fields["broker_order_forbidden"] is False
    assert exact_fields["sell_completion_receipt_source"] == (
        "kt00008_unique_execution_reconciliation"
    )
    assert exact_fields["sell_time_precision"] == "date_only"
    assert exact_fields["sell_time_forbidden_for_intraday_horizon"] is True
    assert exact_fields["realized_pnl_krw"] == calculate_net_realized_pnl(
        132100, 132250, 1
    )
    assert "EV" not in exact_fields["forbidden_uses"]


def test_periodic_account_sync_preserves_concurrent_fast_fill_completion(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "id": 35391,
            "stock_code": "059090",
            "stock_name": "미코",
            "status": "HOLDING",
            "buy_price": 18660.0,
            "buy_qty": 1,
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": None,
            "scale_in_locked": False,
        },
    )()
    target = {
        "id": 35391,
        "code": "059090",
        "status": "HOLDING",
        "buy_qty": 1,
    }
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [target]
    sniper_sync.HIGHEST_PRICES = {"059090": 19000}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        sniper_sync,
        "_committed_trade_lifecycle_snapshot",
        lambda record_id: {
            "id": record_id,
            "status": "COMPLETED",
            "sell_price": 18780,
            "sell_time": datetime.now(),
            "profit_rate": calculate_net_profit_rate(18660, 18780),
        },
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [],
    )
    monkeypatch.setattr(
        sniper_sync,
        "remove_manual_control_exclusion_code",
        lambda code, **kwargs: type(
            "Removal",
            (),
            {
                "removed": False,
                "code": code,
                "source": "manual_control_excluded_codes.txt",
                "reason": "not_present",
            },
        )(),
    )
    emitted = []
    monkeypatch.setattr(
        sniper_sync,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    sniper_sync.periodic_account_sync()

    # The outer ORM object is the stale pre-REST snapshot and must not be
    # mutated.  Runtime custody follows the separately committed terminal row.
    assert record.status == "HOLDING"
    assert record.sell_price == 0
    assert record.profit_rate is None
    assert target["sell_completion_reconciliation_state"] == (
        "newer_committed_receipt_preserved"
    )
    assert target["status"] == "COMPLETED"
    assert target["sell_price"] == 18780
    assert target["profit_rate"] == calculate_net_profit_rate(18660, 18780)
    assert sniper_sync.ACTIVE_TARGETS == []
    assert emitted == []


def test_periodic_account_sync_does_not_borrow_kt00008_sell_for_holding(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "id": 35392,
            "stock_code": "059090",
            "stock_name": "미코",
            "status": "HOLDING",
            "buy_price": 19000.0,
            "buy_qty": 1,
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": None,
            "scale_in_locked": False,
        },
    )()
    target = {"id": 35392, "code": "059090", "status": "HOLDING", "buy_qty": 1}
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [target]
    sniper_sync.HIGHEST_PRICES = {"059090": 19100}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        sniper_sync,
        "_committed_trade_lifecycle_snapshot",
        lambda record_id: {"id": record_id, "status": "HOLDING"},
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [
            {
                "trade_date": datetime.now().strftime("%Y%m%d"),
                "code": "059090",
                "side": "매도",
                "qty": 1,
                "unit_price": 18780,
                "seq": "prior-cycle",
            }
        ],
    )
    monkeypatch.setattr(
        sniper_sync,
        "remove_manual_control_exclusion_code",
        lambda code, **kwargs: type(
            "Removal",
            (),
            {
                "removed": False,
                "code": code,
                "source": "manual_control_excluded_codes.txt",
                "reason": "not_present",
            },
        )(),
    )
    emitted = []
    monkeypatch.setattr(
        sniper_sync,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    sniper_sync.periodic_account_sync()

    assert record.status == "COMPLETED"
    assert record.sell_price is None
    assert record.profit_rate is None
    assert emitted[0][0][3] == "sell_completion_reconciliation_gap"
    assert emitted[0][1]["fields"]["execution_match_reason"] == (
        "prior_status_not_sell_ordered"
    )
    assert emitted[0][1]["fields"]["execution_match_count"] == 0


def test_execution_broker_snapshot_refresh_is_read_only(monkeypatch):
    published = []
    sentinel_db = object()
    sentinel_targets = [{"code": "005930", "status": "HOLDING", "buy_qty": 1}]
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = sentinel_db
    sniper_sync.ACTIVE_TARGETS = sentinel_targets

    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "005930", "qty": 1, "buy_price": 70_000}],
            {"KRX", "NXT"},
        ),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [{"code": "005930", "side": "SELL", "remaining_qty": 1}],
            {"request_succeeded": True},
        ),
    )
    monkeypatch.setattr(
        sniper_sync,
        "publish_broker_account_snapshot",
        lambda **kwargs: published.append(kwargs),
    )

    assert sniper_sync.refresh_broker_account_snapshot_read_only() is True
    assert sniper_sync.DB is sentinel_db
    assert sniper_sync.ACTIVE_TARGETS == sentinel_targets
    assert len(published) == 1
    assert published[0]["inventory"][0]["qty"] == 1
    assert published[0]["open_orders"][0]["remaining_qty"] == 1
    assert published[0]["open_orders_request_succeeded"] is True


def test_periodic_account_sync_attaches_fresh_broker_reconciliation(monkeypatch):
    record = type(
        "Record",
        (),
        {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "status": "HOLDING",
            "buy_price": 70_000.0,
            "buy_qty": 3,
            "scale_in_locked": False,
        },
    )()
    target = {
        "code": "005930",
        "status": "HOLDING",
        "buy_price": 70_000,
        "buy_qty": 3,
        "entry_execution_broker_route": "SOR",
    }
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [target]
    sniper_sync.HIGHEST_PRICES = {}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "005930", "qty": 3, "buy_price": 70_000}],
            {"KRX", "NXT"},
        ),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_unfilled_order_snapshot_ka10075_with_meta",
        lambda *args, **kwargs: (
            [
                {"code": "005930", "side": "BUY", "remaining_qty": 2},
                {"code": "005930", "side": "SELL", "remaining_qty": 1},
            ],
            {"request_succeeded": True},
        ),
    )
    monkeypatch.setattr(
        sniper_sync,
        "_recover_missing_broker_holdings",
        lambda session, real_codes: 0,
    )

    sniper_sync.periodic_account_sync()

    assert target["broker_holding_qty"] == 3
    assert target["open_buy_qty"] == 2
    assert target["open_sell_qty"] == 1
    assert target["entry_execution_broker_route"] == "SOR"
    assert "broker_route" not in target
    assert target["broker_reconciliation_source"] == "kt00005_plus_ka10075"
    assert target["broker_snapshot_at"] > 0
    assert "broker_snapshot_age_sec" not in target


def test_periodic_account_sync_does_not_remove_manual_control_exclusion_on_db_error(
    monkeypatch,
):
    record = type(
        "Record",
        (),
        {
            "stock_code": "123456",
            "stock_name": "TEST",
            "status": "SELL_ORDERED",
            "buy_price": 100000.0,
            "buy_qty": 1,
            "sell_price": 0,
            "sell_time": None,
            "profit_rate": 0.0,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _FailingSyncDB([record], [])
    sniper_sync.ACTIVE_TARGETS = [
        {"code": "123456", "status": "SELL_ORDERED", "sell_target_price": 100100}
    ]
    sniper_sync.HIGHEST_PRICES = {"123456": 100500}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: ([], {"KRX", "NXT"}),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [],
    )
    removals = []
    emitted = []
    monkeypatch.setattr(
        sniper_sync,
        "remove_manual_control_exclusion_code",
        lambda code, *, reason: removals.append({"code": code, "reason": reason}),
    )
    monkeypatch.setattr(
        sniper_sync,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    sniper_sync.periodic_account_sync()

    assert removals == []
    assert emitted == []
    assert len(sniper_sync.ACTIVE_TARGETS) == 1


def test_periodic_account_sync_preserves_original_buy_time_for_recovered_fill(
    monkeypatch,
):
    original_buy_time = datetime(2026, 7, 23, 12, 12, 28)
    record = type(
        "Record",
        (),
        {
            "stock_code": "066570",
            "stock_name": "LG전자",
            "status": "BUY_ORDERED",
            "buy_price": 182_350.0,
            "buy_qty": 1,
            "buy_time": original_buy_time,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([], [record])
    sniper_sync.ACTIVE_TARGETS = [
        {
            "code": "066570",
            "status": "BUY_ORDERED",
            "buy_time": original_buy_time,
        }
    ]
    sniper_sync.HIGHEST_PRICES = {}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "066570", "qty": 1, "buy_price": 182_350}],
            {"KRX", "NXT"},
        ),
    )
    monkeypatch.setattr(
        sniper_sync,
        "_recover_missing_broker_holdings",
        lambda session, real_codes: 0,
    )

    sniper_sync.periodic_account_sync()

    assert record.status == "HOLDING"
    assert record.buy_time == original_buy_time
    assert sniper_sync.ACTIVE_TARGETS[0]["status"] == "HOLDING"
    assert sniper_sync.ACTIVE_TARGETS[0]["holding_started_at"] == original_buy_time


def test_periodic_account_sync_recovers_broker_only_holding_from_watching_record(
    monkeypatch,
):
    watch_record = type(
        "Record",
        (),
        {
            "id": 2205,
            "rec_date": datetime.now().date(),
            "stock_code": "189300",
            "stock_name": "인텔리안테크",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCALP_BASE",
            "prob": 0.8,
            "buy_qty": 0,
            "buy_price": 0.0,
            "buy_time": None,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([], [], [watch_record])
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.HIGHEST_PRICES = {}
    sniper_sync.STATE_LOCK = _DummyLock()
    sniper_sync.EVENT_BUS = _Bus()
    sniper_sync.KIWOOM_TOKEN = "token"
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [],
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "189300", "name": "인텔리안테크", "qty": 7, "buy_price": 133610}],
            {"KRX", "NXT"},
        ),
    )

    sniper_sync.periodic_account_sync()

    assert watch_record.status == "HOLDING"
    assert watch_record.buy_qty == 7
    assert watch_record.buy_price == 133610
    assert sniper_sync.ACTIVE_TARGETS
    assert sniper_sync.ACTIVE_TARGETS[0]["code"] == "189300"
    assert sniper_sync.ACTIVE_TARGETS[0]["status"] == "HOLDING"
    assert sniper_sync.ACTIVE_TARGETS[0]["buy_qty"] == 7
    telegram_events = [
        payload
        for topic, payload in sniper_sync.EVENT_BUS.events
        if topic == "TELEGRAM_BROADCAST"
    ]
    assert any(
        "매수 체결 확인 (브로커 복구)" in event["message"] for event in telegram_events
    )
    assert any("잔고조회 확인" in event["message"] for event in telegram_events)


def test_periodic_account_sync_does_not_recover_operator_excluded_inventory(
    monkeypatch,
):
    watch_record = type(
        "Record",
        (),
        {
            "id": 2206,
            "rec_date": datetime.now().date(),
            "stock_code": "042660",
            "stock_name": "한화오션",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCALP_BASE",
            "prob": 0.8,
            "buy_qty": 0,
            "buy_price": 0.0,
            "buy_time": None,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.DB = _SyncDB([], [], [watch_record])
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.HIGHEST_PRICES = {}
    sniper_sync.STATE_LOCK = _DummyLock()
    sniper_sync.EVENT_BUS = _Bus()
    sniper_sync.KIWOOM_TOKEN = "token"
    monkeypatch.setattr(
        sniper_sync,
        "manual_control_operator_exclusion_source",
        lambda code: "manual_control_excluded_codes.txt" if code == "042660" else None,
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [],
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "042660", "name": "한화오션", "qty": 1, "buy_price": 91_400}],
            {"KRX", "NXT"},
        ),
    )

    sniper_sync.periodic_account_sync()

    assert watch_record.status == "WATCHING"
    assert watch_record.buy_qty == 0
    assert sniper_sync.ACTIVE_TARGETS == []
    assert sniper_sync.HIGHEST_PRICES == {}
    assert not any(
        topic == "TELEGRAM_BROADCAST"
        and "매수 체결 확인 (브로커 복구)" in payload["message"]
        for topic, payload in sniper_sync.EVENT_BUS.events
    )


def test_periodic_account_sync_marks_legacy_broker_recovered_holding(monkeypatch):
    legacy_watch = type(
        "Record",
        (),
        {
            "id": 159,
            "rec_date": datetime(2026, 4, 10).date(),
            "stock_code": "016360",
            "stock_name": "삼성증권",
            "status": "EXPIRED",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCALP_BASE",
            "buy_qty": 0,
            "buy_price": 0.0,
            "buy_time": None,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.DB = _SyncDB([], [], [legacy_watch])
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.HIGHEST_PRICES = {}
    sniper_sync.STATE_LOCK = _DummyLock()
    sniper_sync.EVENT_BUS = _Bus()
    sniper_sync.KIWOOM_TOKEN = "token"
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [
            {
                "trade_date": "20260414",
                "code": "016360",
                "name": "삼성증권",
                "side": "매수",
                "qty": 1,
                "unit_price": 111400,
            }
        ],
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "016360", "name": "삼성증권", "qty": 1, "buy_price": 111400}],
            {"KRX", "NXT"},
        ),
    )

    sniper_sync.periodic_account_sync()

    assert legacy_watch.status == "HOLDING"
    assert sniper_sync.ACTIVE_TARGETS[0]["broker_recovered"] is True
    assert sniper_sync.ACTIVE_TARGETS[0]["broker_recovered_legacy"] is True
    assert sniper_sync.ACTIVE_TARGETS[0]["broker_recovered_execution_verified"] is True
    assert not any(
        topic == "TELEGRAM_BROADCAST"
        and "매수 체결 확인 (브로커 복구)" in payload["message"]
        for topic, payload in sniper_sync.EVENT_BUS.events
    )


def test_periodic_account_sync_recovers_order_ref_when_kt00008_empty(monkeypatch):
    legacy_watch = type(
        "Record",
        (),
        {
            "id": 160,
            "rec_date": datetime.now().date(),
            "stock_code": "189300",
            "stock_name": "인텔리안테크",
            "status": "WATCHING",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCALP_BASE",
            "buy_qty": 0,
            "buy_price": 0.0,
            "buy_time": None,
            "scale_in_locked": False,
        },
    )()

    sniper_sync.DB = _SyncDB([], [], [legacy_watch])
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.HIGHEST_PRICES = {}
    sniper_sync.STATE_LOCK = _DummyLock()
    sniper_sync.EVENT_BUS = _Bus()
    sniper_sync.KIWOOM_TOKEN = (
        "very_long_real_token_for_test_enable_2nd_pass_0123456789"
    )
    sniper_sync.CONF = {
        "ENABLE_ORDER_REF_2ND_PASS": True,
        "BROKER_ORDER_REF_QRY_TP": "0",
        "BROKER_ORDER_REF_STK_BOND_TP": "0",
    }
    monkeypatch.setattr(sniper_sync, "_recover_order_refs_from_logs", lambda code: {})
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda token: [],
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_order_reference_snapshot_2nd_pass",
        lambda token, qry_tp, stk_bond_tp: [
            {
                "code": "189300",
                "side": "매수",
                "qty": 7,
                "unit_price": 133610,
                "ord_no": "0412345",
                "orig_ord_no": "0000000",
            }
        ],
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "get_account_balance_kt00005",
        lambda token: (
            [{"code": "189300", "name": "인텔리안테크", "qty": 7, "buy_price": 133610}],
            {"KRX", "NXT"},
        ),
    )

    sniper_sync.periodic_account_sync()

    assert legacy_watch.status == "HOLDING"
    assert sniper_sync.ACTIVE_TARGETS[0]["broker_recovered_execution_verified"] is True
    assert sniper_sync.ACTIVE_TARGETS[0]["odno"] == "0412345"
    telegram_events = [
        payload
        for topic, payload in sniper_sync.EVENT_BUS.events
        if topic == "TELEGRAM_BROADCAST"
    ]
    assert any("주문번호: `0412345`" in event["message"] for event in telegram_events)
    assert any("체결/주문조회 확인" in event["message"] for event in telegram_events)


def test_sync_balance_with_db_requests_restart_on_auth_failure(tmp_path, monkeypatch):
    restart_flag = tmp_path / "restart.flag"
    invalidations = []
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB([], [])
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.HIGHEST_PRICES = {}
    sniper_sync.STATE_LOCK = _DummyLock()
    sniper_sync._LAST_AUTH_RESTART_TS = 0.0

    monkeypatch.setattr(sniper_sync, "RESTART_FLAG_PATH", restart_flag)
    monkeypatch.setattr(
        sniper_sync.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([], set()),
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_orders,
        "get_last_inventory_errors",
        lambda: [{"return_code": "8005", "return_msg": "Token이 유효하지 않습니다"}],
    )
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "invalidate_kiwoom_token_cache",
        lambda reason="": invalidations.append(reason) or True,
    )
    monkeypatch.setattr(sniper_sync.time, "sleep", lambda _: None)

    sniper_sync.sync_balance_with_db()

    assert restart_flag.exists() is True
    assert invalidations == ["auth_restart:인증 실패(8005)"]


def test_startup_sync_quarantines_prebaseline_scalping_ghosts(monkeypatch):
    records = [
        type(
            "Record",
            (),
            {
                "id": 1,
                "rec_date": datetime(2026, 3, 17).date(),
                "stock_code": "412350",
                "stock_name": "레이저쎌",
                "status": "HOLDING",
                "strategy": "SCALPING",
                "buy_price": 10010.0,
                "buy_qty": 1,
                "buy_time": datetime(2026, 3, 17, 10, 0),
                "sell_time": None,
            },
        )(),
        type(
            "Record",
            (),
            {
                "id": 7,
                "rec_date": datetime(2026, 3, 17).date(),
                "stock_code": "393890",
                "stock_name": "더블유씨피",
                "status": "SELL_ORDERED",
                "strategy": "SCALPING",
                "buy_price": 0.0,
                "buy_qty": 66,
                "buy_time": None,
                "sell_time": None,
            },
        )(),
    ]
    sniper_sync.KIWOOM_TOKEN = "token"
    sniper_sync.DB = _SyncDB(records, [])
    sniper_sync.ACTIVE_TARGETS = [
        {"id": record.id, "code": record.stock_code, "status": record.status}
        for record in records
    ]
    sniper_sync.HIGHEST_PRICES = {"412350": 10100, "393890": 10000}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(
        sniper_sync.kiwoom_orders,
        "get_my_inventory",
        lambda token: ([], {"KRX", "NXT"}),
    )
    removals = []
    monkeypatch.setattr(
        sniper_sync,
        "_remove_manual_control_exclusion_for_completed_holding",
        lambda code, *, reason: removals.append((code, reason)),
    )

    sniper_sync.sync_balance_with_db()

    assert [record.status for record in records] == ["EXPIRED", "EXPIRED"]
    assert [target["status"] for target in sniper_sync.ACTIVE_TARGETS] == [
        "EXPIRED",
        "EXPIRED",
    ]
    assert sniper_sync.HIGHEST_PRICES == {}
    assert removals == [
        ("412350", "startup_sync_prebaseline_scalping_ghost_quarantined"),
        ("393890", "startup_sync_prebaseline_scalping_ghost_quarantined"),
    ]


def test_auth_restart_cooldown_still_invalidates_token_cache(tmp_path, monkeypatch):
    restart_flag = tmp_path / "restart.flag"
    invalidations = []
    sniper_sync._LAST_AUTH_RESTART_TS = 1_000.0

    monkeypatch.setattr(sniper_sync, "RESTART_FLAG_PATH", restart_flag)
    monkeypatch.setattr(sniper_sync.time, "time", lambda: 1_030.0)
    monkeypatch.setattr(
        sniper_sync.kiwoom_utils,
        "invalidate_kiwoom_token_cache",
        lambda reason="": invalidations.append(reason) or True,
    )

    assert sniper_sync._request_auth_restart("인증 실패(8005)") is False

    assert not restart_flag.exists()
    assert invalidations == ["auth_restart:인증 실패(8005)"]


def test_ensure_runtime_target_recovers_order_refs_from_logs(monkeypatch):
    monkeypatch.setattr(sniper_sync, "_iter_recovery_log_paths", lambda: ["dummy.log"])
    monkeypatch.setattr(
        sniper_sync,
        "_tail_text",
        lambda path: "\n".join(
            [
                "[2026-04-15 09:52:15] 🔔 [WS 실제체결] 189300 BUY 7주 @ 133610원 (주문번호: 0412345)",
                "[2026-04-15 09:52:16] 📢 INFO in sniper_execution_receipts: [ENTRY_TP_REFRESH] 인텔리안테크(189300) qty=7 tp_price=135600 ord_no=0412350",
            ]
        ),
    )
    sniper_sync.DB = _SyncDB([], [], [])
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.EVENT_BUS = _Bus()

    record = type(
        "Record",
        (),
        {
            "id": 2241,
            "stock_code": "189300",
            "stock_name": "인텔리안테크",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCALP_BASE",
            "buy_qty": 7,
            "buy_price": 133610.0,
            "buy_time": datetime(2026, 4, 15, 9, 52, 15),
            "scale_in_locked": False,
        },
    )()

    target = sniper_sync._ensure_runtime_target(record)

    assert target["odno"] == "0412345"
    assert target["preset_tp_ord_no"] == "0412350"


def test_ensure_runtime_target_recovers_order_refs_from_pipeline_logs(monkeypatch):
    monkeypatch.setattr(
        sniper_sync, "_iter_recovery_log_paths", lambda: ["pipeline.log"]
    )
    monkeypatch.setattr(
        sniper_sync,
        "_tail_text",
        lambda path: "\n".join(
            [
                "[2026-04-15 09:52:04] [ENTRY_PIPELINE] 인텔리안테크(189300) stage=order_leg_sent id=2205 tag=fallback_main ord_no=0036511",
                "[2026-04-15 09:52:04] [HOLDING_PIPELINE] 인텔리안테크(189300) stage=preset_exit_setup id=2205 preset_tp_price=135800 qty=1 ord_no=0036512",
            ]
        ),
    )
    sniper_sync.DB = _SyncDB([], [], [])
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.EVENT_BUS = _Bus()

    record = type(
        "Record",
        (),
        {
            "id": 2241,
            "stock_code": "189300",
            "stock_name": "인텔리안테크",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCALP_BASE",
            "buy_qty": 7,
            "buy_price": 133610.0,
            "buy_time": datetime(2026, 4, 15, 9, 52, 15),
            "scale_in_locked": False,
        },
    )()

    target = sniper_sync._ensure_runtime_target(record)

    assert target["odno"] == "0036511"
    assert target["preset_tp_ord_no"] == "0036512"


def test_ensure_runtime_target_ignores_trailing_unified_disabled_stage(monkeypatch):
    monkeypatch.setattr(
        sniper_sync, "_iter_recovery_log_paths", lambda: ["pipeline.log"]
    )
    monkeypatch.setattr(
        sniper_sync,
        "_tail_text",
        lambda path: "\n".join(
            [
                "[2026-07-09 10:31:04] [ENTRY_PIPELINE] 인텔리안테크(189300) stage=order_leg_sent id=2205 tag=fallback_main ord_no=0036511",
                "[2026-07-09 10:31:05] [HOLDING_PIPELINE] 인텔리안테크(189300) stage=preset_exit_setup_disabled_trailing_unified id=2205 preset_tp_price=0 qty=1 ord_no=0036512",
            ]
        ),
    )
    sniper_sync.DB = _SyncDB([], [], [])
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.EVENT_BUS = _Bus()

    record = type(
        "Record",
        (),
        {
            "id": 2241,
            "stock_code": "189300",
            "stock_name": "인텔리안테크",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "position_tag": "SCALP_BASE",
            "buy_qty": 7,
            "buy_price": 133610.0,
            "buy_time": datetime(2026, 7, 9, 10, 31, 5),
            "scale_in_locked": False,
        },
    )()

    target = sniper_sync._ensure_runtime_target(record)

    assert target["odno"] == "0036511"
    assert "preset_tp_ord_no" not in target


def test_s15_candidate_does_not_store_expiry_in_profit_rate():
    session = _S15Session()
    s15.DB = _S15DB(session)

    s15._save_armed_candidate_to_db("123456", "TEST", "COND", 100.0, 160.0)

    assert session.added is not None
    assert session.added.profit_rate == 0.0
    assert session.added.hard_stop_price == 160.0
    assert session.added.nxt == 100.0


def test_holding_state_uses_net_profit_rate_for_sell_decision(monkeypatch):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        STOP_LOSS_BULL=0.001,
        STOP_LOSS_BEAR=0.001,
        HOLDING_DAYS=99,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=False,
    )
    state_handlers.KIWOOM_TOKEN = "token"
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}

    record = type("Record", (), {"buy_qty": 1, "status": "HOLDING"})()
    state_handlers.DB = _StateDB(record)

    sell_calls = []
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda **kwargs: (
            sell_calls.append(kwargs)
            or {"return_code": "0", "ord_no": "0000001"}
        ),
    )
    monkeypatch.setattr(
        state_handlers,
        "_sell_side_open_time_block_fields",
        lambda **kwargs: {"sell_time_block_applied": False},
    )
    monkeypatch.setattr(
        state_handlers,
        "_manual_control_exclusion_blocked",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        state_handlers,
        "_maybe_auto_exclude_open_loss_holding",
        lambda *args, **kwargs: False,
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 100000,
        "buy_qty": 1,
    }
    observed_at = datetime(2026, 8, 14, 10, 0, 0)

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 100100},
        admin_id=1,
        market_regime="BULL",
        now_ts=observed_at.replace(tzinfo=timezone(timedelta(hours=9))).timestamp(),
        now_dt=observed_at,
        radar=None,
        ai_engine=None,
    )

    assert sell_calls
    assert stock["status"] == "SELL_ORDERED"
    assert "-0.13%" in stock["pending_sell_msg"]


@pytest.mark.parametrize("http_success", [True, False], ids=["success", "error"])
def test_ws_sell_receipt_before_http_response_never_rolls_back_terminal_state(
    monkeypatch,
    http_success,
):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        STOP_LOSS_BULL=0.001,
        STOP_LOSS_BEAR=0.001,
        HOLDING_DAYS=99,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=False,
    )
    state_handlers.KIWOOM_TOKEN = "token"
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    fixed_at = datetime(2026, 8, 14, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    fixed_epoch = fixed_at.timestamp()
    monkeypatch.setattr(state_handlers.time, "time", lambda: fixed_epoch)

    record = type(
        "Record",
        (),
        {"buy_qty": 1, "buy_price": 100000.0, "status": "HOLDING"},
    )()
    state_handlers.DB = _StateDB(record)
    api_entered = threading.Event()
    release_api = threading.Event()

    def blocking_sell(**_kwargs):
        api_entered.set()
        assert release_api.wait(timeout=5)
        if http_success:
            return {
                "return_code": "0",
                "ord_no": "0000456",
                "broker_route": "SOR",
            }
        return {"return_code": "1", "return_msg": "late transport error"}

    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        blocking_sell,
    )
    monkeypatch.setattr(
        state_handlers,
        "_sell_side_open_time_block_fields",
        lambda **_kwargs: {"sell_time_block_applied": False},
    )
    monkeypatch.setattr(
        state_handlers,
        "_manual_control_exclusion_blocked",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        state_handlers,
        "_maybe_auto_exclude_open_loss_holding",
        lambda *_args, **_kwargs: False,
    )
    logged = []
    monkeypatch.setattr(
        state_handlers,
        "_log_holding_pipeline",
        lambda _stock, _code, stage, **fields: logged.append((stage, fields)),
    )
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *_args, **_kwargs: {
            "structured_append_succeeded": True,
            "structured_append_status": "raw_appended",
        },
    )

    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 100000,
        "buy_qty": 1,
    }
    worker = threading.Thread(
        target=state_handlers.handle_holding_state,
        kwargs={
            "stock": stock,
            "code": "123456",
            "ws_data": {"curr": 100100},
            "admin_id": 1,
            "market_regime": "BULL",
            "now_ts": fixed_epoch,
            "now_dt": fixed_at.replace(tzinfo=None),
            "radar": None,
            "ai_engine": None,
        },
    )
    worker.start()
    assert api_entered.wait(timeout=5)
    received_at = fixed_at + timedelta(milliseconds=200)
    stock.update(
        {
            "main_lifecycle_broker_raw_envelope_schema": (
                "kiwoom_websocket_order_execution_00_values_v1"
            ),
            "main_lifecycle_broker_raw_source_type": "00",
            "broker_execution_received_at": received_at.isoformat(),
            "broker_execution_receive_time_source": (
                "websocket_packet_ingress"
            ),
            "broker_execution_observed_at": fixed_at.isoformat(),
            "broker_execution_time_source": "official_fid_908",
            "broker_actual_execution_venue": "UNKNOWN",
            "broker_actual_exchange_code": "0",
            "broker_actual_exchange_name": "SOR",
            "broker_sor_flag": "Y",
            "9203": "0000456",
            "9001": "123456",
            "913": "체결",
            "900": "1",
            "902": "0",
            "903": "100100",
            "905": "-매도",
            "907": "1",
            "908": "100000",
            "909": "0000002",
            "910": "100100",
            "911": "1",
            "914": "100100",
            "915": "1",
            "2134": "0",
            "2135": "SOR",
            "2136": "Y",
        }
    )
    assert receipts._bind_pending_sell_execution_receipt(
        target_stock=stock,
        target_id=1,
        code="123456",
        order_no="0000456",
        execution_no="0000002",
    )
    stock["status"] = "COMPLETED"
    record.status = "COMPLETED"
    stock.pop("sell_odno", None)
    release_api.set()
    worker.join(timeout=5)
    assert not worker.is_alive()

    assert stock["status"] == "COMPLETED"
    assert record.status == "COMPLETED"
    assert "sell_odno" not in stock
    assert stock["_sell_submit_receipt_proof"]["custody_emitted"] is True
    assert stock["sell_pending_submit_successor_persist_required"] is True
    assert receipts._sell_pending_submit_path(stock["id"]).exists()
    assert not any(stage == "sell_order_failed" for stage, _fields in logged)
    if http_success:
        corroborations = [
            fields for stage, fields in logged if stage == "sell_order_sent"
        ]
        assert len(corroborations) == 1
        assert corroborations[0]["sell_submit_response_corroboration_only"] is True
        assert corroborations[0]["ord_no"] == "0000456"
    else:
        assert any(
            stage == "sell_submit_response_conflicted_with_receipt"
            for stage, _fields in logged
        )


def test_available_quantity_submit_conflict_keeps_exact_receipt_bind_context(
    monkeypatch,
):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        STOP_LOSS_BULL=0.001,
        STOP_LOSS_BEAR=0.001,
        HOLDING_DAYS=99,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        SWING_LIVE_ORDER_DRY_RUN_ENABLED=False,
    )
    state_handlers.KIWOOM_TOKEN = "token"
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"123456": 100100}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    fixed_at = datetime(2026, 8, 14, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    fixed_epoch = fixed_at.timestamp()
    monkeypatch.setattr(state_handlers.time, "time", lambda: fixed_epoch)
    record = type(
        "Record",
        (),
        {"buy_qty": 1, "buy_price": 100000.0, "status": "HOLDING"},
    )()
    state_handlers.DB = _StateDB(record)
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda **_kwargs: {
            "return_code": "1",
            "return_msg": "매도가능수량 0주",
        },
    )
    monkeypatch.setattr(
        state_handlers,
        "_sell_side_open_time_block_fields",
        lambda **_kwargs: {"sell_time_block_applied": False},
    )
    monkeypatch.setattr(
        state_handlers,
        "_manual_control_exclusion_blocked",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(
        state_handlers,
        "_maybe_auto_exclude_open_loss_holding",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setattr(state_handlers, "_log_holding_pipeline", lambda *a, **k: None)
    custody_events = []
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: (
            custody_events.append((args[3], kwargs))
            or {
                "structured_append_succeeded": True,
                "structured_append_status": "raw_appended",
            }
        ),
    )
    stock = {
        "id": 1,
        "code": "123456",
        "name": "TEST",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 100000,
        "buy_qty": 1,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="123456",
        ws_data={"curr": 100100},
        admin_id=1,
        market_regime="BULL",
        now_ts=fixed_epoch,
        now_dt=fixed_at.replace(tzinfo=None),
        radar=None,
        ai_engine=None,
    )

    assert stock["status"] == "SELL_ORDERED"
    assert stock["sell_submit_pending"] is True
    generation = stock["sell_submit_generation"]
    received_at = fixed_at + timedelta(milliseconds=200)
    stock.update(
        {
            "main_lifecycle_broker_raw_envelope_schema": (
                "kiwoom_websocket_order_execution_00_values_v1"
            ),
            "main_lifecycle_broker_raw_source_type": "00",
            "broker_execution_received_at": received_at.isoformat(),
            "broker_execution_receive_time_source": "websocket_packet_ingress",
            "broker_execution_observed_at": fixed_at.isoformat(),
            "broker_execution_time_source": "official_fid_908",
            "broker_actual_execution_venue": "UNKNOWN",
            "broker_actual_execution_venue_source": (
                "official_exchange_fields_ambiguous_or_missing"
            ),
            "broker_actual_exchange_code": "0",
            "broker_actual_exchange_name": "SOR",
            "broker_sor_flag": "Y",
            "9203": "0000456",
            "9001": "123456",
            "913": "체결",
            "900": "1",
            "902": "0",
            "903": "100100",
            "905": "-매도",
            "907": "1",
            "908": "100000",
            "909": "0000002",
            "910": "100100",
            "911": "1",
            "914": "100100",
            "915": "1",
            "2134": "0",
            "2135": "SOR",
            "2136": "Y",
        }
    )

    assert receipts._bind_pending_sell_execution_receipt(
        target_stock=stock,
        target_id=1,
        code="123456",
        order_no="0000456",
        execution_no="0000002",
    )
    assert custody_events[-1][0] == "exit_execution_receipt_submission_custody"
    assert stock["sell_odno"] == "0000456"
    assert stock["sell_submit_generation"] == generation
    assert stock["sell_submit_pending"] is False
    assert stock["sell_pending_submit_successor_persist_required"] is True
    assert receipts._sell_pending_submit_path(1).exists()
    assert stock["_sell_submit_receipt_proof"]["custody_emitted"] is True


def test_holding_state_skips_scalping_loss_exit_for_legacy_broker_recovered(
    monkeypatch,
):
    state_handlers.TRADING_RULES = replace(
        CONFIG,
        SCALE_IN_REQUIRE_HISTORY_TABLE=False,
        ENABLE_SCALE_IN=False,
        SCALP_STOP=-1.5,
        SCALP_HARD_STOP=-2.5,
    )
    state_handlers.KIWOOM_TOKEN = "token"
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {"016360": 111400}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}

    record = type("Record", (), {"buy_qty": 1, "status": "HOLDING"})()
    state_handlers.DB = _StateDB(record)

    sell_calls = []
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_smart_sell_order",
        lambda **kwargs: (
            sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"}
        ),
    )

    stock = {
        "id": 159,
        "code": "016360",
        "name": "삼성증권",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": 111400,
        "buy_qty": 1,
        "buy_time": datetime(2026, 4, 15, 10, 22, 46),
        "rt_ai_prob": 0.5,
        "broker_recovered": True,
        "broker_recovered_legacy": True,
    }

    state_handlers.handle_holding_state(
        stock=stock,
        code="016360",
        ws_data={"curr": 109500},
        admin_id=1,
        market_regime="BULL",
        radar=None,
        ai_engine=None,
    )

    assert not sell_calls
    assert stock["status"] == "HOLDING"
    assert stock["last_exit_guard_reason"] == "broker_recovered_legacy"


def test_cancelled_sell_late_receipt_survives_restart(monkeypatch, tmp_path):
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    stock = {
        "id": 8801,
        "code": "123456",
        "name": "LATE",
        "status": "SELL_ORDERED",
        "buy_price": 10_000,
        "buy_qty": 10,
    }
    first = receipts._resolve_sell_execution_receipt(
        stock,
        order_no="S1",
        exec_price=10_010,
        cumulative_exec_qty=2,
        expected_position_qty=10,
        buy_price=10_000,
        order_qty=10,
        remaining_qty=8,
        cumulative_exec_amount=20_020,
        execution_no="E1",
        unit_exec_price=10_010,
        unit_exec_qty=2,
    )
    assert first["status"] == "partial"
    rotated = state_handlers._rotate_cancelled_sell_receipt_ledger(
        stock, orig_ord_no="S1", broker_qty=8
    )
    assert rotated["reconciled"] is True

    record = type(
        "Record",
        (),
        {"id": 8801, "buy_qty": 10, "scale_in_locked": True},
    )()
    fresh = {
        "id": 8801,
        "code": "123456",
        "name": "LATE",
        "status": "HOLDING",
        "buy_price": 10_000,
        "buy_qty": 10,
    }
    restored, reason = sniper_sync._restore_sell_receipt_recovery(
        target_stock=fresh,
        record=record,
        code="123456",
        broker_remaining_qty=8,
    )
    assert reason == "journal_exact_match"
    assert restored is not None
    assert fresh["status"] == "HOLDING"
    assert fresh["buy_qty"] == 8
    assert fresh["sell_partial_exit_recovery_required"] is False
    monkeypatch.setattr(receipts, "ACTIVE_TARGETS", [fresh])
    assert receipts._find_execution_target("123456", "SELL", "S1") is fresh

    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(receipts, "_get_fast_state", lambda _code: None)
    monkeypatch.setattr(
        receipts,
        "_resolve_sell_execution_context",
        lambda *_args: (record, 10_000.0, 0.0, "SCALPING", False),
    )
    monkeypatch.setattr(receipts, "_log_holding_pipeline", lambda *_a, **_kw: None)
    receipts.handle_real_execution(
        {
            "code": "123456",
            "type": "SELL",
            "order_no": "S1",
            "price": 10_020,
            "qty": 4,
            "order_qty": 10,
            "remaining_qty": 6,
            "cumulative_exec_amount": 40_060,
            "execution_no": "E2",
            "unit_exec_price": 10_020,
            "unit_exec_qty": 2,
        }
    )
    state = fresh[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY]
    assert state["carried_qty"] == 4
    assert state["remaining_qty"] == 6
    assert fresh["buy_qty"] == 6
    assert fresh["sell_reconciled_remaining_qty"] == 6


def test_committed_sell_journal_releases_reentry_without_replaying_order(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    stock = {
        "id": 8803,
        "code": "123456",
        "buy_price": 10_000,
        "buy_qty": 5,
        receipts._SELL_EXECUTION_RECEIPT_STATE_KEY: {
            "position_qty": 5,
            "aggregate_cumulative_qty": 5,
            "aggregate_cumulative_amount": 50_500,
            "final": True,
            "final_pending_db_commit": True,
            "finalization_strategy": "SCALPING",
            "finalization_receipt_snapshot": {
                "strategy": "SCALPING",
                "position_tag": "DEFAULT",
                "last_exit_rule": "scalp_trailing_take_profit",
            },
        },
    }
    assert receipts.persist_sell_receipt_recovery(stock) is True
    record = type(
        "Record",
        (),
        {
            "id": 8803,
            "status": "COMPLETED",
            "strategy": "SCALPING",
            "position_tag": "DEFAULT",
            "sell_time": datetime(2026, 8, 18, 10, 0, 0),
            "sell_price": 10_100,
            "profit_rate": 0.5,
        },
    )()
    callbacks = []
    monkeypatch.setattr(receipts, "DB", _ReceiptDB(record))
    monkeypatch.setattr(
        receipts,
        "_scalp_exit_completed_callback",
        lambda code, **kwargs: callbacks.append((code, kwargs)) or {"reconciled": True},
    )

    result = receipts.reconcile_committed_sell_receipt_recovery_files()

    assert result == {"scanned": 1, "reconciled": 1, "deferred": 0, "invalid": 0}
    assert callbacks[0][0] == "123456"
    assert callbacks[0][1]["exit_price"] == 10_100
    assert not (tmp_path / "8803.json").exists()


def test_committed_sell_recovery_rejects_symlink_directory(monkeypatch, tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", linked)

    result = receipts.reconcile_committed_sell_receipt_recovery_files()

    assert result == {"scanned": 0, "reconciled": 0, "deferred": 0, "invalid": 1}


def test_active_sell_receipt_recovery_journal_survives_weekend(monkeypatch, tmp_path):
    monkeypatch.setattr(receipts, "SELL_RECEIPT_RECOVERY_DIR", tmp_path)
    stock = {
        "id": 8802,
        "code": "123456",
        "buy_price": 10_000,
        "buy_qty": 10,
    }
    receipt = receipts._resolve_sell_execution_receipt(
        stock,
        order_no="S1",
        exec_price=10_010,
        cumulative_exec_qty=2,
        expected_position_qty=10,
        buy_price=10_000,
        order_qty=10,
        remaining_qty=8,
        cumulative_exec_amount=20_020,
        execution_no="E1",
        unit_exec_price=10_010,
        unit_exec_qty=2,
    )
    assert receipt["status"] == "partial"
    assert receipts.persist_sell_receipt_recovery(stock) is True
    path = tmp_path / "8802.json"
    assert path.exists()

    restored, reason = receipts.load_sell_receipt_recovery(
        target_id=8802,
        code="123456",
        position_qty=10,
        broker_remaining_qty=8,
        now_epoch=(
            receipts.time.time() + receipts._SELL_RECEIPT_RECOVERY_MAX_AGE_SEC + 1
        ),
    )

    assert restored is not None
    assert reason == "journal_exact_match"
    assert path.exists()


def test_sell_execution_number_changed_payload_is_blocked():
    stock = {}
    first = receipts._resolve_sell_execution_receipt(
        stock,
        order_no="S1",
        exec_price=10_010,
        cumulative_exec_qty=2,
        expected_position_qty=10,
        buy_price=10_000,
        order_qty=10,
        remaining_qty=8,
        cumulative_exec_amount=20_020,
        execution_no="E1",
        unit_exec_price=10_010,
        unit_exec_qty=2,
    )
    changed = receipts._resolve_sell_execution_receipt(
        stock,
        order_no="S1",
        exec_price=10_015,
        cumulative_exec_qty=4,
        expected_position_qty=10,
        buy_price=10_000,
        order_qty=10,
        remaining_qty=6,
        cumulative_exec_amount=40_050,
        execution_no="E1",
        unit_exec_price=10_015,
        unit_exec_qty=2,
    )
    assert first["status"] == "partial"
    assert changed["reason"] == "receipt_execution_number_reused_with_changed_payload"
    assert stock[receipts._SELL_EXECUTION_RECEIPT_STATE_KEY]["cumulative_qty"] == 2


def test_execution_number_ledger_capacity_fails_closed_before_forgetting_identity():
    executions = {
        f"E{index}": {"cumulative_qty": index + 1}
        for index in range(receipts._EXECUTION_SIGNATURES_PER_ORDER_MAX)
    }

    reason = receipts._execution_number_conflict_reason(
        {"S1": executions},
        order_key="S1",
        execution_no="E-new",
        signature={"cumulative_qty": len(executions) + 1},
    )

    assert reason == "receipt_execution_ledger_capacity_exceeded"


def test_entry_and_add_execution_number_changed_payload_is_blocked():
    entry = {
        "id": 1,
        "code": "123456",
        "status": "BUY_ORDERED",
        "entry_requested_qty": 10,
        "pending_entry_orders": [
            {"ord_no": "B1", "qty": 10, "filled_qty": 0, "status": "OPEN"}
        ],
    }
    receipts._resolve_entry_effective_fill_qty(
        target_stock=entry,
        code="123456",
        order_no="B1",
        exec_price=10_000,
        exec_qty=2,
        order_qty=10,
        remaining_qty=8,
        cumulative_exec_amount=20_000,
        execution_no="E1",
        unit_exec_price=10_000,
        unit_exec_qty=2,
    )
    changed_entry = receipts._resolve_entry_effective_fill_qty(
        target_stock=entry,
        code="123456",
        order_no="B1",
        exec_price=10_010,
        exec_qty=4,
        order_qty=10,
        remaining_qty=6,
        cumulative_exec_amount=40_020,
        execution_no="E1",
        unit_exec_price=10_010,
        unit_exec_qty=2,
    )
    add = {
        "code": "123456",
        "status": "HOLDING",
        "pending_add_order": True,
        "pending_add_ord_no": "A1",
        "pending_add_qty": 10,
        "pending_add_filled_qty": 0,
        "pending_add_filled_amount": 0,
    }
    receipts._resolve_add_effective_fill(
        target_stock=add,
        code="123456",
        order_no="A1",
        exec_price=9_900,
        exec_qty=2,
        order_qty=10,
        remaining_qty=8,
        cumulative_exec_amount=19_800,
        execution_no="E1",
        unit_exec_price=9_900,
        unit_exec_qty=2,
    )
    changed_add = receipts._resolve_add_effective_fill(
        target_stock=add,
        code="123456",
        order_no="A1",
        exec_price=9_910,
        exec_qty=4,
        order_qty=10,
        remaining_qty=6,
        cumulative_exec_amount=39_620,
        execution_no="E1",
        unit_exec_price=9_910,
        unit_exec_qty=2,
    )
    expected = "receipt_execution_number_reused_with_changed_payload"
    assert changed_entry["reason"] == expected
    assert changed_add["reason"] == expected


def test_fast_sell_per_order_ledger_handles_cancel_retry_and_conflicts():
    state = {"cum_buy_qty": 10, "cum_sell_qty": 0, "cum_sell_amount": 0}
    first = receipts._resolve_fast_sell_execution_receipt(
        state,
        order_no="S1",
        exec_price=10_010,
        cumulative_exec_qty=2,
        order_qty=10,
        remaining_qty=8,
        cumulative_exec_amount=20_020,
        execution_no="S1-E1",
        unit_exec_price=10_010,
        unit_exec_qty=2,
    )
    conflict = receipts._resolve_fast_sell_execution_receipt(
        state,
        order_no="S1",
        exec_price=10_020,
        cumulative_exec_qty=2,
        order_qty=10,
        remaining_qty=8,
        cumulative_exec_amount=20_040,
        execution_no="S1-E2",
        unit_exec_price=10_020,
        unit_exec_qty=2,
    )
    replacement = receipts._resolve_fast_sell_execution_receipt(
        state,
        order_no="S2",
        exec_price=10_030,
        cumulative_exec_qty=8,
        order_qty=8,
        remaining_qty=0,
        cumulative_exec_amount=80_240,
        execution_no="S2-E1",
        unit_exec_price=10_030,
        unit_exec_qty=8,
    )
    assert first["status"] == "partial"
    assert conflict["status"] == "invalid"
    assert state["cum_sell_qty"] == 10
    assert state["cum_sell_amount"] == 100_260
    assert state["avg_sell_price"] == 10_026
    assert replacement["position_complete"] is True


def test_fast_sell_final_nonzero_remaining_never_completes():
    state = {"cum_buy_qty": 10, "cum_sell_qty": 0, "cum_sell_amount": 0}
    result = receipts._resolve_fast_sell_execution_receipt(
        state,
        order_no="S1",
        exec_price=10_010,
        cumulative_exec_qty=10,
        order_qty=12,
        remaining_qty=2,
        cumulative_exec_amount=100_100,
        execution_no="E1",
        unit_exec_price=10_010,
        unit_exec_qty=10,
    )
    assert result["status"] == "partial"
    assert state.get("sell_receipt_position_complete") is not True
