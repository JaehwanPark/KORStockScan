import json
import threading
import time
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from src.engine.monitoring import limit_down_watch_report, limit_down_watch_research
from src.engine import kiwoom_websocket, sniper_state_handlers
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


def _observation_event_fields(**fields):
    return {
        "decision_authority": "limit_down_source_observation_only",
        "runtime_effect": "False",
        "actual_order_submitted": "False",
        "broker_order_forbidden": "True",
        **fields,
    }


def _candidate_source_payload(*candidates):
    return {
        "schema_version": 1,
        "report_type": "limit_down_watch_candidate_source",
        "target_date": "2026-07-27",
        "status": "pass",
        "candidate_count": len(candidates),
        "candidates": list(candidates),
        "decision_authority": "limit_down_source_observation_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_signal_radar_fallback_resolves_registered_token_before_request(
    monkeypatch, tmp_path
):
    monkeypatch.setenv(
        "KIWOOM_TOKEN_CACHE_PATH", str(tmp_path / "kiwoom_token_cache.json")
    )
    monkeypatch.setattr(
        "src.engine.signal_radar.fdr.DataReader",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("fdr down")),
    )
    posts = []

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {"rows": [{"cur_prc": str(100 + index)} for index in range(20)]}

    monkeypatch.setattr(
        "src.engine.signal_radar.requests.post",
        lambda *args, **kwargs: posts.append(dict(kwargs.get("headers") or {}))
        or Response(),
    )
    kiwoom_utils.register_kiwoom_token_replacement(
        "STARTUP_TOKEN", "FRESH_TOKEN", source="test"
    )

    SniperRadar("STARTUP_TOKEN").get_market_regime("STARTUP_TOKEN")

    assert posts[0]["authorization"] == "Bearer FRESH_TOKEN"


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
    assert meta["source_label"] == "previous_limit_down"
    assert meta["official_upstream_commit"].startswith("69642586")
    assert meta["official_reference_verified_at"].startswith("2026-08-14T")


def test_ka10099_near_candidate_eligibility_is_fail_closed(monkeypatch):
    def fake_fetch(**kwargs):
        if kwargs["payload"]["mrkt_tp"] == "0":
            return [
                {
                    "list": [
                        {
                            "code": "000010",
                            "auditInfo": "정상",
                            "state": "정상",
                            "orderWarning": "0",
                            "marketCode": "0",
                        },
                        {
                            "code": "000020",
                            "auditInfo": "투자주의환기종목",
                            "state": "관리종목",
                            "orderWarning": "4",
                            "marketCode": "0",
                        },
                    ]
                }
            ]
        return []

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows, meta = kiwoom_utils.get_stock_eligibility_map_ka10099(
        "token", ["000010", "000020", "000030"]
    )

    assert rows["000010"]["eligible"] is True
    assert rows["000020"]["eligible"] is False
    assert "audit_info_excluded" in rows["000020"]["blocked_reasons"]
    assert meta["status"] == "partial"
    assert meta["missing_codes"] == ["000030"]
    assert meta["official_upstream_commit"].startswith("69642586")


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


def test_candidate_source_ignores_nat_daily_index_rows(monkeypatch, tmp_path):
    monkeypatch.setattr(limit_down_watch, "CANDIDATE_DIR", tmp_path)
    daily = pd.DataFrame(
        {"Close": [0, 4000]},
        index=pd.DatetimeIndex([pd.NaT, pd.Timestamp("2026-07-24")]),
    )
    candidates, artifact = build_candidate_source(
        "token",
        object(),
        target_date=date(2026, 7, 27),
        fetch_previous=lambda _token: (
            [
                {
                    "Code": "000010",
                    "Name": "유효일봉",
                    "ConsecutiveCountRaw": "2",
                }
            ],
            {},
        ),
        fetch_daily=lambda _token, _code: daily,
        db_close_loader=lambda _db, _code, _date: (4000, "유효일봉"),
        latest_completed_date_loader=lambda _db, _target_date: date(2026, 7, 24),
    )

    assert [candidate.code for candidate in candidates] == ["000010"]
    assert artifact["status"] == "pass"


