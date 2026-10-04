from copy import deepcopy

import pytest

from src.engine.scalping import samsung_policy_episode_research as P
from src.tests.test_samsung_pattern_campaign import cache, signal


def long_cache():
    return cache(6200)


def test_time_exit_includes_positive_and_negative_neither_in_win_denominator():
    c = long_cache()
    for q in c['depth'][100:]:
        q.update(bid=271200., ask=271700.)
    ctx = P.C.campaign_context(c)
    time_exit = P.exit_label(ctx, signal(c), 'time_600')
    assert time_exit['complete'] and time_exit['binary'] is None and time_exit['terminal_win'] == 1
    unchanged = P.exit_label(P.C.campaign_context(long_cache()), signal(c), 'time_600')
    m = P.terminal_metric([time_exit, unchanged])
    assert m['win_rate'] == .5 and m['binary'] == 0 and m['known_terminal'] == 2
    assert m['states'] == {'time_exit': 2}


def test_known_barrier_does_not_prove_later_trailing_path_after_gap():
    c = long_cache()
    for q in c['depth'][100:]:
        q.update(bid=272000., ask=272500.)
    c['depth'][200]['valid'] = False
    ctx = P.C.campaign_context(c)
    assert P.exit_label(ctx, signal(c), 'barrier')['complete']
    out = P.exit_label(ctx, signal(c), 'trail_04_04')
    assert not out['complete'] and out['net'] is None


@pytest.mark.parametrize('model', P.EXITS)
@pytest.mark.parametrize('defect', ('valid', 'seq', 'ep', 'continuous'))
def test_invalid_prefix_cannot_recover_at_future_profitable_quote(model, defect):
    c = long_cache()
    c['depth'][100][defect] = False if defect in ('valid', 'continuous') else 999
    for q in c['depth'][200:]:
        q.update(bid=275000., ask=275500.)
    out = P.exit_label(P.C.campaign_context(c), signal(c), model)
    assert not out['complete'] and out['net'] is None


def test_trailing_uses_first_kernel_crossing_and_preserves_absorbing_terminal():
    c = long_cache()
    for q in c['depth'][100:200]:
        q.update(bid=274000., ask=274500.)
    for q in c['depth'][200:]:
        q.update(bid=272500., ask=273000.)
    c['depth'][300]['valid'] = False
    out = P.exit_label(P.C.campaign_context(c), signal(c), 'trail_04_04')
    assert out['complete'] and out['status'] == 'trailing_exit'
    assert out['exit_t'] == c['depth'][200]['t'] and out['terminal_win'] == 1


def test_time_exit_with_last_invalid_receipt_remains_unknown():
    c = long_cache()
    c['depth'][2401]['valid'] = False
    out = P.exit_label(P.C.campaign_context(c), signal(c), 'time_600')
    assert not out['complete'] and out['terminal_win'] is None


def test_state_failure_exits_before_later_path_gap_without_changing_gross_stop():
    c = long_cache()
    for q in c['depth'][100:]:
        q.update(bid=269500., ask=270000.)
    c['depth'][200]['valid'] = False
    ctx = P.C.campaign_context(c)
    out = P.exit_label(ctx, signal(c), 'state_failure')
    assert out['complete'] and out['status'] == 'state_failure'
    assert out['net'] < 0 and out['exit_t'] == c['depth'][100]['t']
    assert not P.exit_label(ctx, signal(c), 'barrier')['complete']


def test_past_ceiling_uses_frozen_past_resistance_not_future_maximum():
    c = long_cache()
    for q in c['depth'][100:200]:
        q.update(bid=272000., ask=272500.)
    for q in c['depth'][200:]:
        q.update(bid=273000., ask=273500.)
    f = dict(signal(c), windows={'900': dict(high=273000.)})
    out = P.exit_label(P.C.campaign_context(c), f, 'past_ceiling')
    assert out['complete'] and out['exit_t'] == c['depth'][200]['t']
    assert P.exit_label(P.C.campaign_context(c), f, 'barrier')['exit_t'] == c['depth'][100]['t']


