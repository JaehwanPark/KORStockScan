from copy import deepcopy
import random

import pytest

from src.engine.scalping import samsung_pattern_campaign as C


def cache(n=2800, step=.25):
    rows = [dict(t=i*step,ex=i*step,ep=1,seq=i+1,continuous=True,
        valid=True,flow_valid=True,p=270000.,q=10.,side='SELL') for i in range(n)]
    depth = [dict(t=i*step-.1,ex=i*step-.1,ep=1,seq=i+1,continuous=True,valid=True,
        bid=270000.,ask=270500.,bq=100.,aq=100.) for i in range(n)]
    return dict(rows=rows,depth=depth)


def signal(c, index=4):
    return dict(index=index,t=c['rows'][index]['t'])


def test_tree_first_matches_chronological_brute_force():
    rng = random.Random(109)
    for _ in range(50):
        values = [rng.randrange(100,120) for _ in range(rng.randrange(1,90))]
        tree = C.PriceTree(values)
        for _ in range(20):
            left = rng.randrange(len(values)); right = rng.randrange(left+1,len(values)+1)
            assert tree.extrema(left,right)==(min(values[left:right]),max(values[left:right]))
            expected = next((i for i in range(left,right) if values[i]>=115 or values[i]<=105),None)
            assert tree.first(left,right,115,105)==expected
    assert C.PriceTree([]).first(0,0,1,-1) is None


def test_terminal_before_later_gap_has_valid_support():
    c = cache()
    for q in c['depth'][100:200]: q.update(bid=272000.,ask=272500.)
    for q in c['depth'][300:310]: q['valid']=False
    out = C.label(C.campaign_context(c),signal(c))
    assert out['complete'] and out['binary']==1 and out['after_terminal_gap_ignored']
    assert out['exit_t']==c['depth'][100]['t']


def test_single_invalid_quote_before_terminal_cannot_be_skipped():
    c=cache();c['depth'][100]['valid']=False
    for q in c['depth'][200:]:q.update(bid=272000.,ask=272500.)
    for limit in (1.5,3.,10.):
        out=C.label(C.campaign_context(c,limit),signal(c))
        assert out['status']=='censored_before_terminal' and out['net'] is None


def test_invalid_quote_just_before_time_exit_cannot_be_bridged_by_fresh_endpoint():
    c=cache();c['depth'][2401]['valid']=False
    out=C.label(C.campaign_context(c),signal(c))
    assert out['status']=='censored_before_terminal' and out['net'] is None


def test_observed_gap_sensitivity_preserves_sequence_and_fresh_entry():
    c=cache();del c['depth'][100:107]
    for i,q in enumerate(c['depth']):q['seq']=i+1
    for q in c['depth'][200:]:q.update(bid=272000.,ask=272500.)
    assert C.label(C.campaign_context(c),signal(c))['status']=='censored_before_terminal'
    assert C.label(C.campaign_context(c,3.),signal(c))['binary']==1
    c['depth'][100]['continuous']=False
    assert C.label(C.campaign_context(c,10.),signal(c))['status']=='censored_before_terminal'


@pytest.mark.parametrize('limit',[None,True,-1,0,11])
def test_gap_sensitivity_rejects_invalid_model(limit):
    with pytest.raises(ValueError):C.campaign_context(cache(),limit)


def test_target_after_prior_gap_does_not_recover_support():
    c = cache()
    for q in c['depth'][100:110]: q['valid']=False
    for q in c['depth'][300:]: q.update(bid=272000.,ask=272500.)
    out = C.label(C.campaign_context(c),signal(c))
    assert out['status']=='censored_before_terminal' and out['net'] is None


def test_locked_quotes_are_context_only_never_entry_or_terminal():
    c = cache()
    for q in c['depth'][100:200]: q.update(bid=272000.,ask=272000.)
    out = C.label(C.campaign_context(c),signal(c))
    assert out['status']=='neither'
    assert C.label(C.campaign_context(c),signal(c,110))['status']=='nonactionable_entry'
    for q in c['depth'][200:300]: q.update(bid=272000.,ask=272500.)
    out = C.label(C.campaign_context(c),signal(c))
    assert out['binary']==1 and out['exit_t']==c['depth'][200]['t']


