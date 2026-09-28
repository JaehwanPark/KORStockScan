"""Zero-base Main handoff must commit only a matching attached generation."""

import time
import threading
from queue import Empty
from types import SimpleNamespace

from src.engine import kiwoom_sniper_v2 as main
from src.engine import sniper_state_handlers as handlers
from src.engine import kiwoom_orders


class _Session:
    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def add(self, row):
        row.id = len(self.rows) + 1
        self.rows[row.id] = row

    def flush(self):
        pass

    def get(self, _model, record_id):
        return self.rows.get(record_id)


class _Record:
    def __init__(self, **fields):
        self.__dict__.update(fields)


def _result():
    now = time.time()
    claim = {
        "code": "123456", "route": "krx_nxt_integrated", "source_sha256": "b" * 64,
        "claim_count": 1,
    }
    return {
        "claim": claim, "candidate": {**claim, "name": "TEST"},
        "result": "assessed", "machine_action": "ENTER_NOW",
        "result_epoch": now, "probe_price": 10000,
        "machine_bundle_sha256": "a" * 64,
        "probe_trade_epoch": now, "probe_depth_epoch": now,
    }


def _prepare(monkeypatch):
    rows = {}
    targets = []
    monkeypatch.setenv("KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED", "true")
    monkeypatch.setattr(main, "ACTIVE_TARGETS", targets)
    monkeypatch.setattr(main, "RecommendationHistory", _Record)
    monkeypatch.setattr(main, "DB", SimpleNamespace(get_session=lambda: _Session(rows)))
    monkeypatch.setattr(
        main, "evaluate_main_bot_control_exclusion",
        lambda _code: SimpleNamespace(excluded=False),
    )
    monkeypatch.setattr(main, "is_scalping_buy_time_allowed", lambda _time: True)
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_bucket": "krx_regular", "market_session_regime": "KRX_REGULAR",
    })
    monkeypatch.setattr(main, "_scalping_attach_capacity_decision", lambda *_args: (True, [], {}))
    monkeypatch.setattr(main, "_scanner_scheduler_startup_mode", lambda: "blocking_v0")
    monkeypatch.setattr(main, "_zero_base_attach_receipt", lambda *_args, **_kwargs: None)
    return rows, targets


def test_enter_now_commits_only_matching_attached_watching_row(monkeypatch):
    rows, targets = _prepare(monkeypatch)

    def attach(payload):
        assert payload["market_data_route"] == "krx_nxt_integrated"
        assert payload["broker_route"] == "SOR"
        assert payload["effective_venue"] == "KRX"
        targets.append({
            "id": payload["record_id"], "code": payload["code"],
            "status": "WATCHING", "zero_base_pending_db": True,
        })
        return True

    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", lambda payload, **_kwargs: attach(payload))
    assert main.handle_zero_base_machine_enter(_result()) is True
    assert rows[1].status == "WATCHING"
    assert "zero_base_pending_db" not in targets[0]
    assert main.handle_zero_base_machine_enter(_result()) is False
    assert len(rows) == 1


def test_integrated_aftermarket_attaches_integrated_cohort_and_sor(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_bucket": "KRX_NXT_AFTERMARKET",
        "market_session_regime": "KRX_NXT_AFTERMARKET",
    })
    def attach(payload, **_kwargs):
        targets.append({"id": payload["record_id"], "code": payload["code"], "status": "WATCHING"})
        assert payload["effective_venue"] == "KRX_NXT_INTEGRATED"
        assert payload["broker_route"] == "SOR"
        return True
    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", attach)
    assert main.handle_zero_base_machine_enter(_result()) is True
    assert rows[1].effective_venue == "KRX_NXT_INTEGRATED"


def test_separate_nxt_candidate_is_rejected(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    result = _result()
    result["claim"]["route"] = "nxt_only"
    result["candidate"]["route"] = "nxt_only"
    assert main.handle_zero_base_machine_enter(result) is False
    assert rows == {} and targets == []


def test_premarket_nxt_candidate_attaches_exact_route(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_bucket": "krx_like_premarket",
        "market_session_regime": "krx_like_premarket",
    })
    result = _result()
    result["claim"]["route"] = "nxt_only"
    result["candidate"]["route"] = "nxt_only"

    def attach(payload, **_kwargs):
        assert payload["effective_venue"] == "PREMARKET_KRX_LIKE"
        assert payload["market_data_route"] == "nxt_only"
        assert payload["broker_route"] == "NXT"
        targets.append({"id": payload["record_id"], "code": payload["code"],
                        "status": "WATCHING"})
        return True

    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", attach)
    assert main.handle_zero_base_machine_enter(result) is True
    assert rows[1].effective_venue == "PREMARKET_KRX_LIKE"


def test_integrated_candidate_is_rejected_in_premarket(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "scalping_session_venue_provenance", lambda _epoch: {
        "market_session_bucket": "krx_like_premarket",
        "market_session_regime": "krx_like_premarket",
    })
    assert main.handle_zero_base_machine_enter(_result()) is False
    assert rows == {} and targets == []


