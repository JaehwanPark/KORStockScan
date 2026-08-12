from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.engine.monitoring import hanwha_ocean_widget_advisory as hanwha_ocean
from src.engine.monitoring import hanwha_ocean_widget_contract as contract
from src.engine.monitoring.samsung_widget_advisory import (
    AdvisoryPromotionFilter,
    ExternalPoint,
)
from src.engine.monitoring.samsung_widget_contract import KST


def _bars(
    closes: list[int], *, start: datetime | None = None, lows: list[int] | None = None
) -> list[hanwha_ocean.MinuteBar]:
    start = start or datetime(2026, 8, 5, 9, 0, tzinfo=KST)
    result = []
    for index, close in enumerate(closes):
        open_price = close - 100 if index % 2 == 0 else close + 50
        result.append(
            hanwha_ocean.MinuteBar(
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
    support_confirmation: str = "higher_high_and_low",
    retest_held: bool = False,
    retest_rebound_confirmed: bool = False,
    vwap_reclaimed: bool = True,
    resistance_reclaimed: bool = True,
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
        "hanwha_ocean_policy": {"session_return_pct": -0.9},
        "derived": {
            "structural_support": 98_500,
            "confirmed_support": 98_500,
            "volume_confirmation_mode": volume_mode,
            "support_confirmation": support_confirmation,
            "retest_held": retest_held,
            "retest_rebound_confirmed": retest_rebound_confirmed,
            "vwap_reclaimed": vwap_reclaimed,
            "recent_resistance_reclaimed": resistance_reclaimed,
        },
        "provenance": {},
        "strategy_profile": contract.STRATEGY_PROFILE,
        "metric_contract": contract.METRIC_CONTRACT,
        "authority": "widget_advisory_only",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def test_hanwha_ocean_policy_requires_first_pullback_and_reclaim():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_900, 99_600])

    result = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        _base_advisory(
            now,
            support_confirmation="unconfirmed",
            vwap_reclaimed=False,
            resistance_reclaimed=False,
        ),
        current_price=99_600,
        bars=bars,
        context=contract.session_context(now),
    )

    assert result["state"] == "WATCH"
    assert result["entry_price_low"] is None
    assert "hanwha_ocean_first_pullback_reclaim_pending" in result["unmet_conditions"]


def test_hanwha_ocean_policy_assigns_structure_based_signal_tiers():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_500, 99_000])
    context = contract.session_context(now)

    standard = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        _base_advisory(now),
        current_price=100_400,
        bars=bars,
        context=context,
    )
    high = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        _base_advisory(
            now,
            state="ENTRY_READY",
            support_confirmation="retest_held",
            retest_held=True,
            retest_rebound_confirmed=True,
        ),
        current_price=98_900,
        bars=bars,
        context=context,
    )

    assert standard["state"] == "ENTRY_CAUTION"
    assert standard["signal_tier"] == "STANDARD"
    assert standard["hanwha_ocean_policy"]["session_return_pct"] > 0
    assert high["state"] == "ENTRY_READY"
    assert high["signal_tier"] == "HIGH"
    assert high["hanwha_ocean_policy"]["session_return_authority"] == (
        "diagnostic_only_no_fixed_return_gate"
    )
    assert high["hanwha_ocean_policy"]["retest_held"] is True
    assert "regular_flow_unavailable" not in high["unmet_conditions"]


def test_hanwha_ocean_policy_keeps_absorption_recovery_in_watch():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    result = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        _base_advisory(now, volume_mode="absorption_recovery"),
        current_price=98_500,
        bars=_bars([100_000, 99_000, 98_500]),
        context=contract.session_context(now),
    )

    assert result["state"] == "WATCH"
    assert "hanwha_ocean_standard_rebound_volume_required" in result["unmet_conditions"]


def test_hanwha_ocean_deteriorating_flow_requires_recent_resistance_reclaim():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(now, resistance_reclaimed=False)
    source["auxiliary_context"]["flow_signal"] = "DETERIORATING"

    blocked = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        source,
        current_price=99_000,
        bars=_bars([98_500, 98_700, 99_000]),
        context=contract.session_context(now),
    )

    assert blocked["state"] == "WATCH"
    assert blocked["entry_price_low"] is None
    assert blocked["entry_price_high"] is None
    assert blocked["hanwha_ocean_policy"]["flow_resistance_guard_blocked"] is True
    assert (
        "hanwha_ocean_deteriorating_flow_requires_resistance_reclaim"
        in blocked["unmet_conditions"]
    )

    source["derived"]["recent_resistance_reclaimed"] = True
    allowed = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        source,
        current_price=99_000,
        bars=_bars([98_500, 98_700, 99_000]),
        context=contract.session_context(now),
    )
    assert allowed["state"] == "ENTRY_CAUTION"
    assert allowed["hanwha_ocean_policy"]["flow_resistance_guard_blocked"] is False