@pytest.mark.parametrize('field',['bq','aq'])
def test_nonpositive_quantity_cannot_execute_boundary(field):
    c = cache()
    for q in c['depth'][100:200]: q.update(bid=272000.,ask=272500.); q[field]=0
    assert C.label(C.campaign_context(c),signal(c))['status']=='neither'


def test_observed_price_cost_is_not_replaced_by_target_or_zero():
    c = cache()
    for q in c['depth'][100:200]: q.update(bid=272000.,ask=272500.)
    out = C.label(C.campaign_context(c),signal(c))
    assert out['entry']['price']==270500
    assert out['net']==pytest.approx((272000/270500-1)*100-.33)
    assert out['cost_pct']==.33 and out['native_identity'] is None


def test_neither_has_null_binary_and_time_exit_cf():
    c = cache(); out = C.label(C.campaign_context(c),signal(c))
    assert out['binary'] is None and out['complete'] and out['net']<0
    assert C.metric([out])['binary']==0 and C.metric([out])['neither']==1


def test_clock_invalid_extreme_is_excluded_without_interpolation():
    c = cache(); c['depth'][100].update(valid=False,bid=9999999.)
    assert C.label(C.campaign_context(c),signal(c))['binary'] is None


@pytest.mark.parametrize('defect',['ep','seq','continuous'])
def test_break_before_future_target_censors(defect):
    c = cache()
    c['depth'][100][defect] = 2 if defect=='ep' else 999 if defect=='seq' else False
    for q in c['depth'][200:]: q.update(bid=272000.,ask=272500.)
    assert C.label(C.campaign_context(c),signal(c))['net'] is None


def test_latency_prices_are_after_decision_and_missing_is_not_zero():
    c = cache()
    for q in c['depth'][5:]: q.update(bid=270500.,ask=271000.)
    out = C.label(C.campaign_context(c),signal(c),latency=1.)
    assert out['entry']['t']>=out['decision']['t']+1
    assert out['entry']['price']==271000
    c['rows'][5]['valid']=False
    out = C.label(C.campaign_context(c),signal(c),latency=1.)
    assert out['status']=='latency_trade_gap' and out['net'] is None


def test_first_receipt_per_second_and_full_causal_window():
    c = cache(1400)
    frames = C.feature_rows(c)
    assert len({int(f['t']) for f in frames})==len(frames)
    assert min(f['t'] for f in frames)>=60
    assert frames[0]['windows']['60']['low']==270000
    assert frames[0]['windows']['60']['vwap']==270000
    assert all(c['depth'][f['quote_index']]['t'] < f['t'] for f in frames)


def test_feature_prefix_is_equal_even_if_future_crashes():
    c = cache(1400)
    prefix = deepcopy(c); prefix['rows']=prefix['rows'][:1000]; prefix['depth']=prefix['depth'][:1000]
    full = [f for f in C.feature_rows(c) if f['index']<1000]
    assert C.feature_rows(prefix)==full
    for q in c['depth'][1000:]: q.update(bid=250000.,ask=250500.)
    assert [f for f in C.feature_rows(c) if f['index']<1000]==full


def test_depth_gap_resets_past_low_hold_and_vwap_confirmation():
    c = cache(1400); c['depth'][900]['valid']=False
    frames = C.feature_rows(c)
    assert not [f for f in frames if 225<=f['t']<285]


def frame():
    return dict(index=0,t=0.,ep=1,hour=9,spread=500,hold=5,hold_quotes=20,sell_count=10,
        sell_dominant=True,buy_share=.7,prior_buy_share=.3,sell_decay=.25,
        volume_acceleration=2.,bid=270500.,ask=271000.,depth_ratio=2.,prior_depth_ratio=.8,
        bid_replenishment=1.4,ask_depletion=.5,
        windows={'60':dict(low=270000.,high=272000.,half_low=270500.,drawdown=1500.,
            distance=500.,vwap=270400.,vwap_cross=True,retest=True,previous_high=270500.)})


