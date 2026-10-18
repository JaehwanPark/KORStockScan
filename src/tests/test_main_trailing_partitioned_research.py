"""Whole-population parity and exact dependency invalidation for v2 storage."""
import json
from pathlib import Path
import pytest
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation,capture_window
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.engine.automation import main_trailing_all_scope_research as owner
from src.engine.automation import main_trailing_partitioned_research as research
from src.engine.automation.main_trailing_population_aggregation import aggregate
from src.engine.scalping.universal_trailing_replay import common_evaluation
from src.tests.test_main_all_scope_research import fixture,write,entry_window_fixture
from src.tests.test_main_all_scope_trailing import at


@pytest.mark.parametrize('damage', [None, 'code', 'target', 'source', 'extension', 'bytes'])
def test_bounded_trailing_observation_detects_stale_generation_without_replaying_sources(tmp_path, damage):
    from src.engine.automation.main_trailing_research_handoff import observe_extension
    report = dict(schema='main_all_scope_exit_research_v2', status='complete',
                  source_date='2026-10-16', target_date='2026-10-19',
                  code_contract_sha256=owner.code_contract(), allowed_runtime_apply=False,
                  input_window_generation_sha256='a'*64,
                  initial_policy=dict(policy_sha256='b'*64), scope=dict(scope_count=20832))
    if damage in {'code', 'target', 'source'}:
        report[{'code':'code_contract_sha256', 'target':'target_date', 'source':'source_date'}[damage]] = 'invalid'
    path = tmp_path/'research.json';write(path,report)
    extension = dict(report_path=str(path), report_generation=byte_generation(path),
                     status='complete', input_window_generation_sha256='a'*64,
                     initial_policy_sha256='b'*64, scope_count=20832, allowed_runtime_apply=False)
    if damage == 'extension': extension['scope_count'] = 1
    if damage == 'bytes': path.write_text('{}')
    result = observe_extension(dict(date='2026-10-16', all_scope_trailing_research=extension),
                               target_date='2026-10-19')
    assert result['full_source_revalidation_performed'] is False
    assert result['runtime_effect'] is False
    assert result['status'] == ('generation_current' if damage is None else 'source_invalid')
    assert bool(result['findings']) == (damage is not None)


def sharded(tmp_path,source_fixture=fixture):
    root,out=source_fixture(tmp_path)
    manifest=owner._sealed(root/'manifest.json');refs=[]
    for part in manifest.pop('partitions'):
        payload=owner._sealed(root/part['path'])
        payload.pop('artifact_sha256')
        payload['paths']={i:storage.write_tree(root,events) for i,events in payload['paths'].items()}
        part['artifact_sha256']=write(root/part['path'],payload);refs.append(part)
    manifest.pop('artifact_sha256');ids=manifest.pop('population_ids')
    manifest.update(schema='main_all_scope_exit_input_manifest_v2',source_data_root=str(root),
        source_generations_ref=storage.write_tree(root,[]),partitions_ref=storage.write_tree(root,refs),
        population_ids_ref=storage.write_tree(root,ids),input_window_generation_sha256=capture_window(root,manifest['consumed_dates'])['input_window_generation_sha256'],
        assembly_census={'source_gaps':{}})
    write(root/'manifest.json',manifest)
    return root,out


def test_v2_replay_resume_and_source_pin(tmp_path,monkeypatch):
    root,out=sharded(tmp_path)
    first=owner.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False)
    assert first['status']=='complete' and first['scope']['scope_count']==8
    second=owner.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False,resume=True)
    assert second['counters']['checkpoint_reused']==2
    assert first['initial_policy']==second['initial_policy']
    assert first['common_population_evaluation']==second['common_population_evaluation']
    assert storage.logical_value(first['partition_results_ref'])==storage.logical_value(second['partition_results_ref'])
    original=research.aggregate
    def change_after_replay(*args,**kwargs):
        result=original(*args,**kwargs)
        path=root/'manifest.json';value=owner._sealed(path);value.pop('artifact_sha256');value['as_of']+=1;write(path,value)
        return result
    monkeypatch.setattr(research,'aggregate',change_after_replay)
    with pytest.raises(ValueError,match='manifest_changed'):
        owner.run(root/'manifest.json',input_root=root,output_root=tmp_path/'bad',dry_run=False)
    assert not (tmp_path/'bad'/'initial_policy_2026-10-12.json').exists()


