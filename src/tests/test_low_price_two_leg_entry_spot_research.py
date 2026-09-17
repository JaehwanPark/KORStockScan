from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from src.engine.monitoring import low_price_two_leg_entry_spot_research as research
from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import (
    RESEARCH_PROFILES,
)
from src.engine.monitoring.low_price_two_leg_entry_spot_research import (
    Bar,
    DayContext,
    SignalFeature,
    SpotCandidate,
    _leg_outcome,
    candidate_grid,
    fetch_sor_history,
    select_profile_spot,
)
from src.trading.low_price_two_leg.profiles import PROFILES
from src.trading.order.regular_two_leg_machine import KST


class FakeResponse:
    def __init__(self, body, *, headers=None):
        self.status_code = 200
        self._body = body
        self.headers = headers or {}

    def json(self):
        return self._body


def test_day_low_fact_reuses_frozen_bars_and_invalidates_corrected_tuple(monkeypatch):
    import builtins

    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    context = DayContext(
        anchor.date(), (Bar(anchor, 20000, 20000, 19900, 20000),), {}
    )
    calls = []

    def counted_min(*args, **kwargs):
        calls.append(True)
        return builtins.min(*args, **kwargs)

    monkeypatch.setattr(research, "min", counted_min, raising=False)
    assert context.minimum_low_price == 19900
    assert context.minimum_low_price == 19900
    assert len(calls) == 1
    context.bars = (Bar(anchor, 20000, 20000, 19000, 20000),)
    assert context.minimum_low_price == 19000
    assert len(calls) == 2
    context.bars = ()
    assert context.minimum_low_price is None
    assert context.minimum_low_price is None
    assert len(calls) == 3
    copied = deepcopy(context)
    assert copied.minimum_low_price is None
    assert len(calls) == 3


def test_day_low_fact_cache_is_nonsemantic_and_copy_has_independent_lifetime():
    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    context = DayContext(
        anchor.date(), (Bar(anchor, 20000, 20000, 19000, 20000),), {}
    )
    uncomputed = deepcopy(context)
    assert context.minimum_low_price == 19000
    assert context == uncomputed
    copied = deepcopy(context)
    assert copied._minimum_low_source is copied.bars
    copied.bars = (Bar(anchor, 20000, 20000, 18000, 20000),)
    assert copied.minimum_low_price == 18000
    assert context.minimum_low_price == 19000


def test_day_low_fact_does_not_trust_mutable_list_identity():
    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    bars = [Bar(anchor, 20000, 20000, 19000, 20000)]
    context = DayContext(anchor.date(), bars, {})
    assert context.minimum_low_price == 19000
    bars[0] = Bar(anchor, 20000, 20000, 18000, 20000)
    assert context.minimum_low_price == 18000
    bars.clear()
    assert context.minimum_low_price is None


def test_held_replay_uses_corrected_day_low_without_sharing_candidate_custody():
    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    bars = [
        Bar(
            anchor + timedelta(days=day, minutes=i),
            20000, 20600 if i < 60 else 20000, 20000, 20000,
        )
        for day in range(6)
        for i in range(100)
    ]
    contexts = research.build_day_contexts(bars)
    dates = sorted(contexts)
    candidate = SpotCandidate(10 * 60, 10 * 60, 30, 0.5, 0.5)
    before = research.evaluate_candidate(
        candidate, contexts, dates, include_episodes=True
    )
    assert before["held_legs"] > 0
    changed = contexts[dates[3]]
    assert changed.minimum_low_price == 20000
    changed.bars = tuple(replace(bar, low_price=18000) for bar in changed.bars)
    actual = research.evaluate_candidate(candidate, contexts, dates, include_episodes=True)
    assert actual == _reference_evaluate(
        candidate, deepcopy(contexts), dates, include_episodes=True
    )
    assert actual["worst_filled_max_adverse_excursion_pct"] < before[
        "worst_filled_max_adverse_excursion_pct"
    ]
    assert before["episodes"] is not actual["episodes"]
    assert actual["custody_resolution_required"] is True


@pytest.mark.parametrize("ordered", [True, False])
@pytest.mark.parametrize(
    "bounds", [(540, 541), (541, 541), (530, 539), (542, 541), (float("nan"), 600)]
)
def test_feature_window_index_preserves_order_duplicates_and_bounds(ordered, bounds):
    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    rows = tuple(
        SignalFeature(i, anchor + timedelta(minutes=m), 20000, 0.5, 0.1)
        for i, m in enumerate([0, 1, 1, 2, 3])
    )
    if not ordered:
        rows = rows[::-1]
    context = DayContext(anchor.date(), (), {15: rows})
    start, end = bounds
    expected = [
        item for item in rows
        if start <= item.timestamp.hour * 60 + item.timestamp.minute <= end
    ]
    assert list(context.iter_window_features(15, start, end)) == expected
    assert list(context.iter_window_features(15, start, end)) == expected


def test_feature_window_index_reuses_source_and_invalidates_replaced_tuple():
    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    row = SignalFeature(0, anchor, 20000, 0.5, 0.1)
    context = DayContext(anchor.date(), (), {15: (row,)})
    uncomputed = deepcopy(context)
    assert list(context.iter_window_features(15, 540, 540)) == [row]
    cached = context._feature_minute_index[15]
    assert list(context.iter_window_features(15, 530, 550)) == [row]
    assert context._feature_minute_index[15] is cached
    assert context == uncomputed
    copied = deepcopy(context)
    assert copied._feature_minute_index[15][0] is copied.features[15]
    context.features[15] = (replace(row, timestamp=anchor + timedelta(minutes=1)),)
    assert list(context.iter_window_features(15, 540, 540)) == []
    assert context._feature_minute_index[15] is not cached
    assert list(copied.iter_window_features(15, 540, 540)) == [row]
    context.features[15] = ()
    assert list(context.iter_window_features(15, 530, 550)) == []