@pytest.mark.parametrize('family',C.FAMILIES)
def test_family_is_meaningful_and_missing_window_fails(family):
    f = frame(); r = dict(family=family,window=60,level=1,region='all')
    assert C.qualifies(f,r)
    f['windows']={}
    assert not C.qualifies(f,r)


def test_retest_is_not_continuous_unchanged_bid_hold():
    c = cache(1400)
    assert all(not f['windows']['60']['retest'] for f in C.feature_rows(c))


def test_missing_outcome_cannot_replace_first_admission_or_release_reservation():
    fs = []
    for t in (0.,1.,600.,601.,602.,1204.):
        f = frame(); f['t']=t; fs.append(f)
    rule = dict(family='absorption',window=60,level=1,region='all')
    assert [f['t'] for f in C.select(fs,600,rule)]==[0.,602.,1204.]


def test_train_selection_prefers_win_rate_without_success_or_ev_veto():
    base = {'all:600':dict(binary=4,win_rate=.5)}
    a = dict(family='absorption',window=60,level=1,region='all',horizon=600,
        metric=dict(binary=4,win_rate=.75,wilson=.3,mean_net_cf=-.5,lost_old_winner=1))
    b = {**a,'family':'flow_flip','metric':{**a['metric'],'win_rate':.6}}
    assert C.choose([a,b],base)==a
    assert C.choose([{**a,'metric':{**a['metric'],'binary':2}}],base) is None


def test_native_bridge_keeps_first_native_admission_hard_guard_and_label():
    f = frame(); f['t']=10
    rows = []
    for t,action,cohort,blockers in [(11.,'ENTER_NOW','parent_enter',[]),
        (11.2,'RECHECK','soft_confirmation_only',[]),(11.4,'BLOCK','other_guard_or_wait',['hard'])]:
        rows.append(dict(native=['same-native'],day='d',t=t,trace=str(t),parent=action,
            guard=dict(cohort=cohort,blockers=blockers),recoverable=True,
            label=dict(binary=1,net=.1),cost=.322,features=dict(stream_epoch=1,stream_valid=True)))
    result = C.native_bridge(dict(main=rows),dict(d=[f]),
        dict(family='absorption',window=60,level=1,region='all'))
    assert result['native_groups']==1 and result['candidate']['admitted']==1
    assert result['hits_outside_preserved_guard']==1
    assert result['groups'][0]['candidate']['trace']=='11.0'
    assert result['observations'][-1]['admitted'] is False


def test_authority_cannot_be_overridden_and_report_seal_is_not_self_hashed(tmp_path):
    path = tmp_path/'a.json'
    C.write(path,dict(runtime_effect=True,content_sha256='old',a=1))
    value = C.R.read(path)
    assert value['runtime_effect'] is False and value['policy_publication_forbidden'] is True


@pytest.mark.parametrize('cost',[float('nan'),-1,None,True])
def test_bad_cost_model_is_rejected_not_profitable(cost):
    with pytest.raises(ValueError,match='price_model'):
        C.label(C.campaign_context(cache()),signal(cache()),cost_pct=cost)


def test_fee_only_quote_comparison_and_stress_are_explicitly_different():
    c = cache()
    for q in c['depth'][100:200]: q.update(bid=271500.,ask=272000.)
    ctx = C.campaign_context(c)
    stress = C.label(ctx,signal(c),cost_pct=.33)
    quote_fee = C.label(ctx,signal(c),cost_pct=.23)
    assert stress['binary'] is None and quote_fee['binary']==1
    assert quote_fee['cost_pct']==.23


