"""Quantity observation custody survives early exit, restart and writer failure."""

import copy
import json
from pathlib import Path

import pytest

from src.engine.scalping import initial_quantity_cap_observation as observer


class Sink:
    def __init__(self):
        self.jobs = []
        self.accept = True

    def __call__(self, callback, *args, **kwargs):
        kwargs.pop("observation_category", None)
        # Match the production queue's finite JSON envelope and copy boundary.
        args, kwargs = json.loads(json.dumps([args, kwargs], allow_nan=False))
        if not self.accept:
            return {"status": "unavailable"}
        self.jobs.append((callback, args, kwargs))
        return {"status": "queued", "structured_append_succeeded": False}

    def drain(self):
        while self.jobs:
            callback, args, kwargs = self.jobs.pop(0)
            callback(*args, **kwargs)


@pytest.fixture
def capture(tmp_path, monkeypatch):
    from src.utils import pipeline_event_logger

    monkeypatch.setattr(observer, "_ACTIVE", {})
    monkeypatch.setattr(observer, "_DATA_ROOT", tmp_path)
    monkeypatch.setattr(observer, "_SINK", None)
    monkeypatch.setattr(observer, "_COUNTS", __import__("collections").Counter())
    monkeypatch.setattr(observer, "_process_start", lambda pid: "12345")
    monkeypatch.setattr(observer, "_process_exists", lambda pid: False)
    events = []

    def emit(*args, **kwargs):
        events.append((args, copy.deepcopy(kwargs)))
        from datetime import datetime
        from zoneinfo import ZoneInfo

        emitted = datetime.fromtimestamp(
            kwargs["observed_at_epoch"], ZoneInfo("Asia/Seoul")
        )
        return dict(
            schema_version=1,
            event_type="pipeline_event",
            pipeline=args[0],
            stock_name=args[1],
            stock_code=args[2],
            stage=args[3],
            record_id=kwargs["record_id"],
            fields={str(k): str(v) for k, v in kwargs["fields"].items()},
            emitted_at=emitted.isoformat(),
            emitted_date=emitted.date().isoformat(),
            storage_partition_date=emitted.date().isoformat(),
            text_payload="native source observation",
            structured_append_succeeded=True,
        )

    emit.native = pipeline_event_logger.emit_pipeline_event
    monkeypatch.setattr(pipeline_event_logger, "emit_pipeline_event", emit)
    sink = Sink()
    observer.configure_sink(sink)
    trace = dict(
        started_at_epoch=1792108800.0,
        entry_submit_attempt_id="a" * 32,
        entry_execution_sizing_plan_sha256="b" * 64,
    )
    stock = dict(
        id=49340,
        code="403870",
        name="test",
        status="HOLDING",
        buy_qty=5,
        _initial_quantity_cap_trace=trace,
    )
    yield tmp_path, sink, events, trace, stock


def register(capture):
    _, _, _, trace, stock = capture
    return observer.register(
        code=stock["code"], name=stock["name"], record_id=stock["id"], trace=trace
    )


def pending(root):
    return list((root / "runtime/initial_quantity/cap_capture_pending").glob("*.json"))


def closed(root):
    return list(
        (root / "runtime/initial_quantity/cap_capture_receipts").glob("*/*.json")
    )


def test_start_is_only_queued_until_existing_drain_persists(capture):
    root, sink, events, trace, _ = capture
    assert register(capture)
    assert pending(root) == [] and events == []
    sink.drain()
    assert len(pending(root)) == 1
    receipt = json.loads(pending(root)[0].read_text())
    assert receipt["status"] == "pending" and receipt["raw_event_durable"] is True
    assert receipt["capture_id"] == trace["capture_lifecycle_identity"]["capture_id"]
    assert len(closed(root)) == 0


def test_duplicate_start_does_not_reset_pending_clock_or_emit_twice(capture):
    _, sink, events, _, _ = capture
    assert register(capture) and register(capture)
    sink.drain()
    assert len(events) == 1


