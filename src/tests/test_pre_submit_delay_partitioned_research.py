"""Whole-population timing split and sharded producer/consumer contracts."""
import json
from pathlib import Path
import pytest
from src.engine.automation import pre_submit_delay_partitioned_research as partitioned
from src.engine.lifecycle import research_storage as storage
from src.engine.scalping import pre_submit_delay_initial_policy as initial
from src.tests.test_pre_submit_delay_initial_policy import build as legacy_build


def fixture(tmp_path, monkeypatch):
    records = [{'date':'2026-10-01' if n<14 else '2026-10-02',
                'prices':{0:10000,30:9900,60:9800,120:9900,180:9900}} for n in range(20)]
    # The source fixture spaces each opportunity by ten minutes.
    report,policy = legacy_build(tmp_path,monkeypatch,records)
    return report,policy


def build(report, output):
    return partitioned.build(report['qualified_projection'],report['census'],output_root=output,
        source_date=report['source_date'],publication_date=report['publication_date'],effective_date=report['effective_date'],
        source_sha256=report['source_sha256'],code_contract_sha256=report['code_contract_sha256'],
        source_receipt=report.get('source_receipt'))


def _machine_chain(root, monkeypatch):
    """Small native-loader fixture; production generation validation is separate."""
    from copy import deepcopy
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    base = root/'runtime/mechanistic_entry_policy'
    (base/'generations').mkdir(parents=True)
    (base/'candidates').mkdir()
    def validate(bundle, *, target_date):
        if (bundle['target_date'] != target_date or bundle['bundle_sha256'] != initial.digest(
                {k:v for k,v in bundle.items() if k!='bundle_sha256'})):
            raise ValueError('machine_bundle_contract_invalid')
    monkeypatch.setattr(native, 'validate', validate)
    old = dict(target_date='2026-10-02', continuous_reversal=dict(schema='continuous_reversal_policy_v6',
        effective_date='2026-10-02', execution_manifest_hash='a'*64,
        contract_file_sha256={'runtime.py':'1'*64, 'session_contract.py':'2'*64,
                             'reversal_code_handoff.py':'3'*64, 'reversal_cumulative_postclose.py':'4'*64},
        machine_cells={'scope':{'routes':{'SOR':{'payload':{'rule':'first_hold'},'backend':'union_v6',
                                              'scope_execution_hash':'5'*64}}}},
        auxiliary_cells={'scope':{'routes':{'SOR':{'payload':{'prompt':'original','model':'same'}}}}},
        operating_manifest={'scopes':{'scope|SOR':['first_hold']},'definitions':{'first_hold':'6'*64}}))
    def write(bundle):
        bundle['bundle_sha256'] = initial.digest({k:v for k,v in bundle.items() if k!='bundle_sha256'})
        path = base/'generations'/(bundle['bundle_sha256']+'.json')
        path.write_text(json.dumps(bundle))
    write(old)
    new = deepcopy(old);new['target_date']='2026-10-05'
    new['continuous_reversal'].update(effective_date='2026-10-05',execution_manifest_hash='c'*64,
                                      parent_bundle_sha256=old['bundle_sha256'])
    new['continuous_reversal']['contract_file_sha256']['reversal_code_handoff.py']='7'*64
    new['continuous_reversal']['contract_file_sha256']['reversal_cumulative_postclose.py']='8'*64
    write(new)
    (base/'candidates/policy_2026-10-05.json').write_text(json.dumps(new))
    return old,new,write


