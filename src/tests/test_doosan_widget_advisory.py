from __future__ import annotations

from datetime import datetime, timedelta

from src.engine.monitoring import doosan_widget_advisory as doosan
from src.engine.monitoring import doosan_widget_contract as contract
from src.engine.monitoring.samsung_widget_advisory import (
    AdvisoryPromotionFilter,
    ExternalPoint,
)
from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.monitoring.widget_auxiliary_context import (
    DOOSAN_AUXILIARY_PROFILE,
    MIRAE_ASSET_AUXILIARY_PROFILE,
    WidgetAuxiliaryContextCollector,
    _combined_flow_status,
    _flow_component_status,
    attach_auxiliary_summary,
)


def _bars(
    closes: list[int], *, start: datetime | None = None, lows: list[int] | None = None
) -> list[doosan.MinuteBar]:
    start = start or datetime(2026, 8, 5, 9, 0, tzinfo=KST)
    result = []
    for index, close in enumerate(closes):
        open_price = close - 100 if index % 2 == 0 else close + 50
        result.append(
            doosan.MinuteBar(
                source_time=(start + timedelta(minutes=index)).strftime("%Y%m%d%H%M%S"),
                open=open_price,
                high=max(open_price, close) + 50,
                low=(lows[index] if lows else min(open_price, close) - 50),
                close=close,
                volume=1_500 if close > open_price else 1_000,
            )
        )
    return result


def _base_advisory(
    now: datetime,
    *,
    volume_mode: str = "standard_rebound",
    state: str = "ENTRY_CAUTION",
) -> dict:
    return {
        "state": state,
        "raw_state": state,
        "session": "KRX_REGULAR",
        "entry_price_low": 99_000,
        "entry_price_high": 99_100,
        "reasons": ["low_structure_confirmed"],
        "unmet_conditions": [],
        "observed_at": now.isoformat(),
        "valid_until": (now + timedelta(seconds=60)).isoformat(),
        "source_quality": {"status": "PASS", "issues": []},
        "auxiliary_context": {
            "status": "OBSERVED",
            "relative_status": "OBSERVED",
            "flow_status": "OBSERVED",
            "external_status": "OBSERVED",
            "positive_promotion_ready": True,
        },
        "external_risk": {"level": "CLEAR"},
        "flow": {
            "status": "OBSERVED",
            "live_for_current_session": True,
            "foreign_nonworsening": True,
            "program_nonworsening": True,
        },
        "signal_tier": "STANDARD",
        "doosan_policy": {"session_return_pct": -0.9},
        "derived": {
            "structural_support": 98_500,
            "confirmed_support": 98_500,
            "volume_confirmation_mode": volume_mode,
        },
        "provenance": {},
        "strategy_profile": contract.STRATEGY_PROFILE,
        "metric_contract": contract.METRIC_CONTRACT,
        "authority": "widget_advisory_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_doosan_policy_requires_half_percent_session_drawdown():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_900, 99_600])

    result = doosan.apply_doosan_entry_policy(
        _base_advisory(now),
        current_price=99_600,
        bars=bars,
        context=contract.session_context(now),
    )

    assert result["state"] == "WATCH"
    assert result["entry_price_low"] is None
    assert "doosan_session_drawdown_pending" in result["unmet_conditions"]


def test_doosan_policy_assigns_standard_and_high_confidence_tiers():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_500, 99_000])
    context = contract.session_context(now)

    standard = doosan.apply_doosan_entry_policy(
        _base_advisory(now),
        current_price=99_400,
        bars=bars,
        context=context,
    )
    high = doosan.apply_doosan_entry_policy(
        _base_advisory(now, state="ENTRY_READY"),
        current_price=98_900,
        bars=bars,
        context=context,
    )

    assert standard["state"] == "ENTRY_CAUTION"
    assert standard["signal_tier"] == "STANDARD"
    assert high["state"] == "ENTRY_READY"
    assert high["signal_tier"] == "HIGH"
    assert high["doosan_policy"]["session_return_pct"] <= -1.0
    assert "regular_flow_unavailable" not in high["unmet_conditions"]


def test_doosan_policy_keeps_absorption_recovery_in_watch():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    result = doosan.apply_doosan_entry_policy(
        _base_advisory(now, volume_mode="absorption_recovery"),
        current_price=98_500,
        bars=_bars([100_000, 99_000, 98_500]),
        context=contract.session_context(now),
    )

    assert result["state"] == "WATCH"
    assert "doosan_standard_rebound_volume_required" in result["unmet_conditions"]


