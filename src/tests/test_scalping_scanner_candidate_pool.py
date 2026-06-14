from __future__ import annotations

from types import SimpleNamespace

from src.scanners import scalping_scanner
from src.utils import kiwoom_utils


class _Session:
    def __init__(self, records):
        self.records = records

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def add(self, record):
        self.records.append(record)


class _DB:
    def __init__(self):
        self.records = []

    def get_session(self):
        return _Session(self.records)

    def find_reusable_watching_record(self, session, **kwargs):
        return None


class _EventBus:
    def __init__(self):
        self.events = []

    def publish(self, name, payload):
        self.events.append((name, payload))


def test_candidate_pool_merges_sources_and_prefers_value_vi_combo():
    pool = scalping_scanner.build_candidate_pool(
        soaring_targets=[
            {"Code": "005930", "Name": "삼성전자", "Price": 70000, "FluRate": 2.0, "CntrStr": 110.0}
        ],
        supernova_targets=[
            {"code": "005930", "name": "삼성전자", "spike_rate": 180.0, "priority_score": 20.0}
        ],
        value_targets=[
            {"Code": "005930", "Name": "삼성전자", "TradeValue": 50000000000, "RankNow": 5, "RankPrev": 60}
        ],
        vi_targets=[
            {"Code": "005930", "Name": "삼성전자", "VIMotionCount": 2}
        ],
    )

    target = pool["005930"]

    assert target["Source"] == "VI+VALUE"
    assert target["SourceSet"] == {"OPEN_TOP", "SUPERNOVA", "VALUE_TOP", "VI_TRIGGERED"}
    assert target["TradeValue"] == 50000000000
    assert target["CntrStrAvailable"] is True
    assert scalping_scanner._freshness_score(target) > 0


def test_value_top_without_strength_is_displayed_as_waiting(capsys, monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    db = _DB()
    event_bus = _EventBus()
    pool = scalping_scanner.build_candidate_pool(
        value_targets=[
            {"Code": "005930", "Name": "삼성전자", "Price": 70000, "FluRate": 1.0, "TradeValue": 50000000000}
        ]
    )

    target = pool["005930"]
    codes, _ = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        {},
        max_new_codes=1,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1000.0,
    )

    captured = capsys.readouterr().out
    assert codes == ["005930"]
    assert target["CntrStrAvailable"] is False
    assert "체결강도: 수신대기" in captured
    assert "체결강도: 0.0" not in captured


def test_strength_aliases_are_preserved_for_scanner_display():
    pool = scalping_scanner.build_candidate_pool(
        value_targets=[
            {"Code": "005930", "Name": "삼성전자", "Price": 70000, "FluRate": 1.0, "cntr_strg": "132.5"}
        ]
    )

    target = pool["005930"]

    assert target["CntrStr"] == 132.5
    assert target["CntrStrAvailable"] is True
    assert scalping_scanner._format_strength_display(target) == "132.5"


def test_safe_int_preserves_rank_sentinel_but_price_helper_absorbs_signed_prices():
    assert scalping_scanner._safe_int("-1") == -1
    assert scalping_scanner._safe_positive_int("-50000") == 50000


def test_rank_prev_negative_sentinel_does_not_create_rank_jump_score():
    base = {
        "Code": "005930",
        "Name": "삼성전자",
        "Price": 70000,
        "FluRate": 0.0,
        "CntrStr": 0.0,
        "Source": "VALUE_TOP",
        "SourceSet": {"VALUE_TOP"},
        "PriorityScore": 0.0,
        "SpikeRate": 0.0,
        "TradeValue": 0,
        "RankNow": 1,
        "VIMotionCount": 0,
    }

    no_previous_rank = {**base, "RankPrev": -1}
    real_rank_jump = {**base, "RankPrev": 61}

    assert scalping_scanner._freshness_score(real_rank_jump) > scalping_scanner._freshness_score(no_previous_rank)