def test_order_start_is_frozen_and_queued_once(capture):
    from src.engine import sniper_state_handlers as handler

    root, sink, events, trace, stock = capture
    register(capture)
    stock["initial_quantity_bundle"] = {
        "attempt_id": "a" * 32,
        "schedule": {"order_start_at_epoch": trace["started_at_epoch"] + 10},
    }
    handler._start_initial_quantity_cap_capture(
        stock, attempt_id="a" * 32, submission_fields={}
    )
    stock["initial_quantity_bundle"]["schedule"]["order_start_at_epoch"] += 50
    handler._start_initial_quantity_cap_capture(
        stock, attempt_id="a" * 32, submission_fields={}
    )
    sink.drain()
    assert [e[0][-1] for e in events] == [
        "initial_quantity_cap_capture_started",
        "initial_quantity_cap_capture_order_started",
    ]
    body = json.loads(pending(root)[0].read_text())
    assert body["fields"]["capture_order_start_epoch"] == 1792108810.0
    assert body["fields"]["capture_end_epoch"] == 1792110010.0


@pytest.mark.parametrize(
    "damage", [None, "queue", "raw", "sim", "record", "code", "pid", "unproven", "late"]
)
def test_native_sell_writer_closes_current_capture_without_state_handler(
    capture, monkeypatch, damage
):
    from src.utils import pipeline_event_logger as logger
    from types import SimpleNamespace

    root, sink, events, trace, stock = capture
    register(capture)
    sink.drain()
    from src.engine import sniper_state_handlers as handler

    stock["initial_quantity_bundle"] = {
        "attempt_id": trace["entry_submit_attempt_id"],
        "schedule": {"order_start_at_epoch": trace["started_at_epoch"] + 10},
    }
    handler._start_initial_quantity_cap_capture(
        stock, attempt_id=trace["entry_submit_attempt_id"], submission_fields={}
    )
    sink.drain()
    native = logger.emit_pipeline_event.native
    monkeypatch.setattr(logger, "DATA_DIR", root)
    monkeypatch.setattr(logger, "_get_producer_compactor", lambda: None)
    monkeypatch.setattr(logger, "log_info", lambda *a: None)
    monkeypatch.setattr(
        logger, "TRADING_RULES", SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True)
    )
    fields = dict(
        pipeline_lifecycle_population_scope="real_record_bound",
        actual_order_submitted=True,
        broker_order_forbidden=False,
    )
    if damage == "queue":
        sink.accept = False
    if damage == "raw":
        monkeypatch.setattr(
            logger,
            "_append_pipeline_event_jsonl",
            lambda *a, **k: (_ for _ in ()).throw(OSError("injected")),
        )
    if damage == "sim":
        fields["pipeline_lifecycle_population_scope"] = "sim_observation_only"
    if damage == "unproven":
        fields["actual_order_submitted"] = False
    if damage == "pid":
        observer._ACTIVE[trace["capture_lifecycle_identity"]["capture_id"]]["fields"][
            "capture_runtime_pid"
        ] += 1
    record = stock["id"] + 1 if damage == "record" else stock["id"]
    code = "005930" if damage == "code" else stock["code"]
    at = (
        trace["order_capture_end_epoch"] + 1
        if damage == "late"
        else trace["started_at_epoch"] + 60
    )
    original = copy.deepcopy(stock)
    native(
        "HOLDING_PIPELINE",
        stock["name"],
        code,
        "sell_completed",
        record_id=record,
        fields=fields,
        observed_at_epoch=at,
    )
    assert stock == original  # Source closure grants no position/order mutation.
    assert len(pending(root)) == 1 and closed(root) == []
    sink.drain()
    if damage not in (None, "late"):
        assert len(pending(root)) == 1 and closed(root) == []
        assert observer.capture_active(
            trace["capture_lifecycle_identity"]["capture_id"]
        )
    else:
        body = json.loads(closed(root)[0].read_text())
        assert pending(root) == [] and body["status"] == "interrupted"
        assert body["fields"]["capture_interruption_reason"] == (
            "capture_horizon_terminal_missing_at_position_completion"
            if damage == "late"
            else "position_completed_before_capture_horizon"
        )
        assert len(body["fields"]["capture_position_terminal_sha256"]) == 64
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from src.engine.scalping.initial_quantity_policy import (
            _quantity_capture_lifecycle_sources,
            _capture_source_issue,
        )

        _, receipts = _quantity_capture_lifecycle_sources(
            root, "2026-10-16", decode=True
        )
        assert receipts == [body]
        source = dict(
            attempt_id=trace["entry_submit_attempt_id"],
            plan_sha256=trace["entry_execution_sizing_plan_sha256"],
            record_id=stock["id"],
            stock_code=stock["code"],
            capture_terminal_required=True,
            capture_exit_epoch=at,
            capture_receipts=[
                dict(
                    stage=body["raw_event_stage"],
                    at=datetime.fromtimestamp(at, ZoneInfo("Asia/Seoul")).isoformat(),
                    fields=body["fields"],
                )
            ],
        )
        assert _capture_source_issue(source) == (
            "capture_interrupted" if damage == "late" else None
        )
        assert not observer.capture_active(
            trace["capture_lifecycle_identity"]["capture_id"]
        )
        count = len(events)
        native(
            "HOLDING_PIPELINE",
            stock["name"],
            code,
            "sell_completed",
            record_id=record,
            fields=fields,
            observed_at_epoch=at,
        )
        sink.drain()
        assert len(events) == count