def test_candidate_source_blocks_when_daily_index_has_no_valid_date(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(limit_down_watch, "CANDIDATE_DIR", tmp_path)
    daily = pd.DataFrame({"Close": [0]}, index=pd.DatetimeIndex([pd.NaT]))
    candidates, artifact = build_candidate_source(
        "token",
        object(),
        target_date=date(2026, 7, 27),
        fetch_previous=lambda _token: (
            [
                {
                    "Code": "000010",
                    "Name": "무효일봉",
                    "ConsecutiveCountRaw": "1",
                }
            ],
            {},
        ),
        fetch_daily=lambda _token, _code: daily,
        db_close_loader=lambda _db, _code, _date: (0, ""),
        latest_completed_date_loader=lambda _db, _target_date: date(2026, 7, 24),
    )

    assert candidates == []
    assert artifact["status"] == "blocked"
    assert artifact["blocked_rows"] == [
        {"code": "000010", "reason": "ka10081_no_valid_completed_dates"}
    ]


def test_exact_empty_source_uses_verified_near_limit_rebound_fallback(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(limit_down_watch, "CANDIDATE_DIR", tmp_path)
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *a, **k: True)
    daily = pd.DataFrame(
        {
            "Low": [10_000, 7_200],
            "Close": [10_000, 7_600],
        },
        index=pd.to_datetime(["2026-08-03", "2026-08-04"]),
    )

    candidates, artifact = build_candidate_source(
        "token",
        object(),
        target_date=date(2026, 8, 5),
        fetch_previous=lambda _token: ([], {"api_id": "ka10017"}),
        fetch_daily=lambda _token, _code: daily,
        db_close_loader=lambda _db, _code, _date: (7600, "근접반등"),
        latest_completed_date_loader=lambda _db, _target_date: date(2026, 8, 4),
        near_limit_loader=lambda _db, _target_date: (
            [
                {
                    "Code": "000010",
                    "Name": "근접반등",
                    "SourceTradeDate": "2026-08-04",
                    "Low": 7200,
                    "Close": 7600,
                    "PreviousClose": 10_000,
                    "Volume": 123_000,
                }
            ],
            {"status": "pass", "source_row_count": 2635},
        ),
        near_eligibility_loader=lambda _token, _codes: (
            {
                "000010": {
                    "eligible": True,
                    "audit_info": "정상",
                    "state": "정상",
                    "order_warning": "0",
                    "blocked_reasons": [],
                }
            },
            {"status": "pass", "api_id": "ka10099"},
        ),
    )

    assert [candidate.code for candidate in candidates] == ["000010"]
    candidate = candidates[0]
    assert candidate.cohort == "near_limit_rebound"
    assert candidate.candidate_kind == "near_limit_rebound"
    assert candidate.consecutive_count == 0
    assert candidate.trigger_low_change_pct == -28.0
    assert candidate.close_recovery_from_low_pct == 5.555556
    assert artifact["status"] == "pass"
    assert artifact["candidate_source_mode"] == (
        "exact_empty_near_limit_rebound_fallback"
    )


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
    assert manager.state["unlock_confirmed_epoch"] == 0.0
    assert manager.state["trade_value"] == 1_000_000
    assert manager.state["actual_ws_item_count"] == 1
    assert manager.state["actual_ws_route"] == "krx_nxt_integrated"
    assert manager.state["vi_triggered"] is None

    # An older/coalesced duplicate cannot rewind ordered state.
    manager.on_raw_tick("000001", {"curr": 3200}, 11.5)
    assert manager.state["phase"] == "RELOCKED"
    assert manager.state["current_price"] == 2800


def test_raw_tick_emits_source_only_unlock_confirmation_after_second_tick(
    monkeypatch, tmp_path
):
    emitted = []
    monkeypatch.setattr(limit_down_watch, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(
        limit_down_watch,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    manager = LimitDownWatchManager("token", object(), _Bus())
    manager.active = _candidate()
    manager.state = {
        "phase": "LIMIT_LOCKED",
        "registered_epoch": 1.0,
        "last_transition_epoch": 1.0,
        "lower_limit_price": 2800,
        "unlock_count": 0,
        "relock_count": 0,
        "transition_count": 0,
        "consecutive_unlocked_tick_count": 0,
        "unlock_confirmed_epoch": 0.0,
    }

    manager.on_raw_tick("000001", {"curr": 2900}, 10.0)
    manager.on_raw_tick(
        "000001",
        {"curr": 2910, "best_ask": 2920, "best_bid": 2910},
        11.0,
    )

    confirmations = [
        kwargs["fields"]
        for args, kwargs in emitted
        if len(args) >= 4 and args[3] == "limit_down_watch_unlock_confirmed"
    ]
    assert len(confirmations) == 1
    assert confirmations[0]["confirmation_tick_count"] == 2
    assert confirmations[0]["current_price"] == 2910
    assert confirmations[0]["actual_order_submitted"] is False
    assert confirmations[0]["broker_order_forbidden"] is True
    assert manager.state["unlock_confirmed_epoch"] == 11.0


def test_raw_tick_confirms_near_rebound_only_after_two_qualifying_ticks(
    monkeypatch, tmp_path
):
    emitted = []
    monkeypatch.setattr(limit_down_watch, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(
        limit_down_watch,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    manager = LimitDownWatchManager("token", object(), _Bus())
    base = _candidate(count=1)
    manager.active = LimitDownCandidate(
        **{
            **base.__dict__,
            "consecutive_count": 0,
            "cohort": "near_limit_rebound",
            "candidate_kind": "near_limit_rebound",
        }
    )
    manager.state = {
        "phase": "WAITING_FIRST_TRADE",
        "registered_epoch": 1.0,
        "last_transition_epoch": 1.0,
        "lower_limit_price": 0,
        "consecutive_rebound_tick_count": 0,
        "rebound_confirmed_epoch": 0.0,
    }

    manager.on_raw_tick("000001", {"curr": 2990, "open": 3000, "low": 2950}, 10.0)
    assert manager.state["rebound_confirmed_epoch"] == 0.0
    manager.on_raw_tick("000001", {"curr": 3000, "open": 3000, "low": 2950}, 11.0)
    manager.on_raw_tick(
        "000001",
        {
            "curr": 3020,
            "open": 3000,
            "low": 2950,
            "best_ask": 3030,
            "best_bid": 3020,
        },
        12.0,
    )

    confirmations = [
        kwargs["fields"]
        for args, kwargs in emitted
        if len(args) >= 4 and args[3] == "limit_down_watch_rebound_confirmed"
    ]
    assert len(confirmations) == 1
    assert confirmations[0]["confirmation_tick_count"] == 2
    assert confirmations[0]["rebound_from_low_pct"] > 1.0
    assert manager.state["rebound_confirmed_epoch"] == 12.0


def test_raw_0d_quote_is_observed_without_fabricating_trade_or_unlock(
    monkeypatch, tmp_path
):
    emitted = []
    monkeypatch.setattr(limit_down_watch, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(
        limit_down_watch,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    manager = LimitDownWatchManager("token", object(), _Bus())
    manager.active = _candidate()
    manager.state = {
        "phase": "WAITING_FIRST_TICK",
        "registered_epoch": 1.0,
        "lower_limit_price": 2800,
    }

    manager.on_raw_tick(
        "000001",
        {
            "_limit_down_realtime_type": "0D",
            "orderbook": {
                "asks": [{"price": 2800}],
                "bids": [{"price": 2795}],
            },
            "last_ws_item": "000001",
            "last_ws_market_route": "krx_regular",
        },
        10.0,
    )

    assert manager.state["phase"] == "WAITING_FIRST_TICK"
    assert manager.state["quote_count"] == 1
    assert manager.state.get("tick_count", 0) == 0
    assert manager.state["first_market_data_epoch"] == 10.0
    assert manager.state["best_ask"] == 2800
    assert manager.state["best_bid"] == 2795
    stages = [args[3] for args, _kwargs in emitted if len(args) >= 4]
    assert "limit_down_watch_quote_observed" in stages
    assert "limit_down_watch_quote_snapshot" in stages
    assert "limit_down_watch_unlock_confirmed" not in stages


def test_near_limit_rebound_creates_live_target_after_verified_rebound():
    manager = LimitDownWatchManager("token", _DB(), _Bus())
    base = _candidate(count=1)
    manager.active = LimitDownCandidate(
        **{
            **base.__dict__,
            "consecutive_count": 0,
            "cohort": "near_limit_rebound",
            "candidate_kind": "near_limit_rebound",
        }
    )
    key = "near_limit_rebound|1000_4999"
    manager.active_live_policy_keys = {key}
    manager.live_policy_by_key = {key: {"sample_count": 1}}
    manager.live_policy_source_date = "2026-08-04"
    manager.live_policy_max_entry_spread_pct = 1.5
    manager.state = {
        "phase": "NEAR_REBOUND_OBSERVING",
        "consecutive_rebound_tick_count": 2,
        "rebound_confirmed_epoch": 99.0,
        "last_tick_epoch": 100.0,
        "current_price": 3030,
        "open_price": 3000,
        "low_price": 2950,
        "lower_limit_price": 0,
        "best_ask": 3040,
        "best_bid": 3030,
    }

    target = manager.live_promotion_target(now_epoch=101.0)

    assert target is not None
    assert target["LimitDownLiveTriggerType"] == "near_rebound"
    assert target["LimitDownUnlockConfirmed"] is False
    assert target["LimitDownReboundConfirmed"] is True
    assert target["LimitDownReboundFromLowPct"] > 1.0


def test_ws_raw_sink_receives_every_tick_before_latest_tick_coalescing(monkeypatch):
    observed = []
    monkeypatch.setattr(
        kiwoom_websocket,
        "observe_raw_market_data",
        lambda code, data, _epoch, *, realtime_type: observed.append(
            (code, data["curr"], realtime_type)
        ),
    )
    manager = kiwoom_websocket.KiwoomWSManager.__new__(kiwoom_websocket.KiwoomWSManager)
    manager._stop_event = threading.Event()
    manager.lock = threading.Lock()
    manager._tick_lock = threading.Lock()
    manager._pending_tick_events = {}
    manager._tick_dispatch_event = threading.Event()
    manager._micro_reversion_forward_collector = None
    manager._micro_reversion_observation_only_codes = set()

    manager._queue_tick_event("000010", {"curr": 2800})
    manager._queue_tick_event("000010", {"curr": 2900}, realtime_type="0D")
    manager._queue_tick_event("000010", {"curr": 3000})

    assert observed == [
        ("000010", 2800, "0B"),
        ("000010", 2900, "0D"),
        ("000010", 3000, "0B"),
    ]
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
    monkeypatch.setattr(limit_down_watch, "_krx_session_phase", lambda _epoch: "OPEN")
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
    assert bus.events[-1][1]["reason"] == "first_market_data_pending"
    assert bus.events[-1][1]["required_realtime_types"] == ("0D",)

    assert manager.relinquish_for_trading("000001") is True
    assert LIMIT_DOWN_OBSERVATION_REGISTRY.active_code() == ""
    assert [name for name, _payload in bus.events] == [
        "COMMAND_WS_REG",
        "COMMAND_WS_REG",
    ]
    assert manager.last_release["reason"] == "normal_scanner_claimed"
    assert manager.last_release["keep_ws"] is True


def test_preopen_wait_persists_idle_heartbeat_and_starts_at_krx_open(
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
    preopen = datetime(2026, 8, 5, 8, 30).timestamp()
    market_open = datetime(2026, 8, 5, 9, 0).timestamp()
    manager.loaded_date = "2026-08-05"

    manager.reconcile(now_epoch=preopen)

    assert manager.active is None
    assert bus.events == []
    state = json.loads(next(tmp_path.glob("limit_down_watch_state_*.json")).read_text())
    assert state["enabled"] is True
    assert state["active_slot_count"] == 0
    assert state["active_candidate"] is None

    manager.reconcile(now_epoch=market_open)

    assert manager.active is not None
    assert bus.events[0][0] == "COMMAND_WS_REG"
    assert bus.events[0][1]["required_realtime_types"] == ("0D",)


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


def test_rotation_pays_unseen_candidate_coverage_debt_before_reexploitation():
    manager = LimitDownWatchManager("token", _DB(), _Bus())
    first = _candidate(code="000011", count=2)
    second = _candidate(code="000012", count=2)
    single = _candidate(code="000013", count=1)
    manager.candidates = [first, second, single]
    manager.activity = {
        first.code: {
            "visit_count": 1,
            "unlock_count": 3,
            "tick_count": 100,
            "trade_value": 1_000_000_000,
            "last_tick_epoch": 990.0,
        },
        second.code: {"visit_count": 1},
    }
    manager.cell_visit_counts = {
        "consecutive_limit_down_2plus|1000_4999": 2,
    }

    picked = manager._pick(set(), 1000.0)

    assert picked is single


def test_runtime_loads_latest_prior_source_only_sim_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(limit_down_watch, "SIM_POLICY_DIR", tmp_path)
    path = tmp_path / "limit_down_watch_sim_policy_catalog_2026-08-02.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "limit_down_watch_sim_policy_catalog",
                "target_date": "2026-08-02",
                "status": "pass",
                "allowed_sim_apply": True,
                "active_policy_count": 1,
                "active_policies": [
                    {
                        "policy_key": "single_limit_down|1000_4999",
                        "cohort": "single_limit_down",
                        "price_band": "1000_4999",
                    }
                ],
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "allowed_runtime_apply": False,
            }
        ),
        encoding="utf-8",
    )
    manager = LimitDownWatchManager("token", _DB(), _Bus())

    manager._load_sim_policy(date(2026, 8, 3))

    assert manager.active_sim_policy_keys == {"single_limit_down|1000_4999"}
    assert manager.sim_policy_source_date == "2026-08-02"


def test_runtime_loads_latest_prior_live_auto_policy(monkeypatch, tmp_path):
    monkeypatch.setattr(limit_down_watch, "LIVE_AUTO_POLICY_DIR", tmp_path)
    path = tmp_path / "limit_down_watch_bounded_live_candidate_2026-08-02.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "limit_down_watch_bounded_live_candidate",
                "target_date": "2026-08-02",
                "status": "live_auto_apply_ready",
                "decision_authority": "limit_down_live_auto_eligibility_candidate",
                "operator_approval_required": False,
                "preopen_consumer_implemented": True,
                "activation_mode": "latest_valid_prior_date_policy_auto_loaded",
                "sample_floor": "1_verified_ordered_path_per_cohort_price_band",
                "ready_candidate_count": 1,
                "candidates": [
                    {
                        "policy_key": "single_limit_down|1000_4999",
                        "cohort": "single_limit_down",
                        "price_band": "1000_4999",
                        "sample_count": 1,
                        "source_quality_adjusted_ev_pct": 0.8,
                        "downside_p10_pct": 0.8,
                        "mae_p10_pct": -0.1,
                        "relock_rate_pct": 0.0,
                        "entry_bbo_coverage_pct": 100.0,
                        "evidence_mode": "single_verified_ordered_path_allowed",
                    }
                ],
                "risk_contract": {
                    "max_concurrent_positions": 1,
                    "max_daily_entries": 1,
                    "quantity_owner": "position_sizing_dynamic_formula",
                    "requested_quantity_override": None,
                    "scale_in_allowed": False,
                    "same_day_reentry_allowed": False,
                    "overnight_allowed": False,
                    "entry_requires_two_ordered_unlocked_ticks": True,
                    "entry_requires_fresh_quote_and_bbo": True,
                    "max_entry_spread_pct": 1.5,
                    "relock_or_stale_cancels_unfilled_entry": True,
                    "normal_scalping_ai_and_submit_guards_required": True,
                    "hard_safety_priority": "unchanged_and_unbypassable",
                },
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "allowed_runtime_apply": True,
            }
        ),
        encoding="utf-8",
    )
    manager = LimitDownWatchManager("token", _DB(), _Bus())

    manager._load_live_policy(date(2026, 8, 3))

    assert manager.active_live_policy_keys == {"single_limit_down|1000_4999"}
    assert manager.live_policy_source_date == "2026-08-02"


def test_latest_cumulative_blocked_artifact_withdraws_prior_live_policy(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(limit_down_watch, "LIVE_AUTO_POLICY_DIR", tmp_path)
    positive_cell = {
        "policy_key": "near_limit_rebound|1000_4999",
        "cohort": "near_limit_rebound",
        "price_band": "1000_4999",
        "sample_count": 1,
        "observation_date_count": 1,
        "source_quality_adjusted_ev_pct": 1.0,
        "downside_p10_pct": 1.0,
        "mae_p10_pct": -0.2,
        "relock_rate_pct": 0.0,
        "entry_bbo_coverage_pct": 100.0,
    }
    ready = limit_down_watch_research.build_bounded_live_candidate(
        "2026-08-02",
        {"source_quality_status": "pass", "policy_cells": [positive_cell]},
    )
    blocked = limit_down_watch_research.build_bounded_live_candidate(
        "2026-08-03",
        {
            "source_quality_status": "pass",
            "policy_cells": [
                {
                    **positive_cell,
                    "sample_count": 2,
                    "observation_date_count": 2,
                    "source_quality_adjusted_ev_pct": -0.5,
                    "downside_p10_pct": -2.0,
                }
            ],
        },
    )
    (tmp_path / "limit_down_watch_bounded_live_candidate_2026-08-02.json").write_text(
        json.dumps(ready), encoding="utf-8"
    )
    (tmp_path / "limit_down_watch_bounded_live_candidate_2026-08-03.json").write_text(
        json.dumps(blocked), encoding="utf-8"
    )
    prior_manager = LimitDownWatchManager("token", _DB(), _Bus())
    prior_manager._load_live_policy(date(2026, 8, 3))
    manager = LimitDownWatchManager("token", _DB(), _Bus())

    manager._load_live_policy(date(2026, 8, 4))

    assert ready["status"] == "live_auto_apply_ready"
    assert prior_manager.active_live_policy_keys == {"near_limit_rebound|1000_4999"}
    assert blocked["status"] == "blocked"
    assert manager.active_live_policy_keys == set()
    assert manager.live_policy_source_date == ""


def test_live_policy_handoff_requires_fresh_confirmed_unlock_and_daily_capacity():
    manager = LimitDownWatchManager("token", _DB(), _Bus())
    manager.active = _candidate(count=1)
    key = "single_limit_down|1000_4999"
    manager.active_live_policy_keys = {key}
    manager.live_policy_by_key = {key: {"sample_count": 1}}
    manager.live_policy_source_date = "2026-08-02"
    manager.live_policy_max_entry_spread_pct = 1.5
    manager.state = {
        "phase": "UNLOCKED",
        "consecutive_unlocked_tick_count": 2,
        "unlock_confirmed_epoch": 99.0,
        "last_tick_epoch": 100.0,
        "current_price": 2910,
        "lower_limit_price": 2800,
        "best_ask": 2920,
        "best_bid": 2910,
        "trade_value": 1_000_000,
        "volume": 1000,
    }

    target = manager.live_promotion_target(now_epoch=101.0, daily_promotion_count=0)

    assert target is not None
    assert target["LimitDownLivePolicyKey"] == key
    assert target["ScannerWatchBudgetOwner"] == "limit_down_rotation"
    assert target["LimitDownMaxEntrySpreadPct"] == 1.5
    assert target["LimitDownScaleInAllowed"] is False
    assert (
        manager.live_promotion_target(now_epoch=101.0, daily_promotion_count=1) is None
    )
    assert (
        manager.live_promotion_target(now_epoch=106.0, daily_promotion_count=0) is None
    )


def test_limit_down_live_scanner_contract_and_scale_in_veto():
    now_ts = datetime(2026, 8, 3, 9, 10).timestamp()
    target = {
        "Code": "000001",
        "Name": "테스트",
        "Price": 2910,
        "SourceSet": {limit_down_watch.LIMIT_DOWN_LIVE_UNLOCK_SOURCE},
        "LimitDownLivePolicyMatched": True,
        "LimitDownLivePolicyKey": "single_limit_down|1000_4999",
        "LimitDownLivePolicySourceDate": "2026-08-02",
        "LimitDownLivePolicySampleCount": 1,
        "LimitDownUnlockConfirmed": True,
        "LimitDownLastTickEpoch": now_ts - 1,
        "LimitDownLowerLimitPrice": 2800,
        "LimitDownBestAsk": 2920,
        "LimitDownBestBid": 2910,
        "LimitDownEntrySpreadPct": 0.342466,
        "LimitDownMaxEntrySpreadPct": 1.5,
        "LimitDownCohort": "single_limit_down",
        "LimitDownPriceBand": "1000_4999",
        "LimitDownRiskMaxDailyEntries": 1,
        "LimitDownScaleInAllowed": False,
        "LimitDownSameDayReentryAllowed": False,
        "LimitDownOvernightAllowed": False,
        "LimitDownNormalScalpingGuardsRequired": True,
    }

    assert (
        scalping_scanner._limit_down_live_candidate_block_reason(target, now_ts=now_ts)
        == ""
    )
    guard = scalping_scanner._scanner_real_source_guard_decision(target, {}, now_ts)
    assert guard["blocked"] is False
    target["LimitDownMaxEntrySpreadPct"] = 0.1
    assert (
        scalping_scanner._limit_down_live_candidate_block_reason(target, now_ts=now_ts)
        == "limit_down_live_spread_too_wide"
    )
    target["LimitDownMaxEntrySpreadPct"] = 1.5
    scale_in = sniper_state_handlers.can_consider_scale_in(
        {"source_signature": "LIMIT_DOWN_LIVE_UNLOCK"},
        "000001",
        {},
        "SCALPING",
        "NORMAL",
    )
    assert scale_in == {
        "allowed": False,
        "reason": "limit_down_live_scale_in_forbidden",
    }


def test_near_limit_live_scanner_contract_requires_rebound_provenance():
    now_ts = datetime(2026, 8, 5, 9, 10).timestamp()
    target = {
        "Price": 3030,
        "LimitDownLivePolicyMatched": True,
        "LimitDownLivePolicyKey": "near_limit_rebound|1000_4999",
        "LimitDownLivePolicySourceDate": "2026-08-04",
        "LimitDownLivePolicySampleCount": 1,
        "LimitDownLiveTriggerType": "near_rebound",
        "LimitDownReboundConfirmed": True,
        "LimitDownLastTickEpoch": now_ts - 1,
        "LimitDownBestAsk": 3040,
        "LimitDownBestBid": 3030,
        "LimitDownEntrySpreadPct": 0.328947,
        "LimitDownMaxEntrySpreadPct": 1.5,
        "LimitDownSessionOpenPrice": 3000,
        "LimitDownSessionLowPrice": 2950,
        "LimitDownReboundFromLowPct": 2.711864,
        "LimitDownMinReboundFromLowPct": 1.0,
        "LimitDownCohort": "near_limit_rebound",
        "LimitDownPriceBand": "1000_4999",
        "LimitDownRiskMaxDailyEntries": 1,
        "LimitDownScaleInAllowed": False,
        "LimitDownSameDayReentryAllowed": False,
        "LimitDownOvernightAllowed": False,
        "LimitDownNormalScalpingGuardsRequired": True,
    }

    assert (
        scalping_scanner._limit_down_live_candidate_block_reason(target, now_ts=now_ts)
        == ""
    )
    target["Price"] = 2990
    assert (
        scalping_scanner._limit_down_live_candidate_block_reason(target, now_ts=now_ts)
        == "limit_down_live_quote_contract_invalid"
    )


def test_limit_down_live_pre_submit_guard_blocks_relock(monkeypatch):
    now_ts = time.time()
    stock = {
        "source_signature": "LIMIT_DOWN_LIVE_UNLOCK",
        "limit_down_live_policy_matched": True,
        "limit_down_live_policy_sample_count": 1,
        "limit_down_unlock_confirmed": True,
        "limit_down_risk_max_daily_entries": 1,
        "limit_down_scale_in_allowed": False,
        "limit_down_same_day_reentry_allowed": False,
        "limit_down_overnight_allowed": False,
        "limit_down_normal_scalping_guards_required": True,
        "limit_down_lower_limit_price": 2800,
        "limit_down_max_entry_spread_pct": 1.5,
    }
    relocked = {
        "curr": 2800,
        "best_ask": 2800,
        "best_bid": 2795,
        "last_ws_update_ts": now_ts,
    }
    monkeypatch.setattr(
        sniper_state_handlers,
        "_pre_submit_refresh_real_ws_snapshot",
        lambda *_args: (relocked, {"pre_submit_ws_snapshot_refresh_reason": "fresh"}),
    )

    _, blocked = sniper_state_handlers._limit_down_live_pre_submit_guard(
        stock, "000001", relocked, "SCALPING"
    )

    assert blocked["allowed"] is False
    assert blocked["reason"] == "limit_down_live_relocked_or_quote_invalid"


def test_limit_down_live_pre_submit_guard_accepts_fresh_unlocked_bbo(monkeypatch):
    now_ts = time.time()
    stock = {
        "scanner_source_signature": "LIMIT_DOWN_LIVE_UNLOCK",
        "limit_down_live_policy_matched": True,
        "limit_down_live_policy_sample_count": 1,
        "limit_down_unlock_confirmed": True,
        "limit_down_risk_max_daily_entries": 1,
        "limit_down_scale_in_allowed": False,
        "limit_down_same_day_reentry_allowed": False,
        "limit_down_overnight_allowed": False,
        "limit_down_normal_scalping_guards_required": True,
        "limit_down_lower_limit_price": 2800,
        "limit_down_max_entry_spread_pct": 1.5,
    }
    unlocked = {
        "curr": 2910,
        "best_ask": 2920,
        "best_bid": 2910,
        "last_ws_update_ts": now_ts,
    }
    monkeypatch.setattr(
        sniper_state_handlers,
        "_pre_submit_refresh_real_ws_snapshot",
        lambda *_args: (unlocked, {"pre_submit_ws_snapshot_refresh_reason": "fresh"}),
    )

    _, allowed = sniper_state_handlers._limit_down_live_pre_submit_guard(
        stock, "000001", unlocked, "SCALPING"
    )

    assert allowed["allowed"] is True
    assert allowed["reason"] == "limit_down_live_pre_submit_pass"


def test_near_limit_live_pre_submit_guard_rechecks_open_and_rebound(monkeypatch):
    now_ts = time.time()
    stock = {
        "source_signature": "LIMIT_DOWN_LIVE_UNLOCK",
        "limit_down_live_policy_matched": True,
        "limit_down_live_policy_sample_count": 1,
        "limit_down_live_trigger_type": "near_rebound",
        "limit_down_rebound_confirmed": True,
        "limit_down_risk_max_daily_entries": 1,
        "limit_down_scale_in_allowed": False,
        "limit_down_same_day_reentry_allowed": False,
        "limit_down_overnight_allowed": False,
        "limit_down_normal_scalping_guards_required": True,
        "limit_down_session_open_price": 3000,
        "limit_down_session_low_price": 2950,
        "limit_down_min_rebound_from_low_pct": 1.0,
        "limit_down_max_entry_spread_pct": 1.5,
    }
    refreshed = {
        "curr": 3030,
        "best_ask": 3040,
        "best_bid": 3030,
        "last_ws_update_ts": now_ts,
    }
    monkeypatch.setattr(
        sniper_state_handlers,
        "_pre_submit_refresh_real_ws_snapshot",
        lambda *_args: (refreshed, {"pre_submit_ws_snapshot_refresh_reason": "fresh"}),
    )

    _, allowed = sniper_state_handlers._limit_down_live_pre_submit_guard(
        stock, "000001", refreshed, "SCALPING"
    )
    assert allowed["allowed"] is True

    refreshed["curr"] = 2990
    refreshed["best_ask"] = 3000
    refreshed["best_bid"] = 2990
    _, blocked = sniper_state_handlers._limit_down_live_pre_submit_guard(
        stock, "000001", refreshed, "SCALPING"
    )
    assert blocked["allowed"] is False
    assert blocked["reason"] == "limit_down_live_rebound_lost"


def test_rotation_prefers_active_sim_policy_after_coverage_floor():
    manager = LimitDownWatchManager("token", _DB(), _Bus())
    consecutive = _candidate(code="000021", count=2)
    single = _candidate(code="000022", count=1)
    manager.candidates = [consecutive, single]
    manager.activity = {
        consecutive.code: {"visit_count": 2, "unlock_count": 5},
        single.code: {"visit_count": 2},
    }
    manager.cell_visit_counts = {
        "consecutive_limit_down_2plus|1000_4999": 2,
        "single_limit_down|1000_4999": 2,
    }
    manager.active_sim_policy_keys = {"single_limit_down|1000_4999"}

    picked = manager._pick(set(), 1000.0)

    assert picked is single


def test_limit_down_counterfactual_label_uses_confirmed_unlock_and_cost():
    visit = {
        "row_id": "2026-08-03:000001:1",
        "target_date": "2026-08-03",
        "code": "000001",
        "name": "테스트",
        "cohort": "single_limit_down",
        "price_band": "1000_4999",
        "consecutive_count": 1,
        "registered_at": "2026-08-03T09:00:00",
        "release_reason": "rotation_due",
        "lower_limit_price": 1000,
        "transitions": [
            {"at": "2026-08-03T09:00:05", "phase": "UNLOCKED"},
            {"at": "2026-08-03T09:02:00", "phase": "RELOCKED"},
        ],
        "snapshots": [
            {
                "at": "2026-08-03T09:00:05",
                "phase": "UNLOCKED",
                "current_price": 1050,
                "best_ask": 1050,
                "best_bid": 1045,
            },
            {
                "at": "2026-08-03T09:00:10",
                "phase": "UNLOCKED",
                "current_price": 1060,
                "best_ask": 1060,
                "best_bid": 1055,
            },
            {
                "at": "2026-08-03T09:03:10",
                "phase": "UNLOCKED_AGAIN",
                "current_price": 1120,
                "best_ask": 1120,
                "best_bid": 1115,
            },
        ],
    }

    label = limit_down_watch_research.label_observation_visit(visit)

    assert label["label_status"] == "pass"
    assert label["entry_price"] == 1060
    assert label["entry_bbo_available"] is True
    assert label["selected_exit_horizon_sec"] == 180
    assert label["gross_return_pct"] > 0
    assert label["net_return_pct"] < label["gross_return_pct"]
    assert label["relocked_after_entry"] is True
    assert label["runtime_effect"] is False
    assert label["actual_order_submitted"] is False
    assert label["broker_order_forbidden"] is True


def test_near_limit_rebound_label_requires_ordered_open_recovery():
    row = limit_down_watch_research.label_observation_visit(
        {
            "row_id": "2026-08-05:000001:1",
            "target_date": "2026-08-05",
            "code": "000001",
            "cohort": "near_limit_rebound",
            "price_band": "1000_4999",
            "confirmations": [
                {
                    "at": "2026-08-05T09:00:06",
                    "phase": "NEAR_REBOUND_OBSERVING",
                    "current_price": 3020,
                    "open_price": 3000,
                    "low_price": 2950,
                    "rebound_from_low_pct": 2.372881,
                    "best_ask": 3030,
                    "best_bid": 3020,
                    "confirmation_tick_count": 2,
                    "confirmation_type": "near_rebound",
                }
            ],
            "snapshots": [
                {
                    "at": "2026-08-05T09:00:01",
                    "phase": "NEAR_REBOUND_OBSERVING",
                    "current_price": 3000,
                    "open_price": 3000,
                    "low_price": 2950,
                    "best_ask": 3010,
                    "best_bid": 3000,
                },
                {
                    "at": "2026-08-05T09:00:06",
                    "phase": "NEAR_REBOUND_OBSERVING",
                    "current_price": 3020,
                    "open_price": 3000,
                    "low_price": 2950,
                    "best_ask": 3030,
                    "best_bid": 3020,
                },
                {
                    "at": "2026-08-05T09:03:10",
                    "phase": "NEAR_REBOUND_OBSERVING",
                    "current_price": 3100,
                    "open_price": 3000,
                    "low_price": 2950,
                    "best_ask": 3110,
                    "best_bid": 3100,
                },
            ],
        }
    )

    assert row["label_status"] == "pass"
    assert row["entry_confirmation_type"] == "near_rebound"
    assert row["entry_price"] == 3030
    assert row["runtime_effect"] is False
    assert row["broker_order_forbidden"] is True


def test_research_collector_preserves_raw_near_rebound_confirmation(
    monkeypatch, tmp_path
):
    event_dir = tmp_path / "events"
    candidate_dir = tmp_path / "candidates"
    event_dir.mkdir()
    candidate_dir.mkdir()
    monkeypatch.setattr(limit_down_watch_research, "EVENT_DIR", event_dir)
    monkeypatch.setattr(limit_down_watch_research, "CANDIDATE_DIR", candidate_dir)
    candidate = {
        "code": "000001",
        "name": "테스트",
        "cohort": "near_limit_rebound",
        "price_band": "1000_4999",
        "candidate_kind": "near_limit_rebound",
        "limit_down_close": 3000,
    }
    source = {
        **_candidate_source_payload(candidate),
        "target_date": "2026-08-05",
    }
    (candidate_dir / "limit_down_watch_candidate_source_2026-08-05.json").write_text(
        json.dumps(source), encoding="utf-8"
    )
    events = [
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_registered",
            "stock_code": "000001",
            "emitted_at": "2026-08-05T09:00:00+09:00",
            "fields": _observation_event_fields(
                cohort="near_limit_rebound", price_band="1000_4999"
            ),
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_rebound_confirmed",
            "stock_code": "000001",
            "emitted_at": "2026-08-05T09:00:06+09:00",
            "fields": _observation_event_fields(
                phase="NEAR_REBOUND_OBSERVING",
                current_price=3020,
                open_price=3000,
                low_price=2950,
                rebound_from_low_pct=2.372881,
                best_ask=3030,
                best_bid=3020,
                confirmation_tick_count=2,
            ),
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_released",
            "stock_code": "000001",
            "emitted_at": "2026-08-05T09:03:10+09:00",
            "fields": _observation_event_fields(reason="rotation_due"),
        },
    ]
    (event_dir / "pipeline_events_2026-08-05.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in events), encoding="utf-8"
    )

    visits, status = limit_down_watch_research.collect_observation_visits("2026-08-05")

    assert status["valid"] is True
    assert visits[0]["confirmations"] == [
        {
            "at": "2026-08-05T09:00:06+09:00",
            "phase": "NEAR_REBOUND_OBSERVING",
            "current_price": 3020,
            "open_price": 3000,
            "low_price": 2950,
            "rebound_from_low_pct": 2.372881,
            "best_ask": 3030,
            "best_bid": 3020,
            "confirmation_tick_count": 2,
            "confirmation_type": "near_rebound",
        }
    ]


def test_near_limit_rebound_label_rejects_single_trigger_tick():
    row = limit_down_watch_research.label_observation_visit(
        {
            "row_id": "2026-08-05:000001:1",
            "target_date": "2026-08-05",
            "code": "000001",
            "cohort": "near_limit_rebound",
            "price_band": "1000_4999",
            "snapshots": [
                {
                    "at": "2026-08-05T09:00:01",
                    "phase": "NEAR_REBOUND_OBSERVING",
                    "current_price": 3000,
                    "open_price": 3000,
                    "low_price": 2950,
                    "best_ask": 3010,
                    "best_bid": 3000,
                }
            ],
        }
    )

    assert row["label_status"] == "insufficient_ordered_rebound_confirmation"


def test_sim_policy_is_independent_by_cohort_and_price_band():
    rows = []
    for index in range(5):
        rows.append(
            {
                "row_id": f"positive-{index}",
                "target_date": f"2026-07-{29 + index % 3:02d}",
                "label_status": "pass",
                "cohort": "single_limit_down",
                "price_band": "5000_9999",
                "entry_price": 6000,
                "net_return_pct": 1.0,
                "mfe_pct": 2.0,
                "mae_pct": -0.5,
                "slot_hours": 0.05,
                "entry_bbo_available": True,
                "relocked_after_entry": False,
            }
        )
        rows.append(
            {
                "row_id": f"negative-{index}",
                "target_date": f"2026-07-{29 + index % 3:02d}",
                "label_status": "pass",
                "cohort": "consecutive_limit_down_2plus",
                "price_band": "1000_4999",
                "entry_price": 1500,
                "net_return_pct": -2.0,
                "mfe_pct": 0.3,
                "mae_pct": -3.0,
                "slot_hours": 0.05,
                "entry_bbo_available": True,
                "relocked_after_entry": True,
            }
        )
    cells = limit_down_watch_research._cell_rows(rows)
    counterfactual = {
        "policy_cells": cells,
        "target_date": "2026-08-03",
    }

    catalog = limit_down_watch_research.build_sim_policy_catalog(
        "2026-08-03", counterfactual
    )

    assert catalog["status"] == "pass"
    assert catalog["active_policy_count"] == 1
    assert catalog["active_policies"][0]["policy_key"] == (
        "single_limit_down|5000_9999"
    )
    assert catalog["allowed_sim_apply"] is True
    assert catalog["allowed_runtime_apply"] is False


def test_bounded_live_candidate_auto_applies_one_verified_positive_path():
    counterfactual = {
        "source_quality_status": "pass",
        "policy_cells": [
            {
                "policy_key": "near_limit_rebound|5000_9999",
                "cohort": "near_limit_rebound",
                "price_band": "5000_9999",
                "sample_count": 1,
                "observation_date_count": 1,
                "source_quality_adjusted_ev_pct": 1.0,
                "ev_lower_confidence_bound_90_pct": None,
                "downside_p10_pct": 1.0,
                "mae_p10_pct": -0.5,
                "relock_rate_pct": 0.0,
                "entry_bbo_coverage_pct": 100.0,
            }
        ],
    }

    artifact = limit_down_watch_research.build_bounded_live_candidate(
        "2026-08-03", counterfactual
    )

    assert artifact["status"] == "live_auto_apply_ready"
    assert artifact["ready_candidate_count"] == 1
    assert artifact["candidates"][0]["cohort"] == "near_limit_rebound"
    assert artifact["operator_approval_required"] is False
    assert artifact["preopen_consumer_implemented"] is True
    assert artifact["risk_contract"]["quantity_owner"] == (
        "position_sizing_dynamic_formula"
    )
    assert artifact["risk_contract"]["requested_quantity_override"] is None
    assert artifact["risk_contract"]["scale_in_allowed"] is False
    assert artifact["risk_contract"]["entry_requires_two_ordered_trigger_ticks"] is True
    assert artifact["runtime_effect"] is False
    assert artifact["actual_order_submitted"] is False
    assert artifact["broker_order_forbidden"] is True
    assert artifact["allowed_runtime_apply"] is True


def test_counterfactual_cumulative_rows_auto_merge_and_deduplicate(monkeypatch):
    prior_row = {
        "row_id": "2026-08-04:000001:1",
        "target_date": "2026-08-04",
        "label_status": "pass",
        "cohort": "near_limit_rebound",
        "price_band": "1000_4999",
        "entry_price": 3000,
        "net_return_pct": 1.0,
        "mfe_pct": 1.5,
        "mae_pct": -0.2,
        "slot_hours": 0.05,
        "entry_bbo_available": True,
        "relocked_after_entry": False,
    }
    current_row = {
        **prior_row,
        "row_id": "2026-08-05:000002:1",
        "target_date": "2026-08-05",
        "net_return_pct": 2.0,
    }
    monkeypatch.setattr(
        limit_down_watch_research,
        "collect_observation_visits",
        lambda _target_date: (
            [{"label": current_row}, {"label": dict(current_row)}],
            {"valid": True},
        ),
    )
    monkeypatch.setattr(
        limit_down_watch_research,
        "label_observation_visit",
        lambda visit: dict(visit["label"]),
    )
    monkeypatch.setattr(
        limit_down_watch_research,
        "_latest_prior_artifact",
        lambda *_args: {
            "schema_version": 1,
            "report_type": "limit_down_watch_counterfactual",
            "target_date": "2026-08-04",
            "rows": [prior_row],
            **limit_down_watch_research.COUNTERFACTUAL_CONTRACT,
            **limit_down_watch_research.SOURCE_ONLY_FIELDS,
        },
    )

    artifact, rows, source_status = limit_down_watch_research.build_counterfactual(
        "2026-08-05"
    )

    assert source_status["valid"] is True
    assert len(rows) == 2
    assert len(artifact["rows"]) == 2
    assert artifact["sample_count"] == 2
    assert artifact["observation_date_count"] == 2
    assert artifact["source_quality_adjusted_ev_pct"] == 1.5
    assert artifact["near_limit_rebound_sample_count"] == 2
    assert artifact["cumulative_update"] == {
        "mode": "latest_prior_rolling_rows_plus_current_dedup_by_row_id",
        "prior_artifact_target_date": "2026-08-04",
        "prior_input_row_count": 1,
        "current_input_row_count": 2,
        "deduplicated_rolling_row_count": 2,
        "duplicate_or_out_of_window_row_count": 1,
    }


def test_counterfactual_blocks_live_candidate_when_prior_cumulative_is_invalid(
    monkeypatch,
):
    current_row = {
        "row_id": "2026-08-05:000002:1",
        "target_date": "2026-08-05",
        "label_status": "pass",
        "cohort": "near_limit_rebound",
        "price_band": "1000_4999",
        "entry_price": 3000,
        "net_return_pct": 2.0,
        "mfe_pct": 2.5,
        "mae_pct": -0.2,
        "slot_hours": 0.05,
        "entry_bbo_available": True,
        "relocked_after_entry": False,
    }
    monkeypatch.setattr(
        limit_down_watch_research,
        "collect_observation_visits",
        lambda _target_date: ([{"label": current_row}], {"valid": True}),
    )
    monkeypatch.setattr(
        limit_down_watch_research,
        "label_observation_visit",
        lambda visit: dict(visit["label"]),
    )
    monkeypatch.setattr(
        limit_down_watch_research,
        "_latest_prior_artifact",
        lambda *_args: {
            "schema_version": 1,
            "report_type": "limit_down_watch_counterfactual",
            "target_date": "2026-08-04",
            "rows": [{"row_id": "duplicate"}, {"row_id": "duplicate"}],
            **limit_down_watch_research.COUNTERFACTUAL_CONTRACT,
            **limit_down_watch_research.SOURCE_ONLY_FIELDS,
        },
    )

    counterfactual, _rows, status = limit_down_watch_research.build_counterfactual(
        "2026-08-05"
    )
    bounded = limit_down_watch_research.build_bounded_live_candidate(
        "2026-08-05", counterfactual
    )

    assert status["prior_counterfactual_valid"] is False
    assert counterfactual["source_quality_status"] == "blocked"
    assert bounded["status"] == "blocked"
    assert bounded["allowed_runtime_apply"] is False


def test_report_write_materializes_research_before_final_report(monkeypatch, tmp_path):
    calls = []
    payload = {
        "schema_version": 1,
        "report_type": "limit_down_watch",
        "target_date": "2026-08-03",
        "generated_at": "2026-08-03T20:10:00",
        "status": "no_observation",
        "groups": [],
        "evidence_readiness": {"blockers": []},
        "conversion_readiness": {"evidence_artifacts": {}},
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_sim_apply": False,
        "allowed_runtime_apply": False,
    }
    monkeypatch.setattr(limit_down_watch_report, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(
        limit_down_watch_report,
        "build_report",
        lambda target_date: calls.append(("build", target_date)) or payload,
    )
    monkeypatch.setattr(
        limit_down_watch_research,
        "produce_research_artifacts",
        lambda target_date: calls.append(("research", target_date)) or {},
    )

    json_path, markdown_path = limit_down_watch_report.write_report("2026-08-03")

    assert calls == [
        ("research", "2026-08-03"),
        ("build", "2026-08-03"),
    ]
    assert json_path.exists()
    assert markdown_path.exists()


def test_postclose_report_groups_ordered_intraday_path(tmp_path):
    event_path = tmp_path / "events.jsonl"
    candidate_path = tmp_path / "candidates.json"
    rows = [
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_registered",
            "stock_code": "000001",
            "fields": _observation_event_fields(
                cohort="consecutive_limit_down_2plus",
                price_band="1000_4999",
            ),
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_registered",
            "stock_code": "000002",
            "fields": _observation_event_fields(
                cohort="consecutive_limit_down_2plus",
                price_band="1000_4999",
            ),
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_state_transition",
            "stock_code": "000001",
            "fields": _observation_event_fields(phase="UNLOCKED"),
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_state_transition",
            "stock_code": "000001",
            "fields": _observation_event_fields(phase="RELOCKED"),
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_state_transition",
            "stock_code": "000002",
            "fields": _observation_event_fields(phase="ROTATED"),
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_snapshot",
            "stock_code": "000001",
            "fields": _observation_event_fields(
                cohort="consecutive_limit_down_2plus",
                price_band="1000_4999",
                low_to_high_range_pct="20.0",
                high_vs_limit_down_close_pct="25.0",
                low_vs_limit_down_close_pct="-5.0",
            ),
        },
    ]
    event_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps(
            _candidate_source_payload(
                {
                    "code": "000001",
                    "source_quality": "pass",
                }
            )
        ),
        encoding="utf-8",
    )
    report = limit_down_watch_report.build_report(
        "2026-07-27",
        event_path=event_path,
        candidate_path=candidate_path,
    )
    group = report["groups"][0]
    assert report["status"] == "pass"
    assert group["registered_codes"] == 2
    assert group["snapshot_codes"] == 1
    assert group["unlock_rate_pct"] == 50.0
    assert group["relock_rate_pct"] == 50.0
    assert group["ordered_intraday_path_capture_rate"] == 50.0
    assert group["avg_high_vs_limit_down_close_pct"] == 25.0
    assert group["avg_low_vs_limit_down_close_pct"] == -5.0
    assert report["actual_order_submitted"] is False
    assert report["allowed_sim_apply"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["evidence_readiness"]["sim_candidate_ready"] is False
    assert report["evidence_readiness"]["real_trading_ready"] is False
    assert report["evidence_readiness"]["ordered_path_captured_code_count"] == 1
    assert (
        "bounded_live_candidate_contract_missing"
        in report["evidence_readiness"]["blockers"]
    )
    assert (
        "ordered_intraday_path_capture_incomplete"
        in report["evidence_readiness"]["blockers"]
    )


def test_postclose_report_no_observation_stays_fail_closed(tmp_path):
    event_path = tmp_path / "events.jsonl"
    candidate_path = tmp_path / "candidates.json"
    event_path.write_text(
        json.dumps(
            {
                "pipeline": "LIMIT_DOWN_WATCH",
                "stage": "limit_down_watch_registered",
                "stock_code": "000001",
                "fields": _observation_event_fields(),
            }
        ),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps(
            _candidate_source_payload(
                {
                    "code": "000001",
                    "source_quality": "pass",
                }
            )
        ),
        encoding="utf-8",
    )

    report = limit_down_watch_report.build_report(
        "2026-07-27",
        event_path=event_path,
        candidate_path=candidate_path,
    )

    assert report["status"] == "no_observation"
    assert report["evidence_readiness"]["source_quality_status"] == "pass"
    assert report["evidence_readiness"]["sim_candidate_ready"] is False
    assert report["evidence_readiness"]["real_trading_ready"] is False
    assert (
        "ordered_intraday_path_sample_missing"
        in report["evidence_readiness"]["blockers"]
    )


def test_postclose_report_counts_quote_only_capture_separately(tmp_path):
    event_path = tmp_path / "events.jsonl"
    candidate_path = tmp_path / "candidates.json"
    rows = [
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_registered",
            "stock_code": "000001",
            "fields": _observation_event_fields(
                cohort="single_limit_down", price_band="1000_4999"
            ),
        },
        {
            "pipeline": "LIMIT_DOWN_WATCH",
            "stage": "limit_down_watch_quote_snapshot",
            "stock_code": "000001",
            "fields": _observation_event_fields(
                cohort="single_limit_down",
                price_band="1000_4999",
                market_data_type="0D",
                best_ask=2800,
                best_bid=2795,
            ),
        },
    ]
    event_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps(
            _candidate_source_payload({"code": "000001", "source_quality": "pass"})
        ),
        encoding="utf-8",
    )

    report = limit_down_watch_report.build_report(
        "2026-07-27", event_path=event_path, candidate_path=candidate_path
    )

    assert report["status"] == "pass"
    assert report["snapshot_code_count"] == 0
    assert report["quote_snapshot_code_count"] == 1
    assert report["market_data_observed_code_count"] == 1
    assert report["groups"][0]["quote_snapshot_codes"] == 1
    assert report["groups"][0]["ordered_path_captured_codes"] == 0