def test_feature_window_index_does_not_cache_mutable_list_or_missing_lookback():
    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    row = SignalFeature(0, anchor, 20000, 0.5, 0.1)
    context = DayContext(anchor.date(), (), {15: [row]})
    assert list(context.iter_window_features(15, 540, 540)) == [row]
    context.features[15][0] = replace(row, timestamp=anchor + timedelta(minutes=1))
    assert list(context.iter_window_features(15, 540, 540)) == []
    assert not context._feature_minute_index
    with pytest.raises(KeyError):
        context.iter_window_features(999, 540, 539)


def test_feature_window_index_has_declared_lookback_bound():
    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    row = SignalFeature(0, anchor, 20000, 0.5, 0.1)
    context = DayContext(anchor.date(), (), {})
    for lookback in range(50):
        context.features[lookback] = (row,)
        assert list(context.iter_window_features(lookback, 540, 540)) == [row]
        assert len(context._feature_minute_index) <= len(research.LOOKBACK_GRID)


def _bar(timestamp: datetime, *, low=20_000, high=20_000) -> Bar:
    return Bar(timestamp, 20_000, high, low, 20_000)


def _reference_day_contexts(bars):
    """Frozen full-window oracle: preserve the pre-optimization semantics."""
    grouped = {}
    for bar in bars:
        grouped.setdefault(bar.timestamp.date(), []).append(bar)
    result = {}
    for day_key, raw in sorted(grouped.items()):
        day = tuple(sorted(raw, key=lambda item: item.timestamp))
        features = {}
        for lookback in research.LOOKBACK_GRID:
            rows = []
            for index in range(lookback - 1, len(day)):
                window = day[index - lookback + 1 : index + 1]
                if any(
                    current.timestamp - previous.timestamp != timedelta(minutes=1)
                    for previous, current in zip(window, window[1:])
                ):
                    continue
                candidate = day[index]
                high = max(item.high_price for item in window)
                low = min(item.low_price for item in window)
                if min(high, low, candidate.close_price) <= 0:
                    continue
                rows.append(
                    SignalFeature(
                        index,
                        candidate.timestamp,
                        candidate.close_price,
                        (high - candidate.close_price) / high * 100.0,
                        (candidate.close_price - low) / low * 100.0,
                    )
                )
            features[lookback] = tuple(rows)
        result[day_key] = DayContext(day_key, day, features)
    return result


def _reference_evaluate(candidate, contexts, dates, *, include_episodes=False):
    """Frozen serial prefix replay; intentionally independent of window batching."""
    requested = set(dates)
    episodes, blocked = [], []
    carried = None
    for trade_date in sorted(day for day in contexts if day <= max(dates)):
        context = contexts[trade_date]
        if carried is not None:
            if trade_date in requested:
                blocked.append(trade_date.isoformat())
            for leg in carried["legs"]:
                if leg["status"] != "HELD" or not context.bars:
                    continue
                price = int(leg["entry_price"])
                leg["holding_completed_bars"] = int(
                    leg.get("holding_completed_bars", 0)
                ) + len(context.bars)
                leg["mark_price"] = context.bars[-1].close_price
                leg["active_unrealized_pct"] = round(
                    (leg["mark_price"] / price - 1) * 100 - research.COST_PCT, 6
                )
                leg["max_adverse_excursion_pct"] = min(
                    float(leg.get("max_adverse_excursion_pct", 0)),
                    (min(bar.low_price for bar in context.bars) / price - 1) * 100,
                )
            continue
        signal = next(
            (
                item
                for item in context.features[candidate.lookback_bars]
                if candidate.scan_start_minute
                <= item.timestamp.hour * 60 + item.timestamp.minute
                <= candidate.scan_end_minute
                and item.drawdown_pct + 1e-12 >= candidate.rolling_high_drawdown_pct
                and item.near_low_pct - 1e-12 <= candidate.rolling_low_proximity_pct
            ),
            None,
        )
        if signal is not None:
            episode = research._episode(context, signal, candidate)
            if any(leg["status"] == "HELD" for leg in episode["legs"]):
                episode = deepcopy(episode)
                carried = episode
            if trade_date in requested:
                episodes.append(episode)
    result = research._summary(episodes)
    result.update(
        {
            "economic_replay_contract": research.ECONOMIC_REPLAY_CONTRACT,
            "metric_contract": research.ECONOMIC_METRIC_CONTRACT,
            "source_valid_observation_days": len(dates),
            "observation_dates": [day.isoformat() for day in sorted(dates)],
            "cost_pct": research.COST_PCT,
            "cost_adjusted_net_profit_krw_per_source_valid_observation_day": round(
                result["realized_net_profit_krw"] / len(dates), 8
            ),
            "attempted_episodes_per_source_valid_observation_day": round(
                len(episodes) / len(dates), 8
            ),
            "custody_blocked_dates": blocked,
            "custody_resolution_required": carried is not None,
            "carry_in_held_legs": (
                sum(leg["status"] == "HELD" for leg in (carried or {}).get("legs", []))
                if carried and carried["date"] < min(dates).isoformat()
                else 0
            ),
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "source_only_no_runtime_or_order_authority",
        }
    )
    if include_episodes:
        result["episodes"] = deepcopy(episodes)
    return result


