from datetime import datetime
from types import SimpleNamespace

import src.engine.sniper_condition_handlers as handlers
import src.engine.sniper_s15_fast_track as s15


class _FakeDateTime(datetime):
    _fixed_now = datetime(2026, 4, 4, 9, 5, 0)

    @classmethod
    def now(cls, tz=None):
        return cls._fixed_now


class _DummyEventBus:
    def __init__(self):
        self.events = []

    def publish(self, topic, payload):
        self.events.append((topic, payload))


class _DummyQuery:
    def __init__(self, records):
        self.records = records
        self.filters = {}

    def filter_by(self, **kwargs):
        self.filters.update(kwargs)
        return self

    def first(self):
        for record in self.records:
            if all(getattr(record, key, None) == value for key, value in self.filters.items()):
                return record
        return None

    def all(self):
        return [
            record
            for record in self.records
            if all(getattr(record, key, None) == value for key, value in self.filters.items())
        ]

    def delete(self):
        matches = self.all()
        for record in matches:
            self.records.remove(record)
        return len(matches)


class _DummySession:
    def __init__(self, records):
        self.records = records

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, _model):
        return _DummyQuery(self.records)

    def add(self, record):
        record.id = len(self.records) + 1
        self.records.append(record)

    def flush(self):
        return None


class _DummyDB:
    def __init__(self):
        self.records = []

    def get_session(self):
        return _DummySession(self.records)

    def get_latest_marcap(self, _code):
        return 123456789

    def find_reusable_watching_record(
        self,
        session,
        *,
        rec_date,
        stock_code,
        strategy=None,
        position_tag=None,
    ):
        for record in reversed(session.records):
            if getattr(record, "rec_date", None) != rec_date:
                continue
            if getattr(record, "stock_code", None) != stock_code:
                continue
            if strategy is not None and getattr(record, "strategy", None) != strategy:
                continue
            if position_tag is not None and getattr(record, "position_tag", None) != position_tag:
                continue
            if str(getattr(record, "status", "") or "") not in {"WATCHING", "EXPIRED"}:
                continue
            if getattr(record, "buy_time", None):
                continue
            if int(getattr(record, "buy_qty", 0) or 0) != 0:
                continue
            return record
        return None


def _bind_test_deps(active_targets, db, event_bus):
    handlers._CONDITION_STATE.clear()
    s15.FAST_SCALP_POOL.clear()
    s15.FAST_TRADE_STATE.clear()
    s15.FAST_REENTRY_BLOCK.clear()
    s15.DB = db
    handlers.bind_condition_dependencies(
        kiwoom_token="token",
        ws_manager=None,
        db=db,
        event_bus=event_bus,
        active_targets=active_targets,
        escape_markdown_fn=lambda text: text,
    )


def test_resolve_condition_profile_for_open_reclaim():
    profile = handlers.resolve_condition_profile("scalp_open_reclaim_01")

    assert profile is not None
    assert profile["start"].hour == 9 and profile["start"].minute == 3
    assert profile["end"].hour == 9 and profile["end"].minute == 20
    assert profile["position_tag"] == "OPEN_RECLAIM"
    assert profile["use_debounce"] is False


def test_resolve_condition_profile_for_s15_is_intraday_fast_track():
    base = handlers.resolve_condition_profile("s15_scan_base_01")
    trigger = handlers.resolve_condition_profile("s15_trigger_break_01")

    assert base is not None
    assert base["position_tag"] == "S15_CANDID"
    assert base["is_next_day_target"] is False
    assert base["use_debounce"] is False
    assert trigger is not None
    assert trigger["position_tag"] == "S15_SHOOTING"
    assert trigger["is_next_day_target"] is False
    assert trigger["use_debounce"] is False


