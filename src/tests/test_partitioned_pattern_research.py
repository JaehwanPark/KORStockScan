from copy import deepcopy
from datetime import datetime, timedelta
import json

import numpy as np
import pytest

from src.engine.scalping import partitioned_pattern_research as M


def row(i=0, symbol="005930", **updates):
    ts = datetime.fromisoformat("2026-09-29T10:00:00+09:00") + timedelta(minutes=i)
    r = dict(trace=str(i), day=ts.date().isoformat(), symbol=symbol, ts=ts.isoformat(),
        bundle="a" * 64, route=symbol + "_AL", types=dict(phase="pullback", family="PULLBACK", volatility_band="LOW"),
        features=dict(net_aggressive_delta_10t=10, price_change_10t_pct=.1, top3_depth_ratio=2, spread_bp=10),
        sequence=dict(delta_change=1), cost=.3, gross={str(h): 1. for h in M.HORIZONS},
        past={str(n): dict(ret=1., ret_last=.1, location=.6, efficiency=.7, reclaim=True,
            breakout=True, higher_low=True, compression_release=True) for n in (3, 5, 10, 20)},
        path_state="neither_boundary_hit", parent_action="RECHECK", identity=dict(native=None, watch_origin=None))
    r.update(updates)
    return r


def spec(**updates):
    return dict(partition="samsung", pattern="breakout", length=5, confirmation="none", scope={}, filter=None, **updates)


@pytest.mark.parametrize("value,expected", [("005930", "samsung"), ("000660", "non_samsung"),
    (5930, "unknown"), ("005930_AL", "unknown"), (None, "unknown"), ("００５９３０", "unknown")])
def test_exact_partition(value, expected):
    assert M.partition(value) == expected


def test_definition_and_signal_separate_partition_before_learning():
    with pytest.raises(ValueError, match="cross_partition"):
        M.definitions([row(), row(symbol="000660")], "samsung")
    assert not M.selected(row(symbol="000660"), spec())
    train = [row(i) for i in range(10)]
    definitions = M.definitions(train, "samsung")
    for r in train:
        r.update(gross={"10": -999}, cost=None, binary=0, path_state="fast_stop")
    assert definitions == M.definitions(train, "samsung")


def bars(count=25):
    start = datetime.fromisoformat("2026-09-29T09:35:00+09:00")
    stamps = [start + timedelta(minutes=i) for i in range(count)]
    data = [dict(timestamp=t.isoformat(), stock_code="005930", source_request_code="005930_AL",
        effective_venue="KRX", session_bucket="KRX_REGULAR", open=100. + i, high=102. + i,
        low=99. + i, close=101. + i, completed_bar_only=True, source_quality="pass_completed_ka10080_bar") for i, t in enumerate(stamps)]
    return data, stamps


def test_past_completed_bars_cutoff_future_mutation_and_json_roundtrip():
    data, stamps = bars(30)
    result = M.past_features(row(), data, stamps)
    assert result["20"]["latest_at"] == "2026-09-29T09:59:00+09:00"
    for b in data[25:]:
        b.update(close=9999, high=9999)
    assert M.past_features(row(), data, stamps) == result
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("damage", ["route", "venue", "quality", "partial", "ohlc", "duplicate", "gap"])
def test_past_bar_bad_source_is_not_a_feature(damage):
    data, stamps = bars()
    if damage == "route": data[-1]["source_request_code"] = "005930_NX"
    if damage == "venue": data[-1]["effective_venue"] = "NXT"
    if damage == "quality": data[-1]["source_quality"] = "unknown"
    if damage == "partial": data[-1]["completed_bar_only"] = False
    if damage == "ohlc": data[-1]["low"] = data[-1]["high"] + 1
    if damage == "duplicate": stamps[-2] = stamps[-1]
    if damage == "gap": stamps[-2] -= timedelta(seconds=10)
    assert not M.past_features(row(), data, stamps)


def test_repeat_no_exposure_is_not_no_pattern():
    rows = [row(0), row(2), row(4)]
    for r in rows:
        r["identity"]["native"] = ["real_admission"]
    result = M.cadence(rows)
    assert result["repeat_60_status"] == "not_evaluable_no_adjacent_exposure"
    assert result["pairs_within"]["120"] == 2


def test_first_missing_result_consumes_slot_and_ids_cannot_inflate_entries():
    rows = [row(0, gross={}), row(1), row(9), row(10)]
    for i, r in enumerate(rows):
        r["identity"]["native"] = [str(i)]
    mask = M.nonoverlap(rows, np.ones((1, 4), dtype=bool), 10)[0]
    assert mask.tolist() == [True, False, False, True]
    metric = M.metric(rows, mask, 10)
    assert metric["selected"] == 2 and metric["comparable"] == 1
    assert metric["statuses"] == dict(price_gap=1, comparable=1)


def test_same_time_tie_stable_and_cross_symbol_independent():
    rows = [row(), row(trace="other", symbol="000660"), row(trace="z")]
    assert M.nonoverlap(rows, np.ones((1, 3), dtype=bool), 10).tolist() == [[True, True, False]]


def test_cluster_weighting_missing_and_empty():
    rows = [row(i, gross={"10": 1.3}) for i in range(3)] + [row(4, symbol="000660", gross={"10": -2.7})]
    m = M.metric(rows, np.ones(4, dtype=bool), 10)
    assert m["mean"] == pytest.approx(0.)
    assert m["cluster_mean"] == pytest.approx(-1.)
    assert M.metric([], np.array([], dtype=bool), 10)["mean"] is None
    rows[0]["cost"] = None
    assert M.metric(rows, np.ones(4, dtype=bool), 10)["statuses"]["cost_gap"] == 1