@pytest.mark.parametrize('evidence',['actual_completed','actual_entry_alternative_exit','enter_pass_opportunity_cf'])
@pytest.mark.parametrize('offset',[-1,0])
def test_v2_entry_window_censors_carry_preserves_census_and_resume(tmp_path,evidence,offset):
    root,out=sharded(tmp_path,lambda path:entry_window_fixture(path,evidence,offset))
    sources={str(p.relative_to(root)):byte_generation(p) for p in root.rglob('*') if p.is_file()}
    first=owner.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False)
    refs=list(storage.iter_tree(out,first['partition_results_ref']))
    checkpoint=out/refs[0]['path'];original=checkpoint.read_bytes()
    results=list(research.checkpoint_results(owner._sealed(checkpoint),out))
    assert results[0]['population_context']['main:0']['entry_at']==at('2026-10-07T00:00:00')+offset
    assert results[0]['population_context']['main:0']['research_entry_window_start_at']==at('2026-10-07T00:00:00')
    assert results[0]['common_ids']==([] if offset<0 else ['main:0'])
    assert first['missing_population_ids_ref']['count']==0
    assert first['assembly_census']=={'source_gaps':{}}
    if offset<0:
        assert first['counters']['entry_before_research_window']==1
        assert all(r['status']=='source_gap' and r['reason']=='entry_before_research_window'
            and r['modeled_net_pnl_krw'] is None and r['actual_pnl_krw'] is None
            for r in results[0]['minimal_results']['main:0'].values())
    again=owner.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False,resume=True)
    clean_out=tmp_path/'clean'
    clean=owner.run(root/'manifest.json',input_root=root,output_root=clean_out,dry_run=False)
    clean_ref=next(storage.iter_tree(clean_out,clean['partition_results_ref']))
    assert list(research.checkpoint_results(owner._sealed(clean_out/clean_ref['path']),clean_out))==results
    assert again['counters']=={'checkpoint_reused':2,'complete_report_reused':1}
    assert first['common_population_evaluation']==again['common_population_evaluation']
    assert checkpoint.read_bytes()==original
    assert sources=={str(p.relative_to(root)):byte_generation(p) for p in root.rglob('*') if p.is_file()}


def test_independent_handoff_recomputes_pair_metrics_not_just_tree_bytes(tmp_path):
    from src.engine.automation.main_trailing_research_handoff import verify_report
    root,out=sharded(tmp_path)
    owner.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False)
    path=out/'research_2026-10-08.json'
    report,_=verify_report(path,target_date='2026-10-12')
    report.pop('artifact_sha256')
    report['common_population_evaluation']['strata']['actual_completed']['metrics']['incumbent']['train']['paired_ev_pct']=999
    write(path,report)
    with pytest.raises(ValueError,match='pair_metrics_invalid'):
        verify_report(path,target_date='2026-10-12')


def minimal(n=12):
    aliases={'incumbent':'a'*64,'candidate':'b'*64}
    context={};outcomes={}
    for i in range(n):
        clock=1780000000+i*86400
        identity=f'cf:{i:08d}'
        context[identity]={'evidence_kind':'enter_pass_opportunity_cf','entry_at':clock,'observation_end_at':clock+10,
            'buy_basis_krw':'100000','completion_at':None,'entry_context':None,'situation_pin':None,'operating_ai_required':False}
        outcomes[identity]={sha:{'status':'modeled','modeled_net_pnl_krw':100+delta,'actual_pnl_krw':None,
            'slippage_net_pnl_krw':[100+delta,70+delta,0+delta]} for sha,delta in [('a'*64,0),('b'*64,i)]}
    return {'candidate_aliases':aliases,'population_context':context,'minimal_results':outcomes,'common_ids':list(context)}


