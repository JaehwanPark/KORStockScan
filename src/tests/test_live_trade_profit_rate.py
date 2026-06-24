from dataclasses import replace
from datetime import datetime

import src.engine.sniper_execution_receipts as receipts
import src.engine.sniper_s15_fast_track as s15
import src.engine.sniper_sync as sniper_sync
import src.engine.sniper_state_handlers as state_handlers
from src.engine.trade_profit import calculate_net_profit_rate
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


class _ReceiptDB:
    def __init__(self, record):
        self.record = record

    def get_session(self):
        return _ReceiptSession(self.record)


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
                record for record in self._history_records
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


class _SyncDB:
    def __init__(self, active_records, pending_records=None, history_records=None):
        self._session = _SyncSession(active_records, pending_records or [], history_records or [])

    def get_session(self):
        return self._session

    def get_latest_is_nxt(self, code):
        return False

    def get_latest_marcap(self, code):
        return 0


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


def test_trade_profit_helper_accounts_for_costs():
    assert calculate_net_profit_rate(100000, 100100) == -0.13
    assert calculate_net_profit_rate(14320, 14420) == 0.47


def test_sell_receipt_persists_net_profit_rate(monkeypatch):
    record = type(
        "Record",
        (),
        {"buy_price": 100000.0, "status": "SELL_ORDERED", "sell_price": 0, "sell_time": None, "profit_rate": 0.0},
    )()

    receipts.DB = _ReceiptDB(record)
    receipts.event_bus = _Bus()
    monkeypatch.setattr(receipts, "_log_holding_pipeline", lambda *args, **kwargs: None)

    receipts._update_db_for_sell(
        7,
        100100,
        datetime(2026, 4, 7, 9, 0, 0),
        {"code": "123456", "name": "TEST", "msg_audience": "ADMIN_ONLY"},
        "SCALPING",
        False,
    )

    assert record.status == "COMPLETED"
    assert record.sell_price == 100100
    assert record.profit_rate == -0.13
    assert receipts.event_bus.events
    _, payload = receipts.event_bus.events[-1]
    assert "-0.13%" in payload["message"]


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
    }

    receipts._update_db_for_sell(
        7,
        100100,
        datetime(2026, 4, 7, 9, 0, 0),
        receipt_snapshot,
        "SCALPING",
        False,
    )

    assert receipt_snapshot["no_scale_in_counterfactual_profit_pct"] == calculate_net_profit_rate(97000.0, 100100)
    assert receipt_snapshot["scale_in_incremental_realized_delta_pct"] == round(
        record.profit_rate - receipt_snapshot["no_scale_in_counterfactual_profit_pct"],
        4,
    )
    assert logged["kwargs"]["no_scale_in_counterfactual_profit_pct"] == receipt_snapshot[
        "no_scale_in_counterfactual_profit_pct"
    ]
    assert logged["kwargs"]["scale_in_incremental_realized_delta_pct"] == receipt_snapshot[
        "scale_in_incremental_realized_delta_pct"
    ]
    assert logged["kwargs"]["pre_add_avg_price"] == 97000.0
    assert logged["kwargs"]["post_add_avg_price"] == 100000.0
    assert logged["kwargs"]["pre_add_qty"] == 10
    assert logged["kwargs"]["post_add_qty"] == 20
    assert len(post_sell_calls) == 1
    assert post_sell_calls[0]["stock"]["no_scale_in_counterfactual_profit_pct"] == receipt_snapshot[
        "no_scale_in_counterfactual_profit_pct"
    ]
    assert post_sell_calls[0]["stock"]["scale_in_incremental_realized_delta_pct"] == receipt_snapshot[
        "scale_in_incremental_realized_delta_pct"
    ]


def test_periodic_account_sync_uses_net_profit_rate_for_missing_sell_receipt(monkeypatch):
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
    sniper_sync.ACTIVE_TARGETS = [{"code": "123456", "status": "SELL_ORDERED", "sell_target_price": 100100}]
    sniper_sync.HIGHEST_PRICES = {"123456": 100500}
    sniper_sync.STATE_LOCK = _DummyLock()
    monkeypatch.setattr(sniper_sync.kiwoom_utils, "get_account_balance_kt00005", lambda token: ([], {"KRX"}))

    sniper_sync.periodic_account_sync()

    assert record.status == "COMPLETED"
    assert record.sell_price == 100100
    assert record.profit_rate == -0.13
    assert sniper_sync.ACTIVE_TARGETS[0]["status"] == "COMPLETED"
    assert "123456" not in sniper_sync.HIGHEST_PRICES


def test_periodic_account_sync_recovers_broker_only_holding_from_watching_record(monkeypatch):
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
        lambda token: ([{"code": "189300", "name": "인텔리안테크", "qty": 7, "buy_price": 133610}], {"KRX"}),
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
    assert any("매수 체결 확인 (브로커 복구)" in event["message"] for event in telegram_events)
    assert any("잔고조회 확인" in event["message"] for event in telegram_events)


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
        lambda token: ([{"code": "016360", "name": "삼성증권", "qty": 1, "buy_price": 111400}], {"KRX"}),
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
    sniper_sync.KIWOOM_TOKEN = "very_long_real_token_for_test_enable_2nd_pass_0123456789"
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
        lambda token: ([{"code": "189300", "name": "인텔리안테크", "qty": 7, "buy_price": 133610}], {"KRX"}),
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
    monkeypatch.setattr(sniper_sync, "_iter_recovery_log_paths", lambda: ["pipeline.log"])
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
        lambda **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
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
        radar=None,
        ai_engine=None,
    )

    assert sell_calls
    assert stock["status"] == "SELL_ORDERED"
    assert "-0.13%" in stock["pending_sell_msg"]


def test_holding_state_skips_scalping_loss_exit_for_legacy_broker_recovered(monkeypatch):
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
        lambda **kwargs: sell_calls.append(kwargs) or {"return_code": "0", "ord_no": "S1"},
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
