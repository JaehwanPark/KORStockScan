from __future__ import annotations

import copy
from datetime import date, datetime, timedelta

import pytest

from src.engine.monitoring import pure_market_adaptive_opportunity_replay as adaptive
from src.engine.monitoring import pure_market_reversal_replay as base


def _bar(minute: int, price: int, *, volume: int = 100) -> base.Bar:
    return base.Bar(
        symbol="005930",
        venue="KRX",
        session="KRX_REGULAR",
        timestamp=datetime(2026, 8, 10, 9, 0) + timedelta(minutes=minute),
        open=price,
        high=price + 1,
        low=price - 1,
        close=price,
        volume=volume,
        source="test",
    )


def test_oracle_uses_cost_only_and_finds_multiple_profitable_swings():
    bars = [_bar(index, price) for index, price in enumerate([100, 100, 110, 90, 120])]

    actions, trades, summary = adaptive._optimal_actions(bars, cost_pct=0.20)

    assert [row["entry_price"] for row in trades] == [100.0, 90.0]
    assert [row["exit_price"] for row in trades] == [110.0, 120.0]
    assert actions[0] == 1
    assert actions[1] == -1
    assert actions[2] == 1
    assert summary["trade_count"] == 2
    assert summary["compounded_return_pct"] > 40.0


def test_oracle_rejects_move_that_does_not_pay_round_trip_cost():
    bars = [
        _bar(index, price)
        for index, price in enumerate([100_000, 100_000, 100_100, 100_050])
    ]

    actions, trades, summary = adaptive._optimal_actions(bars, cost_pct=0.20)

    assert actions == {}
    assert trades == []
    assert summary["compounded_return_pct"] == 0.0


def test_oracle_cost_sensitivity_keeps_venue_and_cost_provenance():
    bars = [_bar(index, price) for index, price in enumerate([100, 100, 110, 90, 120])]

    result = adaptive._oracle_cost_sensitivity(bars, cost_pcts=(0.2, 20.0))

    assert result["KRX"][0] == {
        "round_trip_cost_pct": 0.2,
        "oracle_trade_count": 2,
        "trading_date_count": 1,
        "avg_oracle_trades_per_date": 2.0,
        "equal_weight_avg_profit_pct": 21.423334,
        "authority": "ex_post_opportunity_density_upper_bound_only",
    }
    assert result["KRX"][1]["oracle_trade_count"] == 1
    assert result["NXT"][0]["trading_date_count"] == 0


def test_causal_feature_is_unchanged_when_future_bars_are_added():
    stock = [_bar(index, 10_000 + index * 2, volume=100 + index) for index in range(25)]
    kospi = [
        base.Bar(
            symbol="KOSPI",
            venue="KRX",
            session="KRX_REGULAR",
            timestamp=bar.timestamp,
            open=300_000 + index,
            high=300_001 + index,
            low=299_999 + index,
            close=300_000 + index,
            volume=1_000,
            source="test",
        )
        for index, bar in enumerate(stock)
    ]
    stock_map = {bar.timestamp: bar for bar in stock}
    kospi_map = {bar.timestamp: bar for bar in kospi}
    before = adaptive._feature_vector(
        stock,
        22,
        stock_by_timestamp=stock_map,
        kospi_by_timestamp=kospi_map,
    )

    stock.extend(_bar(index, 20_000 + index * 100) for index in range(25, 30))
    stock_map.update({bar.timestamp: bar for bar in stock[25:]})
    after = adaptive._feature_vector(
        stock,
        22,
        stock_by_timestamp=stock_map,
        kospi_by_timestamp=kospi_map,
    )

    assert before == after
    assert before is not None
    assert len(before) == len(adaptive.FEATURE_NAMES)


def test_session_progress_uses_known_clock_bounds_not_future_bar_count():
    bar = _bar(195, 10_000)

    assert adaptive._session_progress(bar) == pytest.approx(0.5)


def test_metric_contract_forbids_oracle_and_future_runtime_use():
    forbidden = adaptive.METRIC_CONTRACT["forbidden_uses"]

    assert "oracle_action_as_live_input" in forbidden
    assert "future_price_or_outcome_as_feature" in forbidden
    assert "real_order_submission" in forbidden


def test_scored_probability_keeps_row_identity_across_session_groups():
    class _Model:
        def predict_proba(self, matrix):
            probabilities = matrix[:, 0]
            return __import__("numpy").column_stack(
                [1.0 - probabilities, probabilities]
            )

    feature_count = len(adaptive.FEATURE_NAMES)
    rows = []
    for minute, session, probability in [
        (0, "KRX_REGULAR", 0.1),
        (1, "NXT_AFTERMARKET", 0.2),
        (2, "KRX_REGULAR", 0.3),
        (3, "NXT_AFTERMARKET", 0.4),
    ]:
        decision_at = datetime(2026, 8, 10, 9, 0) + timedelta(minutes=minute)
        rows.append(
            adaptive.FeatureRow(
                trade_date=decision_at.date(),
                venue="NXT",
                session=session,
                decision_at=decision_at,
                execution_at=decision_at + timedelta(minutes=1),
                execution_price=10_000.0,
                session_close_price=10_000.0,
                features=(probability,) + (0.0,) * (feature_count - 1),
                oracle_action=0,
            )
        )

    _, scored = adaptive._simulate_evaluation_rows(
        rows,
        buy_model=_Model(),
        buy_threshold=2.0,
        sell_model=_Model(),
        sell_threshold=2.0,
        cost_pct=0.2,
    )

    score_by_time = {row.decision_at: buy_score for row, buy_score, _ in scored}
    assert score_by_time == {
        row.decision_at: pytest.approx(row.features[0]) for row in rows
    }


def test_confidence_slice_is_diagnostic_and_orders_without_outcome_selection():
    trades = [
        {"joint_transition_confidence": confidence, "net_profit_pct": profit}
        for confidence, profit in [(0.9, 1.0), (0.8, 0.5), (0.7, -1.0), (0.6, -1.0)]
    ]

    result = adaptive._confidence_diagnostics(trades)

    assert result["role"] == "post_oos_confidence_slice_diagnostic_only"
    assert result["top_slices"]["top_50pct"]["sample_count"] == 2
    assert result["top_slices"]["top_50pct"]["equal_weight_avg_profit_pct"] == 0.75
    assert "runtime_apply" in result["forbidden_use"]


def test_holding_cap_is_selected_only_from_prior_oracle_durations():
    feature_count = len(adaptive.FEATURE_NAMES)
    rows = []
    for minute, action in [(0, 1), (2, -1), (3, 1), (8, -1)]:
        decision_at = datetime(2026, 8, 10, 9, 0) + timedelta(minutes=minute)
        rows.append(
            adaptive.FeatureRow(
                trade_date=decision_at.date(),
                venue="KRX",
                session="KRX_REGULAR",
                decision_at=decision_at,
                execution_at=decision_at + timedelta(minutes=1),
                execution_price=10_000.0,
                session_close_price=10_000.0,
                features=(0.0,) * feature_count,
                oracle_action=action,
            )
        )

    result = adaptive._historical_oracle_hold_cap(rows)

    assert result is not None
    assert result["max_hold_minutes"] == 5
    assert result["source_sample_count"] == 2
    assert result["selection_policy"] == "prior_train_oracle_duration_75th_percentile"


def test_buy_probability_arms_then_positive_acceleration_confirms_entry():
    class _ColumnModel:
        def __init__(self, index):
            self.index = index

        def predict_proba(self, matrix):
            probabilities = matrix[:, self.index]
            return __import__("numpy").column_stack(
                [1.0 - probabilities, probabilities]
            )

    rows = []
    for minute, return_1m, acceleration, buy_probability, sell_probability in [
        (0, -1.0, -1.0, 0.9, 0.1),
        (1, 0.5, 0.0, 0.4, 0.1),
        (2, 0.2, 0.1, 0.2, 0.9),
    ]:
        decision_at = datetime(2026, 8, 10, 9, 0) + timedelta(minutes=minute)
        features = [0.0] * len(adaptive.FEATURE_NAMES)
        features[0] = return_1m
        features[4] = acceleration
        features[15] = buy_probability
        features[16] = sell_probability
        rows.append(
            adaptive.FeatureRow(
                trade_date=decision_at.date(),
                venue="KRX",
                session="KRX_REGULAR",
                decision_at=decision_at,
                execution_at=decision_at + timedelta(minutes=1),
                execution_price=10_000.0 + minute * 100,
                session_close_price=10_200.0,
                features=tuple(features),
                oracle_action=0,
            )
        )

    trades, _ = adaptive._simulate_evaluation_rows(
        rows,
        buy_model=_ColumnModel(15),
        buy_threshold=0.8,
        sell_model=_ColumnModel(16),
        sell_threshold=0.8,
        cost_pct=0.2,
        max_hold_minutes=5,
    )

    assert len(trades) == 1
    assert trades[0]["candidate_armed_at"] == rows[0].decision_at.isoformat()
    assert trades[0]["entry_at"] == rows[1].execution_at.isoformat()
    assert trades[0]["exit_at"] == rows[2].execution_at.isoformat()
    assert trades[0]["entry_reason"] == "adaptive_buy_armed_recovery_confirmed"
    assert trades[0]["pairability_lane"] == "weak_reversal"
    assert len(trades[0]["pairability_features"]) == len(
        adaptive.PAIRABILITY_FEATURE_NAMES
    )


def _pairability_trade(day_offset: int, index: int, *, positive: bool):
    trade_date = (datetime(2026, 7, 1) + timedelta(days=day_offset)).date()
    feature_value = 1.0 if positive else -1.0
    return {
        "trade_date": trade_date.isoformat(),
        "pairability_features": [feature_value]
        * len(adaptive.PAIRABILITY_FEATURE_NAMES),
        "pairability_lane": ("bullish_transition" if positive else "weak_reversal"),
        "exit_reason": (
            "adaptive_sell_probability" if positive else "prior_duration_cap_next_open"
        ),
        "net_profit_pct": 0.5 if positive else -0.5,
        "entry_price": 10_000.0 + index,
    }


def test_pairability_model_uses_chronological_prior_oos_episodes():
    prior = [
        _pairability_trade(day_offset, index, positive=index % 2 == 0)
        for day_offset in range(8)
        for index in range(4)
    ]

    bundle = adaptive._fit_pairability_model(prior)

    assert bundle is not None
    _, threshold, meta = bundle
    assert 0.0 <= threshold <= 1.0
    assert meta["history_date_count"] == 8
    assert meta["history_episode_count"] == 32
    assert set(meta["fit_dates"]).isdisjoint(meta["validation_dates"])
    assert max(meta["fit_dates"]) < min(meta["validation_dates"])
    assert meta["selection_policy"] == (
        "chronological_prior_validation_max_ev_then_simple_sum"
    )


def test_pairability_gate_rejects_candidate_then_reopens_state_for_next_candidate():
    class _ColumnModel:
        def __init__(self, index):
            self.index = index

        def predict_proba(self, matrix):
            probabilities = matrix[:, self.index]
            return __import__("numpy").column_stack(
                [1.0 - probabilities, probabilities]
            )

    class _PairModel:
        def predict_proba(self, matrix):
            probabilities = (matrix[:, 0] + 1.0) / 2.0
            return __import__("numpy").column_stack(
                [1.0 - probabilities, probabilities]
            )

    rows = []
    for minute, return_1m, acceleration, buy_probability, sell_probability in [
        (0, -1.0, -1.0, 0.9, 0.1),
        (1, 0.5, 0.0, 0.4, 0.1),
        (2, 1.0, -1.0, 0.9, 0.1),
        (3, 0.5, 0.0, 0.4, 0.1),
        (4, 0.2, 0.1, 0.2, 0.9),
    ]:
        decision_at = datetime(2026, 8, 10, 9, 0) + timedelta(minutes=minute)
        features = [0.0] * len(adaptive.FEATURE_NAMES)
        features[0] = return_1m
        features[4] = acceleration
        features[15] = buy_probability
        features[16] = sell_probability
        rows.append(
            adaptive.FeatureRow(
                trade_date=decision_at.date(),
                venue="KRX",
                session="KRX_REGULAR",
                decision_at=decision_at,
                execution_at=decision_at + timedelta(minutes=1),
                execution_price=10_000.0 + minute * 100,
                session_close_price=10_400.0,
                features=tuple(features),
                oracle_action=0,
            )
        )

    trades, _ = adaptive._simulate_evaluation_rows(
        rows,
        buy_model=_ColumnModel(15),
        buy_threshold=0.8,
        sell_model=_ColumnModel(16),
        sell_threshold=0.8,
        cost_pct=0.2,
        max_hold_minutes=5,
        pairability_model=_PairModel(),
        pairability_threshold=0.5,
    )

    assert len(trades) == 1
    assert trades[0]["candidate_armed_at"] == rows[2].decision_at.isoformat()
    assert trades[0]["entry_at"] == rows[3].execution_at.isoformat()
    assert trades[0]["pairability_selected"] is True
    assert trades[0]["pairability_probability"] == 1.0