@pytest.mark.parametrize(
    "mode", ["zero", "complete", "held", "mixed", "empty_day", "gap"]
)
@pytest.mark.parametrize("include_episodes", [False, True])
def test_window_batch_matches_frozen_serial_prefix_replay(mode, include_episodes):
    profile = next(iter(PROFILES.values()))
    anchor = datetime.combine(
        date(2026, 6, 5), profile.policy.scan_start, tzinfo=KST
    ) - timedelta(minutes=60)
    bars = [
        Bar(
            anchor + timedelta(days=day, minutes=i),
            20000,
            (
                20000
                if mode == "zero"
                else (
                    20000
                    if i >= 60 and (mode == "held" or (mode == "mixed" and day >= 3))
                    else 20600
                )
            ),
            20000,
            20000,
        )
        for day in range(8)
        for i in range(180)
    ]
    if mode == "gap":
        bars = [b for b in bars if b.timestamp.minute != 15]
    actual = research.build_day_contexts(bars)
    if mode == "empty_day":
        key = sorted(actual)[3]
        actual[key] = DayContext(key, (), {n: () for n in research.LOOKBACK_GRID})
    expected = deepcopy(actual)
    dates = sorted(actual)
    windows = [dates[:4], dates[4:6], dates[:6], dates[::2], dates[::-1], dates[:4]]
    saw_held = saw_completed = False
    for candidate in candidate_grid(profile):
        result = research._evaluate_candidate_windows(
            candidate, actual, windows, include_episodes=include_episodes
        )
        assert result == [
            _reference_evaluate(
                candidate, expected, w, include_episodes=include_episodes
            )
            for w in windows
        ]
        saw_held |= any(item["held_legs"] > 0 for item in result)
        saw_completed |= any(item["completed_legs"] > 0 for item in result)
        if include_episodes:
            # A duplicate window gets a separate mutable episode snapshot.
            assert result[0]["episodes"] is not result[-1]["episodes"]
    assert actual == expected
    if mode in {"held", "mixed"}:
        assert saw_held
    if mode in {"complete", "mixed", "empty_day"}:
        assert saw_completed


@pytest.mark.parametrize("mode", ["zero", "complete", "held"])
def test_window_batch_selection_matches_frozen_serial_oracle(monkeypatch, mode):
    profile = next(iter(PROFILES.values()))
    anchor = datetime.combine(
        date(2026, 6, 5), profile.policy.scan_start, tzinfo=KST
    ) - timedelta(minutes=60)
    bars = [
        Bar(
            anchor + timedelta(days=day, minutes=i),
            20000,
            20000 if mode == "zero" or (mode == "held" and i >= 60) else 20600,
            20000,
            20000,
        )
        for day in range(research.CALIBRATION_DAYS + research.HOLDOUT_DAYS)
        for i in range(180)
    ]
    contexts = research.build_day_contexts(bars)
    actual = select_profile_spot(profile, deepcopy(contexts))
    monkeypatch.setattr(
        research,
        "_evaluate_candidate_windows",
        lambda candidate, ctx, windows, **kw: [
            _reference_evaluate(candidate, ctx, dates, **kw) for dates in windows
        ],
    )
    assert actual == select_profile_spot(profile, contexts)


def _full_sort_rank(item):
    """Frozen original economic ordering, before bounded retention."""
    return (
        item[4]["full"][
            "cost_adjusted_net_profit_krw_per_source_valid_observation_day"
        ],
        item[0],
        item[1],
        item[2],
    )


@pytest.mark.parametrize("holdout_net", [-0.2, 0.1, 0.2])
def test_selection_final_views_share_prefix_without_changing_public_results(
    monkeypatch, holdout_net
):
    candidate = SpotCandidate(800, 809, 30, 1.5, 0.1)
    profile = RESEARCH_PROFILES["candidate_007660_midday"]
    monkeypatch.setattr(research, "candidate_grid", lambda _: (candidate,))
    contexts = _contexts(holdout_candidate_net=holdout_net)
    calls = []
    original = research._evaluate_candidate_windows

    def counted(item, source, windows, **kwargs):
        calls.append((item, tuple(len(window) for window in windows), kwargs))
        return original(item, source, windows, **kwargs)

    monkeypatch.setattr(research, "_evaluate_candidate_windows", counted)
    actual = select_profile_spot(profile, deepcopy(contexts))
    assert [lengths for _, lengths, _ in calls] == [
        (15, 15, 30), (30, 16, 46), (16, 46)
    ]
    assert all(options == {"include_episodes": True} for _, _, options in calls[1:])
    for owner in ("baseline", "calibration_winner", "selected"):
        assert "episodes" not in actual[owner]["calibration"]
        assert "episodes" not in actual[owner]["holdout"]
        assert "episodes" in actual[owner]["full"]

    def serial_views(item, source, windows, *, include_episodes=False):
        return [
            _reference_evaluate(
                item, deepcopy(source), window, include_episodes=include_episodes
            )
            for window in windows
        ]

    monkeypatch.setattr(research, "_evaluate_candidate_windows", serial_views)
    assert actual == select_profile_spot(profile, deepcopy(contexts))


@pytest.mark.parametrize("mode", ["zero", "complete", "held"])
def test_selection_final_views_full_grid_and_carry_match_serial_oracle(
    monkeypatch, mode
):
    profile = PROFILES["samsung_heavy_midday"]
    anchor = datetime.combine(
        date(2026, 6, 5), profile.policy.scan_start, tzinfo=KST
    ) - timedelta(minutes=60)
    contexts = research.build_day_contexts([
        Bar(
            anchor + timedelta(days=day, minutes=i), 20000,
            20000 if mode == "zero" or (mode == "held" and i >= 60) else 20600,
            20000, 20000,
        )
        for day in range(46) for i in range(180)
    ])
    actual = select_profile_spot(profile, deepcopy(contexts))

    def serial_views(item, source, windows, *, include_episodes=False):
        return [
            _reference_evaluate(
                item, deepcopy(source), window, include_episodes=include_episodes
            )
            for window in windows
        ]

    # Calibration full-grid batching is already covered elsewhere. Keep that
    # original implementation; independently check the final baseline/winner
    # views that this change batches for the first time.
    original = research._evaluate_candidate_windows

    def oracle(item, source, windows, **kwargs):
        return (serial_views if kwargs.get("include_episodes") else original)(
            item, source, windows, **kwargs
        )

    monkeypatch.setattr(research, "_evaluate_candidate_windows", oracle)
    assert actual == select_profile_spot(profile, deepcopy(contexts))


