from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest

from src.engine.scalping import entry_policy_path_sequence_research as research


def row(i=0, **updates):
    r = dict(trace=str(i), day="2026-09-29", symbol="005930", bundle="a" * 64,
             ts=f"2026-09-29T09:{i:02d}:00+09:00", route="005930_AL", observed_price=100. + i,
             features=dict(net_aggressive_delta_10t=float(i), price_change_10t_pct=.1,
                           buy_pressure_10t=60., spread_bp=20., tick_pct=.1, curr_vs_micro_vwap_bp=1.),
             types=dict(phase="continuation"), native_opportunity=None,
             gross={str(h): 1. for h in research.HORIZONS}, cost=.3,
             sequence=dict(price_change_pct=1., previous_price_change_pct=-1.), path_state="late_stop",
             path={}, horizons={})
    r.update(updates)
    return r


@pytest.mark.parametrize("first,field,stem", [
    ("net_target_first", "time_to_net_target_sec", "target"),
    ("exact_stop_first", "time_to_exact_stop_sec", "stop"),
])
def test_target_stop_timing_is_symmetric_and_missing_is_not_loss(first, field, stem):
    assert research.state(dict(first_hit=first, **{field: 180}), .3) == "fast_" + stem
    assert research.state(dict(first_hit=first, **{field: 181}), .3) == "late_" + stem
    assert research.state(dict(first_hit=first), .3) == "hit_time_gap"
    assert research.state(dict(first_hit=first, **{field: 181}), None) == "cost_gap"
    assert research.state(dict(first_hit="same_bar_ambiguous"), .3) == "same_bar_ambiguous"
    assert research.state(dict(first_hit="neither_hit"), .3) == "neither_boundary_hit"


def test_sequence_uses_past_features_without_outcomes_and_preserves_unknown():
    rows = [row(0, observed_price=102.), row(1, observed_price=100.), row(2, observed_price=101.)]
    before = research.sequence_rows(rows)
    assert before[-1]["sequence"]["previous_trace"] == "1"
    assert before[-1]["sequence"]["older_trace"] == "0"
    assert research.rule(before[-1], "price_turn")
    for r in rows:
        r.update(gross={"10": -999}, path_state="same_bar_ambiguous", cost=None)
    after = research.sequence_rows(rows)
    assert [r["sequence"] for r in before] == [r["sequence"] for r in after]
    unknown = deepcopy(before[-1]); unknown["sequence"]["previous_price_change_pct"] = None
    assert not research.rule(unknown, "price_turn")


@pytest.mark.parametrize("damage", ["route", "bundle", "duplicate", "too_old", "too_close"])
def test_sequence_does_not_cross_identity_or_ambiguous_clock(damage):
    a, b = row(0), row(1)
    rows = [a, b]
    if damage == "route": a["route"] = "005930_NX"
    if damage == "bundle": a["bundle"] = "b" * 64
    if damage == "duplicate": rows.insert(1, row(0, trace="duplicate"))
    if damage == "too_old": b["ts"] = "2026-09-29T09:04:00+09:00"
    if damage == "too_close": b["ts"] = "2026-09-29T09:00:10+09:00"
    result = next(r for r in research.sequence_rows(rows) if r["trace"] == "1")
    assert result["sequence"] == {}


def test_missing_endpoint_cost_and_session_are_separate():
    rows = [row(), row(1, gross={}), row(2, cost=None), row(3, ts="2026-09-29T15:00:00+09:00")]
    result = research.metric(rows, [True] * 4, 60)
    assert result["selected"] == 4 and result["comparable"] == 1
    assert result["statuses"] == dict(comparable=1, price_gap=1, cost_gap=1, session_censored=1)
    assert result["mean"] == pytest.approx(.7)
    assert result["extra_cost_stress"]["0.1"] == pytest.approx(.6)
    assert research.horizon_status(row(ts="2026-09-29T15:20:01+09:00"), 10) == "session_censored"


