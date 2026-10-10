"""All-symbol census, causal classification and executable-path regressions."""
from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest

from src.engine.scalping import main_exit_scope as scope
from src.engine.scalping import trailing_situation_policy as typed
from src.engine.scalping import universal_trailing_replay as replay
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.engine.scalping.trailing_mechanical_policy import DEFAULTS, START_MARKETS, market_values_hash
from src.tests.test_scalp_trailing_mechanical_strength import _snapshot, _depth


def vector():
    return {m: dict(DEFAULTS) for m in START_MARKETS}


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=ZoneInfo('Asia/Seoul')).timestamp()


def position():
    return dict(position_key='main:1', evidence_kind='actual_completed', owner='main',
        automatic_management_allowed=True, entry_at=at('2026-10-08T09:00:00'), qty=10, buy_basis_krw=1000,
        route='KRX', item='123456', terminal_status='COMPLETED', cost_model={
            'buy_cost_krw': 0, 'sell_cost_rate': .0023, 'source_sha256': 'a' * 64},
        actual_cost_reconciliation={'status': 'actual_cost_reconciled', 'exact_pnl_krw': 4,
            'exact_profit_rate': .4, 'receipt_sha256': 'b' * 64, 'raw_sha256': 'c' * 64})


def quote(seq, clock, *, bid=100.5, peak=101, qty=10):
    stamp = at(clock)
    source = _depth(seq, int(stamp * 1000), qty, 10)
    source['bid_levels'][0]['price'] = bid
    source['ask_levels'][0]['price'] = 102
    ws = _snapshot([source], [])
    raw = dict(kind='QUOTE', event_at=stamp, known_at=stamp, source_kind='tick_depth',
        coverage_complete=True, route='KRX', item='123456', transport_epoch=1, sequence=seq,
        max_quote_age_sec=.7, bid=bid, ask=102, bid_qty=qty, trade_peak_price=peak, ws_data=ws,
        quote_snapshot_sha256=digest(ws), sell_execution_plan={
            'valid_until': stamp + .7, 'quote_source_sha256': digest(ws), 'limit_price': bid, 'quantity': 10})
    raw['source_sha256'] = digest(raw)
    return raw


def test_scope_keeps_all_symbols_and_disjoint_custody_registration_coverage():
    key = '123456|REGULAR|SOR'
    value = scope.build_scope([{'code': '123456', 'known_at': 1, 'tradable': True},
                              {'code': '654321', 'known_at': 1, 'tradable': True}],
        as_of=2, universe_source_sha256='a'*64, operating=[key],
        coverage={key: {'known_at': 1, 'continuous_complete': True, 'opportunity_count': 0, 'generation_sha256': 'b'*64}},
        custody={'654321': {'automatic_management_allowed': False}})
    scope.validate_scope(value)
    assert value['symbol_count'] == 2 and value['scope_count'] == 16
    assert value['counts']['operating_no_opportunity'] == 1
    assert value['counts']['custody_excluded'] == 8
    bad = scope.build_scope([{'code':'123456', 'known_at': 1, 'tradable': True}], as_of=2,
        universe_source_sha256='a'*64, operating=[key], coverage={key:{'known_at':1,
        'continuous_complete':True, 'opportunity_count':False, 'generation_sha256':'b'*64}})
    assert bad['counts']['operating_unobserved'] == 1


@pytest.mark.parametrize('bad_legs', [[{'at': '2026-10-08T09:00:00'}], ['broken'],
    [{'at': '2026-10-08T09:00:00', 'qty': 10, 'amount_krw': 1000}, {'at': None}]])