def test_external_metrics_equal_whole_reference_and_late_conflict(tmp_path):
    full=minimal();reference=common_evaluation([full])
    def shards():
        for i in range(0,12,3):
            ids=list(full['population_context'])[i:i+3]
            yield {**full,'population_context':{j:full['population_context'][j] for j in ids},
                'minimal_results':{j:full['minimal_results'][j] for j in ids},'common_ids':ids}
    evaluated=aggregate(shards,output_root=tmp_path)
    cohort=evaluated['strata']['enter_pass_opportunity_cf'];old=reference['strata']['enter_pass_opportunity_cf']
    for split in ('train','holdout'):
        assert list(storage.iter_tree(tmp_path,cohort[split+'_ids_ref']))==old[split+'_ids']
        for name in ('incumbent','candidate'):
            for key,value in old['metrics'][name][split].items():
                if key in {'worsened_ids','paired_ids','large_loss_worsened_ids'}:
                    assert list(storage.iter_tree(tmp_path,cohort['metrics'][name][split][key+'_ref']))==value
                else: assert cohort['metrics'][name][split][key]==value
    conflict=json.loads(json.dumps(full));identity=next(iter(conflict['population_context']))
    conflict['minimal_results'][identity]['b'*64]['modeled_net_pnl_krw']+=1
    result=aggregate(lambda:iter([full,conflict]),output_root=tmp_path/'conflict')
    assert result['conflicts_ref']['count']==1 and result['population_ids_ref']['count']==11


@pytest.mark.parametrize('evidence', [
    'actual_completed', 'actual_entry_alternative_exit', 'enter_pass_opportunity_cf'])
@pytest.mark.parametrize('one_day', [False, True])
def test_external_training_cost_cutoff_preserves_census_and_reference_parity(tmp_path,evidence,one_day):
    full=minimal(10);identities=list(full['population_context'])
    start=full['population_context'][identities[0]]['entry_at']
    step=10 if one_day else 86400
    cutoff=start+7*step
    known=[None,cutoff+1,str(cutoff),True,cutoff-1,cutoff,cutoff-2,None,None,None]
    for index,identity in enumerate(identities):
        context=full['population_context'][identity]
        clock=start+index*step
        context.update(evidence_kind=evidence,entry_at=clock,observation_end_at=clock+2,
                       completion_at=clock+2,actual_cost_available_at=known[index])
        for outcome in full['minimal_results'][identity].values(): outcome['actual_pnl_krw']=50
    full['population_context'][identities[0]].pop('actual_cost_available_at')
    if not one_day:
        # One row lacks both cost and path timing, another only path timing.
        for index in (1,6): full['population_context'][identities[index]]['observation_end_at']=cutoff
    def shards():
        for start in range(0,len(identities),3):
            selected=identities[start:start+3]
            yield {**full,'population_context':{i:full['population_context'][i] for i in selected},
                   'minimal_results':{i:full['minimal_results'][i] for i in selected},'common_ids':selected}
    resident=common_evaluation([full]);streamed=common_evaluation(shards)
    assert streamed==resident
    actual=aggregate(shards,output_root=tmp_path)
    assert list(storage.iter_tree(tmp_path,actual['common_ids_ref']))==identities
    assert list(storage.iter_tree(tmp_path,actual['population_ids_ref']))==identities
    assert actual['conflicts_ref']['count']==0
    for kind,reference in resident['strata'].items():
        external=actual['strata'][kind]
        for field in ('common_ids','train_ids','holdout_ids','purged_ids','cost_unavailable_train_ids'):
            assert list(storage.iter_tree(tmp_path,external[field+'_ref']))==reference[field]
        for name in full['candidate_aliases']:
            for split in ('train','holdout'):
                metrics=dict(external['metrics'][name][split])
                for field in ('worsened_ids','paired_ids','large_loss_worsened_ids'):
                    metrics[field]=list(storage.iter_tree(tmp_path,metrics.pop(field+'_ref')))
                assert metrics==reference['metrics'][name][split]
    cohort=resident['strata'][evidence]
    expected_cost=([identities[i] for i in (0,2,3,7,8,9)] if one_day
                   else identities[:4]) if evidence=='actual_completed' else []
    assert cohort['cost_unavailable_train_ids']==expected_cost
    assert cohort['holdout_ids']==([] if one_day else identities[7:])
    assert len(cohort['train_ids'])+len(cohort['holdout_ids'])+len(cohort['purged_ids'])==len(identities)
    if evidence=='actual_completed':
        assert identities[5] in cohort['train_ids']  # Cost known exactly at cutoff is usable.
        assert (identities[1] in cohort['train_ids'])==one_day


