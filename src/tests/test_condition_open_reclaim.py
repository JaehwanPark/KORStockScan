from datetime import datetime

import src.engine.sniper_condition_handlers as handlers


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

    def find_reusable_watching_record(self, session, *, rec_date, stock_code, strategy=None):
        for record in reversed(session.records):
            if getattr(record, "rec_date", None) != rec_date:
                continue
            if getattr(record, "stock_code", None) != stock_code:
                continue
            if strategy is not None and getattr(record, "strategy", None) != strategy:
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
