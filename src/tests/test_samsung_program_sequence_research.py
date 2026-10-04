from copy import deepcopy

from src.engine.scalping import samsung_program_sequence_research as S
from src.tests.test_samsung_environment_conditioned_research import capture, iso


def points():
    result = []
    for t, buy, sell in ((100, 100, 200), (110, 110, 230), (120, 130, 240)):
        c = capture()
        c.update(t=float(t), snapshot_t=float(t))
        c['program'].update(observed_at=iso(t-1), value=dict(buy_qty=buy, sell_qty=sell, net_qty=buy-sell))
        result.append(c)
    return result


def test_distinct_program_points_detect_sell_easing_and_positive_turn():
    rows = S.sequence_rows(points())
    assert rows[0]['sequence']['program_change'] is None
    assert rows[1]['sequence']['program_change'] == 'down'
    assert rows[2]['sequence']['sell_easing'] is True
    assert rows[2]['sequence']['turn_positive'] is True


def test_duplicate_observed_snapshot_does_not_create_third_point():
    p = points()[:2]
    extra = deepcopy(p[-1]);extra.update(t=115., snapshot_t=115.)
    extra['program']['age_ms'] = 6000.
    rows = S.sequence_rows(p + [extra])
    assert rows[-1]['sequence']['sell_easing'] is None


def test_future_point_cannot_change_past_derivative_and_capture_availability():
    p = points();full = S.sequence_rows(p);prefix = S.sequence_rows(p[:2])
    assert full[:2] == prefix
    times = [r['t'] for r in full]
    assert S.asof(full, times, 119.5, 1)['turn_positive'] is None
    assert S.asof(full, times, 120., 1)['turn_positive'] is True
    assert S.asof(full, times, 180., 1)['turn_positive'] is None


def test_epoch_change_and_counter_reset_break_sequence():
    p = points();p[-1]['ep'] = 2
    assert S.sequence_rows(p)[-1]['sequence']['program_change'] is None
    p = points();p[-1]['program']['value']['sell_qty'] = 100
    assert S.sequence_rows(p)[-1]['sequence']['program_change'] is None


def test_same_event_clock_conflicting_values_are_not_new_observation():
    p = points()[:2]
    extra = deepcopy(p[-1]);extra.update(t=115., snapshot_t=115.)
    extra['program']['age_ms'] = 6000.
    extra['program']['value']['net_qty'] = 1
    row = S.sequence_rows(p + [extra])[-1]
    assert row['sequence']['sequence_status'] == 'same_clock_conflict'
    assert row['sequence']['program_change'] is None
    repeated = deepcopy(extra);repeated.update(t=116., snapshot_t=116.)
    repeated['program']['age_ms'] = 7000.
    last = S.sequence_rows(p + [extra, repeated])[-1]
    assert last['sequence']['sequence_status'] == 'same_clock_conflict_quarantined'
    assert last['sequence']['program_change'] is None


def test_past_endpoint_interval_does_not_extend_latest_source_expiry():
    p = points()
    for i, row in enumerate(p):
        row.update(t=100. + i*90, snapshot_t=100. + i*90)
        row['program']['observed_at'] = iso(row['t']-1)
    assert S.sequence_rows(p, 60)[-1]['sequence']['program_change'] is None
    rows = S.sequence_rows(p, 180)
    assert rows[-1]['sequence']['sell_easing'] is True
    assert S.asof(rows, [r['t'] for r in rows], 280., 1)['sell_easing'] is True
    assert S.asof(rows, [r['t'] for r in rows], 340., 1)['sell_easing'] is None