def test_population_above_single_object_limit_stays_global(tmp_path):
    def shards():
        for offset in range(0,20001,100):
            rows=minimal(min(100,20001-offset))
            rows['population_context']={f'{offset}:{i}':v for i,v in rows['population_context'].items()}
            rows['minimal_results']={f'{offset}:{i}':v for i,v in rows['minimal_results'].items()}
            rows['common_ids']=list(rows['population_context'])
            yield rows
    result=aggregate(shards,output_root=tmp_path)
    assert result['common_ids_ref']['count']==20001
    assert result['population_ids_ref']['count']==20001
    assert len(storage.encoded(result))<4*1024*1024


def test_registered_grid_external_train_winner_and_holdout_equal_reference(tmp_path):
    from src.engine.automation.main_trailing_situation_aggregation import research as grid_research
    from src.engine.scalping import trailing_situation_policy as typed
    from src.engine.scalping.trailing_mechanical_policy import market_values_hash
    from src.engine.scalping.trailing_mechanical_strength import CONFIG_DEFAULTS
    from src.tests.test_main_all_scope_trailing import vector,at
    from copy import deepcopy
    parent=vector();a,b=deepcopy(parent),deepcopy(parent)
    a['REGULAR']['SCALP_TRAILING_LIMIT_WEAK']=.1;b['REGULAR']['SCALP_TRAILING_LIMIT_WEAK']=.2
    cfg={m:dict(CONFIG_DEFAULTS) for m in typed.START_MARKETS}
    aliases={name:market_values_hash(v,cfg) for name,v in [('incumbent',parent),('a',a),('b',b)]}
    contexts={};outcomes={};start=at('2026-09-29T09:00:00')
    for day in range(10):
        for seq in range(6):
            identity=f'{day}:{seq}';clock=start+day*86400+seq*10
            features=dict(range_pct=1,return_pct=.1,trend_efficiency=.2,vwap_distance_pct=-1,spread_pct=.1,rebound_pct=.1)
            source=dict(status='ready',known_at=clock-1,window_bars=2,source_sha256='a'*64,
                features=features,feature_sha256=digest(features))
            contexts[identity]=dict(entry_at=clock,observation_end_at=clock+2,completion_at=clock+2,
                evidence_kind='actual_completed',
                actual_cost_available_at=start+7*86400+1 if day==0 else clock+2,
                buy_basis_krw=1000,entry_context=source)
            # These six late-cost outcomes would incorrectly select b if
            # situation fitting bypassed the common training membership.
            deltas={'incumbent':0,'a':5 if day<7 else -2,'b':50 if day==0 else 4 if day<7 else 8}
            outcomes[identity]={aliases[name]:dict(modeled_net_pnl_krw=v,actual_pnl_krw=0,slippage_net_pnl_krw=[v,v,v]) for name,v in deltas.items()}
    part=dict(candidate_aliases=aliases,population_context=contexts,minimal_results=outcomes,common_ids=sorted(contexts))
    hypotheses=[]
    for width in (.5,2):
        h=dict(schema=typed.CLASSIFIER_SCHEMA,window_bars=2,trained_through=0,thresholds=dict(range_min=width,
            spread_min=.5,trend_return_min=.2,trend_efficiency_min=.5,vwap_min=0,rebound_min=.5))
        h['classifier_sha256']=digest(h);hypotheses.append(h)
    args=dict(grid=hypotheses,candidates={'a':a,'b':b},parent_values=parent,parent_classifier_parameters=cfg)
    old=typed.research_registered_grid([part],evaluation=common_evaluation([part]),**args)
    evaluated=aggregate(lambda:iter([part]),output_root=tmp_path)
    assert evaluated['strata']['actual_completed']['train_ids_ref']['count']==36
    assert evaluated['strata']['actual_completed']['cost_unavailable_train_ids_ref']['count']==6
    new=grid_research(lambda:iter([part]),evaluation=evaluated,output_root=tmp_path,**args)
    assert new['classifier']==old['classifier']
    assert new['train_grid_scores']==old['train_grid_scores']
    selected={cell['train_selected_candidate'] for cell in new['cells'].values()}
    assert 'a' in selected and 'b' not in selected
    for key,cell in old['cells'].items():
        current=new['cells'][key]
        assert current['train_selected_candidate']==cell['train_selected_candidate']
        assert current['disposition']==cell['disposition']
        for split in ('train','holdout'):
            expanded=dict(current[split])
            for field in ('worsened_ids','paired_ids','large_loss_worsened_ids'):
                expanded[field]=list(storage.iter_tree(tmp_path,expanded.pop(field+'_ref')))
            assert expanded==cell[split]