def test_attached_integrated_watching_registers_al_item(monkeypatch):
    _rows, targets = _prepare(monkeypatch)
    published = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda name, payload: published.append((name, payload)),
    ))
    monkeypatch.setattr(main, "_resolve_stock_marcap", lambda *_args: 0)
    monkeypatch.setattr(main, "_resolve_scanner_runtime_record_id", lambda *_args: 1)
    monkeypatch.setattr(main, "_scanner_identity_guard", lambda *_args: (True, {}))
    monkeypatch.setattr(main, "_log_scanner_runtime_target_attach", lambda *_args, **_kwargs: None)
    now = time.time()
    attached = main._apply_scalping_scanner_promoted_target({
        "record_id": 1, "code": "123456", "name": "TEST",
        "strategy": "SCALPING", "position_tag": "SCANNER",
        "buy_price": 10000, "added_time": now,
        "scanner_promotion_id": "ZBPROM-123456-1-1",
        "scanner_promotion_emitted_epoch": now,
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "venue": "KRX", "effective_venue": "KRX",
        "market_data_route": "krx_nxt_integrated",
        "broker_route": "SOR", "market_session_bucket": "krx_regular",
    })
    assert attached is True
    assert targets[0]["market_data_route"] == "krx_nxt_integrated"
    assert targets[0]["broker_route"] == "SOR"
    assert published == [("COMMAND_WS_REG", {
        "codes": ["123456_AL"], "source": "scanner_runtime_target_attach",
    })]


def test_attached_premarket_watching_registers_nx_item(monkeypatch):
    _rows, targets = _prepare(monkeypatch)
    published = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda name, payload: published.append((name, payload)),
    ))
    monkeypatch.setattr(main, "_resolve_stock_marcap", lambda *_args: 0)
    monkeypatch.setattr(main, "_resolve_scanner_runtime_record_id", lambda *_args: 1)
    monkeypatch.setattr(main, "_scanner_identity_guard", lambda *_args: (True, {}))
    monkeypatch.setattr(main, "_log_scanner_runtime_target_attach", lambda *_args, **_kwargs: None)
    now = time.time()
    assert main._apply_scalping_scanner_promoted_target({
        "record_id": 1, "code": "123456", "name": "TEST",
        "strategy": "SCALPING", "position_tag": "SCANNER",
        "buy_price": 10000, "added_time": now,
        "scanner_promotion_id": "ZBPROM-123456-1-1",
        "scanner_promotion_emitted_epoch": now,
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "venue": "PREMARKET_KRX_LIKE", "effective_venue": "PREMARKET_KRX_LIKE",
        "market_data_route": "nxt_only",
        "broker_route": "NXT", "market_session_bucket": "krx_like_premarket",
    })
    assert targets[0]["broker_route"] == "NXT"
    assert published == [("COMMAND_WS_REG", {
        "codes": ["123456_NX"], "source": "scanner_runtime_target_attach",
    })]


def test_zero_base_entry_request_binds_sor_and_fails_closed_on_lost_route():
    stock = {
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "market_data_route": "krx_nxt_integrated",
        "broker_route": "SOR", "effective_venue": "KRX_NXT_INTEGRATED",
    }
    request = {"qty": 1, "price": 10000, "order_type_code": "00"}
    assert handlers._bind_zero_base_order_request(stock, request)
    assert request["dmst_stex_tp"] == "SOR"
    assert kiwoom_orders.describe_buy_order_resolution(
        "00", price=10000, dmst_stex_tp=request["dmst_stex_tp"],
    )["effective_dmst_stex_tp"] == "SOR"
    for field, value in (("broker_route", "NXT"),
                         ("market_data_route", "nxt_only"),
                         ("effective_venue", "NXT")):
        assert not handlers._bind_zero_base_order_request(
            {**stock, field: value}, {},
        )


def test_zero_base_premarket_entry_binds_nxt_only_during_buy_window(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    class _Clock:
        @staticmethod
        def now(_zone):
            return datetime(2026, 9, 28, 8, 10, tzinfo=ZoneInfo("Asia/Seoul"))

    monkeypatch.setattr(handlers, "datetime", _Clock)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _time: True)
    stock = {
        "source_signature": "ZERO_BASE_DISCOVERY:" + "b" * 64,
        "market_data_route": "nxt_only", "broker_route": "NXT",
        "effective_venue": "PREMARKET_KRX_LIKE",
    }
    request = {"qty": 1, "price": 10000, "order_type_code": "00"}
    assert handlers._bind_zero_base_order_request(stock, request)
    assert request["dmst_stex_tp"] == "NXT"
    for field, value in (("broker_route", "SOR"),
                         ("market_data_route", "krx_nxt_integrated"),
                         ("effective_venue", "NXT")):
        assert not handlers._bind_zero_base_order_request({**stock, field: value}, {})