def test_doosan_policy_blocks_shallow_pullback_after_extended_runup():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(now)
    source["derived"]["recent_runup_chase_guard"] = {
        "runup_pct": 0.90,
        "recent_high": 99_200,
        "recent_low": 98_300,
    }

    result = doosan.apply_doosan_entry_policy(
        source,
        current_price=99_000,
        bars=_bars([100_000, 99_300, 99_000]),
        context=contract.session_context(now),
    )

    assert result["state"] == "NO_CHASE"
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert result["reasons"] == ["doosan_extended_runup_pullback_too_shallow"]
    assert "doosan_three_tick_pullback_pending" in result["unmet_conditions"]
    assert result["doosan_policy"]["extended_runup_pullback_guard"] == {
        "applied": True,
        "runup_pct": 0.9,
        "trigger_pct": 0.7,
        "recent_high": 99_200,
        "minimum_pullback_ticks": 3,
        "maximum_entry_price": 98_900,
        "authority": "widget_advisory_only",
        "runtime_effect": False,
    }


def test_doosan_policy_allows_three_tick_pullback_after_extended_runup():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(now)
    source["entry_price_low"] = 98_900
    source["entry_price_high"] = 98_900
    source["derived"]["recent_runup_chase_guard"] = {
        "runup_pct": 0.90,
        "recent_high": 99_200,
        "recent_low": 98_300,
    }

    result = doosan.apply_doosan_entry_policy(
        source,
        current_price=98_900,
        bars=_bars([100_000, 99_300, 98_900]),
        context=contract.session_context(now),
    )

    assert result["state"] == "ENTRY_CAUTION"
    assert result["entry_price_low"] == 98_900
    assert result["entry_price_high"] == 98_900
    assert result["doosan_policy"]["extended_runup_pullback_guard"]["applied"] is False


def test_doosan_policy_blocks_borderline_runup_near_recent_high():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(now)
    source["derived"]["recent_runup_chase_guard"] = {
        "runup_pct": 0.7682,
        "recent_high": 78_800,
        "recent_low": 78_100,
    }

    result = doosan.apply_doosan_entry_policy(
        source,
        current_price=78_700,
        bars=_bars([79_500, 78_100, 78_700]),
        context=contract.session_context(now),
    )

    assert result["state"] == "NO_CHASE"
    assert result["entry_price_low"] is None
    assert result["entry_price_high"] is None
    assert result["doosan_policy"]["extended_runup_pullback_guard"] == {
        "applied": True,
        "runup_pct": 0.7682,
        "trigger_pct": 0.7,
        "recent_high": 78_800,
        "minimum_pullback_ticks": 3,
        "maximum_entry_price": 78_500,
        "authority": "widget_advisory_only",
        "runtime_effect": False,
    }


def test_high_tier_does_not_override_portable_recovery_caution():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(now)
    source["state"] = source["raw_state"] = "ENTRY_READY"
    source["derived"]["recovery_episode"] = {"support": 98_500}

    result = doosan.apply_doosan_entry_policy(
        source,
        current_price=98_500,
        bars=_bars([100_000, 99_000, 98_500]),
        context=contract.session_context(now),
    )

    assert result["signal_tier"] == "HIGH"
    assert result["state"] == "ENTRY_CAUTION"
    assert result["doosan_policy"]["base_caution_preserved"] is True


def test_doosan_signal_still_requires_two_ten_second_observations():
    first_at = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    first = doosan.apply_doosan_entry_policy(
        _base_advisory(first_at, state="ENTRY_READY"),
        current_price=98_500,
        bars=bars,
        context=contract.session_context(first_at),
    )
    second = doosan.apply_doosan_entry_policy(
        _base_advisory(first_at + timedelta(seconds=10), state="ENTRY_READY"),
        current_price=98_500,
        bars=bars,
        context=contract.session_context(first_at),
    )
    promotion = AdvisoryPromotionFilter()

    assert promotion.apply(first)["state"] == "WATCH"
    assert promotion.apply(second)["state"] == "ENTRY_READY"


def test_doosan_high_price_structure_is_capped_when_auxiliary_context_is_limited():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(now)
    source["auxiliary_context"]["status"] = "LIMITED"

    result = doosan.apply_doosan_entry_policy(
        source,
        current_price=98_500,
        bars=_bars([100_000, 99_000, 98_500]),
        context=contract.session_context(now),
    )

    assert result["state"] == "ENTRY_CAUTION"
    assert result["signal_tier"] == "STANDARD"
    assert "auxiliary_context_not_ready_for_high" in result["unmet_conditions"]