def test_postclose_report_distinguishes_missing_event_source(tmp_path):
    candidate_path = tmp_path / "candidates.json"
    candidate_path.write_text(
        json.dumps(
            _candidate_source_payload(
                {
                    "code": "000001",
                    "source_quality": "pass",
                }
            )
        ),
        encoding="utf-8",
    )

    report = limit_down_watch_report.build_report(
        "2026-07-27",
        event_path=tmp_path / "missing-events.jsonl",
        candidate_path=candidate_path,
    )

    assert report["status"] == "source_blocked"
    assert report["evidence_readiness"]["event_source_valid"] is False
    assert (
        "ordered_intraday_event_source_invalid"
        in report["evidence_readiness"]["blockers"]
    )


def test_postclose_report_skips_event_scan_without_candidate_source(
    tmp_path, monkeypatch
):
    event_path = tmp_path / "events.jsonl"
    event_path.write_text("not-json\n" * 100, encoding="utf-8")

    def fail_if_scanned(_path):
        raise AssertionError(
            "event source must not be scanned before candidate preflight"
        )

    monkeypatch.setattr(limit_down_watch_report, "_load_events", fail_if_scanned)

    report = limit_down_watch_report.build_report(
        "2026-07-27",
        event_path=event_path,
        candidate_path=tmp_path / "missing-candidates.json",
    )

    readiness = report["evidence_readiness"]
    assert report["status"] == "source_blocked"
    assert readiness["source_quality_status"] == "missing"
    assert readiness["event_source_required"] is False
    assert readiness["event_source_valid"] is True
    assert readiness["event_source"]["read_mode"] == ("not_scanned_candidate_preflight")
    assert readiness["event_source"]["scan_skip_reason"] == "missing"
    assert readiness["event_source"]["line_count"] == 0
    assert "ordered_intraday_event_source_invalid" not in readiness["blockers"]
    markdown = limit_down_watch_report._render_markdown(report)
    assert "- event_source_required: `False`" in markdown
    assert "- event_source_read_mode: `not_scanned_candidate_preflight`" in markdown


