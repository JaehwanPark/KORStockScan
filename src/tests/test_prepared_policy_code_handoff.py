"""Prepared code compatibility never supplies PREOPEN or PID authority."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from src.engine.automation import prepared_policy_code_handoff as C
from src.engine.automation import intraday_release_handoff as H
from src.engine.automation import ordered_intraday_deploy as O
from src.engine.infrastructure import runtime_release_router as R

DAY = '2026-10-19'
COMMIT = 'b'*40
ORIGIN = 'a'*40
NOW = datetime(2026,10,17,12,tzinfo=ZoneInfo('Asia/Seoul'))


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    data=tmp_path/'data'; data.mkdir()
    root=tmp_path/'release'; root.mkdir()
    source=root/'consumer.py'; source.write_text('reviewed code\n')
    policy=data/'policy.json'; policy.write_text('{}')
    paths={'consumer.py':'consumer.py'}
    actual=C._digest({'consumer.py':C._sha(source)})
    def write(name, value):
        path=tmp_path/name
        path.write_text(json.dumps(value)); return path
    env=tmp_path/'env'; env.write_text('export TEST=true\n')
    manifest={'target_date':DAY,'selected_release_sha':ORIGIN,
              'pre_submit_delay_handoff':{'target_date':DAY,'policy_sha256':'policy'}}
    manifest['manifest_sha256']=C._digest(manifest)
    mp=write('manifest.json',manifest)
    vp=write('verify.json',{'status':'pass','findings':[], 'manifest_sha256':manifest['manifest_sha256']})
    controller=write('controller.json',{'status':'done'})
    summary=write('summary.json',{'date':'2026-10-16'})
    body=dict(schema='next_preopen_readiness_v1',status='prepared_verified',target_date=DAY,
              selected_release_commit=ORIGIN,actual_pid_consumed=False,runtime_effect=False,
              policy_receipts=[])
    for field,digest,path in [('manifest_path','manifest_file_sha256',mp),('env_path','env_sha256',env),
                             ('verification_path','verification_sha256',vp),
                             ('controller_path','controller_sha256',controller),
                             ('summary_path','summary_sha256',summary)]:
        body[field]=str(path);body[digest]=C._sha(path)
    pp=write('prepared.json',body)
    monkeypatch.setattr(C,'_clock',lambda day,now=None: None)
    monkeypatch.setattr(C,'_policy',lambda *a: (policy,'expected'))
    monkeypatch.setattr(H,'_verify_entry_code_delta',lambda *a: ['consumer.py'])
    monkeypatch.setattr(R,'selected_release',lambda *a: (root,COMMIT))
    monkeypatch.setattr(R,'validate_release',lambda *a: (root,COMMIT))
    monkeypatch.setattr(O,'_main_pids',lambda: [])
    monkeypatch.setattr(O,'_session_absent',lambda: True)
    import subprocess
    monkeypatch.setattr(subprocess,'check_output',lambda *a,**kw: COMMIT+'\n')
    args=dict(family='pre_submit_delay',policy_sha='policy',expected='expected',paths=paths)
    receipt=C.issue(data,DAY,**args,release_root=root,prepared_receipt=pp,
                    origin_verification=vp,confirm=C.AUTHORITY)
    return data,root,args,actual,receipt,pp


def test_future_and_target_day_proof_preserves_policy_without_pid(prepared):
    data,root,args,actual,receipt,pp=prepared
    before=pp.read_bytes()
    proof=C.verify(data,DAY,**args,actual=actual)
    assert proof['verification_basis']==C.SCHEMA
    assert proof['policy_effect']=='unchanged' and proof['actual_pid_consumed'] is False
    assert pp.read_bytes()==before


@pytest.mark.parametrize('fault',['runtime','policy','expected','source','receipt','origin','symlink'])
def test_invalid_binding_never_uses_prepared_code_authority(prepared,fault):
    data,root,args,actual,receipt,pp=prepared
    args=dict(args)
    if fault=='runtime': (root/'consumer.py').write_text('changed')
    elif fault=='policy': args['policy_sha']='different'
    elif fault=='expected': args['expected']='different'
    elif fault=='source': (data/'policy.json').write_text('{"changed":true}')
    elif fault=='origin':
        Path(receipt['historical_snapshots'][str(pp)]).write_text('changed')
    else:
        path=C.receipt_path(data,DAY,COMMIT,'pre_submit_delay')
        if fault=='receipt':
            receipt['actual_pid_consumed']=True;receipt['receipt_sha256']=C._digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
            path.write_text(json.dumps(receipt))
        else:
            target=path.with_suffix('.saved');path.rename(target);path.symlink_to(target)
    with pytest.raises(ValueError): C.verify(data,DAY,**args,actual=actual)


def test_missing_receipt_keeps_ordinary_native_path(tmp_path,monkeypatch):
    monkeypatch.setattr(R,'selected_release',lambda *a: (tmp_path,COMMIT))
    assert C.verify(tmp_path,DAY,family='main_stop',policy_sha='x',expected='x',paths={},actual='x') is None


def test_target_expiry_is_not_renewed():
    C._clock(DAY,NOW)
    C._clock(DAY,NOW.replace(day=19))
    with pytest.raises(ValueError,match='expired'):C._clock(DAY,NOW.replace(day=20))


def test_origin_rejects_modified_prepared_hashes(prepared):
    data,root,args,actual,receipt,pp=prepared
    body=json.loads(pp.read_text());body['manifest_file_sha256']='0'*64;pp.write_text(json.dumps(body))
    with pytest.raises(ValueError):C._origin(pp,args['family'],DAY)


def test_original_closure_can_advance_without_rewriting_historical_authority(prepared):
    data,root,args,actual,receipt,pp=prepared
    body=json.loads(pp.read_text())
    Path(body['controller_path']).write_text('{"status":"new generation"}')
    assert C.verify(data,DAY,**args,actual=actual)['actual_pid_consumed'] is False
    # The current policy remains independently pinned despite historical retention.
    (data/'policy.json').write_text('{"different":true}')
    with pytest.raises(ValueError):C.verify(data,DAY,**args,actual=actual)


def test_native_code_inventory_accepts_utils_paths_and_rejects_escape(tmp_path):
    import subprocess
    import hashlib
    root=tmp_path/'repo';root.mkdir()
    own=root/'src/engine/automation/intraday_release_handoff.py'
    own.parent.mkdir(parents=True);own.write_bytes(Path(H.__file__).read_bytes())
    utility=root/'src/utils/market_day.py';utility.parent.mkdir();utility.write_text('value = 1\n')
    subprocess.run(['git','init','-q',str(root)],check=True)
    subprocess.run(['git','-C',str(root),'add','.'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Test','-c','user.email=test@example.invalid',
                    'commit','-qm','fixture'],check=True)
    commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    expected=C._digest({'market_day':hashlib.sha256(utility.read_bytes()).hexdigest()})
    assert H._verify_entry_code_delta(root,commit,commit,
        {'market_day':'src/engine/../utils/market_day.py'},expected)==[]
    (tmp_path/'outside.py').write_text('private fixture\n')
    with pytest.raises(ValueError,match='outside_release'):
        H._verify_entry_code_delta(root,commit,commit,{'outside':'../outside.py'},expected)


@pytest.mark.parametrize('family,expected', [
    ('pre_submit_delay', 'bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256'),
    ('holding_vote', '6c664915b34289cddceeaf20399cce45f5e9e3f3373fdeae885910043f343112'),
    ('main_stop', '687c06b51d0e4b581f1927151b31483d5f979e438cc67a726e6718f84bead533'),
])
def test_delay_research_exact_original_policy_inventory_is_preserved(monkeypatch, family, expected):
    """Bind reviewed bytes to the real frozen origin, without issuing a receipt."""
    import hashlib
    from src.engine.scalping import pre_submit_delay_initial_policy as delay
    from src.engine.scalping import holding_vote_experiment as holding
    from src.engine.scalping import main_stop_policy as stop
    root = Path(H.__file__).resolve().parents[3]
    origin = '7f2552aedde8fec6ef904a43105827907e50dfc8'
    candidate = 'b' * 40
    paths = ({name:name for name in delay.CONTRACT_PATHS} if family == 'pre_submit_delay'
             else {name:'src/engine/'+name for name in
                   (holding._code_paths() if family == 'holding_vote' else stop.implementation_paths())})
    real_git = H.subprocess.check_output
    def fixture_revision(command, **kwargs):
        revision, name = command[-1].split(':', 1)
        return (root/name).read_bytes() if revision == candidate else real_git(command, **kwargs)
    monkeypatch.setattr(H.subprocess, 'check_output', fixture_revision)
    before = {name:(root/name).read_bytes() for name in paths.values()}
    changed = H._verify_entry_code_delta(root, candidate, origin, paths, expected)
    assert 'src/engine/sniper_state_handlers.py' in changed
    assert before == {name:(root/name).read_bytes() for name in paths.values()}
    if family == 'pre_submit_delay':
        extensions = H.REVIEWED_DELAY_CONTRACT_EXTENSIONS[(origin, expected)]
        assert set(extensions) == {'src/engine/pipeline_event_summary.py', 'src/utils/threshold_cycle_registry.py'}
        assert all(hashlib.sha256((root/name).read_bytes()).hexdigest() == digest
                   for name, digest in extensions.items())
        for name, pair in H.REVIEWED_DELAY_RESEARCH_SOURCES.items():
            prior = real_git(['git', '-C', str(root), 'show', origin+':'+name])
            assert pair == (hashlib.sha256(prior).hexdigest(),
                            hashlib.sha256((root/name).read_bytes()).hexdigest())