def test_open_reclaim_adds_target_only_within_window(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 5, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )

    handlers.handle_condition_matched({"code": "005930", "condition_name": "scalp_open_reclaim_01"})

    assert len(active_targets) == 1
    assert active_targets[0]["code"] == "005930"
    assert db.records and db.records[0].stock_code == "005930"
    assert any(topic == "COMMAND_WS_REG" for topic, _ in event_bus.events)

    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 21, 0)
    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)

    handlers.handle_condition_matched({"code": "000660", "condition_name": "scalp_open_reclaim_01"})

    assert active_targets == []
    assert db.records == []
    assert event_bus.events == []


def test_open_reclaim_skips_when_code_already_active(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = [{"code": "005930", "status": "WATCHING", "strategy": "SCALPING"}]
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 10, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: (_ for _ in ()).throw(AssertionError("duplicate path should not load basic info")),
    )

    handlers.handle_condition_matched({"code": "005930", "condition_name": "scalp_open_reclaim_01"})

    assert len(active_targets) == 1
    assert db.records == []
    assert event_bus.events == []


def test_open_reclaim_allows_same_code_when_existing_target_is_other_strategy(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = [{"code": "005930", "status": "WATCHING", "strategy": "KOSPI_ML", "position_tag": "KOSPI_BASE"}]
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 10, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )

    handlers.handle_condition_matched({"code": "005930", "condition_name": "scalp_open_reclaim_01"})

    assert len(active_targets) == 2
    assert {item["strategy"] for item in active_targets} == {"KOSPI_ML", "SCALPING"}
    assert any(item["position_tag"] == "OPEN_RECLAIM" for item in active_targets)


def test_open_reclaim_does_not_overwrite_completed_scalp_row(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 6, 0)

    completed = handlers.RecommendationHistory(
        rec_date=_FakeDateTime._fixed_now.date(),
        stock_code="005930",
        stock_name="OLD-TEST-005930",
        buy_price=60000,
        buy_qty=1,
        trade_type="SCALP",
        strategy="SCALPING",
        status="COMPLETED",
        position_tag="SCANNER",
    )
    db.records.append(completed)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )

    handlers.handle_condition_matched({"code": "005930", "condition_name": "scalp_open_reclaim_01"})

    assert len(db.records) == 2
    assert db.records[0].status == "COMPLETED"
    assert db.records[0].buy_price == 60000
    assert db.records[1].status == "WATCHING"
    assert db.records[1].position_tag == "OPEN_RECLAIM"