def test_identical_machine_parent_recalculation_reaches_prepared_consumer(tmp_path, monkeypatch):
    from src.engine.automation import pre_submit_delay_situation_projection as recovery
    from src.engine.automation import pre_submit_delay_research_review as review
    original,_ = fixture(tmp_path/'source',monkeypatch)
    _machine_chain(tmp_path/'native',monkeypatch)
    proof = recovery.prepare_machine_compatibility(tmp_path/'native','2026-10-05')
    rows = original['qualified_projection']
    for row in rows:
        row['parent_compatibility']=['a'*64,'b'*64]
        row['native_evaluation_bound']=True
    census={**original['census'],'native_evaluation_unverified_n':0,'parent_compatibility_unverified_n':0}
    kwargs=dict(census=census,source_date='2026-10-02',publication_date='2026-10-02',effective_date='2026-10-05',
                source_sha256='d'*64,code_contract_sha256='e'*64,source_receipt={})
    before,old=partitioned.build(rows,output_root=tmp_path/'before',**kwargs)
    query=dict(target_date='2026-10-05',market='REGULAR',parents=['c'*64,'b'*64])
    assert initial.PreparedPolicy.from_artifacts(old,before,target_date='2026-10-05').lookup(**query)['delay_sec']==0
    after,new=partitioned.build(rows,output_root=tmp_path/'after',machine_compatibility=proof,**kwargs)
    prepared=initial.PreparedPolicy.from_artifacts(new,after,target_date='2026-10-05')
    assert prepared.lookup(**query)['delay_sec']==60
    assert after['qualified_projection_ref']['logical_sha256']==before['qualified_projection_ref']['logical_sha256']
    assert after['census']==before['census']
    for parents in (['c'*64,'f'*64],['f'*64,'b'*64]):
        assert prepared.lookup(**{**query,'parents':parents})['status']=='unsupported_existing_behavior'
    assert prepared.lookup(**{**query,'target_date':'2026-10-06'})['delay_sec']==0
    with storage.index(tmp_path/'review') as db:
        monkeypatch.setattr(review,'_enrich',lambda db,row,receipt:row)
        counts,_=review._populate(db,after.evidence_root,after,{})
        assert counts['anchors']==len(rows)
    # Same checksum-sealed report cannot authorize changed native source bytes.
    path=Path(proof['chain'][1]['path']);path.write_text(path.read_text()+'\n')
    with pytest.raises(ValueError,match='compatibility_binding_invalid'):
        initial.PreparedPolicy.from_artifacts(new,after,target_date='2026-10-05')


@pytest.mark.parametrize('changed', ['runtime','session','new_code','rule','route','auxiliary','membership','definition','unknown'])
def test_changed_machine_semantics_do_not_join_parents(tmp_path,monkeypatch,changed):
    from src.engine.automation import pre_submit_delay_situation_projection as recovery
    _,new,write=_machine_chain(tmp_path,monkeypatch)
    family=new['continuous_reversal']
    if changed in {'runtime','session','new_code'}:
        key={'runtime':'runtime.py','session':'session_contract.py','new_code':'new_runtime.py'}[changed]
        family['contract_file_sha256'][key]='f'*64
    elif changed=='rule':family['machine_cells']['scope']['routes']['SOR']['payload']['rule']='different'
    elif changed=='route':family['machine_cells']['scope']['routes']['NXT']=family['machine_cells']['scope']['routes'].pop('SOR')
    elif changed=='auxiliary':family['auxiliary_cells']['scope']['routes']['SOR']['payload']['prompt']='different'
    elif changed=='membership':family['operating_manifest']['scopes']['scope|SOR'].append('other')
    elif changed=='definition':family['operating_manifest']['definitions']['first_hold']='f'*64
    else:family['new_behavior']='different'
    write(new)
    (tmp_path/'runtime/mechanistic_entry_policy/candidates/policy_2026-10-05.json').write_text(json.dumps(new))
    assert recovery.prepare_machine_compatibility(tmp_path,'2026-10-05') is None


def test_machine_parent_proof_rejects_wrong_date_hash_ancestry_and_missing_source(tmp_path,monkeypatch):
    from copy import deepcopy
    from src.engine.automation import pre_submit_delay_situation_projection as recovery
    _machine_chain(tmp_path,monkeypatch)
    proof=recovery.prepare_machine_compatibility(tmp_path,'2026-10-05')
    for changed in ('date','hash','ancestry','semantic'):
        bad=deepcopy(proof)
        if changed=='date':bad['target_date']='2026-10-06'
        elif changed=='hash':bad['chain'][1]['sha256']='f'*64
        elif changed=='ancestry':bad['chain'].reverse()
        else:bad['semantic_sha256']='f'*64
        bad['sha256']=initial.digest({k:v for k,v in bad.items() if k!='sha256'})
        with pytest.raises(ValueError,match='delay_machine_compatibility'):
            recovery.machine_parent_mapping(bad,target_date='2026-10-05')
    Path(proof['chain'][1]['path']).unlink()
    with pytest.raises(FileNotFoundError):recovery.machine_parent_mapping(proof,target_date='2026-10-05')