def test_enter_now_failure_expires_provisional_row(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", lambda _payload, **_kwargs: False)
    assert main.handle_zero_base_machine_enter(_result()) is False
    assert rows[1].status == "EXPIRED"
    assert targets == []


def test_enter_now_attach_exception_expires_provisional_row(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    events = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda topic, payload: events.append((topic, payload)),
    ))

    def failed_attach(payload, **_kwargs):
        targets.append({
            "id": payload["record_id"], "code": payload["code"],
            "status": "WATCHING", "zero_base_pending_db": True,
        })
        raise RuntimeError("partial_attach")

    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", failed_attach)
    assert main.handle_zero_base_machine_enter(_result()) is False
    assert rows[1].status == "EXPIRED"
    assert targets == []
    assert events[-1][0] == "COMMAND_WS_UNREG"


def test_inbox_attach_exception_expires_provisional_row_and_continues(monkeypatch):
    rows, targets = _prepare(monkeypatch)
    payload = {
        "code": "123456", "strategy": "SCALPING", "record_id": 1,
        "zero_base_pending_db": True,
    }
    rows[1] = _Record(
        stock_code="123456", status="PROBE_READY",
        scanner_source_signature="ZERO_BASE_DISCOVERY:" + "b" * 64,
    )
    inbox_items = [SimpleNamespace(payload=payload, enqueued_epoch=time.time())]

    def get_nowait():
        if inbox_items:
            return inbox_items.pop(0)
        raise Empty

    monkeypatch.setattr(main, "_SCANNER_PROMOTION_INBOX", SimpleNamespace(get_nowait=get_nowait))
    monkeypatch.setattr(main, "_scanner_scheduler_coalesce_duplicate_inbox", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(publish=lambda *_args: None))

    def failed_attach(attached_payload, **_kwargs):
        targets.append({
            "id": attached_payload["record_id"], "code": attached_payload["code"],
            "status": "WATCHING", "zero_base_pending_db": True,
        })
        raise RuntimeError("partial_attach")

    monkeypatch.setattr(main, "_apply_scalping_scanner_promoted_target", failed_attach)
    summary = main._drain_scanner_promotion_inbox(SimpleNamespace(), max_items=1)
    assert summary["drained"] == 1
    assert summary["applied"] == 0
    assert rows[1].status == "EXPIRED"
    assert targets == []


def test_enter_now_rejects_source_or_bundle_gap_before_db(monkeypatch):
    rows, _targets = _prepare(monkeypatch)
    result = _result()
    result["machine_bundle_sha256"] = "invalid"
    assert main.handle_zero_base_machine_enter(result) is False
    result = _result()
    result["candidate"]["source_sha256"] = "c" * 64
    assert main.handle_zero_base_machine_enter(result) is False
    result = _result()
    result["probe_depth_epoch"] -= 10
    assert main.handle_zero_base_machine_enter(result) is False
    assert rows == {}


def test_zero_base_uses_global_watch_cap_without_owner_quota_or_eviction(monkeypatch):
    monkeypatch.setattr(main, "_scalping_fifo_max_active", lambda: 2)
    incoming = {
        "code": "123456", "strategy": "SCALPING", "status": "WATCHING",
        "position_tag": "SCANNER", "source_signature": "ZERO_BASE_DISCOVERY:" + "a" * 64,
    }
    assert main._is_zero_base_watch_target(incoming)
    one = [{**incoming, "code": "000001"}]
    allowed, replacements, fields = main._scalping_attach_capacity_decision(
        incoming, time.time(), watching_targets=one,
    )
    assert allowed is True and replacements == []
    assert fields["scanner_watch_budget_policy"] == "zero_base_global_watch_cap_v1"
    full = [*one, {**incoming, "code": "000002"}]
    allowed, replacements, _fields = main._scalping_attach_capacity_decision(
        incoming, time.time(), watching_targets=full,
    )
    assert allowed is False and replacements == []


def test_late_registration_keeps_same_code_probe_reserved_until_cleanup(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED", "true")
    monkeypatch.setattr(main, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_IN_FLIGHT", set())
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_SLOTS", threading.BoundedSemaphore(8))
    monkeypatch.setattr(main, "_ZERO_BASE_PROBE_EXECUTOR", SimpleNamespace(
        submit=lambda fn: fn(),
    ))
    monkeypatch.setattr(main, "evaluate_main_bot_control_exclusion", lambda _code: SimpleNamespace(excluded=False))
    events = []
    monkeypatch.setattr(main, "event_bus", SimpleNamespace(
        publish=lambda topic, payload: events.append((topic, payload)),
    ))
    callbacks = []

    def probe(request, **kwargs):
        callbacks.append(kwargs["release_ws"])
        return {**request, "result": "source_unavailable", "reason": "ws_registration_timeout",
                "_ws_cleanup_deferred": True}

    monkeypatch.setattr(main, "run_zero_base_probe", probe)
    monkeypatch.setattr(main, "_zero_base_release_probe_ws", lambda *_args: None)
    request = {"claim": _result()["claim"], "candidate": _result()["candidate"]}
    main.handle_zero_base_probe_requested(request)
    assert "123456" in main._ZERO_BASE_PROBE_IN_FLIGHT
    main.handle_zero_base_probe_requested(request)
    assert events[-1][1]["reason"] == "same_code_probe_in_flight"
    callbacks[0]("123456", "123456")
    assert "123456" not in main._ZERO_BASE_PROBE_IN_FLIGHT