def _retain_full_sort_reference(heap, item, ordinal, limit):
    # Keep all eligible calibration evidence. Diagnostic output needs only the
    # stable-sort winner; it never participates in choosing the live candidate.
    heap.append((_full_sort_rank(item) + (-ordinal,), item))
    if limit == 1:
        heap[:] = sorted(
            heap, key=lambda row: _full_sort_rank(row[1]), reverse=True
        )[:1]


@pytest.mark.parametrize("limit", [1, 10])
@pytest.mark.parametrize("ordering", ["ascending", "descending", "ties", "mixed"])
def test_bounded_calibration_retention_matches_original_stable_sort(limit, ordering):
    items = []
    heap = []
    for ordinal in range(1536):
        score = {
            "ascending": ordinal,
            "descending": 1536 - ordinal,
            "ties": 1,
            "mixed": (ordinal * 23) % 13 - 6,
        }[ordering]
        item = (
            score / 3,
            (ordinal % 5 if ordering == "mixed" else 1) / 7,
            ordinal % 3 if ordering == "mixed" else 8,
            {"ordinal": ordinal},
            {
                "full": {
                    "cost_adjusted_net_profit_krw_per_source_valid_observation_day": score
                }
            },
        )
        items.append(item)
        research._retain_calibration_candidate(heap, item, ordinal, limit)
        assert len(heap) <= limit
    actual = [item for _, item in sorted(heap, key=lambda row: row[0], reverse=True)]
    assert actual == sorted(items, key=_full_sort_rank, reverse=True)[:limit]
    if ordering == "ties":
        assert [item[3]["ordinal"] for item in actual] == list(range(limit))


@pytest.mark.parametrize("mode", ["zero", "complete", "held"])
def test_bounded_selection_full_grid_matches_full_sort_oracle(monkeypatch, mode):
    profile = PROFILES["samsung_heavy_midday"]
    anchor = datetime.combine(
        date(2026, 6, 5), profile.policy.scan_start, tzinfo=KST
    ) - timedelta(minutes=60)
    bars = [
        Bar(
            anchor + timedelta(days=day, minutes=i),
            20000,
            20000 if mode == "zero" or (mode == "held" and i >= 60) else 20600,
            20000,
            20000,
        )
        for day in range(research.CALIBRATION_DAYS + research.HOLDOUT_DAYS)
        for i in range(180)
    ]
    contexts = research.build_day_contexts(bars)
    actual = select_profile_spot(profile, deepcopy(contexts))
    monkeypatch.setattr(
        research, "_retain_calibration_candidate", _retain_full_sort_reference
    )
    expected = select_profile_spot(profile, deepcopy(contexts))
    assert actual == expected
    assert actual["grid_candidate_count"] == len(candidate_grid(profile))
    if mode == "complete":
        assert actual["calibration_ready_candidate_count"] > 10
        assert actual["baseline"]["full"]["completed_legs"] > 0
    if mode == "held":
        assert actual["baseline"]["full"]["held_legs"] > 0


@pytest.mark.parametrize("holdout_net", [-0.20, 0.10, 0.20])
def test_bounded_selection_counts_all_candidates_and_does_not_rank_on_holdout(
    monkeypatch, holdout_net
):
    candidate = SpotCandidate(800, 809, 30, 1.5, 0.1)
    grid = tuple(
        replace(candidate, rolling_high_drawdown_pct=1.3 + i * 0.005)
        for i in range(36)
    )
    monkeypatch.setattr(research, "candidate_grid", lambda profile: grid)
    calls = []
    original = research._evaluate_candidate_windows

    def counted(item, contexts, windows, **kwargs):
        calls.append((item, deepcopy(windows)))
        return original(item, contexts, windows, **kwargs)

    monkeypatch.setattr(research, "_evaluate_candidate_windows", counted)
    profile = RESEARCH_PROFILES["candidate_007660_midday"]
    contexts = _contexts(holdout_candidate_net=holdout_net)
    actual = select_profile_spot(profile, deepcopy(contexts))
    assert [item for item, _ in calls[:len(grid)]] == list(grid)
    assert all(
        max(max(w) for w in windows) < sorted(contexts)[30]
        for _, windows in calls[: len(grid)]
    )
    assert actual["calibration_ready_candidate_count"] == len(grid)
    assert actual["calibration_gate_counts"] == {
        "sample_ready": len(grid),
        "manageable_carry": len(grid),
        "both_halves_positive_ev": len(grid),
    }
    assert [item["parameters"] for item in actual["top_calibration_candidates"]] == [
        item.public() for item in grid[:10]
    ]
    assert actual["calibration_winner"]["parameters"] == grid[0].public()
    monkeypatch.setattr(
        research, "_retain_calibration_candidate", _retain_full_sort_reference
    )
    assert actual == select_profile_spot(profile, deepcopy(contexts))