def test_auxiliary_gap_is_explicit_and_not_reported_as_supportive_relative_strength():
    advisory = {
        "reasons": ["relative_strength_not_weak", "low_structure_confirmed"],
        "unmet_conditions": [],
        "source_quality": {"status": "PASS", "issues": []},
        "provenance": {},
    }

    result = attach_auxiliary_summary(
        advisory,
        {
            "status": "LIMITED",
            "relative_status": "UNAVAILABLE",
            "flow_status": "PARTIAL",
            "external_status": "LIMITED",
            "context_version": "doosan_krx_auxiliary_context_v1",
        },
    )

    assert "relative_strength_not_weak" not in result["reasons"]
    assert "low_structure_confirmed" in result["reasons"]
    assert set(result["unmet_conditions"]) == {
        "relative_strength_unavailable",
        "regular_flow_unavailable",
        "external_context_data_limited",
    }
    assert result["source_quality"]["auxiliary_status"] == "LIMITED"
    assert result["auxiliary_context"]["relative_signal"] == "DATA_LIMITED"
    assert result["auxiliary_context"]["flow_signal"] == "DATA_LIMITED"
    assert result["auxiliary_context"]["external_risk_level"] == "DATA_LIMITED"
    assert result["provenance"]["auxiliary_context_version"] == (
        "doosan_krx_auxiliary_context_v1"
    )


def test_auxiliary_request_failures_remain_limited_without_blocking_core_collector():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)

    class FailingClient:
        def post(self, *_args, **_kwargs):
            raise RuntimeError("optional_market_data_failed")

    class FailingExternalProvider:
        def fetch(self, _observed_at):
            raise RuntimeError("optional_external_data_failed")

    collector = WidgetAuxiliaryContextCollector(
        DOOSAN_AUXILIARY_PROFILE,
        external_provider=FailingExternalProvider(),
    )
    result = collector.collect(
        client=FailingClient(),
        observed_at=now,
        context=contract.session_context(now),
        primary_bars=_bars(
            [100_000 - index * 10 for index in range(60)],
            start=datetime(2026, 8, 5, 9, 0, tzinfo=KST),
        ),
    )

    assert result["summary"]["status"] == "LIMITED"
    assert result["relative"]["authority"] == (
        "unavailable_neutral_no_positive_or_negative_authority"
    )
    assert result["flow"]["status"] == "UNAVAILABLE"
    assert result["external_points"] == {}
    assert {gap["source"] for gap in result["summary"]["optional_gaps"]} == {
        "ka10080",
        "ka20005",
        "ka10064",
        "ka90008",
        "USDKRW",
    }


def test_auxiliary_summary_preserves_fresh_program_when_foreign_source_is_stale():
    advisory = {
        "reasons": [],
        "unmet_conditions": ["regular_flow_unavailable"],
        "source_quality": {"status": "PASS", "issues": []},
        "provenance": {},
        "flow": {
            "status": "STALE",
            "foreign_nonworsening": False,
            "program_nonworsening": True,
        },
        "external_risk": {"level": "CLEAR"},
    }

    result = attach_auxiliary_summary(
        advisory,
        {
            "status": "LIMITED",
            "relative_status": "OBSERVED",
            "flow_status": "STALE",
            "foreign_flow_status": "STALE",
            "program_flow_status": "OBSERVED",
            "external_status": "OBSERVED",
            "context_version": "doosan_krx_auxiliary_context_v1",
        },
    )

    assert result["auxiliary_context"]["flow_signal"] == (
        "PROGRAM_NONWORSENING_FOREIGN_LIMITED"
    )
    assert "regular_flow_unavailable" in result["unmet_conditions"]


