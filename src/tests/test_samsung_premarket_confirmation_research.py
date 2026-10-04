from copy import deepcopy
from pathlib import Path

import pytest

from src.engine.scalping import samsung_premarket_confirmation_research as A


def cache():
    rows = [dict(t=float(i), ep=1, seq=i + 1, continuous=True, p=100., q=2.,
                 side='BUY', valid=True, flow_valid=True) for i in range(80)]
    depth = [dict(t=i + .1, ep=1, seq=i + 1, continuous=True,
                  bid=99., ask=100., bq=20., aq=100. - i, valid=True) for i in range(80)]
    return dict(rows=rows, depth=depth)


def features():
    return dict(usable=True, delta=10., price_pct=.1, bid_5=1., bid_15=1.,
                proof=.9, refill=.2, depletion=20., downward=False)


def prepared(action='RECHECK', reason='SETUP_DISCOVERY_RECHECK', blockers=()):
    risks = [dict(risk_code='CONFIRMATION_MISSING', fact_id='no_supported_setup', disposition='RECHECKABLE')]
    risks += [dict(risk_code='STRUCTURE_INVALIDATED', fact_id=x, disposition='BLOCKING') for x in blockers]
    return dict(decision=dict(action=action, reason=reason, core_comparison=dict(risk_assessments=risks),
        liquidity_inputs_complete=True, liquidity_threshold_pass=True,
        applied_thresholds=dict(minimum_micro_price_change_10t_pct=0., minimum_micro_net_aggressive_delta_10t=1.)),
        rebuilt=dict(micro_recovery_observation=dict(source_usable=True, net_aggressive_delta_10t=10., price_change_10t_pct=.1)),
        receipt=dict(effective_thresholds=dict(micro_confirmation_recipe=0)))


def captured():
    now = '2026-10-02T08:15:00+09:00'; at = A.R.epoch(now) * 1000
    feature = dict(source_quality_status='eligible', eligible_for_feature_ablation=True,
        horizon_ms=1000, checkpoint_at_ms=at - 100, window_started_at_ms=at - 1100,
        source_gap_reasons=[], aggressive_buy_trade_backed_ratio=.9, refill_ratio=.2,
        max_best_ask_depletion_qty=20., downward_reprice_observed=False)
    return dict(decision_ts=now, setup_evidence=dict(strategy_raw_input=dict(
        quote=dict(quote_stale=False, quote_age_ms=100., evaluation_as_of=at / 1000 - .1,
                   best_ask=100., best_bid=99.),
        mechanistic_micro_window=dict(feature=feature, item='005930_NX',
            cutoff_ms=at - 100, source_quality_status='eligible',
            machine_market_route_binding=dict(market_data_route='nxt_only')))))


def test_price_sign_ablation_is_one_component_and_valid_zero_is_not_missing():
    f = features(); f['price_pct'] = 0.
    m = A.masks(f)
    assert not m['positive_micro'] and m['nonnegative_price'] and m['nonnegative_bid_hold_5']
    f['price_pct'] = None
    assert not A.masks(f)['nonnegative_price']


@pytest.mark.parametrize('field,value', [('delta', None), ('delta', -1.), ('delta', True),
    ('price_pct', float('nan')), ('bid_5', None), ('proof', None), ('depletion', 0.)])
def test_missing_bad_or_adverse_inputs_never_become_confirmation(field, value):
    f = features(); f[field] = value
    m = A.masks(f)
    if field == 'delta':
        assert not any(v for k, v in m.items() if k != 'soft_only_bound')
    elif field == 'price_pct':
        assert not m['positive_micro'] and not m['nonnegative_price']
    elif field == 'bid_5':
        assert not m['bid_hold_5'] and not m['bid_rise_5']
    else:
        assert not m['trade_backed_1']


@pytest.mark.parametrize('action', ['BLOCK', 'SOURCE_INVALID', 'ENTER_NOW'])
def test_only_original_soft_recheck_can_be_overlaid(action):
    assert not A.envelope(prepared(action))[0]


@pytest.mark.parametrize('defect', ['provenance', 'hard', 'liquidity', 'breakout', 'recipe', 'risk'])
def test_all_nonconfirmation_guards_are_retained(defect):
    p = prepared()
    if defect == 'hard': p = prepared(blockers=['large_sell_print_present'])
    if defect == 'liquidity': p['decision']['liquidity_threshold_pass'] = False
    if defect == 'breakout': p['rebuilt']['local_breakout'] = dict(recheck_required=True)
    if defect == 'recipe': p['receipt']['effective_thresholds']['micro_confirmation_recipe'] = 1
    if defect == 'risk': p['decision']['core_comparison']['risk_assessments'][0]['risk_code'] = 'ADVERSE_TAPE'
    assert not A.envelope(p, provenance=defect != 'provenance')[0]