@pytest.mark.parametrize(
    "windows", [[], [[]], [[date(2026, 6, 5)]], [[date(2026, 6, 5)] * 2]]
)
def test_window_batch_rejects_invalid_observation_windows(windows):
    with pytest.raises(
        research.ResearchError, match="economic_replay_observation_dates_invalid"
    ):
        research._evaluate_candidate_windows(
            research.baseline_candidate(next(iter(PROFILES.values()))), {}, windows
        )


def test_window_batch_replays_clean_prefix_once_and_seals_early_evidence(monkeypatch):
    anchor = datetime(2026, 6, 5, 9, 0, tzinfo=KST)
    bars = [
        Bar(anchor + timedelta(days=day, minutes=i), 20000, 20600, 20000, 20000)
        for day in range(6)
        for i in range(100)
    ]
    contexts = research.build_day_contexts(bars)
    candidate = SpotCandidate(9 * 60 + 30, 10 * 60, 30, 0.5, 0.5)
    dates = sorted(contexts)
    windows = [dates[:3], dates[3:], dates]
    calls = []
    original = research._episode

    def counted(*args):
        calls.append(args[0].trade_date)
        return original(*args)

    monkeypatch.setattr(research, "_episode", counted)
    actual = research._evaluate_candidate_windows(
        candidate, deepcopy(contexts), windows
    )
    assert calls == dates
    calls.clear()
    expected = [_reference_evaluate(candidate, deepcopy(contexts), w) for w in windows]
    assert len(calls) == 3 + 6 + 6
    assert actual == expected


def test_window_batch_rejects_prebaseline_prefix_even_outside_requested_window():
    key = research.CLEAN_BASELINE_DATE - timedelta(days=1)
    current = research.CLEAN_BASELINE_DATE
    contexts = {key: DayContext(key, (), {}), current: DayContext(current, (), {})}
    with pytest.raises(
        research.ResearchError, match="economic_replay_prebaseline_context_forbidden"
    ):
        research._evaluate_candidate_windows(
            research.baseline_candidate(next(iter(PROFILES.values()))),
            contexts,
            [[current]],
        )


@pytest.mark.parametrize(
    "kind",
    [
        "ordered",
        "shuffled",
        "gap",
        "duplicate",
        "zero_low",
        "zero_close",
        "negative_high",
        "short",
        "empty",
    ],
)
def test_rolling_day_features_match_full_window_oracle(kind):
    bars = []
    for offset in range(3):
        anchor = datetime(2026, 8, 10 + offset, 9, 0, tzinfo=KST)
        for index in range(90):
            price = 20000 + ((index * 17) % 101)
            bars.append(
                Bar(
                    anchor + timedelta(minutes=index),
                    price,
                    price + (index % 5),
                    price - (index % 7),
                    price,
                )
            )
    if kind == "shuffled":
        bars = bars[::2][::-1] + bars[1::2]
    elif kind == "gap":
        bars = [bar for index, bar in enumerate(bars) if index % 90 not in {12, 48}]
    elif kind == "duplicate":
        bars.insert(15, bars[15])
    elif kind in {"zero_low", "zero_close", "negative_high"}:
        old = bars[21]
        bars[21] = Bar(
            old.timestamp,
            old.open_price,
            -1 if kind == "negative_high" else old.high_price,
            0 if kind == "zero_low" else old.low_price,
            0 if kind == "zero_close" else old.close_price,
        )
    elif kind == "short":
        bars = bars[:2]
    elif kind == "empty":
        bars = []
    original = tuple(bars)
    assert research.build_day_contexts(bars) == _reference_day_contexts(bars)
    assert tuple(bars) == original


def test_rolling_features_preserve_full_grid_replay_and_carry_partitions():
    anchor = datetime(2026, 8, 10, 9, 0, tzinfo=KST)
    bars = [
        Bar(
            anchor + timedelta(days=day, minutes=index),
            20000,
            20100,
            19950 if index < 40 else 19700,
            20000 if index < 40 else 19800,
        )
        for day in range(4)
        for index in range(120)
    ]
    actual = research.build_day_contexts(bars)
    expected = _reference_day_contexts(bars)
    dates = sorted(actual)
    profile = next(iter(PROFILES.values()))
    for candidate in candidate_grid(profile):
        for partition in (dates, dates[:2], dates[2:]):
            assert research.evaluate_candidate(
                candidate, actual, partition, include_episodes=True
            ) == research.evaluate_candidate(
                candidate, expected, partition, include_episodes=True
            )


@pytest.mark.parametrize("outcome", ["zero", "complete_partial_fill", "held"])
def test_rolling_features_preserve_selection_full_grid_and_holdout(outcome):
    profile = next(iter(PROFILES.values()))
    anchor = datetime.combine(
        date(2026, 6, 5), profile.policy.scan_start, tzinfo=KST
    ) - timedelta(minutes=60)
    high = (
        20000
        if outcome == "zero"
        else 20600 if outcome == "complete_partial_fill" else 20100
    )
    bars = [
        Bar(anchor + timedelta(days=day, minutes=index), 20000, high, 20000, 20000)
        for day in range(research.CALIBRATION_DAYS + research.HOLDOUT_DAYS)
        for index in range(180)
    ]
    actual = research.build_day_contexts(bars)
    expected = _reference_day_contexts(bars)
    assert select_profile_spot(profile, actual) == select_profile_spot(
        profile, expected
    )
    assert actual.keys() == expected.keys()
    assert actual == expected  # Includes candidate-specific outcome-cache state.


def test_candidate_grid_stays_inside_each_profile_base_window():
    for profile in PROFILES.values():
        lower = profile.policy.scan_start.hour * 60 + profile.policy.scan_start.minute
        upper = (
            profile.policy.scan_last_bar.hour * 60 + profile.policy.scan_last_bar.minute
        )
        grid = candidate_grid(profile)
        assert grid
        assert all(lower <= item.scan_start_minute for item in grid)
        assert all(item.scan_end_minute <= upper for item in grid)
        assert all(
            item.scan_end_minute - item.scan_start_minute + 1 >= 10 for item in grid
        )