def test_missing_past_resistance_cannot_be_replaced_by_barrier_outcome():
    c = long_cache()
    for q in c['depth'][100:]:
        q.update(bid=275000., ask=275500.)
    out = P.exit_label(P.C.campaign_context(c), signal(c), 'past_ceiling')
    assert not out['complete'] and out['status'] == 'past_ceiling_input_missing' and out['net'] is None


def outcome(f, complete=True, exit_t=None):
    return dict(complete=complete, net=.1 if complete else None, binary=1 if complete else None,
                status='target_first' if complete else 'censored_before_terminal',
                entry=dict(t=f['t']), exit_t=f['t'] + 10 if exit_t is None else exit_t, horizon=1200)


def test_terminal_admission_recovers_next_cycle_and_horizon_reservation_does_not():
    signals = [dict(t=t, index=t) for t in (0, 20, 40)]
    actual = P.replay(signals, outcome)
    reserved = P.replay(signals, outcome, reservation='horizon')
    assert actual['metric']['attempts'] == 3
    assert reserved['metric']['attempts'] == 1


def test_unknown_termination_blocks_all_later_cycles():
    signals = [dict(t=t, index=t) for t in (0, 20, 4000)]
    result = P.replay(signals, lambda f: outcome(f, complete=False))
    assert result['metric']['attempts'] == 1 and result['blocked_signals'] == 2
    assert result['metric']['unknown_win_bounds'] == [0., 1.]


def native_row(i, label, *, native=None, day='2026-09-29'):
    return dict(t=i, trace=str(i), day=day, native=[i] if native is None else native,
                parent='ENTER_NOW', label=dict(binary=label))


def test_native_first_does_not_count_fixed_watch_attempts_as_independent_groups():
    rows = [native_row(i, 1, native=['fixed']) for i in range(10)]
    ids = {str(i) for i in range(10)}
    assert P.binary_metric(rows)['binary'] == 10
    assert P.binary_metric(P.native_first(rows, ids))['binary'] == 1


def test_native_choice_can_discard_an_incumbent_winner_without_retention_veto():
    rows = [native_row(i, int(i < 4)) for i in range(6)]
    definitions = [P.definitions()[0]]
    key = definitions[0]['id']
    masks = {key + ':' + mode: {'0', '1', '2'} for mode in P.MODES}
    result = P.choose_native(rows, definitions, masks, ['2026-09-29'])
    assert result['selected']['metric']['win_rate'] == 1.
    assert result['baseline']['wins'] == 4
    assert result['selected']['metric']['wins'] == 3


def test_native_choice_uses_training_dates_only():
    rows = [native_row(i, int(i < 4)) for i in range(6)]
    rows += [native_row(100 + i, 0, day='2026-10-02') for i in range(10)]
    definitions = [P.definitions()[0]]
    key = definitions[0]['id']
    masks = {key + ':' + mode: {'0', '1', '2'} | {str(100 + i) for i in range(10)} for mode in P.MODES}
    first = P.choose_native(rows, definitions, masks, ['2026-09-29'])
    for r in rows:
        if r['day'] == '2026-10-02':
            r['label']['binary'] = 1
    assert P.choose_native(rows, definitions, masks, ['2026-09-29']) == first


def frames_for(c):
    return [dict(index=i, quote_index=i, t=c['rows'][i]['t'], ep=1, bid=q['bid'], ask=q['ask'],
        buy_share=.8, sell_dominant=False, sell_count=5, hold=20., sell_decay=.3,
        windows={'300': dict(low=270000., high=273000., distance=q['bid'] - 270000.,
                             drawdown=273000. - q['bid'])})
        for i, q in enumerate(c['depth'])]


def test_state_signals_are_past_only_and_rearm_on_distinct_same_low_cycle():
    c = cache(400, step=1.)
    for i, q in enumerate(c['depth']):
        price = 270000. if i < 20 or 60 <= i < 80 else 270500. if i < 40 or 80 <= i < 100 else 272000.
        q.update(bid=price, ask=price + 500.)
    ctx = P.C.campaign_context(c)
    fs = frames_for(c)
    definition = P.definitions()[0]
    signals = P.state_signals(ctx, fs, definition)
    assert [f['index'] for f in signals] == [20, 80]
    cutoff = 55
    assert P.state_signals(ctx, fs[:cutoff], definition) == [f for f in signals if f['index'] < cutoff]
    altered = deepcopy(fs)
    for f in altered[cutoff:]:
        f['bid'] = 200000.
    assert P.state_signals(ctx, altered, definition)[0] == signals[0]


