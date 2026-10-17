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