def test_auxiliary_classifies_delayed_foreign_separately_from_fresh_program():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    primary_bars = _bars(
        [10_000 + index for index in range(60)],
        start=datetime(2026, 8, 5, 9, 0, tzinfo=KST),
    )

    class Client:
        def __init__(self):
            self.calls = []

        def post(self, _path, api_id, payload, *, optional=False):
            self.calls.append((api_id, payload, optional))
            if api_id == "ka10080":
                return {
                    "stk_min_pole_chart_qry": [
                        {
                            "cntr_tm": bar.source_time,
                            "open_pric": str(bar.open),
                            "high_pric": str(bar.high),
                            "low_pric": str(bar.low),
                            "cur_prc": str(bar.close),
                            "trde_qty": str(bar.volume),
                        }
                        for bar in primary_bars
                    ]
                }
            if api_id == "ka10064":
                return {
                    "opmr_invsr_trde_chart": [
                        {"tm": "092900", "frgnr_invsr": "-100"},
                        {"tm": "093000", "frgnr_invsr": "-50"},
                    ]
                }
            if api_id == "ka90008":
                return {
                    "stk_tm_prm_trde_trnsn": [
                        {
                            "tm": "100000",
                            "prm_netprps_amt": "10",
                            "prm_netprps_amt_irds": "5",
                        }
                    ]
                }
            raise AssertionError(api_id)

    market_payload = {
        "inds_min_pole_qry": [
            {
                "cntr_tm": bar.source_time,
                "open_pric": str(bar.open),
                "high_pric": str(bar.high),
                "low_pric": str(bar.low),
                "cur_prc": str(bar.close),
                "trde_qty": str(bar.volume),
            }
            for bar in primary_bars
        ]
    }
    external = {
        "USDKRW": ExternalPoint(
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
    }
    client = Client()
    collector = WidgetAuxiliaryContextCollector(MIRAE_ASSET_AUXILIARY_PROFILE)
    result = collector.collect(
        client=client,
        observed_at=now,
        context=contract.session_context(now),
        primary_bars=primary_bars,
        market_payload=market_payload,
        external_points=external,
    )

    assert result["summary"]["status"] == "OBSERVED_PARTIAL"
    assert result["summary"]["flow_status"] == "OBSERVED_PARTIAL"
    assert result["summary"]["foreign_flow_status"] == "DELAYED_ESTIMATE"
    assert result["summary"]["program_flow_status"] == "OBSERVED"
    assert result["summary"]["positive_promotion_ready"] is False
    assert result["summary"]["negative_veto_ready"] is True
    assert result["summary"]["market_index"] == "KOSPI_001"
    assert {api_id for api_id, _, _ in client.calls} == {
        "ka10080",
        "ka10064",
        "ka90008",
    }

    advisory = attach_auxiliary_summary(
        {
            "reasons": [],
            "unmet_conditions": ["regular_flow_unavailable"],
            "source_quality": {"status": "PASS", "issues": []},
            "provenance": {},
            "flow": result["flow"],
            "external_risk": {"level": "CLEAR"},
        },
        result["summary"],
    )
    assert advisory["auxiliary_context"]["flow_signal"] == (
        "PROGRAM_NONWORSENING_FOREIGN_DELAYED"
    )
    assert "regular_flow_unavailable" not in advisory["unmet_conditions"]
    assert "foreign_flow_delayed_estimate" in advisory["unmet_conditions"]


def test_delayed_foreign_without_a_fresh_component_cannot_look_observed():
    assert (
        _flow_component_status(
            {"foreign_available": True, "foreign_source_age_sec": 1800}, "foreign"
        )
        == "DELAYED_ESTIMATE"
    )
    assert (
        _flow_component_status(
            {"foreign_available": True, "foreign_source_age_sec": 3601}, "foreign"
        )
        == "STALE"
    )
    assert _combined_flow_status("DELAYED_ESTIMATE", "STALE") == ("DELAYED_ESTIMATE")


def test_entry_linked_exit_uses_target_or_completed_close_not_intrabar_low():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = doosan.DoosanDailyEpisodeTracker()
    entry, exit_watch = tracker.apply(
        _base_advisory(now),
        observed_at=now,
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000, "best_ask": 99_100},
        source_quality={"status": "PASS", "issues": []},
    )
    assert entry["state"] == "ENTRY_CAUTION"
    assert exit_watch["state"] == "EXIT_WATCH"
    assert tracker.target_price == 100_100

    intrabar = _bars(
        [98_600],
        start=datetime(2026, 8, 5, 9, 3, tzinfo=KST),
        lows=[98_000],
    )[0]
    _, still_watch = tracker.apply(
        _base_advisory(now + timedelta(minutes=1)),
        observed_at=now + timedelta(minutes=1),
        current_price=98_600,
        bars=[*bars, intrabar],
        bbo={"best_bid": 98_500, "best_ask": 98_600},
        source_quality={"status": "PASS", "issues": []},
    )
    assert still_watch["state"] == "EXIT_WATCH"

    close_break = doosan.MinuteBar(
        source_time="20260805090400",
        open=98_600,
        high=98_650,
        low=98_300,
        close=98_400,
        volume=2_000,
    )
    suppressed, ready = tracker.apply(
        _base_advisory(now + timedelta(minutes=2)),
        observed_at=now + timedelta(minutes=2),
        current_price=98_400,
        bars=[*bars, intrabar, close_break],
        bbo={"best_bid": 98_300, "best_ask": 98_400},
        source_quality={"status": "PASS", "issues": []},
    )
    assert suppressed["state"] == "WATCH"
    assert ready["state"] == "EXIT_READY"
    assert ready["reasons"] == ["doosan_completed_close_below_entry_support"]
    assert tracker.completed is True