def test_s15_scan_base_arms_intraday_candidate_without_active_target(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    emitted = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 5, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(
        s15,
        "_log_s15_event",
        lambda stage, code, name="-", actual_order_submitted=False, **fields: emitted.append(
            {
                "stage": stage,
                "code": code,
                "name": name,
                "actual_order_submitted": actual_order_submitted,
                "fields": fields,
            }
        ),
    )

    handlers.handle_condition_matched({"code": "123456", "condition_name": "s15_scan_base_01"})

    assert active_targets == []
    assert db.records
    assert db.records[0].strategy == "S15_CANDID"
    assert db.records[0].status == "WATCHING"
    assert db.records[0].position_tag == "S15_CANDID:s15_scan_base_01"
    assert db.records[0].profit_rate == 0.0
    assert db.records[0].hard_stop_price > db.records[0].nxt
    assert "123456" in s15.FAST_SCALP_POOL
    assert emitted
    assert emitted[0]["stage"] == "s15_candidate_armed"
    assert emitted[0]["fields"]["base_condition"] == "s15_scan_base_01"
    assert emitted[0]["fields"]["ttl_sec"] == 180


def test_s15_trigger_without_arm_blocks_with_provenance(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    emitted = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 10, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(
        handlers,
        "_log_s15_event",
        lambda stage, code, name="-", actual_order_submitted=False, **fields: emitted.append(
            {
                "stage": stage,
                "code": code,
                "name": name,
                "actual_order_submitted": actual_order_submitted,
                "fields": fields,
            }
        ),
    )
    monkeypatch.setattr(
        handlers.threading,
        "Thread",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked trigger must not start thread")),
    )

    handlers.handle_condition_matched({"code": "123456", "condition_name": "s15_trigger_break_01"})

    assert [event["stage"] for event in emitted] == ["s15_trigger_received", "s15_trigger_blocked"]
    assert emitted[-1]["fields"]["s15_block_reason"] == "not_armed"
    assert active_targets == []
    assert db.records == []


def test_s15_trigger_reentry_blocked_does_not_start_thread(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    emitted = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 10, 0)
    s15.FAST_SCALP_POOL["123456"] = {
        "name": "TEST-123456",
        "armed_at": 1_000.0,
        "last_seen": 1_000.0,
        "base_condition": "s15_scan_base_01",
        "expires_at": 9_999_999_999.0,
    }
    s15.FAST_REENTRY_BLOCK["123456"] = 9_999_999_999.0

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(
        handlers,
        "_log_s15_event",
        lambda stage, code, name="-", actual_order_submitted=False, **fields: emitted.append(
            {
                "stage": stage,
                "fields": fields,
            }
        ),
    )
    monkeypatch.setattr(
        handlers.threading,
        "Thread",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked trigger must not start thread")),
    )

    handlers.handle_condition_matched({"code": "123456", "condition_name": "s15_trigger_break_01"})

    assert emitted[-1]["stage"] == "s15_trigger_blocked"
    assert emitted[-1]["fields"]["s15_block_reason"] == "reentry_blocked"


def test_s15_trigger_bypasses_general_active_target_filter_and_emits_provenance(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = [{"code": "123456", "strategy": "SCALPING", "position_tag": "SCANNER"}]
    emitted = []
    started = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 10, 0)
    s15.FAST_SCALP_POOL["123456"] = {
        "name": "TEST-123456",
        "armed_at": 1_000.0,
        "last_seen": 1_000.0,
        "base_condition": "s15_scan_base_01",
        "expires_at": 9_999_999_999.0,
    }

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(
        handlers,
        "WS_MANAGER",
        type("WS", (), {"get_latest_data": lambda self, code: {"curr": 10000}})(),
    )
    monkeypatch.setattr(
        handlers,
        "_log_s15_event",
        lambda stage, code, name="-", actual_order_submitted=False, **fields: emitted.append(
            {"stage": stage, "fields": fields}
        ),
    )

    class _DummyThread:
        def __init__(self, *args, **kwargs):
            started.append({"args": args, "kwargs": kwargs})

        def start(self):
            return None

    monkeypatch.setattr(handlers.threading, "Thread", _DummyThread)

    handlers.handle_condition_matched({"code": "123456", "condition_name": "s15_trigger_break_01"})

    assert [event["stage"] for event in emitted] == ["s15_trigger_received"]
    assert started
    assert db.records
    assert db.records[0].strategy == "S15_FAST"
    assert "123456" in s15.FAST_TRADE_STATE


def test_s15_trigger_blocks_when_same_symbol_order_or_holding_active(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = [
        {
            "code": "123456",
            "strategy": "SCALPING",
            "status": "HOLDING",
            "position_tag": "SCANNER",
        }
    ]
    emitted = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 10, 0)
    s15.FAST_SCALP_POOL["123456"] = {
        "name": "TEST-123456",
        "armed_at": 1_000.0,
        "last_seen": 1_000.0,
        "base_condition": "s15_scan_base_01",
        "expires_at": 9_999_999_999.0,
    }

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(
        handlers,
        "WS_MANAGER",
        type("WS", (), {"get_latest_data": lambda self, code: {"curr": 10000}})(),
    )
    monkeypatch.setattr(
        handlers,
        "_log_s15_event",
        lambda stage, code, name="-", actual_order_submitted=False, **fields: emitted.append(
            {"stage": stage, "fields": fields}
        ),
    )
    monkeypatch.setattr(
        handlers,
        "create_s15_shadow_record",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("active holding must not create shadow")),
    )
    monkeypatch.setattr(
        handlers.threading,
        "Thread",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("active holding must not start thread")),
    )

    handlers.handle_condition_matched({"code": "123456", "condition_name": "s15_trigger_break_01"})

    assert [event["stage"] for event in emitted] == ["s15_trigger_received", "s15_trigger_blocked"]
    assert emitted[-1]["fields"]["s15_block_reason"] == "same_symbol_active_order_or_holding"
    assert emitted[-1]["fields"]["active_target_status"] == "HOLDING"
    assert "123456" not in s15.FAST_TRADE_STATE