def test_candidate_pool_keeps_latest_vi_release_time():
    pool = scalping_scanner.build_candidate_pool(
        vi_targets=[
            {"Code": "005930", "Name": "삼성전자", "VIReleaseTime": "091500"},
            {"Code": "005930", "Name": "삼성전자", "VIReleaseTime": "091200"},
            {"Code": "005930", "Name": "삼성전자", "VIReleaseTime": "092000"},
        ],
    )

    assert pool["005930"]["VIReleaseTime"] == "092000"


def test_promote_candidates_blocks_identical_recent_pick(monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    db = _DB()
    event_bus = _EventBus()
    target = {
        "Code": "005930",
        "Name": "삼성전자",
        "Price": 70000,
        "FluRate": 2.0,
        "CntrStr": 120.0,
        "Source": "OPEN_TOP",
        "SourceSet": {"OPEN_TOP"},
        "PriorityScore": 0.0,
        "SpikeRate": 0.0,
        "TradeValue": 0,
        "RankNow": 0,
        "RankPrev": 0,
    }

    first_codes, recent = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        {},
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1000.0,
    )
    second_codes, recent = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        recent,
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1100.0,
    )

    assert first_codes == ["005930"]
    assert second_codes == []
    assert event_bus.events == [("COMMAND_WS_REG", {"codes": ["005930"]})]
    assert len(db.records) == 1


def test_promote_candidates_allows_value_top_reentry(monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "005930": {
            "last_promoted_at": 1000.0,
            "last_source_signature": ("OPEN_TOP",),
            "last_score": 100.0,
        }
    }
    target = {
        "Code": "005930",
        "Name": "삼성전자",
        "Price": 70000,
        "FluRate": 2.0,
        "CntrStr": 120.0,
        "Source": "VALUE_TOP",
        "SourceSet": {"OPEN_TOP", "VALUE_TOP"},
        "PriorityScore": 0.0,
        "SpikeRate": 0.0,
        "TradeValue": 70000000000,
        "RankNow": 3,
        "RankPrev": 50,
    }

    codes, _ = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        recent,
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1100.0,
    )

    assert codes == ["005930"]
    assert event_bus.events == [("COMMAND_WS_REG", {"codes": ["005930"]})]