def test_logic_improvement_grid_expands_execution_plan_without_live_authority():
    profile = RESEARCH_PROFILES["logic_mirae_asset_morning"]
    plans = {
        (
            item.entry_offsets_ticks,
            item.entry_valid_completed_bars,
            item.target_ticks,
        )
        for item in candidate_grid(profile)
    }

    assert ((-1, -2), 5, 4) in plans
    assert ((0, -1), 3, 4) in plans
    assert all(len(item.entry_offsets_ticks) == 2 for item in candidate_grid(profile))


def test_fixed_operator_observation_grid_never_reoptimizes_the_policy():
    profile = RESEARCH_PROFILES["candidate_475560_morning"]
    grid = candidate_grid(profile)

    assert len(grid) == 1
    assert grid[0].public() == {
        "scan_start": "09:40",
        "scan_end": "09:59",
        "lookback_bars": 20,
        "rolling_high_drawdown_pct": 0.5,
        "rolling_low_proximity_pct": 0.35,
        "entry_offsets_ticks": [0, -1],
        "entry_valid_completed_bars": 5,
        "target_ticks": 4,
    }


def test_target_cannot_complete_on_the_same_bar_as_fill():
    started = datetime(2026, 8, 10, 13, 16, tzinfo=KST)
    fill = _bar(started, low=19_900, high=20_100)
    later_below = _bar(started + timedelta(minutes=1), low=20_000, high=20_050)
    held = _leg_outcome(
        entry_price=20_000,
        fill_bars=(fill, later_below),
        target_bars=(fill, later_below),
    )
    assert held["status"] == "HELD"

    later_target = _bar(started + timedelta(minutes=2), low=20_000, high=20_100)
    complete = _leg_outcome(
        entry_price=20_000,
        fill_bars=(fill,),
        target_bars=(fill, later_target),
    )
    assert complete["status"] == "COMPLETE"


def test_held_leg_exposes_mark_to_market_mae_and_manageable_carry_budget():
    started = datetime(2026, 8, 10, 13, 16, tzinfo=KST)
    fill = Bar(started, 20_000, 20_000, 19_950, 20_000)
    later = Bar(started + timedelta(minutes=1), 19_800, 19_850, 19_500, 19_600)
    held = _leg_outcome(
        entry_price=20_000,
        fill_bars=(fill,),
        target_bars=(fill, later),
    )

    assert held["status"] == "HELD"
    assert held["active_unrealized_pct"] == pytest.approx(-2.23)
    assert held["max_adverse_excursion_pct"] == pytest.approx(-2.5)
    assert research._manageable_carry(
        {
            "held_leg_rate_per_filled_leg": 0.25,
            "worst_held_active_unrealized_pct": -2.2,
        }
    )
    assert not research._manageable_carry(
        {
            "held_leg_rate_per_filled_leg": 0.26,
            "worst_held_active_unrealized_pct": -2.2,
        }
    )


def test_fetch_uses_integrated_sor_and_cached_token_without_other_api_calls():
    start = date(2026, 6, 5)
    dates = [start + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
        for item in dates
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
    )
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({"return_code": 0, "stk_min_pole_chart_qry": rows})

    bars, meta = fetch_sor_history(
        symbol="010140",
        token="CACHED",
        start_date=start,
        end_date=dates[-1],
        post=post,
        page_delay_sec=0,
    )

    assert len(calls) == 1
    assert calls[0][1]["headers"]["api-id"] == "ka10080"
    assert calls[0][1]["json"] == {
        "stk_cd": "010140_AL",
        "tic_scope": "1",
        "upd_stkpc_tp": "1",
    }
    assert len(bars) == 46
    assert meta["source_quality_status"] == "PASS"


def test_fetch_uses_shared_source_only_read_capacity(monkeypatch):
    start = date(2026, 6, 5)
    dates = [start + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
        for item in dates
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
    )
    admissions = []

    def acquire(**kwargs):
        admissions.append(kwargs)
        return SimpleNamespace(admitted=True, reason="shared_read_rate_admitted")

    monkeypatch.setattr(research.kiwoom_utils, "acquire_kiwoom_read_capacity", acquire)

    fetch_sor_history(
        symbol="010140",
        token="CACHED",
        start_date=start,
        end_date=dates[-1],
        post=lambda *args, **kwargs: FakeResponse(
            {"return_code": 0, "stk_min_pole_chart_qry": rows}
        ),
        page_delay_sec=0,
        shared_read_control_enabled=True,
    )

    assert len(admissions) == 1
    assert admissions[0]["request_owner"] == ("low_price_two_leg_entry_spot_research")
    assert admissions[0]["request_class"] == "source_only"
    assert admissions[0]["request_code"] == "010140_AL"


def test_fetch_waits_and_retries_the_same_continuation_page_on_shared_defer(
    monkeypatch,
):
    start = date(2026, 6, 5)
    dates = [start + timedelta(days=index) for index in range(46)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
        for item in dates
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
    )
    admissions = iter(
        [
            SimpleNamespace(admitted=False, reason="source_only_reserve"),
            SimpleNamespace(admitted=False, reason="source_only_reserve"),
            SimpleNamespace(admitted=True, reason="shared_read_rate_admitted"),
        ]
    )
    sleeps = []
    post_calls = []
    monkeypatch.setattr(
        research.kiwoom_utils,
        "acquire_kiwoom_read_capacity",
        lambda **_kwargs: next(admissions),
    )

    bars, meta = fetch_sor_history(
        symbol="010140",
        token="CACHED",
        start_date=start,
        end_date=dates[-1],
        post=lambda *args, **kwargs: (
            post_calls.append((args, kwargs))
            or FakeResponse({"return_code": 0, "stk_min_pole_chart_qry": rows})
        ),
        page_delay_sec=0,
        shared_read_control_enabled=True,
        shared_defer_max_attempts=2,
        shared_defer_delay_sec=0.5,
        sleeper=sleeps.append,
    )

    assert len(bars) == 46
    assert len(post_calls) == 1
    assert sleeps == [0.5, 0.5]
    assert meta["shared_read_deferred_count"] == 2
    assert meta["shared_read_deferred_wait_sec"] == 1.0


