from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from src.engine.scalping import samsung_environment_conditioned_research as N
from src.tests.test_samsung_pattern_campaign import cache


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def capture():
    base = dict(day='2026-09-29', t=100., ep=1, stream_valid=True, snapshot_t=100.,
                market_route='krx_nxt_integrated', market_suffix='_AL')
    source = dict(value=dict(net_qty=-10., delta_qty=3.), observed_at=iso(99.), age_ms=1000.,
                  freshness_limit_ms=60000., market_route='krx_nxt_integrated',
                  market_suffix='_AL', quality='fresh')
    investor = dict(source, value=dict(foreign_net=0., inst_net=-3., smart_money_net=-3.,
                                      request_code='005930_AL', source_data_date='2026-09-29'))
    return dict(base, program=source, investor=investor)


def test_capture_availability_is_later_than_observed_clock():
    c = capture()
    assert N.flow_environment([c], [100.], 99.5, 1)['program_delta'] is None
    assert N.flow_environment([c], [100.], 100., 1)['program_delta'] == 'up'


def test_original_source_expiry_cannot_be_extended_from_capture_clock():
    c = capture()
    assert N.flow_environment([c], [100.], 159., 1)['program_delta'] == 'up'
    assert N.flow_environment([c], [100.], 159.001, 1)['program_delta'] is None


@pytest.mark.parametrize('change', [dict(quality='stale'), dict(observed_at=iso(101.)),
    dict(observed_at=None), dict(observed_at='2026-09-29T09:00:00'), dict(age_ms=0.),
    dict(freshness_limit_ms=120000), dict(freshness_limit_ms=True),
    dict(market_route='nxt_only'), dict(market_suffix='_NX')])
def test_unusable_flow_is_isolated_without_reinterpreting_as_zero(change):
    c = capture()
    c['program'].update(change)
    assert N.source_status(c['program'], c) != 'valid'
    out = N.flow_environment([c], [100.], 100., 1)
    assert out['program_net'] is None and out['foreign'] == 'flat'


@pytest.mark.parametrize('change', [dict(source_data_date='2026-09-30'), dict(request_code='005930_NX')])
def test_investor_date_and_item_are_required(change):
    c = capture()
    c['investor']['value'].update(change)
    assert N.source_status(c['investor'], c, investor=True) == 'investor_date_or_item_conflict'


@pytest.mark.parametrize('ep', [None, 2])
def test_flow_cannot_cross_stream_epoch_or_missing_epoch(ep):
    assert N.flow_environment([capture()], [100.], 100., ep)['program_delta'] is None


def test_latest_unusable_capture_does_not_fall_back_to_older_positive_flow():
    first = capture()
    second = deepcopy(first)
    second.update(t=110., snapshot_t=110.)
    second['program']['quality'] = 'stale'
    assert N.flow_environment([first, second], [100., 110.], 110., 1)['program_delta'] is None


def test_zero_and_missing_and_negative_have_different_states():
    out = N.flow_environment([capture()], [100.], 100., 1)
    assert out['foreign'] == 'flat' and out['institution'] == 'down'
    assert N.sign(None) is None and N.sign(True) is None and N.sign(float('nan')) is None


def stock_fixture():
    c = cache(4200)
    c['depth'][4000].update(bid=271000., ask=271500.)
    f = dict(t=c['rows'][4000]['t'], index=4000, quote_index=4000, ep=1,
             bid=271000., windows={'300': dict(vwap=270100., high=271000., low=270000.),
                                  '900': dict(vwap=270100., high=271000., low=270000.)})
    return c, f


def test_stock_direction_uses_only_past_bid_and_cannot_see_future_prices():
    c, f = stock_fixture()
    first = N.stock_environment(N.C.campaign_context(c), f)
    for q in c['depth'][4001:]:
        q.update(bid=300000., ask=300500.)
    second = N.stock_environment(N.C.campaign_context(c), f)
    assert first == second and first['stock_300'] == first['stock_900'] == 'up'
    assert first['past_range_900'] == 'cost_room'


@pytest.mark.parametrize('field', ['valid', 'continuous', 'seq', 'ep'])
def test_intervening_bad_quote_breaks_stock_regime(field):
    c, f = stock_fixture()
    c['depth'][3500][field] = False if field in ('valid', 'continuous') else 999
    assert N.stock_environment(N.C.campaign_context(c), f)['stock_300'] is None


def test_missing_window_is_not_neutral_stock_regime():
    c, f = stock_fixture()
    f['windows'] = {}
    e = N.stock_environment(N.C.campaign_context(c), f)
    assert e['stock_900'] is None and e['vwap_900'] is None


def test_condition_registry_is_unique_and_unknown_is_not_flat():
    registry = N.selectors()
    assert len(registry) == len({r['id'] for r in registry}) == 51
    condition = dict(conditions={'stock_900': 'up', 'program_delta': 'up'})
    assert N.matches({'stock_900': 'down', 'program_delta': None}, condition) is None
    assert N.matches({'stock_900': 'down', 'program_delta': 'up'}, condition) is False
    assert N.matches({'stock_900': 'up', 'program_delta': 'up'}, condition) is True


@pytest.mark.parametrize('mode', N.P.MODES)
def test_missing_context_preserves_parent_but_cannot_add_soft_entry(mode):
    rows = [dict(trace='old', parent='ENTER_NOW'), dict(trace='soft', parent='RECHECK')]
    condition = dict(conditions={'program_delta': 'up'})
    contexts = {r['trace']: {'program_delta': None} for r in rows}
    assert N.capture_mask(rows, {'soft'}, condition, contexts, mode) == {'old'}