def test_completed_census_isolates_bad_fill_without_losing_healthy_position(bad_legs):
    p = position()
    trade = dict(id='healthy', main_automatic_management_allowed=True,
        status='COMPLETED', holding_ai_required=False,
        buy_fill_legs=[dict(at='2026-10-08T09:00:00', qty=10, amount_krw=1000)],
        trailing_replay_cost_model=p['cost_model'], actual_cost_reconciliation=p['actual_cost_reconciliation'],
        timeline=[dict(stage='scalp_trailing_input_transition', fields={
            'universal_trailing_quote':quote(1, '2026-10-08T09:00:01')})])
    result = replay.completed_census([trade, {**trade, 'id':'bad', 'buy_fill_legs':bad_legs}],
                                    incumbent=vector())
    assert result['population_ids'] == ['bad', 'healthy']
    parent = result['candidate_aliases']['incumbent']
    assert result['minimal_results']['bad'][parent]['status'] == 'source_gap'
    assert result['minimal_results']['healthy'][parent]['status'] == 'modeled_full_exit'


def test_quote_envelope_limit_includes_final_source_hash(monkeypatch):
    import json
    event = quote(1, '2026-10-08T09:00:01')
    kwargs = dict(known_at=event['known_at'], event_at=event['event_at'], route='KRX',
        item='123456', transport_epoch=1, sequence=1, bid=100.5, ask=102, bid_qty=10,
        peak=101, quantity=10, coverage_complete=True)
    result = replay.quote_projection(event['ws_data'], **kwargs)
    assert result['kind'] == 'QUOTE'
    size = len(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
    monkeypatch.setattr(replay, 'MAX_QUOTE_ENVELOPE_BYTES', size - 1)
    assert replay.quote_projection(event['ws_data'], **kwargs)['reason'] == 'shared_quote_envelope_budget_exceeded'


def test_parent_carry_all_market_types_and_forged_override_rejected():
    v = vector()
    bundle = typed.initial_bundle(v, parent_sha256=market_values_hash(v),
        source_date='2026-10-08', target_date='2026-10-12')
    prepared = typed.PreparedTrailingPolicy.prepare(bundle, target_date='2026-10-12', parent_sha256=market_values_hash(v))
    pin = typed.PreparedPin.prepare(typed.pin_context(None, position_key='main:1', entry_at=1), 'main:1')
    for market in START_MARKETS:
        assert prepared.effective(market, pin, position_key='main:1', target_date='2026-10-12') == v[market]
    altered = deepcopy(bundle)
    altered['cells']['REGULAR|BASE']['values']['SCALP_TRAILING_START_PCT'] = .7
    altered['policy_sha256'] = digest({k:v for k,v in altered.items() if k != 'policy_sha256'})
    with pytest.raises(ValueError, match='parent_or_authority'):
        typed.PreparedTrailingPolicy.prepare(altered, target_date='2026-10-12', parent_sha256=market_values_hash(v))


def test_classification_cannot_use_future_bars_or_relabel_on_missing_upper_features():
    classifier = dict(schema=typed.CLASSIFIER_SCHEMA, window_bars=2, trained_through=0,
        thresholds=dict(range_min=2, spread_min=.5, trend_return_min=.2, trend_efficiency_min=.5, vwap_min=0, rebound_min=.3))
    classifier['classifier_sha256'] = digest(classifier)
    f = {'status':'ready', 'known_at':2, 'anchor_at':2, 'window_bars':2, 'source_sha256':'a'*64, 'features':dict(
        range_pct=3, return_pct=1, trend_efficiency=.9, vwap_distance_pct=.5, spread_pct=.1, rebound_pct=1)}
    f['feature_sha256'] = digest(f['features'])
    pin = typed.pin_context(f, position_key='main:1', entry_at=2, classifier=classifier)
    assert pin['situation_type'] == 'HIGH_VARIABILITY'
    assert typed.pin_context(f, position_key='main:1', entry_at=1, classifier=classifier)['situation_type'] == 'BASE'
    assert typed.pin_context({**f, 'window_bars':3}, position_key='main:1', entry_at=2,
                             classifier=classifier)['reason'] == 'classification_source_gap'
    assert typed.pin_context({**f, 'source_sha256':None}, position_key='main:1', entry_at=2,
                             classifier=classifier)['reason'] == 'classification_source_gap'
    del f['features']['spread_pct']
    assert typed.pin_context(f, position_key='main:1', entry_at=2, classifier=classifier)['situation_type'] == 'BASE'


def test_replay_actual_economics_partial_unknown_safety_and_source_are_separate():
    p, e = position(), quote(1, '2026-10-08T09:00:01')
    outcome = replay.replay(p, [e], vector())
    assert outcome['status'] == 'modeled_full_exit'
    assert outcome['actual_pnl_krw'] == 4
    assert outcome['modeled_net_pnl_krw'] != outcome['actual_pnl_krw']
    assert outcome['strength_counts']['UNKNOWN'] == 1
    partial = replay.replay(p, [quote(1, '2026-10-08T09:00:01', qty=3)], vector())
    assert partial['status'] == 'censored' and partial['modeled_residual_qty'] == 7
    assert partial['modeled_net_pnl_krw'] is None
    safety = {'kind':'SAFETY_EXIT','event_at':p['entry_at']+.5,'known_at':p['entry_at']+.5}
    assert replay.replay(p, [safety, e], vector())['reason'] == 'higher_priority_safety_exit'
    e['bid'] = 1
    assert replay.replay(p, [e], vector())['reason'] == 'route_path_coverage_unverified'
    assert replay.replay({**p,'automatic_management_allowed':False}, [], vector())['reason'] == 'position_identity_or_custody_unverified'


def test_candidate_feature_path_prepared_once_and_state_never_crosses_positions(monkeypatch):
    calls = []
    original = replay.classify_ws_history
    monkeypatch.setattr(replay, 'classify_ws_history', lambda *a, **k: (calls.append(1) or original(*a, **k)))
    rows = [position(), {**position(), 'position_key':'main:2'}]
    paths = {r['position_key']:[quote(1, '2026-10-08T09:00:01')] for r in rows}
    candidate = vector()
    candidate['REGULAR']['SCALP_TRAILING_START_PCT'] = .5
    result = replay.summarize_partitions(rows, paths, {'copy':vector(), 'candidate':candidate}, incumbent=vector())
    assert len(calls) == 2 and result['unique_candidate_count'] == 2
    assert len(result['common_ids']) == 2


def test_ai_vote_is_bound_to_original_candidate_not_just_same_quote():
    p = {**position(), 'operating_ai_required':True, 'holding_ai_policy_sha256':'e'*64}
    event = quote(1, '2026-10-08T09:00:01')
    missing = replay.replay(p, [event], vector())
    assert missing['reason'] == 'candidate_holding_ai_input_unobserved'
    # A historical vote recorded at this original crossing, with its own seal.
    vote = dict(signal_at=event['known_at'], input_source_sha256=event['source_sha256'],
        input_context_sha256=missing['first_crossing']['input_context_sha256'],
        policy_sha256='e'*64, known_at=event['known_at'], decision='PASS',
        started_at=event['known_at'], max_defer_sec=30, max_worsen_pct=.2)
    vote['receipt_sha256'] = digest(vote)
    event['holding_ai'] = vote
    assert replay.replay(p, [event], vector())['status'] == 'modeled_full_exit'
    changed = vector()
    changed['REGULAR']['SCALP_TRAILING_START_PCT'] = .5
    other = replay.replay(p, [event], changed)
    assert other['first_crossing']['at'] == missing['first_crossing']['at']
    assert other['reason'] == 'candidate_holding_ai_input_unobserved'
    tampered = deepcopy(event)
    tampered['holding_ai']['decision'] = 'VETO'
    assert replay.replay(p, [tampered], vector())['reason'] == 'candidate_holding_ai_input_unobserved'
    legacy = deepcopy(event)
    del legacy['holding_ai']['input_context_sha256']
    legacy['holding_ai']['receipt_sha256'] = digest({k:v for k,v in legacy['holding_ai'].items() if k!='receipt_sha256'})
    assert replay.replay(p, [legacy], vector())['reason'] == 'candidate_holding_ai_input_unobserved'


def test_registered_type_grid_trains_before_holdout_and_keeps_failed_winner():
    from src.engine.scalping.trailing_mechanical_strength import CONFIG_DEFAULTS
    parent = vector()
    a, b = deepcopy(parent), deepcopy(parent)
    a['REGULAR']['SCALP_TRAILING_LIMIT_WEAK'] = .3
    b['REGULAR']['SCALP_TRAILING_LIMIT_WEAK'] = .2
    cfg = {m:dict(CONFIG_DEFAULTS) for m in START_MARKETS}
    aliases = {name:market_values_hash(v, cfg) for name,v in [('incumbent',parent),('a',a),('b',b)]}
    context, results = {}, {}
    start = at('2026-09-29T09:00:00')
    for day in range(10):
        for seq in range(6):
            identity = f'{day}:{seq}'
            entry = start + day*86400 + seq*10
            features = dict(range_pct=1,return_pct=.1,trend_efficiency=.2,vwap_distance_pct=-1,spread_pct=.1,rebound_pct=.1)
            source = dict(status='ready',known_at=entry-1,window_bars=2,source_sha256='a'*64,
                          features=features,feature_sha256=digest(features))
            context[identity] = dict(entry_at=entry,observation_end_at=entry+2,completion_at=entry+2,
                evidence_kind='actual_completed',buy_basis_krw=1000,entry_context=source)
            deltas = {'incumbent':0,'a':5 if day<7 else -2,'b':4 if day<7 else 8}
            results[identity] = {aliases[name]:dict(modeled_net_pnl_krw=delta,actual_pnl_krw=0,
                slippage_net_pnl_krw=[delta,delta,delta]) for name,delta in deltas.items()}
    part = dict(candidate_aliases=aliases,population_context=context,minimal_results=results,common_ids=sorted(context))
    hypotheses = []
    for width in (.5,2):
        hypothesis = dict(schema=typed.CLASSIFIER_SCHEMA,window_bars=2,trained_through=0,
            thresholds=dict(range_min=width,spread_min=.5,trend_return_min=.2,
                            trend_efficiency_min=.5,vwap_min=0,rebound_min=.5))
        hypothesis['classifier_sha256'] = digest(hypothesis)
        hypotheses.append(hypothesis)
    evaluation = replay.common_evaluation([part])
    result = typed.research_registered_grid([part],grid=hypotheses,candidates={'a':a,'b':b},
        parent_values=parent,parent_classifier_parameters=cfg,evaluation=evaluation)
    cell = result['cells']['actual_completed|REGULAR|HIGH_VARIABILITY']
    assert result['classifier']['thresholds']['range_min'] == .5
    assert result['classifier']['trained_through'] < start+7*86400
    assert cell['train_selected_candidate'] == 'a' and cell['holdout']['equal_weight_avg_profit_pct'] < 0
    assert cell['holdout_reselected'] is False and cell['disposition'] == 'parent_carry'
    assert not result['allowed_runtime_apply']
    changed = deepcopy(part)
    for row in changed['population_context'].values():
        row['entry_context']['known_at'] = row['entry_at']+1
    diagnostic = typed.research_registered_grid(lambda:iter([changed]),grid=hypotheses,candidates={'a':a,'b':b},
        parent_values=parent,parent_classifier_parameters=cfg,evaluation=evaluation)
    assert all(c['train_selected_candidate']=='incumbent' for c in diagnostic['cells'].values())


def test_candidate_cannot_replace_parent_alias():
    with pytest.raises(ValueError, match='approved_parent'):
        replay.summarize_partitions([position()], {}, {'incumbent':vector()}, incumbent=vector())


def test_prepared_m1_path_cannot_be_reused_for_another_classifier():
    from src.engine.scalping.trailing_mechanical_strength import CONFIG_DEFAULTS
    event = quote(1,'2026-10-08T09:00:01')
    prepared = replay.prepare_path([event])
    different = {m:dict(CONFIG_DEFAULTS) for m in START_MARKETS}
    different['REGULAR']['trade_window_ms'] = 500
    assert replay.replay(position(),prepared,vector(),classifier_config=different)['reason'] == 'm1_prepared_classifier_generation_changed'


def test_selector_reference_uses_original_byte_hash_and_warm_lookup_has_no_io(tmp_path,monkeypatch):
    import json,hashlib
    from pathlib import Path
    from src.utils import constants
    from src.engine.scalping.trailing_mechanical_strength import CONFIG_DEFAULTS
    monkeypatch.setattr(constants,'DATA_DIR',tmp_path)
    classifier=dict(schema=typed.CLASSIFIER_SCHEMA,window_bars=2,trained_through=0,
        thresholds=dict(range_min=.5,spread_min=.5,trend_return_min=.2,trend_efficiency_min=.5,vwap_min=0,rebound_min=.5))
    classifier['classifier_sha256']=digest(classifier)
    report={'situation_scope':{'market':'REGULAR','situation_type':'HIGH_VARIABILITY'},
            'situation_classifier_sha256':classifier['classifier_sha256']}
    raw=(json.dumps(report,indent=2)+'\n').encode()
    report_path=tmp_path/'report/type_report.json';report_path.parent.mkdir();report_path.write_bytes(raw)
    sha=hashlib.sha256(raw).hexdigest()
    assert sha!=digest(report)
    parent=vector();m1={m:dict(CONFIG_DEFAULTS) for m in START_MARKETS}
    values=deepcopy(parent);values['REGULAR']['SCALP_TRAILING_START_PCT']=.5
    policy={'market_values':values,'classifier_parameters':m1,'rollback_market_values_sha256':market_values_hash(parent,m1),'source_report_sha256':sha}
    policy_path=tmp_path/'report/type_policy.json';policy_path.write_text(json.dumps(policy))
    calls=[]
    def existing_selector(policy,report,*,target_date,report_sha256):
        assert report_sha256==policy['source_report_sha256']==sha
        calls.append(target_date)
        return {}
    # This fixture isolates byte/reference transport. Economic approval remains
    # the existing selector's independently tested contract, and is still called.
    monkeypatch.setattr(typed,'selected_policy_env',existing_selector)
    reference={'report_path':'report/type_report.json','report_byte_sha256':sha,
               'policy_path':'report/type_policy.json','policy_byte_sha256':hashlib.sha256(policy_path.read_bytes()).hexdigest()}
    evidence={'evidence_kind':'actual_completed_paired','parent_sha256':market_values_hash(parent,m1),'selector_evidence_reference':reference}
    bundle=typed.initial_bundle(parent,parent_sha256=market_values_hash(parent,m1),source_date='2026-10-08',target_date='2026-10-12',
        classifier=classifier,parent_classifier_parameters=m1,overrides={'REGULAR|HIGH_VARIABILITY':evidence})
    assert bundle['evidence_kind']=='actual_completed_paired_selected'
    prepared=typed.PreparedTrailingPolicy.prepare(bundle,target_date='2026-10-12',parent_sha256=market_values_hash(parent,m1))
    assert len(calls)==2 and len(json.dumps(bundle).encode())<64000
    changed=deepcopy(classifier);changed['thresholds']['range_min']=2
    changed['classifier_sha256']=digest({k:v for k,v in changed.items() if k!='classifier_sha256'})
    with pytest.raises(ValueError,match='selector_scope'):
        typed.initial_bundle(parent,parent_sha256=market_values_hash(parent,m1),source_date='2026-10-08',target_date='2026-10-12',
            classifier=changed,parent_classifier_parameters=m1,overrides={'REGULAR|HIGH_VARIABILITY':evidence})
    fields=dict(range_pct=1,return_pct=0,trend_efficiency=0,vwap_distance_pct=0,spread_pct=.1,rebound_pct=0)
    ctx=dict(status='ready',window_bars=2,known_at=1,source_sha256='a'*64,features=fields,feature_sha256=digest(fields))
    pin=typed.PreparedPin.prepare(typed.pin_context(ctx,position_key='main:1',entry_at=2,classifier=classifier),'main:1')
    with monkeypatch.context() as warm:
        warm.setattr(Path,'read_bytes',lambda *a:pytest.fail('warm selector file I/O'))
        assert prepared.effective('REGULAR',pin,position_key='main:1',target_date='2026-10-12')['SCALP_TRAILING_START_PCT']==.5
    report_path.write_bytes(raw.replace(b'REGULAR',b'PRE____'))
    with pytest.raises(ValueError,match='reference_generation'):
        typed.PreparedTrailingPolicy.prepare(bundle,target_date='2026-10-12',parent_sha256=market_values_hash(parent,m1))


def test_typed_overrides_cannot_combine_multiple_market_canaries(monkeypatch):
    parent=vector()
    classifier=dict(schema=typed.CLASSIFIER_SCHEMA,window_bars=2,trained_through=0,
        thresholds=dict(range_min=.5,spread_min=.5,trend_return_min=.2,trend_efficiency_min=.5,vwap_min=0,rebound_min=.5))
    classifier['classifier_sha256']=digest(classifier)
    # Isolate the composition guard after each existing selector accepted its
    # own child. Combining separate PRE and REGULAR approvals is still invalid.
    monkeypatch.setattr(typed,'_override_values',lambda *a,**kw:{**parent[kw['market']],'SCALP_TRAILING_START_PCT':.5})
    with pytest.raises(ValueError,match='one_market_canary'):
        typed.initial_bundle(parent,parent_sha256=market_values_hash(parent),source_date='2026-10-08',target_date='2026-10-12',
            classifier=classifier,overrides={'REGULAR|HIGH_VARIABILITY':{},'PREMARKET|HIGH_VARIABILITY':{}})


def test_large_native_clock_and_sequence_projection_is_lossless_and_bounded():
    from src.tests.test_scalp_trailing_mechanical_strength import _trade
    base=int(at('2026-10-08T09:00:00')*1000)
    depths=[_depth(12345678+i,base+i*100,2147483647,2147483647) for i in range(120)]
    trades=[_trade(23456789+i,base+i*100,'BUY') for i in range(120)]
    for row in trades:
        row['volume']=2147483647
        row['price']=1234567
    ws=_snapshot(depths,trades)
    packed=replay.compact_ws(ws); restored=replay.expand_ws(packed)
    assert [(r['route_sequence'],r['received_at_ms']) for r in restored['recent_depth_ticks_by_route']['KRX|KRX']]==[(r['route_sequence'],r['received_at_ms']) for r in depths]
    assert [(r['route_sequence'],r['received_at_ms'],r['volume']) for r in restored['recent_trade_ticks_by_route']['KRX|KRX']]==[(r['route_sequence'],r['received_at_ms'],r['volume']) for r in trades]
    result=replay.quote_projection(ws,known_at=(base+11900)/1000,event_at=(base+11900)/1000,
        route='KRX',item='123456',transport_epoch=1,sequence=12345797,bid=100,ask=101,
        bid_qty=2147483647,peak=101,quantity=10,coverage_complete=True)
    assert result['kind']=='QUOTE'


def test_result_construction_is_admitted_before_m1_allocation(monkeypatch):
    from src.engine.lifecycle.research_input_budget import Claim,LIMIT_BYTES,health
    def no_feature(*a,**kw):
        pytest.fail('M1 allocated before shared result budget admission')
    monkeypatch.setattr(replay,'prepare_path',no_feature)
    with Claim(LIMIT_BYTES-health()['used_bytes']-1024):
        with pytest.raises(ValueError,match='partition_resume_required'):
            replay.summarize_partitions([position()],{}, {},incumbent=vector())


def reseal(event):
    event['quote_snapshot_sha256'] = digest(event['ws_data'])
    event['sell_execution_plan']['quote_source_sha256'] = event['quote_snapshot_sha256']
    event['source_sha256'] = digest({k:v for k,v in event.items() if k != 'source_sha256'})
    return event


@pytest.mark.parametrize('clock,market', [('2026-10-08T08:00:00','PREMARKET'),
    ('2026-10-08T09:00:00','REGULAR'), ('2026-10-08T16:00:00','INTEGRATED_AFTERMARKET')])
def test_first_crossing_uses_each_markets_permission(clock, market):
    p = {**position(), 'entry_at':at(clock)}
    event = quote(1, clock[:-2]+'01')
    result = replay.replay(p, [event], vector())
    assert result['status'] == 'modeled_full_exit'
    assert result['first_crossing']['market'] == market
    assert result['allowed_runtime_apply'] is False


def test_add_keeps_peak_arm_and_cost_basis_without_future_add_lookahead():
    p = position()
    first = quote(1, '2026-10-08T09:00:01', bid=100.8, peak=100.8)
    added = dict(kind='ADD',event_at=p['entry_at']+2,known_at=p['entry_at']+2,
        qty=5,buy_amount_krw=500,buy_cost_krw=0,buy_generation_sha256='d'*64)
    final = quote(2,'2026-10-08T09:00:03',bid=100.3,peak=100.8,qty=15)
    final['sell_execution_plan']['quantity']=15; reseal(final)
    result=replay.replay(p,[first,added,final],vector())
    assert result['status']=='modeled_full_exit' and result['modeled_sold_qty']==15
    early=quote(1,'2026-10-08T09:00:01')
    assert replay.replay(p,[early,added],vector())['reason']=='candidate_exit_changes_observed_add_path'


def test_overnight_path_and_restart_epoch_are_not_truncated_at_regular_close():
    p={**position(),'entry_at':at('2026-10-07T19:59:58')}
    first=quote(1,'2026-10-07T19:59:59',bid=100.8,peak=100.8)
    following=quote(1,'2026-10-08T08:00:01',bid=100.3,peak=100.8)
    following['transport_epoch']=2;following['ws_data']['market_data_transport_epoch']=2
    for rows in following['ws_data']['recent_depth_ticks_by_route'].values():
        for row in rows: row['transport_epoch']=2
    reseal(following)
    result=replay.replay(p,[first,following],vector())
    assert result['status']=='modeled_full_exit'
    assert result['first_crossing']['market']=='PREMARKET'


def test_optional_bad_projection_does_not_raise_and_native_touch_mismatch_is_censored():
    result=replay.quote_projection({'recent_depth_ticks_by_route':{'broken':[None]}}, known_at=1,
        event_at=1, route='KRX',item='123456',transport_epoch=1,sequence=1,bid=100,ask=101,
        bid_qty=10,peak=101,quantity=10,coverage_complete=True)
    assert result['status']=='source_gap'
    e=quote(1,'2026-10-08T09:00:01')
    e['ws_data']['recent_depth_ticks_by_route']['KRX|KRX'][0]['bid_levels'][0]['price']=1
    reseal(e)
    assert replay.replay(position(),[e],vector())['reason']=='m1_snapshot_execution_touch_mismatch'


def test_compact_route_projection_preserves_m1_and_omits_unconsumed_payload():
    import json
    from src.tests.test_scalp_trailing_mechanical_strength import _trade
    from src.engine.scalping.trailing_mechanical_strength import classify_ws_history
    original_state = compact_state = None
    base = int(at('2026-10-08T09:00:00') * 1000)
    for count in range(1, 5):
        depths = [_depth(i+1, base+i*100, 10+i, 5) for i in range(count)]
        trades = [_trade(i+1, base+i*100, 'BUY' if i < 2 else 'SELL') for i in range(count)]
        ws = _snapshot(depths, trades)
        for row in ws['recent_depth_ticks_by_route']['KRX|KRX']:
            row['unused_raw_payload'] = 'x'*10000
            row['bid_levels'] += [{'price':99, 'quantity':100000}]*9
        ws['recent_depth_ticks_by_route']['OTHER|OTHER'] = [{'raw_payload':'y'*100000}]
        compact = replay.compact_ws(ws)
        actual, original_state = classify_ws_history(ws, original_state, now_ms=base+(count-1)*100,
                                                      max_quote_age_ms=700, market='REGULAR')
        restored, compact_state = classify_ws_history(replay.expand_ws(compact), compact_state,
                                                      now_ms=base+(count-1)*100, max_quote_age_ms=700, market='REGULAR')
        assert actual == restored and original_state == compact_state
        assert len(json.dumps(compact).encode()) < 2000
    q = replay.quote_projection(ws, known_at=(base+300)/1000, event_at=(base+300)/1000,
        route='KRX', item='123456', transport_epoch=1, sequence=4, bid=100, ask=101, bid_qty=13,
        peak=101, quantity=10, coverage_complete=True)
    assert q['kind'] == 'QUOTE' and q['ws_data']['schema'] == replay.WS_PROJECTION_SCHEMA
    assert q['quote_snapshot_sha256'] == digest(q['ws_data'])
    modeled = replay.replay(position(), [q], vector())
    assert modeled['status'] == 'modeled_full_exit'
    assert modeled['strength_counts'] == {'UNKNOWN':1}
    full = {**q, 'ws_data':ws, 'quote_snapshot_sha256':digest(ws),
            'sell_execution_plan':{**q['sell_execution_plan'], 'quote_source_sha256':digest(ws)}}
    full['source_sha256'] = digest({k:v for k,v in full.items() if k != 'source_sha256'})
    direct = replay.replay(position(), [full], vector())
    assert modeled['modeled_net_pnl_krw'] == direct['modeled_net_pnl_krw']
    assert modeled['reason'] == direct['reason']
    q['sequence'] = True
    reseal(q)
    assert replay.replay(position(), [q], vector())['reason'] == 'source_sequence_invalid'


def test_situation_pin_survives_add_restart_and_new_policy_generation(tmp_path):
    from src.engine.scalping.position_peak_ledger import PositionPeakRuntimeLedger, position_cycle_id
    ledger=PositionPeakRuntimeLedger(tmp_path/'peaks.json')
    stock=dict(id=12,code='123456',buy_price=100,buy_qty=10)
    ledger.record(stock,peak_price=102,observed_at=1,reason='first_buy')
    pin=typed.pin_context(None,position_key=position_cycle_id(stock),entry_at=1)
    assert ledger.record_situation_pin(stock,pin)
    ledger.record_trailing_arm(stock,observed_at=2,market='REGULAR',start_pct=.4,policy_sha256='parent')
    added={**stock,'buy_price':101,'buy_qty':20}
    ledger.record(added,peak_price=102,observed_at=3,reason='add')
    restored=PositionPeakRuntimeLedger(ledger.path).get_for_stock(added)
    assert restored['trailing_situation_pin']==pin and restored['trailing_arm_at_epoch']==2
    changed=typed.pin_context(None,position_key=position_cycle_id(stock),entry_at=4)
    assert ledger.record_situation_pin(added,changed) is False


def test_wrong_route_and_identified_malformed_path_cannot_create_economics():
    p=position(); e=quote(1,'2026-10-08T09:00:01')
    e['ws_data']['recent_depth_ticks_by_route']['NXT|NXT_ONLY']=e['ws_data']['recent_depth_ticks_by_route'].pop('KRX|KRX')
    reseal(e)
    assert replay.replay(p,[e],vector())['reason']=='m1_snapshot_execution_touch_mismatch'
    result=replay.summarize_partitions([p,{**p,'position_key':'bad'}],
        {p['position_key']:[quote(1,'2026-10-08T09:00:01')],'bad':[None]}, {},incumbent=vector())
    assert result['common_ids']==[p['position_key']]
    assert result['excluded_ids']==['bad']
    assert replay.replay({**p,'cost_model':{**p['cost_model'],'known_at':p['entry_at']+1}},[],vector())['reason']=='cost_model_not_known_at_entry'