def test_masks_do_not_consume_outcomes_or_mutate_parent():
    r, p, f = captured(), prepared(), features()
    before = deepcopy((r, p, f))
    first = A.captured_masks(r, p, f, {})
    assert (r, p, f) == before
    r['comparison'] = dict(entry_path_first_hit='adverse_first', pnl=-100.)
    assert A.captured_masks(r, p, f, {}) == first


@pytest.mark.parametrize('defect', ['future', 'old', 'route', 'window', 'gap'])
def test_captured_depletion_requires_clock_route_and_source_contract(defect):
    r = captured(); w = r['setup_evidence']['strategy_raw_input']['mechanistic_micro_window']; f = w['feature']
    if defect == 'future': f['checkpoint_at_ms'] += 200
    if defect == 'old': f['checkpoint_at_ms'] -= 3000
    if defect == 'route': w['item'] = '005930_AL'
    if defect == 'window': f['window_started_at_ms'] += 1
    if defect == 'gap': f['source_gap_reasons'] = ['gap']
    masks, _, inputs = A.captured_masks(r, prepared(), features(), {})
    assert inputs['proof'] is None and not masks['trade_backed_1']


def test_situation_veto_uses_original_parent_not_legacy_projection(monkeypatch):
    parent = dict(entry_situation_veto={'sentinel': True})
    def veto(decision, setup, policy):
        assert policy is parent
        return dict(decision, action='BLOCK')
    monkeypatch.setattr(A.D.E, '_apply_entry_situation_veto', veto)
    masks, guard, _ = A.captured_masks(captured(), prepared(), features(), parent)
    assert not any(masks.values()) and 'entry_situation_veto' in guard['blockers']


def test_actual_past_feature_does_not_see_equal_timestamp_or_future():
    c = cache(); at = 40.
    ctx = A.C.campaign_context(c); full = A.past_features(ctx, at)
    prefix = {k: [r for r in rs if r['t'] < at] for k, rs in c.items()}
    assert full == A.past_features(A.C.campaign_context(prefix), at)
    c['rows'][40]['p'] = 10000.; c['depth'][40]['bid'] = 9999.
    assert full == A.past_features(A.C.campaign_context(c), at)
    assert full['last_trade_at'] < at and full['last_quote_at'] < at


def test_trade_at_depth_anchor_same_clock_is_not_post_anchor_buy_proof():
    c = cache(); c['rows'][38].update(t=38.1, q=1000.)
    c['rows'][39]['side'] = 'SELL'
    f = A.past_features(A.C.campaign_context(c), 40.)
    assert f['depletion'] > 0 and f['proof'] == 0.


@pytest.mark.parametrize('defect', ['epoch', 'sequence', 'invalid', 'gap', 'locked'])
def test_past_quote_confirmation_does_not_skip_intervening_bad_rows(defect):
    c = cache(); q = c['depth'][37]
    if defect == 'epoch': q['ep'] = 2
    if defect == 'sequence': q['seq'] += 2
    if defect == 'invalid': q['valid'] = False
    if defect == 'gap': q['continuous'] = False
    if defect == 'locked': q['ask'] = q['bid']
    f = A.past_features(A.C.campaign_context(c), 40.)
    assert f['bid_5'] is None and not A.masks(f)['bid_hold_5']


def test_first_unknown_model_position_blocks_later_signals_and_cost_exit_shared(monkeypatch):
    fs = [dict(features(), signal=dict(t=float(i), index=i)) for i in range(3)]
    calls = []
    def label(ctx, signal, **kw):
        calls.append((signal, kw))
        return dict(complete=False, binary=None, net=None, status='censored_before_terminal')
    monkeypatch.setattr(A.C, 'label', label)
    trials = A.price_trials({}, fs)
    assert len(calls) == 3  # one label per signal, not one per hypothesis
    assert all(kw == dict(horizon=1200, target_net=.1, cost_pct=.23) for _, kw in calls)
    assert all(t['metric']['attempts'] == 1 and t['metric']['censored'] == 1 and t['blocked'] == 2 for t in trials.values())
    assert all(t['metric']['win_rate'] is None for t in trials.values())


def test_selection_is_train_only_without_winner_retention_veto():
    def trial(n, w): return dict(metric=dict(binary=n, conditional_target_first_win_rate=w))
    ts = {key: trial(3, .5) for key in A.RECIPES}
    ts['nonnegative_price'] = trial(3, .67)
    assert A.choose(ts) == 'nonnegative_price'
    ts['nonnegative_price'] = trial(2, 1.)
    assert A.choose(ts) is None