def metric(wins, n, net=.1):
    return dict(attempts=n, known_terminal=n, positive=wins, binary=n, target_first=wins,
                mean_net_cf=net, censored=0)


def test_selection_uses_train_only_and_can_discard_existing_successes():
    days = {N.DAYS[0]: metric(2, 2), N.DAYS[1]: metric(1, 1), N.DAYS[2]: metric(0, 20, -.9)}
    item = dict(key='test', selector='program_delta=up', baseline='parent', days=days)
    base = {'parent': {N.DAYS[0]: metric(3, 4), N.DAYS[1]: metric(1, 2), N.DAYS[2]: metric(20, 20)}}
    first = N.select_price([item], base)
    assert first['selected']['train']['positive'] == 3
    assert first['selected']['baseline_train']['positive'] == 4
    item['days'][N.DAYS[2]] = metric(20, 20)
    assert N.select_price([item], base) == first


def test_conditional_selection_requires_support_on_both_training_days():
    item = dict(key='test', selector='up', baseline='parent', days={N.DAYS[0]: metric(3, 3), N.DAYS[1]: metric(0, 0)})
    base = {'parent': {N.DAYS[0]: metric(1, 2), N.DAYS[1]: metric(0, 0)}}
    assert N.select_price([item], base)['selected'] is None


def test_weighted_aggregate_does_not_average_daily_percentages():
    m = N.aggregate([metric(1, 1, .2), metric(0, 3, -.2)])
    assert m['win_rate'] == .25 and m['mean_net_cf'] == pytest.approx(-.1)


def test_output_forces_no_runtime_authority_and_verifies_content(tmp_path):
    path = tmp_path / 'result.json'
    N.write(path, dict(runtime_effect=True, live_selector_registered=True))
    result = N.R.read(path)
    assert result['runtime_effect'] is False and result['live_selector_registered'] is False
    assert result['policy_publication_forbidden'] and result['provider_calls'] == 0


def test_same_day_eod_breadth_cannot_be_used_before_publication():
    report = dict(published_t=100., quote_close_t=50., path='report', ma20_ratio=30.)
    assert N.published_breadth([report], 99.)['state'] is None
    assert N.published_breadth([report], 100.)['state'] == 'down'


def test_new_publication_cannot_renew_stale_quote_breadth():
    report = dict(published_t=300000., quote_close_t=1., path='report', ma20_ratio=70.)
    assert N.published_breadth([report], 300001.)['state'] is None


def test_missing_and_neutral_published_breadth_remain_distinct():
    report = dict(published_t=100., quote_close_t=50., path='report', ma20_ratio=50.)
    assert N.published_breadth([report], 100.)['state'] == 'flat'
    assert N.published_breadth([], 100.)['state'] is None


def test_parent_condition_only_filter_keeps_unknown_and_cannot_add_block():
    rows = [dict(trace=str(i), parent='ENTER_NOW' if i < 3 else 'BLOCK') for i in range(4)]
    contexts = {'0': {'program_delta': 'up'}, '1': {'program_delta': 'down'},
                '2': {'program_delta': None}, '3': {'program_delta': 'up'}}
    assert N.parent_context_mask(rows, dict(conditions={'program_delta': 'up'}), contexts) == {'0', '2'}


def test_native_ranking_can_remove_winners_without_retention_veto():
    rows = [dict(trace=str(i), native=['native', i], day=N.DAYS[i % 2],
                 t=i, parent='ENTER_NOW', label=dict(binary=1 if i < 4 else 0, net=.2 if i < 4 else -.7)) for i in range(6)]
    result = N.native_summary(rows, {'candidate': {'0', '1', '2'}})
    assert result['selected']['train']['win_rate_pct'] == 100.
    assert result['selected']['train']['winning_attempt_count'] == 3
    assert result['baseline']['train']['winning_attempt_count'] == 4
    assert result['official_policy_candidate'] is None


def test_native_ranking_does_not_use_held_labels():
    rows = [dict(trace=str(i), native=['native', i], day=N.DAYS[0], t=i,
                 parent='ENTER_NOW', label=dict(binary=1 if i < 3 else 0, net=.2 if i < 3 else -.7)) for i in range(6)]
    rows.append(dict(trace='held', native=['held'], day=N.DAYS[2], t=10, parent='ENTER_NOW', label=dict(binary=0, net=-.7)))
    masks = {'better': {'0', '1', '2', 'held'}, 'worse': {'0', '1', '2', '3'}}
    first = N.native_summary(rows, masks)['selected']['key']
    rows[-1]['label'].update(binary=1, net=.2)
    assert N.native_summary(rows, masks)['selected']['key'] == first == 'better'


def test_bad_optional_external_report_is_isolated(tmp_path):
    producer = tmp_path / 'src/engine/daily_report_service.py'
    producer.parent.mkdir(parents=True)
    producer.write_text('')
    path = tmp_path / 'data/report/report_2026-09-29.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'stats': {'ma20_ratio': 30., 'total_valid': 100, 'quote_date': 'bad'}}))
    reports, seals, excluded = N.breadth_intake(tmp_path)
    assert reports == [] and str(path) in seals and len(excluded) == 1
    assert excluded[0]['reason'] == 'invalid_optional_breadth_source'