def test_finished_requires_raw_durability_before_pending_is_closed(
    capture, monkeypatch
):
    from src.engine import sniper_state_handlers as handler
    from src.utils import pipeline_event_logger

    root, sink, _, trace, stock = capture
    register(capture)
    sink.drain()
    trace.update(
        order_start_epoch=1792108800.0,
        order_capture_end_epoch=1792110000.0,
        capture_clock_status="frozen_order_start",
    )
    monkeypatch.setattr(
        pipeline_event_logger,
        "emit_pipeline_event",
        lambda *a, **k: {
            "structured_append_succeeded": False,
            "structured_append_status": "raw_append_failed",
        },
    )
    handler._observe_initial_quantity_cap_following_tick(
        stock, stock["code"], {}, now_ts=1792110001.0
    )
    assert (
        "_initial_quantity_cap_trace" not in stock
    )  # admitted is separate from durable
    sink.drain()
    assert len(pending(root)) == 1 and closed(root) == []
    assert json.loads(pending(root)[0].read_text())["status"] == "pending"


def test_unpersisted_handler_label_cannot_censor_or_remove_capture(
    capture, monkeypatch
):
    from src.engine import sniper_state_handlers as handler

    root, sink, _, trace, stock = capture
    register(capture)
    sink.drain()
    monkeypatch.setattr(
        handler, "_holding_pipeline_stable_block_log_decision", lambda *a: (False, {})
    )
    handler._log_holding_pipeline(stock, stock["code"], "sell_completed")
    assert stock["_initial_quantity_cap_trace"] is trace
    assert len(pending(root)) == 1 and closed(root) == []


def test_shutdown_and_dead_producer_have_explicit_distinct_dispositions(
    capture, monkeypatch
):
    root, sink, events, trace, stock = capture
    register(capture)
    sink.drain()
    observer.configure_sink(None)
    sink.drain()
    assert (
        events[-1][1]["fields"]["capture_interruption_reason"]
        == "process_shutdown_observation_censored"
    )
    assert json.loads(closed(root)[0].read_text())["status"] == "interrupted"
    trace["entry_submit_attempt_id"] = "c" * 32
    trace.pop("capture_lifecycle_identity")
    observer.configure_sink(sink)
    register(capture)
    sink.drain()
    monkeypatch.setattr(observer, "_process_start", lambda pid: None)
    before = trace["capture_lifecycle_identity"].copy()
    observer._recover_pending()
    fields = events[-1][1]["fields"]
    assert (
        fields["capture_interruption_reason"] == "prior_process_ended_before_terminal"
    )
    assert fields["capture_runtime_pid"] == before["capture_runtime_pid"]
    assert fields["capture_source_date"] == "2026-10-16"
    assert fields["capture_durable_tick_count"] is None
    assert (
        fields["capture_recovery_observed_at_epoch"] > fields["capture_planned_epoch"]
    )
    assert pending(root) == []


def test_recovery_does_not_close_live_same_start_ticks(capture):
    root, sink, events, _, _ = capture
    register(capture)
    sink.drain()
    observer._recover_pending()
    assert len(events) == 1 and len(pending(root)) == 1 and closed(root) == []


@pytest.mark.parametrize("bad", ["hash", "size", "symlink"])
def test_invalid_pending_is_preserved_without_invented_terminal(
    capture, monkeypatch, bad
):
    root, sink, events, _, _ = capture
    register(capture)
    sink.drain()
    path = pending(root)[0]
    if bad == "hash":
        value = json.loads(path.read_text())
        value["record_id"] = 999
        path.write_text(json.dumps(value))
    elif bad == "size":
        path.write_text("x" * (observer.MAX_RECEIPT_BYTES + 1))
    else:
        target = root / "original"
        path.rename(target)
        path.symlink_to(target)
    monkeypatch.setattr(observer, "_process_start", lambda pid: None)
    observer._recover_pending()
    assert len(events) == 1 and len(pending(root)) == 1 and closed(root) == []