def test_real_source_guard_blocks_deteriorating_value_top_only_without_strength(monkeypatch, capsys):
    emitted = []
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        scalping_scanner,
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
    monkeypatch.setattr(
        scalping_scanner,
        "TRADING_RULES",
        SimpleNamespace(
            SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED=True,
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY=True,
            SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT=0.0,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "011070": {
            "last_promoted_at": 1000.0,
            "last_source_signature": ("VALUE_TOP",),
            "last_score": 100.0,
            "first_flu_rate": 8.4,
            "first_price": 1082000,
        }
    }
    target = {
        "Code": "011070",
        "Name": "LG이노텍",
        "Price": 1050000,
        "FluRate": 0.0,
        "CntrStr": 0.0,
        "CntrStrAvailable": False,
        "Source": "VALUE_TOP",
        "SourceSet": {"VALUE_TOP"},
        "PriorityScore": 0.0,
        "SpikeRate": 0.0,
        "TradeValue": 90000000000,
        "RankNow": 1,
        "RankPrev": 2,
    }

    codes, recent = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        recent,
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1100.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert db.records == []
    assert recent["011070"]["last_flu_rate"] == 0.0
    assert "value_top_only_repeat_deteriorating_without_strength" in capsys.readouterr().out
    assert emitted
    event = emitted[0]
    assert event["pipeline"] == "ENTRY_PIPELINE"
    assert event["stage"] == "scalping_scanner_real_source_guard_block"
    assert event["fields"]["scanner_real_source_guard_applied"] is True
    assert event["fields"]["scanner_real_source_guard_skip_reason"] == (
        "value_top_only_repeat_deteriorating_without_strength"
    )
    assert event["fields"]["scanner_real_source_guard_block_event_emitted"] is True
    assert event["fields"]["actual_order_submitted"] is False
    assert event["fields"]["broker_order_forbidden"] is True
    assert event["fields"]["decision_authority"] == "real_scalping_scanner_source_guard_only"


def test_real_source_guard_allows_independent_source_even_when_guard_enabled(monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        scalping_scanner,
        "TRADING_RULES",
        SimpleNamespace(
            SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED=True,
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY=True,
            SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT=0.0,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "005930": {
            "last_promoted_at": 1000.0,
            "last_source_signature": ("VALUE_TOP",),
            "last_score": 100.0,
            "first_flu_rate": 10.0,
            "first_price": 70000,
        }
    }
    target = {
        "Code": "005930",
        "Name": "삼성전자",
        "Price": 69000,
        "FluRate": 8.0,
        "CntrStr": 0.0,
        "CntrStrAvailable": False,
        "Source": "VI+VALUE",
        "SourceSet": {"VALUE_TOP", "VI_TRIGGERED"},
        "PriorityScore": 0.0,
        "SpikeRate": 0.0,
        "TradeValue": 90000000000,
        "RankNow": 1,
        "RankPrev": 2,
    }

    codes, _ = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        recent,
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1100.0,
    )

    assert codes == ["005930"]
    assert event_bus.events == [("COMMAND_WS_REG", {"codes": ["005930"]})]


def test_run_scalper_iteration_keeps_ws_payload_and_max_new_codes(monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        kiwoom_utils,
        "get_top_open_fluctuation_ka10028",
        lambda *args, **kwargs: [
            {"Code": f"00000{i}", "Name": f"OPEN{i}", "Price": 10000 + i, "FluRate": 1.0}
            for i in range(5)
        ],
    )
    monkeypatch.setattr(kiwoom_utils, "get_value_top_ka10032", lambda *args, **kwargs: [])
    monkeypatch.setattr(kiwoom_utils, "get_vi_triggered_ka10054", lambda *args, **kwargs: [])
    radar = SimpleNamespace(find_supernova_targets=lambda *args, **kwargs: [])
    db = _DB()
    event_bus = _EventBus()

    codes, _ = scalping_scanner.run_scalper_iteration(
        token="TOKEN",
        radar=radar,
        db=db,
        event_bus=event_bus,
        recent_picks={},
        reentry_cooldown_sec=1500,
        max_new_codes=3,
        open_top_limit=60,
        supernova_limit=30,
    )

    assert codes == ["000000", "000001", "000002"]
    assert event_bus.events == [("COMMAND_WS_REG", {"codes": ["000000", "000001", "000002"]})]
    assert len(db.records) == 3


def test_run_scalper_iteration_continues_when_one_source_fails(monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        kiwoom_utils,
        "get_top_open_fluctuation_ka10028",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("timeout")),
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "get_value_top_ka10032",
        lambda *args, **kwargs: [{"Code": "005930", "Name": "삼성전자", "Price": 70000}],
    )
    monkeypatch.setattr(kiwoom_utils, "get_vi_triggered_ka10054", lambda *args, **kwargs: [])
    radar = SimpleNamespace(find_supernova_targets=lambda *args, **kwargs: [])
    db = _DB()
    event_bus = _EventBus()

    codes, _ = scalping_scanner.run_scalper_iteration(
        token="TOKEN",
        radar=radar,
        db=db,
        event_bus=event_bus,
        recent_picks={},
        reentry_cooldown_sec=1500,
        max_new_codes=3,
        open_top_limit=60,
        supernova_limit=30,
    )

    assert codes == ["005930"]
    assert event_bus.events == [("COMMAND_WS_REG", {"codes": ["005930"]})]


def test_new_kiwoom_source_helpers_return_empty_list_on_fetch_failure(monkeypatch):
    def fail_fetch(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fail_fetch)

    assert kiwoom_utils.get_value_top_ka10032("TOKEN") == []
    assert kiwoom_utils.get_vi_triggered_ka10054("TOKEN") == []