def test_invalid_actionable_contract_does_not_consume_entry_episode():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = doosan.DoosanDailyEpisodeTracker()
    blocked = _base_advisory(now)
    blocked["source_quality"] = {"status": "BLOCKED", "issues": ["bbo_stale"]}

    suppressed, exit_watch = tracker.apply(
        blocked,
        observed_at=now,
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000, "best_ask": 99_100},
        source_quality=blocked["source_quality"],
    )

    assert suppressed["state"] == "DATA_WAIT"
    assert suppressed["entry_price_low"] is None
    assert "doosan_entry_episode_contract_invalid" in suppressed["unmet_conditions"]
    assert exit_watch["state"] == "DATA_WAIT"
    assert tracker.entry_issued is False
    assert tracker.entry_event is None

    invalid_support = _base_advisory(now + timedelta(seconds=10))
    invalid_support["derived"]["structural_support"] = 99_200
    invalid_advisory, _ = tracker.apply(
        invalid_support,
        observed_at=now + timedelta(seconds=10),
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000, "best_ask": 99_100},
        source_quality=invalid_support["source_quality"],
    )
    assert invalid_advisory["state"] == "WATCH"
    assert invalid_advisory["entry_price_high"] is None
    assert tracker.entry_issued is False

    valid = _base_advisory(now + timedelta(seconds=20))
    captured, _ = tracker.apply(
        valid,
        observed_at=now + timedelta(seconds=20),
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000, "best_ask": 99_100},
        source_quality=valid["source_quality"],
    )

    assert captured["state"] == "ENTRY_CAUTION"
    assert tracker.entry_issued is True
    assert tracker.entry_event is not None


def test_active_episode_prevents_overlap_and_restores_after_restart():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = doosan.DoosanDailyEpisodeTracker()
    tracker.apply(
        _base_advisory(now),
        observed_at=now,
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000},
        source_quality={"status": "PASS", "issues": []},
    )
    snapshot = tracker.snapshot()
    restarted = doosan.DoosanDailyEpisodeTracker()

    assert restarted.restore(snapshot, observed_at=now + timedelta(minutes=5))
    repeated, _ = restarted.apply(
        _base_advisory(now + timedelta(minutes=5)),
        observed_at=now + timedelta(minutes=5),
        current_price=99_200,
        bars=bars,
        bbo={"best_bid": 99_100},
        source_quality={"status": "PASS", "issues": []},
    )
    assert repeated["state"] == "WATCH"
    assert "doosan_entry_episode_active" in repeated["unmet_conditions"]
    assert restarted.entry_event["event_id"] == snapshot["entry_event"]["event_id"]
    assert restarted.daily_entry_count == 1

    corrupted = {**snapshot, "target_price": 1}
    assert not doosan.DoosanDailyEpisodeTracker().restore(
        corrupted, observed_at=now + timedelta(minutes=5)
    )


def test_entry_linked_target_exit_is_tick_rounded_and_requires_rearm():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = doosan.DoosanDailyEpisodeTracker()
    tracker.apply(
        _base_advisory(now),
        observed_at=now,
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000},
        source_quality={"status": "PASS", "issues": []},
    )

    suppressed, exit_ready = tracker.apply(
        _base_advisory(now + timedelta(seconds=10)),
        observed_at=now + timedelta(seconds=10),
        current_price=100_100,
        bars=bars,
        bbo={"best_bid": 100_000},
        source_quality={"status": "PASS", "issues": []},
    )

    assert tracker.target_price == 100_100
    assert exit_ready["state"] == "EXIT_READY"
    assert exit_ready["reasons"] == ["doosan_target_1pct_reached"]
    assert suppressed["state"] == "WATCH"
    assert tracker.entry_event["status"] == "CLOSED"
    assert tracker.completed is True
    assert tracker.rearm_required is True
    assert tracker.daily_entry_count == 1
    completed_snapshot = tracker.snapshot()
    assert doosan.DoosanDailyEpisodeTracker().restore(
        completed_snapshot, observed_at=now + timedelta(seconds=20)
    )
    completed_snapshot["exit_event"] = {
        **completed_snapshot["exit_event"],
        "reference_exit_price": None,
    }
    assert not doosan.DoosanDailyEpisodeTracker().restore(
        completed_snapshot, observed_at=now + timedelta(seconds=20)
    )
    stranded = tracker.snapshot()
    stranded["rearm_required"] = False
    assert not doosan.DoosanDailyEpisodeTracker().restore(
        stranded, observed_at=now + timedelta(seconds=20)
    )


