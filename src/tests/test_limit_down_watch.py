import json
import threading
from datetime import date
from types import SimpleNamespace

import pandas as pd

from src.engine.monitoring import limit_down_watch_report
from src.engine import kiwoom_websocket
from src.engine.scalping import limit_down_watch
from src.engine.scalping.limit_down_watch import (
    LIMIT_DOWN_OBSERVATION_REGISTRY,
    LimitDownCandidate,
    LimitDownWatchManager,
    build_candidate_source,
    price_band,
)
from src.engine.signal_radar import SniperRadar
from src.scanners import scalping_scanner
from src.utils import kiwoom_utils


class _Bus:
    def __init__(self, on_publish=None):
        self.events = []
        self.on_publish = on_publish

    def publish(self, name, payload):
        self.events.append((name, payload))
        if self.on_publish is not None:
            self.on_publish(name, payload)


class _Session:
    def __init__(self, records):
        self.records = records

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def add(self, record):
        self.records.append(record)

    def flush(self):
        return None


class _DB:
    def __init__(self):
        self.records = []

    def get_session(self):
        return _Session(self.records)

    def find_reusable_watching_record(self, _session, **_kwargs):
        return None


def _candidate(code="000001", count=2):
    return LimitDownCandidate(
        code=code,
        name=code,
        source_trade_date="2026-07-24",
        limit_down_close=4_000,
        consecutive_count=count,
        cohort=("consecutive_limit_down_2plus" if count >= 2 else "single_limit_down"),
        price_band="1000_4999",
        volume=100_000,
    )


def test_ka10017_previous_limit_down_request_and_parser(monkeypatch):
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return (
            [
                {
                    "updown_pric": [
                        {
                            "stk_cd": "A000001",
                            "stk_nm": "테스트",
                            "cur_prc": "-4,000",
                            "flu_rt": "-29.98",
                            "trde_qty": "10,000",
                            "cnt": "2",
                        }
                    ]
                }
            ],
            {"page_count": 1},
        )

    monkeypatch.setattr(
        kiwoom_utils, "_fetch_kiwoom_api_continuous_with_meta", fake_fetch
    )
    rows, meta = kiwoom_utils.get_previous_limit_down_stocks_ka10017("token")

    assert captured["api_id"] == "ka10017"
    assert captured["payload"]["updown_tp"] == "7"
    assert captured["payload"]["trde_qty_tp"] == "00000"
    assert captured["use_continuous"] is True
    assert rows[0]["Code"] == "000001"
    assert rows[0]["CurrentPrice"] == 4000
    assert rows[0]["ConsecutiveCountRaw"] == "2"
    assert meta["official_upstream_commit"].startswith("1504d45f")


def test_price_band_boundaries():
    assert price_band(999) == "under_1000"
    assert price_band(1000) == "1000_4999"
    assert price_band(5000) == "5000_9999"
    assert price_band(10_000) == "10000_29999"
    assert price_band(30_000) == "30000_plus"