def test_fetch_accepts_expanding_clean_baseline_trading_day_count():
    start = date(2026, 6, 5)
    dates = [start + timedelta(days=index) for index in range(47)]
    rows = [
        {
            "cntr_tm": f"{item.strftime('%Y%m%d')}131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
        for item in dates
    ]
    rows.append(
        {
            "cntr_tm": "20260604131500",
            "open_pric": "20000",
            "high_pric": "20100",
            "low_pric": "19900",
            "cur_prc": "20000",
        }
    )

    bars, meta = fetch_sor_history(
        symbol="010140",
        token="CACHED",
        start_date=start,
        end_date=dates[-1],
        post=lambda *args, **kwargs: FakeResponse(
            {"return_code": 0, "stk_min_pole_chart_qry": rows}
        ),
        page_delay_sec=0,
        expected_trading_day_count=47,
    )

    assert len(bars) == 47
    assert meta["expected_trading_date_count"] == 47
    assert meta["source_quality_status"] == "PASS"


def _episode(day: date, signal_minute: int, *, net_profit_pct: float) -> dict:
    timestamp = datetime.combine(day, time(13, signal_minute), tzinfo=KST)
    return {
        "date": day.isoformat(),
        "signal_at": timestamp.isoformat(),
        "signal_close": 20_000,
        "observed_drawdown_pct": 2.0,
        "observed_near_low_pct": 0.05,
        "legs": [
            {
                "status": "COMPLETE",
                "entry_price": 20_000,
                "target_price": 20_100,
                "net_profit_pct": net_profit_pct,
            },
            {
                "status": "COMPLETE",
                "entry_price": 19_950,
                "target_price": 20_050,
                "net_profit_pct": net_profit_pct,
            },
        ],
    }


def _contexts(
    *,
    holdout_candidate_net: float,
    baseline_net: float = -0.10,
    total_days: int = 46,
    calibration_days: int = 30,
) -> dict[date, DayContext]:
    started = date(2026, 6, 5)
    result = {}
    for index in range(total_days):
        day = started + timedelta(days=index)
        first = SignalFeature(
            0,
            datetime.combine(day, time(13, 15), tzinfo=KST),
            20_000,
            1.25,
            0.20,
        )
        second = SignalFeature(
            1,
            datetime.combine(day, time(13, 20), tzinfo=KST),
            20_000,
            2.0,
            0.05,
        )
        candidate_net = 0.20 if index < calibration_days else holdout_candidate_net
        result[day] = DayContext(
            day,
            (),
            {30: (first, second)},
            {
                0: _episode(day, 15, net_profit_pct=baseline_net),
                1: _episode(day, 20, net_profit_pct=candidate_net),
            },
        )
    return result


def test_profile_selection_uses_calibration_then_requires_untouched_holdout(
    monkeypatch,
):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))
    profile = RESEARCH_PROFILES["candidate_007660_midday"]

    passed = select_profile_spot(profile, _contexts(holdout_candidate_net=0.20))
    assert passed["calibration_winner"]["parameters"] == candidate.public()
    assert passed["decision"] == "holdout_pass_source_only_early_candidate"
    assert passed["selected"]["parameters"] == candidate.public()

    failed = select_profile_spot(profile, _contexts(holdout_candidate_net=-0.20))
    assert failed["calibration_winner"]["parameters"] == candidate.public()
    assert failed["decision"] == "holdout_failed_keep_baseline"
    assert failed["selected"]["parameters"] != candidate.public()


def test_profile_selection_expands_calibration_and_keeps_16_day_holdout(
    monkeypatch,
):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))

    result = select_profile_spot(
        RESEARCH_PROFILES["candidate_007660_midday"],
        _contexts(
            holdout_candidate_net=0.20,
            total_days=47,
            calibration_days=31,
        ),
        calibration_days=31,
        holdout_days=16,
    )

    assert result["date_split"]["calibration_trading_day_count"] == 31
    assert result["date_split"]["holdout_trading_day_count"] == 16
    assert result["decision"] == "holdout_pass_source_only_early_candidate"


def test_profile_selection_requires_strict_holdout_improvement(monkeypatch):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))

    result = select_profile_spot(
        RESEARCH_PROFILES["candidate_007660_midday"],
        _contexts(holdout_candidate_net=0.10, baseline_net=0.10),
    )

    assert result["decision"] == "holdout_positive_not_better_keep_baseline"
    assert result["recommended_action"] == "retain_existing_baseline"
    assert result["selected"]["parameters"] != candidate.public()


