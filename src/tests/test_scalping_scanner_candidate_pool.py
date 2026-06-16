from __future__ import annotations

from types import SimpleNamespace
from datetime import time

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


def test_resolve_scan_interval_matches_intraday_schedule():
    assert scalping_scanner._resolve_scan_interval_sec(time(9, 5)) == 90
    assert scalping_scanner._resolve_scan_interval_sec(time(10, 29)) == 90
    assert scalping_scanner._resolve_scan_interval_sec(time(10, 30)) == 120
    assert scalping_scanner._resolve_scan_interval_sec(time(13, 59)) == 120
    assert scalping_scanner._resolve_scan_interval_sec(time(14, 0)) == 90
    assert scalping_scanner._resolve_scan_interval_sec(time(15, 0)) == 90


def test_ka10028_open_pric_pre_is_preserved_as_rate(monkeypatch):
    def fake_fetch(**kwargs):
        assert kwargs["api_id"] == "ka10028"
        return [
            {
                "open_pric_pre_flu_rt": [
                    {
                        "stk_cd": "487580",
                        "stk_nm": "마키나락스",
                        "cur_prc": "+74800",
                        "open_pric": "+65000",
                        "high_pric": "+76000",
                        "low_pric": "+64000",
                        "open_pric_pre": "+15.08",
                        "flu_rt": "+18.20",
                        "now_trde_qty": "123456",
                        "cntr_str": "101.5",
                    }
                ]
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows = kiwoom_utils.get_top_open_fluctuation_ka10028("TOKEN", limit=10)

    assert len(rows) == 1
    row = rows[0]
    assert row["OpenFluRate"] == 15.08
    assert row["OpenFluRateRaw"] == 15.08
    assert row["OpenPreRateRaw"] == 15.08
    assert row["OpenDiff"] == 15.08
    assert row["DayFluRate"] == 18.20
    assert row["FluRateMetric"] == "open_flu_rate"
    assert row["FluRateSource"] == "OPEN_TOP"


def test_ka10054_vi_rates_are_split_by_metric(monkeypatch):
    def fake_fetch(**kwargs):
        assert kwargs["api_id"] == "ka10054"
        return [
            {
                "motn_stk": [
                    {
                        "stk_cd": "005930",
                        "stk_nm": "삼성전자",
                        "motn_pric": "+72000",
                        "open_pric_pre_flu_rt": "+2.50",
                        "dynm_dispty_rt": "+1.20",
                        "static_dispty_rt": "+3.40",
                        "vimotn_cnt": "2",
                    }
                ]
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows = kiwoom_utils.get_vi_triggered_ka10054("TOKEN", limit=10)

    assert len(rows) == 1
    row = rows[0]
    assert row["ViFluRate"] == 2.5
    assert row["ViOpenFluRate"] == 2.5
    assert row["ViDynamicDisparityRate"] == 1.2
    assert row["ViStaticDisparityRate"] == 3.4
    assert row["ViFluRateMetric"] == "vi_open_flu_rate"


def test_ka00198_realtime_rank_start_is_normalized(monkeypatch):
    def fake_fetch(**kwargs):
        assert kwargs["api_id"] == "ka00198"
        assert kwargs["payload"]["qry_tp"] == "5"
        return [
            {
                "item_inq_rank": [
                    {
                        "stk_cd": "005930",
                        "stk_nm": "삼성전자",
                        "past_curr_prc": "+72000",
                        "base_comp_chgr": "+1.25",
                        "prev_base_chgr": "+0.35",
                        "bigd_rank": "7",
                        "rank_chg": "12",
                        "rank_chg_sign": "+",
                    }
                ]
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows = kiwoom_utils.get_realtime_item_rank_ka00198("TOKEN", qry_tp="5", limit=10)

    assert rows == [
        {
            "Code": "005930",
            "Name": "삼성전자",
            "Price": 72000,
            "FluRate": 1.25,
            "RealtimeRankFluRate": 1.25,
            "RealtimePrevBaseChange": 0.35,
            "RankNow": 7,
            "RankChange": 12,
            "RankChangeSign": "+",
            "RealtimeRankWindow": "5",
            "Source": "REALTIME_RANK_START",
        }
    ]


def test_ka10019_price_jump_start_preserves_jump_metrics(monkeypatch):
    def fake_fetch(**kwargs):
        assert kwargs["api_id"] == "ka10019"
        assert kwargs["payload"]["flu_tp"] == "1"
        assert kwargs["payload"]["tm"] == "3"
        return [
            {
                "pric_jmpflu": [
                    {
                        "stk_cd": "005930",
                        "stk_nm": "삼성전자",
                        "cur_prc": "+72000",
                        "flu_rt": "+1.75",
                        "jmp_rt": "+0.62",
                        "trde_qty": "123456",
                        "pred_pre_sig": "2",
                    }
                ]
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows = kiwoom_utils.get_price_jump_ka10019("TOKEN", minutes=3, limit=10)

    assert len(rows) == 1
    assert rows[0]["Code"] == "005930"
    assert rows[0]["Price"] == 72000
    assert rows[0]["FluRate"] == 1.75
    assert rows[0]["JumpRate"] == 0.62
    assert rows[0]["TradeQty"] == 123456
    assert rows[0]["PreSig"] == "2"
    assert rows[0]["Source"] == "PRICE_JUMP_START"


def test_ka10023_positive_volume_surge_filters_non_positive(monkeypatch):
    monkeypatch.setattr(
        kiwoom_utils,
        "scan_volume_spike_ka10023",
        lambda *args, **kwargs: [
            {"Code": "000001", "Name": "NEG", "Price": 10000, "FluRate": -0.1, "PreSig": "2"},
            {"Code": "000002", "Name": "BAD_SIG", "Price": 10000, "FluRate": 0.4, "PreSig": "5"},
            {"Code": "000003", "Name": "POS", "Price": 10000, "FluRate": 0.8, "PreSig": "2"},
        ],
    )

    rows = kiwoom_utils.get_positive_volume_surge_ka10023("TOKEN", limit=10)

    assert [row["Code"] for row in rows] == ["000003"]
    assert rows[0]["Source"] == "VOLUME_SURGE_POSITIVE"


def test_ka10021_bid_balance_surge_is_normalized(monkeypatch):
    def fake_fetch(**kwargs):
        assert kwargs["api_id"] == "ka10021"
        assert kwargs["payload"]["trde_tp"] == "1"
        assert kwargs["payload"]["tm_tp"] == "1"
        assert kwargs["payload"]["tm"] == "3"
        return [
            {
                "bid_req_sdnin": [
                    {
                        "stk_cd": "005930",
                        "stk_nm": "삼성전자",
                        "cur_prc": "+72000",
                        "flu_rt": "+1.1",
                        "sdnin_qty": "50000",
                        "sdnin_rt": "95.5",
                        "tot_buy_qty": "321000",
                        "pred_pre_sig": "2",
                    }
                ]
            }
        ]

    monkeypatch.setattr(kiwoom_utils, "fetch_kiwoom_api_continuous", fake_fetch)

    rows = kiwoom_utils.get_bid_balance_surge_ka10021("TOKEN", minutes=3, limit=10)

    assert len(rows) == 1
    assert rows[0]["Code"] == "005930"
    assert rows[0]["Price"] == 72000
    assert rows[0]["FluRate"] == 1.1
    assert rows[0]["BidSurgeQty"] == 50000
    assert rows[0]["BidSurgeRate"] == 95.5
    assert rows[0]["TotalBuyQty"] == 321000
    assert rows[0]["Source"] == "BID_IMBALANCE_SURGE"


def test_vi_triggered_without_primary_source_is_secondary_only_block(monkeypatch):
    emitted = []
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        scalping_scanner,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    pool = scalping_scanner.build_candidate_pool(
        vi_targets=[
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": 72000,
                "FluRate": 2.5,
                "ViFluRate": 2.5,
                "ViOpenFluRate": 2.5,
                "ViFluRateMetric": "vi_open_flu_rate",
            }
        ]
    )

    target = pool["005930"]
    codes, recent = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        {},
        max_new_codes=1,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1000.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert db.records == []
    assert recent["005930"]["last_guard_block_reason"] == "vi_secondary_confirmation_only"
    assert emitted[0]["fields"]["scanner_candidate_role"] == "late_confirmation"
    assert emitted[0]["fields"]["scanner_block_reason"] == "vi_secondary_confirmation_only"


def test_candidate_pool_preserves_vi_flu_metric():
    pool = scalping_scanner.build_candidate_pool(
        vi_targets=[
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": 72000,
                "FluRate": 2.5,
                "ViFluRate": 2.5,
                "ViOpenFluRate": 2.5,
                "ViDynamicDisparityRate": 1.2,
                "ViStaticDisparityRate": 3.4,
                "ViFluRateMetric": "vi_open_flu_rate",
            }
        ]
    )

    target = pool["005930"]
    assert target["ViFluRate"] == 2.5
    assert target["ViOpenFluRate"] == 2.5
    assert target["ViDynamicDisparityRate"] == 1.2
    assert target["ViStaticDisparityRate"] == 3.4
    assert target["ScannerFluRateMetric"] == "vi_open_flu_rate"
    assert target["ScannerFluRateSource"] == "VI_TRIGGERED"


def test_freshness_score_does_not_treat_vi_disparity_as_flu_acceleration():
    base = {
        "Code": "005930",
        "Name": "삼성전자",
        "Price": 72000,
        "Source": "VI_TRIGGERED",
        "SourceSet": {"VI_TRIGGERED"},
        "VIMotionCount": 1,
        "PriorityScore": 0.0,
        "SpikeRate": 0.0,
        "TradeValue": 0,
        "CntrStr": 0.0,
    }
    open_rate_target = {
        **base,
        "ViFluRate": 10.0,
        "ViFluRateMetric": "vi_open_flu_rate",
    }
    disparity_target = {
        **base,
        "ViFluRate": 10.0,
        "ViFluRateMetric": "vi_dynamic_disparity_rate",
    }

    assert scalping_scanner._freshness_score(open_rate_target) - scalping_scanner._freshness_score(disparity_target) == 80.0


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


def test_candidate_pool_keeps_source_specific_flu_rate_for_late_probe():
    pool = scalping_scanner.build_candidate_pool(
        soaring_targets=[
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": 70000,
                "OpenFluRate": 2.0,
                "FluRate": 2.0,
                "DayFluRate": 15.0,
            }
        ],
        value_targets=[
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": 70000,
                "FluRate": 15.0,
                "TradeValue": 50000000000,
            }
        ],
    )

    target = pool["005930"]

    assert target["SourceSet"] == {"OPEN_TOP", "VALUE_TOP"}
    assert target["OpenFluRate"] == 2.0
    assert target["ValueFluRate"] == 15.0
    assert target["FluRate"] == 2.0
    assert target["ScannerFluRateMetric"] == "open_flu_rate"
    assert target["ScannerFluRateSource"] == "OPEN_TOP"


def test_candidate_pool_recomputes_open_flu_rate_after_later_source_updates_price():
    pool = scalping_scanner.build_candidate_pool(
        soaring_targets=[
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": 10200,
                "OpenPrice": 10000,
                "OpenFluRate": 2.0,
                "FluRate": 2.0,
            }
        ],
        value_targets=[
            {
                "Code": "005930",
                "Name": "삼성전자",
                "Price": 10100,
                "FluRate": 15.0,
                "TradeValue": 50000000000,
            }
        ],
    )

    target = pool["005930"]

    assert target["Price"] == 10100
    assert target["OpenPrice"] == 10000
    assert target["OpenFluRate"] == 1.0
    assert target["ValueFluRate"] == 15.0
    assert target["FluRate"] == 1.0
    assert target["ScannerFluRateMetric"] == "open_flu_rate"


def test_value_top_without_primary_source_is_liquidity_only_block(monkeypatch):
    emitted = []
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        scalping_scanner,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
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

    assert codes == []
    assert event_bus.events == []
    assert db.records == []
    assert target["CntrStrAvailable"] is False
    assert emitted[0]["fields"]["scanner_filter_reason"] == "liquidity_only_source_not_seed"
    assert emitted[0]["fields"]["scanner_candidate_role"] == "liquidity_enrichment_only"


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
    assert capsys.readouterr().out == ""
    assert emitted
    assert [item["stage"] for item in emitted[:2]] == [
        "scalping_scanner_candidate_observed",
        "scalping_scanner_real_source_guard_block",
    ]
    event = emitted[1]
    assert event["pipeline"] == "ENTRY_PIPELINE"
    assert event["stage"] == "scalping_scanner_real_source_guard_block"
    assert event["fields"]["scanner_real_source_guard_applied"] is True
    assert event["fields"]["scanner_real_source_guard_skip_reason"] == "non_positive_liquidity_only_source"
    assert event["fields"]["scanner_real_source_guard_block_event_emitted"] is True
    assert event["fields"]["actual_order_submitted"] is False
    assert event["fields"]["broker_order_forbidden"] is True
    assert event["fields"]["decision_authority"] == "real_scalping_scanner_source_guard_only"


def test_real_source_guard_blocks_value_top_first_seen_as_probe(monkeypatch):
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
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    target = {
        "Code": "011070",
        "Name": "LG이노텍",
        "Price": 1082000,
        "FluRate": 8.4,
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
        {},
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1000.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert db.records == []
    assert recent["011070"]["scanner_probe_state"] == "first_seen_probe"
    assert recent["011070"]["first_price"] == 1082000
    assert [event["stage"] for event in emitted] == [
        "scalping_scanner_candidate_observed",
        "scalping_scanner_real_source_guard_block",
    ]
    assert emitted[0]["fields"]["scanner_candidate_role"] == "liquidity_enrichment_only"
    assert emitted[0]["fields"]["scanner_block_reason"] == "liquidity_only_source_not_seed"


def test_real_source_guard_blocks_open_top_first_seen_without_acceleration(monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        scalping_scanner,
        "TRADING_RULES",
        SimpleNamespace(
            SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED=True,
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY=True,
            SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT=0.0,
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    target = {
        "Code": "000001",
        "Name": "OPEN1",
        "Price": 10000,
        "FluRate": 4.0,
        "CntrStr": 0.0,
        "CntrStrAvailable": False,
        "Source": "OPEN_TOP",
        "SourceSet": {"OPEN_TOP"},
        "PriorityScore": 0.0,
        "SpikeRate": 0.0,
        "TradeValue": 0,
        "RankNow": 0,
        "RankPrev": 0,
    }

    codes, recent = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        {},
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1000.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert recent["000001"]["scanner_probe_state"] == "first_seen_probe"


def test_real_source_guard_promotes_probe_after_price_or_flu_acceleration(monkeypatch):
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
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "011070": {
            "scanner_probe_state": "first_seen_probe",
            "first_seen_at": 1000.0,
            "first_flu_rate": 4.0,
            "first_price": 10000,
            "last_source_signature": ("VALUE_TOP",),
            "last_score": 100.0,
        }
    }
    target = {
        "Code": "011070",
        "Name": "LG이노텍",
        "Price": 10020,
        "FluRate": 4.1,
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
        now_ts=1060.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert recent["011070"]["scanner_probe_state"] == "first_seen_probe"
    assert [event["stage"] for event in emitted] == [
        "scalping_scanner_candidate_observed",
        "scalping_scanner_real_source_guard_block",
    ]
    blocked_fields = emitted[0]["fields"]
    assert blocked_fields["scanner_block_reason"] == "liquidity_only_source_not_seed"
    assert blocked_fields["scanner_candidate_role"] == "liquidity_enrichment_only"
    assert blocked_fields["actual_order_submitted"] is False
    assert blocked_fields["broker_order_forbidden"] is True


def test_real_source_guard_reports_price_declined_even_when_flu_accelerated(monkeypatch):
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
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "477850": {
            "scanner_probe_state": "first_seen_probe",
            "first_seen_at": 1000.0,
            "first_flu_rate": 13.18,
            "first_price": 10000,
            "last_source_signature": ("OPEN_TOP",),
            "last_score": 100.0,
        }
    }
    target = {
        "Code": "477850",
        "Name": "마키나락스",
        "Price": 9990,
        "FluRate": 16.54,
        "CntrStr": 0.0,
        "CntrStrAvailable": False,
        "Source": "OPEN_TOP",
        "SourceSet": {"OPEN_TOP"},
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
        now_ts=1060.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert recent["477850"]["scanner_probe_state"] == "first_seen_probe"
    fields = emitted[0]["fields"]
    assert fields["scanner_block_reason"] == "late_confirmation_price_declined"
    assert fields["flu_delta_since_first_seen"] == "3.36"
    assert fields["price_delta_since_first_seen_pct"] == "-0.10"
    assert fields["probe_age_sec"] == "60.0"


def test_real_source_guard_reports_probe_expired_even_when_flu_accelerated(monkeypatch):
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
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "477850": {
            "scanner_probe_state": "first_seen_probe",
            "first_seen_at": 1000.0,
            "first_flu_rate": 13.18,
            "first_price": 10000,
            "last_source_signature": ("OPEN_TOP",),
            "last_score": 100.0,
        }
    }
    target = {
        "Code": "477850",
        "Name": "마키나락스",
        "Price": 10100,
        "FluRate": 16.54,
        "CntrStr": 0.0,
        "CntrStrAvailable": False,
        "Source": "OPEN_TOP",
        "SourceSet": {"OPEN_TOP"},
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
        now_ts=1401.0,
    )

    assert codes == []
    assert event_bus.events == []
    fields = emitted[0]["fields"]
    assert fields["scanner_block_reason"] == "late_confirmation_probe_expired"
    assert fields["flu_delta_since_first_seen"] == "3.36"
    assert fields["price_delta_since_first_seen_pct"] == "1.00"
    assert fields["probe_age_sec"] == "401.0"


def test_real_source_guard_does_not_promote_on_mixed_flu_metric_delta(monkeypatch):
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
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "005930": {
            "scanner_probe_state": "first_seen_probe",
            "first_seen_at": 1000.0,
            "first_flu_rate": 1.0,
            "first_flu_rate_metric": "day_flu_rate",
            "first_flu_rate_source": "VALUE_TOP",
            "first_price": 10000,
            "last_source_signature": ("VALUE_TOP",),
            "last_score": 100.0,
        }
    }
    target = {
        "Code": "005930",
        "Name": "삼성전자",
        "Price": 10000,
        "OpenFluRate": 5.0,
        "FluRate": 5.0,
        "CntrStr": 0.0,
        "CntrStrAvailable": False,
        "Source": "OPEN_TOP",
        "SourceSet": {"OPEN_TOP"},
        "PriorityScore": 0.0,
        "SpikeRate": 0.0,
        "TradeValue": 0,
        "RankNow": 0,
        "RankPrev": 0,
    }

    codes, recent = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        recent,
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1060.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert recent["005930"]["scanner_probe_state"] == "first_seen_probe"
    assert recent["005930"]["first_seen_at"] == 1060.0
    assert recent["005930"]["first_flu_rate"] == 5.0
    assert recent["005930"]["first_flu_rate_metric"] == "open_flu_rate"
    assert recent["005930"]["first_flu_rate_source"] == "OPEN_TOP"
    fields = emitted[0]["fields"]
    assert fields["scanner_block_reason"] == "late_confirmation_flu_metric_changed"
    assert fields["flu_delta_since_first_seen"] == "4.00"
    assert fields["comparable_flu_delta_since_first_seen"] == "0.00"
    assert fields["flu_metric_changed"] is True
    assert fields["first_flu_rate_metric"] == "day_flu_rate"
    assert fields["current_flu_rate_metric"] == "open_flu_rate"


def test_real_source_guard_strength_available_promotion_keeps_provenance(monkeypatch):
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
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "011070": {
            "scanner_probe_state": "first_seen_probe",
            "first_seen_at": 1000.0,
            "first_flu_rate": 4.0,
            "first_price": 10000,
            "last_source_signature": ("VALUE_TOP",),
            "last_score": 100.0,
        }
    }
    target = {
        "Code": "011070",
        "Name": "LG이노텍",
        "Price": 10010,
        "FluRate": 4.05,
        "CntrStr": 108.0,
        "CntrStrAvailable": True,
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
        now_ts=1060.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert recent["011070"]["scanner_probe_state"] == "first_seen_probe"
    assert [event["stage"] for event in emitted] == [
        "scalping_scanner_candidate_observed",
        "scalping_scanner_real_source_guard_block",
    ]
    blocked_fields = emitted[0]["fields"]
    assert blocked_fields["scanner_block_reason"] == "liquidity_only_source_not_seed"
    assert blocked_fields["scanner_candidate_role"] == "liquidity_enrichment_only"
    assert blocked_fields["actual_order_submitted"] is False
    assert blocked_fields["broker_order_forbidden"] is True


def test_real_source_guard_value_top_disabled_promotion_keeps_provenance(monkeypatch):
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
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY=False,
            SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT=0.0,
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    recent = {
        "011070": {
            "scanner_probe_state": "first_seen_probe",
            "first_seen_at": 1000.0,
            "first_flu_rate": 4.0,
            "first_price": 10000,
            "last_source_signature": ("VALUE_TOP",),
            "last_score": 100.0,
        }
    }
    target = {
        "Code": "011070",
        "Name": "LG이노텍",
        "Price": 10000,
        "FluRate": 4.0,
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

    codes, _ = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        recent,
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1060.0,
    )

    assert codes == []
    blocked_fields = emitted[0]["fields"]
    assert blocked_fields["scanner_block_reason"] == "liquidity_only_source_not_seed"
    assert blocked_fields["scanner_candidate_role"] == "liquidity_enrichment_only"
    assert blocked_fields["source_signature"] == "VALUE_TOP"


def test_real_source_guard_promotes_immediate_acceleration_sources(monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        scalping_scanner,
        "TRADING_RULES",
        SimpleNamespace(
            SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED=True,
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY=True,
            SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT=0.0,
            SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN=True,
            SCALP_SCANNER_ACCEL_MIN_RANK_JUMP=10,
            SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE=80.0,
            SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE=80.0,
            SCALP_SCANNER_ACCEL_MIN_CNTR_STR=110.0,
            SCALP_SCANNER_PROBE_MIN_SEC=30,
            SCALP_SCANNER_PROBE_MAX_SEC=300,
            SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT=0.15,
            SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT=0.30,
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    targets = [
        {
            "Code": "000101",
            "Name": "SUPERNOVA",
            "Price": 10000,
            "FluRate": 1.0,
            "CntrStr": 0.0,
            "CntrStrAvailable": False,
            "Source": "SUPERNOVA",
            "SourceSet": {"SUPERNOVA"},
            "PriorityScore": 0.0,
            "SpikeRate": 0.0,
            "TradeValue": 0,
            "RankNow": 0,
            "RankPrev": 0,
        },
        {
            "Code": "000102",
            "Name": "PRICEJUMP",
            "Price": 10000,
            "FluRate": 1.0,
            "CntrStr": 0.0,
            "CntrStrAvailable": False,
            "Source": "PRICE_JUMP_START",
            "SourceSet": {"PRICE_JUMP_START"},
            "PriorityScore": 0.0,
            "SpikeRate": 0.0,
            "JumpRate": 0.5,
            "TradeValue": 90000000000,
            "RankNow": 3,
            "RankPrev": 30,
        },
    ]

    codes, _ = scalping_scanner.promote_candidates(
        db,
        event_bus,
        targets,
        {},
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1000.0,
    )

    assert codes == ["000101", "000102"]
    assert event_bus.events == [("COMMAND_WS_REG", {"codes": ["000101", "000102"]})]


def test_real_source_guard_blocks_vi_value_without_primary_source(monkeypatch):
    emitted = []
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        scalping_scanner,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
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
    assert recent["005930"]["last_guard_block_reason"] == "vi_secondary_confirmation_only"
    assert emitted[0]["fields"]["scanner_candidate_role"] == "late_confirmation"
    assert emitted[0]["fields"]["scanner_block_reason"] == "vi_secondary_confirmation_only"


def test_promote_candidates_records_invalid_stock_filter_as_block(monkeypatch):
    emitted = []
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        scalping_scanner,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    db = _DB()
    event_bus = _EventBus()
    target = {
        "Code": "001930",
        "Name": "KODEX 삼성전자단일종목레버리지",
        "Price": 26540,
        "FluRate": 3.33,
        "CntrStr": 0.0,
        "CntrStrAvailable": False,
        "Source": "VOLUME_SURGE_POSITIVE",
        "SourceSet": {"VOLUME_SURGE_POSITIVE"},
        "PriorityScore": 0.0,
        "SpikeRate": 2.58,
        "TradeValue": 0,
        "RankNow": 0,
        "RankPrev": 0,
    }

    codes, recent = scalping_scanner.promote_candidates(
        db,
        event_bus,
        [target],
        {},
        max_new_codes=12,
        reentry_cooldown_sec=1500,
        token="TOKEN",
        now_ts=1000.0,
    )

    assert codes == []
    assert event_bus.events == []
    assert db.records == []
    assert recent["001930"]["last_guard_block_reason"] == "invalid_stock_filter"
    assert recent["001930"]["scanner_probe_state"] == "first_seen_probe"
    assert [event["stage"] for event in emitted] == [
        "scalping_scanner_candidate_observed",
        "scalping_scanner_real_source_guard_block",
    ]
    assert emitted[0]["fields"]["scanner_block_reason"] == "invalid_stock_filter"
    assert emitted[0]["fields"]["scanner_filter_reason"] == "invalid_stock_filter"
    assert emitted[0]["fields"]["actual_order_submitted"] is False
    assert emitted[0]["fields"]["broker_order_forbidden"] is True


def test_run_scalper_iteration_keeps_ws_payload_and_max_new_codes(monkeypatch):
    monkeypatch.setattr(kiwoom_utils, "is_valid_stock", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        kiwoom_utils,
        "get_realtime_item_rank_ka00198",
        lambda *args, **kwargs: [
            {"Code": f"00000{i}", "Name": f"RANK{i}", "Price": 10000 + i, "FluRate": 1.0}
            for i in range(5)
        ],
    )
    monkeypatch.setattr(kiwoom_utils, "get_price_jump_ka10019", lambda *args, **kwargs: [])
    monkeypatch.setattr(kiwoom_utils, "get_positive_volume_surge_ka10023", lambda *args, **kwargs: [])
    monkeypatch.setattr(kiwoom_utils, "get_bid_balance_surge_ka10021", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        kiwoom_utils,
        "get_top_open_fluctuation_ka10028",
        lambda *args, **kwargs: [],
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
        "get_realtime_item_rank_ka00198",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("timeout")),
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "get_price_jump_ka10019",
        lambda *args, **kwargs: [
            {"Code": "005930", "Name": "삼성전자", "Price": 70000, "FluRate": 1.2, "JumpRate": 0.5}
        ],
    )
    monkeypatch.setattr(kiwoom_utils, "get_positive_volume_surge_ka10023", lambda *args, **kwargs: [])
    monkeypatch.setattr(kiwoom_utils, "get_bid_balance_surge_ka10021", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        kiwoom_utils,
        "get_top_open_fluctuation_ka10028",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("timeout")),
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "get_value_top_ka10032",
        lambda *args, **kwargs: [],
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
    assert kiwoom_utils.get_realtime_item_rank_ka00198("TOKEN") == []
    assert kiwoom_utils.get_price_jump_ka10019("TOKEN") == []
    assert kiwoom_utils.get_bid_balance_surge_ka10021("TOKEN") == []