def test_cache_overflow_classifies_once_for_all_candidates_and_preserves_add(tmp_path,monkeypatch):
    from copy import deepcopy
    from src.engine.automation import main_trailing_path_projection as projection
    from src.engine.scalping import universal_trailing_replay as kernel
    from src.tests.test_main_all_scope_trailing import position,quote,vector
    events=[quote(1,'2026-10-08T09:00:01'),quote(2,'2026-10-08T09:00:02',bid=100.2)]
    calls=[];original=projection.classify_ws_history
    def classify(*args,**kwargs):
        calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(projection,'classify_ws_history',classify)
    quota={'used':research.CACHE_BYTES,'limit':research.CACHE_BYTES}
    prepared=research._prepared(lambda:iter(events),None,count=len(events),end=events[-1]['known_at'],
        last_add=0,cache_root=tmp_path,quota=quota,counters={
            'feature_cache_large_path_streamed':0})
    candidates={}
    for i in range(12):
        v=deepcopy(vector());v['REGULAR']['SCALP_TRAILING_LIMIT_WEAK']=.05+i*.01;candidates[str(i)]=v
    actual=kernel.summarize_partitions([position()],{'main:1':kernel.PreparedVariants({
        kernel.classifier_hash(None):prepared})},candidates,incumbent=vector())
    assert len(calls)<=len(events)
    expected=kernel.summarize_partitions([position()],{'main:1':events},candidates,incumbent=vector())
    assert actual['minimal_results']==expected['minimal_results']
    calls.clear()
    add={'kind':'ADD','known_at':events[-1]['known_at']+1}
    guarded=research._prepared(lambda:iter([*events,add]),None,count=3,end=add['known_at'],
        last_add=add['known_at'],cache_root=tmp_path,quota=quota,counters={
            'feature_cache_large_path_streamed':0})
    result=kernel.replay(position(),guarded,vector())
    assert result['reason']=='candidate_exit_changes_observed_add_path'
    assert len(calls)==1