def test_s15_trigger_missing_price_blocks_without_shadow_or_thread(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    emitted = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 10, 0)
    s15.FAST_SCALP_POOL["123456"] = {
        "name": "TEST-123456",
        "armed_at": 1_000.0,
        "last_seen": 1_000.0,
        "base_condition": "s15_scan_base_01",
        "expires_at": 9_999_999_999.0,
    }

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(
        handlers,
        "WS_MANAGER",
        type("WS", (), {"get_latest_data": lambda self, code: {"curr": 0}})(),
    )
    monkeypatch.setattr(
        handlers,
        "_log_s15_event",
        lambda stage, code, name="-", actual_order_submitted=False, **fields: emitted.append(
            {"stage": stage, "fields": fields}
        ),
    )
    monkeypatch.setattr(
        handlers,
        "create_s15_shadow_record",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("missing price must not create shadow")),
    )
    monkeypatch.setattr(
        handlers.threading,
        "Thread",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("missing price must not start thread")),
    )

    handlers.handle_condition_matched({"code": "123456", "condition_name": "s15_trigger_break_01"})

    assert [event["stage"] for event in emitted] == ["s15_trigger_received", "s15_trigger_blocked"]
    assert emitted[-1]["fields"]["s15_block_reason"] == "missing_price"
    assert db.records == []
    assert "123456" not in s15.FAST_TRADE_STATE


def test_s15_candidate_unmatched_unarms_candidate(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 9, 5, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(s15, "_log_s15_event", lambda *args, **kwargs: None)

    handlers.handle_condition_matched({"code": "123456", "condition_name": "s15_scan_base_01"})
    assert "123456" in s15.FAST_SCALP_POOL
    assert db.records

    handlers.handle_condition_unmatched({"code": "123456", "condition_name": "s15_scan_base_01"})

    assert "123456" not in s15.FAST_SCALP_POOL
    assert db.records == []


def test_resolve_condition_profile_for_vwap_reclaim():
    profile = handlers.resolve_condition_profile("scalp_vwap_reclaim_01")

    assert profile is not None
    assert profile["start"].hour == 10 and profile["start"].minute == 0
    assert profile["end"].hour == 14 and profile["end"].minute == 0
    assert profile["position_tag"] == "VWAP_RECLAIM"
    assert profile["use_debounce"] is False


def test_vwap_reclaim_adds_target_only_when_price_is_within_vwap_band(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 10, 30, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(handlers, "_get_latest_price", lambda code: 1005)
    monkeypatch.setattr(handlers, "_get_latest_open_and_vwap", lambda code: (1000, 1000))

    handlers.handle_condition_matched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})

    assert len(active_targets) == 1
    assert active_targets[0]["position_tag"] == "VWAP_RECLAIM"
    assert db.records and db.records[0].position_tag == "VWAP_RECLAIM"
    assert any(topic == "COMMAND_WS_REG" for topic, _ in event_bus.events)


def test_vwap_reclaim_skips_when_vwap_gap_is_outside_allowed_band(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 11, 0, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: (_ for _ in ()).throw(AssertionError("precheck should skip before basic info")),
    )
    monkeypatch.setattr(handlers, "_get_latest_price", lambda code: 1015)
    monkeypatch.setattr(handlers, "_get_latest_open_and_vwap", lambda code: (1000, 1000))

    handlers.handle_condition_matched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})

    assert active_targets == []
    assert db.records == []
    assert event_bus.events == []