def test_sampling_keeps_exact_routes_and_first_missing_outcome():
    rows = [row(0, gross={}), row(1), row(2, route="005930"), row(10)]
    assert [r["trace"] for r in research.anchors(rows, 600)] == ["0", "2", "10"]


def test_fast_training_ranking_matches_metric_with_missing_and_symbol_weighting():
    rows = [row(i, symbol=str(i % 6), gross={} if i == 0 else {str(h): i / 10 for h in research.HORIZONS}) for i in range(24)]
    definitions = research.definitions(rows, research.STATIC_RULES)
    selected, trials = research.choose(rows, definitions, (3, 5, 10))
    assert selected is not None
    for trial in trials:
        for h in (3, 5, 10):
            expected = research.metric(rows, research.selection_mask(rows, trial["definition"]), h)
            for k, value in trial["train"][str(h)].items():
                assert value == pytest.approx(expected[k]) if value is not None else expected[k] is None
    prepared = research.fit_inputs(rows, definitions, (3, 5, 10))
    fast, _ = research.choose(rows, definitions, (3, 5, 10), prepared=prepared, omit_symbol="0")
    reference, _ = research.choose([r for r in rows if r["symbol"] != "0"], definitions, (3, 5, 10))
    assert fast == reference


def test_held_labels_do_not_select_rules():
    training = [row(i, symbol=str(i % 6)) for i in range(24)]
    held = [row(30, day="2026-10-02", ts="2026-10-02T09:30:00+09:00")]
    first = research.fold(training + held, ["2026-09-29"], "2026-10-02")
    held[0]["gross"] = {str(h): 100000 for h in research.HORIZONS}
    second = research.fold(training + held, ["2026-09-29"], "2026-10-02")
    for name, value in first["objectives"].items():
        assert value["trials"] == second["objectives"][name]["trials"]


def test_aux_risk_uses_correct_units_and_unknown_keeps_pass():
    r = row(1)
    r["features"]["price_change_10t_pct"] = 0.
    assert research.aux_risk(r, "flow_without_price")
    assert research.aux_risk(r, "spread_over_tick_without_price")
    r["features"]["spread_bp"] = 10.
    assert not research.aux_risk(r, "spread_over_tick_without_price")
    r["features"] = {}
    assert not research.aux_risk(r, "flow_without_price")
    assert not research.aux_risk(r, "spread_over_tick_without_price")


def test_projection_rejects_scope_and_retained_cost_mismatch(monkeypatch):
    raw = dict(source_provenance_verified=True, machine_observation_hash_verified=True,
               effective_venue="NXT", session_bucket="KRX_REGULAR")
    with pytest.raises(ValueError, match="provenance_or_scope"):
        research.extend_row(raw, row())
    raw.update(effective_venue="KRX", source_date="2026-09-29", stock_code="005930",
               decision_ts=row()["ts"], bundle_sha256="a" * 64, setup_evidence={},
               outcome_horizon_metrics={"60m": dict(status="observed", sample_count=60, end_return_pct=2.)})
    monkeypatch.setattr(research.deep, "features", lambda _: (row()["features"], row()["types"]))
    monkeypatch.setattr(research.deep, "projection_horizons", lambda _: (row()["gross"], .5))
    with pytest.raises(ValueError, match="changed:cost"):
        research.extend_row(raw, row())
    monkeypatch.setattr(research.deep, "projection_horizons", lambda _: (row()["gross"], .3))
    extended = research.extend_row(raw, row())
    assert extended["gross"]["60"] == 2.


def bars():
    result = []
    for i, close in enumerate([103., 102., 101., 100., 101., 102.]):
        result.append(dict(timestamp=f"2026-09-29T09:{i:02d}:00+09:00", stock_code="005930",
            effective_venue="KRX", session_bucket="KRX_REGULAR", source_request_code="005930_AL",
            open=close - .5, close=close, high=close + .5, low=close - 1.,
            completed_bar_only=True, source_quality="pass_completed_ka10080_bar"))
    return result


