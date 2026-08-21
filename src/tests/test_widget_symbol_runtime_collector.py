from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from src.engine.monitoring.samsung_widget_advisory import MinuteBar
from src.engine.monitoring.samsung_widget_advisory import ExternalPoint
from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.monitoring import widget_symbol_runtime_contract as runtime_contract
from src.engine.monitoring.widget_symbol_runtime_collector import (
    CACHE_BOUNDARY_REQUEST_CAPACITY,
    CONTRACTS,
    EpisodeState,
    REQUESTS_PER_MINUTE,
    WidgetSymbolRuntimeCollector,
    _advance_support_break_count,
    _source_quality,
)
from src.engine.monitoring.widget_auxiliary_context import (
    WIDGET_SYMBOL_AUXILIARY_PROFILES,
)


def _bar(minute: int, open_: int, high: int, low: int, close: int, volume: int):
    return MinuteBar(
        source_time=f"2026081211{minute:02d}00",
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def test_entry_candidate_uses_symbol_policy_reclaim_completed_bar_and_fresh_bbo():
    bars = [_bar(index, 10_000, 10_010, 9_990, 10_000, 100) for index in range(30)]
    bars[-5] = _bar(25, 9_920, 9_930, 9_900, 9_910, 100)
    bars[-4] = _bar(26, 9_910, 9_920, 9_890, 9_900, 100)
    bars[-3] = _bar(27, 9_970, 9_980, 9_900, 9_920, 100)
    bars[-2] = _bar(28, 9_920, 9_950, 9_910, 9_940, 100)
    bars[-1] = _bar(29, 9_940, 9_960, 9_930, 9_950, 150)
    policy = {
        "signal_policy": {
            "segment_start_time": "10:30:00",
            "segment_end_time": "13:30:00",
            "lookback_bars": 15,
            "drawdown_pct": 0.5,
            "near_low_pct": 0.5,
            "reclaim_ticks": 1,
            "setup_valid_bars": 5,
            "target_bps": 50,
        }
    }

    candidate = WidgetSymbolRuntimeCollector._entry_candidate(
        bars=bars,
        current_price=9_950,
        bbo={"best_bid": 9_940, "best_ask": 9_950, "age_sec": 1.0},
        policy=policy,
        episode=EpisodeState(trade_date="2026-08-12"),
        observed_at=datetime(2026, 8, 12, 11, 30, tzinfo=KST),
    )

    assert candidate is not None
    assert candidate["state"] == "ENTRY_READY"
    assert candidate["structural_support"] == 9_900
    assert candidate["entry_price_low"] <= candidate["entry_price_high"]


def test_entry_candidate_blocks_stale_or_wide_bbo_and_active_episode():
    bars = [_bar(index, 10_000, 10_010, 9_990, 10_000, 100) for index in range(30)]
    policy = {
        "signal_policy": {
            "segment_start_time": "10:30:00",
            "segment_end_time": "13:30:00",
            "lookback_bars": 15,
            "drawdown_pct": 0.5,
            "near_low_pct": 0.5,
            "reclaim_ticks": 1,
            "setup_valid_bars": 5,
            "target_bps": 50,
        }
    }
    now = datetime(2026, 8, 12, 11, 30, tzinfo=KST)

    assert (
        WidgetSymbolRuntimeCollector._entry_candidate(
            bars=bars,
            current_price=10_000,
            bbo={"best_bid": 9_900, "best_ask": 10_000, "age_sec": 36.0},
            policy=policy,
            episode=EpisodeState(trade_date="2026-08-12"),
            observed_at=now,
        )
        is None
    )
    active = EpisodeState(trade_date="2026-08-12", active=True)
    assert (
        WidgetSymbolRuntimeCollector._entry_candidate(
            bars=bars,
            current_price=10_000,
            bbo={"best_bid": 9_990, "best_ask": 10_000, "age_sec": 1.0},
            policy=policy,
            episode=active,
            observed_at=now + timedelta(seconds=1),
        )
        is None
    )


def test_entry_evaluation_can_use_partial_early_history_when_policy_calibrated_it():
    bars = [_bar(index, 10_000, 10_010, 9_990, 10_000, 100) for index in range(12)]
    bars[-4] = _bar(8, 9_950, 9_960, 9_900, 9_910, 100)
    bars[-3] = _bar(9, 9_910, 9_920, 9_890, 9_900, 100)
    bars[-2] = _bar(10, 9_900, 9_940, 9_900, 9_930, 100)
    bars[-1] = _bar(11, 9_930, 9_960, 9_920, 9_950, 150)
    policy = {
        "signal_policy": {
            "segment_start_time": "10:30:00",
            "segment_end_time": "13:30:00",
            "lookback_bars": 15,
            "minimum_history_bars": 8,
            "anchor_mode": "rolling",
            "drawdown_pct": 0.5,
            "near_low_pct": 0.5,
            "reclaim_ticks": 1,
            "setup_valid_bars": 5,
            "target_bps": 50,
        }
    }

    candidate, diagnostic = WidgetSymbolRuntimeCollector._entry_evaluation(
        bars=bars,
        current_price=9_950,
        bbo={"best_bid": 9_940, "best_ask": 9_950, "age_sec": 1.0},
        policy=policy,
        episode=EpisodeState(trade_date="2026-08-12"),
        observed_at=datetime(2026, 8, 12, 11, 12, tzinfo=KST),
    )

    assert candidate is not None
    assert diagnostic["first_blocker"] is None
    assert diagnostic["minimum_history_bars"] == 8
    assert diagnostic["runtime_effect"] is False


def test_entry_evaluation_reports_drawdown_as_first_policy_blocker():
    bars = [_bar(index, 10_000, 10_010, 9_990, 10_000, 100) for index in range(30)]
    policy = {
        "signal_policy": {
            "segment_start_time": "10:30:00",
            "segment_end_time": "13:30:00",
            "lookback_bars": 15,
            "drawdown_pct": 2.0,
            "near_low_pct": 0.5,
            "reclaim_ticks": 1,
            "setup_valid_bars": 5,
            "target_bps": 50,
        }
    }

    candidate, diagnostic = WidgetSymbolRuntimeCollector._entry_evaluation(
        bars=bars,
        current_price=10_000,
        bbo={"best_bid": 9_990, "best_ask": 10_000, "age_sec": 1.0},
        policy=policy,
        episode=EpisodeState(trade_date="2026-08-12"),
        observed_at=datetime(2026, 8, 12, 11, 30, tzinfo=KST),
    )

    assert candidate is None
    assert diagnostic["first_blocker"] == "drawdown_below_threshold"
    assert diagnostic["best_observed_drawdown_pct"] == 0.0999
    assert diagnostic["actual_order_submitted"] is False


def test_support_break_confirmation_advances_once_per_completed_bar():
    episode = EpisodeState(trade_date="2026-08-12", active=True, support=10_000)
    first = _bar(28, 9_990, 10_000, 9_980, 9_990, 100)
    second = _bar(29, 9_980, 9_990, 9_970, 9_980, 100)

    _advance_support_break_count(episode, first)
    _advance_support_break_count(episode, first)
    assert episode.support_break_count == 1

    _advance_support_break_count(episode, second)
    assert episode.support_break_count == 2


def test_source_quality_blocks_stale_completed_bar_or_missing_bbo():
    now = datetime(2026, 8, 12, 11, 30, 30, tzinfo=KST)
    fresh = _bar(29, 9_980, 9_990, 9_970, 9_980, 100)

    assert _source_quality(
        latest=fresh,
        bbo={"best_bid": 9_970, "best_ask": 9_980, "age_sec": 0.0},
        observed_at=now,
    ) == ("PASS", ())
    status, reasons = _source_quality(
        latest=_bar(20, 9_980, 9_990, 9_970, 9_980, 100),
        bbo={"best_bid": None, "best_ask": None, "age_sec": 40.0},
        observed_at=now,
    )
    assert status == "BLOCKED"
    assert set(reasons) == {"completed_1m_stale", "bbo_invalid", "bbo_stale"}


def test_all_new_widget_symbols_have_market_specific_auxiliary_profiles():
    assert set(WIDGET_SYMBOL_AUXILIARY_PROFILES) == {
        "006800",
        "010140",
        "080220",
        "475150",
    }
    assert WIDGET_SYMBOL_AUXILIARY_PROFILES["080220"].market_index_code == "101"
    assert WIDGET_SYMBOL_AUXILIARY_PROFILES["080220"].market_index_name == (
        "KOSDAQ_101"
    )
    assert all(
        profile.peer_symbol != symbol
        for symbol, profile in WIDGET_SYMBOL_AUXILIARY_PROFILES.items()
    )


def test_shared_market_payload_fetches_each_index_only_once_per_minute():
    class Client:
        def __init__(self):
            self.calls = []

        def post(self, path, api_id, payload, *, optional=False):
            self.calls.append((path, api_id, payload, optional))
            return {"inds_min_pole_qry": []}

    collector = WidgetSymbolRuntimeCollector()
    client = Client()
    now = datetime(2026, 8, 12, 11, 30, 5, tzinfo=KST)

    collector._shared_market_payload(client=client, index_code="001", observed_at=now)
    collector._shared_market_payload(
        client=client, index_code="001", observed_at=now + timedelta(seconds=20)
    )
    collector._shared_market_payload(
        client=client, index_code="101", observed_at=now + timedelta(seconds=20)
    )

    assert [call[2]["inds_cd"] for call in client.calls] == ["001", "101"]
    assert all(call[1] == "ka20005" and call[3] is True for call in client.calls)


def test_runtime_collector_budget_covers_four_symbol_cache_boundary_burst():
    collector = WidgetSymbolRuntimeCollector()

    assert REQUESTS_PER_MINUTE == 64
    assert REQUESTS_PER_MINUTE > CACHE_BOUNDARY_REQUEST_CAPACITY
    assert collector.request_budget.max_requests_per_minute == REQUESTS_PER_MINUTE


def test_collect_once_isolates_source_failure_and_rotates_first_symbol(monkeypatch):
    collector = WidgetSymbolRuntimeCollector()
    now = datetime(2026, 8, 12, 11, 30, 5, tzinfo=KST)
    collector._policies = {
        "006800": {"policy_id": "A"},
        "010140": {"policy_id": "B"},
    }
    monkeypatch.setattr(collector, "_activate_date", lambda _now: None)
    monkeypatch.setattr(collector, "_client", lambda: object())
    calls: list[str] = []

    def collect_symbol(**kwargs):
        symbol = kwargs["symbol"]
        calls.append(symbol)
        if symbol == "006800":
            raise RuntimeError("widget_request_budget_exhausted")
        return {"status": "ok", "symbol": symbol}

    monkeypatch.setattr(collector, "_collect_symbol", collect_symbol)
    monkeypatch.setattr(
        collector,
        "_degraded_symbol_payload",
        lambda **kwargs: {
            "status": "data_wait",
            "symbol": kwargs["symbol"],
            "reason": kwargs["reason"],
        },
    )

    first = collector.collect_once(now)
    second = collector.collect_once(now + timedelta(seconds=15))

    assert first["status"] == "partial_data_wait"
    assert first["failures"] == {"006800": "request_budget_deferred"}
    assert first["symbols"]["010140"]["status"] == "ok"
    assert calls == ["006800", "010140", "010140", "006800"]
    assert second["status"] == "partial_data_wait"


def test_degraded_symbol_payload_clears_actionable_events(monkeypatch, tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    monkeypatch.setitem(
        CONTRACTS,
        "999999",
        SimpleNamespace(
            name="test",
            STRATEGY_PROFILE="TEST_V1",
            DEFAULT_SNAPSHOT_PATH=snapshot_path,
        ),
    )
    collector = WidgetSymbolRuntimeCollector(observation_dir=tmp_path / "observations")
    now = datetime(2026, 8, 12, 11, 30, 5, tzinfo=KST)
    collector._active_date = now.date().isoformat()
    collector._episodes["999999"] = EpisodeState(trade_date=now.date().isoformat())

    payload = collector._degraded_symbol_payload(
        symbol="999999",
        policy={"policy_id": "POLICY", "effective_date": "2026-08-12"},
        observed_at=now,
        reason="request_budget_deferred",
    )

    assert payload["status"] == "data_wait"
    assert payload["advisory"]["state"] == "DATA_WAIT"
    assert payload["advisory"]["source_quality"]["status"] == "BLOCKED"
    assert (
        payload["advisory"]["entry_diagnostic"]["first_blocker"]
        == "source_quality_blocked"
    )
    assert payload["entry_event"] is None
    assert payload["exit_event"] is None
    assert payload["actual_order_submitted"] is False
    assert payload["broker_order_forbidden"] is True
    assert snapshot_path.exists()


def test_new_symbol_snapshot_records_partial_flow_without_granting_signal_authority(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        runtime_contract, "DEFAULT_SNAPSHOT_DIR", tmp_path / "snapshots"
    )
    now = datetime(2026, 8, 12, 11, 30, 5, tzinfo=KST)

    class Client:
        def __init__(self):
            self.calls = []

        def post(self, _path, api_id, payload, *, optional=False):
            self.calls.append((api_id, payload, optional))
            if api_id == "ka10001":
                return {"cur_prc": "10000"}
            if api_id == "ka10004":
                return {
                    "buy_fpr_bid": "9990",
                    "sel_fpr_bid": "10000",
                    "buy_fpr_req": "1000",
                    "sel_fpr_req": "900",
                }
            if api_id in {"ka10080", "ka20005"}:
                key = (
                    "stk_min_pole_chart_qry"
                    if api_id == "ka10080"
                    else "inds_min_pole_qry"
                )
                return {
                    key: [
                        {
                            "cntr_tm": (
                                datetime(2026, 8, 12, 11, 0, tzinfo=KST)
                                + timedelta(minutes=index)
                            ).strftime("%Y%m%d%H%M%S"),
                            "open_pric": "10000",
                            "high_pric": "10010",
                            "low_pric": "9990",
                            "cur_prc": str(10000 + index),
                            "trde_qty": "1000",
                        }
                        for index in range(30)
                    ]
                }
            if api_id == "ka10064":
                return {
                    "opmr_invsr_trde_chart": [
                        {"tm": "105900", "frgnr_invsr": "-100"},
                        {"tm": "110000", "frgnr_invsr": "-50"},
                    ]
                }
            if api_id == "ka90008":
                return {
                    "stk_tm_prm_trde_trnsn": [
                        {
                            "tm": "113000",
                            "prm_netprps_amt": "10",
                            "prm_netprps_amt_irds": "5",
                        }
                    ]
                }
            raise AssertionError(api_id)

    collector = WidgetSymbolRuntimeCollector(observation_dir=tmp_path / "observations")
    collector._active_date = now.date().isoformat()
    collector._episodes["080220"] = EpisodeState(trade_date=now.date().isoformat())
    point = ExternalPoint(
        "USDKRW",
        "KRW=X",
        1400.0,
        0.0,
        now.isoformat(),
        now.isoformat(),
        0.0,
        "test",
        "BEST_EFFORT_DELAYED",
        "OPEN",
    )
    monkeypatch.setattr(
        collector,
        "_shared_external_points",
        lambda _observed_at: ({"USDKRW": point}, []),
    )
    policy = {
        "policy_id": "POLICY",
        "effective_date": now.date().isoformat(),
        "signal_policy": {
            "segment_start_time": "13:30:00",
            "segment_end_time": "15:00:00",
            "lookback_bars": 15,
            "drawdown_pct": 1.0,
            "near_low_pct": 0.5,
            "reclaim_ticks": 1,
            "target_bps": 50,
            "setup_valid_bars": 5,
            "reentry_cooldown_bars": 10,
        },
    }

    payload = collector._collect_symbol(
        symbol="080220", policy=policy, client=Client(), observed_at=now
    )

    auxiliary = payload["advisory"]["auxiliary_context"]
    assert payload["status"] == "ok"
    assert payload["advisory"]["source_quality"]["status"] == "PASS"
    assert auxiliary["status"] == "OBSERVED_PARTIAL"
    assert auxiliary["market_index"] == "KOSDAQ_101"
    assert auxiliary["foreign_flow_status"] == "DELAYED_ESTIMATE"
    assert auxiliary["program_flow_status"] == "OBSERVED"
    assert auxiliary["flow_signal"] == "PROGRAM_NONWORSENING_FOREIGN_DELAYED"
    assert (
        "foreign_flow_delayed_estimate"
        in payload["advisory"]["auxiliary_unmet_conditions"]
    )
    assert payload["advisory"]["auxiliary_decision_authority"] == (
        "observation_only_no_entry_veto_or_positive_promotion"
    )
    assert payload["actual_order_submitted"] is False
    assert payload["broker_order_forbidden"] is True