def test_calibration_half_negative_is_diagnostic_when_overall_and_holdout_positive(
    monkeypatch,
):
    candidate = SpotCandidate(13 * 60 + 20, 13 * 60 + 29, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))
    contexts = _contexts(holdout_candidate_net=0.20)
    for index, context in enumerate(contexts.values()):
        if 15 <= index < 30:
            context.outcome_cache[1]["legs"][0]["net_profit_pct"] = -0.10
            context.outcome_cache[1]["legs"][1]["net_profit_pct"] = -0.10

    result = select_profile_spot(RESEARCH_PROFILES["candidate_007660_midday"], contexts)

    assert result["decision"] == "holdout_pass_source_only_early_candidate"
    assert result["runtime_effect"] is False
    assert result["calibration_half_diagnostics"]["second_half_positive_ev"] is False
    assert result["calibration_ready_candidate_count"] == 1
    assert result["calibration_gate_counts"]["sample_ready"] == 1
    assert result["calibration_gate_counts"]["both_halves_positive_ev"] == 0
    assert result["best_diagnostic_candidate"]["parameters"] == candidate.public()


def test_higher_trade_ev_with_lower_same_window_profit_is_not_recommended(monkeypatch):
    candidate = SpotCandidate(800, 809, 30, 1.50, 0.10)
    monkeypatch.setattr(research, "candidate_grid", lambda profile: (candidate,))
    contexts = _contexts(holdout_candidate_net=0.20, baseline_net=0.10)
    for index, context in enumerate(contexts.values()):
        if index % 3 != 0:
            context.features[30] = context.features[30][:1]
    result = select_profile_spot(RESEARCH_PROFILES["candidate_007660_midday"], contexts)
    assert (
        result["calibration_winner"]["holdout"]["notional_weighted_ev_pct"]
        > result["baseline"]["holdout"]["notional_weighted_ev_pct"]
    )
    assert result["paired_economics"]["net_profit_uplift_krw_per_observation_day"] < 0
    assert result["decision"] == "holdout_positive_not_better_keep_baseline"
    assert "episodes" in result["baseline"]["full"]


def test_held_inventory_blocks_following_days_and_holdout_without_mutating_cache():
    contexts = _contexts(holdout_candidate_net=0.2)
    dates = sorted(contexts)
    first = contexts[dates[0]].outcome_cache[1]
    first["legs"][0].update(status="HELD", active_unrealized_pct=-0.1)
    first["legs"][0].pop("net_profit_pct")
    candidate = SpotCandidate(800, 809, 30, 1.5, 0.10)
    full = research.evaluate_candidate(
        candidate, contexts, dates, include_episodes=True
    )
    holdout = research.evaluate_candidate(candidate, contexts, dates[-16:])
    assert full["signal_episodes"] == 1
    assert len(full["custody_blocked_dates"]) == 45
    assert holdout["signal_episodes"] == 0
    assert holdout["carry_in_held_legs"] == 1
    assert holdout["custody_resolution_required"] is True
    assert "holding_completed_bars" not in first["legs"][0]
    assert full["runtime_effect"] is False


def test_existing_axis_replay_finds_later_signal_with_execution_fields_unchanged():
    contexts = _contexts(holdout_candidate_net=0.2, baseline_net=0.05)
    for context in contexts.values():
        first, second = context.features[30]
        first = research.replace(
            first, timestamp=first.timestamp.replace(minute=20), drawdown_pct=0.8
        )
        second = research.replace(
            second, timestamp=second.timestamp.replace(minute=25), drawdown_pct=1.0
        )
        context.features[30] = (first, second)
        context.outcome_cache[0]["signal_at"] = first.timestamp.isoformat()
        context.outcome_cache[1]["signal_at"] = second.timestamp.isoformat()
    from src.trading.low_price_two_leg.profiles import get_profile

    profile = get_profile("samsung_heavy_midday", target_date=max(contexts))
    replay = research.existing_axis_economic_replay(profile, contexts)
    drawdown = next(
        item
        for item in replay["alternatives"]
        if item["axis"] == "rolling_high_drawdown_pct"
    )
    assert drawdown["comparison"]["net_profit_improved"] is True
    assert (
        drawdown["outcome"]["episodes"][0]["signal_at"]
        != replay["current_outcome"]["episodes"][0]["signal_at"]
    )
    for key in (
        "entry_offsets_ticks",
        "entry_valid_completed_bars",
        "target_ticks",
        "lookback_bars",
    ):
        assert drawdown["parameters"][key] == replay["current_parameters"][key]
    assert replay["allowed_runtime_apply"] is False
    assert research.valid_existing_axis_economic_replay(replay)
    drawdown["parameters"]["target_ticks"] += 1
    assert not research.valid_existing_axis_economic_replay(replay)


def test_paired_economics_rejects_different_windows_and_costs():
    contexts = _contexts(holdout_candidate_net=0.2)
    candidate = SpotCandidate(800, 809, 30, 1.5, 0.1)
    dates = sorted(contexts)
    current = research.evaluate_candidate(candidate, contexts, dates[:16])
    different = research.evaluate_candidate(candidate, contexts, dates[-16:])
    assert (
        research.paired_economics(current, different)["comparable_observation_window"]
        is False
    )
    assert (
        research.paired_economics(current, dict(current, cost_pct=0.2))[
            "comparable_observation_window"
        ]
        is False
    )


def test_cached_fill_outcomes_do_not_reuse_another_lookback_signal_features():
    contexts = _contexts(holdout_candidate_net=0.2)
    context = contexts[min(contexts)]
    signal = context.features[30][0]
    candidate = SpotCandidate(795, 809, 30, 0.75, 0.35)
    first = research._episode(context, signal, candidate)
    changed_signal = research.replace(signal, drawdown_pct=0.91, near_low_pct=0.07)
    second = research._episode(context, changed_signal, candidate)
    assert first["observed_drawdown_pct"] == 1.25
    assert second["observed_drawdown_pct"] == 0.91
    assert second["observed_near_low_pct"] == 0.07
    assert first["legs"] == second["legs"]
    assert context.outcome_cache[0]["observed_drawdown_pct"] == 2.0
