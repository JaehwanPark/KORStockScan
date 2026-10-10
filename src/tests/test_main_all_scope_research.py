"""Partition resume, past-date influence and read-only research orchestration."""
import json
import hashlib
from pathlib import Path
import pytest
from src.engine.automation import main_trailing_all_scope_research as research
from src.engine.lifecycle.holding_window_generation import capture_window
from src.engine.lifecycle.broker_cost_reconciliation import receipt_path
from src.engine.lifecycle.research_input_budget import Claim, LIMIT_BYTES, health
from src.engine.scalping.trailing_mechanical_policy import baseline_receipt
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.tests.test_main_all_scope_trailing import position, quote


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {**value, 'artifact_sha256':digest(value)}
    path.write_text(json.dumps(value))
    return digest(value)


def fixture(tmp_path):
    root, output = tmp_path/'source', tmp_path/'result'
    root.mkdir()
    dates=['2026-10-07','2026-10-08']
    window=capture_window(root, dates)
    parts=[]
    for n,day in enumerate(dates):
        p={**position(), 'position_key':f'main:{n}', 'symbol':'123456'}
        p['actual_cost_reconciliation'] = {**p['actual_cost_reconciliation'], 'known_at':position()['entry_at']+1}
        if day == '2026-10-07':
            p['entry_at'] -= 86400
        payload=dict(source_date='2026-10-08', positions=[p], paths={p['position_key']:[quote(1,day+'T09:00:01')]},
                     cost_generations={day:window['dependencies'][day]['cost_generation']})
        name=f'part-{n}.json'
        sha=write(root/name,payload)
        parts.append({'path':name,'artifact_sha256':sha,'consumed_dates':[day]})
    manifest=dict(schema=research.INPUT_SCHEMA, source_date='2026-10-08',target_date='2026-10-12',
        universe=[{'code':'123456','known_at':1,'tradable':True}],as_of=position()['entry_at']+2,
        universe_source_sha256='a'*64, approved_parent_receipt=baseline_receipt({},source='operator_directed_m1_baseline'),
        consumed_dates=dates, population_ids=['main:0','main:1'],partitions=parts)
    from src.engine.automation.runtime_policy_bootstrap import _digest_json
    parent={'target_date':'2026-10-08','scalp_trailing_mechanical_policy_receipt':manifest['approved_parent_receipt']}
    parent['manifest_sha256']=_digest_json(parent)
    parent_path=root/'parent.json';parent_path.write_text(json.dumps(parent))
    manifest['approved_parent_source']={'path':'parent.json','sha256':hashlib.sha256(parent_path.read_bytes()).hexdigest()}
    write(root/'manifest.json',manifest)
    return root,output


def test_default_preflight_and_dry_run_never_write_source_or_output(tmp_path):
    root,output=fixture(tmp_path)
    before={p.name:p.read_bytes() for p in root.iterdir()}
    result=research.run(root/'manifest.json',input_root=root)
    assert result['status']=='preflight_only' and not output.exists()
    result=research.run(root/'manifest.json',input_root=root,output_root=output)
    assert result['status']=='complete' and len(result['population_ids'])==2
    assert not output.exists()
    assert before=={p.name:p.read_bytes() for p in root.iterdir()}
    with pytest.raises(ValueError,match='isolated_output'):
        research.run(root/'manifest.json',input_root=root,output_root=root/'result')


def test_checkpoint_resume_cost_only_revision_reuses_source_and_matches_clean_recompute(tmp_path, monkeypatch):
    root,output=fixture(tmp_path)
    first=research.run(root/'manifest.json',input_root=root,output_root=output,dry_run=False)
    assert first['counters']['decoded_partitions']==2
    again=research.run(root/'manifest.json',input_root=root,output_root=output,dry_run=False,resume=True)
    assert again['counters']=={'checkpoint_reused':2}
    path=receipt_path(root,'2026-10-07','1');path.parent.mkdir(parents=True);path.write_text('{"revision":1}')
    sealed = research._sealed
    def no_source_decode(path, *args, **kwargs):
        assert not Path(path).name.startswith('part-')
        return sealed(path, *args, **kwargs)
    monkeypatch.setattr(research, '_sealed', no_source_decode)
    revised=research.run(root/'manifest.json',input_root=root,output_root=output,dry_run=False,resume=True)
    assert revised['counters']=={'cost_only_source_reused':1,'checkpoint_reused':1}
    assert revised['input_window_generation_sha256']!=first['input_window_generation_sha256']
    assert len(revised['common_population_evaluation']['common_ids'])==1
    assert first['initial_policy']==revised['initial_policy']
    assert len(list((output/'partitions').glob('*.json')))==3
    monkeypatch.setattr(research, '_sealed', sealed)
    clean=research.run(root/'manifest.json', input_root=root, output_root=tmp_path/'clean', dry_run=False)
    assert revised['common_population_evaluation'] == clean['common_population_evaluation']
    assert [sealed(Path(p['path']))['result'] for p in revised['partition_results']] == [
        sealed(Path(p['path']))['result'] for p in clean['partition_results']]