def test_completed_episode_rearms_and_allows_second_entry_same_day():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    later_bars = [
        *bars,
        _bars([98_700], start=datetime(2026, 8, 5, 9, 3, tzinfo=KST))[0],
    ]
    tracker = doosan.DoosanDailyEpisodeTracker()
    tracker.apply(
        _base_advisory(now),
        observed_at=now,
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000},
        source_quality={"status": "PASS", "issues": []},
    )
    tracker.apply(
        _base_advisory(now + timedelta(seconds=10)),
        observed_at=now + timedelta(seconds=10),
        current_price=100_100,
        bars=bars,
        bbo={"best_bid": 100_000},
        source_quality={"status": "PASS", "issues": []},
    )
    first_event_id = str(tracker.entry_event["event_id"])

    same_setup, _ = tracker.apply(
        _base_advisory(now + timedelta(seconds=80)),
        observed_at=now + timedelta(seconds=80),
        current_price=99_200,
        bars=later_bars,
        bbo={"best_bid": 99_100},
        source_quality={"status": "PASS", "issues": []},
    )
    assert same_setup["state"] == "WATCH"
    assert "doosan_entry_episode_rearm_pending" in same_setup["unmet_conditions"]
    assert tracker.rearm_required is True

    blocked_reset = _base_advisory(now + timedelta(seconds=90), state="WATCH")
    blocked_reset["source_quality"] = {
        "status": "BLOCKED",
        "issues": ["bbo_stale"],
    }
    tracker.apply(
        blocked_reset,
        observed_at=now + timedelta(seconds=90),
        current_price=99_000,
        bars=later_bars,
        bbo={"best_bid": 98_900},
        source_quality=blocked_reset["source_quality"],
    )
    assert tracker.rearm_required is True

    unconfirmed = _base_advisory(now + timedelta(seconds=95))
    unconfirmed["state"] = "WATCH"
    tracker.apply(
        unconfirmed,
        observed_at=now + timedelta(seconds=95),
        current_price=99_000,
        bars=later_bars,
        bbo={"best_bid": 98_900},
        source_quality={"status": "PASS", "issues": []},
    )
    assert tracker.rearm_required is True

    non_actionable, _ = tracker.apply(
        _base_advisory(now + timedelta(seconds=100), state="WATCH"),
        observed_at=now + timedelta(seconds=100),
        current_price=99_000,
        bars=later_bars,
        bbo={"best_bid": 98_900},
        source_quality={"status": "PASS", "issues": []},
    )
    assert "doosan_entry_episode_rearmed" in non_actionable["reasons"]
    assert tracker.entry_issued is False
    assert tracker.daily_entry_count == 1
    restarted = doosan.DoosanDailyEpisodeTracker()
    assert restarted.restore(
        tracker.snapshot(), observed_at=now + timedelta(seconds=105)
    )
    tracker = restarted

    second_entry, _ = tracker.apply(
        _base_advisory(now + timedelta(seconds=110)),
        observed_at=now + timedelta(seconds=110),
        current_price=99_100,
        bars=later_bars,
        bbo={"best_bid": 99_000},
        source_quality={"status": "PASS", "issues": []},
    )
    assert second_entry["state"] == "ENTRY_CAUTION"
    assert tracker.active is True
    assert tracker.daily_entry_count == 2
    assert tracker.entry_event["episode_sequence"] == 2
    assert ":ENTRY:02:" in tracker.entry_event["event_id"]
    assert tracker.entry_event["event_id"] != first_event_id