def test_vwap_reclaim_uses_candle_close_when_ws_curr_missing(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 10, 30, 0)

    class _DummyWS:
        def get_latest_data(self, code):
            return {"curr": 0, "open": 1000}

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(handlers, "WS_MANAGER", _DummyWS())
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda token, code, limit=120: [
            {"현재가": 1005, "거래량": 100, "시가": 1000},
            {"현재가": 1000, "거래량": 100, "시가": 1000},
        ],
    )

    handlers.handle_condition_matched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})

    assert len(active_targets) == 1
    assert active_targets[0]["position_tag"] == "VWAP_RECLAIM"
    assert db.records and db.records[0].position_tag == "VWAP_RECLAIM"
    assert any(topic == "COMMAND_WS_REG" for topic, _ in event_bus.events)


def test_vwap_reclaim_parses_signed_comma_candles_when_ws_curr_missing(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 10, 30, 0)

    class _DummyWS:
        def get_latest_data(self, code):
            return {"curr": "0", "open": "+1,000"}

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(handlers, "WS_MANAGER", _DummyWS())
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda token, code, limit=120: [
            {"현재가": "+1,005", "거래량": "+100", "시가": "+1,000"},
            {"현재가": "-1,000", "거래량": "100", "시가": "1,000"},
        ],
    )

    handlers.handle_condition_matched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})

    assert len(active_targets) == 1
    assert active_targets[0]["position_tag"] == "VWAP_RECLAIM"
    assert db.records and db.records[0].position_tag == "VWAP_RECLAIM"
    assert any(topic == "COMMAND_WS_REG" for topic, _ in event_bus.events)


def test_vwap_reclaim_missing_price_or_vwap_requests_ws_registration(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 10, 30, 0)

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: (_ for _ in ()).throw(AssertionError("precheck should skip before basic info")),
    )
    monkeypatch.setattr(handlers, "_get_latest_price", lambda code: 0)
    monkeypatch.setattr(handlers, "_get_latest_open_and_vwap", lambda code: (0, 0))

    handlers.handle_condition_matched({"code": "060250", "condition_name": "scalp_vwap_reclaim_01"})

    assert active_targets == []
    assert db.records == []
    assert event_bus.events == [
        (
            "COMMAND_WS_REG",
            {"codes": ["060250"], "source": "condition_precheck:scalp_vwap_reclaim_01"},
        )
    ]


def test_condition_unmatch_guard_keeps_unmatched_only_watching(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    emitted = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 10, 30, 0)
    now = {"ts": 1_000.0}

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(handlers.time, "time", lambda: now["ts"])
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            SCALP_CONDITION_UNMATCH_GUARD_ENABLED=True,
            SCALP_CONDITION_UNMATCH_GUARD_TAGS=("VWAP_RECLAIM", "DRYUP_SQUEEZE", "PRECLOSE"),
        ),
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(handlers, "_get_latest_price", lambda code: 1005)
    monkeypatch.setattr(handlers, "_get_latest_open_and_vwap", lambda code: (1000, 1000))
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    handlers.handle_condition_matched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})
    now["ts"] = 1_040.0
    handlers.handle_condition_unmatched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})

    assert active_targets and active_targets[0]["status"] == "WATCHING"
    assert db.records and db.records[0].status == "WATCHING"
    assert ("COMMAND_WS_UNREG", {"codes": ["035420"]}) not in event_bus.events
    assert emitted
    event = emitted[0]
    assert event["pipeline"] == "ENTRY_PIPELINE"
    assert event["stage"] == "condition_unmatch_guard"
    assert event["fields"]["condition_unmatch_guard_applied"] is True
    assert event["fields"]["condition_unmatch_guard_action"] == "pending_unmatched"
    assert event["fields"]["condition_unmatch_guard_reason"] == "unmatched_only_guard_hold"
    assert event["fields"]["condition_name"] == "scalp_vwap_reclaim_01"
    assert event["fields"]["position_tag"] == "VWAP_RECLAIM"
    assert event["fields"]["actual_order_submitted"] is False
    assert event["fields"]["broker_order_forbidden"] is True