@pytest.mark.parametrize(
    "flow_signal",
    [
        "PROGRAM_DETERIORATING_FOREIGN_DELAYED",
        "PROGRAM_DETERIORATING_FOREIGN_LIMITED",
        "FOREIGN_DETERIORATING_PROGRAM_LIMITED",
    ],
)
def test_hanwha_ocean_single_observed_deteriorating_flow_requires_reclaim(
    flow_signal,
):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(now, resistance_reclaimed=False)
    source["auxiliary_context"]["flow_signal"] = flow_signal

    blocked = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        source,
        current_price=99_000,
        bars=_bars([98_500, 98_700, 99_000]),
        context=contract.session_context(now),
    )

    assert blocked["state"] == "WATCH"
    assert blocked["hanwha_ocean_policy"]["deteriorating_flow_observed"] is True
    assert blocked["hanwha_ocean_policy"]["flow_resistance_guard_blocked"] is True


def test_hanwha_ocean_single_observed_nonworsening_flow_does_not_block():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(now, resistance_reclaimed=False)
    source["auxiliary_context"]["flow_signal"] = "PROGRAM_NONWORSENING_FOREIGN_LIMITED"

    allowed = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        source,
        current_price=99_000,
        bars=_bars([98_500, 98_700, 99_000]),
        context=contract.session_context(now),
    )

    assert allowed["state"] == "ENTRY_CAUTION"
    assert allowed["hanwha_ocean_policy"]["deteriorating_flow_observed"] is False
    assert allowed["hanwha_ocean_policy"]["flow_resistance_guard_blocked"] is False


def test_high_tier_does_not_override_portable_recovery_caution():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(
        now,
        state="ENTRY_READY",
        support_confirmation="retest_held",
        retest_held=True,
        retest_rebound_confirmed=True,
    )
    source["derived"]["recovery_episode"] = {"support": 98_500}

    result = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        source,
        current_price=98_500,
        bars=_bars([100_000, 99_000, 98_500]),
        context=contract.session_context(now),
    )

    assert result["signal_tier"] == "HIGH"
    assert result["state"] == "ENTRY_CAUTION"
    assert result["hanwha_ocean_policy"]["base_caution_preserved"] is True


def test_hanwha_ocean_signal_still_requires_two_ten_second_observations():
    first_at = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    first = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        _base_advisory(
            first_at,
            state="ENTRY_READY",
            support_confirmation="retest_held",
            retest_held=True,
            retest_rebound_confirmed=True,
        ),
        current_price=98_500,
        bars=bars,
        context=contract.session_context(first_at),
    )
    second = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        _base_advisory(
            first_at + timedelta(seconds=10),
            state="ENTRY_READY",
            support_confirmation="retest_held",
            retest_held=True,
            retest_rebound_confirmed=True,
        ),
        current_price=98_500,
        bars=bars,
        context=contract.session_context(first_at),
    )
    promotion = AdvisoryPromotionFilter()

    assert promotion.apply(first)["state"] == "WATCH"
    assert promotion.apply(second)["state"] == "ENTRY_READY"


def test_hanwha_ocean_high_requires_resistance_reclaim_and_auxiliary_context():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    source = _base_advisory(
        now,
        state="ENTRY_READY",
        support_confirmation="retest_held",
        retest_held=True,
        retest_rebound_confirmed=True,
        resistance_reclaimed=False,
    )

    resistance_pending = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        source,
        current_price=98_500,
        bars=_bars([100_000, 99_000, 98_500]),
        context=contract.session_context(now),
    )
    assert resistance_pending["state"] == "ENTRY_CAUTION"
    assert resistance_pending["signal_tier"] == "STANDARD"
    assert (
        "hanwha_ocean_recent_resistance_reclaim_required_for_high"
        in resistance_pending["unmet_conditions"]
    )

    source["derived"]["recent_resistance_reclaimed"] = True
    source["auxiliary_context"]["status"] = "LIMITED"
    auxiliary_limited = hanwha_ocean.apply_hanwha_ocean_entry_policy(
        source,
        current_price=98_500,
        bars=_bars([100_000, 99_000, 98_500]),
        context=contract.session_context(now),
    )
    assert auxiliary_limited["state"] == "ENTRY_CAUTION"
    assert auxiliary_limited["signal_tier"] == "STANDARD"
    assert (
        "auxiliary_context_not_ready_for_high" in auxiliary_limited["unmet_conditions"]
    )