@pytest.mark.parametrize(
    ("source_passed", "floor_passed", "sample_count", "ev", "expected"),
    [
        (False, True, 10, 0.5, "source_quality_blocked"),
        (True, False, 10, 0.5, "insufficient_coverage_dates"),
        (True, True, 0, None, "insufficient_pairability_labels"),
        (True, True, 10, 0.1, "pairability_oos_positive"),
        (True, True, 10, -0.1, "pairability_detected_execution_negative"),
    ],
)
def test_pairability_decision_preserves_source_and_evidence_boundaries(
    source_passed, floor_passed, sample_count, ev, expected
):
    assert (
        adaptive._pairability_decision(
            {
                "sample_count": sample_count,
                "equal_weight_avg_profit_pct": ev,
            },
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def test_competing_risk_candidate_uses_first_causal_transition_without_duration_cap():
    class _ColumnModel:
        def __init__(self, index):
            self.index = index

        def predict_proba(self, matrix):
            probabilities = matrix[:, self.index]
            return __import__("numpy").column_stack(
                [1.0 - probabilities, probabilities]
            )

    rows = []
    for minute, return_1m, acceleration, buy_probability, sell_probability in [
        (0, -1.0, -1.0, 0.9, 0.1),
        (1, 0.5, 0.0, 0.4, 0.1),
        (2, 0.1, 0.0, 0.2, 0.2),
        (3, 0.2, 0.1, 0.1, 0.9),
    ]:
        decision_at = datetime(2026, 8, 10, 9, 0) + timedelta(minutes=minute)
        features = [0.0] * len(adaptive.FEATURE_NAMES)
        features[0] = return_1m
        features[4] = acceleration
        features[15] = buy_probability
        features[16] = sell_probability
        rows.append(
            adaptive.FeatureRow(
                trade_date=decision_at.date(),
                venue="KRX",
                session="KRX_REGULAR",
                decision_at=decision_at,
                execution_at=decision_at + timedelta(minutes=1),
                execution_price=10_000.0 + minute * 100,
                session_close_price=10_300.0,
                features=tuple(features),
                oracle_action=0,
            )
        )

    candidates = adaptive._extract_competing_risk_candidates(
        rows,
        buy_model=_ColumnModel(15),
        buy_threshold=0.8,
        sell_model=_ColumnModel(16),
        sell_threshold=0.8,
        cost_pct=0.2,
    )

    assert len(candidates) == 1
    assert candidates[0]["first_event"] == "sell_transition"
    assert candidates[0]["entry_at"] == rows[1].execution_at.isoformat()
    assert candidates[0]["exit_at"] == rows[3].execution_at.isoformat()
    assert candidates[0]["event_duration_minutes"] == 2.0
    assert candidates[0]["pairability_lane"] == "weak_reversal"


def test_competing_risk_session_end_uses_last_execution_timestamp():
    class _ColumnModel:
        def __init__(self, index):
            self.index = index

        def predict_proba(self, matrix):
            probabilities = matrix[:, self.index]
            return __import__("numpy").column_stack(
                [1.0 - probabilities, probabilities]
            )

    rows = []
    for minute, return_1m, acceleration, buy_probability, sell_probability in [
        (0, -1.0, -1.0, 0.9, 0.1),
        (1, 0.5, 0.0, 0.4, 0.1),
        (2, 0.1, 0.0, 0.2, 0.2),
    ]:
        decision_at = datetime(2026, 8, 10, 9, 0) + timedelta(minutes=minute)
        features = [0.0] * len(adaptive.FEATURE_NAMES)
        features[0] = return_1m
        features[4] = acceleration
        features[15] = buy_probability
        features[16] = sell_probability
        rows.append(
            adaptive.FeatureRow(
                trade_date=decision_at.date(),
                venue="KRX",
                session="KRX_REGULAR",
                decision_at=decision_at,
                execution_at=decision_at + timedelta(minutes=1),
                execution_price=10_000.0 + minute * 100,
                session_close_price=10_300.0,
                features=tuple(features),
                oracle_action=0,
            )
        )

    candidates = adaptive._extract_competing_risk_candidates(
        rows,
        buy_model=_ColumnModel(15),
        buy_threshold=0.8,
        sell_model=_ColumnModel(16),
        sell_threshold=0.8,
        cost_pct=0.2,
    )

    assert candidates[0]["first_event"] == "session_end_censored"
    assert candidates[0]["exit_at"] == rows[-1].execution_at.isoformat()


def test_competing_risk_scoring_uses_direct_predicted_ev():
    class _EventModel:
        classes_ = __import__("numpy").array([0, 1])

        def predict_proba(self, matrix):
            probability = (matrix[:, 0] + 1.0) / 2.0
            return __import__("numpy").column_stack([1.0 - probability, probability])

    class _EvModel:
        def predict(self, matrix):
            return matrix[:, 0]

    candidates = []
    for value in (-0.2, 0.3):
        row = _pairability_trade(0, int(value > 0), positive=value > 0)
        row["competing_risk_features"] = [value] * len(
            adaptive.PAIRABILITY_FEATURE_NAMES
        )
        row["first_event"] = (
            "sell_transition" if value > 0 else "adverse_buy_transition"
        )
        row["first_event_label"] = int(value > 0)
        candidates.append(row)

    scored = adaptive._score_competing_risk_candidates(
        candidates,
        event_model=_EventModel(),
        ev_model=_EvModel(),
    )

    assert [row["competing_risk_selected"] for row in scored] == [False, True]
    assert [row["predicted_cost_adjusted_ev_pct"] for row in scored] == [-0.2, 0.3]


def test_lane_competing_risk_model_uses_only_chronological_lane_history():
    candidates = []
    for day_offset in range(8):
        for index in range(6):
            positive = index % 2 == 0
            row = _pairability_trade(day_offset, index, positive=positive)
            row["pairability_lane"] = "weak_reversal"
            row["competing_risk_features"] = row.pop("pairability_features")
            row["first_event"] = (
                "sell_transition" if positive else "adverse_buy_transition"
            )
            row["first_event_label"] = int(positive)
            entry_at = datetime.combine(
                date.fromisoformat(row["trade_date"]), datetime.min.time()
            ).replace(hour=9, minute=index)
            row.update(
                {
                    "venue": "KRX",
                    "session": "KRX_REGULAR",
                    "entry_at": entry_at.isoformat(),
                    "exit_at": (entry_at + timedelta(minutes=1)).isoformat(),
                }
            )
            candidates.append(row)

    bundle = adaptive._fit_lane_competing_risk_model(candidates, lane="weak_reversal")

    assert bundle is not None
    _, _, meta = bundle
    assert meta["lane"] == "weak_reversal"
    assert meta["history_date_count"] == 8
    assert set(meta["fit_dates"]).isdisjoint(meta["validation_dates"])
    assert max(meta["fit_dates"]) < min(meta["validation_dates"])
    assert meta["selection_policy"] == "direct_predicted_cost_adjusted_ev_gt_zero"


@pytest.mark.parametrize(
    ("source_passed", "floor_passed", "control_ev", "selected_ev", "expected"),
    [
        (False, True, -0.2, 0.2, "source_quality_blocked"),
        (True, False, -0.2, 0.2, "insufficient_coverage_dates"),
        (True, True, -0.2, 0.1, "lane_competing_risk_oos_positive"),
        (True, True, -0.2, -0.1, "lane_ev_improved_but_negative"),
        (True, True, -0.1, -0.2, "no_incremental_predictive_value"),
    ],
)
def test_competing_risk_decision_boundaries(
    source_passed, floor_passed, control_ev, selected_ev, expected
):
    assert (
        adaptive._competing_risk_decision(
            {"sample_count": 10, "source_quality_adjusted_ev_pct": selected_ev},
            {"sample_count": 10, "source_quality_adjusted_ev_pct": control_ev},
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def test_competing_risk_decision_does_not_fallback_to_unadjusted_ev():
    assert (
        adaptive._competing_risk_decision(
            {
                "sample_count": 10,
                "equal_weight_avg_profit_pct": 0.5,
                "source_quality_adjusted_ev_pct": None,
            },
            {
                "sample_count": 10,
                "equal_weight_avg_profit_pct": -0.5,
                "source_quality_adjusted_ev_pct": None,
            },
            sample_floor_passed=True,
            source_quality_passed=True,
        )
        == "no_incremental_predictive_value"
    )


def _economic_candidate(
    day_offset: int,
    index: int,
    *,
    favorable: bool,
    lane: str = "weak_reversal",
):
    trade_date = date(2026, 7, 1) + timedelta(days=day_offset)
    entry_at = datetime.combine(trade_date, datetime.min.time()).replace(
        hour=9, minute=index * 3
    )
    entry_price = 100.0
    reference_price = 101.0 if favorable else 99.0
    return {
        "trade_date": trade_date.isoformat(),
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "candidate_armed_at": (entry_at - timedelta(minutes=1)).isoformat(),
        "entry_at": entry_at.isoformat(),
        "entry_price": entry_price,
        "pairability_lane": lane,
        "economic_features": [float(favorable), float(index)]
        + [0.0] * (len(adaptive.ECONOMIC_FEATURE_NAMES) - 3)
        + [0.2],
        "candidate_age_minutes": 1.0,
        "volatility_scale_pct": 0.2,
        "_economic_path": [
            {
                "observed_at": (entry_at + timedelta(minutes=1)).isoformat(),
                "execution_at": (entry_at + timedelta(minutes=2)).isoformat(),
                "reference_price": reference_price,
                "execution_price": reference_price,
                "point_type": "completed_close_next_open",
                "return_3m_vol_units": -1.0 if not favorable else 1.0,
                "return_5m_vol_units": -1.0 if not favorable else 1.0,
                "acceleration_vol_units": -1.0 if not favorable else 1.0,
                "decision_features": [0.0] * len(adaptive.FEATURE_NAMES),
            }
        ],
    }


def _recovery_candidate(
    day_offset: int,
    index: int,
    *,
    recovers: bool,
    lane: str = "weak_reversal",
):
    candidate = _economic_candidate(day_offset, index, favorable=False, lane=lane)
    entry_at = datetime.fromisoformat(candidate["entry_at"])
    adverse_features = [0.0] * len(adaptive.FEATURE_NAMES)
    adverse_features[1] = -1.0
    adverse_features[2] = -1.0
    adverse_features[4] = -1.0
    adverse_features[6] = 0.2
    adverse_features[7] = -1.0
    adverse_features[8] = 0.1
    adverse_features[15] = 0.2
    terminal_price = 101.2 if recovers else 98.0
    candidate["_economic_path"] = [
        {
            "observed_at": (entry_at + timedelta(minutes=1)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=2)).isoformat(),
            "reference_price": 99.7,
            "execution_price": 99.7,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": -1.0,
            "return_5m_vol_units": -1.0,
            "acceleration_vol_units": -1.0,
            "decision_features": adverse_features,
        },
        {
            "observed_at": (entry_at + timedelta(minutes=2)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=3)).isoformat(),
            "reference_price": 99.6,
            "execution_price": 99.6,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": -1.0,
            "return_5m_vol_units": -1.0,
            "acceleration_vol_units": -1.0,
            "decision_features": adverse_features,
        },
        {
            "observed_at": (entry_at + timedelta(minutes=4)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=5)).isoformat(),
            "reference_price": terminal_price,
            "execution_price": terminal_price,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": 1.0 if recovers else -2.0,
            "return_5m_vol_units": 1.0 if recovers else -2.0,
            "acceleration_vol_units": 1.0 if recovers else -1.0,
            "decision_features": adverse_features,
        },
    ]
    return candidate


def _trailing_candidate(
    day_offset: int,
    index: int,
    *,
    beneficial: bool,
    lane: str = "weak_reversal",
):
    candidate = _economic_candidate(day_offset, index, favorable=True, lane=lane)
    entry_at = datetime.fromisoformat(candidate["entry_at"])
    favorable_features = [0.0] * len(adaptive.FEATURE_NAMES)
    favorable_features[1] = 1.0
    favorable_features[2] = 1.0
    favorable_features[4] = 1.0
    favorable_features[6] = 0.8
    favorable_features[7] = 1.0
    favorable_features[8] = 0.4
    favorable_features[15] = 0.3
    peak_price = 102.0 if beneficial else 100.5
    final_price = 101.5 if beneficial else 100.4
    candidate["_economic_path"] = [
        {
            "observed_at": (entry_at + timedelta(minutes=1)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=2)).isoformat(),
            "reference_price": 101.0,
            "execution_price": 101.0,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": 1.0,
            "return_5m_vol_units": 1.0,
            "acceleration_vol_units": 1.0,
            "decision_features": favorable_features,
        },
        {
            "observed_at": (entry_at + timedelta(minutes=2)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=3)).isoformat(),
            "reference_price": peak_price,
            "execution_price": peak_price,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": 1.0 if beneficial else -1.0,
            "return_5m_vol_units": 1.0 if beneficial else -1.0,
            "acceleration_vol_units": 1.0 if beneficial else -1.0,
            "decision_features": favorable_features,
        },
        {
            "observed_at": (entry_at + timedelta(minutes=3)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=4)).isoformat(),
            "reference_price": final_price,
            "execution_price": final_price,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": -1.0,
            "return_5m_vol_units": 0.5 if beneficial else -1.0,
            "acceleration_vol_units": -1.0,
            "decision_features": favorable_features,
        },
    ]
    return candidate


def test_economic_candidate_path_starts_after_causal_next_open_entry():
    class _ColumnModel:
        def __init__(self, index):
            self.index = index

        def predict_proba(self, matrix):
            probabilities = matrix[:, self.index]
            return __import__("numpy").column_stack(
                [1.0 - probabilities, probabilities]
            )

    rows = []
    for minute, return_1m, acceleration, buy_probability, sell_probability in [
        (0, -1.0, -1.0, 0.9, 0.1),
        (1, 0.5, 0.0, 0.4, 0.1),
        (2, 0.2, 0.1, 0.2, 0.2),
    ]:
        decision_at = datetime(2026, 8, 10, 9, 0) + timedelta(minutes=minute)
        features = [0.0] * len(adaptive.FEATURE_NAMES)
        features[0] = return_1m
        features[4] = acceleration
        features[15] = buy_probability
        features[16] = sell_probability
        rows.append(
            adaptive.FeatureRow(
                trade_date=decision_at.date(),
                venue="KRX",
                session="KRX_REGULAR",
                decision_at=decision_at,
                execution_at=decision_at + timedelta(minutes=1),
                execution_price=100.0 + minute,
                session_close_price=104.0,
                features=tuple(features),
                oracle_action=0,
                decision_close_price=101.0 + minute,
                volatility_scale_pct=0.25,
            )
        )

    candidates = adaptive._extract_economic_first_passage_candidates(
        rows,
        buy_model=_ColumnModel(15),
        buy_threshold=0.8,
        sell_model=_ColumnModel(16),
        sell_threshold=0.8,
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["entry_at"] == rows[1].execution_at.isoformat()
    assert candidate["candidate_armed_execution_at"] == rows[0].execution_at.isoformat()
    assert candidate["volatility_scale_pct"] == pytest.approx(0.25)
    assert (
        candidate["_economic_path"][0]["observed_at"] == rows[2].decision_at.isoformat()
    )
    assert (
        candidate["_economic_path"][0]["execution_at"]
        == rows[2].execution_at.isoformat()
    )
    assert candidate["_economic_path"][-1]["point_type"] == "session_close_mark"
    assert candidate["_economic_path"][0]["buy_probability"] == pytest.approx(0.2)
    assert candidate["_economic_path"][0]["sell_probability"] == pytest.approx(0.2)
    assert candidate["_economic_path"][0]["volatility_scale_pct"] == pytest.approx(0.25)
    assert len(candidate["economic_features"]) == len(adaptive.ECONOMIC_FEATURE_NAMES)
    assert candidate["economic_features"][-1] == pytest.approx(0.25)


def test_economic_first_passage_uses_cost_plus_causal_volatility_boundary():
    episode = adaptive._apply_economic_first_passage_policy(
        _economic_candidate(0, 0, favorable=True),
        target_vol_multiplier=1.0,
        adverse_vol_multiplier=1.0,
        cost_pct=0.2,
    )

    assert episode["favorable_boundary_pct"] == pytest.approx(0.4)
    assert episode["adverse_boundary_pct"] == pytest.approx(0.2)
    assert episode["economic_first_passage_event"] == "favorable_first_passage"
    assert episode["exit_reason"] == "favorable_first_passage"
    assert episode["net_profit_pct"] > 0.0
    assert "_economic_path" not in episode


def test_economic_first_passage_stops_at_first_adverse_close_and_next_open():
    candidate = _economic_candidate(0, 0, favorable=False)
    candidate["_economic_path"] = [
        {
            "observed_at": "2026-07-01T09:01:00",
            "execution_at": "2026-07-01T09:02:00",
            "reference_price": 99.7,
            "execution_price": 99.6,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": -1.0,
            "return_5m_vol_units": -1.0,
            "acceleration_vol_units": -1.0,
        },
        {
            "observed_at": "2026-07-01T09:02:00",
            "execution_at": "2026-07-01T09:03:00",
            "reference_price": 99.6,
            "execution_price": 99.5,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": -1.0,
            "return_5m_vol_units": -1.0,
            "acceleration_vol_units": -1.0,
        },
        {
            "observed_at": "2026-07-01T09:03:00",
            "execution_at": "2026-07-01T09:04:00",
            "reference_price": 101.0,
            "execution_price": 101.0,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": 1.0,
            "return_5m_vol_units": 1.0,
            "acceleration_vol_units": 1.0,
        },
    ]

    episode = adaptive._apply_economic_first_passage_policy(
        candidate,
        target_vol_multiplier=1.0,
        adverse_vol_multiplier=1.0,
        cost_pct=0.2,
    )

    assert episode["economic_first_passage_event"] == "adverse_first_passage"
    assert episode["exit_at"] == "2026-07-01T09:03:00"
    assert episode["exit_price"] == 99.5
    assert episode["adverse_breach_streak_at_exit"] == 2
    assert episode["adverse_confirmation_reason"] == "two_consecutive_boundary_breaches"
    assert episode["mfe_pct"] == pytest.approx(-0.3)
    assert episode["mae_pct"] == pytest.approx(-0.4)
    assert episode["post_entry_session_mfe_pct"] == pytest.approx(1.0)


def test_weak_reversal_does_not_exit_on_single_adverse_breach_before_rebound():
    candidate = _economic_candidate(0, 0, favorable=False)
    candidate["_economic_path"] = [
        {
            "observed_at": "2026-07-01T09:01:00",
            "execution_at": "2026-07-01T09:02:00",
            "reference_price": 99.7,
            "execution_price": 99.6,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": -1.0,
            "return_5m_vol_units": -1.0,
            "acceleration_vol_units": -1.0,
        },
        {
            "observed_at": "2026-07-01T09:02:00",
            "execution_at": "2026-07-01T09:03:00",
            "reference_price": 101.0,
            "execution_price": 100.9,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": 1.0,
            "return_5m_vol_units": 1.0,
            "acceleration_vol_units": 1.0,
        },
    ]

    episode = adaptive._apply_economic_first_passage_policy(
        candidate,
        target_vol_multiplier=1.0,
        adverse_vol_multiplier=1.0,
        cost_pct=0.2,
    )

    assert episode["economic_first_passage_event"] == "favorable_first_passage"
    assert episode["exit_at"] == "2026-07-01T09:03:00"


def test_bullish_transition_exits_single_breach_with_confirmed_trend_damage():
    candidate = _economic_candidate(0, 0, favorable=False, lane="bullish_transition")
    candidate["_economic_path"] = [
        {
            "observed_at": "2026-07-01T09:01:00",
            "execution_at": "2026-07-01T09:02:00",
            "reference_price": 99.7,
            "execution_price": 99.6,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": -1.0,
            "return_5m_vol_units": -1.0,
            "acceleration_vol_units": -1.0,
        },
        {
            "observed_at": "2026-07-01T09:02:00",
            "execution_at": "2026-07-01T09:03:00",
            "reference_price": 101.0,
            "execution_price": 101.0,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": 1.0,
            "return_5m_vol_units": 1.0,
            "acceleration_vol_units": 1.0,
        },
    ]

    episode = adaptive._apply_economic_first_passage_policy(
        candidate,
        target_vol_multiplier=1.0,
        adverse_vol_multiplier=1.0,
        cost_pct=0.2,
    )

    assert episode["economic_first_passage_event"] == "adverse_first_passage"
    assert episode["exit_at"] == "2026-07-01T09:02:00"
    assert episode["adverse_breach_streak_at_exit"] == 1
    assert (
        episode["adverse_confirmation_reason"] == "bullish_negative_3m_5m_acceleration"
    )


def test_lane_economic_first_passage_model_uses_only_prior_lane_dates():
    candidates = [
        _economic_candidate(day_offset, index, favorable=index % 2 == 0)
        for day_offset in range(8)
        for index in range(8)
    ]

    bundle = adaptive._fit_lane_economic_first_passage_model(
        candidates,
        lane="weak_reversal",
        cost_pct=0.2,
    )

    assert bundle is not None
    _, _, policy, meta = bundle
    assert policy["target_vol_multiplier"] in adaptive.ECONOMIC_TARGET_VOL_MULTIPLIERS
    assert policy["adverse_vol_multiplier"] in adaptive.ECONOMIC_ADVERSE_VOL_MULTIPLIERS
    assert meta["history_date_count"] == 8
    assert set(meta["fit_dates"]).isdisjoint(meta["validation_dates"])
    assert max(meta["fit_dates"]) < min(meta["validation_dates"])
    assert meta["selection_policy"] == "direct_predicted_cost_adjusted_ev_gt_zero"


@pytest.mark.parametrize(
    ("source_passed", "floor_passed", "control_ev", "selected_ev", "expected"),
    [
        (False, True, -0.2, 0.2, "source_quality_blocked"),
        (True, False, -0.2, 0.2, "insufficient_coverage_dates"),
        (True, True, -0.2, 0.1, "economic_first_passage_oos_positive"),
        (
            True,
            True,
            -0.2,
            -0.1,
            "economic_first_passage_improved_but_negative",
        ),
        (True, True, -0.1, -0.2, "no_incremental_predictive_value"),
    ],
)
def test_economic_first_passage_decision_boundaries(
    source_passed, floor_passed, control_ev, selected_ev, expected
):
    assert (
        adaptive._economic_first_passage_decision(
            {"source_quality_adjusted_ev_pct": selected_ev},
            {"source_quality_adjusted_ev_pct": control_ev},
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def test_recovery_checkpoint_contains_only_causal_adverse_state():
    checkpoint = adaptive._recovery_checkpoint(
        _recovery_candidate(0, 0, recovers=True),
        target_vol_multiplier=1.0,
        adverse_vol_multiplier=1.0,
        cost_pct=0.2,
    )

    assert checkpoint is not None
    assert checkpoint["checkpoint_index"] == 1
    assert checkpoint["confirmation_reason"] == "two_consecutive_boundary_breaches"
    assert len(checkpoint["recovery_features"]) == len(adaptive.RECOVERY_FEATURE_NAMES)
    assert "post_entry_session_mfe_pct" not in checkpoint
    assert "_economic_path" not in checkpoint


def test_recovery_defer_can_reach_later_favorable_boundary():
    candidate = _recovery_candidate(0, 0, recovers=True)
    policy = {
        "target_vol_multiplier": 1.0,
        "adverse_vol_multiplier": 1.0,
        "trailing_vol_multiplier": 0.0,
        "recovery_wait_minutes": 10.0,
        "recovery_deep_adverse_multiplier": 4.0,
    }

    immediate = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy=policy,
        cost_pct=0.2,
        force_recovery=False,
    )
    recovered = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy=policy,
        cost_pct=0.2,
        force_recovery=True,
    )

    assert immediate["exit_reason"] == "adverse_immediate_exit"
    assert recovered["exit_reason"] == "favorable_immediate_exit"
    assert recovered["recovery_deferred"] is True
    assert recovered["recovery_realized_minutes"] == pytest.approx(2.0)
    assert recovered["net_profit_pct"] > immediate["net_profit_pct"]


def test_recovery_defer_requires_positive_predicted_incremental_ev():
    class _EventModel:
        classes_ = __import__("numpy").asarray([0, 1])

        def predict_proba(self, matrix):
            return __import__("numpy").asarray([[0.4, 0.6] for _ in matrix])

    class _DeltaModel:
        def __init__(self, value):
            self.value = value

        def predict(self, matrix):
            return __import__("numpy").asarray([self.value for _ in matrix])

    policy = {
        "target_vol_multiplier": 1.0,
        "adverse_vol_multiplier": 1.0,
        "trailing_vol_multiplier": 0.0,
        "recovery_wait_minutes": 10.0,
        "recovery_deep_adverse_multiplier": 4.0,
    }
    candidate = _recovery_candidate(0, 0, recovers=True)

    blocked = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy=policy,
        cost_pct=0.2,
        recovery_models=(_EventModel(), _DeltaModel(-0.01), None, 2.0),
    )
    deferred = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy=policy,
        cost_pct=0.2,
        recovery_models=(_EventModel(), _DeltaModel(0.01), None, 2.0),
    )

    assert blocked["recovery_deferred"] is False
    assert blocked["exit_reason"] == "adverse_immediate_exit"
    assert deferred["recovery_deferred"] is True
    assert deferred["exit_reason"] == "favorable_immediate_exit"