def test_cached_recalculation_verifies_new_native_sources_before_publication(tmp_path,monkeypatch):
    from src.engine.automation import pre_submit_delay_situation_projection as recovery
    original,_=fixture(tmp_path/'source',monkeypatch)
    _machine_chain(tmp_path/'native',monkeypatch)
    checked=[]
    def verify(root,report):
        proof=report.get('machine_parent_compatibility')
        assert proof is not None
        checked.append(recovery.machine_parent_mapping(proof,target_date=report['effective_date']))
    monkeypatch.setattr(initial,'verify_source',verify)
    partitioned.run(tmp_path/'native',tmp_path/'candidate','2026-10-02',publication_date='2026-10-02',
        effective_date='2026-10-05',require_ledger=True,dry_run=True,contract=initial.code_contract(),
        cached=(original,iter(original['qualified_projection'])))
    assert checked and checked[0]['a'*64]=='c'*64


def test_whole_split_and_metrics_equal_supported_resident_reference(tmp_path,monkeypatch):
    reference,policy = fixture(tmp_path/'source',monkeypatch)
    result,selected = build(reference,tmp_path/'result')
    cells = {r['key']:r['value'] for r in storage.iter_tree(tmp_path/'result',result['cells_ref'])}
    assert set(cells)==set(reference['cells'])
    for key,cell in cells.items():
        assert {k:v for k,v in cell.items() if k!='partition_sha256'} == {
            k:v for k,v in reference['cells'][key].items() if k!='partition_sha256'}
    initial.validate(selected,result,target_date=reference['effective_date'])
    prepared = initial.PreparedPolicy.from_artifacts(selected,result,target_date=reference['effective_date'])
    assert prepared.lookup(target_date=reference['effective_date'],market='REGULAR')['delay_sec']==60


def test_ordinary_verifier_keeps_evidence_owned_disposable_scratch(tmp_path, monkeypatch):
    import tempfile
    from src.engine.infrastructure import startup_validation_code_context as context
    reference, _ = fixture(tmp_path/'source', monkeypatch)
    report, policy = build(reference, tmp_path/'evidence')
    original = tempfile.TemporaryDirectory
    parents = []
    def observed(*args, **kwargs):
        if kwargs.get('prefix') == '.verify-': parents.append(Path(kwargs['dir']))
        return original(*args, **kwargs)
    monkeypatch.setattr(tempfile, 'TemporaryDirectory', observed)
    monkeypatch.setenv('TMPDIR', str(tmp_path/'untrusted-env'))
    assert context.validate_preparation_delay_selection(None, None) is False
    before = {str(p.relative_to(report.evidence_root)): p.read_bytes()
        for p in report.evidence_root.rglob('*') if p.is_file()}
    initial.validate(policy, report)
    assert parents == [report.evidence_root]
    assert before == {str(p.relative_to(report.evidence_root)): p.read_bytes()
        for p in report.evidence_root.rglob('*') if p.is_file()}
    assert not list(report.evidence_root.glob('.verify-*'))


def test_sharded_population_survives_changed_layout_and_legacy_limits(tmp_path,monkeypatch):
    report,policy = fixture(tmp_path/'source',monkeypatch)
    monkeypatch.setattr(initial,'MAX_OPPORTUNITIES',2)
    first,_ = build(report,tmp_path/'first')
    monkeypatch.setattr(storage,'LEAF_BYTES',1024)
    monkeypatch.setattr(storage,'FANOUT',3)
    second,selected = build(report,tmp_path/'second')
    for key in ('qualified_projection_ref','partitions_ref','cells_ref'):
        assert first[key]['logical_sha256']==second[key]['logical_sha256']
    assert first['qualified_projection_ref']['sha256']!=second['qualified_projection_ref']['sha256']
    initial.validate(selected,second)