def test_cap_tick_does_not_add_pending_disk_writes(capture, monkeypatch):
    root, sink, _, trace, stock = capture
    register(capture)
    sink.drain()
    before = pending(root)[0].read_bytes()
    observer.append(
        code=stock["code"],
        name=stock["name"],
        record_id=stock["id"],
        stage="initial_quantity_cap_following_tick",
        fields={
            **trace["capture_lifecycle_identity"],
            "entry_submit_attempt_id": "a" * 32,
            "entry_execution_sizing_plan_sha256": "b" * 64,
        },
        observed_at_epoch=trace["started_at_epoch"] + 10,
    )
    sink.drain()
    assert pending(root)[0].read_bytes() == before


def test_registry_budget_never_becomes_order_or_startup_gate(capture, monkeypatch):
    _, sink, events, trace, stock = capture
    monkeypatch.setattr(observer, "MAX_ACTIVE", 1)
    register(capture)
    foreign = {**trace, "entry_submit_attempt_id": "c" * 32}
    assert (
        observer.register(code="005930", name="foreign", record_id=1, trace=foreign)
        is False
    )
    assert stock["status"] == "HOLDING" and stock["buy_qty"] == 5
    assert len(sink.jobs) == 1


def test_lifecycle_id_is_stable_after_pipeline_scalar_normalization(capture):
    _, _, _, trace, _ = capture
    register(capture)
    fields = {
        **trace["capture_lifecycle_identity"],
        "entry_submit_attempt_id": "a" * 32,
        "entry_execution_sizing_plan_sha256": "b" * 64,
    }
    assert observer._capture_id(fields) == observer._capture_id(
        {k: str(v) for k, v in fields.items()}
    )


def test_receipt_io_failure_preserves_original_raw_observation(capture, monkeypatch):
    _, sink, events, _, _ = capture

    def fail(*a, **k):
        raise OSError("disk unavailable")

    monkeypatch.setattr(observer, "_atomic_receipt", fail)
    assert register(capture)
    sink.drain()
    assert len(events) == 1 and observer.snapshot()["lifecycle_receipt_failed"] == 2


def test_start_queue_refusal_is_preserved_in_terminal_queue_gap(capture):
    _, sink, events, trace, stock = capture
    sink.accept = False
    assert register(capture) is False
    assert trace["queue_rejected_count"] == 1
    sink.accept = True
    assert observer.interrupt(
        code=stock["code"],
        name=stock["name"],
        record_id=stock["id"],
        trace=trace,
        reason="attempt_replaced",
    )
    sink.drain()
    assert events[-1][1]["fields"]["capture_queue_rejected_count"] == 1


def test_stale_stock_identity_cannot_rebind_capture_to_new_record(capture):
    from src.engine import sniper_state_handlers as handler

    root, sink, events, trace, stock = capture
    register(capture)
    sink.drain()
    stock["id"] = 99999
    handler._observe_initial_quantity_cap_following_tick(
        stock, stock["code"], {}, now_ts=trace["started_at_epoch"] + 10
    )
    sink.drain()
    assert "_initial_quantity_cap_trace" not in stock
    assert events[-1][1]["record_id"] == 49340
    assert (
        events[-1][1]["fields"]["capture_interruption_reason"]
        == "record_identity_replaced"
    )
    assert json.loads(closed(root)[0].read_text())["record_id"] == 49340


def test_first_durable_interruption_is_not_upgraded_by_late_finish(capture):
    root, sink, events, trace, stock = capture
    register(capture)
    sink.drain()
    observer.interrupt(
        code=stock["code"],
        name=stock["name"],
        record_id=stock["id"],
        trace=trace,
        reason="attempt_replaced",
    )
    sink.drain()
    before = closed(root)[0].read_bytes()
    fields = events[-1][1]["fields"]
    observer.append(
        code=stock["code"],
        name=stock["name"],
        record_id=stock["id"],
        stage="initial_quantity_cap_capture_finished",
        fields={**fields, "capture_disposition": "horizon_reached"},
        observed_at_epoch=trace["started_at_epoch"] + 1201,
    )
    sink.drain()
    assert closed(root)[0].read_bytes() == before
    assert pending(root) == []


