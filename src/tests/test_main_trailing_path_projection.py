"""Source-preserving candidate changes, dense segmented paths and corruption."""
import json
from pathlib import Path
import pytest

from src.engine.automation import main_trailing_all_scope_research as research
from src.engine.automation import main_trailing_path_projection as projection
from src.engine.lifecycle.research_input_budget import health
from src.engine.scalping import universal_trailing_replay as replay
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.engine.scalping.trailing_mechanical_policy import classifier_hash
from src.tests.test_main_all_scope_research import fixture, write
from src.tests.test_main_all_scope_trailing import quote, position, vector, at


def test_numeric_candidate_change_reuses_source_and_features_and_equals_clean(tmp_path,monkeypatch):
    root,out=fixture(tmp_path)
    research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False)
    manifest=json.loads((root/'manifest.json').read_text());manifest.pop('artifact_sha256')
    candidate=vector();candidate['REGULAR']['SCALP_TRAILING_START_PCT']=.5
    manifest['candidates']={'new':candidate};write(root/'manifest.json',manifest)
    original_read=projection.read_sealed
    def cache_only(path,*args,**kwargs):
        assert not Path(path).name.startswith('part-')
        return original_read(path,*args,**kwargs)
    monkeypatch.setattr(projection,'read_sealed',cache_only)
    changed=research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False,resume=True)
    assert changed['counters']=={'source_feature_projection_reused':2}
    monkeypatch.setattr(projection,'read_sealed',original_read)
    clean=research.run(root/'manifest.json',input_root=root,output_root=tmp_path/'clean',dry_run=False)
    assert changed['common_population_evaluation']==clean['common_population_evaluation']
    assert changed['initial_policy']==clean['initial_policy']


@pytest.mark.parametrize('event_count',[200,4000])
def test_dense_segmented_path_preserves_m1_state_and_candidate_outcomes(tmp_path,monkeypatch,event_count):
    root,out=fixture(tmp_path)
    # Keep a live path below crossing until its last quote. The original
    # sealed manifest references the whole event census, never a tail slice.
    events=[]
    for n in range(event_count):
        e=quote(n+1,'2026-10-08T09:00:01',bid=100,peak=100)
        e['known_at']=e['event_at']=position()['entry_at']+(n+1)*.001
        ws=e['ws_data'];depth=ws['recent_depth_ticks_by_route']['KRX|KRX'][0]
        depth['received_at_ms']=int(e['known_at']*1000)
        e['sell_execution_plan']['valid_until']=e['known_at']+.7
        from src.tests.test_main_all_scope_trailing import reseal
        reseal(e);events.append(e)
    events[-1]=quote(event_count,'2026-10-08T09:00:04' if event_count==4000 else '2026-10-08T09:00:01')
    if event_count==4000:
        assert len(json.dumps(events).encode())>4*1024*1024
    refs=[]
    for offset in range(0,len(events),17):
        name=f'seg-{offset}.json'
        sha=write(root/name,dict(source_date='2026-10-08',events=events[offset:offset+17]))
        refs.append({'path':name,'artifact_sha256':json.loads((root/name).read_text())['artifact_sha256']})
    manifest=json.loads((root/'manifest.json').read_text());manifest.pop('artifact_sha256')
    p=position();p.update(position_key='dense',symbol='123456')
    p['actual_cost_reconciliation']={**p['actual_cost_reconciliation'],'known_at':p['entry_at']+1}
    original=json.loads((root/'part-1.json').read_text())
    payload=dict(source_date='2026-10-08',positions=[p],paths={'dense':{'segments':refs,'event_count':event_count}},
        cost_generations=original['cost_generations'])
    sha=write(root/'dense.json',payload)
    manifest['partitions']=[dict(path='dense.json',artifact_sha256=sha,consumed_dates=['2026-10-08'])]
    manifest['population_ids']=['dense'];manifest['as_of']=p['entry_at']+5;write(root/'manifest.json',manifest)
    monkeypatch.setattr(projection,'PIECE_BYTES',16*1024)
    before=health()['used_bytes']
    streamed=research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False)
    expected=replay.summarize_partitions([p],{'dense':events},{},incumbent={
        'market_values':manifest['approved_parent_receipt']['market_values'],
        'classifier_parameters':manifest['approved_parent_receipt']['classifier_parameters']})
    checkpoint=research._sealed(Path(streamed['partition_results'][0]['path']))
    assert checkpoint['result']==expected
    assert health()['used_bytes']==before
    assert len(list((out/'source_features/pieces').glob('*.json')))>1
    resumed=research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False,resume=True)
    assert resumed['counters']=={'checkpoint_reused':1}
    # The original leaf bytes are still checked, even when outcome is cached.
    leaf=root/refs[0]['path'];leaf.write_text(leaf.read_text()+' ')
    with pytest.raises(ValueError,match='source_changed_after_checkpoint'):
        research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False,resume=True)


def test_corrupt_feature_piece_rebuilds_from_original_and_does_not_trust_hash_only(tmp_path):
    root,out=fixture(tmp_path)
    original=research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False)
    for reference in original['partition_results']:
        Path(reference['path']).unlink()
    leaf=next((out/'source_features/pieces').glob('*.json'));leaf.write_text('{"partial":')
    recovered=research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False,resume=True)
    assert recovered['counters']['source_feature_projection_invalid_rebuilt']==1
    assert recovered['common_population_evaluation']==original['common_population_evaluation']


def test_wrong_segment_count_or_link_cannot_publish(tmp_path):
    root,out=fixture(tmp_path)
    payload=json.loads((root/'part-0.json').read_text());payload.pop('artifact_sha256')
    events=payload['paths']['main:0'];write(root/'segment.json',dict(source_date='2026-10-08',events=events))
    ref={'path':'segment.json','artifact_sha256':json.loads((root/'segment.json').read_text())['artifact_sha256']}
    payload['paths']['main:0']={'segments':[ref],'event_count':len(events)+1}
    sha=write(root/'part-0.json',payload)
    manifest=json.loads((root/'manifest.json').read_text());manifest.pop('artifact_sha256')
    manifest['partitions'][0]['artifact_sha256']=sha;write(root/'manifest.json',manifest)
    before=health()['used_bytes']
    with pytest.raises(ValueError,match='segment_census'):
        research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False)
    assert not (out/'research_2026-10-08.json').exists()
    assert health()['used_bytes']==before


def test_identified_malformed_path_keeps_other_positions_and_census(tmp_path):
    root,out=fixture(tmp_path)
    payload=json.loads((root/'part-0.json').read_text());payload.pop('artifact_sha256')
    payload['paths']['main:0']=[None]
    sha=write(root/'part-0.json',payload)
    manifest=json.loads((root/'manifest.json').read_text());manifest.pop('artifact_sha256')
    manifest['partitions'][0]['artifact_sha256']=sha;write(root/'manifest.json',manifest)
    result=research.run(root/'manifest.json',input_root=root,output_root=out,dry_run=False)
    assert result['counters']['identified_path_invalid']==1
    assert result['population_ids']==['main:0','main:1']
    assert result['common_population_evaluation']['common_ids']==['main:1']
    checkpoint=research._sealed(Path(result['partition_results'][0]['path']))
    assert {r['reason'] for r in checkpoint['result']['minimal_results']['main:0'].values()}=={'identified_event_path_contract_invalid'}