def test_recovery_comparison_keeps_exact_economic_entry_cohort():
    economic_selected = [
        adaptive._apply_economic_first_passage_policy(
            _economic_candidate(0, index, favorable=True),
            target_vol_multiplier=1.0,
            adverse_vol_multiplier=1.0,
            cost_pct=0.2,
        )
        for index in range(3)
    ]
    recovery_by_entry = {
        adaptive._entry_identity(economic_selected[index]): {
            **economic_selected[index],
            "exit_reason": "recovery_timeout_exit",
        }
        for index in (0, 2)
    }

    baseline, recovery = adaptive._same_entry_recovery_cohort(
        economic_selected, recovery_by_entry
    )

    assert [row["entry_at"] for row in baseline] == [
        economic_selected[0]["entry_at"],
        economic_selected[2]["entry_at"],
    ]
    assert [row["entry_at"] for row in recovery] == [
        row["entry_at"] for row in baseline
    ]


def test_recovery_diagnostics_use_explicit_baseline_event_provenance():
    candidate = _recovery_candidate(0, 0, recovers=True)
    episode = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy={
            "target_vol_multiplier": 1.0,
            "adverse_vol_multiplier": 1.0,
            "trailing_vol_multiplier": 0.0,
            "recovery_wait_minutes": 10.0,
            "recovery_deep_adverse_multiplier": 4.0,
        },
        cost_pct=0.2,
        force_recovery=True,
    )
    episode["baseline_economic_first_passage_event"] = "adverse_first_passage"

    diagnostics = adaptive._recovery_path_diagnostics([episode])

    assert diagnostics["sample_count"] == 1
    assert diagnostics["adverse_first_then_later_favorable_count"] == 1
    assert diagnostics["recovery_deferred_count"] == 1


def test_favorable_trailing_extends_exit_until_causal_drawdown():
    candidate = _economic_candidate(0, 0, favorable=True)
    entry_at = datetime.fromisoformat(candidate["entry_at"])
    candidate["_economic_path"] = [
        {
            "observed_at": (entry_at + timedelta(minutes=1)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=2)).isoformat(),
            "reference_price": 101.0,
            "execution_price": 101.0,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": 1.0,
            "return_5m_vol_units": 1.0,
            "acceleration_vol_units": 1.0,
            "decision_features": [0.0] * len(adaptive.FEATURE_NAMES),
        },
        {
            "observed_at": (entry_at + timedelta(minutes=2)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=3)).isoformat(),
            "reference_price": 102.0,
            "execution_price": 102.0,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": 1.0,
            "return_5m_vol_units": 1.0,
            "acceleration_vol_units": 1.0,
            "decision_features": [0.0] * len(adaptive.FEATURE_NAMES),
        },
        {
            "observed_at": (entry_at + timedelta(minutes=3)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=4)).isoformat(),
            "reference_price": 101.5,
            "execution_price": 101.5,
            "point_type": "completed_close_next_open",
            "return_3m_vol_units": -1.0,
            "return_5m_vol_units": 1.0,
            "acceleration_vol_units": -1.0,
            "decision_features": [0.0] * len(adaptive.FEATURE_NAMES),
        },
    ]
    policy = {
        "target_vol_multiplier": 1.0,
        "adverse_vol_multiplier": 1.0,
        "trailing_vol_multiplier": 1.0,
        "recovery_wait_minutes": 5.0,
        "recovery_deep_adverse_multiplier": 1.5,
    }

    episode = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy=policy,
        cost_pct=0.2,
        force_recovery=False,
    )

    assert episode["exit_reason"] == "favorable_trailing_exit"
    assert episode["exit_price"] == pytest.approx(101.5)


def test_favorable_checkpoint_contains_only_completed_causal_state():
    candidate = _trailing_candidate(0, 0, beneficial=True)
    result = adaptive._baseline_favorable_checkpoint(
        candidate,
        boundary_policy={
            "target_vol_multiplier": 1.0,
            "adverse_vol_multiplier": 1.0,
        },
        cost_pct=0.2,
    )

    assert result is not None
    checkpoint, baseline = result
    assert baseline["economic_first_passage_event"] == "favorable_first_passage"
    assert checkpoint["checkpoint_index"] == 0
    assert len(checkpoint["trailing_features"]) == len(adaptive.TRAILING_FEATURE_NAMES)
    assert "post_entry_session_mfe_pct" not in checkpoint
    assert "_economic_path" not in checkpoint


def test_trailing_application_requires_positive_predicted_incremental_ev():
    class _EventModel:
        classes_ = __import__("numpy").asarray([0, 1])

        def predict_proba(self, matrix):
            return __import__("numpy").asarray([[0.3, 0.7] for _ in matrix])

    class _DeltaModel:
        def __init__(self, value):
            self.value = value

        def predict(self, matrix):
            return __import__("numpy").asarray([self.value for _ in matrix])

    candidate = _trailing_candidate(0, 0, beneficial=True)
    policy = {
        "target_vol_multiplier": 1.0,
        "adverse_vol_multiplier": 1.0,
        "trailing_vol_multiplier": 1.0,
        "recovery_wait_minutes": 5.0,
        "recovery_deep_adverse_multiplier": 1.5,
    }

    blocked = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy=policy,
        cost_pct=0.2,
        force_recovery=False,
        trailing_models=(_EventModel(), _DeltaModel(-0.01)),
    )
    applied = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy=policy,
        cost_pct=0.2,
        force_recovery=False,
        trailing_models=(_EventModel(), _DeltaModel(0.01)),
    )

    assert blocked["trailing_applied"] is False
    assert blocked["exit_reason"] == "favorable_immediate_exit"
    assert applied["trailing_applied"] is True
    assert applied["exit_reason"] == "favorable_trailing_exit"


def test_lane_trailing_model_uses_prior_validation_and_zero_baseline():
    candidates = [
        _trailing_candidate(day_offset, index, beneficial=index % 3 != 0)
        for day_offset in range(8)
        for index in range(8)
    ]

    bundle = adaptive._fit_lane_trailing_model(
        candidates,
        lane="weak_reversal",
        boundary_policy={
            "target_vol_multiplier": 1.0,
            "adverse_vol_multiplier": 1.0,
        },
        cost_pct=0.2,
    )

    assert bundle is not None
    models, multiplier, meta = bundle
    assert models is not None
    assert multiplier in adaptive.RECOVERY_TRAILING_VOL_MULTIPLIERS
    assert multiplier > 0.0
    assert set(meta["fit_dates"]).isdisjoint(meta["validation_dates"])
    assert max(meta["fit_dates"]) < min(meta["validation_dates"])
    assert meta["policy_grid"][0]["trailing_vol_multiplier"] == 0.0
    assert meta["policy_grid"][0]["avg_incremental_net_profit_pct"] == 0.0


def test_axis_cohort_preserves_exact_entries_for_all_arms():
    economic_selected = [
        adaptive._apply_economic_first_passage_policy(
            _economic_candidate(0, index, favorable=True),
            target_vol_multiplier=1.0,
            adverse_vol_multiplier=1.0,
            cost_pct=0.2,
        )
        for index in range(3)
    ]
    arm_maps = {
        arm: {
            adaptive._entry_identity(economic_selected[index]): {
                **economic_selected[index],
                "axis_arm": arm,
            }
            for index in (0, 2)
        }
        for arm in (
            "recovery_only",
            "trailing_only",
            "recovery_plus_trailing",
        )
    }

    arms = adaptive._same_entry_axis_cohort(economic_selected, arm_maps)

    expected = [economic_selected[0]["entry_at"], economic_selected[2]["entry_at"]]
    assert set(arms) == {
        "baseline",
        "recovery_only",
        "trailing_only",
        "recovery_plus_trailing",
    }
    assert all([row["entry_at"] for row in rows] == expected for rows in arms.values())


@pytest.mark.parametrize(
    ("baseline_ev", "recovery_ev", "trailing_ev", "combined_ev", "expected"),
    [
        (-0.2, 0.1, -0.2, -0.2, "recovery_only_oos_positive"),
        (-0.2, -0.2, 0.1, -0.2, "trailing_incremental_ev_positive"),
        (-0.2, -0.1, -0.2, -0.3, "axis_separation_improved_but_negative"),
        (-0.1, -0.2, -0.2, -0.2, "no_incremental_predictive_value"),
    ],
)
def test_axis_separation_decision_boundaries(
    baseline_ev, recovery_ev, trailing_ev, combined_ev, expected
):
    summaries = {
        "baseline": {
            "sample_count": 1,
            "source_quality_adjusted_ev_pct": baseline_ev,
        },
        "recovery_only": {
            "sample_count": 1,
            "source_quality_adjusted_ev_pct": recovery_ev,
        },
        "trailing_only": {
            "sample_count": 1,
            "source_quality_adjusted_ev_pct": trailing_ev,
        },
        "recovery_plus_trailing": {
            "sample_count": 1,
            "source_quality_adjusted_ev_pct": combined_ev,
        },
    }

    assert (
        adaptive._axis_separation_decision(
            summaries,
            sample_floor_passed=True,
            source_quality_passed=True,
        )
        == expected
    )


def test_lane_recovery_model_uses_prior_validation_and_separate_policy():
    candidates = [
        _recovery_candidate(day_offset, index, recovers=index % 2 == 0)
        for day_offset in range(8)
        for index in range(8)
    ]

    bundle = adaptive._fit_lane_recovery_aware_model(
        candidates,
        lane="weak_reversal",
        boundary_policy={
            "target_vol_multiplier": 1.0,
            "adverse_vol_multiplier": 1.0,
        },
        cost_pct=0.2,
    )

    assert bundle is not None
    _, policy, meta = bundle
    assert policy["recovery_wait_minutes"] in adaptive.RECOVERY_WAIT_MINUTES
    assert (
        policy["recovery_deep_adverse_multiplier"]
        in adaptive.RECOVERY_DEEP_ADVERSE_MULTIPLIERS
    )
    assert (
        policy["trailing_vol_multiplier"] in adaptive.RECOVERY_TRAILING_VOL_MULTIPLIERS
    )
    assert set(meta["fit_dates"]).isdisjoint(meta["validation_dates"])
    assert max(meta["fit_dates"]) < min(meta["validation_dates"])
    assert meta["recovery_selection"] == "predicted_incremental_ev_gt_zero"


def test_recovery_only_training_excludes_trailing_outcomes():
    candidates = [
        _recovery_candidate(day_offset, index, recovers=index % 2 == 0)
        for day_offset in range(8)
        for index in range(8)
    ]

    bundle = adaptive._fit_lane_recovery_aware_model(
        candidates,
        lane="weak_reversal",
        boundary_policy={
            "target_vol_multiplier": 1.0,
            "adverse_vol_multiplier": 1.0,
        },
        cost_pct=0.2,
        trailing_policy_enabled=False,
    )

    assert bundle is not None
    _, policy, meta = bundle
    assert policy["trailing_vol_multiplier"] == 0.0
    assert meta["trailing_policy_enabled_in_recovery_labels"] is False
    assert [
        row["trailing_vol_multiplier"] for row in meta["trailing_policy_results"]
    ] == [0.0]


def test_trailing_checkpoint_marks_prior_adverse_recovery_context():
    checkpoint = adaptive._first_favorable_checkpoint(
        _recovery_candidate(0, 0, recovers=True),
        boundary_policy={
            "target_vol_multiplier": 1.0,
            "adverse_vol_multiplier": 1.0,
        },
        cost_pct=0.2,
    )

    assert checkpoint is not None
    assert checkpoint["checkpoint_index"] == 2
    assert checkpoint["trailing_features"][-1] == 1.0
    assert len(checkpoint["trailing_features"]) == len(adaptive.TRAILING_FEATURE_NAMES)