def test_large_feature_observations_are_lossless_and_classified_once(tmp_path,monkeypatch):
    from collections import Counter
    from dataclasses import asdict
    from src.engine.scalping.trailing_mechanical_strength import StrengthDecision
    event={'kind':'QUOTE','known_at':1,'source_sha256':'a'*64}
    observations=[{'sequence':i,'trade_receipts':[{'qty':i,'source':'x'*2400}]} for i in range(32)]
    strength=StrengthDecision(state='STRONG',reason='strong_retained',
        **{key:None for key in StrengthDecision.__dataclass_fields__ if key not in {'state','reason','new_observations'}},
        new_observations=tuple(observations))
    feature=['REGULAR',None,asdict(strength)];calls=[]
    assert len(storage.encoded([event,feature]))>storage.RECORD_BYTES
    def pairs(events,config):
        calls.append(1)
        for row in events:yield row,feature
    monkeypatch.setattr(research,'stream_pairs',pairs)
    counters=Counter();quota={'used':0,'limit':research.CACHE_BYTES}
    prepared=research._prepared(lambda:iter([event]),None,count=1,end=1,last_add=0,
        cache_root=tmp_path,quota=quota,counters=counters)
    for _ in range(2):
        row,(_,_,actual)=next(prepared.pairs())
        assert row==event and asdict(actual)==asdict(strength)
    assert calls==[1] and counters['feature_cache_created']==1
    for path in tmp_path.rglob('*.json'):
        body=json.loads(path.read_bytes())
        assert all(len(storage.encoded(row))<=storage.RECORD_BYTES for row in body.get('rows',[]))


def test_partitioned_feature_cache_rejects_changed_observation_shard(tmp_path,monkeypatch):
    event={'kind':'QUOTE','known_at':1}
    feature=['REGULAR',None,{'state':'STRONG','new_observations':[{'sequence':i,'source':'x'*2400} for i in range(32)]}]
    monkeypatch.setattr(research,'stream_pairs',lambda events,config:((row,feature) for row in events))
    ref=storage.write_tree(tmp_path,research._cache_pairs(lambda:iter([event]),None,tmp_path,
        {'used':0,'limit':research.CACHE_BYTES}),inline=False)
    _,cached=next(storage.iter_tree(tmp_path,ref))
    child=cached[2]['new_observations_ref'];path=storage.safe_path(tmp_path,child['path'])
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='generation'):
        list(research._cached_pairs(tmp_path,ref))


def test_single_oversized_observation_uses_existing_stream_without_truncation(tmp_path,monkeypatch):
    from collections import Counter
    from dataclasses import asdict
    from src.engine.scalping.trailing_mechanical_strength import StrengthDecision
    event={'kind':'QUOTE','known_at':1}
    strength=StrengthDecision(state='STRONG',reason='strong_retained',
        **{key:None for key in StrengthDecision.__dataclass_fields__ if key not in {'state','reason','new_observations'}},
        new_observations=({'source':'x'*storage.RECORD_BYTES},))
    feature=['REGULAR',None,asdict(strength)]
    monkeypatch.setattr(research,'stream_pairs',lambda events,config:((row,feature) for row in events))
    counters=Counter()
    prepared=research._prepared(lambda:iter([event]),None,count=1,end=1,last_add=0,
        cache_root=tmp_path,quota={'used':0,'limit':research.CACHE_BYTES},counters=counters)
    assert asdict(next(prepared.pairs())[1][2])==asdict(strength)
    assert counters['feature_cache_overflow_streamed']==1