def test_recent_support_loss_reentry_requires_reclaim_and_support_floor():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = doosan.DoosanDailyEpisodeTracker()
    tracker.apply(
        _base_advisory(now),
        observed_at=now,
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000},
        source_quality={"status": "PASS", "issues": []},
    )
    close_break = doosan.MinuteBar(
        source_time="20260805090300",
        open=98_600,
        high=98_650,
        low=98_300,
        close=98_400,
        volume=2_000,
    )
    tracker.apply(
        _base_advisory(now + timedelta(seconds=10)),
        observed_at=now + timedelta(seconds=10),
        current_price=98_400,
        bars=[*bars, close_break],
        bbo={"best_bid": 98_300},
        source_quality={"status": "PASS", "issues": []},
    )
    closed_snapshot = tracker.snapshot()
    restarted = doosan.DoosanDailyEpisodeTracker()
    assert restarted.restore(closed_snapshot, observed_at=now + timedelta(seconds=20))
    tracker = restarted
    later_bar = doosan.MinuteBar(
        source_time="20260805090400",
        open=98_500,
        high=99_100,
        low=98_500,
        close=99_000,
        volume=2_500,
    )
    later_bars = [*bars, close_break, later_bar]

    non_actionable = _base_advisory(now + timedelta(seconds=80), state="WATCH")
    pending, _ = tracker.apply(
        non_actionable,
        observed_at=now + timedelta(seconds=80),
        current_price=99_000,
        bars=later_bars,
        bbo={"best_bid": 98_900},
        source_quality={"status": "PASS", "issues": []},
    )
    assert tracker.rearm_required is True
    assert "doosan_loss_reentry_structure_pending" in pending["unmet_conditions"]

    no_reclaim = _base_advisory(now + timedelta(seconds=90))
    no_reclaim["derived"]["recent_resistance_reclaimed"] = False
    blocked, _ = tracker.apply(
        no_reclaim,
        observed_at=now + timedelta(seconds=90),
        current_price=99_000,
        bars=later_bars,
        bbo={"best_bid": 98_900},
        source_quality={"status": "PASS", "issues": []},
    )
    assert blocked["state"] == "WATCH"
    assert blocked["entry_price_low"] is None
    assert (
        blocked["derived"]["doosan_loss_reentry_guard"]["recent_resistance_reclaimed"]
        is False
    )
    assert tracker.daily_entry_count == 1

    reclaimed = _base_advisory(now + timedelta(seconds=100))
    reclaimed["derived"]["recent_resistance_reclaimed"] = True
    second_entry, _ = tracker.apply(
        reclaimed,
        observed_at=now + timedelta(seconds=100),
        current_price=99_000,
        bars=later_bars,
        bbo={"best_bid": 98_900},
        source_quality={"status": "PASS", "issues": []},
    )
    assert second_entry["state"] == "ENTRY_CAUTION"
    assert "doosan_entry_episode_rearmed" in second_entry["reasons"]
    assert second_entry["derived"]["doosan_loss_reentry_guard"]["ready"] is True
    assert tracker.active is True
    assert tracker.daily_entry_count == 2

    expired_tracker = doosan.DoosanDailyEpisodeTracker()
    assert expired_tracker.restore(
        closed_snapshot, observed_at=now + timedelta(minutes=16)
    )
    expired_watch = _base_advisory(now + timedelta(minutes=16), state="WATCH")
    expired_tracker.apply(
        expired_watch,
        observed_at=now + timedelta(minutes=16),
        current_price=99_000,
        bars=later_bars,
        bbo={"best_bid": 98_900},
        source_quality={"status": "PASS", "issues": []},
    )
    assert expired_tracker.entry_issued is False
    unrestricted = _base_advisory(now + timedelta(minutes=16, seconds=10))
    unrestricted["derived"]["recent_resistance_reclaimed"] = False
    after_window, _ = expired_tracker.apply(
        unrestricted,
        observed_at=now + timedelta(minutes=16, seconds=10),
        current_price=99_000,
        bars=later_bars,
        bbo={"best_bid": 98_900},
        source_quality={"status": "PASS", "issues": []},
    )
    assert after_window["state"] == "ENTRY_CAUTION"
    assert expired_tracker.daily_entry_count == 2


def test_completed_legacy_snapshot_migrates_to_rearm_pending():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = doosan.DoosanDailyEpisodeTracker()
    tracker.apply(
        _base_advisory(now),
        observed_at=now,
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000},
        source_quality={"status": "PASS", "issues": []},
    )
    tracker.apply(
        _base_advisory(now + timedelta(seconds=10)),
        observed_at=now + timedelta(seconds=10),
        current_price=100_100,
        bars=bars,
        bbo={"best_bid": 100_000},
        source_quality={"status": "PASS", "issues": []},
    )
    legacy = tracker.snapshot()
    for key in (
        "episode_policy",
        "daily_entry_count",
        "rearm_required",
        "rearm_after_bar",
    ):
        legacy.pop(key)
    restarted = doosan.DoosanDailyEpisodeTracker()

    assert restarted.restore(legacy, observed_at=now + timedelta(seconds=20))
    assert restarted.daily_entry_count == 1
    assert restarted.rearm_required is True
    assert restarted.rearm_after_bar == "20260805100000"


def test_non_actionable_reset_requires_fresh_two_observation_promotion():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    promotion = AdvisoryPromotionFilter()

    assert promotion.apply(_base_advisory(now))["state"] == "WATCH"
    assert (
        promotion.apply(_base_advisory(now + timedelta(seconds=10)))["state"]
        == "ENTRY_CAUTION"
    )
    assert (
        promotion.apply(_base_advisory(now + timedelta(seconds=20), state="WATCH"))[
            "state"
        ]
        == "WATCH"
    )
    assert (
        promotion.apply(_base_advisory(now + timedelta(seconds=30)))["state"] == "WATCH"
    )
    assert (
        promotion.apply(_base_advisory(now + timedelta(seconds=40)))["state"]
        == "ENTRY_CAUTION"
    )


