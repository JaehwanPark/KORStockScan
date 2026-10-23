"""Additive capability proofs must not rewrite historical operational evidence."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from src.engine.monitoring import policy_generation_contract as generation
from src.engine.monitoring import policy_generation_validation as validation
from src.engine.automation import policy_generation_fixture_validation as writer

DAY='2026-10-14'


def _fixture(data, family):
    payload=dict(date=DAY,generated_at=DAY+'T21:00:00+09:00',status='valid_empty',count=0)
    contract=generation.native(payload,family=family,day=DAY,data_root=data,
        source_state='valid_empty',comparison_state='insufficient_sample',handoff_state='incumbent_carried')
    payload['policy_generation']=contract
    if family=='holding_vote':payload={'holding_path_vote_replay':payload}
    relative={
        'entry_cancel_wait':f'report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_{DAY}.json',
        'rising_missed':f'report/rising_missed_classifier_prior/rising_missed_classifier_prior_{DAY}.json',
        'holding_vote':f'report/monitor_snapshots/holding_exit_observation_{DAY}.json',
        'auxiliary':f'report/reversal_auxiliary_tuning/{DAY}/evaluation.json',
    }[family]
    report=data/relative;report.parent.mkdir(parents=True);report.write_text(json.dumps(payload))
    observed=generation.observations(data.parent,DAY,data_root=data)[0]
    assert observed['status']=='unverified'
    run=data/'report/postclose_generation_validation/runs/test-run';run.mkdir(parents=True)
    xml=ET.Element('testsuites');suite=ET.SubElement(xml,'testsuite')
    for name in validation.PLANS[family]:
        ET.SubElement(suite,'testcase',classname='src.tests.'+Path(name).stem,name='synthetic_reader_contract')
    ET.ElementTree(xml).write(run/'tests.xml')
    (run/'tests.log').write_text('synthetic reader fixture, not operational proof\n')
    (run/'network.json').write_text('{"blocked_attempts":0}')
    value=dict(schema='postclose_generation_fixture_receipt_v1',family=family,
        code_sha256=generation.code_generation(family),status='pass',closure_tests=validation.PLANS[family],
        unresolved_findings=[],passed_tests=len(validation.PLANS[family]),validation_plan=validation.plan_identity(family),
        validation_run=str(run),evidence={n:validation.file_sha(run/n) for n in ['tests.log','tests.xml','network.json']},
        provider_calls=0,orders=0,protected_unchanged=True,protected_artifact_sha256={},
        **{k:False for k in validation.AUTHORITY_FALSE})
    path=validation.fixture_path(data,family)
    def seal():
        value['receipt_sha256']=generation.digest({k:v for k,v in value.items() if k!='receipt_sha256'})
        path.write_text(json.dumps(value))
    seal()
    return observed,report,run,path,value,seal


@pytest.mark.parametrize('family',validation.PLANS)
def test_current_fixture_closes_only_code_warning_without_rewriting_native_report(tmp_path,family):
    data=tmp_path/'data'; observed,report,run,path,value,seal=_fixture(data,family)
    before={p:p.read_bytes() for p in data.rglob('*') if p.is_file()}
    result=validation.current_fixture_observation(observed,data)
    assert result['status']=='verified',result
    assert result['findings']==[] and result['native_validated'] is False
    assert result['historical_contract_status']=='unverified' and result['current_code_capability_verified'] is True
    assert result['source_state']=='valid_empty' and result['comparison_state']=='insufficient_sample'
    assert result['handoff_state']=='incumbent_carried'
    assert result['runtime_effect'] is False and result['allowed_runtime_apply'] is False
    assert result['report_sha256']==observed['report_sha256']
    assert result['contract_sha256']==observed['contract_sha256']
    assert result['source_generation']==observed['source_generation']
    assert generation.observations(tmp_path,DAY,data_root=data)[0]['status']=='unverified'
    assert all(p.read_bytes()==raw for p,raw in before.items())


@pytest.mark.parametrize('damage',[None,'original','compact','pointer','missing','symlink','logical','physical'])
def test_lossless_native_report_projection_keeps_original_hash_and_budget(tmp_path,monkeypatch,damage):
    data=tmp_path/'data';_,report,_,_,_,_=_fixture(data,'entry_cancel_wait')
    payload=json.loads(report.read_text());report.write_text(json.dumps(payload,indent=12))
    original=report.read_bytes()
    import gzip
    limit=len(gzip.compress(original,mtime=0))+32
    assert len(original)>limit
    monkeypatch.setattr(validation,'NATIVE_REPORT_LIMIT',limit)
    receipt=validation.publish_native_report_projection(data,'entry_cancel_wait',DAY)
    compact=Path(str(report)+'.gz')
    pointer=Path(str(compact)+'.archive_receipt.json')
    if damage=='original':report.write_bytes(original+b'\n')
    elif damage=='compact':compact.write_text('{}')
    elif damage=='pointer':pointer.write_text('{}')
    elif damage=='missing':compact.unlink()
    elif damage=='symlink':
        other=tmp_path/'foreign.json';compact.rename(other);compact.symlink_to(other)
    elif damage=='logical':
        row=json.loads(pointer.read_text());row['logical_content_sha256']='a'*64
        row['artifact_content_sha256']=generation.digest({k:v for k,v in row.items() if k!='artifact_content_sha256'})
        pointer.write_text(json.dumps(row))
    elif damage=='physical':monkeypatch.setattr(validation,'NATIVE_REPORT_LIMIT',1)
    result=generation.observations(tmp_path,DAY,data_root=data)[0]
    if damage:
        assert result['status']=='unobservable'
    else:
        value,sha=validation.read_native_report(data,'entry_cancel_wait',DAY)
        assert value==payload and sha==hashlib.sha256(original).hexdigest()
        assert result['status']=='unverified' and result['report_sha256']==sha
        assert validation.current_fixture_observation(result,data)['status']=='verified'
        assert compact.stat().st_size<limit
    if damage!='original':assert report.read_bytes()==original


def test_projection_refuses_logically_oversized_source_and_invalid_native_contract(tmp_path,monkeypatch):
    data=tmp_path/'data';_,report,_,_,_,_=_fixture(data,'entry_cancel_wait')
    original=report.read_bytes()
    monkeypatch.setattr(validation,'NATIVE_REPORT_LIMIT',64)
    with pytest.raises(ValueError):validation.publish_native_report_projection(data,'entry_cancel_wait',DAY)
    assert report.read_bytes()==original
    payload=json.loads(original);payload['policy_generation']['contract_sha256']='a'*64
    report.write_text(json.dumps(payload));changed=report.read_bytes()
    with pytest.raises(ValueError,match='source_contract_invalid|policy_generation_contract_invalid'):
        validation.publish_native_report_projection(data,'entry_cancel_wait',DAY)
    assert report.read_bytes()==changed


@pytest.mark.parametrize('damage',['code','family','schema','runtime','profit','provider','orders','protected',
    'plan','tests','count','log','xml','network','skipped','failed','missing_test_file','run_path','source',
    'report_hash','contract_hash','source_generation','projection_code','projection_state',
    'native_contract','receipt_digest','fixture_symlink'])
def test_supplement_never_closes_changed_or_unverified_contract(tmp_path,damage):
    data=tmp_path/'data';observed,report,run,path,value,seal=_fixture(data,'entry_cancel_wait')
    if damage=='code':value['code_sha256']='a'*64
    elif damage=='family':value['family']='holding_vote'
    elif damage=='schema':value['schema']='unknown'
    elif damage=='runtime':value['runtime_effect']=True
    elif damage=='profit':value['actual_profit_verified']=True
    elif damage=='provider':value['provider_calls']=1
    elif damage=='orders':value['orders']=True
    elif damage=='protected':value['protected_unchanged']=False
    elif damage=='plan':value['validation_plan']={}
    elif damage=='tests':value['closure_tests']=[]
    elif damage=='count':value['passed_tests']=True
    elif damage=='log':(run/'tests.log').write_text('tampered')
    elif damage=='xml':(run/'tests.xml').write_text('tampered')
    elif damage in {'network','skipped','failed','missing_test_file'}:
        if damage=='network':(run/'network.json').write_text('{"blocked_attempts":1}')
        else:
            tree=ET.parse(run/'tests.xml');suite=tree.getroot().find('testsuite')
            if damage=='missing_test_file':suite.remove(suite[0])
            else:ET.SubElement(suite[0], 'skipped' if damage=='skipped' else 'failure')
            tree.write(run/'tests.xml')
        value['evidence']={n:validation.file_sha(run/n) for n in value['evidence']}
    elif damage=='run_path':value['validation_run']=str(tmp_path)
    elif damage=='source':report.write_text(report.read_text()+' ')
    elif damage=='report_hash':observed['report_sha256']='a'*64
    elif damage=='contract_hash':observed['contract_sha256']='a'*64
    elif damage=='source_generation':observed['source_generation']='a'*64
    elif damage=='projection_code':observed['code_sha256']='a'*64
    elif damage=='projection_state':observed['source_state']='complete'
    elif damage=='native_contract':
        payload=json.loads(report.read_text());payload['policy_generation']['runtime_effect']=True
        report.write_text(json.dumps(payload));observed['report_sha256']=hashlib.sha256(report.read_bytes()).hexdigest()
    seal()
    if damage=='receipt_digest':path.write_text(path.read_text().replace(value['receipt_sha256'],'0'*64))
    if damage=='fixture_symlink':
        dest=run/'other.json';path.rename(dest);path.symlink_to(dest)
    result=validation.current_fixture_observation(observed,data)
    assert result['status']=='unverified' and result['findings']==['policy_generation_unverified']
    assert result.get('current_code_capability_verified') is not True


@pytest.mark.parametrize('bad',['failed','timeout','network','changed_report','missing_cases','large_report','large_report_changed'])
def test_fixture_writer_failure_cannot_publish_or_modify_protected_source(tmp_path,monkeypatch,bad):
    data=tmp_path/'data';family='entry_cancel_wait'
    report=data/'report/entry_cancel_wait_tuning'/f'entry_cancel_wait_tuning_{DAY}.json'
    original='x'*(8*1024*1024+1) if bad.startswith('large_report') else 'original native source'
    report.parent.mkdir(parents=True);report.write_text(original)
    class Process:
        pid=123
        def __init__(self,command,**kwargs):
            self.command=command
            output=Path(next(x.split('=',1)[1] for x in command if x.startswith('--junitxml=')))
            assert not output.is_relative_to(data)
            assert output.parent.is_dir()
            self.running=True
        def wait(self,timeout):
            if bad=='timeout' and self.running:
                self.running=False
                raise writer.subprocess.TimeoutExpired(self.command,timeout)
            self.running=False
            xml_path=Path(next(x.split('=',1)[1] for x in self.command if x.startswith('--junitxml=')))
            root=ET.Element('testsuite')
            if bad!='missing_cases':
                for name in validation.PLANS[family]:
                    ET.SubElement(root,'testcase',classname='src.tests.'+Path(name).stem,name='fixture')
            ET.ElementTree(root).write(xml_path)
            (xml_path.parent/'network.json').write_text(json.dumps({'blocked_attempts':int(bad=='network')}))
            if bad in {'changed_report','large_report_changed'}:report.write_text('concurrent update')
            return 1 if bad=='failed' else 0
        def poll(self):return None if self.running else 0
    monkeypatch.setattr(writer,'_assert_committed',lambda family:None)
    monkeypatch.setattr(writer.subprocess,'Popen',Process)
    monkeypatch.setattr(writer.os,'killpg',lambda *a:None)
    monkeypatch.setattr(writer.subprocess,'check_output',lambda *a,**kw:'a'*40+'\n')
    if bad=='large_report':
        result=writer.validate(family,data,source_date=DAY,target_date='2026-10-15',publish=True)
        assert result['status']=='pass' and result['published'] is True
        assert validation.verify_fixture(data,family)[0]['protected_artifact_sha256'][str(report)]==hashlib.sha256(original.encode()).hexdigest()
        assert report.read_text()==original
        return
    with pytest.raises((ValueError,writer.subprocess.TimeoutExpired)):
        writer.validate(family,data,source_date=DAY,target_date='2026-10-15',publish=True)
    assert not validation.fixture_path(data,family).exists()
    assert report.read_text()==('concurrent update' if bad in {'changed_report','large_report_changed'} else original)
    assert len(list((data/'report/postclose_generation_validation/runs').glob('*/failure.json')))==1


@pytest.mark.parametrize('kind',['fifo','symlink','oversize'])
def test_fixture_reader_is_bounded_and_rejects_special_sources(tmp_path,kind):
    import os
    path=tmp_path/'input'
    if kind=='fifo':os.mkfifo(path)
    elif kind=='symlink':
        target=tmp_path/'target';target.write_text('value');path.symlink_to(target)
    else:path.write_text('x'*11)
    with pytest.raises((ValueError,OSError)):
        validation.file_bytes(path,10)
    if kind != 'oversize':
        with pytest.raises((ValueError,OSError)):
            validation.file_sha(path,stream=True)



def test_fixture_publication_rejects_dirty_or_untracked_source(monkeypatch):
    monkeypatch.setattr(writer.subprocess,'check_output',lambda *a,**k:'?? untracked.py\n')
    with pytest.raises(ValueError,match='committed_sources'):
        writer._assert_committed('entry_cancel_wait')


@pytest.mark.parametrize('family',validation.PLANS)
def test_fixture_publication_checks_the_same_shared_budget_dependency(monkeypatch,family):
    calls=[]
    def dirty(command,**kwargs):
        calls.append(command)
        for name in generation.COMMON_CODE_COMPONENTS:
            assert command.count('src/engine/'+name)==1
        return ' M src/engine/lifecycle/research_input_budget.py\n'
    monkeypatch.setattr(writer.subprocess,'check_output',dirty)
    with pytest.raises(ValueError,match='committed_sources'):writer._assert_committed(family)
    assert len(calls)==1


@pytest.mark.parametrize('dependency',[
    'lifecycle/research_input_budget.py',
    'monitoring/policy_generation_validation.py',
    'automation/policy_generation_fixture_validation.py'])
def test_shared_dependency_change_creates_new_capability_and_fixture_paths(tmp_path,monkeypatch,dependency):
    names=set(generation.COMMON_CODE_COMPONENTS)
    for paths in generation.COMPONENTS.values():names.update(paths)
    engine=tmp_path/'src/engine'
    for name in names:
        path=engine/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((generation.ENGINE/name).read_bytes())
    monkeypatch.setattr(generation,'ENGINE',engine)
    data=tmp_path/'data';before={family:validation.fixture_path(data,family) for family in validation.PLANS}
    for family,path in before.items():
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(('preserved '+family).encode())
    originals={path:path.read_bytes() for path in before.values()}
    helper=engine/dependency
    helper.write_bytes(helper.read_bytes()+b'\n# Different shared Claim generation.\n')
    after={family:validation.fixture_path(data,family) for family in validation.PLANS}
    assert all(after[family]!=before[family] and not after[family].exists() for family in validation.PLANS)
    assert all(path.read_bytes()==raw for path,raw in originals.items())


@pytest.mark.parametrize('damage',[None,'plan','issuer','source','evidence'])
def test_late_historical_fixture_uses_exact_original_issuer_plan(tmp_path,monkeypatch,damage):
    import subprocess
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    from src.engine.infrastructure import runtime_release_router as router
    data=tmp_path/'data'
    _,report,_,path,value,seal=_fixture(data,'holding_vote')
    issuer=tmp_path/'issuer';issuer.mkdir()
    subprocess.run(['git','init','-q',str(issuer)],check=True)
    plan={}
    for name in validation.plan_identity('holding_vote'):
        target=issuer/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(b'original reviewed validation bytes\n')
        plan[name]=validation.file_sha(target)
    subprocess.run(['git','-C',str(issuer),'add','.'],check=True)
    subprocess.run(['git','-C',str(issuer),'-c','user.name=fixture','-c','user.email=fixture@example.test',
        'commit','-qm','original issuer'],check=True)
    revision=subprocess.check_output(['git','-C',str(issuer),'rev-parse','HEAD'],text=True).strip()
    def validate(workspace,selection):
        assert selection['release_root']==str(issuer) and selection['git_commit']==revision
        if damage=='issuer':raise ValueError('untrusted issuer')
    monkeypatch.setattr(router,'validate_release',validate)
    sha=validation.file_sha(report)
    value.update(validation_plan=plan,release_root=str(issuer),git_commit=revision,
        protected_artifact_sha256={str(report):sha})
    if damage=='plan':value['validation_plan']={**plan,next(iter(plan)):'b'*64}
    if damage=='source':value['protected_artifact_sha256'][str(report)]='b'*64
    if damage=='evidence':value['evidence']['network.json']='b'*64
    seal()
    contract=dict(code_sha256=value['code_sha256'],fixture_receipt=None)
    if damage:
        with pytest.raises(ValueError):handoff._historical_fixture(contract,data,'holding_vote',late_report=(report,sha))
    else:
        result=handoff._historical_fixture(contract,data,'holding_vote',late_report=(report,sha))
        assert result['path']==str(path)


@pytest.mark.parametrize('family,review_map', [
    (family, review_map) for family in validation.PLANS for review_map in [
    'REVIEWED_SUCCESSORS', 'REVIEWED_PRESERVED_SOURCE_SUCCESSORS',
    'REVIEWED_DEPLOYED_SOURCE_SUCCESSORS', 'REVIEWED_DELAY_SOURCE_SUCCESSORS',
    'REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS',
    'REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS', 'REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS',
    'REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS', 'REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS',
    'REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS', 'REVIEWED_CLEANUP_SOURCE_SUCCESSORS']
] + [(family, 'REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS')
     for family in ('rising_missed', 'holding_vote')]
  + [(family, 'REVIEWED_ARCHIVE_RETENTION_SOURCE_SUCCESSORS')
     for family in ('entry_cancel_wait', 'holding_vote')]
  + [(family, review_map) for family in ('rising_missed','holding_vote')
     for review_map in ('REVIEWED_INTEGRATED_OBSERVATION_SUCCESSORS','REVIEWED_INTEGRATED_CONSUMED_SUCCESSORS')])
@pytest.mark.parametrize('damage', [None,'unreviewed_old','unreviewed_current','source','contract',
    'fixture_code','plan','report_path','state','missing','authority','receipt'])
def test_exact_reviewed_successor_preserves_historical_code_and_source(tmp_path, monkeypatch, family, damage, review_map):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    if review_map in {'REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS',
                      'REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS', 'REVIEWED_CLEANUP_SOURCE_SUCCESSORS'}:
        monkeypatch.setitem(globals(),'DAY','2026-10-16')
    data=tmp_path/'data'; observed,report,run,path,value,seal=_fixture(data,family)
    payload=json.loads(report.read_text())
    native=payload['holding_path_vote_replay'] if family=='holding_vote' else payload
    contract=native['policy_generation']; old='a'*64; current=contract['code_sha256']
    contract['code_sha256']=old
    if review_map in {'REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS',
                      'REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS', 'REVIEWED_CLEANUP_SOURCE_SUCCESSORS',
                      'REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS',
                      'REVIEWED_ARCHIVE_RETENTION_SOURCE_SUCCESSORS', 'REVIEWED_INTEGRATED_OBSERVATION_SUCCESSORS',
                      'REVIEWED_INTEGRATED_CONSUMED_SUCCESSORS'}:
        historical=dict(value,code_sha256=old)
        historical['receipt_sha256']=generation.digest({k:v for k,v in historical.items() if k!='receipt_sha256'})
        historical_path=data/'report/postclose_generation_validation'/(family+'_'+old+'.json')
        historical_path.write_text(json.dumps(historical))
        contract['fixture_receipt']=dict(path=str(historical_path),sha256=validation.file_sha(historical_path))
    contract['retry_key']=generation.digest([family,contract['source_generation'],old,contract['source_state']])
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    report.write_text(json.dumps(payload))
    observed=generation.observations(tmp_path,DAY,data_root=data)[0]
    monkeypatch.setattr(handoff,'REVIEWED_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_PRESERVED_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_DEPLOYED_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_DELAY_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_CLEANUP_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,review_map,{family:(old,current)})
    if damage=='unreviewed_old':monkeypatch.setattr(handoff,review_map,{family:('b'*64,current)})
    elif damage=='unreviewed_current':monkeypatch.setattr(handoff,review_map,{family:(old,'b'*64)})
    elif damage=='source':native['count']=1;report.write_text(json.dumps(payload))
    elif damage=='contract':contract['code_sha256']='b'*64;report.write_text(json.dumps(payload))
    elif damage=='fixture_code':value['code_sha256']='b'*64;seal()
    elif damage=='plan':value['validation_plan']={};seal()
    elif damage=='report_path':observed['artifact']=str(tmp_path/'foreign.json')
    elif damage=='state':observed['source_state']='foreign'
    elif damage=='missing':observed['missing_components']=['reader']
    elif damage=='authority':contract['allowed_runtime_apply']=True;report.write_text(json.dumps(payload))
    elif damage=='receipt':value['receipt_sha256']='b'*64;path.write_text(json.dumps(value))
    before={p:p.read_bytes() for p in data.rglob('*') if p.is_file()}
    result=handoff.current_fixture_observation(observed,data)
    assert result['status']==('verified' if damage is None else 'unverified'),result
    if damage is None:
        assert result['code_sha256']==old and result['current_capability_code_sha256']==current
        assert result['native_validated'] is False and result['runtime_effect'] is False
        assert result['allowed_runtime_apply'] is False and result['source_generation']==observed['source_generation']
        assert result['contract_sha256']==observed['contract_sha256']
        assert all(result[key] == observed[key] for key in
                   ('source_state', 'comparison_state', 'handoff_state'))
    assert all(p.read_bytes()==b for p,b in before.items())


FROZEN_PRE_CLEANUP_TARGETS = {'auxiliary': '00e4f1813805e520e9daed86fa1b71b55c06f76c7128b4ad7762d978ab956822',
 'entry_cancel_wait': '4bf8bb24955fa5889d9090bcbbee1fd317493f0841d2a5a46566453291a5e907',
 'holding_vote': 'e28c76991bc6f09b02d44469d5238ca2d6b0f45f41c5a4414c67054197dd44ea',
 'rising_missed': '7fa7a62c8bd2f75b7218cee881ea1cffd41c4ade083b97fc73c0559693447aeb'}


@pytest.mark.parametrize('review_map', [
    'REVIEWED_SUCCESSORS', 'REVIEWED_PRESERVED_SOURCE_SUCCESSORS',
    'REVIEWED_DEPLOYED_SOURCE_SUCCESSORS', 'REVIEWED_DELAY_SOURCE_SUCCESSORS',
])
def test_historical_targets_remain_frozen_and_current_has_its_own_direct_pair(review_map):
    """Historical targets cannot silently chain to a newer family reader."""
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    for family, (_, successor) in getattr(handoff, review_map).items():
        prepared = handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS[family]
        assert successor == prepared[1]
        reviewed = (handoff.REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS if family == 'auxiliary'
                    else handoff.REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS)
        assert reviewed[family] == (prepared[0], FROZEN_PRE_CLEANUP_TARGETS[family])


def test_auxiliary_input_successor_preserves_prior_prepared_pair():
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    old = 'd04bcb11a28f731c1af5c332d33d49774f977a01a2ac90463df50865186fa6b0'
    assert handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS['auxiliary'] == (
        old, '2cfae7da4242e371d3e3a335b7915c2615c384aaa0747a358df315cde0a991b4')
    assert handoff.REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS == {
        'auxiliary': (old, 'dea0b4f9d124372e48413635f5f82fbf3f0fbd6477a4f1beaca6769a68e9990b')}
    assert handoff.REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS['auxiliary'] == (
        old, 'a249dbc9baa7fb5e05a36481cf476083de6c8b7ad369e3b26ceb7f3ba74373b5')
    assert handoff.REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS['auxiliary'] == (
        old, '00e4f1813805e520e9daed86fa1b71b55c06f76c7128b4ad7762d978ab956822')


def test_post_aux_guard_successor_preserves_exact_original_reports_and_prior_targets():
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    original_pairs = {
        'rising_missed': (
            'e9f1620fd55d335d1db3ccad52f1211440b5d2df57ddf45988e2012ecf6ed874',
            '676d7922cd257b940012445f9c0f1bd7eb905fb649e9492728b0bce097769962'),
        'holding_vote': (
            '057c1274c876450cc5f97a918899c96c85fed7dadb408ea6af445c67808c4fce',
            '8322022b48cd30484741f23c1f6f906a547e8a3145920645b022dba0d2d0fedf'),
    }
    for family, pair in original_pairs.items():
        assert handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS[family] == pair
    assert handoff.REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS == {
        'rising_missed': (original_pairs['rising_missed'][0],
            'b47474ed46cc63f090ccf14ce40b6d53b1d1518cba43211e648a1ee1b0f2aa36'),
        'holding_vote': (original_pairs['holding_vote'][0],
            '02b637bfb01bb9f01b4d8b33672d2ae0d9be74ff07c3ee972608f0c55beaf2e5')}
    assert handoff.REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS == {
        'rising_missed': (original_pairs['rising_missed'][0],
                         '5f8cd733ba9fb8b4733f3bafbc5a9431d45d6638713934daf74ba144844d74a5'),
        'holding_vote': (original_pairs['holding_vote'][0],
            'e06ee4b2d6d09410dd81d88cb661b6a18df2ca1dea2e7e81823a7d6e03d24b46')}
    assert handoff.REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS == {
        'holding_vote': (original_pairs['holding_vote'][0],
                         '6c4734c5e4204b36faf3d72ee873a429147d7a6e5a3a019d55fee29f4e145137')}
    for family,pair in original_pairs.items():
        assert handoff.REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS[family] == (
            pair[0], FROZEN_PRE_CLEANUP_TARGETS[family])


@pytest.mark.parametrize('family,prior', [
    ('entry_cancel_wait','b2a2017deb606554fbe1c9d481426786b3a8ab463c948ee84cd8ab856eddfca0'),
    ('rising_missed','dde49a32b7299deabf981e9f3a734a9da3019ba3f4e3eb7abbaff91dd3d01fa3'),
])
def test_preserved_oct15_reports_retain_their_reviewed_capability_target(family, prior):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    expected_target = handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS[family][1]
    assert handoff.REVIEWED_PRESERVED_SOURCE_SUCCESSORS[family] == (prior, expected_target)


@pytest.mark.parametrize('family,historical,cleanup', [
    *[(family, False, False) for family in validation.PLANS], ('auxiliary', True, False),
    *[(family, False, True) for family in validation.PLANS],
])
@pytest.mark.parametrize('fault',[None,'historical_fixture_absent','other_date','prior_target','unknown_source','unknown_current'])
def test_integrated_direct_pair_never_chains_history_or_skips_original_fixture(tmp_path,monkeypatch,family,historical,cleanup,fault):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    monkeypatch.setitem(globals(),'DAY','2026-10-15' if fault=='other_date' else '2026-10-16')
    reviewed = (handoff.REVIEWED_CLEANUP_SOURCE_SUCCESSORS if cleanup else
                handoff.REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS
                if family == 'auxiliary' and not historical
                else handoff.REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS)
    source,current=reviewed[family]
    # This test validates the named historical registration, not a later target.
    monkeypatch.setattr(generation,'code_generation',lambda candidate: current)
    data=tmp_path/'data';_,report,_,_,value,_=_fixture(data,family)
    assert current==generation.code_generation(family)
    if fault=='prior_target':source=handoff.REVIEWED_PREPARED_CODE_SOURCE_SUCCESSORS[family][1]
    elif fault=='unknown_source':source='f'*64
    historical=dict(value,code_sha256=source)
    historical['receipt_sha256']=generation.digest({k:v for k,v in historical.items() if k!='receipt_sha256'})
    path=data/'report/postclose_generation_validation'/(family+'_'+source+'.json')
    path.write_text(json.dumps(historical))
    reference=dict(path=str(path),sha256=validation.file_sha(path))
    body=json.loads(report.read_text());native=body['holding_path_vote_replay'] if family=='holding_vote' else body
    contract=native['policy_generation']
    contract.update(code_sha256=source,fixture_receipt=None if fault=='historical_fixture_absent' else reference,
        retry_key=generation.digest([family,contract['source_generation'],source,contract['source_state']]))
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    report.write_text(json.dumps(body))
    if fault=='unknown_current':monkeypatch.setattr(generation,'code_generation',lambda family:'b'*64)
    observed=generation.observations(tmp_path,DAY,data_root=data)[0]
    before={p:p.read_bytes() for p in data.rglob('*') if p.is_file()}
    result=handoff.current_fixture_observation(observed,data)
    assert result['status']==('verified' if fault is None else 'unverified')
    if fault is None:
        assert result['preserved_historical_fixture']==reference
        assert result['current_fixture']!=reference and result['native_validated'] is False
        assert result['runtime_effect'] is False and result['allowed_runtime_apply'] is False
        assert all(result[name]==observed[name] for name in ('source_generation','source_state','comparison_state','handoff_state'))
    assert all(path.read_bytes()==raw for path,raw in before.items())


@pytest.mark.parametrize('family', ['rising_missed', 'holding_vote'])
def test_post_aux_guard_successor_does_not_transitively_promote_older_reports(tmp_path, family):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    data=tmp_path/'data'
    _,report,_,_,_,_=_fixture(data,family)
    payload=json.loads(report.read_text())
    native=payload['holding_path_vote_replay'] if family=='holding_vote' else payload
    contract=native['policy_generation']
    old=handoff.REVIEWED_PRESERVED_SOURCE_SUCCESSORS[family][0]
    contract.update(code_sha256=old,
        retry_key=generation.digest([family,contract['source_generation'],old,contract['source_state']]))
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    report.write_text(json.dumps(payload))
    observed=generation.observations(tmp_path,DAY,data_root=data)[0]
    before=report.read_bytes()
    result=handoff.current_fixture_observation(observed,data)
    assert result['status']=='unverified'
    assert result.get('current_code_capability_verified') is not True
    assert report.read_bytes()==before


@pytest.mark.parametrize('family,review_map', [
    ('auxiliary', 'REVIEWED_SUCCESSORS'),
    ('auxiliary', 'REVIEWED_AUXILIARY_INPUT_SOURCE_SUCCESSORS'),
    ('auxiliary', 'REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS'),
    ('rising_missed', 'REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS'),
    ('holding_vote', 'REVIEWED_POST_AUX_GUARD_SOURCE_SUCCESSORS'),
    ('holding_vote', 'REVIEWED_QUANTITY_COST_SOURCE_SUCCESSORS'),
    ('rising_missed', 'REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS'),
    ('holding_vote', 'REVIEWED_DELAY_RESEARCH_SOURCE_SUCCESSORS'),
    *[(family,'REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS') for family in validation.PLANS],
    *[(family,'REVIEWED_CLEANUP_SOURCE_SUCCESSORS') for family in validation.PLANS],
    *[(family,'REVIEWED_RECEIPT_CUSTODY_SOURCE_SUCCESSORS') for family in validation.PLANS],
    ('holding_vote','REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS'),
    ('auxiliary','REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS'),

    *[(family,'REVIEWED_SOURCE_READER_SUCCESSORS') for family in ('rising_missed','auxiliary')],
    *[(family,'REVIEWED_DELAY_CLEANUP_SUCCESSORS') for family in ('rising_missed','auxiliary','holding_vote')],
    ('holding_vote','REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS'),
    *[(family,'REVIEWED_HOLDING_REPUBLICATION_SUCCESSORS') for family in ('entry_cancel_wait','auxiliary')],
    *[(family,'REVIEWED_FIXED_WAIT_SUCCESSORS') for family in ('rising_missed','holding_vote')],
    *[(family,'REVIEWED_ENTRY_COST_SOURCE_SUCCESSORS') for family in validation.PLANS],
    *[(family,'REVIEWED_ENTRY_COST_SUCCESSORS') for family in validation.PLANS],
    *[(family,'REVIEWED_SHUTDOWN_SUCCESSORS') for family in validation.PLANS],
    *[(family,'REVIEWED_SHUTDOWN_SOURCE_SUCCESSORS') for family in validation.PLANS],
    *[(family,'REVIEWED_SHUTDOWN_CONSUMED_SUCCESSORS') for family in validation.PLANS],
    *[(family,review_map) for family in ('rising_missed','holding_vote') for review_map in (
        'REVIEWED_NATIVE_SELECTION_SUCCESSORS','REVIEWED_NATIVE_SELECTION_SOURCE_SUCCESSORS',
        'REVIEWED_NATIVE_SELECTION_CONSUMED_SUCCESSORS','REVIEWED_ENTRY_ROUTE_SOURCE_SUCCESSORS',
        'REVIEWED_PRE_SUBMIT_CONSUMED_SUCCESSORS','REVIEWED_INTEGRATED_OBSERVATION_SUCCESSORS',
        'REVIEWED_INTEGRATED_CONSUMED_SUCCESSORS')],
    *[(family,'REVIEWED_QUANTITY_CAPTURE_SUCCESSORS') for family in ('rising_missed','holding_vote')],
    *[(family,'REVIEWED_ARCHIVE_RETENTION_SOURCE_SUCCESSORS') for family in ('entry_cancel_wait','holding_vote')],
    ('entry_cancel_wait','REVIEWED_BUY_IDENTITY_SUCCESSORS'),
    *[(family,'REVIEWED_ENTRY_RECEIPT_SUCCESSORS') for family in ('entry_cancel_wait','rising_missed','holding_vote')],
])
@pytest.mark.parametrize('damage', [None, 'missing', 'bytes', 'path', 'authority', 'seal', 'symlink',
                                   'current_missing', 'current_bytes', 'current_code'])
def test_successor_requires_preserved_prior_fixture_and_independent_current_fixture(tmp_path, monkeypatch, damage, review_map, family):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    if review_map in {'REVIEWED_INTEGRATED_RESEARCH_SOURCE_SUCCESSORS',
                      'REVIEWED_STARTUP_READONLY_SOURCE_SUCCESSORS', 'REVIEWED_CLEANUP_SOURCE_SUCCESSORS'}:
        monkeypatch.setitem(globals(),'DAY','2026-10-16')
    data=tmp_path/'data'
    _,report,_,current_path,value,seal_current=_fixture(data,family)
    payload=json.loads(report.read_text())
    native=payload['holding_path_vote_replay'] if family=='holding_vote' else payload
    contract=native['policy_generation']
    old='a'*64; current=contract['code_sha256']
    historical=dict(value,code_sha256=old)
    if damage=='authority':historical['allowed_runtime_apply']=True
    historical['receipt_sha256']=generation.digest({k:v for k,v in historical.items() if k!='receipt_sha256'})
    if damage=='seal':historical['receipt_sha256']='b'*64
    path=data/'report/postclose_generation_validation'/(family+'_'+old+'.json')
    path.write_text(json.dumps(historical))
    reference=dict(path=str(path),sha256=validation.file_sha(path))
    contract.update(code_sha256=old,fixture_receipt=reference,
        retry_key=generation.digest([family,contract['source_generation'],old,contract['source_state']]))
    if damage=='path':reference['path']=str(tmp_path/'foreign.json')
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    report.write_text(json.dumps(payload))
    observed=generation.observations(tmp_path,DAY,data_root=data)[0]
    monkeypatch.setattr(handoff,review_map,{family:((old,current),) if review_map=='REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS' else (old,current)})
    if damage=='missing':path.unlink()
    elif damage=='bytes':path.write_text('{}')
    elif damage=='symlink':
        other=tmp_path/'historical.json';path.rename(other);path.symlink_to(other)
    elif damage=='current_missing':current_path.unlink()
    elif damage=='current_bytes':current_path.write_text('{}')
    elif damage=='current_code':value['code_sha256']=old;seal_current()
    before=report.read_bytes()
    result=handoff.current_fixture_observation(observed,data)
    assert result['status']==('verified' if damage is None else 'unverified'),result
    assert report.read_bytes()==before
    if damage is None:
        assert result['preserved_historical_fixture']==reference
        assert result['current_fixture']!=reference
        assert result['native_validated'] is False
        assert result['historical_contract_status']=='unverified'


@pytest.mark.parametrize('family', list(validation.PLANS))
def test_latest_capability_pair_is_current_and_keeps_original_source(family):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    old, current = handoff.REVIEWED_FROZEN_INPUT_SOURCE_SUCCESSORS[family][-1]
    assert current == generation.code_generation(family)
    assert old == {
        'rising_missed': 'b1fb8b69fb938893d36c8b16192bbd0cd5e414f169b8304374d781cc54248ab5',
        'holding_vote': 'b37bdd2ec37e69e281fad273e3b9d07dab8aaf559c5a7841b9d4473141beb9ee',
        'entry_cancel_wait': '60620f4b8fbe73f3c0506eed8f49c27c031d74a643b68667ca7421c6512d6f57',
        'auxiliary': '507700d07f88f668f1b467678615656db7af893e0c3e6dbf8148d5c918ed9120',
    }[family]


@pytest.mark.parametrize('family', list(validation.PLANS))
def test_native_verified_family_does_not_require_historical_successor(family, monkeypatch, tmp_path):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    observed = dict(family=family, status='verified', findings=[],
        code_sha256=generation.code_generation(family), native_validated=True)
    monkeypatch.setattr(validation, 'verify_fixture', lambda *a: pytest.fail('native verdict already verified'))
    assert handoff.current_fixture_observation(observed, tmp_path) == observed


@pytest.mark.parametrize('family', ['rising_missed', 'holding_vote', 'auxiliary'])
def test_unreviewed_code_pair_is_not_reported_as_original_report_mutation(family, tmp_path):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    observed = dict(family=family, status='unverified', findings=['policy_generation_unverified'],
        missing_components=[], observation_complete=True, native_validated=False, code_sha256='a'*64)
    result = handoff.current_fixture_observation(observed, tmp_path)
    assert result['status'] == 'unverified' and result['findings'] == observed['findings']
    assert result['current_fixture_reason'] == 'successor_code_pair_unreviewed'
    assert 'current_code_capability_verified' not in result


@pytest.mark.parametrize('foreign', [False, True])
def test_native_fixture_relative_reference_binds_data_owner_not_launcher_cwd(tmp_path, monkeypatch, foreign):
    data=tmp_path/'workspace/data'
    _,report,_,fixture,_,_=_fixture(data,'auxiliary')
    payload=json.loads(report.read_text());contract=payload['policy_generation']
    contract['fixture_receipt']=dict(path=('outside/'+fixture.name if foreign else 'data/report/postclose_generation_validation/'+fixture.name),
        sha256=validation.file_sha(fixture))
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    other=tmp_path/'unrelated-launcher';other.mkdir();monkeypatch.chdir(other)
    if foreign:
        with pytest.raises(ValueError,match='fixture_path_invalid'):
            generation.inspect(contract,family='auxiliary',day=DAY,payload=payload,data_root=data)
    else:
        result=generation.inspect(contract,family='auxiliary',day=DAY,payload=payload,data_root=data)
        assert result['status']=='verified'


@pytest.mark.parametrize('successor', ['REVIEWED_HISTORICAL_RESOLUTION_SUCCESSORS', 'REVIEWED_FIXED_WAIT_SUCCESSORS', 'REVIEWED_ENTRY_RECEIPT_SUCCESSORS', 'REVIEWED_QUANTITY_CAPTURE_SUCCESSORS'])
@pytest.mark.parametrize('damage', [None, 'report', 'missing', 'network', 'plan', 'count', 'wrong_pair'])
def test_exact_successor_accepts_late_original_fixture_only_with_native_report_binding(tmp_path, monkeypatch, damage, successor):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    data=tmp_path/'data';family='holding_vote'
    _,report,run,current_path,current,seal=_fixture(data,family)
    payload=json.loads(report.read_bytes());contract=payload['holding_path_vote_replay']['policy_generation']
    old='a'*64;new=contract['code_sha256']
    contract.update(code_sha256=old,fixture_receipt=None,
        retry_key=generation.digest([family,contract['source_generation'],old,contract['source_state']]))
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    report.write_text(json.dumps(payload));before=report.read_bytes()
    prior=dict(current,code_sha256=old,protected_artifact_sha256={str(report):validation.file_sha(report)})
    if damage=='report':prior['protected_artifact_sha256'][str(report)]='b'*64
    if damage=='plan':prior['validation_plan']={}
    if damage=='count':prior['passed_tests']=True
    if damage=='network':
        (run/'network.json').write_text('{"blocked_attempts":1}')
        prior['evidence']={**prior['evidence'],'network.json':validation.file_sha(run/'network.json')}
    prior['receipt_sha256']=generation.digest({k:v for k,v in prior.items() if k!='receipt_sha256'})
    path=data/'report/postclose_generation_validation'/(family+'_'+old+'.json')
    if damage!='missing':path.write_text(json.dumps(prior))
    monkeypatch.setattr(handoff,successor,
        {family: ('c'*64 if damage=='wrong_pair' else old,new)})
    observed=generation.observations(tmp_path,DAY,data_root=data)[0]
    result=handoff.current_fixture_observation(observed,data)
    assert result['status']==('verified' if damage is None else 'unverified'),result
    assert report.read_bytes()==before and contract['fixture_receipt'] is None


@pytest.mark.parametrize('mutation', [None, 'rewrite', 'append', 'replace'])
def test_protected_hash_stream_is_bounded_and_rejects_mid_read_generation_change(tmp_path, monkeypatch, mutation):
    path=tmp_path/'protected.json';raw=b'x'*(128*1024+1);path.write_bytes(raw)
    fdopen=validation.os.fdopen
    class Reader:
        def __init__(self, stream):self.stream=stream;self.reads=0
        def __enter__(self):return self
        def __exit__(self,*args):return self.stream.__exit__(*args)
        def fileno(self):return self.stream.fileno()
        def read(self,size):
            assert 0 < size <= 64*1024
            value=self.stream.read(size);self.reads+=1
            if self.reads==1:
                if mutation=='rewrite':path.write_bytes(b'y'*len(raw))
                elif mutation=='append':
                    with path.open('ab') as handle:handle.write(b'y')
                elif mutation=='replace':
                    replacement=tmp_path/'replacement';replacement.write_bytes(raw);replacement.replace(path)
            return value
    monkeypatch.setattr(validation.os,'fdopen',lambda *a,**kw:Reader(fdopen(*a,**kw)))
    if mutation:
        with pytest.raises(ValueError,match='fixture_read_changed_or_limit_exceeded'):
            validation.file_sha(path,stream=True)
    else:
        assert validation.file_sha(path,stream=True)==hashlib.sha256(raw).hexdigest()
