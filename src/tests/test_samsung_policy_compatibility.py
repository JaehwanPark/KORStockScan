from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

import pytest
from src.engine.scalping import samsung_policy_compatibility as K
from src.engine.scalping import entry_designated_policy as D
from src.engine.scalping import entry_admission_recipe as A
from src.engine.scalping import entry_admission_analysis as H
from src.engine.scalping import mechanistic_entry_runtime_policy as M
from src.engine.scalping import entry_setup_evidence as E
from src.tests.test_entry_strategy_policy import policy


def test_component_migration_requires_explicit_sealed_receipt(tmp_path):
    old=policy();new=A.candidate_policy(old);frozen=dict(parent_policy=old,parent_sha256=D.S.digest(old))
    with pytest.raises(ValueError,match='parent_changed'):
        K.effective_policy(tmp_path,frozen,bundle=dict(machine_policy=new))
    value=D.seal(dict(frozen_sha256=D.S.digest(frozen),old_parent=old,new_parent=new))
    path=K.path(tmp_path,frozen);path.parent.mkdir(parents=True);path.write_text(json.dumps(value))
    # A self hash and component equality alone cannot substitute for replay
    # and original/new kernel provenance.
    with pytest.raises(ValueError):K.effective_policy(tmp_path,frozen,bundle=dict(machine_policy=new))
    bad=deepcopy(new);bad['unknown_guard']=False
    with pytest.raises(ValueError):K.effective_policy(tmp_path,frozen,bundle=dict(machine_policy=bad))


def test_guard_projection_only_removes_policy_identity_metadata():
    old=dict(action='BLOCK',liquidity_threshold_pass=False,strategy_selection=dict(policy_sha256='old',effective_thresholds={'min':1}))
    new=deepcopy(old);new['strategy_selection']['policy_sha256']='new';new['admission_recipe']={'changed':False}
    assert K.decision_projection(old)==K.decision_projection(new)
    new['liquidity_threshold_pass']=True
    assert K.decision_projection(old)!=K.decision_projection(new)


def test_capture_resolves_its_own_bundle_and_checks_activation_and_action(tmp_path,monkeypatch):
    old=policy();frozen=dict(parent_policy=old,parent_sha256=D.S.digest(old));sha='a'*64
    bundle=dict(bundle_sha256=sha,target_date='2026-10-06',machine_policy=old,
        strategy_activation=dict(effective_from='2026-10-06T08:50:00+09:00'))
    path=M.root(tmp_path/'data')/'generations'/(sha+'.json');path.parent.mkdir(parents=True);path.write_text(json.dumps(bundle))
    monkeypatch.setattr(M,'validate',lambda *a,**k:None)
    monkeypatch.setattr(M,'_validate_bundle_sources',lambda b,*a:b)
    monkeypatch.setattr(E,'mechanistic_entry_policy_decision',lambda *a,**k:dict(action='RECHECK'))
    row=dict(bundle_sha256=sha,decision_ts='2026-10-06T09:00:00+09:00',setup_evidence={},machine_action='RECHECK')
    assert K.source_bundle(tmp_path,frozen,row)==bundle
    for mutation in [dict(machine_action='ENTER_NOW'),dict(decision_ts='2026-10-06T08:40:00+09:00'),dict(bundle_sha256='b'*64)]:
        with pytest.raises((ValueError,OSError)):
            K.source_bundle(tmp_path,frozen,{**row,**mutation})


def test_complete_migration_preserves_old_kernel_and_rejects_bad_parity(tmp_path):
    old=policy();new=A.candidate_policy(old)
    kernel=tmp_path/'old.py';kernel.write_text('original kernel\n')
    digest=H.file_sha(kernel);frozen=dict(parent_policy=old,parent_sha256=D.S.digest(old),kernel_manifest={str(kernel):digest})
    parity=D.seal(dict(observation_count=519,old_parent_sha256=D.S.digest(old),new_parent_sha256=D.S.digest(new),
        action_guard_difference_count=0,raw_manifest=[dict(trace=str(i),raw_sha256='a'*64) for i in range(519)]))
    proof=tmp_path/'parity.json';proof.write_text(json.dumps(parity))
    migration=D.seal(dict(schema=K.SCHEMA,frozen_sha256=D.S.digest(frozen),old_kernels=frozen['kernel_manifest'],
        new_kernels=frozen['kernel_manifest'],migration_kernel_sha256=H.file_sha(K.__file__),old_parent=old,new_parent=new,
        runtime_apply_allowed=False,parity_path=str(proof),parity_file_sha256=H.file_sha(proof),
        old_kernel_archives=[dict(key=str(kernel),path=str(kernel),sha256=digest)]))
    path=K.path(tmp_path,frozen);path.parent.mkdir(parents=True);path.write_text(json.dumps(migration))
    assert K.effective_policy(tmp_path,frozen,bundle=dict(machine_policy=new))==new
    parity['action_guard_difference_count']=1;proof.write_text(json.dumps(D.seal(parity)))
    migration['parity_file_sha256']=H.file_sha(proof);path.write_text(json.dumps(D.seal(migration)))
    with pytest.raises(ValueError,match='parity_invalid'):
        K.effective_policy(tmp_path,frozen,bundle=dict(machine_policy=new))