def test_streaming_duplicate_across_closed_gap_matches_resident(tmp_path,monkeypatch):
    from src.engine.scalping import universal_trailing_replay as kernel
    from src.tests.test_main_all_scope_trailing import position,quote,vector
    # Freeze only the gap predicate, retaining clock, source, route, and quote
    # validation. Reuse across an allowed gap must still be rejected globally.
    events=[quote(1,'2026-10-08T09:00:01',bid=100,peak=100),
            quote(1,'2026-10-08T09:00:05',bid=100,peak=100)]
    monkeypatch.setattr(kernel,'closed_exit_gap',lambda *args:True)
    prepared=research._prepared(lambda:iter(events),None,count=2,end=events[-1]['known_at'],last_add=0,
        cache_root=tmp_path,quota={'used':research.CACHE_BYTES,'limit':research.CACHE_BYTES},
        counters={'feature_cache_large_path_streamed':0})
    actual=kernel.replay(position(),prepared,vector())
    expected=kernel.replay(position(),events,vector())
    assert actual==expected and actual['reason']=='source_identity_duplicate'


def test_path_above_one_hundred_thousand_events_streams_once_without_cache(tmp_path,monkeypatch):
    from copy import deepcopy
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.automation import main_trailing_path_projection as projection
    from src.engine.scalping import universal_trailing_replay as kernel
    from src.engine.lifecycle.research_input_budget import health
    from src.tests.test_main_all_scope_trailing import position,quote,vector
    p=position();n=100001;decoded=[0];classified=[0]
    original=projection.classify_ws_history
    def classify(*args,**kwargs):classified[0]+=1;return original(*args,**kwargs)
    monkeypatch.setattr(projection,'classify_ws_history',classify)
    def events():
        for i in range(n):
            clock=datetime.fromtimestamp(p['entry_at']+(i+1)*.0005,ZoneInfo('Asia/Seoul')).replace(tzinfo=None).isoformat()
            decoded[0]+=1;yield quote(i+1,clock,bid=100,peak=100)
    before=health()['used_bytes']
    prepared=research._prepared(events,None,count=n,end=p['entry_at']+n*.0005,last_add=0,cache_root=tmp_path,
        quota={'used':research.CACHE_BYTES,'limit':research.CACHE_BYTES},
        counters={'feature_cache_large_path_streamed':0})
    candidates={}
    for i in range(2):
        values=deepcopy(vector());values['REGULAR']['SCALP_TRAILING_START_PCT']=.5+i*.1;candidates[str(i)]=values
    result=kernel.summarize_partitions([p],{'main:1':kernel.PreparedVariants({kernel.classifier_hash(None):prepared})},
        candidates,incumbent=vector())
    assert decoded[0]==classified[0]==n
    assert all(r['reason']=='trailing_crossing_not_observed' for r in result['minimal_results']['main:1'].values())
    assert health()['used_bytes']==before
    assert not list(tmp_path.rglob('*.json'))