def test_entry_linked_exit_uses_target_or_completed_close_not_intrabar_low():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()
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

    close_break = hanwha_ocean.MinuteBar(
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
    assert ready["reasons"] == ["hanwha_ocean_completed_close_below_entry_support"]
    assert tracker.completed is True


def test_invalid_actionable_contract_does_not_consume_entry_episode():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()
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
    assert (
        "hanwha_ocean_entry_episode_contract_invalid" in suppressed["unmet_conditions"]
    )
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
    tracker = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()
    tracker.apply(
        _base_advisory(now),
        observed_at=now,
        current_price=99_100,
        bars=bars,
        bbo={"best_bid": 99_000},
        source_quality={"status": "PASS", "issues": []},
    )
    snapshot = tracker.snapshot()
    restarted = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()

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
    assert "hanwha_ocean_entry_episode_active" in repeated["unmet_conditions"]
    assert restarted.entry_event["event_id"] == snapshot["entry_event"]["event_id"]
    assert restarted.daily_entry_count == 1

    corrupted = {**snapshot, "target_price": 1}
    assert not hanwha_ocean.HanwhaOceanDailyEpisodeTracker().restore(
        corrupted, observed_at=now + timedelta(minutes=5)
    )


def test_entry_linked_target_exit_is_tick_rounded_and_requires_rearm():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()
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
    assert exit_ready["reasons"] == ["hanwha_ocean_target_1pct_reached"]
    assert suppressed["state"] == "WATCH"
    assert tracker.entry_event["status"] == "CLOSED"
    assert tracker.completed is True
    assert tracker.rearm_required is True
    assert tracker.daily_entry_count == 1
    completed_snapshot = tracker.snapshot()
    assert hanwha_ocean.HanwhaOceanDailyEpisodeTracker().restore(
        completed_snapshot, observed_at=now + timedelta(seconds=20)
    )
    completed_snapshot["exit_event"] = {
        **completed_snapshot["exit_event"],
        "reference_exit_price": None,
    }
    assert not hanwha_ocean.HanwhaOceanDailyEpisodeTracker().restore(
        completed_snapshot, observed_at=now + timedelta(seconds=20)
    )
    stranded = tracker.snapshot()
    stranded["rearm_required"] = False
    assert not hanwha_ocean.HanwhaOceanDailyEpisodeTracker().restore(
        stranded, observed_at=now + timedelta(seconds=20)
    )


def test_completed_episode_rearms_and_allows_second_entry_same_day():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    later_bars = [
        *bars,
        _bars([98_700], start=datetime(2026, 8, 5, 9, 3, tzinfo=KST))[0],
    ]
    tracker = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()
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
    assert "hanwha_ocean_entry_episode_rearm_pending" in same_setup["unmet_conditions"]
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
    assert "hanwha_ocean_entry_episode_rearmed" in non_actionable["reasons"]
    assert tracker.entry_issued is False
    assert tracker.daily_entry_count == 1
    restarted = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()
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


def test_completed_legacy_snapshot_migrates_to_rearm_pending():
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    bars = _bars([100_000, 99_000, 98_500])
    tracker = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()
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
    restarted = hanwha_ocean.HanwhaOceanDailyEpisodeTracker()

    assert restarted.restore(legacy, observed_at=now + timedelta(seconds=20))
    assert restarted.daily_entry_count == 1
    assert restarted.rearm_required is True
    assert restarted.rearm_after_bar == "20260805100000"


def test_collector_uses_cached_token_and_auxiliary_read_only_market_requests(
    monkeypatch, tmp_path
):
    now = datetime(2026, 8, 5, 10, 0, 5, tzinfo=KST)
    monkeypatch.setattr(
        hanwha_ocean.kiwoom_utils, "get_cached_kiwoom_token", lambda _: "TOKEN"
    )
    monkeypatch.setattr(
        hanwha_ocean.kiwoom_utils, "resolve_kiwoom_request_token", lambda token: token
    )
    monkeypatch.setattr(
        hanwha_ocean.kiwoom_utils,
        "get_kiwoom_token",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("token issue forbidden")
        ),
    )
    monkeypatch.setattr(
        hanwha_ocean.kiwoom_utils,
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
    collector = hanwha_ocean.HanwhaOceanWidgetCollector(
        snapshot_path=tmp_path / "snapshot.json",
        observation_dir=tmp_path / "observations",
        external_provider=ExternalProvider(),
        request_session=session,
    )
    payload = collector.collect_once(now)

    assert payload["symbol"] == "042660"
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
    assert payload["advisory"]["relative_strength"]["peer_symbol"] == "010140"
    assert payload["advisory"]["relative_strength"]["authority"] == (
        "observed_negative_veto_and_recovery_authority"
    )
    stock_codes = [
        call_payload["stk_cd"]
        for _, call_payload in session.calls
        if "stk_cd" in call_payload
    ]
    assert "042660" in stock_codes
    assert "010140" in stock_codes