def test_collector_uses_cached_token_and_auxiliary_read_only_market_requests(
    monkeypatch, tmp_path
):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    monkeypatch.setattr(
        doosan.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )
    monkeypatch.setattr(
        doosan.kiwoom_utils, "resolve_kiwoom_request_token", lambda token: token
    )
    monkeypatch.setattr(
        doosan.kiwoom_utils,
        "get_kiwoom_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("token issue forbidden")
        ),
    )
    monkeypatch.setattr(
        doosan.kiwoom_utils,
        "get_api_url",
        lambda path: f"https://api.example.test{path}",
    )

    class Response:
        status_code = 200

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return {"return_code": 0, **self.payload}

    class FakeSession:
        def __init__(self):
            self.calls = []

        def post(self, url, *, headers, json, timeout):
            self.calls.append((headers["api-id"], json))
            api_id = headers["api-id"]
            if api_id == "ka10001":
                return Response({"cur_prc": "98500", "low_pric": "98000"})
            if api_id == "ka10004":
                return Response(
                    {
                        "buy_fpr_bid": "98400",
                        "sel_fpr_bid": "98500",
                        "buy_fpr_req": "1000",
                        "sel_fpr_req": "1000",
                    }
                )
            if api_id == "ka10080":
                return Response(
                    {
                        "stk_min_pole_chart_qry": [
                            {
                                "cntr_tm": (
                                    datetime(2026, 8, 5, 9, 0, tzinfo=KST)
                                    + timedelta(minutes=index)
                                ).strftime("%Y%m%d%H%M%S"),
                                "open_pric": str(close + 100),
                                "high_pric": str(close + 150),
                                "low_pric": str(close - 50),
                                "cur_prc": str(close),
                                "trde_qty": "1000",
                            }
                            for index, close in enumerate(
                                [100_000 - index * 10 for index in range(60)]
                            )
                        ]
                    }
                )
            if api_id == "ka20005":
                return Response(
                    {
                        "inds_min_pole_qry": [
                            {
                                "cntr_tm": (
                                    datetime(2026, 8, 5, 9, 0, tzinfo=KST)
                                    + timedelta(minutes=index)
                                ).strftime("%Y%m%d%H%M%S"),
                                "open_pric": str(close + 100),
                                "high_pric": str(close + 150),
                                "low_pric": str(close - 50),
                                "cur_prc": str(close),
                                "trde_qty": "1000",
                            }
                            for index, close in enumerate(
                                [300_000 - index * 10 for index in range(60)]
                            )
                        ]
                    }
                )
            if api_id == "ka10064":
                return Response(
                    {
                        "opmr_invsr_trde_chart": [
                            {"tm": "095900", "frgnr_invsr": "-100"},
                            {"tm": "100000", "frgnr_invsr": "-50"},
                        ]
                    }
                )
            if api_id == "ka90008":
                return Response(
                    {
                        "stk_tm_prm_trde_trnsn": [
                            {
                                "tm": "100000",
                                "prm_netprps_amt": "10",
                                "prm_netprps_amt_irds": "5",
                            }
                        ]
                    }
                )
            if api_id == "ka10081":
                return Response(
                    {
                        "stk_dt_pole_chart_qry": [
                            {
                                "dt": "20260804",
                                "open_pric": "100000",
                                "high_pric": "101000",
                                "low_pric": "98000",
                                "cur_prc": "99500",
                            }
                        ]
                    }
                )
            raise AssertionError(api_id)

    class ExternalProvider:
        def fetch(self, observed_at):
            return {
                "USDKRW": ExternalPoint(
                    "USDKRW",
                    "KRW=X",
                    1400.0,
                    0.0,
                    observed_at.isoformat(),
                    observed_at.isoformat(),
                    0.0,
                    "test",
                    "BEST_EFFORT_DELAYED",
                    "OPEN",
                )
            }

    session = FakeSession()
    collector = doosan.DoosanWidgetCollector(
        snapshot_path=tmp_path / "snapshot.json",
        observation_dir=tmp_path / "observations",
        external_provider=ExternalProvider(),
        request_session=session,
    )
    payload = collector.collect_once(now)

    assert payload["symbol"] == "034020"
    assert payload["token_mode"] == "shared_cache_only"
    assert {api_id for api_id, _ in session.calls} == {
        "ka10001",
        "ka10004",
        "ka10064",
        "ka10080",
        "ka10081",
        "ka20005",
        "ka90008",
    }
    assert payload["advisory"]["auxiliary_context"]["status"] == "OBSERVED"
    assert payload["advisory"]["auxiliary_context"]["relative_signal"] in {
        "NOT_WEAK",
        "WEAK",
    }
    assert payload["advisory"]["auxiliary_context"]["flow_signal"] == "NONWORSENING"
    assert payload["advisory"]["flow"]["status"] == "OBSERVED"
    assert payload["advisory"]["external_risk"]["level"] == "CLEAR"
    assert payload["advisory"]["relative_strength"]["peer_symbol"] == "267260"
    assert payload["advisory"]["relative_strength"]["authority"] == (
        "observed_negative_veto_and_recovery_authority"
    )
    stock_codes = [
        call_payload["stk_cd"]
        for _, call_payload in session.calls
        if "stk_cd" in call_payload
    ]
    assert "034020" in stock_codes
    assert "267260" in stock_codes