def test_postclose_report_skips_event_scan_for_valid_empty_candidate_set(
    tmp_path, monkeypatch
):
    candidate_path = tmp_path / "candidates.json"
    candidate_path.write_text(json.dumps(_candidate_source_payload()), encoding="utf-8")

    def fail_if_scanned(_path):
        raise AssertionError("empty candidate set must not scan the event source")

    monkeypatch.setattr(limit_down_watch_report, "_load_events", fail_if_scanned)

    report = limit_down_watch_report.build_report(
        "2026-07-27",
        event_path=tmp_path / "missing-events.jsonl",
        candidate_path=candidate_path,
    )

    readiness = report["evidence_readiness"]
    assert report["status"] == "no_observation"
    assert readiness["source_quality_status"] == "no_candidate"
    assert readiness["candidate_source_valid"] is True
    assert readiness["event_source_required"] is False
    assert readiness["event_source_valid"] is True
    assert readiness["event_source"]["scan_skip_reason"] == "no_candidate"


def test_postclose_report_blocks_event_contract_violation(tmp_path):
    event_path = tmp_path / "events.jsonl"
    candidate_path = tmp_path / "candidates.json"
    event_path.write_text(
        json.dumps(
            {
                "pipeline": "LIMIT_DOWN_WATCH",
                "stage": "limit_down_watch_registered",
                "stock_code": "000001",
                "fields": {
                    **_observation_event_fields(),
                    "runtime_effect": "True",
                },
            }
        ),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps(
            _candidate_source_payload(
                {
                    "code": "000001",
                    "source_quality": "pass",
                }
            )
        ),
        encoding="utf-8",
    )

    report = limit_down_watch_report.build_report(
        "2026-07-27",
        event_path=event_path,
        candidate_path=candidate_path,
    )

    assert report["status"] == "source_blocked"
    event_source = report["evidence_readiness"]["event_source"]
    assert event_source["contract_violation_count"] == 1
    assert report["evidence_readiness"]["event_source_valid"] is False