def test_capture_watch_cluster_never_selects_a_later_winner():
    rows = [dict(day='2026-09-30', trace=str(i), native=['watch'],
        masks=dict(positive_micro=True), original_diagnosis=dict(value=value),
        price_label=dict(complete=False, binary=None, net=None, status='censored'))
        for i, value in enumerate((None, 1., 1.))]
    result = A.captured_summary(rows, 'positive_micro', ['2026-09-30'])
    assert result['selected_observations'] == 3 and result['original_native_clusters'] == 1
    assert result['original_known_binary'] == 0 and result['original_unknown'] == 1
    assert result['first_selected_traces'] == ['0']


def test_changed_parent_price_threshold_cannot_silently_use_zero():
    p = prepared(); p['decision']['applied_thresholds']['minimum_micro_price_change_10t_pct'] = .2
    with pytest.raises(ValueError, match='requires_replan'):
        A.captured_masks(captured(), p, features(), {})


@pytest.mark.parametrize('defect', ['stale', 'future', 'age', 'locked', 'untrusted'])
def test_soft_bound_cannot_bypass_capture_freshness_or_trusted_flow(defect):
    r, p = captured(), prepared(); q = r['setup_evidence']['strategy_raw_input']['quote']
    if defect == 'stale': q['quote_stale'] = True
    if defect == 'future': q['evaluation_as_of'] += 1
    if defect == 'age': q['quote_age_ms'] = 2001
    if defect == 'locked': q['best_bid'] = q['best_ask']
    if defect == 'untrusted': p['rebuilt']['micro_recovery_observation']['source_usable'] = False
    assert not any(A.captured_masks(r, p, features(), {})[0].values())


def test_output_guard_rejects_live_path_and_old_generation(tmp_path):
    with pytest.raises(ValueError, match='new_workspace_tmp'):
        A.run(tmp_path, tmp_path / 'data/runtime/new')
    old = tmp_path / 'tmp/old'; old.mkdir(parents=True)
    with pytest.raises(ValueError, match='new_workspace_tmp'):
        A.run(tmp_path, old)


def test_report_enforces_no_authority_and_content_seal(tmp_path):
    path = tmp_path / 'result.json'
    A.write(path, dict(runtime_effect=True, policy_publication_forbidden=False))
    r = A.R.read(path)
    assert r['runtime_effect'] is False and r['policy_publication_forbidden'] is True
    assert r['synthetic_native_identity'] is False and r['success_preservation_veto'] is False


def canonical_pair():
    payload = dict(current={'price': 100}, quote={'best_ask': 100}, features={'delta': 10},
                   ai_market_snapshot_v1=dict(market_data_route='nxt_only'))
    row = dict(source_date='2026-10-02', stock_code='005930', effective_venue=A.SCOPE[0],
        session_bucket=A.SCOPE[1], watch_origin='MAIN_FIXED_WATCH', watch_admission_id='watch',
        watch_generation_id='generation', bundle_sha256='bundle', decision_ts='2026-10-02T08:15:00+09:00',
        source_provenance_verified=True, machine_observation_hash_verified=True,
        setup_evidence=dict(strategy_raw_input=deepcopy(payload)))
    cap = dict(captured_at=row['decision_ts'], bundle='bundle',
               top_native={k: row.get(k) for k in A.O.NATIVE_KEYS}, payload_native={})
    return row, (dict(source=dict(exact_payload=payload)), cap)


@pytest.mark.parametrize('defect', ['clock', 'bundle', 'route', 'features', 'provenance', 'native', 'scope'])
def test_canonical_join_rejects_changed_identity_scope_and_payload(defect):
    row, (raw, cap) = canonical_pair()
    if defect == 'clock': cap['captured_at'] = '2026-10-02T08:16:00+09:00'
    if defect == 'bundle': cap['bundle'] = 'other'
    if defect == 'route': raw['source']['exact_payload']['ai_market_snapshot_v1']['market_data_route'] = 'krx_nxt_integrated'
    if defect == 'features': raw['source']['exact_payload']['features']['delta'] = 99
    if defect == 'provenance': row['source_provenance_verified'] = False
    if defect == 'native': cap['top_native']['watch_admission_id'] = 'different'
    if defect == 'scope': row['effective_venue'] = 'KRX'
    with pytest.raises(ValueError, match='canonical'):
        A.verify_capture(row, (raw, cap))


def test_canonical_original_native_identity_is_kept():
    row, cap = canonical_pair()
    assert A.verify_capture(row, cap) == ['2026-10-02', '005930', *A.SCOPE,
                                         'MAIN_FIXED_WATCH', 'watch', 'generation']


def test_unused_scanner_null_string_cannot_exclude_a_fixed_watch():
    row, cap = canonical_pair(); row['scanner_promotion_id'] = 'None'
    assert A.verify_capture(row, cap)[4:] == ['MAIN_FIXED_WATCH', 'watch', 'generation']