def test_state_does_not_continue_across_invalid_quote():
    c = cache(200, step=1.)
    for q in c['depth'][20:]:
        q.update(bid=270500., ask=271000.)
    c['depth'][19]['valid'] = False
    signals = P.state_signals(P.C.campaign_context(c), frames_for(c), P.definitions()[0])
    assert not any(s['index'] == 20 for s in signals)


@pytest.mark.parametrize('defect', ('stale', 'epoch', 'guard', 'future'))
def test_capture_soft_admission_requires_fresh_past_state_and_preserved_guard(defect):
    c = cache(200, step=1.)
    ctx = P.C.campaign_context(c)
    frames = frames_for(c)
    signal_ = dict(frames[5], anchor=270000.)
    row = dict(t=10.5, trace='r', parent='RECHECK', recoverable=True,
               features=dict(stream_valid=True, stream_epoch=1),
               guard=dict(cohort='soft_confirmation_only', blockers=[]))
    good, _ = P.captured_mask([row], frames, ctx, [signal_], 'soft_add')
    assert good == {'r'}
    if defect == 'stale':
        row['t'] = 100.5
    elif defect == 'epoch':
        row['features']['stream_epoch'] = 2
    elif defect == 'guard':
        row['guard']['blockers'] = ['liquidity_inputs_missing']
    else:
        signal_['t'] = 11.
    chosen, _ = P.captured_mask([row], frames, ctx, [signal_], 'soft_add')
    assert not chosen


def test_actual_prefix_context_rebuild_cannot_change_earlier_state_signals():
    c = cache(400, step=1.)
    for q in c['depth'][20:]:
        q.update(bid=270500., ask=271000.)
    definition = P.definitions()[0]
    full = P.state_signals(P.C.campaign_context(c), frames_for(c), definition)
    short = dict(rows=c['rows'][:50], depth=c['depth'][:50])
    assert P.state_signals(P.C.campaign_context(short), frames_for(short), definition) == [s for s in full if s['index'] < 50]


def test_opportunity_maximum_is_diagnostic_and_cannot_see_through_gap():
    c = long_cache()
    c['depth'][100]['valid'] = False
    for q in c['depth'][200:]:
        q.update(bid=275000., ask=275500.)
    f = signal(c)
    ctx = P.C.campaign_context(c)
    census = P.opportunity_census(ctx, [f], .23)
    assert all(v.get('observed_fee_covering_move', 0) == 0 for v in census.values())
    assert all(v['censored_horizon'] == 1 for v in census.values())


@pytest.mark.parametrize('model', ('unknown', None))
def test_unregistered_exit_rejected(model):
    with pytest.raises(ValueError):
        P.exit_label(P.C.campaign_context(cache()), signal(cache()), model)


def test_artifact_cannot_grant_runtime_or_native_support(tmp_path):
    path = tmp_path / 'report.json'
    P.write(path, dict(runtime_effect=True, native_promotion_support=True, official_policy_candidate=None))
    value = P.R.read(path)
    assert value['runtime_effect'] is False and value['native_promotion_support'] is False
    assert value['policy_publication_forbidden'] is True