def test_global_late_conflict_is_excluded_before_split(tmp_path,monkeypatch):
    report,_ = fixture(tmp_path/'source',monkeypatch)
    # New producer qualification uses the original event rows, rather than a
    # report's already-selected projection as its opportunity denominator.
    rows = [json.loads(line) for path in (tmp_path/'source/threshold_cycle').glob(
        'date=*/family=pre_submit_delay/part-execution-*.jsonl') for line in path.read_text().splitlines()]
    from src.engine.scalping.pre_submit_delay_tuning import decision_source_sha256, quote_source_sha256
    commits = [r for r in rows if r['stage']=='pre_submit_delay_committed']
    for row in commits:
        row['fields']['original_evaluation_attempt_id'] = row['fields']['delay_intent_id']
    expected, expected_counts = initial.project_rows(rows)
    original = commits[0]
    alias = json.loads(json.dumps(original))
    alias['fields']['decision_committed_at_epoch'] += 1
    alias['fields']['delay_intent_id'] += '-alias'
    alias['fields']['decision_source_sha256'] = decision_source_sha256(alias['fields'])
    with storage.index(tmp_path/'result') as db:
        census = partitioned.project(iter(rows+[alias]),db)
        assert census['qualified_pass_n']==expected_counts['qualified_pass_n']-1
        assert census['exclusions']['canonical_opportunity_conflict']==1


def test_publish_copies_only_verified_referenced_evidence_and_loader_reads_it(tmp_path,monkeypatch):
    report,_ = fixture(tmp_path/'source',monkeypatch)
    result,policy = build(report,tmp_path/'candidate')
    data=tmp_path/'published'
    pointer=initial.publish(data,result,policy,expected_incumbent=None)
    report_file,policy_file,_,manifest=initial.committed_paths(data,report['source_date'])
    durable_report,durable_policy=initial._read(report_file),initial._read(policy_file)
    initial.validate(durable_policy,durable_report)
    assert durable_report.evidence_root!=result.evidence_root
    assert manifest['report_artifact_sha256']==initial.digest(result)
    child=next((durable_report.evidence_root/'shards').glob('*.json'))
    child.write_text('{}')
    with pytest.raises(ValueError):
        initial.committed_paths(data,report['source_date'])