def test_postclose_report_ignores_non_finite_metric_values():
    assert limit_down_watch_report._safe_float("nan") is None
    assert limit_down_watch_report._safe_float("inf") is None
    assert limit_down_watch_report._safe_float("-inf") is None


def test_postclose_event_loader_streams_and_filters_source(tmp_path, monkeypatch):
    event_path = tmp_path / "events.jsonl"
    matching = {
        "pipeline": "LIMIT_DOWN_WATCH",
        "stage": "limit_down_watch_registered",
        "stock_code": "000001",
        "fields": _observation_event_fields(),
    }
    event_path.write_text(
        "\n".join(
            [
                json.dumps({"pipeline": "OTHER", "stage": "ignored"}),
                json.dumps(matching),
            ]
        ),
        encoding="utf-8",
    )

    def forbid_full_read(*_args, **_kwargs):
        raise AssertionError("event loader must not materialize the full source")

    monkeypatch.setattr(Path, "read_text", forbid_full_read)
    rows, status = limit_down_watch_report._load_events(event_path)

    assert rows == [matching]
    assert status["readable"] is True
    assert status["read_mode"] == "streaming_filtered"
    assert status["full_source_materialized"] is False
    assert status["line_count"] == 2
    assert status["matching_event_count"] == 1
    assert status["valid"] is True