def test_unfilled_attempt_clear_accounts_for_source_without_rewriting_position(
    capture, monkeypatch
):
    from src.engine import sniper_state_handlers as handler

    root, sink, events, trace, stock = capture
    register(capture)
    sink.drain()
    stock.update(buy_qty=0, entry_filled_qty=0, status="BUY_ORDERED")
    monkeypatch.setattr(handler, "move_orders_to_terminal", lambda *a, **k: None)
    monkeypatch.setattr(handler, "_clear_entry_arm", lambda *a: None)
    handler._clear_pending_entry_meta(stock)
    sink.drain()
    assert "_initial_quantity_cap_trace" not in stock
    assert stock["status"] == "BUY_ORDERED" and stock["buy_qty"] == 0
    assert (
        events[-1][1]["fields"]["capture_interruption_reason"]
        == "entry_attempt_cleared_without_position"
    )
    assert len(closed(root)) == 1


def test_pending_recovery_uses_existing_queue_instead_of_startup_io(
    capture, monkeypatch
):
    root, sink, events, _, _ = capture
    register(capture)
    sink.drain()
    monkeypatch.setattr(observer, "_process_start", lambda pid: None)
    observer.configure_sink(sink, recover_pending=True)
    assert len(events) == 1 and len(pending(root)) == 1
    sink.drain()
    assert len(events) == 2 and pending(root) == []


@pytest.mark.parametrize("string_record_id", [False, True])
def test_real_native_writer_receipt_is_accepted_by_dated_consumer(
    capture, monkeypatch, string_record_id
):
    import hashlib
    from src.utils import pipeline_event_logger as logger
    from src.engine.scalping.initial_quantity_policy import (
        _quantity_capture_lifecycle_sources,
    )

    root, sink, _, trace, stock = capture
    if string_record_id:
        stock["id"] = str(stock["id"])
    monkeypatch.setattr(
        logger, "emit_pipeline_event", logger.emit_pipeline_event.native
    )
    monkeypatch.setattr(logger, "DATA_DIR", root)
    monkeypatch.setattr(logger, "_get_producer_compactor", lambda: None)
    monkeypatch.setattr(logger, "_should_emit_text_info", lambda *a: False)
    from dataclasses import replace

    monkeypatch.setattr(
        logger,
        "TRADING_RULES",
        replace(logger.TRADING_RULES, PIPELINE_EVENT_JSONL_ENABLED=True),
    )
    register(capture)
    sink.drain()
    observer.interrupt(
        code=stock["code"],
        name=stock["name"],
        record_id=stock["id"],
        trace=trace,
        reason="attempt_replaced",
        now=trace["started_at_epoch"] + 20,
    )
    sink.drain()
    native_lines = (
        (root / "pipeline_events/pipeline_events_2026-10-16.jsonl")
        .read_text()
        .splitlines()
    )
    raw_terminal = json.loads(native_lines[-1])
    receipt = json.loads(closed(root)[0].read_text())
    assert (
        receipt["raw_event_identity_contract"]
        == "canonical_original_pipeline_event_sha256_v1"
    )
    assert (
        receipt["raw_event_id"]
        == hashlib.sha256(
            json.dumps(
                raw_terminal,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
        ).hexdigest()
    )
    generation, rows = _quantity_capture_lifecycle_sources(
        root, "2026-10-16", decode=True
    )
    assert len(generation["files"]) == 1 and len(rows) == 1
    assert rows[0]["capture_id"] == trace["capture_lifecycle_identity"]["capture_id"]
    assert rows[0]["status"] == "interrupted"


def test_shutdown_preserves_rejected_start_without_live_stock(capture):
    _, sink, events, trace, _ = capture
    sink.accept = False
    assert register(capture) is False
    sink.accept = True
    observer.configure_sink(None)
    sink.drain()
    assert events[-1][1]["fields"]["capture_queue_rejected_count"] == 1


def test_failed_recovery_admission_is_explicit_and_keeps_pending(capture):
    root, sink, events, _, _ = capture
    register(capture)
    sink.drain()
    sink.accept = False
    observer.configure_sink(sink, recover_pending=True)
    assert observer.snapshot()["pending_recovery_queue_failed"] == 1
    assert len(events) == 1 and len(pending(root)) == 1


def test_unreadable_live_pid_identity_does_not_invent_process_end(capture, monkeypatch):
    root, sink, events, _, _ = capture
    register(capture)
    sink.drain()
    monkeypatch.setattr(observer, "_process_start", lambda pid: None)
    monkeypatch.setattr(observer, "_process_exists", lambda pid: True)
    observer._recover_pending()
    assert len(events) == 1 and len(pending(root)) == 1
    assert observer.snapshot()["pending_recovery_identity_unproven"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        {"capture_lifecycle_identity": ["invalid"]},
        {"capture_lifecycle_identity": {"capture_stock_code": "403870"}},
        {"queue_rejected_count": "invalid"},
        {"queued_observation_count": -1},
    ],
)
def test_malformed_trace_cannot_interrupt_live_sell_or_cancel_cleanup(
    capture, monkeypatch, mutation
):
    from src.engine import sniper_state_handlers as handler

    _, _, _, trace, stock = capture
    trace.update(mutation)
    monkeypatch.setattr(
        handler, "_holding_pipeline_stable_block_log_decision", lambda *a: (False, {})
    )
    assert (
        handler._log_holding_pipeline(stock, stock["code"], "sell_completed") is False
    )
    assert stock["buy_qty"] == 5 and stock["status"] == "HOLDING"
    stock.update(buy_qty=0, entry_filled_qty=0, status="BUY_ORDERED")
    monkeypatch.setattr(handler, "move_orders_to_terminal", lambda *a, **k: None)
    monkeypatch.setattr(handler, "_clear_entry_arm", lambda *a: None)
    handler._clear_pending_entry_meta(stock)
    assert stock["status"] == "BUY_ORDERED" and stock["buy_qty"] == 0
    assert (
        observer.snapshot()["capture_metadata_invalid"] == 1
    )  # Only the real cancellation path inspects the trace.