def test_condition_unmatch_guard_still_removes_below_vwap(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    emitted = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 10, 30, 0)
    now = {"ts": 1_000.0}
    latest_price = {"value": 1005}

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(handlers.time, "time", lambda: now["ts"])
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            SCALP_CONDITION_UNMATCH_GUARD_ENABLED=True,
            SCALP_CONDITION_UNMATCH_GUARD_TAGS=("VWAP_RECLAIM", "DRYUP_SQUEEZE", "PRECLOSE"),
        ),
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(handlers, "_get_latest_price", lambda code: latest_price["value"])
    monkeypatch.setattr(handlers, "_get_latest_open_and_vwap", lambda code: (1000, 1000))
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    handlers.handle_condition_matched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})
    now["ts"] = 1_040.0
    latest_price["value"] = 990
    handlers.handle_condition_unmatched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})

    assert active_targets == []
    assert db.records and db.records[0].status == "EXPIRED"
    assert ("COMMAND_WS_UNREG", {"codes": ["035420"]}) in event_bus.events
    assert emitted
    event = emitted[-1]
    assert event["pipeline"] == "ENTRY_PIPELINE"
    assert event["stage"] == "condition_unmatch_guard"
    assert event["fields"]["condition_unmatch_guard_action"] == "removed"
    assert event["fields"]["condition_unmatch_guard_reason"] == "below_open"
    assert event["fields"]["condition_name"] == "scalp_vwap_reclaim_01"
    assert event["fields"]["actual_order_submitted"] is False
    assert event["fields"]["broker_order_forbidden"] is True


def test_condition_unmatch_guard_state_missing_still_removes_price_damage(monkeypatch):
    db = _DummyDB()
    event_bus = _DummyEventBus()
    active_targets = []
    emitted = []
    _bind_test_deps(active_targets, db, event_bus)
    _FakeDateTime._fixed_now = datetime(2026, 4, 4, 10, 30, 0)
    now = {"ts": 1_000.0}
    latest_price = {"value": 1005}

    monkeypatch.setattr(handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(handlers.time, "time", lambda: now["ts"])
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            SCALP_CONDITION_UNMATCH_GUARD_ENABLED=True,
            SCALP_CONDITION_UNMATCH_GUARD_TAGS=("VWAP_RECLAIM", "DRYUP_SQUEEZE", "PRECLOSE"),
        ),
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_basic_info_ka10001",
        lambda token, code: {"Name": f"TEST-{code}"},
    )
    monkeypatch.setattr(handlers, "_get_latest_price", lambda code: latest_price["value"])
    monkeypatch.setattr(handlers, "_get_latest_open_and_vwap", lambda code: (1000, 1000))
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    handlers.handle_condition_matched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})
    handlers._CONDITION_STATE.clear()
    now["ts"] = 1_040.0
    latest_price["value"] = 990
    handlers.handle_condition_unmatched({"code": "035420", "condition_name": "scalp_vwap_reclaim_01"})

    assert active_targets == []
    assert db.records and db.records[0].status == "EXPIRED"
    assert ("COMMAND_WS_UNREG", {"codes": ["035420"]}) in event_bus.events
    assert emitted
    event = emitted[-1]
    assert event["stage"] == "condition_unmatch_guard"
    assert event["fields"]["condition_unmatch_guard_action"] == "removed"
    assert event["fields"]["condition_unmatch_guard_reason"] == "below_open"


def test_resolve_condition_profile_for_dryup_squeeze():
    profile = handlers.resolve_condition_profile("scalp_dryup_squeeze_01")

    assert profile is not None
    assert profile["start"].hour == 9 and profile["start"].minute == 30
    assert profile["end"].hour == 13 and profile["end"].minute == 30
    assert profile["position_tag"] == "DRYUP_SQUEEZE"
    assert profile["use_debounce"] is False


def test_resolve_condition_profile_for_preclose():
    profile = handlers.resolve_condition_profile("scalp_preclose_01")

    assert profile is not None
    assert profile["start"].hour == 14 and profile["start"].minute == 30
    assert profile["end"].hour == 15 and profile["end"].minute == 20
    assert profile["position_tag"] == "PRECLOSE"
    assert profile["use_debounce"] is False