def test_rolling_observation_evidence_enforces_cohort_and_day_floors(tmp_path):
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    for day_index in range(1, 5):
        target_date = f"2026-07-{27 + day_index:02d}"
        (history_dir / f"limit_down_watch_{target_date}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "report_type": "limit_down_watch",
                    "target_date": target_date,
                    "status": "pass",
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "allowed_runtime_apply": False,
                    "evidence_readiness": {
                        "candidate_source_valid": True,
                        "event_source_valid": True,
                    },
                    "groups": [
                        {
                            "cohort": "consecutive_limit_down_2plus",
                            "registered_codes": 2,
                            "ordered_path_captured_codes": 1,
                        },
                        {
                            "cohort": "single_limit_down",
                            "registered_codes": 3,
                            "ordered_path_captured_codes": 2,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    evidence = limit_down_watch_report._rolling_observation_evidence(
        "2026-08-03",
        current_status="pass",
        current_groups=[
            {
                "cohort": "consecutive_limit_down_2plus",
                "registered_codes": 1,
                "ordered_path_captured_codes": 1,
            },
            {
                "cohort": "single_limit_down",
                "registered_codes": 2,
                "ordered_path_captured_codes": 2,
            },
        ],
        current_readiness={
            "candidate_source_valid": True,
            "event_source_valid": True,
        },
        history_dir=history_dir,
    )

    assert evidence["observation_day_count"] == 5
    assert evidence["ordered_path_captured_code_count"] == 15
    assert evidence["cohort_ordered_path_counts"] == {
        "consecutive_limit_down_2plus": 5,
        "single_limit_down": 10,
    }
    assert evidence["checks"]["observation_days"] is True
    assert evidence["checks"]["ordered_paths"] is False
    assert "consecutive_limit_down_2plus_paths" not in evidence["checks"]
    assert "single_limit_down_paths" not in evidence["checks"]
    assert evidence["status"] == "insufficient_sample"


def test_conversion_readiness_auto_applies_without_operator_approval():
    artifact_checks = {
        "counterfactual": {"status": "pass"},
        "sim_policy_catalog": {"status": "pass"},
        "post_sim_attribution": {"status": "pass"},
        "bounded_live_candidate": {"status": "pass"},
        "live_conversion_approval": {"status": "missing"},
    }
    readiness = limit_down_watch_report._conversion_readiness(
        "2026-08-03",
        candidate_source_valid=True,
        source_quality_status="pass",
        event_source_valid=True,
        rolling_observation={"status": "pass"},
        artifact_checks=artifact_checks,
        runtime_state={"target_date": "2026-08-03", "enabled": True},
    )

    assert readiness["decision"] == "auto_live_policy_ready"
    assert readiness["live_conversion_review_ready"] is True
    assert readiness["operator_approval_required"] is False
    assert readiness["separate_preopen_apply_ready"] is True
    assert readiness["automatic_live_conversion_scheduled"] is True
    assert readiness["automatic_live_conversion_performed"] is False
    assert readiness["real_trading_ready"] is True
    assert readiness["allowed_runtime_apply"] is True


def test_conversion_artifact_checks_require_metric_and_authority_contracts(tmp_path):
    paths = {
        "runtime_state": tmp_path / "runtime.json",
        "counterfactual": tmp_path / "counterfactual.json",
        "sim_policy_catalog": tmp_path / "sim-policy.json",
        "post_sim_attribution": tmp_path / "post-sim.json",
        "bounded_live_candidate": tmp_path / "bounded.json",
        "live_conversion_approval": tmp_path / "approval.json",
    }
    source_only = {
        "schema_version": 1,
        "target_date": "2026-08-03",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
    }
    paths["counterfactual"].write_text(
        json.dumps(
            {
                **source_only,
                **limit_down_watch_report.COUNTERFACTUAL_METRIC_CONTRACT,
                "report_type": "limit_down_watch_counterfactual",
                "status": "pass",
                "source_quality_status": "pass",
                "sample_count": 20,
                "observation_date_count": 5,
                "consecutive_limit_down_2plus_sample_count": 5,
                "single_limit_down_sample_count": 10,
                "source_quality_adjusted_ev_pct": 0.1,
                "eligible_policy_count": 1,
                "best_eligible_policy_ev_pct": 0.1,
                "rows": [{"row_id": f"row-{index}"} for index in range(20)],
                "cumulative_update": {
                    "mode": "latest_prior_rolling_rows_plus_current_dedup_by_row_id",
                    "deduplicated_rolling_row_count": 20,
                },
            }
        ),
        encoding="utf-8",
    )
    paths["sim_policy_catalog"].write_text(
        json.dumps(
            {
                **source_only,
                "report_type": "limit_down_watch_sim_policy_catalog",
                "status": "pass",
                "allowed_sim_apply": True,
                "active_policy_count": 1,
                "decision_authority": "limit_down_sim_policy_only",
                "forbidden_uses": limit_down_watch_report.CONVERSION_FORBIDDEN_USES,
            }
        ),
        encoding="utf-8",
    )
    paths["post_sim_attribution"].write_text(
        json.dumps(
            {
                **source_only,
                **limit_down_watch_report.POST_SIM_METRIC_CONTRACT,
                "report_type": "limit_down_watch_post_sim_attribution",
                "status": "pass",
                "source_quality_status": "pass",
                "sample_count": 20,
                "source_quality_adjusted_ev_pct": 0.2,
                "qualified_policy_count": 1,
                "best_qualified_policy_ev_pct": 0.2,
            }
        ),
        encoding="utf-8",
    )
    paths["bounded_live_candidate"].write_text(
        json.dumps(
            {
                **source_only,
                "report_type": "limit_down_watch_bounded_live_candidate",
                "status": "live_auto_apply_ready",
                "ready_candidate_count": 1,
                "candidates": [
                    {
                        "policy_key": "single_limit_down|5000_9999",
                        "cohort": "single_limit_down",
                        "price_band": "5000_9999",
                        "sample_count": 1,
                        "source_quality_adjusted_ev_pct": 0.5,
                        "downside_p10_pct": 0.5,
                        "mae_p10_pct": -0.2,
                        "relock_rate_pct": 0.0,
                        "entry_bbo_coverage_pct": 100.0,
                    }
                ],
                "decision_authority": "limit_down_live_auto_eligibility_candidate",
                "operator_approval_required": False,
                "preopen_consumer_implemented": True,
                "forbidden_uses": limit_down_watch_report.LIVE_AUTO_FORBIDDEN_USES,
                "allowed_runtime_apply": True,
                "risk_contract": {
                    "max_concurrent_positions": 1,
                    "max_daily_entries": 1,
                    "quantity_owner": "position_sizing_dynamic_formula",
                    "requested_quantity_override": None,
                    "scale_in_allowed": False,
                    "same_day_reentry_allowed": False,
                    "overnight_allowed": False,
                    "entry_requires_two_ordered_unlocked_ticks": True,
                    "entry_requires_two_ordered_trigger_ticks": True,
                    "near_rebound_requires_session_open_recovery": True,
                    "near_rebound_min_from_low_pct": 1.0,
                    "entry_requires_fresh_quote_and_bbo": True,
                    "max_entry_spread_pct": 1.5,
                    "relock_or_stale_cancels_unfilled_entry": True,
                    "normal_scalping_ai_and_submit_guards_required": True,
                    "hard_safety_priority": "unchanged_and_unbypassable",
                },
            }
        ),
        encoding="utf-8",
    )
    paths["live_conversion_approval"].write_text(
        json.dumps(
            {
                **source_only,
                "report_type": "limit_down_watch_live_conversion_approval",
                "approved": True,
                "approved_by": "user",
                "approval_scope": "limit_down_watch_live_conversion",
                "decision_authority": "limit_down_live_conversion_approval_record_only",
                "rollback_guard": "set flag false and gracefully restart",
            }
        ),
        encoding="utf-8",
    )

    checks = limit_down_watch_report._conversion_artifact_checks("2026-08-03", paths)
    assert {name: item["status"] for name, item in checks.items()} == {
        "counterfactual": "pass",
        "sim_policy_catalog": "pass",
        "post_sim_attribution": "pass",
        "bounded_live_candidate": "pass",
        "live_conversion_approval": "not_required_live_auto",
    }

    payload = json.loads(paths["counterfactual"].read_text(encoding="utf-8"))
    payload["metric_role"] = "diagnostic"
    paths["counterfactual"].write_text(json.dumps(payload), encoding="utf-8")
    invalid = limit_down_watch_report._conversion_artifact_checks("2026-08-03", paths)
    assert invalid["counterfactual"]["status"] == "invalid"
    assert "contract_mismatch:metric_role" in invalid["counterfactual"]["issues"]


def test_postclose_report_marks_missing_daily_observer_activation(tmp_path):
    report = limit_down_watch_report.build_report(
        "2026-08-03",
        event_path=tmp_path / "missing-events.jsonl",
        candidate_path=tmp_path / "missing-candidates.json",
        history_dir=tmp_path / "history",
        conversion_paths={
            "runtime_state": tmp_path / "missing-runtime.json",
            "counterfactual": tmp_path / "missing-counterfactual.json",
            "sim_policy_catalog": tmp_path / "missing-sim-policy.json",
            "post_sim_attribution": tmp_path / "missing-post-sim.json",
            "bounded_live_candidate": tmp_path / "missing-bounded.json",
            "live_conversion_approval": tmp_path / "missing-approval.json",
        },
    )

    conversion = report["conversion_readiness"]
    assert conversion["observer_activation_expected"] is True
    assert conversion["observer_activation_observed"] is False
    assert "observer_activation_not_observed" in conversion["blockers"]
    assert conversion["automatic_live_conversion_performed"] is False