def test_completed_bar_features_exclude_current_and_future_bars():
    sample = row(6)
    before = bars()
    values, status = research.bar_features(sample, before, [datetime.fromisoformat(b["timestamp"]) for b in before])
    assert status == "usable" and values["two_step_recovery"]
    assert values["latest_bar_at"] == "2026-09-29T09:05:00+09:00"
    future = deepcopy(before[-1]); future.update(timestamp=sample["ts"], close=99999., high=999999.)
    augmented = before + [future]
    assert research.bar_features(sample, augmented, [datetime.fromisoformat(b["timestamp"]) for b in augmented]) == (values, status)
    # At 09:05:59 the 09:05 bar cannot be consumed, even if stored after close.
    assert research.bar_features(row(ts="2026-09-29T09:05:59+09:00"), before,
        [datetime.fromisoformat(b["timestamp"]) for b in before])[1] == "fewer_than_six_past_bars"


@pytest.mark.parametrize("damage", ["route", "date", "duplicate", "gap", "ohlc", "unfinished", "quality"])
def test_completed_bar_contract_exclusions_are_explicit(damage):
    values = bars(); sample = row(6)
    if damage == "route": values[0]["source_request_code"] = "005930_NX"
    if damage == "date": values[0]["timestamp"] = "2026-09-28T09:00:00+09:00"
    if damage == "duplicate": values.insert(0, deepcopy(values[0]))
    if damage == "gap": values[0]["timestamp"] = "2026-09-29T08:59:00+09:00"
    if damage == "ohlc": values[0]["low"] = 1000.
    if damage == "unfinished": values[0]["completed_bar_only"] = False
    if damage == "quality": values[0]["source_quality"] = "unknown"
    features, status = research.bar_features(sample, values, [datetime.fromisoformat(b["timestamp"]) for b in values])
    assert features == {} and status != "usable"


def test_completed_bar_rule_reselection_uses_its_own_hypotheses():
    rows = [row(i, symbol=str(i % 6), bar_features=dict(turn=True)) for i in range(24)]
    fitted, _ = research.choose(rows, research.definitions(rows, research.BAR_RULES), (3, 5, 10))
    result = research.evaluate_selected(rows, [], fitted, (3, 5, 10), research.BAR_RULES)
    assert result["definition"]["rule"] == "bar_turn"
    assert all(x["definition"] is None or x["definition"]["rule"] in research.BAR_RULES
               for x in result["leave_selected_train_symbol_out"])


def test_unchanged_auxiliary_filter_is_not_a_candidate(monkeypatch):
    rows = [row(i, features={}, exact_pre_ai_projection_join=False) for i in range(12)]
    rows += [row(i + 20, day="2026-10-02", ts=f"2026-10-02T09:{i:02d}:00+09:00",
                 features={}, exact_pre_ai_projection_join=False) for i in range(6)]
    monkeypatch.setattr(research.deep, "auxiliary_rows", lambda _: rows)
    monkeypatch.setattr(research.C, "read", lambda _: dict(rows=[]))
    result = research.auxiliary(Path("/not_used"), [])
    assert all(fold["selected"] is None for fold in result["folds"].values())
    assert all(not t["behavior_changed"] for fold in result["folds"].values() for t in fold["trials"])


def test_outcome_subgroups_do_not_reselect_later_observations():
    rows = [row(0, path_state="late_stop"), row(1, path_state="late_target"), row(10, path_state="neither_boundary_hit")]
    result = research.retained_path_diagnostics(rows)
    assert result["all"]["10"]["comparable"] == 2
    assert result["late_target"]["10"]["comparable"] == 0
    assert result["late_stop"]["10"]["comparable"] == 1


def test_individual_horizon_can_detect_late_gain_without_forcing_early_gain():
    rows = [row(i, symbol=str(i % 6), bar_features=dict(turn=True),
                gross={"3": -.1, "5": -.1, "10": -.1, "20": -.1, "30": -.1, "60": 1.}) for i in range(24)]
    definitions = research.definitions(rows, research.BAR_RULES)
    single, _ = research.choose(rows, definitions, (60,))
    combined, _ = research.choose(rows, definitions, (20, 30, 60))
    assert single["score"] > 0 and combined["score"] < 0