def test_typed_global_training_evidence_reaches_existing_selector_without_holdout_reselection(tmp_path,monkeypatch):
    from copy import deepcopy
    from src.engine.scalping import trailing_situation_policy as typed
    from src.engine.scalping.trailing_mechanical_policy import market_values_hash,baseline_receipt
    from src.engine.automation.main_trailing_situation_aggregation import research as tune
    from src.engine.automation import main_trailing_research_handoff as handoff
    from src.engine.automation.scalp_trailing_mechanical_policy_apply import select_typed_bundle,verify_type_view,_type_view
    from src.tests.test_main_all_scope_trailing import at
    parent=baseline_receipt({},source='operator_directed_m1_baseline');a=deepcopy(parent['market_values'])
    a['REGULAR']['SCALP_TRAILING_LIMIT_WEAK']=.1
    cfg=parent['classifier_parameters'];aliases={n:market_values_hash(v,cfg) for n,v in [('incumbent',parent['market_values']),('a',a)]}
    contexts={};results={};start=at('2026-09-29T09:00:00');days=[]
    for day in range(10):
        days.append(__import__('datetime').datetime.fromtimestamp(start+day*86400,__import__('zoneinfo').ZoneInfo('Asia/Seoul')).date().isoformat())
        for seq in range(6):
            identity=f'{day}:{seq}';clock=start+day*86400+seq*10
            features=dict(range_pct=1,return_pct=.1,trend_efficiency=.2,vwap_distance_pct=-1,spread_pct=.1,rebound_pct=.1)
            ctx=dict(status='ready',known_at=clock-1,window_bars=2,source_sha256='a'*64,features=features,feature_sha256=digest(features))
            contexts[identity]=dict(entry_at=clock,observation_end_at=clock+2,completion_at=clock+2,evidence_kind='actual_completed',
                actual_cost_available_at=clock+2,buy_basis_krw=1000,entry_context=ctx,operating_ai_required=False)
            results[identity]={aliases[n]:dict(modeled_net_pnl_krw=d,actual_pnl_krw=0,slippage_net_pnl_krw=[d,d,d]) for n,d in [('incumbent',0),('a',5)]}
    part=dict(candidate_aliases=aliases,population_context=contexts,minimal_results=results,common_ids=sorted(contexts))
    h=dict(schema=typed.CLASSIFIER_SCHEMA,window_bars=2,trained_through=0,thresholds=dict(range_min=.5,
        spread_min=.5,trend_return_min=.2,trend_efficiency_min=.5,vwap_min=0,rebound_min=.5));h['classifier_sha256']=digest(h)
    evaluation=aggregate(lambda:iter([part]),output_root=tmp_path/'stats')
    grid=tune(lambda:iter([part]),evaluation=evaluation,output_root=tmp_path/'stats',grid=[h],candidates={'a':a},
        parent_values=parent['market_values'],parent_classifier_parameters=cfg)
    from src.utils import constants
    monkeypatch.setattr(constants,'DATA_DIR',tmp_path/'source')
    manifest=tmp_path/'manifest.json';write(manifest,dict(source_data_root=str(tmp_path/'source'),consumed_dates=days,
        approved_parent_receipt=parent,candidates={'a':{'market_values':a,'classifier_parameters':cfg}}))
    report=dict(source_date='2026-10-08',target_date='2026-10-12',status='complete',input_manifest_path=str(manifest),
        evidence_root=str(tmp_path/'stats'),trailing_situation_research=grid)
    # This unit isolates the existing economic selector from the separate
    # full report byte/source verifier, which has its own corruption tests.
    generation={'path':'research.json','sha256':'a'*64,'size':1}
    monkeypatch.setattr(handoff,'verify_report',lambda *args,**kwargs:(report,generation))
    bundle=select_typed_bundle(tmp_path/'source',report,generation,report_path=tmp_path/'research.json',target_date='2026-10-12')
    assert bundle['cells']['REGULAR|HIGH_VARIABILITY']['disposition']=='qualified_candidate'
    assert all(v['disposition']=='parent_carry' for k,v in bundle['cells'].items() if k!='REGULAR|HIGH_VARIABILITY')
    view=_type_view(report,generation,report_path=tmp_path/'research.json',market='REGULAR',kind='HIGH_VARIABILITY')
    forged=deepcopy(view);forged['trailing_mechanical_market_tuning']['research_candidate']['values']['REGULAR']['SCALP_TRAILING_LIMIT_WEAK']=.05
    with pytest.raises(ValueError,match='selector_source_changed'):verify_type_view(forged,target_date='2026-10-12')
    assert _type_view(report,generation,report_path=tmp_path/'research.json',market='AFTER',kind='HIGH_VARIABILITY') is None


def test_required_postclose_trailing_extension_cannot_be_missing():
    from src.engine.automation.main_trailing_research_handoff import observe_extension
    optional = observe_extension({'date': '2026-10-16'}, target_date='2026-10-19')
    assert optional['status'] == 'not_observed' and optional['findings'] == []
    required = observe_extension({'date': '2026-10-16'}, target_date='2026-10-19', required=True)
    assert required['status'] == 'source_invalid'
    assert required['findings'] == ['all_scope_research_extension_missing']
    assert required['full_source_revalidation_performed'] is False