def test_current_generation_uses_adopted_hash_not_same_date_staging_file(tmp_path, monkeypatch):
    generation = dict(target_date='2026-09-28', bundle_sha256='a' * 64,
                      strategy_activation=dict(effective_from='2026-09-28T07:35:00+09:00', parent_bundle_sha256='b' * 64))
    receipt = dict(schema='main_entry_current_v2', bundle_sha256='a' * 64,
                   previous_bundle_sha256='b' * 64, effective_from=generation['strategy_activation']['effective_from'])
    receipt['receipt_sha256'] = P.M.digest(receipt)
    (tmp_path / 'generations').mkdir()
    (tmp_path / 'current.json').write_text(P.C.json.dumps(receipt))
    adopted = tmp_path / 'generations' / ('a' * 64 + '.json')
    adopted.write_text(P.C.json.dumps(generation))
    (tmp_path / 'policy_2026-09-28.json').write_text(P.C.json.dumps(dict(bundle_sha256='c' * 64)))
    validated = []
    monkeypatch.setattr(P.M, 'validate', lambda value, target_date: validated.append(value))
    _, result, _, path = P.current_generation(tmp_path)
    assert result == generation and path == adopted and validated == [generation]
    receipt['effective_from'] = '2026-09-28T08:00:00+09:00'
    receipt['receipt_sha256'] = P.M.digest({k: v for k, v in receipt.items() if k != 'receipt_sha256'})
    (tmp_path / 'current.json').write_text(P.C.json.dumps(receipt))
    with pytest.raises(ValueError, match='generation_binding'):
        P.current_generation(tmp_path)


def test_oracle_movements_are_distinct_but_not_policy_entries():
    c = long_cache()
    for q in c['depth'][100:400]:
        q.update(bid=272000., ask=272500.)
    for q in c['depth'][600:]:
        q.update(bid=272000., ask=272500.)
    result = P.excursion_census(P.C.campaign_context(c), .23)
    assert result['events'] == 2
    assert result['retrospective_low_not_tradable_entry'] and not result['native_promotion_support']
    first, second = result['cycles']
    assert second['low']['t'] >= first['recovery_t'] + 60


def test_oracle_restarts_in_new_valid_segment_instead_of_bridging_invalid_quote():
    c = long_cache()
    c['depth'][100]['valid'] = False
    for q in c['depth'][200:]:
        q.update(bid=272000., ask=272500.)
    result = P.excursion_census(P.C.campaign_context(c), .23)
    assert result['events'] == 1
    assert result['cycles'][0]['low']['t'] == c['depth'][101]['t']
    assert result['cycles'][0]['recovery_t'] == c['depth'][200]['t']


def test_native_rate_change_from_known_loss_to_unknown_is_visible():
    old = native_row(1, 0, native=['fixed'])
    new = native_row(0, None, native=['fixed'])
    pair = P.paired_native([old, new], {'1'}, {'0'})
    assert pair['counts']['changed_unresolved_or_admission'] == 1
    assert pair['changes'][0]['baseline_binary'] == 0
    assert pair['changes'][0]['candidate_binary'] is None


def test_prior_domain_reader_restores_its_route_table_even_on_failure(tmp_path, monkeypatch):
    primary = tmp_path / 'primary.json'
    P.write(primary, dict(source_seals={}))
    original = P.S.SESSION_ROUTES
    def fail(*args):
        assert P.S.SESSION_ROUTES['SOR_REGULAR'] == ('SOR', '005930_AL')
        raise ValueError('source_bad')
    monkeypatch.setattr(P.S, 'partition', fail)
    with pytest.raises(ValueError, match='source_bad'):
        P.prior_day(tmp_path, tmp_path / 'output', primary)
    assert P.S.SESSION_ROUTES is original


def test_higher_low_restarts_after_equal_original_low_before_a_new_valid_retest():
    c = cache(200, step=1.)
    points = [(20, 271000.), (30, 270500.), (32, 270000.),
              (45, 271000.), (55, 270500.), (65, 271000.)]
    price = 270000.
    for i, q in enumerate(c['depth']):
        for start, value in points:
            if i == start:
                price = value
        q.update(bid=price, ask=price + 500.)
    d = next(d for d in P.definitions() if d['id'] == 'higher_low_sequence:300:5')
    result = P.state_signals(P.C.campaign_context(c), frames_for(c), d)
    assert result[0]['index'] == 65


def test_perfect_labels_cannot_overcome_one_fixed_watch_native_group():
    rows = [native_row(i, 1, native=[day], day=day) for day in P.R.DAYS for i in range(100)]
    result = P.promotion_feasibility(rows)
    assert result['train_selected_opportunity_upper_bound'] == 2
    assert result['held_selected_opportunity_upper_bound'] == 1
    assert not result['eligible_under_current_identity_contract']