def test_normalized_three_level_contract_and_malformed_is_missing():
    row = dict(best_bid=270000.,best_ask=270500.,best_bid_qty=100,best_ask_qty=100,
        bid_levels=[[1,270000.,100],[2,269500.,100],[3,269000.,100]],
        ask_levels=[[1,270500.,100],[2,271000.,100],[3,271500.,100]])
    assert C.normalized_book(row)==dict(bid_sum=300,ask_sum=300)
    bad = deepcopy(row); bad['bid_levels'][1][1]=271000.
    assert C.normalized_book(bad) is None
    bad = deepcopy(row); bad['bid_levels'][0][2]=99
    assert C.normalized_book(bad) is None
    bad = deepcopy(row); bad['ask_levels'][2][2]=-1
    assert C.normalized_book(bad) is None
    bad = deepcopy(row);bad['bid_levels'][0][0]=True
    assert C.normalized_book(bad) is None


def test_book_history_is_past_only_and_gap_does_not_create_replenishment():
    c = cache(1400)
    books = {(q['ep'],q['seq']):dict(bid_sum=300,ask_sum=100) for q in c['depth']}
    fs = C.feature_rows(c,books)
    assert fs[0]['depth_ratio']==3 and fs[0]['prior_depth_ratio']==3
    books[(1,300)] = None
    fs = C.feature_rows(c,books)
    assert all(f['bid_replenishment'] is None for f in fs if 75<=f['t']<=79)
    prefix = deepcopy(c);prefix['rows']=prefix['rows'][:1000];prefix['depth']=prefix['depth'][:1000]
    assert C.feature_rows(prefix,books)==[f for f in fs if f['index']<1000]


def test_cost_headroom_uses_past_high_ask_and_matching_cost():
    f = frame(); f['windows']['60']['high']=272000.
    r = dict(family='sell_decay',window=60,level=1,region='all',room_net=.1,cost_pct=.33)
    assert not C.qualifies(f,r)
    r['cost_pct']=.23
    assert C.qualifies(f,r)


def test_registry_discloses_all_model_combinations():
    rs = C.rules(.23)
    assert sum(len(r['horizons']) for r in rs)==2808
    assert len({r['id'] for r in rs})==len(rs)


def test_manifest_itself_is_bound_and_change_during_run_is_detected(tmp_path):
    path=tmp_path/'manifest.json'
    C.write(path,dict(records={},files={}))
    manifest,seals,sha=C.load_manifest(path)
    assert seals[str(path)]==sha and manifest['files']=={}
    C.write(path,dict(records={},files={},changed=True))
    with pytest.raises(ValueError,match='sealed_file_changed'):
        C.Q.verify_hashes(seals)


def test_three_level_hypothesis_consumes_five_level_local_snapshot():
    row=dict(best_bid=270000.,best_ask=270500.,best_bid_qty=100, best_ask_qty=100,
        bid_levels=[[i+1,270000.-i*500,100 if i<3 else 10000] for i in range(5)],
        ask_levels=[[i+1,270500.+i*500,100 if i<3 else 20000] for i in range(5)])
    assert C.normalized_book(row)==dict(bid_sum=300,ask_sum=300)
    # The unused tail still belongs to the source snapshot contract.
    row['bid_levels'][4][1]=271000.
    assert C.normalized_book(row) is None


def test_common_clock_does_not_turn_longer_candidate_window_into_entry_effect():
    c=cache(2800);f=frame();f.update(index=4,t=1.)
    later=frame();later.update(index=100,t=25.)
    for q in c['depth'][2450:]:q.update(bid=272000.,ask=272500.)
    rule=dict(horizon=600,cost_pct=.33,region='all')
    result=C.common_clock_comparison(C.campaign_context(c),[f,later],[later],rule)
    assert result['candidate']['wins']==0
    assert C.label(C.campaign_context(c),later,600)['binary']==1
    assert result['mean_endpoint_delta']==0 and result['gained_targets']==0


def test_common_endpoint_positive_flag_uses_its_own_cost_model():
    c=cache(2800);f=frame();f.update(index=4,t=1.)
    for q in c['depth'][2000:]:q.update(bid=271250.,ask=271750.)
    result=C.common_clock_comparison(C.campaign_context(c),[f],[f],
        dict(horizon=600,cost_pct=.23,region='all'))
    p=result['rows'][0]['endpoint']
    assert p['candidate_positive_cf'] and p['candidate_net_cf']>0