@pytest.mark.parametrize("clock", [None, True, float("nan"), float("inf"), -1, 1e100])
def test_registration_clock_invalid_returns_source_only_failure(capture, clock):
    _, sink, _, trace, stock = capture
    trace["started_at_epoch"] = clock
    assert register(capture) is False
    assert observer.snapshot()["capture_metadata_invalid"] == 1 and sink.jobs == []
    assert stock["status"] == "HOLDING" and stock["buy_qty"] == 5


def test_malformed_registered_identity_does_not_throw_from_runtime_observers(capture):
    from src.engine import sniper_state_handlers as handler

    _, _, _, trace, stock = capture
    trace["capture_lifecycle_identity"] = ["invalid"]
    handler._start_initial_quantity_cap_capture(
        stock, attempt_id="a" * 32, submission_fields={}
    )
    handler._observe_initial_quantity_cap_following_tick(
        stock, stock["code"], {}, now_ts=1792108801.0
    )
    assert trace["capture_clock_status"] == "capture_metadata_invalid"
    assert stock["status"] == "HOLDING" and stock["buy_qty"] == 5


@pytest.mark.parametrize("quote", [None, {}])
def test_native_horizon_completion_does_not_depend_on_a_terminal_quote(
    capture, monkeypatch, quote
):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping.initial_quantity_policy import (
        _quantity_capture_lifecycle_sources,
    )

    root, sink, events, trace, stock = capture
    register(capture)
    sink.drain()
    stock["initial_quantity_bundle"] = {
        "attempt_id": trace["entry_submit_attempt_id"],
        "schedule": {"order_start_at_epoch": trace["started_at_epoch"] + 10},
    }
    handler._start_initial_quantity_cap_capture(
        stock, attempt_id=trace["entry_submit_attempt_id"], submission_fields={}
    )
    sink.drain()
    handler._observe_initial_quantity_cap_following_tick(
        stock, stock["code"], quote, now_ts=trace["order_capture_end_epoch"] + 1
    )
    assert closed(root) == []  # Queue acceptance alone is not completion.
    sink.drain()
    _, receipts = _quantity_capture_lifecycle_sources(root, "2026-10-16", decode=True)
    assert len(receipts) == 1 and receipts[0]["status"] == "finished"
    assert receipts[0]["fields"]["capture_disposition"] == "horizon_reached"
    assert receipts[0]["fields"]["observation_coverage"] == "sampled_last_trade_tick"
    assert (stock["status"], stock["buy_qty"]) == ("HOLDING", 5)