def test_prepared_native_raw_ledger_publishes_only_verified_evidence(tmp_path,monkeypatch):
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.automation.pre_submit_delay_source_ledger import seal,publish_prepared
    from src.engine.scalping import pre_submit_delay_tuning as owner
    from src.engine.infrastructure.research_release_transition import Transition
    root=tmp_path/'workspace/data';day='2026-10-02'
    _price_pattern_fixture(root,monkeypatch,[{'prices':{0:10000,30:9900}}])
    rows=[json.loads(line) for p in (root/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl') for line in p.read_text().splitlines()]
    raw=root/'pipeline_events'/f'pipeline_events_{day}.jsonl';raw.parent.mkdir()
    raw.write_text(''.join(json.dumps({**row,'event_type':'pipeline_event'})+'\n' for row in rows))
    prepared=tmp_path/'prepared';ledger=seal(root,day,output_root=prepared)
    path=prepared/owner.family_source_ledger_path(root,day).name
    assert ledger['status']=='ready' and owner.family_source_ledger_issues(root,day,ledger_path=path)==[]
    transition=Transition(root.parent,'ledger')
    with transition.owner():transition.execute([lambda:publish_prepared(root,day,path)],verify=lambda:None)
    assert owner.family_source_ledger_issues(root,day)==[]
    raw.write_text(raw.read_text()+'{}\n')
    with pytest.raises(ValueError,match='prepared_delay_ledger_invalid'):publish_prepared(root,day,path)


def test_more_than_4096_cells_retains_every_research_row_and_zero_runtime_behavior(tmp_path,monkeypatch):
    from copy import deepcopy
    reference,_=fixture(tmp_path/'source',monkeypatch)
    row=next(r for r in reference['qualified_projection'] if r['anchor_kind']=='price_ready' and r['p0_valid'])
    count=4097
    def records():
        for i in range(count):
            value=deepcopy(row);value.update(identity=initial.digest(['original',i]),situation='UNKNOWN',
                parent_compatibility=[f'unverified-parent-{i}','unverified-aux'],native_evaluation_bound=False)
            yield value
    census=dict(raw_commit_n=count,qualified_pass_n=count,p0_valid_n=count,native_evaluation_unverified_n=count,
        parent_compatibility_unverified_n=count,exclusions={})
    report,policy=partitioned.build(records(),census,output_root=tmp_path/'full',source_date='2026-10-02',
        publication_date='2026-10-10',effective_date='2026-10-12',source_sha256=reference['source_sha256'],
        code_contract_sha256=reference['code_contract_sha256'],source_receipt=reference['source_receipt'])
    assert report['qualified_projection_ref']['count']==count and report['cells_ref']['count']==count
    assert report['status']=='initial_baseline_immediate'
    prepared=initial.PreparedPolicy.from_artifacts(policy,report,target_date='2026-10-12')
    assert len(prepared.cells)==0
    assert prepared.lookup(target_date='2026-10-12',market='REGULAR',parents=['new-parent','new-aux'])['delay_sec']==0


def test_normal_native_cli_budgets_family_outputs_without_scanning_shared_raw_aliases(tmp_path,monkeypatch):
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.scalping import pre_submit_delay_tuning as cli
    root=tmp_path/'data'
    _price_pattern_fixture(root,monkeypatch,[{'prices':{0:10000,30:9900,60:9800}}])
    with (root/'unrelated-large-source.bin').open('wb') as handle:handle.truncate(5*1024**3)
    (root/'unrelated-raw-alias').symlink_to(tmp_path/'external-input')
    rows=[json.loads(line) for p in (root/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl') for line in p.read_text().splitlines()]
    raw=root/'pipeline_events/pipeline_events_2026-10-02.jsonl';raw.parent.mkdir()
    raw.write_text(''.join(json.dumps({**row,'event_type':'pipeline_event'})+'\n' for row in rows))
    summaries=root/'pipeline_event_summaries';summaries.mkdir()
    (summaries/'unrelated-source-alias').symlink_to(tmp_path/'external-summary')
    from src.engine.automation.pre_submit_delay_source_ledger import seal
    assert seal(root,'2026-10-02')['status']=='ready'
    assert cli.main(['--date','2026-10-02','--publication-date','2026-10-10','--effective-date','2026-10-12',
        '--initial-policy-v2','--require-family-ledger','--input-root',str(root),'--output-root',str(root)])==0
    report_file,policy_file,_,_=initial.committed_paths(root,'2026-10-02',validate_selection=False)
    report,policy=initial._read(report_file),initial._read(policy_file)
    assert report['census']['raw_commit_n']==1 and report['price_ready_pair_n']==2
    assert len(initial.PreparedPolicy.from_artifacts(policy,report,target_date='2026-10-12').cells)==0


def test_supported_zero_situation_masks_positive_parent_in_both_formats(tmp_path,monkeypatch):
    report,_=fixture(tmp_path/'source',monkeypatch)
    rows=report['qualified_projection']
    for n,row in enumerate(rows):
        row['situation']='H1' if n in {0,4,8,12,14,18} else 'D1'
        row['pairs']={30:-10 if row['situation']=='H1' else 100}
    kwargs=dict(source_date=report['source_date'],publication_date=report['publication_date'],
        effective_date=report['effective_date'],source_sha256=report['source_sha256'],
        code_contract_sha256=report['code_contract_sha256'],source_receipt=report.get('source_receipt'))
    reference,selected=initial.build_initial([],_projected=(rows,report['census']),**kwargs)
    result,sharded=partitioned.build(rows,report['census'],output_root=tmp_path/'result',**kwargs)
    for policy,evidence in ((selected,reference),(sharded,result)):
        prepared=initial.PreparedPolicy.from_artifacts(policy,evidence,target_date=report['effective_date'])
        assert prepared.lookup(target_date=report['effective_date'],market='REGULAR',kind='H1')['delay_sec']==0
        assert prepared.lookup(target_date=report['effective_date'],market='REGULAR',kind='D1')['delay_sec']==30


def test_native_situation_join_preserves_original_hash_and_gzip_currentness(tmp_path):
    import sqlite3,gzip,hashlib
    from src.engine.automation import pre_submit_delay_situation_projection as recovery
    from src.engine.scalping.ai_decision_trace import _json_bytes
    from src.engine.scalping.reversal_extended_catalog import DEFINITIONS
    branch=next(iter(DEFINITIONS))
    native=dict(captured_at='2026-10-15T10:00:00+09:00',label_context=dict(evaluation_attempt_id='eval',stock_code='005930'),
        source=dict(assessment=dict(action='ENTER_NOW',machine_component_sha256='a'*64,primary_branch=None,matched_branches=[branch])))
    sha=hashlib.sha256(_json_bytes(native)).hexdigest();native['machine_observation_sha256']=sha
    source=tmp_path/'ai_decision_payloads/ai_decision_payloads_2026-10-15.jsonl'
    source.parent.mkdir();source.write_bytes(_json_bytes(native)+b'\n')
    from datetime import datetime
    fields=dict(anchor_contract_version=3,original_machine_observation_sha256=sha,evaluation_attempt_id='eval',
        entry_mechanistic_policy_sha256='a'*64,decision_source_sha256='b'*64,
        decision_committed_at_epoch=datetime.fromisoformat('2026-10-15T10:00:01+09:00').timestamp())
    row=dict(stage='pre_submit_delay_committed',emitted_date='2026-10-15',stock_code='005930',fields=fields)
    db=sqlite3.connect(':memory:');receipt=recovery.prepare([row],db,tmp_path)
    projected=list(recovery.enrich([row],db,receipt))[0]
    assert initial.situation(projected['fields']['_native_situation_projection']['fields'])==branch
    assert projected['fields']['decision_source_sha256']=='b'*64
    assert row['fields']==fields and '_native_situation_projection' not in fields
    later={**row,'fields':{**fields,'decision_committed_at_epoch':fields['decision_committed_at_epoch']-2}}
    assert '_native_situation_projection' not in list(recovery.enrich([later],db,receipt))[0]['fields']
    gz=Path(str(source)+'.gz');gz.write_bytes(gzip.compress(source.read_bytes()));source.unlink()
    recovery.verify(receipt)
    gz.write_bytes(gz.read_bytes()[:-5])
    with pytest.raises((ValueError,EOFError,OSError)):recovery.verify(receipt)


@pytest.mark.parametrize('damage',[None,'crc','different','late','conflicting_alias'])
def test_original_delay_ledger_accepts_only_identical_logical_archive(tmp_path,monkeypatch,damage):
    import gzip
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.automation.pre_submit_delay_source_ledger import seal
    from src.engine.scalping import pre_submit_delay_tuning as owner
    root=tmp_path/'data';day='2026-10-02'
    _price_pattern_fixture(root,monkeypatch,[{'prices':{0:10000,30:9900}}])
    rows=[json.loads(line) for p in (root/'threshold_cycle').glob('date=*/family=pre_submit_delay/part-execution-*.jsonl') for line in p.read_text().splitlines()]
    raw=root/'pipeline_events'/f'pipeline_events_{day}.jsonl';raw.parent.mkdir()
    original=''.join(json.dumps({**row,'event_type':'pipeline_event'})+'\n' for row in rows).encode();raw.write_bytes(original)
    out=tmp_path/'prepared';seal(root,day,output_root=out)
    path=out/owner.family_source_ledger_path(root,day).name;ledger_bytes=path.read_bytes()
    gz=Path(str(raw)+'.gz');gz.write_bytes(gzip.compress(original));raw.unlink()
    assert owner.family_source_ledger_issues(root,day,ledger_path=path)==[]
    if damage=='crc':gz.write_bytes(gz.read_bytes()[:-5])
    if damage=='different':gz.write_bytes(gzip.compress(original+b'{}\n'))
    if damage=='late':(raw.parent/f'pipeline_events_{day}.late.jsonl').write_text('{}\n')
    if damage=='conflicting_alias':raw.write_bytes(original+b'{}\n')
    assert bool(owner.family_source_ledger_issues(root,day,ledger_path=path)) is bool(damage)
    assert path.read_bytes()==ledger_bytes