def test_shared_budget_is_one_allowance_across_families_and_overflow_is_explicit():
    initial=health()['used_bytes']
    with Claim(LIMIT_BYTES-initial-1024):
        with pytest.raises(ValueError,match='partition_resume_required'):
            Claim(2048)
        with Claim(1024):
            assert health()['used_bytes']==LIMIT_BYTES
    assert health()['used_bytes']==initial


def test_scope_admission_happens_before_population_expansion(tmp_path, monkeypatch):
    root, output = fixture(tmp_path)
    from src.engine.lifecycle import research_input_budget
    monkeypatch.setattr(research_input_budget, 'LIMIT_BYTES', 1024)
    monkeypatch.setattr(research, 'build_scope', lambda *a, **kw: pytest.fail('scope allocated before admission'))
    with Claim(0) as budget:
        with pytest.raises(ValueError, match='partition_resume_required'):
            research.preflight(root/'manifest.json', root, scope_budget=budget)
    assert health()['used_bytes'] == 0


def test_damaged_checkpoint_rebuilds_only_its_sealed_source_partition(tmp_path):
    root, output = fixture(tmp_path)
    clean = research.run(root/'manifest.json', input_root=root, output_root=output, dry_run=False)
    checkpoint = Path(clean['partition_results'][0]['path'])
    checkpoint.write_text('{"partial_write":')
    recovered = research.run(root/'manifest.json', input_root=root, output_root=output,
                             dry_run=False, resume=True)
    assert recovered['counters'] == {'checkpoint_invalid_rebuilt': 1,
                                    'source_feature_projection_reused': 1, 'checkpoint_reused': 1}
    assert recovered['common_population_evaluation'] == clean['common_population_evaluation']
    assert recovered['initial_policy'] == clean['initial_policy']


def test_output_partition_link_cannot_write_back_into_input(tmp_path):
    root, output = fixture(tmp_path)
    output.mkdir()
    (output/'partitions').symlink_to(root, target_is_directory=True)
    before = {path.name:path.read_bytes() for path in root.iterdir()}
    with pytest.raises(ValueError, match='artifact_path'):
        research.run(root/'manifest.json', input_root=root, output_root=output, dry_run=False)
    assert before == {path.name:path.read_bytes() for path in root.iterdir()}


def test_cost_revision_during_final_aggregation_cannot_publish_old_generation(tmp_path,monkeypatch):
    root,output = fixture(tmp_path)
    original = research.common_evaluation
    def changed_during_aggregation(parts):
        result = original(parts)
        path=receipt_path(root,'2026-10-07','1')
        path.parent.mkdir(parents=True)
        path.write_text('{"revision":1}')
        return result
    monkeypatch.setattr(research,'common_evaluation',changed_during_aggregation)
    with pytest.raises(ValueError,match='window.*changed'):
        research.run(root/'manifest.json',input_root=root,output_root=output,dry_run=False)
    assert not (output/'research_2026-10-08.json').exists()
    assert not (output/'initial_policy_2026-10-12.json').exists()


def test_code_generation_change_cannot_publish_old_report(tmp_path,monkeypatch):
    root,output=fixture(tmp_path)
    values=iter(['a'*64,'b'*64])
    monkeypatch.setattr(research,'code_contract',lambda:next(values))
    with pytest.raises(ValueError,match='code_changed'):
        research.run(root/'manifest.json',input_root=root,output_root=output,dry_run=False)
    assert not (output/'research_2026-10-08.json').exists()


def test_cutoff_change_does_not_reuse_future_exit_or_cost_checkpoint(tmp_path):
    root, output = fixture(tmp_path)
    original = research.run(root/'manifest.json', input_root=root, output_root=output, dry_run=False)
    assert len(original['common_population_evaluation']['common_ids']) == 2
    manifest = json.loads((root/'manifest.json').read_text())
    manifest['as_of'] = position()['entry_at'] + .5
    manifest.pop('artifact_sha256'); write(root/'manifest.json', manifest)
    earlier = research.run(root/'manifest.json', input_root=root, output_root=output, dry_run=False, resume=True)
    assert earlier['counters'].get('decoded_partitions') == 2
    assert earlier['counters']['as_of_future_events_excluded'] == 1
    assert earlier['common_population_evaluation']['common_ids'] == []
    assert earlier['population_ids'] == original['population_ids']


def test_streamed_checkpoints_equal_resident_comparison_and_release_budget(tmp_path):
    root,output=fixture(tmp_path)
    before=health()['used_bytes']
    resident=research.run(root/'manifest.json',input_root=root,output_root=output)
    streamed=research.run(root/'manifest.json',input_root=root,output_root=output,dry_run=False)
    assert resident['common_population_evaluation']==streamed['common_population_evaluation']
    assert all('result_bytes' in part and 'minimal_results' not in part for part in streamed['partition_results'])
    assert health()['used_bytes']==before
    manifest=json.loads((root/'manifest.json').read_text())
    manifest['universe'] += [{'code':str(200000+n),'known_at':1,'tradable':True} for n in range(600)]
    manifest.pop('artifact_sha256');write(root/'manifest.json',manifest)
    large=research.run(root/'manifest.json',input_root=root,output_root=output,dry_run=False,resume=True)
    assert large['scope']['scope_count']==601*8
    assert 'scopes' not in large['scope']
    assert sum(p['count'] for p in large['scope']['partitions'])==601*8
    assert health()['used_bytes']==before
