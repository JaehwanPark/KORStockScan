"""Consumer-driven HTTP elimination and explicitly reduced entry inputs."""

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_radar_without_receiver_never_prepares_or_calculates(monkeypatch):
    from src.engine.signal_radar import SniperRadar

    radar = SniperRadar.__new__(SniperRadar)
    radar.event_bus = SimpleNamespace(has_subscribers=lambda event: False)
    monkeypatch.setattr(
        radar,
        "calculate_market_leader_score",
        lambda *a: pytest.fail("No receiver may consume this work"),
    )
    monkeypatch.setattr(
        radar,
        "_prepared_market_regime",
        lambda: pytest.fail("No source preparation without receiver"),
    )
    radar._on_realtime_tick({"code": "005930", "data": {"curr": 1000}})


@pytest.mark.parametrize("candidate", ["none", "tracked", "manual", "zero_qty"])
def test_recovery_without_eligible_holding_has_no_enrichment(monkeypatch, candidate):
    from src.engine import sniper_sync as sync

    query = SimpleNamespace(
        filter=lambda *a: SimpleNamespace(
            all=lambda: (
                [SimpleNamespace(stock_code="005930")] if candidate == "tracked" else []
            )
        )
    )
    session = SimpleNamespace(query=lambda *a: query)
    monkeypatch.setattr(sync, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(sync, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        sync,
        "resolve_symbol_owner_policy",
        lambda *a: SimpleNamespace(coexistence_enabled=False),
    )
    monkeypatch.setattr(
        sync,
        "default_order_owner_registry",
        lambda: SimpleNamespace(symbol_registered=lambda *a: False),
    )
    monkeypatch.setattr(
        sync,
        "evaluate_main_bot_control_exclusion",
        lambda *a, **kw: SimpleNamespace(excluded=candidate == "manual"),
    )
    monkeypatch.setattr(
        sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda *a: pytest.fail("No eligible recovery candidate"),
    )
    monkeypatch.setattr(
        sync.kiwoom_utils,
        "get_order_reference_snapshot_2nd_pass",
        lambda *a, **kw: pytest.fail("No eligible recovery candidate"),
    )
    holdings = (
        {}
        if candidate == "none"
        else {"005930": {"qty": 0 if candidate == "zero_qty" else 1}}
    )
    assert sync._recover_missing_broker_holdings(session, holdings) == 0


def test_real_recovery_candidates_share_one_enrichment_bundle(monkeypatch):
    from src.engine import sniper_sync as sync

    calls, records = [], []

    class Query:
        def filter(self, *args):
            return self

        def filter_by(self, **kwargs):
            return self

        def all(self):
            return []

    session = SimpleNamespace(
        query=lambda *a: Query(), add=records.append, flush=lambda: None
    )
    monkeypatch.setattr(sync, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(sync, "HIGHEST_PRICES", {})
    monkeypatch.setattr(sync, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(sync, "CONF", {"ENABLE_ORDER_REF_2ND_PASS": True})
    monkeypatch.setattr(
        sync,
        "resolve_symbol_owner_policy",
        lambda *a: SimpleNamespace(coexistence_enabled=False),
    )
    monkeypatch.setattr(
        sync,
        "default_order_owner_registry",
        lambda: SimpleNamespace(symbol_registered=lambda *a: False),
    )
    monkeypatch.setattr(
        sync,
        "evaluate_main_bot_control_exclusion",
        lambda *a, **kw: SimpleNamespace(excluded=False),
    )
    monkeypatch.setattr(
        sync.kiwoom_utils,
        "get_account_execution_snapshot_kt00008",
        lambda *a: calls.append("settlement") or [],
    )
    monkeypatch.setattr(
        sync.kiwoom_utils,
        "get_order_reference_snapshot_2nd_pass",
        lambda *a, **kw: calls.append("orders") or [],
    )
    monkeypatch.setattr(sync, "_ensure_runtime_target", lambda *a, **kw: {})
    monkeypatch.setattr(
        sync, "_publish_broker_recovered_buy_message", lambda *a, **kw: None
    )
    assert (
        sync._recover_missing_broker_holdings(
            session,
            {
                "005930": {"qty": 1, "buy_price": 1000},
                "034020": {"qty": 2, "buy_price": 2000},
            },
        )
        == 2
    )
    assert calls == ["settlement", "orders"]
    assert len(records) == 2 and all(r.buy_qty > 0 for r in records)


@pytest.mark.parametrize(
    "target,expected",
    [
        ({"status": "WATCHING", "buy_qty": 0}, False),
        ({"status": "HOLDING", "buy_qty": 1}, True),
        ({"status": "BUY_ORDERED"}, True),
        ({"status": "WATCHING", "buy_ord_no": "1"}, True),
        ({"status": "WATCHING", "buy_qty": "bad"}, True),
        ({"status": "WATCHING", "buy_qty": 0.1}, True),
        ({"status": "WATCHING", "buy_qty": "nan"}, True),
        ({}, True),
    ],
)
def test_optional_broker_poll_requires_actual_demand(monkeypatch, target, expected):
    from src.engine import kiwoom_sniper_v2 as main

    monkeypatch.setattr(
        main._reconcile_main_fixed_watch, "broker_refresh_needed", False, raising=False
    )
    assert main._periodic_broker_snapshot_required([target]) is expected
    monkeypatch.setattr(main._reconcile_main_fixed_watch, "broker_refresh_needed", True)
    assert main._periodic_broker_snapshot_required([]) is True


def test_reduced_rest_entry_requests_completed_window_only(monkeypatch):
    from src.engine.scalping import entry_candle_context as ctx
    from src.trading.market import shared_ws_snapshot as ws
    from src.utils import kiwoom_utils
    from src.tests.test_entry_candle_context import KST
    from datetime import datetime

    seen = []
    monkeypatch.setattr(ws, "selected_completed_bar_payload", lambda *a, **kw: None)
    monkeypatch.setattr(
        kiwoom_utils,
        "get_minute_candles_ka10080_with_meta",
        lambda *a, **kw: (seen.append(kw) or [], {}),
    )
    _, meta = ctx.fetch_entry_candles_with_meta(
        "token",
        "005930",
        {},
        venue="KRX",
        now_ts=datetime(2026, 10, 13, 10, tzinfo=KST),
        reduced_inputs=True,
    )
    assert seen[0]["limit"] == 61 and seen[0]["include_forming"] is False
    assert meta["decision_input_profile"] == "reduced_completed_v1"
    assert meta["multi_timeframe_auxiliary_fetch"] is False
    assert meta["complete_session_prefix"] is False


def test_partial_raw_ws_entry_does_not_query_rest_or_claim_full_session(
    tmp_path, monkeypatch
):
    from src.tests.test_micro_reversion_completed_bars import (
        BASE,
        INTEGRITY,
        point,
        bind,
    )
    from src.engine.scalping.micro_reversion.completed_bars import (
        CompletedBarProjection,
    )
    from src.trading.market import shared_ws_snapshot as reader
    from src.engine.scalping.entry_candle_context import fetch_entry_candles_with_meta
    from src.utils import kiwoom_utils

    p = CompletedBarProjection(tmp_path)
    now = BASE + timedelta(hours=1, seconds=2)
    p.consume(
        [point(1, 10), point(2, 60), point(3, 121), point(4, 3540), point(5, 3601)],
        integrity=INTEGRITY,
        journal_path="durable.jsonl",
        now_ts=now.timestamp(),
    )
    monkeypatch.setattr(reader, "COMPLETED_BARS_ROOT", tmp_path)
    monkeypatch.setattr(reader, "SNAPSHOT_PATH", bind(tmp_path, p, now))
    monkeypatch.setenv("KORSTOCKSCAN_MAIN_BAR_SOURCE", "ws_when_ready")
    monkeypatch.setenv("KORSTOCKSCAN_MAIN_BAR_WS_SYMBOLS", "005930")
    monkeypatch.setattr(
        kiwoom_utils,
        "get_minute_candles_ka10080_with_meta",
        lambda *a, **kw: pytest.fail("Valid partial raw WS rows require no REST"),
    )
    rows, meta = fetch_entry_candles_with_meta(
        "token",
        "005930_AL",
        {
            "market_suffix": "_AL",
            "market_route": "krx_nxt_integrated",
            "market_data_transport_epoch": 2,
        },
        venue="SOR",
        session="krx_nxt_aftermarket",
        now_ts=now,
        reduced_inputs=True,
    )
    assert rows and meta["api_id"] == "WS_0B_completed_1m"
    assert meta["complete_session_prefix"] is False
    assert meta["completed_bar_source"]["full_session_claimed"] is False
    assert all(r["_history_basis"] == "observed_valid_rows" for r in rows)
    with pytest.raises(ValueError, match="transport_changed"):
        fetch_entry_candles_with_meta(
            "token",
            "005930_AL",
            {
                "market_suffix": "_AL",
                "market_route": "krx_nxt_integrated",
                "market_data_transport_epoch": 3,
            },
            venue="SOR",
            session="krx_nxt_aftermarket",
            now_ts=now,
            reduced_inputs=True,
        )
    from src.engine.scalping.zero_base_probe import exact_probe_rest_source_issue

    assert (
        exact_probe_rest_source_issue(
            [],
            meta,
            request_code="005930_AL",
            now_epoch=now.timestamp(),
            allow_empty_ticks=True,
            transport_epoch=2,
        )
        == ""
    )
    assert (
        exact_probe_rest_source_issue(
            [],
            meta,
            request_code="005930_AL",
            now_epoch=now.timestamp(),
            allow_empty_ticks=True,
            transport_epoch=3,
        )
        == "candle_ws_provenance_invalid"
    )
    with pytest.raises(RuntimeError, match="live_binding_invalid"):
        reader.selected_completed_bar_payload(
            "005930_AL",
            now=now + timedelta(seconds=21),
            allow_partial_history=True,
            required_adjustment="raw_same_day",
        )


def test_reduced_context_has_no_forming_or_optional_network_sources(monkeypatch):
    from src.tests.test_entry_candle_context import _ws, _candles, KST
    from src.engine.scalping import entry_candle_context as ctx
    from src.engine.scalping import multi_timeframe_context as mtf
    from src.utils import kiwoom_utils
    from datetime import datetime

    monkeypatch.setattr(
        mtf, "_previous_day_source", lambda *a, **kw: pytest.fail("Optional fetch")
    )
    monkeypatch.setattr(
        mtf, "_index_context_source", lambda *a, **kw: pytest.fail("Optional fetch")
    )
    monkeypatch.setattr(
        kiwoom_utils,
        "get_investor_daily_ka10059_df",
        lambda *a, **kw: pytest.fail("Optional investor fetch"),
    )
    bars = _candles(12)
    now = datetime(2026, 7, 23, 10, 12, tzinfo=KST)
    ws = _ws()
    ws["recent_trade_ticks"] = [{"time": "10:12:00", "price": 999999, "volume": 1}]
    result = ctx.build_entry_candle_context(
        "token",
        "000660",
        ws,
        "KRX",
        "krx_regular",
        now_ts=now,
        recent_candles=bars,
        source_meta={
            "api_id": "ka10080",
            "decision_input_profile": "reduced_completed_v1",
            "complete_session_prefix": False,
            "multi_timeframe_auxiliary_fetch": True,
        },
    )
    assert result["forming_bar_present"] is False
    assert result["structure"]["session_high_at"] is None
    for field in ("session_bar_vwap", "opening_range_5m", "opening_range_15m"):
        row = result["multi_timeframe_context"][field]
        assert (
            row["value"] is None
            and row["reason"] == "full_session_history_not_required"
        )
    neutral = ctx.build_session_candle_source(
        "token",
        "000660",
        ws,
        "KRX",
        "krx_regular",
        now_ts=now,
        recent_candles=bars,
        source_meta={
            "api_id": "ka10080",
            "decision_input_profile": "reduced_completed_v1",
            "multi_timeframe_auxiliary_fetch": False,
        },
    )
    assert (
        "history_scope" not in neutral["structure"]
    )  # Holding/neutral consumer is not opted in.


def test_truncated_ws_window_does_not_claim_complete_session(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.trading.market import shared_ws_snapshot as ws
    from src.engine.scalping.entry_candle_context import fetch_entry_candles_with_meta

    start = datetime(2026, 10, 13, 9, tzinfo=ZoneInfo("Asia/Seoul"))
    rows = [
        dict(
            cntr_tm=(start + timedelta(minutes=i)).strftime("%Y%m%d%H%M%S"),
            open_pric="100",
            high_pric="110",
            low_pric="90",
            cur_prc="100",
            trde_qty="1",
        )
        for i in range(100)
    ]
    monkeypatch.setattr(
        ws,
        "selected_completed_bar_payload",
        lambda *a, **kw: {
            "stk_min_pole_chart_qry": rows,
            "_completed_bar_source": {
                "complete_session_prefix": True,
                "transport_epoch": 2,
            },
        },
    )
    selected, meta = fetch_entry_candles_with_meta(
        "token",
        "005930_AL",
        {
            "market_suffix": "_AL",
            "market_route": "krx_nxt_integrated",
            "market_data_transport_epoch": 2,
        },
        venue="SOR",
        session="krx_regular",
        now_ts=start + timedelta(hours=2),
        reduced_inputs=True,
    )
    assert len(selected) == 61 and meta["complete_session_prefix"] is False


def test_scheduled_census_disables_optional_executable_quotes():
    source = Path("deploy/run_market_opportunity_census_intraday.sh").read_text()
    capture = source.split("capture_cmd=(", 1)[1].split("\n)", 1)[0]
    assert "--skip-executable-bbo" in capture


@pytest.mark.parametrize("signal", [False, True])
def test_native_probe_spends_sources_only_after_signal(monkeypatch, signal):
    import time
    from src.engine.scalping import zero_base_probe as probe
    from src.engine.scalping import reversal_source_diagnostics as diagnostics
    from src.engine.scalping import reversal_current_backend as backend
    from src.tests.test_zero_base_probe import _snapshot

    stamp = time.time()
    raw = _snapshot(route="krx_nxt_integrated", item="005930_AL", epoch=stamp)
    ws_data, reason = probe.exact_probe_ws_data(
        raw,
        code="005930",
        route="krx_nxt_integrated",
        after_epoch=stamp,
        now_epoch=stamp,
    )
    assert reason == "ready"
    calls = []
    monkeypatch.setattr(
        probe, "wait_for_exact_probe_ws_data", lambda *a, **kw: (ws_data, {}, "ready")
    )
    monkeypatch.setattr(diagnostics, "branch_readiness", lambda *a, **kw: {})
    monkeypatch.setattr(diagnostics, "observation_sequence", lambda *a: 1)
    monkeypatch.setattr(
        backend, "backend", lambda: SimpleNamespace(_GENERATION="family")
    )

    def observe(*args, **kwargs):
        calls.append("native")
        return ([{"epoch": stamp}] if signal else None), {
            "status": "no_match",
            "reason": "no_match",
        }

    monkeypatch.setattr(diagnostics, "observe_snapshot", observe)

    def candles(*args, **kwargs):
        assert calls == ["native"]
        assert kwargs["reduced_inputs"] is True
        calls.append("candles")
        return [{"close": 1000}], {
            "request_code": "005930_AL",
            "rest_received_ts_ms": int(stamp * 1000),
        }

    def ticks(*args, **kwargs):
        assert calls == ["native", "candles"]
        calls.append("ticks")
        return [{"request_code": "005930_AL", "rest_received_ts_ms": int(stamp * 1000)}]

    def machine(*args, **kwargs):
        calls.append("machine")
        return {"entry_mechanistic_action": "BLOCK"}

    result = probe.run_zero_base_probe(
        {
            "claim": {
                "code": "005930",
                "route": "krx_nxt_integrated",
                "observed_epoch": stamp,
            },
            "candidate": {"code": "005930", "route": "krx_nxt_integrated"},
        },
        ws_manager=SimpleNamespace(
            subscribed_codes={"005930"},
            _registered_items_by_code={"005930": ("005930_AL",)},
            get_latest_data=lambda *a: raw,
        ),
        ai_engine=SimpleNamespace(analyze_target=machine),
        token="token",
        now=lambda: stamp,
        native_wait_deadline_epoch=stamp,
        candle_fetcher=candles,
        tick_fetcher=ticks,
        context_builder=lambda *a, **kw: {},
    )
    assert calls == (
        ["native", "candles", "ticks", "machine"] if signal else ["native"]
    )
    assert result["actual_order_submitted"] is False


def test_census_keeps_rank_observation_without_optional_bbo_requests():
    from src.engine.monitoring import market_opportunity_census as census
    from datetime import datetime

    records = census.capture_market_snapshots(
        "token",
        target_date="2026-10-13",
        captured_at=datetime.fromisoformat("2026-10-13T10:00:00+09:00"),
        venues=("KRX",),
        panels=("all",),
        collect_executable_bbo=False,
        fetcher=lambda *a, **kw: (
            [
                {
                    "Code": "005930",
                    "Name": "TEST",
                    "Price": 1000,
                    "ChangeRate": 1.0,
                    "Volume": 1000,
                }
            ],
            {},
        ),
        bbo_fetcher=lambda *a, **kw: pytest.fail("Observation BBO is disabled"),
        bbo_request_reserver=lambda: pytest.fail("No unused BBO reservation"),
    )
    assert len(records) == 1 and records[0]["row_count"] == 1


@pytest.mark.parametrize("forming,expected_requests", [(False, 1), (True, 4)])
def test_completed_rest_revision_reuses_across_short_cache_expiry(
    tmp_path, monkeypatch, forming, expected_requests
):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.utils import kiwoom_utils as utils

    base = datetime(2026, 10, 13, 10, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    clock = [base.timestamp() + 1]
    calls = []
    monkeypatch.setattr(utils, "DATA_DIR", tmp_path)
    monkeypatch.setattr(utils.time, "time", lambda: clock[0])
    monkeypatch.setattr(
        utils, "_market_data_cache_scope", lambda token: ("test", "isolated")
    )
    monkeypatch.setattr(utils, "_cache_get", lambda *a: None)
    monkeypatch.setattr(utils, "_cache_set", lambda name, key, value, ttl: value)
    rows = [
        dict(
            cntr_tm=(base - timedelta(minutes=i)).strftime("%Y%m%d%H%M%S"),
            open_pric="100",
            high_pric="110",
            low_pric="90",
            cur_prc="100",
            trde_qty="10",
        )
        for i in range(65)
    ]

    def fetch(**kwargs):
        calls.append(kwargs)
        return [{"stk_min_pole_chart_qry": rows}], {
            "rest_received_ts_ms": int(clock[0] * 1000),
            "request_code": "005930_AL",
            "read_rate_control_status": "admitted",
        }

    monkeypatch.setattr(utils, "_fetch_kiwoom_api_continuous_with_meta", fetch)
    for seconds in [1, 7, 13, 19]:
        clock[0] = base.timestamp() + seconds
        selected, meta = utils.get_minute_candles_ka10080_with_meta(
            "test",
            "005930_AL",
            limit=61,
            explicit_request_code=True,
            base_dt="20261013",
            include_forming=forming,
        )
        assert len(selected) == 61
        if not forming:
            assert all(r["source_timestamp"] < "20261013103000" for r in selected)
    assert len(calls) == expected_requests
    clock[0] = base.timestamp() + 61
    utils.get_minute_candles_ka10080_with_meta(
        "test",
        "005930_AL",
        limit=61,
        explicit_request_code=True,
        base_dt="20261013",
        include_forming=forming,
    )
    assert len(calls) == expected_requests + 1  # New completed cutoff must refresh.
