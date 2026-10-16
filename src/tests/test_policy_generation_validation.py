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


@pytest.mark.parametrize('bad',['failed','timeout','network','changed_report','missing_cases'])
def test_fixture_writer_failure_cannot_publish_or_modify_protected_source(tmp_path,monkeypatch,bad):
    data=tmp_path/'data';family='entry_cancel_wait'
    report=data/'report/entry_cancel_wait_tuning'/f'entry_cancel_wait_tuning_{DAY}.json'
    report.parent.mkdir(parents=True);report.write_text('original native source')
    class Process:
        pid=123
        def __init__(self,command,**kwargs):
            self.command=command
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
            if bad=='changed_report':report.write_text('concurrent update')
            return 1 if bad=='failed' else 0
        def poll(self):return None if self.running else 0
    monkeypatch.setattr(writer,'_assert_committed',lambda family:None)
    monkeypatch.setattr(writer.subprocess,'Popen',Process)
    monkeypatch.setattr(writer.os,'killpg',lambda *a:None)
    with pytest.raises((ValueError,writer.subprocess.TimeoutExpired)):
        writer.validate(family,data,source_date=DAY,target_date='2026-10-15',publish=True)
    assert not validation.fixture_path(data,family).exists()
    assert report.read_text()==('concurrent update' if bad=='changed_report' else 'original native source')
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



def test_fixture_publication_rejects_dirty_or_untracked_source(monkeypatch):
    monkeypatch.setattr(writer.subprocess,'check_output',lambda *a,**k:'?? untracked.py\n')
    with pytest.raises(ValueError,match='committed_sources'):
        writer._assert_committed('entry_cancel_wait')


@pytest.mark.parametrize('family', ['entry_cancel_wait','rising_missed','holding_vote','auxiliary'])
@pytest.mark.parametrize('review_map', ['REVIEWED_SUCCESSORS', 'REVIEWED_PRESERVED_SOURCE_SUCCESSORS',
    'REVIEWED_DEPLOYED_SOURCE_SUCCESSORS', 'REVIEWED_DELAY_SOURCE_SUCCESSORS'])
@pytest.mark.parametrize('damage', [None,'unreviewed_old','unreviewed_current','source','contract',
    'fixture_code','plan','report_path','state','missing','authority','receipt'])
def test_exact_reviewed_successor_preserves_historical_code_and_source(tmp_path, monkeypatch, family, damage, review_map):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    data=tmp_path/'data'; observed,report,run,path,value,seal=_fixture(data,family)
    payload=json.loads(report.read_text())
    native=payload['holding_path_vote_replay'] if family=='holding_vote' else payload
    contract=native['policy_generation']; old='a'*64; current=contract['code_sha256']
    contract['code_sha256']=old
    contract['retry_key']=generation.digest([family,contract['source_generation'],old,contract['source_state']])
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    report.write_text(json.dumps(payload))
    observed=generation.observations(tmp_path,DAY,data_root=data)[0]
    monkeypatch.setattr(handoff,'REVIEWED_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_PRESERVED_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_DEPLOYED_SOURCE_SUCCESSORS',{})
    monkeypatch.setattr(handoff,'REVIEWED_DELAY_SOURCE_SUCCESSORS',{})
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
    assert all(p.read_bytes()==b for p,b in before.items())


@pytest.mark.parametrize('family', ['entry_cancel_wait', 'rising_missed', 'holding_vote', 'auxiliary'])
def test_reviewed_successor_binds_current_family_code(family):
    """Shared handler edits must renew the preserved-report capability review."""
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    assert handoff.REVIEWED_SUCCESSORS[family][1] == generation.code_generation(family)


@pytest.mark.parametrize('family,prior', [
    ('entry_cancel_wait','b2a2017deb606554fbe1c9d481426786b3a8ab463c948ee84cd8ab856eddfca0'),
    ('rising_missed','dde49a32b7299deabf981e9f3a734a9da3019ba3f4e3eb7abbaff91dd3d01fa3'),
])
def test_preserved_oct15_reports_bind_exact_current_capability(family, prior):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    assert handoff.REVIEWED_PRESERVED_SOURCE_SUCCESSORS[family] == (
        prior, generation.code_generation(family))


@pytest.mark.parametrize('damage', [None, 'missing', 'bytes', 'path', 'authority', 'seal', 'symlink'])
def test_successor_requires_preserved_prior_fixture_and_independent_current_fixture(tmp_path, monkeypatch, damage):
    from src.engine.monitoring import policy_generation_code_handoff as handoff
    data=tmp_path/'data'; family='auxiliary'
    _,report,_,_,value,_=_fixture(data,family)
    payload=json.loads(report.read_text());contract=payload['policy_generation']
    old='a'*64; current=contract['code_sha256']
    historical=dict(value,code_sha256=old)
    if damage=='authority':historical['allowed_runtime_apply']=True
    historical['receipt_sha256']=generation.digest({k:v for k,v in historical.items() if k!='receipt_sha256'})
    if damage=='seal':historical['receipt_sha256']='b'*64
    path=data/'report/postclose_generation_validation'/('auxiliary_'+old+'.json')
    path.write_text(json.dumps(historical))
    reference=dict(path=str(path),sha256=validation.file_sha(path))
    contract.update(code_sha256=old,fixture_receipt=reference,
        retry_key=generation.digest([family,contract['source_generation'],old,contract['source_state']]))
    if damage=='path':reference['path']=str(tmp_path/'foreign.json')
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    report.write_text(json.dumps(payload))
    observed=generation.observations(tmp_path,DAY,data_root=data)[0]
    monkeypatch.setattr(handoff,'REVIEWED_SUCCESSORS',{family:(old,current)})
    if damage=='missing':path.unlink()
    elif damage=='bytes':path.write_text('{}')
    elif damage=='symlink':
        other=tmp_path/'historical.json';path.rename(other);path.symlink_to(other)
    before=report.read_bytes()
    result=handoff.current_fixture_observation(observed,data)
    assert result['status']==('verified' if damage is None else 'unverified'),result
    assert report.read_bytes()==before
    if damage is None:
        assert result['preserved_historical_fixture']==reference
        assert result['current_fixture']!=reference
        assert result['native_validated'] is False
        assert result['historical_contract_status']=='unverified'