def test_missing_past_flow_does_not_confirm():
    r = row(past={}, features={})
    assert not M.selected(r, spec())
    assert not M.confirms(r, "flow_price")
    assert not M.confirms(r, "flow_improving")


def test_fit_only_uses_training_and_consistent_nonoverlap():
    train = [row(i * 60) for i in range(4)]
    definitions = [spec()]
    winner, metrics, score, supported = M.fit(train, definitions, "samsung", (3, 5, 10))
    assert winner == 0 and supported.tolist() == [0]
    assert score[0] == pytest.approx(.7)
    for h in (3, 5, 10):
        assert metrics[h]["comparable"][0] == M.evaluated(train, definitions[0])[str(h)]["comparable"]


def test_native_identity_never_invented_and_projection_mismatch_fails():
    r = row()
    raw = dict(stock_code=r["symbol"], source_date=r["day"], decision_ts=r["ts"], bundle_sha256=r["bundle"],
        outcome_request_code=r["route"], effective_venue="KRX", session_bucket="KRX_REGULAR")
    assert M.bind_identity(raw, r)["native"] is None
    raw["stock_code"] = "000660"
    with pytest.raises(ValueError, match="identity_changed"):
        M.bind_identity(raw, r)


def test_null_search_seed_is_reproducible():
    rows = [row(i * 10, gross={str(h): float(i % 3) for h in M.HORIZONS}) for i in range(12)]
    specs = [spec()]
    masks = M.mask_matrix(rows, specs)
    first = M.permutation_check(rows, specs, masks, "samsung", (3, 5, 10), .1, iterations=5)
    assert first == M.permutation_check(rows, specs, masks, "samsung", (3, 5, 10), .1, iterations=5)
    assert 0 < first["adjusted_tail_fraction"] <= 1


def test_clock_and_session_censoring():
    with pytest.raises(ValueError, match="clock"):
        M.clock(row(ts="2026-09-29T10:00:00"))
    r = row(ts="2026-09-29T15:25:00+09:00")
    assert np.isnan(M.values([r], 10)[0])


def test_signal_runs_are_causal_and_do_not_create_native_support():
    rows = [row(0), row(1), row(2, past={}), row(3), row(8)]
    before = M.signal_runs(rows, spec())
    assert [r["first_trace"] for r in before["runs"]] == ["0", "3", "8"]
    for r in rows:
        r.update(gross={}, cost=None)
    after = M.signal_runs(rows, spec())
    assert before["runs"] == after["runs"]
    assert after["native_promotion_support_increment"] == 0


def test_signal_runs_reset_on_native_identity_change():
    rows = [row(0, identity=dict(native=["a"])), row(1, identity=dict(native=["b"]))]
    assert len(M.signal_runs(rows, spec())["runs"]) == 2


def test_fit_requires_each_training_day():
    rows = [row(i * 60) for i in range(4)] + [row(day="2026-09-30", ts="2026-09-30T10:00:00+09:00", past={})]
    assert M.fit(rows, [spec()], "samsung", (3, 5, 10))[0] is None


def test_single_horizon_freezes_choice_before_held_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "permutation_check", lambda *a, **k: {"status": "fixture"})
    train = [row(i * 60) for i in range(4)]
    held = [row(0, day="2026-09-30", ts="2026-09-30T10:00:00+09:00")]
    specs = [spec()]
    one = M.single_fold(train + held, "samsung", ["2026-09-29"], "2026-09-30", specs, tmp_path / "one", "samsung")
    held[0]["gross"] = {str(h): -1000 for h in M.HORIZONS}
    two = M.single_fold(train + held, "samsung", ["2026-09-29"], "2026-09-30", specs, tmp_path / "two", "samsung")
    for h in one["selections"]:
        assert one["selections"][h]["spec"] == two["selections"][h]["spec"]
        assert one["selections"][h]["train_score"] == two["selections"][h]["train_score"]


def test_disjoint_type_mixture_excludes_unknown_and_other_partition():
    rows = [row(), row(1, symbol="000660"), row(2, types={})]
    leaves = {"pullback": spec()}
    assert M.mixture_mask(rows, "phase", leaves).tolist() == [[True, False, False]]
    assert M.mixture_mask(rows, "phase", {}).sum() == 0


def test_mixture_fits_cells_without_held_inputs_and_rejects_missing_dates():
    train = [row(i * 60) for i in range(4)]
    leaves, _ = M.fit_mixture(train, "samsung", [spec()], "phase", 10)
    assert list(leaves) == ["pullback"]
    train.append(row(day="2026-09-30", ts="2026-09-30T10:00:00+09:00", types=dict(phase="different")))
    leaves, diagnostics = M.fit_mixture(train, "samsung", [spec()], "phase", 10)
    assert not leaves and diagnostics["pullback"]["status"] == "training_date_missing"


def test_repeat_respects_real_cadence_native_phase_and_past_only():
    rows = [row(0, identity=dict(native=["a"])), row(2, identity=dict(native=["a"])),
            row(4, identity=dict(native=["b"]))]
    mask, exposure = M.repeat_mask(rows, spec(), 60)
    assert not mask.any() and exposure["status"].startswith("not_evaluable")
    mask, exposure = M.repeat_mask(rows, spec(), 180)
    assert mask.tolist() == [[False, True, False]] and exposure["adjacent_native_phase_pairs"] == 1
    rows[1]["gross"] = {}
    assert M.repeat_mask(rows, spec(), 180)[0].tolist() == mask.tolist()
    rows[1]["types"]["phase"] = "different"
    assert not M.repeat_mask(rows, spec(), 180)[0].any()