@pytest.mark.parametrize(
    (
        "source_passed",
        "floor_passed",
        "sample_count",
        "baseline_ev",
        "selected_ev",
        "expected",
    ),
    [
        (False, True, 1, -0.2, 0.2, "source_quality_blocked"),
        (True, False, 1, -0.2, 0.2, "insufficient_coverage_dates"),
        (True, True, 0, None, None, "insufficient_recovery_evaluation"),
        (True, True, 1, -0.2, 0.1, "recovery_aware_exit_oos_positive"),
        (
            True,
            True,
            1,
            -0.2,
            -0.1,
            "recovery_aware_exit_improved_but_negative",
        ),
        (True, True, 1, -0.1, -0.2, "no_incremental_predictive_value"),
    ],
)
def test_recovery_aware_decision_boundaries(
    source_passed, floor_passed, sample_count, baseline_ev, selected_ev, expected
):
    assert (
        adaptive._recovery_aware_decision(
            {
                "sample_count": sample_count,
                "source_quality_adjusted_ev_pct": selected_ev,
            },
            {
                "sample_count": sample_count,
                "source_quality_adjusted_ev_pct": baseline_ev,
            },
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def _recovery_entry_episode(day_offset: int, index: int, *, profitable: bool):
    candidate = _recovery_candidate(
        day_offset,
        index,
        recovers=profitable,
    )
    episode = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy={
            "target_vol_multiplier": 1.0,
            "adverse_vol_multiplier": 1.0,
            "trailing_vol_multiplier": 0.0,
            "recovery_wait_minutes": 10.0,
            "recovery_deep_adverse_multiplier": 4.0,
        },
        cost_pct=0.2,
        force_recovery=True,
        force_trailing=False,
    )
    episode.update(
        {
            "recovery_entry_label_oos": True,
            "recovery_entry_label_exit_policy": "recovery_only",
            "recovery_exit_model_fit_max_date": (
                date(2026, 6, 30) + timedelta(days=day_offset)
            ).isoformat(),
        }
    )
    return episode


def test_recovery_entry_utility_model_uses_prior_oos_recovery_only_labels():
    episodes = [
        _recovery_entry_episode(day_offset, index, profitable=index % 2 == 0)
        for day_offset in range(8)
        for index in range(4)
    ]

    bundle = adaptive._fit_recovery_entry_utility_model(
        episodes,
        lane="weak_reversal",
    )

    assert bundle is not None
    _, meta = bundle
    assert meta["history_date_count"] == 8
    assert meta["history_episode_count"] == 32
    assert meta["label"] == "recovery_only_cost_adjusted_net_profit_pct"
    assert max(meta["fit_dates"]) == episodes[-1]["trade_date"]


def test_recovery_entry_utility_model_rejects_trailing_label_contamination():
    episodes = [
        _recovery_entry_episode(day_offset, index, profitable=index % 2 == 0)
        for day_offset in range(8)
        for index in range(4)
    ]
    episodes[0]["trailing_applied"] = True

    with pytest.raises(ValueError, match="recovery-only labels"):
        adaptive._fit_recovery_entry_utility_model(
            episodes,
            lane="weak_reversal",
        )


def test_recovery_entry_utility_model_rejects_non_prior_exit_model_provenance():
    episodes = [
        _recovery_entry_episode(day_offset, index, profitable=index % 2 == 0)
        for day_offset in range(8)
        for index in range(4)
    ]
    episodes[0]["recovery_exit_model_fit_max_date"] = episodes[0]["trade_date"]

    with pytest.raises(ValueError, match="prior OOS recovery-only labels"):
        adaptive._fit_recovery_entry_utility_model(
            episodes,
            lane="weak_reversal",
        )


def test_recovery_entry_utility_selection_uses_direct_predicted_ev():
    class _Model:
        def predict(self, matrix):
            return __import__("numpy").asarray([-0.01, 0.02])

    episodes = [
        _recovery_entry_episode(0, index, profitable=bool(index)) for index in range(2)
    ]

    scored = adaptive._score_recovery_entry_utility_episodes(
        episodes,
        ev_model=_Model(),
    )

    assert [row["recovery_entry_selected"] for row in scored] == [False, True]
    assert [row["predicted_recovery_entry_ev_pct"] for row in scored] == [
        -0.01,
        0.02,
    ]


def test_recovery_entry_contract_forbids_current_outcome_and_trailing_labels():
    forbidden = adaptive.RECOVERY_ENTRY_UTILITY_CONTRACT["forbidden_uses"]

    assert "current_evaluation_date_recovery_outcome_in_entry_model" in forbidden
    assert "trailing_outcome_as_recovery_entry_label" in forbidden
    assert "full_session_mfe_or_mae_as_entry_feature" in forbidden


@pytest.mark.parametrize(
    ("source_passed", "floor_passed", "count", "control_ev", "selected_ev", "expected"),
    [
        (False, True, 1, -0.2, 0.1, "source_quality_blocked"),
        (True, False, 1, -0.2, 0.1, "insufficient_coverage_dates"),
        (True, True, 0, None, None, "insufficient_recovery_entry_labels"),
        (True, True, 1, -0.2, 0.1, "recovery_entry_utility_oos_positive"),
        (
            True,
            True,
            1,
            -0.2,
            -0.1,
            "recovery_entry_utility_improved_but_negative",
        ),
        (True, True, 1, -0.1, -0.2, "no_incremental_predictive_value"),
    ],
)
def test_recovery_entry_utility_decision_boundaries(
    source_passed, floor_passed, count, control_ev, selected_ev, expected
):
    assert (
        adaptive._recovery_entry_utility_decision(
            {
                "sample_count": count,
                "source_quality_adjusted_ev_pct": selected_ev,
            },
            {
                "sample_count": count,
                "source_quality_adjusted_ev_pct": control_ev,
            },
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def _calibration_episode(day_offset: int, index: int, *, profitable: bool):
    episode = _recovery_entry_episode(day_offset, index, profitable=profitable)
    episode.update(
        {
            "predicted_recovery_entry_ev_pct": 0.2 if profitable else -0.2,
            "recovery_entry_selected": profitable,
            "recovery_entry_prediction_oos": True,
            "recovery_entry_model_fit_max_date": (
                date(2026, 6, 30) + timedelta(days=day_offset)
            ).isoformat(),
        }
    )
    return episode


def test_recovery_entry_calibrator_uses_only_prior_oos_predictions():
    episodes = [
        _calibration_episode(day_offset, index, profitable=index % 2 == 0)
        for day_offset in range(4)
        for index in range(6)
    ]

    bundle = adaptive._fit_recovery_entry_calibrator(
        episodes,
        lane="weak_reversal",
    )

    assert bundle is not None
    parameters, meta = bundle
    assert meta["history_date_count"] == 4
    assert meta["history_episode_count"] == 24
    assert max(meta["fit_dates"]) == episodes[-1]["trade_date"]
    assert meta["uncertainty_role"] == "diagnostic_only_not_selection_lower_bound"
    assert parameters["slope"] > 0.0


def test_recovery_entry_calibrator_rejects_current_date_model_provenance():
    episodes = [
        _calibration_episode(day_offset, index, profitable=index % 2 == 0)
        for day_offset in range(4)
        for index in range(6)
    ]
    episodes[0]["recovery_entry_model_fit_max_date"] = episodes[0]["trade_date"]

    with pytest.raises(ValueError, match="prior OOS recovery-only predictions"):
        adaptive._fit_recovery_entry_calibrator(
            episodes,
            lane="weak_reversal",
        )


def test_calibrated_selection_uses_mean_ev_not_uncertainty_lower_bound():
    episodes = [
        _calibration_episode(0, index, profitable=bool(index)) for index in range(2)
    ]
    episodes[0]["predicted_recovery_entry_ev_pct"] = -0.1
    episodes[1]["predicted_recovery_entry_ev_pct"] = 0.1

    scored = adaptive._score_calibrated_recovery_entry_episodes(
        episodes,
        parameters={
            "intercept": 0.01,
            "slope": 1.0,
            "prediction_mean": 0.0,
            "prediction_variance": 0.01,
            "residual_std": 1.0,
            "residual_standard_error": 1.0,
        },
    )

    assert [row["calibrated_recovery_entry_selected"] for row in scored] == [
        False,
        True,
    ]
    assert (
        scored[1]["calibrated_recovery_entry_uncertainty_pct"]
        > scored[1]["calibrated_recovery_entry_ev_pct"]
    )


def test_calibration_capacity_floor_falls_back_to_raw_arm_without_outcomes():
    candidates = []
    for index in range(4):
        row = _calibration_episode(0, index, profitable=True)
        row.update(
            {
                "calibrated_recovery_entry_ev_pct": -0.1,
                "calibrated_recovery_entry_mean_selected": False,
                "calibrated_recovery_entry_selected": False,
            }
        )
        candidates.append(row)

    selected, meta = adaptive._apply_calibration_capacity_floor(
        candidates,
        [],
        candidates,
    )

    assert meta["opportunity_floor_count"] == 3
    assert meta["capacity_fallback_applied"] is True
    assert len(selected) == 4
    assert all(row["calibration_capacity_fallback_selected"] for row in selected)
    assert all(row["calibrated_recovery_entry_selected"] for row in selected)


def test_calibration_capacity_floor_keeps_mean_arm_when_retention_is_met():
    candidates = []
    for index in range(4):
        row = _calibration_episode(0, index, profitable=True)
        row.update(
            {
                "calibrated_recovery_entry_ev_pct": 0.1,
                "calibrated_recovery_entry_mean_selected": index < 3,
                "calibrated_recovery_entry_selected": index < 3,
            }
        )
        candidates.append(row)

    selected, meta = adaptive._apply_calibration_capacity_floor(
        candidates,
        candidates[:3],
        candidates,
    )

    assert meta["opportunity_floor_count"] == 3
    assert meta["capacity_fallback_applied"] is False
    assert len(selected) == 3
    assert all(not row["calibration_capacity_fallback_selected"] for row in selected)


def test_prediction_calibration_diagnostics_are_post_oos_only():
    episodes = [
        {
            **_calibration_episode(0, index, profitable=index % 2 == 0),
            "calibrated_recovery_entry_ev_pct": float(index),
        }
        for index in range(8)
    ]

    diagnostics = adaptive._prediction_calibration_diagnostics(
        episodes,
        prediction_key="calibrated_recovery_entry_ev_pct",
    )

    assert diagnostics["role"] == "post_oos_diagnostic_only"
    assert diagnostics["forbidden_use"] == "same_report_threshold_or_lane_switch"
    assert len(diagnostics["prediction_bins"]) == 4
    assert diagnostics["sample_count"] == 8


def _decision_summary(count, ev):
    return {"sample_count": count, "source_quality_adjusted_ev_pct": ev}


def _decision_path(compounded, mae):
    return {"compounded_net_return_pct": compounded, "avg_mae_pct": mae}


@pytest.mark.parametrize(
    (
        "source_passed",
        "floor_passed",
        "evaluation_count",
        "control_ev",
        "raw_ev",
        "calibrated_ev",
        "calibrated_count",
        "calibrated_compounded",
        "calibrated_mae",
        "expected",
    ),
    [
        (
            False,
            True,
            1,
            -0.2,
            -0.1,
            0.1,
            8,
            1.0,
            -0.1,
            "source_quality_blocked",
        ),
        (
            True,
            False,
            1,
            -0.2,
            -0.1,
            0.1,
            8,
            1.0,
            -0.1,
            "insufficient_coverage_dates",
        ),
        (
            True,
            True,
            0,
            -0.2,
            -0.1,
            None,
            0,
            0.0,
            None,
            "insufficient_calibration_history",
        ),
        (
            True,
            True,
            1,
            -0.2,
            -0.1,
            0.1,
            8,
            1.0,
            -0.1,
            "calibrated_recovery_entry_oos_positive",
        ),
        (
            True,
            True,
            1,
            -0.2,
            -0.1,
            0.1,
            7,
            1.0,
            -0.1,
            "no_incremental_predictive_value",
        ),
        (
            True,
            True,
            1,
            -0.3,
            -0.2,
            -0.1,
            8,
            -1.0,
            -0.1,
            "calibrated_recovery_entry_pareto_improved",
        ),
        (
            True,
            True,
            1,
            -0.3,
            -0.2,
            -0.1,
            7,
            -1.0,
            -0.1,
            "no_incremental_predictive_value",
        ),
        (
            True,
            True,
            1,
            -0.2,
            0.1,
            0.1,
            10,
            -2.0,
            -0.2,
            "no_incremental_predictive_value",
        ),
    ],
)
def test_calibrated_recovery_entry_decision_boundaries(
    source_passed,
    floor_passed,
    evaluation_count,
    control_ev,
    raw_ev,
    calibrated_ev,
    calibrated_count,
    calibrated_compounded,
    calibrated_mae,
    expected,
):
    assert (
        adaptive._calibrated_recovery_entry_decision(
            _decision_summary(calibrated_count, calibrated_ev),
            _decision_summary(10, raw_ev),
            _decision_summary(8, control_ev),
            calibrated_path=_decision_path(
                calibrated_compounded,
                calibrated_mae,
            ),
            raw_path=_decision_path(-2.0, -0.2),
            control_path=_decision_path(-3.0, -0.3),
            evaluation_count=evaluation_count,
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def test_recovery_entry_calibration_contract_forbids_overblocking_and_leakage():
    forbidden = adaptive.RECOVERY_ENTRY_CALIBRATION_CONTRACT["forbidden_uses"]

    assert "current_evaluation_date_residual_in_same_date_calibrator" in forbidden
    assert "positive_lower_confidence_bound_only_zero_sample_gate" in forbidden
    assert "same_report_lane_outcome_as_lane_on_off_switch" in forbidden


def _timing_candidate(
    *, continuation: bool = True, day_offset: int = 0, index: int = 0
):
    candidate = _economic_candidate(day_offset, index, favorable=True)
    entry_at = datetime.fromisoformat(candidate["entry_at"])
    candidate["candidate_armed_execution_at"] = (
        entry_at - timedelta(minutes=1)
    ).isoformat()
    candidate["economic_features"] = [0.0] * len(adaptive.ECONOMIC_FEATURE_NAMES)
    points = []
    for offset, (return_1m, return_3m, return_5m, acceleration, vwap) in enumerate(
        [
            (-0.2, -0.1, 0.1, -0.1, -0.1),
            (0.2, 0.3 if continuation else -0.3, 0.2, 0.2, 0.1),
            (0.1, 0.4, 0.3, 0.2, 0.2),
        ],
        start=1,
    ):
        features = [0.0] * len(adaptive.FEATURE_NAMES)
        features[0] = return_1m
        features[1] = return_3m
        features[2] = return_5m
        features[4] = acceleration
        features[7] = vwap
        points.append(
            {
                "observed_at": (entry_at + timedelta(minutes=offset)).isoformat(),
                "execution_at": (entry_at + timedelta(minutes=offset + 1)).isoformat(),
                "reference_price": 99.9 + offset * 0.05,
                "execution_price": 99.9 + offset * 0.05,
                "point_type": "completed_close_next_open",
                "return_3m_vol_units": return_3m,
                "return_5m_vol_units": return_5m,
                "acceleration_vol_units": acceleration,
                "buy_probability": 0.6 + offset * 0.01,
                "sell_probability": 0.2,
                "volatility_scale_pct": 0.2 + offset * 0.01,
                "decision_features": features,
            }
        )
    points.append(
        {
            "observed_at": (entry_at + timedelta(minutes=5)).isoformat(),
            "execution_at": (entry_at + timedelta(minutes=5)).isoformat(),
            "reference_price": 100.5,
            "execution_price": 100.5,
            "point_type": "session_close_mark",
            "return_3m_vol_units": None,
            "return_5m_vol_units": None,
            "acceleration_vol_units": None,
            "decision_features": None,
        }
    )
    candidate["_economic_path"] = points
    return candidate


def test_recovery_entry_timing_uses_first_causal_completed_bar_and_rebases_context():
    candidate = _timing_candidate()

    timed = adaptive._derive_recovery_entry_timing_candidate(
        candidate,
        arm="confirmation_continuation",
        max_wait_minutes=5,
    )

    assert timed is not None
    assert timed["entry_timing_trigger_observed_at"].endswith("09:02:00")
    assert timed["entry_at"].endswith("09:03:00")
    feature_count = len(adaptive.FEATURE_NAMES)
    trigger = candidate["_economic_path"][1]
    assert timed["economic_features"][feature_count : feature_count * 2] == [
        round(float(value), 8) for value in trigger["decision_features"]
    ]
    assert timed["economic_features"][feature_count * 2 + 2] == pytest.approx(
        trigger["buy_probability"]
    )
    assert timed["_economic_path"][0] == candidate["_economic_path"][2]


def test_recovery_entry_timing_does_not_use_a_trigger_beyond_bounded_wait():
    candidate = _timing_candidate()

    timed = adaptive._derive_recovery_entry_timing_candidate(
        candidate,
        arm="confirmation_continuation",
        max_wait_minutes=1,
    )

    assert timed is None
    assert adaptive._missed_timing_mfe_pct(candidate) == pytest.approx(0.5)


@pytest.mark.parametrize(
    (
        "source_passed",
        "floor_passed",
        "evaluation_count",
        "control_ev",
        "timing_ev",
        "timing_count",
        "timing_compounded",
        "timing_mae",
        "expected",
    ),
    [
        (False, True, 1, -0.2, 0.1, 8, 1.0, -0.1, "source_quality_blocked"),
        (
            True,
            False,
            1,
            -0.2,
            0.1,
            8,
            1.0,
            -0.1,
            "insufficient_timing_history",
        ),
        (
            True,
            True,
            0,
            -0.2,
            None,
            0,
            0.0,
            None,
            "insufficient_timing_history",
        ),
        (
            True,
            True,
            1,
            -0.2,
            0.1,
            8,
            1.0,
            -0.1,
            "entry_timing_oos_positive",
        ),
        (
            True,
            True,
            1,
            -0.3,
            -0.2,
            8,
            -1.0,
            -0.1,
            "entry_timing_pareto_improved",
        ),
        (
            True,
            True,
            1,
            -0.2,
            -0.2,
            10,
            -2.0,
            -0.2,
            "no_incremental_predictive_value",
        ),
    ],
)
def test_recovery_entry_timing_decision_boundaries(
    source_passed,
    floor_passed,
    evaluation_count,
    control_ev,
    timing_ev,
    timing_count,
    timing_compounded,
    timing_mae,
    expected,
):
    assert (
        adaptive._recovery_entry_timing_decision(
            _decision_summary(timing_count, timing_ev),
            _decision_summary(10, control_ev),
            timing_path=_decision_path(timing_compounded, timing_mae),
            control_path=_decision_path(-2.0, -0.2),
            evaluation_count=evaluation_count,
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def test_recovery_entry_timing_contract_forbids_same_report_selection():
    forbidden = adaptive.RECOVERY_ENTRY_TIMING_CONTRACT["forbidden_uses"]

    assert "current_evaluation_date_outcome_in_timing_policy_selection" in forbidden
    assert "same_report_arm_or_wait_selection" in forbidden
    assert "fixed_profit_label_as_entry_timing_target" in forbidden


def test_recovery_entry_timing_policy_uses_control_fallback_before_capacity_gate():
    rows = []
    for day_offset in range(4):
        trade_date = date(2026, 7, 10) + timedelta(days=day_offset)
        for index in range(3):
            entry_at = datetime.combine(trade_date, datetime.min.time()).replace(
                hour=9, minute=index * 10
            )
            rows.append(
                {
                    "trade_date": trade_date.isoformat(),
                    "venue": "KRX",
                    "session": "KRX_REGULAR",
                    "entry_at": entry_at.isoformat(),
                    "exit_at": (entry_at + timedelta(minutes=5)).isoformat(),
                    "entry_price": 100.0,
                    "exit_price": 100.1,
                    "exit_reason": "session_end_censored",
                    "gross_profit_pct": 0.1,
                    "net_profit_pct": -0.1,
                    "pairability_lane": "weak_reversal",
                    "entry_timing_arm": "next_open_control",
                    "entry_timing_max_wait_minutes": 0,
                    "entry_timing_label_oos": True,
                    "entry_timing_exit_policy": "recovery_only",
                    "entry_timing_recovery_fit_max_date": (
                        trade_date - timedelta(days=1)
                    ).isoformat(),
                    "post_entry_session_mfe_pct": 0.2,
                    "post_entry_session_mae_pct": -0.2,
                    "mfe_pct": 0.2,
                    "mae_pct": -0.2,
                    "event_duration_minutes": 5.0,
                    "favorable_boundary_pct": 0.4,
                }
            )

    policy = adaptive._fit_recovery_entry_timing_policy(
        rows,
        lane="weak_reversal",
    )

    assert policy is not None
    assert policy["status"] == "prior_policy_selected"
    assert policy["opportunity_floor_count"] == 9
    assert all(row["opportunity_retention_passed"] for row in policy["grid"])
    assert all(row["capacity_fallback_date_count"] == 4 for row in policy["grid"])
    assert all(row["nonoverlap_count"] == 12 for row in policy["grid"])


def _timing_policy(*, max_wait_minutes: int = 5):
    return {
        "status": "prior_policy_selected",
        "fit_max_date": "2026-06-30",
        "selected_policy": {
            "arm": "confirmation_continuation",
            "max_wait_minutes": max_wait_minutes,
        },
    }


def _recovery_policy():
    return {
        "target_vol_multiplier": 1.0,
        "adverse_vol_multiplier": 1.0,
        "trailing_vol_multiplier": 0.0,
        "recovery_wait_minutes": 5.0,
        "recovery_deep_adverse_multiplier": 2.0,
    }


def _timing_control(candidate):
    episode = adaptive._simulate_recovery_aware_candidate(
        candidate,
        policy=_recovery_policy(),
        cost_pct=0.2,
        force_recovery=False,
    )
    episode["recovery_entry_selected"] = True
    return episode


def test_candidate_timing_baseline_features_do_not_contain_trigger_context():
    candidate = _timing_candidate()
    changed_trigger = copy.deepcopy(candidate)
    changed_trigger["_economic_path"][1]["decision_features"][0] = 99.0
    changed_trigger["_economic_path"][1]["buy_probability"] = 0.99
    policy = _timing_policy()

    assert adaptive._candidate_timing_base_features(
        candidate, policy
    ) == adaptive._candidate_timing_base_features(changed_trigger, policy)
    timed = adaptive._derive_recovery_entry_timing_candidate(
        changed_trigger,
        arm="confirmation_continuation",
        max_wait_minutes=5,
    )
    assert timed is not None
    trigger_features = adaptive._candidate_timing_trigger_features(
        changed_trigger, timed, policy
    )
    assert len(trigger_features) == len(
        adaptive.RECOVERY_ENTRY_TIMING_UTILITY_TRIGGER_FEATURE_NAMES
    )
    assert trigger_features != adaptive._candidate_timing_base_features(
        changed_trigger, policy
    )


def test_candidate_timing_missing_trigger_is_no_trade_not_retroactive_fallback():
    candidate = _timing_candidate(continuation=False)
    pair = adaptive._build_candidate_timing_utility_pair(
        candidate,
        control_episode=_timing_control(candidate),
        timing_policy=_timing_policy(max_wait_minutes=1),
        recovery_policy=_recovery_policy(),
        cost_pct=0.2,
        recovery_models=(None, None, None, 0.0),
        recovery_fit_max_date="2026-06-30",
    )

    assert pair["timing_available"] is False
    assert pair["timing_entry_at"] is None
    assert pair["timing_net_profit_pct"] == 0.0
    assert pair["timing_incremental_net_profit_pct"] == pytest.approx(
        -pair["control_net_profit_pct"]
    )


def test_candidate_timing_model_rejects_non_oos_pair_provenance():
    pairs = []
    for day_offset in range(4):
        for index in range(4):
            candidate = _timing_candidate(day_offset=day_offset, index=index * 4)
            pair = adaptive._build_candidate_timing_utility_pair(
                candidate,
                control_episode=_timing_control(candidate),
                timing_policy=_timing_policy(),
                recovery_policy=_recovery_policy(),
                cost_pct=0.2,
                recovery_models=(None, None, None, 0.0),
                recovery_fit_max_date="2026-06-30",
            )
            pairs.append(pair)
    pairs[0]["candidate_timing_policy_fit_max_date"] = pairs[0]["trade_date"]

    with pytest.raises(ValueError, match="must be prior OOS"):
        adaptive._fit_candidate_timing_utility_models(pairs, lane="weak_reversal")


def test_candidate_timing_utility_uses_causal_three_to_one_wait_budget():
    class _FixedModel:
        def __init__(self, value):
            self.value = value

        def predict(self, matrix):
            return __import__("numpy").asarray([self.value for _ in matrix])

    candidates = [_timing_candidate(index=index * 4) for index in range(4)]
    controls = [_timing_control(candidate) for candidate in candidates]

    selected, decisions, capacity = adaptive._evaluate_candidate_timing_utility(
        candidates,
        controls,
        timing_policy=_timing_policy(),
        recovery_policy=_recovery_policy(),
        cost_pct=0.2,
        recovery_models=(None, None, None, 0.0),
        baseline_model=_FixedModel(0.1),
        trigger_model=_FixedModel(0.1),
        model_fit_max_date="2026-06-30",
    )

    assert [row["baseline_action"] for row in decisions] == [
        "enter_now",
        "enter_now",
        "enter_now",
        "wait",
    ]
    assert decisions[-1]["trigger_action"] == "timed_entry"
    assert capacity["enter_now_decision_count"] == 3
    assert capacity["wait_decision_count"] == 1
    assert capacity["opportunity_retention_passed"] is True
    assert all(
        row["candidate_timing_utility_action"] in {"enter_now", "timed_entry"}
        for row in selected
    )


def test_candidate_timing_utility_carries_exploration_budget_across_dates():
    class _FixedModel:
        def predict(self, matrix):
            return __import__("numpy").asarray([0.1 for _ in matrix])

    candidate = _timing_candidate(day_offset=1)
    _, decisions, capacity = adaptive._evaluate_candidate_timing_utility(
        [candidate],
        [_timing_control(candidate)],
        timing_policy=_timing_policy(),
        recovery_policy=_recovery_policy(),
        cost_pct=0.2,
        recovery_models=(None, None, None, 0.0),
        baseline_model=_FixedModel(),
        trigger_model=_FixedModel(),
        model_fit_max_date="2026-06-30",
        prior_enter_now_count=3,
        prior_wait_count=0,
    )

    assert decisions[0]["baseline_action"] == "wait"
    assert decisions[0]["trigger_action"] == "timed_entry"
    assert capacity["prior_enter_now_decision_count"] == 3
    assert capacity["prior_wait_decision_count"] == 0
    assert capacity["wait_decision_count"] == 1


@pytest.mark.parametrize(
    (
        "source_passed",
        "floor_passed",
        "evaluation_count",
        "control_ev",
        "selected_ev",
        "selected_count",
        "selected_compounded",
        "selected_mae",
        "expected",
    ),
    [
        (False, True, 1, -0.2, 0.1, 8, 1.0, -0.1, "source_quality_blocked"),
        (
            True,
            False,
            1,
            -0.2,
            0.1,
            8,
            1.0,
            -0.1,
            "insufficient_timing_pair_history",
        ),
        (
            True,
            True,
            1,
            -0.2,
            0.1,
            7,
            1.0,
            -0.1,
            "no_incremental_predictive_value",
        ),
        (
            True,
            True,
            1,
            -0.2,
            0.1,
            8,
            1.0,
            -0.1,
            "candidate_timing_utility_oos_positive",
        ),
        (
            True,
            True,
            1,
            -0.3,
            -0.2,
            8,
            -1.0,
            -0.1,
            "candidate_timing_utility_pareto_improved",
        ),
    ],
)
def test_candidate_timing_utility_decision_boundaries(
    source_passed,
    floor_passed,
    evaluation_count,
    control_ev,
    selected_ev,
    selected_count,
    selected_compounded,
    selected_mae,
    expected,
):
    assert (
        adaptive._candidate_timing_utility_decision(
            _decision_summary(selected_count, selected_ev),
            _decision_summary(10, control_ev),
            selected_path=_decision_path(selected_compounded, selected_mae),
            control_path=_decision_path(-2.0, -0.2),
            evaluation_count=evaluation_count,
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def test_candidate_timing_utility_contract_forbids_leakage_and_fallback():
    forbidden = adaptive.RECOVERY_ENTRY_TIMING_UTILITY_CONTRACT["forbidden_uses"]

    assert "trigger_context_in_baseline_enter_now_or_wait_decision" in forbidden
    assert "current_evaluation_date_pair_in_same_date_utility_model" in forbidden
    assert "missing_trigger_as_retroactive_raw_next_open_fallback" in forbidden


def _trigger_prediction_row(day_offset, index, predicted, realized):
    trade_date = date(2026, 8, 1) + timedelta(days=day_offset)
    return {
        "trade_date": trade_date.isoformat(),
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "pairability_lane": "weak_reversal",
        "source_entry_at": datetime.combine(trade_date, datetime.min.time())
        .replace(hour=9, minute=index)
        .isoformat(),
        "timing_entry_at": datetime.combine(trade_date, datetime.min.time())
        .replace(hour=9, minute=index + 1)
        .isoformat(),
        "raw_predicted_trigger_net_ev_pct": predicted,
        "realized_trigger_net_profit_pct": realized,
        "trigger_prediction_residual_pct": realized - predicted,
        "trigger_prediction_model_fit_max_date": (
            trade_date - timedelta(days=1)
        ).isoformat(),
        "candidate_timing_policy_fit_max_date": (
            trade_date - timedelta(days=1)
        ).isoformat(),
        "candidate_timing_recovery_fit_max_date": (
            trade_date - timedelta(days=1)
        ).isoformat(),
        "trigger_prediction_oos": True,
        "trigger_prediction_exit_policy": "recovery_only",
    }


def test_trigger_utility_prediction_rows_require_prior_oos_model():
    class _FixedModel:
        def predict(self, matrix):
            return __import__("numpy").asarray([0.1 for _ in matrix])

    candidate = _timing_candidate()
    pair = adaptive._build_candidate_timing_utility_pair(
        candidate,
        control_episode=_timing_control(candidate),
        timing_policy=_timing_policy(),
        recovery_policy=_recovery_policy(),
        cost_pct=0.2,
        recovery_models=(None, None, None, 0.0),
        recovery_fit_max_date="2026-06-30",
    )

    rows = adaptive._build_trigger_utility_prediction_rows(
        [pair], trigger_model=_FixedModel(), model_fit_max_date="2026-06-30"
    )

    assert len(rows) == 1
    assert rows[0]["trigger_prediction_oos"] is True
    assert rows[0]["raw_predicted_trigger_net_ev_pct"] == 0.1
    with pytest.raises(ValueError, match="must predate"):
        adaptive._build_trigger_utility_prediction_rows(
            [pair], trigger_model=_FixedModel(), model_fit_max_date=pair["trade_date"]
        )


def test_trigger_utility_calibration_is_shrunk_and_prior_only():
    rows = [
        _trigger_prediction_row(0, 0, -0.4, 0.3),
        _trigger_prediction_row(0, 1, -0.2, 0.2),
        _trigger_prediction_row(0, 2, 0.1, 0.4),
    ]

    calibration = adaptive._fit_trigger_utility_calibration(rows, lane="weak_reversal")

    assert calibration is not None
    assert calibration["fit_max_date"] == "2026-08-01"
    assert calibration["history_pair_count"] == 3
    assert 0.0 < calibration["shrinkage_weight"] < 1.0
    assert 0.0 <= calibration["calibrated_rank_slope"] <= 2.0
    rows[0]["trigger_prediction_model_fit_max_date"] = rows[0]["trade_date"]
    with pytest.raises(ValueError, match="must be prior OOS"):
        adaptive._fit_trigger_utility_calibration(rows, lane="weak_reversal")


@pytest.mark.parametrize(
    "provenance_key",
    (
        "candidate_timing_policy_fit_max_date",
        "candidate_timing_recovery_fit_max_date",
    ),
)
def test_trigger_utility_calibration_rejects_nonprior_timing_provenance(
    provenance_key,
):
    rows = [
        _trigger_prediction_row(0, 0, -0.4, 0.3),
        _trigger_prediction_row(0, 1, -0.2, 0.2),
        _trigger_prediction_row(0, 2, 0.1, 0.4),
    ]
    rows[0][provenance_key] = rows[0]["trade_date"]

    with pytest.raises(ValueError, match="must be prior OOS"):
        adaptive._fit_trigger_utility_calibration(rows, lane="weak_reversal")


def test_trigger_calibration_forces_initial_negative_trigger_exploration():
    class _FixedModel:
        def __init__(self, value):
            self.value = value

        def predict(self, matrix):
            return __import__("numpy").asarray([self.value for _ in matrix])

    candidate = _timing_candidate(day_offset=1)
    calibration = {
        "fit_max_date": "2026-06-30",
        "residual_intercept_pct": 0.0,
        "bounded_recent_drift_pct": 0.0,
        "calibrated_rank_slope": 1.0,
    }

    selected, decisions, capacity = adaptive._evaluate_candidate_timing_utility(
        [candidate],
        [_timing_control(candidate)],
        timing_policy=_timing_policy(),
        recovery_policy=_recovery_policy(),
        cost_pct=0.2,
        recovery_models=(None, None, None, 0.0),
        baseline_model=_FixedModel(0.1),
        trigger_model=_FixedModel(-0.5),
        model_fit_max_date="2026-06-30",
        prior_enter_now_count=3,
        trigger_calibration=calibration,
    )

    assert len(selected) == 1
    assert decisions[0]["trigger_action"] == "timed_entry"
    assert decisions[0]["trigger_entry_reason"] == "bounded_trigger_exploration"
    assert capacity["forced_trigger_exploration_count"] == 1
    assert capacity["trigger_model_skip_count"] == 0


def test_trigger_calibration_allows_one_skip_after_three_trigger_entries():
    class _FixedModel:
        def __init__(self, value):
            self.value = value

        def predict(self, matrix):
            return __import__("numpy").asarray([self.value for _ in matrix])

    candidate = _timing_candidate(day_offset=1)
    selected, decisions, capacity = adaptive._evaluate_candidate_timing_utility(
        [candidate],
        [_timing_control(candidate)],
        timing_policy=_timing_policy(),
        recovery_policy=_recovery_policy(),
        cost_pct=0.2,
        recovery_models=(None, None, None, 0.0),
        baseline_model=_FixedModel(0.1),
        trigger_model=_FixedModel(-0.5),
        model_fit_max_date="2026-06-30",
        prior_enter_now_count=3,
        trigger_calibration={
            "fit_max_date": "2026-06-30",
            "residual_intercept_pct": 0.0,
            "bounded_recent_drift_pct": 0.0,
            "calibrated_rank_slope": 1.0,
        },
        prior_trigger_enter_count=3,
    )

    assert selected == []
    assert decisions[0]["trigger_action"] == "skip_nonpositive_predicted_net_ev"
    assert decisions[0]["trigger_skip_budget_available"] is True
    assert capacity["trigger_model_skip_count"] == 1
    assert capacity["forced_trigger_exploration_count"] == 0


def test_trigger_calibration_fit_must_predate_evaluation_date():
    class _FixedModel:
        def predict(self, matrix):
            return __import__("numpy").asarray([0.1 for _ in matrix])

    candidate = _timing_candidate(day_offset=1)

    with pytest.raises(ValueError, match="must predate evaluation date"):
        adaptive._evaluate_candidate_timing_utility(
            [candidate],
            [_timing_control(candidate)],
            timing_policy=_timing_policy(),
            recovery_policy=_recovery_policy(),
            cost_pct=0.2,
            recovery_models=(None, None, None, 0.0),
            baseline_model=_FixedModel(),
            trigger_model=_FixedModel(),
            model_fit_max_date="2026-06-30",
            trigger_calibration={
                "fit_max_date": candidate["trade_date"],
                "residual_intercept_pct": 0.0,
                "bounded_recent_drift_pct": 0.0,
                "calibrated_rank_slope": 1.0,
            },
        )


@pytest.mark.parametrize(
    (
        "source_passed",
        "floor_passed",
        "evaluation_count",
        "control_ev",
        "raw_ev",
        "calibrated_ev",
        "calibrated_count",
        "calibrated_compounded",
        "calibrated_mae",
        "expected",
    ),
    [
        (False, True, 1, -0.2, -0.3, 0.1, 8, 1.0, -0.1, "source_quality_blocked"),
        (
            True,
            True,
            0,
            -0.2,
            -0.3,
            None,
            0,
            0.0,
            None,
            "insufficient_trigger_history",
        ),
        (
            True,
            True,
            1,
            -0.2,
            -0.3,
            0.1,
            8,
            1.0,
            -0.1,
            "calibrated_trigger_utility_oos_positive",
        ),
        (
            True,
            True,
            1,
            -0.3,
            -0.4,
            -0.2,
            8,
            -1.0,
            -0.1,
            "calibrated_trigger_utility_pareto_improved",
        ),
        (
            True,
            True,
            1,
            -0.2,
            -0.3,
            -0.1,
            7,
            -1.0,
            -0.1,
            "no_incremental_predictive_value",
        ),
    ],
)
def test_trigger_utility_calibration_decision_boundaries(
    source_passed,
    floor_passed,
    evaluation_count,
    control_ev,
    raw_ev,
    calibrated_ev,
    calibrated_count,
    calibrated_compounded,
    calibrated_mae,
    expected,
):
    assert (
        adaptive._trigger_utility_calibration_decision(
            _decision_summary(calibrated_count, calibrated_ev),
            _decision_summary(10, raw_ev),
            _decision_summary(10, control_ev),
            calibrated_path=_decision_path(calibrated_compounded, calibrated_mae),
            raw_gate_path=_decision_path(-2.0, -0.2),
            control_path=_decision_path(-2.0, -0.2),
            evaluation_count=evaluation_count,
            sample_floor_passed=floor_passed,
            source_quality_passed=source_passed,
        )
        == expected
    )


def test_trigger_utility_calibration_contract_forbids_same_date_feedback():
    forbidden = adaptive.TRIGGER_UTILITY_CALIBRATION_CONTRACT["forbidden_uses"]

    assert "current_date_trigger_outcome_in_same_date_calibration" in forbidden
    assert "missing_trigger_as_retroactive_raw_next_open_fallback" in forbidden
    assert "different_baseline_wait_or_exit_owner_between_comparison_arms" in forbidden


def test_wait_budget_ratio_changes_only_baseline_wait_capacity():
    class _FixedModel:
        def __init__(self, value):
            self.value = value

        def predict(self, matrix):
            return __import__("numpy").asarray([self.value for _ in matrix])

    candidate = _timing_candidate(day_offset=1)
    common = {
        "timing_policy": _timing_policy(),
        "recovery_policy": _recovery_policy(),
        "cost_pct": 0.2,
        "recovery_models": (None, None, None, 0.0),
        "baseline_model": _FixedModel(0.1),
        "trigger_model": _FixedModel(0.1),
        "model_fit_max_date": "2026-06-30",
        "prior_enter_now_count": 1,
        "trigger_calibration": {
            "fit_max_date": "2026-06-30",
            "residual_intercept_pct": 0.0,
            "bounded_recent_drift_pct": 0.0,
            "calibrated_rank_slope": 1.0,
        },
    }

    _, one_to_one, one_capacity = adaptive._evaluate_candidate_timing_utility(
        [candidate],
        [_timing_control(candidate)],
        **common,
        wait_budget_enter_per_wait=1,
        wait_budget_arm="enter1_wait1",
    )
    _, two_to_one, two_capacity = adaptive._evaluate_candidate_timing_utility(
        [candidate],
        [_timing_control(candidate)],
        **common,
        wait_budget_enter_per_wait=2,
        wait_budget_arm="enter2_wait1",
    )

    assert one_to_one[0]["baseline_action"] == "wait"
    assert two_to_one[0]["baseline_action"] == "enter_now"
    assert one_capacity["wait_budget_enter_per_wait"] == 1
    assert two_capacity["wait_budget_enter_per_wait"] == 2


def test_wait_budget_arm_ratio_must_match_contract():
    class _FixedModel:
        def predict(self, matrix):
            return __import__("numpy").asarray([0.1 for _ in matrix])

    candidate = _timing_candidate(day_offset=1)

    with pytest.raises(ValueError, match="arm and ratio must match"):
        adaptive._evaluate_candidate_timing_utility(
            [candidate],
            [_timing_control(candidate)],
            timing_policy=_timing_policy(),
            recovery_policy=_recovery_policy(),
            cost_pct=0.2,
            recovery_models=(None, None, None, 0.0),
            baseline_model=_FixedModel(),
            trigger_model=_FixedModel(),
            model_fit_max_date="2026-06-30",
            wait_budget_enter_per_wait=2,
            wait_budget_arm="enter3_wait1",
        )


def _wait_budget_history_row(arm, net_profit_pct, mae_pct):
    return {
        "trade_date": "2026-08-01",
        "pairability_lane": "weak_reversal",
        "wait_budget_arm": arm,
        "wait_budget_enter_per_wait": adaptive.WAIT_BUDGET_ARMS[arm],
        "wait_budget_oos": True,
        "wait_budget_exit_policy": "recovery_only",
        "wait_budget_opportunity_retention_passed": True,
        "candidate_timing_utility_model_fit_max_date": "2026-07-31",
        "trigger_utility_calibration_fit_max_date": "2026-07-31",
        "net_profit_pct": net_profit_pct,
        "mae_pct": mae_pct,
    }


def test_wait_budget_policy_uses_only_complete_prior_arm_history():
    history = [
        _wait_budget_history_row("enter3_wait1", -0.4, -0.3),
        _wait_budget_history_row("enter2_wait1", -0.2, -0.2),
        _wait_budget_history_row("enter1_wait1", 0.1, -0.1),
    ]

    policy = adaptive._select_wait_budget_policy(history, lane="weak_reversal")

    assert policy is not None
    assert policy["selected_arm"] == "enter1_wait1"
    assert policy["fit_max_date"] == "2026-08-01"
    history[0]["candidate_timing_utility_model_fit_max_date"] = "2026-08-01"
    with pytest.raises(ValueError, match="must be prior OOS"):
        adaptive._select_wait_budget_policy(history, lane="weak_reversal")


def test_wait_budget_policy_excludes_capacity_failed_arm_without_deadlock():
    history = [
        _wait_budget_history_row("enter3_wait1", -0.4, -0.3),
        _wait_budget_history_row("enter2_wait1", -0.2, -0.2),
        _wait_budget_history_row("enter1_wait1", 0.1, -0.1),
    ]
    history[-1]["wait_budget_opportunity_retention_passed"] = False

    policy = adaptive._select_wait_budget_policy(history, lane="weak_reversal")

    assert policy is not None
    assert policy["selected_arm"] == "enter2_wait1"
    assert "enter1_wait1" not in policy["arm_diagnostics"]


def test_wait_budget_prior_decisions_preserve_pre_arm_seed_across_dates():
    baseline = [
        {"trade_date": "2026-08-07", "baseline_action": "enter_now"},
        {"trade_date": "2026-08-10", "baseline_action": "wait"},
    ]
    trigger = [
        {"trade_date": "2026-08-10", "trigger_action": "timed_entry"},
    ]
    arm = [
        {"trade_date": "2026-08-10", "baseline_action": "wait"},
    ]

    budget_prior, trigger_prior = adaptive._wait_budget_prior_decisions(
        arm,
        prior_baseline_decisions=baseline,
        prior_trigger_decisions=trigger,
    )

    assert [row["trade_date"] for row in budget_prior] == [
        "2026-08-07",
        "2026-08-10",
    ]
    assert [row["trade_date"] for row in trigger_prior] == ["2026-08-10"]
    assert trigger_prior[0] is arm[0]


@pytest.mark.parametrize(
    (
        "source_passed",
        "arm_count",
        "selected_count",
        "fixed_ev",
        "selected_ev",
        "expected",
    ),
    [
        (False, 1, 1, -0.2, 0.1, "source_quality_blocked"),
        (True, 1, 0, -0.2, None, "insufficient_wait_budget_history"),
        (True, 1, 1, -0.2, 0.1, "wait_budget_oos_positive"),
        (True, 1, 1, -0.3, -0.2, "wait_budget_pareto_improved"),
        (True, 1, 1, -0.2, -0.3, "no_incremental_predictive_value"),
    ],
)
def test_wait_budget_decision_boundaries(
    source_passed,
    arm_count,
    selected_count,
    fixed_ev,
    selected_ev,
    expected,
):
    assert (
        adaptive._wait_budget_decision(
            _decision_summary(3 if selected_ev is not None else 0, selected_ev),
            _decision_summary(3, fixed_ev),
            selected_path=_decision_path(
                1.0 if selected_ev is not None else 0.0,
                -0.1 if selected_ev is not None else None,
            ),
            fixed_path=_decision_path(-1.0, -0.2),
            arm_evaluation_count=arm_count,
            selected_policy_evaluation_count=selected_count,
            sample_floor_passed=True,
            source_quality_passed=source_passed,
        )
        == expected
    )


def test_wait_budget_contract_forbids_same_date_selection_and_owner_drift():
    forbidden = adaptive.WAIT_BUDGET_CONTRACT["forbidden_uses"]

    assert "current_date_arm_outcome_as_same_date_budget_selection" in forbidden
    assert (
        "different_trigger_calibration_or_exit_owner_between_budget_arms" in forbidden
    )


def _execution_bar(
    minute: int,
    *,
    open_: int,
    high: int,
    low: int,
    close: int,
    day: int = 10,
) -> base.Bar:
    return base.Bar(
        symbol="005930",
        venue="KRX",
        session="KRX_REGULAR",
        timestamp=datetime(2026, 8, day, 9, 0) + timedelta(minutes=minute),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=100,
        source="test",
    )


def _fixed_entry(*, day: int = 10) -> dict:
    return {
        "trade_date": f"2026-08-{day:02d}",
        "venue": "KRX",
        "session": "KRX_REGULAR",
        "entry_at": f"2026-08-{day:02d}T09:00:00",
        "entry_price": 100.0,
        "economic_first_passage_event": "adverse_first_passage",
        "pairability_lane": "weak_reversal",
    }


def test_fixed_tp_split_reprices_target_and_forbids_same_fill_bar_exit():
    bars = [
        _execution_bar(0, open_=100, high=100, low=100, close=100),
        _execution_bar(1, open_=100, high=102, low=99, close=100),
        _execution_bar(2, open_=100, high=101, low=100, close=100),
    ]

    trade = adaptive._simulate_fixed_tp_split_trade(
        _fixed_entry(),
        bars,
        arm="two_40_60_add0p5_tp0p5",
        cost_pct=0.2,
    )

    assert trade["filled_leg_count"] == 2
    assert trade["weighted_average_price"] < 100.0
    assert trade["exit_reason"] == "fixed_average_take_profit"
    assert trade["exit_at"] == "2026-08-10T09:02:00"
    assert trade["same_bar_target_after_fill_allowed"] is False


def test_fixed_tp_split_same_bar_adds_precede_catastrophic_stop():
    bars = [
        _execution_bar(0, open_=100, high=101, low=97, close=98),
    ]

    trade = adaptive._simulate_fixed_tp_split_trade(
        _fixed_entry(),
        bars,
        arm="three_20_30_50_add0p4_0p8_tp0p5",
        cost_pct=0.2,
    )

    assert trade["exit_reason"] == "catastrophic_stop"
    assert trade["filled_leg_count"] == 3
    assert trade["exit_price"] == 98.0
    assert trade["exit_at"] == "2026-08-10T09:00:00"
    assert trade["planned_budget_mae_pct"] < -1.0


def test_fixed_tp_split_policy_uses_only_complete_prior_arm_history():
    history = []
    for index, arm in enumerate(adaptive.FIXED_TP_SPLIT_ARMS):
        history.append(
            {
                **_fixed_entry(),
                "fixed_tp_split_arm": arm,
                "fixed_tp_split_oos": True,
                "net_profit_pct": float(index),
                "planned_budget_mae_pct": -0.1,
                "filled_leg_count": 1,
            }
        )

    policy = adaptive._select_fixed_tp_split_policy(history)

    assert policy is not None
    assert policy["selected_arm"] == list(adaptive.FIXED_TP_SPLIT_ARMS)[-1]
    assert policy["fit_max_date"] == "2026-08-10"
    assert "current_date_arm_outcome_as_same_date_arm_selection" in (
        adaptive.FIXED_TP_SPLIT_CONTRACT["forbidden_uses"]
    )


def test_equal_share_carry_can_complete_next_day_without_next_day_add():
    bars = [
        _execution_bar(0, open_=100, high=100, low=100, close=100),
        _execution_bar(1, open_=100, high=100, low=100, close=100),
        _execution_bar(0, open_=99, high=101, low=99, close=100, day=11),
    ]

    trade = adaptive._simulate_equal_share_carry_trade(
        _fixed_entry(),
        bars,
        arm="two_equal_add0p5_tp0p4",
        cost_pct=0.2,
    )

    assert trade["completed"] is True
    assert trade["exit_at"] == "2026-08-11T09:00:00"
    assert trade["filled_leg_count"] == 1
    assert trade["calendar_days_to_target"] == 1
    assert trade["net_return_pct"] > 0


def test_equal_share_carry_reprices_after_same_day_add_and_blocks_same_bar_target():
    bars = [
        _execution_bar(0, open_=100, high=101, low=99, close=100),
        _execution_bar(1, open_=100, high=101, low=100, close=100),
    ]

    trade = adaptive._simulate_equal_share_carry_trade(
        _fixed_entry(),
        bars,
        arm="two_equal_add0p5_tp0p4",
        cost_pct=0.2,
    )

    assert trade["filled_leg_count"] == 2
    assert trade["weighted_average_price"] == pytest.approx(99.5)
    assert trade["exit_at"] == "2026-08-10T09:01:00"
    assert trade["same_bar_target_after_fill_allowed"] is False


def test_equal_share_carry_right_censor_is_not_completed_profit():
    trade = adaptive._simulate_equal_share_carry_trade(
        _fixed_entry(),
        [_execution_bar(0, open_=100, high=100, low=98, close=98)],
        arm="two_equal_add0p5_tp0p4",
        cost_pct=0.2,
    )
    summary = adaptive._equal_share_carry_path_diagnostics([trade])

    assert trade["completed"] is False
    assert trade["net_return_pct"] is None
    assert summary["completed_trade_count"] == 0
    assert summary["right_censored_count"] == 1
    assert summary["ending_open_share_units"] == 2
    assert "right_censored_position_as_zero_return_or_completed_profit" in (
        adaptive.FIXED_TP_EQUAL_SHARE_CARRY_CONTRACT["forbidden_uses"]
    )


def test_equal_share_daily_reset_capacity_skips_overlap_and_reopens_next_date():
    bars = [
        _execution_bar(0, open_=100, high=100, low=99, close=99),
        _execution_bar(1, open_=99, high=99, low=99, close=99),
        _execution_bar(0, open_=100, high=101, low=100, close=101, day=11),
        _execution_bar(1, open_=101, high=101, low=101, close=101, day=11),
    ]
    entries = [
        _fixed_entry(),
        {**_fixed_entry(), "entry_at": "2026-08-10T09:01:00"},
        _fixed_entry(day=11),
    ]

    selected, skipped = adaptive._simulate_daily_reset_single_bundle_arm(
        entries,
        bars,
        arm="single_1_tp0p4",
        cost_pct=0.2,
    )

    assert len(selected) == 2
    assert len(skipped) == 1
    assert selected[0]["completed"] is False
    assert selected[1]["completed"] is True
    assert selected[1]["calendar_days_to_target"] == 0
    assert skipped[0]["reason"] == "single_active_bundle_capacity"


def _entry_quality_trade(
    *,
    day: int,
    minute: int,
    feature_seed: float,
    net_profit_pct: float,
    catastrophic: bool,
) -> dict:
    return {
        **_fixed_entry(day=day),
        "entry_at": f"2026-08-{day:02d}T09:{minute:02d}:00",
        "fixed_tp_split_arm": adaptive.FIXED_TP_ENTRY_QUALITY_EXECUTION_ARM,
        "fixed_tp_split_oos": True,
        "economic_features": [
            feature_seed + index * 0.001
            for index in range(len(adaptive.ECONOMIC_FEATURE_NAMES))
        ],
        "predicted_cost_adjusted_ev_pct": feature_seed,
        "predicted_event_probabilities": {
            "favorable_first_passage": 0.3,
            "adverse_first_passage": 0.6,
            "session_end_censored": 0.1,
        },
        "volatility_scale_pct": 0.5,
        "exit_at": f"2026-08-{day:02d}T09:{minute + 1:02d}:00",
        "exit_price": 98.0 if catastrophic else 100.5,
        "exit_reason": (
            "catastrophic_stop" if catastrophic else "fixed_average_take_profit"
        ),
        "gross_profit_pct": net_profit_pct + 0.2,
        "net_profit_pct": net_profit_pct,
        "planned_budget_return_pct": net_profit_pct,
        "deployed_notional_return_pct": net_profit_pct,
        "planned_budget_mae_pct": -2.0 if catastrophic else -0.1,
        "planned_budget_mfe_pct": 0.1 if catastrophic else 0.5,
        "deployed_fraction": 1.0,
        "filled_leg_count": 2,
        "average_price_improvement_vs_initial_pct": 0.4,
        "exit_below_initial_entry": catastrophic,
    }


def test_fixed_tp_entry_quality_uses_prior_failures_and_retains_current_floor():
    prior = [
        _entry_quality_trade(
            day=10,
            minute=0,
            feature_seed=-1.0,
            net_profit_pct=-2.2,
            catastrophic=True,
        ),
        _entry_quality_trade(
            day=10,
            minute=2,
            feature_seed=1.0,
            net_profit_pct=-0.1,
            catastrophic=False,
        ),
    ]
    current = [
        _entry_quality_trade(
            day=11,
            minute=minute,
            feature_seed=float(minute),
            net_profit_pct=-0.1,
            catastrophic=False,
        )
        for minute in (0, 2, 4, 6)
    ]
    evaluations = [
        {
            "evaluation_date": "2026-08-10",
            "arm_trades": {
                adaptive.FIXED_TP_ENTRY_QUALITY_EXECUTION_ARM: prior,
            },
        },
        {
            "evaluation_date": "2026-08-11",
            "arm_trades": {
                adaptive.FIXED_TP_ENTRY_QUALITY_EXECUTION_ARM: current,
            },
        },
    ]
    fitted = adaptive._fit_fixed_tp_entry_quality_model(prior)
    assert fitted is not None
    fitted_model, _ = fitted
    assert fitted_model.named_steps["logisticregression"].class_weight is None

    result = adaptive._fixed_tp_split_entry_quality_walk_forward(
        evaluations,
        sample_floor_passed=True,
        source_quality_passed=True,
    )

    evaluated = result["evaluations"][1]
    assert evaluated["model"]["fit_max_date"] == "2026-08-10"
    assert evaluated["capacity"]["selected_count"] == 3
    assert evaluated["capacity"]["opportunity_floor_count"] == 3
    assert evaluated["capacity"]["current_retention"] == 0.75
    assert result["capacity_diagnostics"]["skipped_count"] == 1
    assert [row["action"] for row in evaluated["decisions"]] == [
        "enter_bounded_exploration",
        "enter_bounded_exploration",
        "enter_bounded_exploration",
        "skip_negative_expected_ev",
    ]
    assert "catastrophic_probability_as_hard_gate" in (
        adaptive.FIXED_TP_ENTRY_QUALITY_CONTRACT["forbidden_uses"]
    )


def test_recoverable_basin_uses_prior_date_and_replays_broader_candidates():
    first_candidates = [
        _entry_quality_trade(
            day=10,
            minute=minute,
            feature_seed=float(minute),
            net_profit_pct=0.1,
            catastrophic=False,
        )
        for minute in (0, 2, 4, 6)
    ]
    second_candidates = [
        _entry_quality_trade(
            day=11,
            minute=minute,
            feature_seed=float(minute),
            net_profit_pct=0.1,
            catastrophic=False,
        )
        for minute in (0, 2, 4, 6)
    ]
    series_by_key = {
        (date(2026, 8, day), "KRX", "KRX_REGULAR"): [
            _execution_bar(
                minute,
                open_=100,
                high=101,
                low=100,
                close=100,
                day=day,
            )
            for minute in range(9)
        ]
        for day in (10, 11)
    }
    candidate_evaluations = [
        {
            "evaluation_date": "2026-08-10",
            "candidate_trades": first_candidates,
        },
        {
            "evaluation_date": "2026-08-11",
            "candidate_trades": second_candidates,
        },
    ]
    fixed_split_evaluations = [
        {
            "evaluation_date": "2026-08-10",
            "arm_trades": {
                adaptive.RECOVERABLE_BASIN_EXECUTION_ARM: first_candidates[:2],
            },
        },
        {
            "evaluation_date": "2026-08-11",
            "arm_trades": {
                adaptive.RECOVERABLE_BASIN_EXECUTION_ARM: second_candidates[:2],
            },
        },
    ]

    result = adaptive._recoverable_basin_walk_forward(
        candidate_evaluations,
        fixed_split_evaluations,
        series_by_key,
        venue="KRX",
        cost_pct=0.2,
        sample_floor_passed=True,
        source_quality_passed=True,
    )

    evaluated = result["evaluations"][1]
    assert evaluated["model"]["fit_max_date"] == "2026-08-10"
    assert evaluated["raw_candidate_count"] == 4
    assert evaluated["capacity"]["broader_control_count"] == 4
    assert evaluated["capacity"]["selected_count"] == 4
    assert evaluated["capacity"]["selected_vs_broader_control_retention"] == 1.0
    assert evaluated["trade_detail_storage"] == ("omitted_replayable_from_source_bars")
    assert "broader_control_trades" not in evaluated
    assert "selected_trades" not in evaluated
    assert "future_candidate_count_as_skip_budget_input" in (
        adaptive.RECOVERABLE_BASIN_CONTRACT["forbidden_uses"]
    )


def test_fixed_execution_report_payload_omits_replayable_trade_arrays():
    trade = {"entry_at": "2026-08-11T09:00:00"}
    compact_split = adaptive._compact_fixed_execution_report_payload(
        {
            "evaluations": [
                {
                    "evaluation_date": "2026-08-11",
                    "arm_trades": {"arm_a": [trade, trade]},
                    "selected_policy_trades": [trade],
                    "selected_control_trades": [trade, trade],
                }
            ]
        },
        split_execution=True,
    )["evaluations"][0]
    assert compact_split["arm_trade_counts"] == {"arm_a": 2}
    assert compact_split["selected_policy_trade_count"] == 1
    assert compact_split["selected_control_trade_count"] == 2
    assert "arm_trades" not in compact_split

    compact_quality = adaptive._compact_fixed_execution_report_payload(
        {
            "evaluations": [
                {
                    "evaluation_date": "2026-08-11",
                    "control_trades": [trade, trade],
                    "selected_trades": [trade],
                }
            ]
        },
        split_execution=False,
    )["evaluations"][0]
    assert compact_quality["control_trade_count"] == 2
    assert compact_quality["selected_trade_count"] == 1
    assert "control_trades" not in compact_quality
    assert "selected_trades" not in compact_quality


def test_parent_bucket_uses_prior_boundaries_and_prior_axis_choice():
    candidate_evaluations = []
    fixed_split_evaluations = []
    series_by_key = {}
    for day in (9, 10, 11):
        candidates = [
            _entry_quality_trade(
                day=day,
                minute=minute,
                feature_seed=float(minute),
                net_profit_pct=0.1,
                catastrophic=False,
            )
            for minute in (0, 2, 4, 6)
        ]
        candidate_evaluations.append(
            {
                "evaluation_date": f"2026-08-{day:02d}",
                "candidate_trades": candidates,
            }
        )
        fixed_split_evaluations.append(
            {
                "evaluation_date": f"2026-08-{day:02d}",
                "arm_trades": {
                    adaptive.PARENT_BUCKET_EXECUTION_ARM: candidates[:2],
                },
            }
        )
        series_by_key[(date(2026, 8, day), "KRX", "KRX_REGULAR")] = [
            _execution_bar(
                minute,
                open_=100,
                high=101,
                low=100,
                close=100,
                day=day,
            )
            for minute in range(9)
        ]

    result = adaptive._parent_bucket_walk_forward(
        candidate_evaluations,
        fixed_split_evaluations,
        series_by_key,
        venue="KRX",
        cost_pct=0.2,
        sample_floor_passed=True,
        source_quality_passed=True,
    )

    assert result["evaluation_count"] == 1
    evaluated = result["evaluations"][2]
    assert evaluated["status"] == "evaluated_prior_only_parent_axis"
    assert evaluated["prior_selected_axis"]["fit_max_date"] == "2026-08-10"
    assert evaluated["prior_selected_axis"]["selected_axis"] == "lane_parent"
    assert all(
        model["fit_max_date"] == "2026-08-10"
        for model in evaluated["axis_models"].values()
    )
    assert all(
        model["capacity"]["selected_vs_broader_control_retention"] >= 0.75
        for model in evaluated["axis_models"].values()
    )
    assert evaluated["trade_detail_storage"] == ("omitted_replayable_from_source_bars")
    assert result["conflict_diagnostics"]["selected_axis_bucket_attribution"]
    assert "multi_axis_child_combo_as_parent_bucket_authority" in (
        adaptive.PARENT_BUCKET_CONTRACT["forbidden_uses"]
    )


def test_parent_bucket_negative_ev_skip_quota_is_prefix_safe():
    scored = []
    for minute in (0, 2, 4, 6):
        trade = _entry_quality_trade(
            day=11,
            minute=minute,
            feature_seed=float(minute),
            net_profit_pct=0.1,
            catastrophic=False,
        )
        scored.append(
            {
                **trade,
                "parent_bucket_axis": "volatility_parent",
                "parent_bucket_label": "low",
                "parent_bucket_source_value": 0.1,
                "parent_bucket_prior_sample_count": 12,
                "predicted_parent_bucket_ev_pct": -0.1,
                "parent_bucket_fit_max_date": "2026-08-10",
            }
        )

    selected, decisions, capacity = adaptive._apply_parent_bucket_state_machine(scored)

    assert len(selected) == 3
    assert [row["action"] for row in decisions] == [
        "enter_bounded_exploration",
        "enter_bounded_exploration",
        "enter_bounded_exploration",
        "skip_negative_parent_ev",
    ]
    assert capacity["selected_vs_broader_control_retention"] == 0.75


def test_parent_bucket_stability_uses_fixed_oos_decisions_without_reselection():
    evaluations = []
    for day, value in ((9, 0.1), (10, 0.2), (11, -0.1)):
        evaluations.append(
            {
                "evaluation_date": f"2026-08-{day:02d}",
                "status": "evaluated_prior_only_parent_axis",
                "selected_axis_decisions": [
                    {
                        "trade_date": f"2026-08-{day:02d}",
                        "axis": "volatility_parent",
                        "bucket": "middle",
                        "action": "enter_bounded_exploration",
                        "post_oos_outcome_attribution": {
                            "planned_budget_return_pct": value,
                            "catastrophic": value < 0.0,
                        },
                    }
                ],
            }
        )
    parent_result = {
        "decision": "parent_bucket_conflict_only",
        "evaluation_count": 3,
        "evaluations": evaluations,
    }

    result = adaptive._parent_bucket_conflict_stability(
        parent_result,
        source_quality_passed=True,
    )

    focus = result["focus_summary"]
    assert result["input_decisions_unchanged"] is True
    assert result["decision"] == "parent_edge_concentrated_not_reproducible"
    assert focus["sample_count"] == 3
    assert focus["observed_date_count"] == 3
    assert focus["equal_weight_avg_profit_pct"] == pytest.approx(0.066667)
    assert focus["positive_date_ratio"] == pytest.approx(0.666667)
    assert focus["leave_one_date_all_positive"] is False
    assert focus["catastrophic_negative_magnitude_share"] == 1.0

    blocked = adaptive._parent_bucket_conflict_stability(
        parent_result,
        source_quality_passed=False,
    )
    assert blocked["decision"] == "source_quality_blocked"
    assert blocked["focus_summary"]["source_quality_adjusted_ev_pct"] is None


def test_parent_bucket_stability_distinguishes_stable_catastrophic_and_empty():
    def parent_result(values: tuple[float, ...]) -> dict[str, object]:
        return {
            "decision": "parent_bucket_conflict_only",
            "evaluation_count": len(values),
            "evaluations": [
                {
                    "evaluation_date": f"2026-08-{index + 1:02d}",
                    "status": "evaluated_prior_only_parent_axis",
                    "selected_axis_decisions": [
                        {
                            "trade_date": f"2026-08-{index + 1:02d}",
                            "axis": "volatility_parent",
                            "bucket": "middle",
                            "action": "enter_positive_parent_ev",
                            "post_oos_outcome_attribution": {
                                "planned_budget_return_pct": value,
                                "catastrophic": value <= -1.0,
                            },
                        }
                    ],
                }
                for index, value in enumerate(values)
            ],
        }

    stable = adaptive._parent_bucket_conflict_stability(
        parent_result((0.1, 0.2, 0.1, 0.2)),
        source_quality_passed=True,
    )
    catastrophic = adaptive._parent_bucket_conflict_stability(
        parent_result((-1.5, -1.6, -1.7)),
        source_quality_passed=True,
    )
    empty = adaptive._parent_bucket_conflict_stability(
        parent_result(()),
        source_quality_passed=True,
    )

    assert stable["decision"] == "stable_parent_edge_needs_next_date_confirmation"
    assert stable["focus_summary"]["leave_one_date_all_positive"] is True
    assert catastrophic["decision"] == "catastrophic_loss_cluster_identified"
    assert catastrophic["focus_summary"]["catastrophic_negative_magnitude_share"] == 1.0
    assert empty["decision"] == "no_stable_parent_edge"
    assert empty["focus_summary"] is None


def test_parent_catastrophic_episode_audit_uses_only_joined_pre_entry_context():
    feature_index = {
        name: index for index, name in enumerate(adaptive.ECONOMIC_FEATURE_NAMES)
    }
    decisions = []
    candidates = []
    series_by_key = {}
    start_date = date(2026, 6, 5)
    for index in range(24):
        trade_date = start_date + timedelta(days=index)
        entry_at = datetime.combine(trade_date, datetime.min.time()).replace(
            hour=9, minute=30
        )
        catastrophic = index < 4
        prices = [
            10_000 - minute * 5 if catastrophic else 10_000 + minute * 5
            for minute in range(31)
        ]
        bars = [
            base.Bar(
                symbol="005930",
                venue="KRX",
                session="KRX_REGULAR",
                timestamp=datetime.combine(trade_date, datetime.min.time()).replace(
                    hour=9
                )
                + timedelta(minutes=minute),
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                volume=100 + minute,
                source="test",
            )
            for minute, price in enumerate(prices)
        ]
        series_by_key[(trade_date, "KRX", "KRX_REGULAR")] = bars
        economic_features = [0.0] * len(adaptive.ECONOMIC_FEATURE_NAMES)
        economic_features[feature_index["confirmation_return_1m_vol_units"]] = (
            -2.0 if catastrophic else 1.0
        )
        economic_features[feature_index["confirmation_market_context_available"]] = 1.0
        economic_features[feature_index["causal_volatility_scale_pct"]] = 0.1
        candidate = {
            "trade_date": trade_date.isoformat(),
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "entry_at": entry_at.isoformat(),
            "entry_price": float(prices[-1]),
            "pairability_lane": (
                "weak_reversal" if catastrophic else "bullish_transition"
            ),
            "economic_features": economic_features,
        }
        candidates.append(candidate)
        decisions.append(
            {
                "trade_date": trade_date.isoformat(),
                "venue": "KRX",
                "session": "KRX_REGULAR",
                "entry_at": entry_at.isoformat(),
                "entry_price": float(prices[-1]),
                "axis": "volatility_parent",
                "bucket": "middle",
                "action": "enter_positive_parent_ev",
                "post_oos_outcome_attribution": {
                    "exit_reason": (
                        "catastrophic_stop"
                        if catastrophic
                        else "fixed_average_take_profit"
                    ),
                    "planned_budget_return_pct": -1.8 if catastrophic else 0.3,
                    "catastrophic": catastrophic,
                },
            }
        )
    parent_result = {
        "decision": "parent_bucket_conflict_only",
        "evaluations": [
            {
                "status": "evaluated_prior_only_parent_axis",
                "selected_axis_decisions": decisions,
            }
        ],
    }

    result = adaptive._parent_catastrophic_episode_audit(
        parent_result,
        [{"candidate_trades": candidates}],
        series_by_key,
        venue="KRX",
        source_quality_passed=True,
    )

    assert result["decision"] == "repeatable_pre_entry_loss_signature_identified"
    assert result["input_decisions_unchanged"] is True
    assert result["source_gap_count"] == 0
    assert result["episode_counts"] == {
        "total": 24,
        "catastrophic_stop": 4,
        "target_recovery": 20,
        "session_close_other": 0,
    }
    assert "confirmation_return_1m_vol_units" in result["numeric_signature_candidates"]
    assert (
        "confirmation_market_context_available"
        not in result["numeric_feature_summaries"]
    )
    assert result["focus_source_quality_adjusted_ev_pct"] == pytest.approx(-0.05)
    assert result["lane_summary"]["signature_candidate"] is True
    assert all(
        episode["provenance"]["future_path_used_as_feature"] is False
        for episode in result["episodes"]
    )

    blocked = adaptive._parent_catastrophic_episode_audit(
        parent_result,
        [{"candidate_trades": candidates}],
        series_by_key,
        venue="KRX",
        source_quality_passed=False,
    )
    assert blocked["decision"] == "source_quality_blocked"

    gap = adaptive._parent_catastrophic_episode_audit(
        parent_result,
        [{"candidate_trades": candidates[1:]}],
        series_by_key,
        venue="KRX",
        source_quality_passed=True,
    )
    assert gap["decision"] == "source_contract_gap"
    assert gap["source_gap_count"] == 1

    context_gap_candidates = copy.deepcopy(candidates)
    context_gap_candidates[0]["economic_features"][
        feature_index["confirmation_market_context_available"]
    ] = 0.0
    context_gap = adaptive._parent_catastrophic_episode_audit(
        parent_result,
        [{"candidate_trades": context_gap_candidates}],
        series_by_key,
        venue="KRX",
        source_quality_passed=True,
    )
    assert context_gap["decision"] == "source_contract_gap"
    assert context_gap["source_gaps"][0]["reason"] == (
        "exact_market_context_unavailable"
    )


def test_parent_catastrophic_stop_recovery_separates_control_and_continuation():
    start_date = date(2026, 7, 1)
    candidates = []
    decisions = []
    series_by_key = {}
    for index in range(4):
        trade_date = start_date + timedelta(days=index)
        entry_at = datetime.combine(trade_date, datetime.min.time()).replace(
            hour=9, minute=30
        )
        recovers = index < 3
        bars = []
        for minute in range(61):
            if minute <= 30:
                price = 10_000
                high = 10_010
                low = 9_990
            elif minute == 31:
                price = 9_820
                high = 10_010
                low = 9_790
            elif recovers:
                price = {32: 9_850, 33: 9_950}.get(minute, 10_050)
                high = price + 20
                low = price - 20
            else:
                price = max(9_750, 9_810 - (minute - 32) * 10)
                high = price + 10
                low = price - 10
            bars.append(
                base.Bar(
                    symbol="005930",
                    venue="KRX",
                    session="KRX_REGULAR",
                    timestamp=datetime.combine(trade_date, datetime.min.time()).replace(
                        hour=9
                    )
                    + timedelta(minutes=minute),
                    open=price,
                    high=high,
                    low=low,
                    close=price,
                    volume=100,
                    source="test",
                )
            )
        terminal_price = 10_050 if recovers else 9_750
        bars.append(
            base.Bar(
                symbol="005930",
                venue="KRX",
                session="KRX_REGULAR",
                timestamp=datetime.combine(trade_date, datetime.min.time()).replace(
                    hour=15, minute=30
                ),
                open=terminal_price,
                high=terminal_price + 10,
                low=terminal_price - 10,
                close=terminal_price,
                volume=100,
                source="test",
            )
        )
        candidate = {
            "trade_date": trade_date.isoformat(),
            "venue": "KRX",
            "session": "KRX_REGULAR",
            "entry_at": entry_at.isoformat(),
            "entry_price": 10_000.0,
        }
        fixed = adaptive._simulate_fixed_tp_split_trade(
            candidate,
            bars,
            arm=adaptive.PARENT_BUCKET_EXECUTION_ARM,
            cost_pct=0.2,
        )
        assert fixed["exit_reason"] == "catastrophic_stop"
        candidates.append(candidate)
        decisions.append(
            {
                **candidate,
                "axis": "volatility_parent",
                "bucket": "middle",
                "action": "enter_positive_parent_ev",
                "post_oos_outcome_attribution": {
                    "exit_reason": fixed["exit_reason"],
                    "planned_budget_return_pct": fixed["net_profit_pct"],
                    "catastrophic": True,
                },
            }
        )
        series_by_key[(trade_date, "KRX", "KRX_REGULAR")] = bars
    parent_result = {
        "decision": "parent_bucket_conflict_only",
        "evaluations": [
            {
                "status": "evaluated_prior_only_parent_axis",
                "selected_axis_decisions": decisions,
            }
        ],
    }

    result = adaptive._parent_catastrophic_stop_recovery_path(
        parent_result,
        [{"candidate_trades": candidates}],
        series_by_key,
        venue="KRX",
        cost_pct=0.2,
        source_quality_passed=True,
    )

    assert result["decision"] == "recoverable_adverse_first_dominates"
    assert result["episode_count"] == 4
    assert result["target_recovery_count"] == 3
    assert result["target_recovery_ratio"] == 0.75
    assert result["continuation_better_count"] == 3
    assert result["hard_stop_protected_count"] == 1
    assert result["recovery_by_horizon_count"]["3"] == 3
    assert (
        result["continue_target_or_terminal_mark_equal_weight_avg_profit_pct"]
        > result["hard_stop_control_equal_weight_avg_profit_pct"]
    )
    assert result["terminal_mark_limited_count"] == 0
    assert result["decision_evidence_complete"] is True
    assert all(
        episode["provenance"]["stop_bar_excluded_from_counterfactual_path"]
        and not episode["provenance"]["control_and_counterfactual_summed"]
        for episode in result["episodes"]
    )

    grace = adaptive._parent_post_stop_bounded_grace_arms(
        result,
        series_by_key,
        venue="KRX",
        source_quality_passed=True,
    )
    assert grace["decision"] == "bounded_grace_candidate_for_prospective_only"
    assert grace["input_episode_count"] == 4
    assert grace["prospective_candidate_horizons_minutes"] == [5, 10, 20]
    assert grace["same_sample_best_arm_selected"] is False
    assert grace["runtime_effect"] is False
    assert grace["allowed_runtime_apply"] is False
    assert grace["actual_order_submitted"] is False
    assert grace["broker_order_forbidden"] is True
    for minutes in (5, 10, 20):
        arm = grace["arms"][str(minutes)]
        assert arm["episode_count"] == 4
        assert arm["target_recovery_count"] == 3
        assert arm["improves_both_control_ev_and_compounded_return"] is True
        assert arm["prospective_candidate_only"] is True
        assert arm["average_additional_mae_from_stop_pct_conservative"] <= 0.0
        assert arm["worst_additional_mae_from_stop_pct_conservative"] <= 0.0
        assert all(
            row["provenance"]["stop_bar_excluded"]
            and row["provenance"]["existing_target_unchanged"]
            and row["provenance"]["filled_quantity_unchanged"]
            and not row["provenance"]["same_sample_best_arm_selected"]
            and not row["provenance"]["runtime_effect"]
            for row in arm["episodes"]
        )

    missing_horizon_series = {key: list(value) for key, value in series_by_key.items()}
    non_recovery_date = start_date + timedelta(days=3)
    first_key = (non_recovery_date, "KRX", "KRX_REGULAR")
    missing_at = datetime.combine(non_recovery_date, datetime.min.time()).replace(
        hour=9, minute=36
    )
    missing_horizon_series[first_key] = [
        bar for bar in missing_horizon_series[first_key] if bar.timestamp != missing_at
    ]
    grace_gap = adaptive._parent_post_stop_bounded_grace_arms(
        result,
        missing_horizon_series,
        venue="KRX",
        source_quality_passed=True,
    )
    assert grace_gap["decision"] == "source_contract_gap"
    assert grace_gap["source_gap_count"] == 1
    assert grace_gap["source_gaps"][0]["reason"] == (
        "exact_horizon_completed_bar_missing"
    )
    assert all(
        arm["source_quality_adjusted_ev_pct"] is None
        for arm in grace_gap["arms"].values()
    )

    grace_blocked = adaptive._parent_post_stop_bounded_grace_arms(
        result,
        series_by_key,
        venue="KRX",
        source_quality_passed=False,
    )
    assert grace_blocked["decision"] == "source_quality_blocked"
    assert grace_blocked["venue"] == "KRX"

    empty_blocked = adaptive._parent_post_stop_bounded_grace_arms(
        {
            "decision": "source_quality_blocked",
            "episodes": [],
            "hard_stop_control_source_quality_adjusted_ev_pct": None,
            "hard_stop_control_compounded_return_pct": 0.0,
        },
        {},
        venue="NXT",
        source_quality_passed=False,
    )
    assert empty_blocked["decision"] == "source_quality_blocked"
    assert empty_blocked["hard_stop_control_compounded_return_pct"] is None
    assert all(
        arm["compounded_return_pct"] is None for arm in empty_blocked["arms"].values()
    )

    prospective_empty = adaptive._parent_post_stop_grace_prospective_oos(
        grace,
        venue="KRX",
        source_quality_passed=True,
    )
    assert prospective_empty["decision"] == ("no_new_catastrophic_episode_observe")
    assert prospective_empty["calibration_episode_count_excluded"] == 4
    assert prospective_empty["prospective_episode_count"] == 0
    assert prospective_empty["candidate_horizons_minutes_frozen"] == [5, 10, 20]
    assert prospective_empty["same_sample_best_arm_selected"] is False
    assert prospective_empty["calibration_and_prospective_returns_mixed"] is False
    assert prospective_empty["hard_stop_control_equal_weight_avg_profit_pct"] is None
    assert all(
        arm["source_quality_adjusted_ev_pct"] is None
        and arm["compounded_return_pct"] is None
        for arm in prospective_empty["arms"].values()
    )

    future_grace = copy.deepcopy(grace)
    future_trade_date = date(2026, 8, 11)
    original_trade_date = date.fromisoformat(
        future_grace["arms"]["5"]["episodes"][0]["trade_date"]
    )
    future_delta = future_trade_date - original_trade_date
    for arm in future_grace["arms"].values():
        future_episode = copy.deepcopy(arm["episodes"][0])
        future_episode["trade_date"] = future_trade_date.isoformat()
        for field in ("entry_at", "stop_at", "exit_at"):
            future_episode[field] = (
                datetime.fromisoformat(future_episode[field]) + future_delta
            ).isoformat()
        arm["episodes"].append(future_episode)
    prospective_one = adaptive._parent_post_stop_grace_prospective_oos(
        future_grace,
        venue="KRX",
        source_quality_passed=True,
    )
    assert prospective_one["decision"] == ("prospective_grace_evidence_accumulating")
    assert prospective_one["calibration_episode_count_excluded"] == 4
    assert prospective_one["prospective_episode_count"] == 1
    assert prospective_one["source_gap_count"] == 0
    assert all(
        arm["prospective_episode_count"] == 1
        and arm["improves_both_prospective_control_ev_and_compounded_return"]
        for arm in prospective_one["arms"].values()
    )

    changed_grace = copy.deepcopy(future_grace)
    changed_episode = changed_grace["arms"]["20"]["episodes"][-1]
    changed_episode["grace_planned_budget_return_pct"] = (
        changed_episode["hard_stop_control_return_pct"] - 0.5
    )
    changed_episode["incremental_return_vs_hard_stop_pct"] = -0.5
    prospective_changed = adaptive._parent_post_stop_grace_prospective_oos(
        changed_grace,
        venue="KRX",
        source_quality_passed=True,
    )
    assert prospective_changed["decision"] == "prospective_grace_tradeoff_changed"
    assert (
        prospective_changed["arms"]["20"][
            "improves_both_prospective_control_ev_and_compounded_return"
        ]
        is False
    )

    candidate_gap = copy.deepcopy(grace)
    candidate_gap["arms"].pop("20")
    prospective_gap = adaptive._parent_post_stop_grace_prospective_oos(
        candidate_gap,
        venue="KRX",
        source_quality_passed=True,
    )
    assert prospective_gap["decision"] == "source_contract_gap"
    assert prospective_gap["source_gaps"][0]["reason"] == (
        "frozen_candidate_horizon_set_mismatch"
    )

    prospective_blocked = adaptive._parent_post_stop_grace_prospective_oos(
        empty_blocked,
        venue="NXT",
        source_quality_passed=False,
    )
    assert prospective_blocked["decision"] == "source_quality_blocked"

    limited_series_by_key = {key: bars[:-1] for key, bars in series_by_key.items()}
    limited = adaptive._parent_catastrophic_stop_recovery_path(
        parent_result,
        [{"candidate_trades": candidates}],
        limited_series_by_key,
        venue="KRX",
        cost_pct=0.2,
        source_quality_passed=True,
    )
    assert limited["decision"] == "mixed_post_stop_paths_no_owner_change"
    assert limited["terminal_mark_limited_count"] == 1
    assert limited["decision_evidence_complete"] is False
    assert (
        limited["continue_target_or_terminal_mark_source_quality_adjusted_ev_pct"]
        is None
    )

    blocked = adaptive._parent_catastrophic_stop_recovery_path(
        parent_result,
        [{"candidate_trades": candidates}],
        series_by_key,
        venue="KRX",
        cost_pct=0.2,
        source_quality_passed=False,
    )
    assert blocked["decision"] == "source_quality_blocked"

    gap = adaptive._parent_catastrophic_stop_recovery_path(
        parent_result,
        [{"candidate_trades": candidates[1:]}],
        series_by_key,
        venue="KRX",
        cost_pct=0.2,
        source_quality_passed=True,
    )
    assert gap["decision"] == "source_contract_gap"
    assert gap["source_gap_count"] == 1