def test_candidate_source_prioritizes_two_plus_and_blocks_bad_rows(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(limit_down_watch, "CANDIDATE_DIR", tmp_path)
    index = pd.to_datetime(["2026-07-24", "2026-07-27"])
    daily = pd.DataFrame({"Close": [4000, 3900]}, index=index)

    def fetch_previous(_token):
        return (
            [
                {
                    "Code": "000010",
                    "Name": "연속",
                    "ConsecutiveCountRaw": "2",
                    "Volume": 10,
                },
                {
                    "Code": "000020",
                    "Name": "단일",
                    "ConsecutiveCountRaw": "1",
                    "Volume": 20,
                },
                {
                    "Code": "000030",
                    "Name": "결함",
                    "ConsecutiveCountRaw": "",
                    "Volume": 30,
                },
            ],
            {"api_id": "ka10017"},
        )

    candidates, artifact = build_candidate_source(
        "token",
        object(),
        target_date=date(2026, 7, 27),
        fetch_previous=fetch_previous,
        fetch_daily=lambda _token, _code: daily,
        db_close_loader=lambda _db, _code, _date: (4000, "DB이름"),
        latest_completed_date_loader=lambda _db, _target_date: date(2026, 7, 24),
    )

    assert [item.code for item in candidates] == ["000010", "000020"]
    assert candidates[0].cohort == "consecutive_limit_down_2plus"
    assert candidates[1].cohort == "single_limit_down"
    assert artifact["status"] == "partial"
    assert artifact["blocked_rows"] == [
        {"code": "000030", "reason": "invalid_consecutive_count"}
    ]
    assert artifact["runtime_effect"] is False
    assert artifact["broker_order_forbidden"] is True


def test_candidate_source_close_mismatch_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(limit_down_watch, "CANDIDATE_DIR", tmp_path)
    daily = pd.DataFrame({"Close": [4000]}, index=pd.to_datetime(["2026-07-24"]))
    candidates, artifact = build_candidate_source(
        "token",
        object(),
        target_date=date(2026, 7, 27),
        fetch_previous=lambda _token: (
            [
                {
                    "Code": "000010",
                    "Name": "불일치",
                    "ConsecutiveCountRaw": "1",
                }
            ],
            {},
        ),
        fetch_daily=lambda _token, _code: daily,
        db_close_loader=lambda _db, _code, _date: (3995, "불일치"),
        latest_completed_date_loader=lambda _db, _target_date: date(2026, 7, 24),
    )
    assert candidates == []
    assert artifact["status"] == "blocked"
    assert artifact["blocked_rows"][0]["reason"] == "ka10081_db_close_mismatch"


def test_candidate_source_stale_completed_date_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(limit_down_watch, "CANDIDATE_DIR", tmp_path)
    daily = pd.DataFrame({"Close": [4000]}, index=pd.to_datetime(["2026-07-23"]))
    candidates, artifact = build_candidate_source(
        "token",
        object(),
        target_date=date(2026, 7, 27),
        fetch_previous=lambda _token: (
            [
                {
                    "Code": "000010",
                    "Name": "오래된일봉",
                    "ConsecutiveCountRaw": "1",
                }
            ],
            {},
        ),
        fetch_daily=lambda _token, _code: daily,
        db_close_loader=lambda _db, _code, _date: (4000, "오래된일봉"),
        latest_completed_date_loader=lambda _db, _target_date: date(2026, 7, 24),
    )
    assert candidates == []
    assert artifact["status"] == "blocked"
    assert artifact["blocked_rows"][0] == {
        "code": "000010",
        "reason": "completed_daily_date_stale_or_mismatch",
        "source_trade_date": "2026-07-23",
        "expected_source_trade_date": "2026-07-24",
    }


def test_raw_tick_state_preserves_locked_unlock_relock_order(monkeypatch, tmp_path):
    monkeypatch.setattr(limit_down_watch, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(limit_down_watch, "emit_pipeline_event", lambda *a, **k: None)
    monkeypatch.setenv("KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED", "true")
    manager = LimitDownWatchManager("token", object(), _Bus())
    manager.active = _candidate()
    manager.state = {
        "phase": "WAITING_FIRST_TICK",
        "registered_epoch": 1.0,
        "last_transition_epoch": 1.0,
        "lower_limit_price": 2800,
        "unlock_count": 0,
        "relock_count": 0,
        "transition_count": 0,
    }

    manager.on_raw_tick("000001", {"curr": 2800, "open": 2800}, 10.0)
    assert manager.state["phase"] == "LIMIT_LOCKED"
    manager.on_raw_tick(
        "000001",
        {
            "curr": 3000,
            "high": 3050,
            "cum_trade_value": 1_000_000,
            "orderbook": {
                "asks": [{"price": 3010}],
                "bids": [{"price": 3000}],
            },
            "last_ws_item": "000001_AL",
            "last_ws_market_route": "krx_nxt_integrated",
        },
        11.0,
    )
    assert manager.state["phase"] == "UNLOCKED"
    manager.on_raw_tick("000001", {"curr": 2800, "low": 2800}, 12.0)
    assert manager.state["phase"] == "RELOCKED"
    assert manager.state["unlock_count"] == 1
    assert manager.state["relock_count"] == 1
    assert manager.state["first_unlock_epoch"] == 11.0
    assert manager.state["first_relock_epoch"] == 12.0
    assert manager.state["trade_value"] == 1_000_000
    assert manager.state["actual_ws_item_count"] == 1
    assert manager.state["actual_ws_route"] == "krx_nxt_integrated"
    assert manager.state["vi_triggered"] is None

    # An older/coalesced duplicate cannot rewind ordered state.
    manager.on_raw_tick("000001", {"curr": 3200}, 11.5)
    assert manager.state["phase"] == "RELOCKED"
    assert manager.state["current_price"] == 2800


def test_ws_raw_sink_receives_every_tick_before_latest_tick_coalescing(monkeypatch):
    observed = []
    monkeypatch.setattr(
        kiwoom_websocket,
        "observe_raw_tick",
        lambda code, data, _epoch: observed.append((code, data["curr"])),
    )
    manager = kiwoom_websocket.KiwoomWSManager.__new__(kiwoom_websocket.KiwoomWSManager)
    manager._stop_event = threading.Event()
    manager._tick_lock = threading.Lock()
    manager._pending_tick_events = {}
    manager._tick_dispatch_event = threading.Event()

    manager._queue_tick_event("000010", {"curr": 2800})
    manager._queue_tick_event("000010", {"curr": 2900}, realtime_type="0D")
    manager._queue_tick_event("000010", {"curr": 3000})

    assert observed == [("000010", 2800), ("000010", 3000)]
    assert manager._pending_tick_events["000010"]["data"]["curr"] == 3000


def test_normal_scanner_handoff_keeps_ws_and_clears_observation_registry(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(limit_down_watch, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(limit_down_watch, "emit_pipeline_event", lambda *a, **k: None)
    monkeypatch.setattr(
        kiwoom_utils,
        "get_basic_info_ka10001",
        lambda _token, _code: {"LowerLimitPrice": 2800},
    )
    monkeypatch.setenv("KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED", "true")
    bus = _Bus()
    manager = LimitDownWatchManager("token", object(), bus)
    manager.candidates = [_candidate()]
    manager.loaded_date = date.fromtimestamp(1000.0).isoformat()

    manager.reconcile(active_codes=set(), now_epoch=1000.0)
    assert LIMIT_DOWN_OBSERVATION_REGISTRY.active_code() == "000001"
    assert [name for name, _payload in bus.events] == ["COMMAND_WS_REG"]

    manager.reconcile(active_codes=set(), now_epoch=1020.0)
    assert [name for name, _payload in bus.events] == [
        "COMMAND_WS_REG",
        "COMMAND_WS_REG",
    ]
    assert bus.events[-1][1]["reason"] == "first_tick_pending"

    assert manager.relinquish_for_trading("000001") is True
    assert LIMIT_DOWN_OBSERVATION_REGISTRY.active_code() == ""
    assert [name for name, _payload in bus.events] == [
        "COMMAND_WS_REG",
        "COMMAND_WS_REG",
    ]
    assert manager.last_release["reason"] == "normal_scanner_claimed"
    assert manager.last_release["keep_ws"] is True


def test_scanner_promotion_handoff_blocks_signal_until_attach_event(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(limit_down_watch, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(limit_down_watch, "emit_pipeline_event", lambda *a, **k: None)
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *a, **k: True)
    monkeypatch.setattr(
        scalping_scanner, "_scanner_candidate_pre_filter_reason", lambda _target: ""
    )
    monkeypatch.setattr(
        scalping_scanner, "_should_promote_candidate", lambda *a, **k: True
    )
    monkeypatch.setattr(
        scalping_scanner,
        "_scanner_real_source_guard_decision",
        lambda *a, **k: {"blocked": False},
    )
    monkeypatch.setattr(
        scalping_scanner,
        "_scanner_candidate_identity_decision",
        lambda *a, **k: {"blocked": False},
    )
    monkeypatch.setattr(
        scalping_scanner,
        "TRADING_RULES",
        SimpleNamespace(SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED=False),
    )
    monkeypatch.setenv("KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "16")

    attach_observed = []

    def on_publish(name, _payload):
        if name == "SCALPING_SCANNER_PROMOTED_TARGET":
            attach_observed.append(
                LIMIT_DOWN_OBSERVATION_REGISTRY.active_code() == "000010"
            )

    bus = _Bus(on_publish=on_publish)
    db = _DB()
    manager = LimitDownWatchManager("token", db, bus)
    manager.active = _candidate(code="000010")
    manager.state = {
        "phase": "UNLOCKED",
        "registered_epoch": 900.0,
        "last_transition_epoch": 900.0,
    }
    LIMIT_DOWN_OBSERVATION_REGISTRY.activate("000010", manager.on_raw_tick)
    target = {
        "Code": "000010",
        "Name": "정상인수",
        "Price": 3000,
        "FluRate": 2.0,
        "CntrStr": 120.0,
        "Source": "PRICE_JUMP_START",
        "SourceSet": {"PRICE_JUMP_START"},
        "PriorityScore": 10.0,
        "SpikeRate": 5.0,
        "TradeValue": 100_000_000,
        "RankNow": 1,
        "RankPrev": 2,
    }
    try:
        codes, _recent = scalping_scanner.promote_candidates(
            db,
            bus,
            [target],
            {},
            max_new_codes=12,
            reentry_cooldown_sec=1500,
            token="token",
            now_ts=1000.0,
            limit_down_manager=manager,
        )
        assert codes == ["000010"]
        assert attach_observed == [True]
        assert LIMIT_DOWN_OBSERVATION_REGISTRY.active_code() == ""
        assert not any(name == "COMMAND_WS_UNREG" for name, _ in bus.events)
    finally:
        LIMIT_DOWN_OBSERVATION_REGISTRY.release("000010")


def test_observation_registry_suppresses_trade_signal():
    LIMIT_DOWN_OBSERVATION_REGISTRY.activate("000001", lambda *_args: None)
    try:
        radar = SniperRadar.__new__(SniperRadar)
        radar.calculate_market_leader_score = lambda _data: (_ for _ in ()).throw(
            AssertionError("observation-only tick reached signal analysis")
        )
        radar._on_realtime_tick({"code": "000001", "data": {"curr": 3000}})
    finally:
        LIMIT_DOWN_OBSERVATION_REGISTRY.release("000001")


def test_postclose_report_groups_ordered_intraday_path(tmp_path):
    event_path = tmp_path / "events.jsonl"
    rows = [
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_registered",
            "stock_code": "000001",
            "fields": {},
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_state_transition",
            "stock_code": "000001",
            "fields": {"phase": "UNLOCKED"},
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_state_transition",
            "stock_code": "000001",
            "fields": {"phase": "RELOCKED"},
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_snapshot",
            "stock_code": "000001",
            "fields": {
                "cohort": "consecutive_limit_down_2plus",
                "price_band": "1000_4999",
                "low_to_high_range_pct": "20.0",
                "high_vs_limit_down_close_pct": "25.0",
                "low_vs_limit_down_close_pct": "-5.0",
            },
        },
    ]
    event_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )
    report = limit_down_watch_report.build_report("2026-07-27", event_path=event_path)
    group = report["groups"][0]
    assert report["status"] == "pass"
    assert group["unlock_rate_pct"] == 100.0
    assert group["relock_rate_pct"] == 100.0
    assert group["ordered_intraday_path_capture_rate"] == 100.0
    assert group["avg_high_vs_limit_down_close_pct"] == 25.0
    assert group["avg_low_vs_limit_down_close_pct"] == -5.0
    assert report["actual_order_submitted"] is False
