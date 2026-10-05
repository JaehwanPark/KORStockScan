from copy import deepcopy
from datetime import datetime
import json

import pytest
from src.engine.scalping import entry_designated_policy as D
from src.engine.scalping import entry_admission_analysis as H
from src.engine.scalping import entry_admission_recipe as A
from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import mechanistic_entry_runtime_policy as M
from src.engine.scalping import ai_action_outcome_calibration as C
from src.tests.test_entry_admission_acceptance import observations

NOW = datetime(2026, 10, 5, 20, tzinfo=M.KST)


@pytest.fixture
def staged_request(tmp_path):
    bootstrap = tmp_path / 'bootstrap.json'
    C._atomic_write_json(bootstrap, C._with_artifact_content_sha256(dict(schema=C.SCHEMA,
        target_date='2026-09-11', clean_tuning_baseline_date='2026-06-05',
        mechanistic_entry_refinement=dict(policy_candidate=None, promotion_pass=False),
        mechanistic_flow_groups=dict(source_population=dict(accepted_unique_trace_count=15)))))
    previous = M.publish(bootstrap, data_root=tmp_path, bootstrap=True,
        now=datetime(2026, 9, 13, 20, tzinfo=M.KST))
    previous['machine_policy'] = S.seed(previous['machine_policy'], ('KRX', 'KRX_REGULAR'))
    previous['machine_policy']['entry_situation_veto'] = C._winrate_veto_payload(68.75)
    previous['bundle_sha256'] = S.digest({k:v for k,v in previous.items() if k != 'bundle_sha256'})
    for path in [M.root(tmp_path) / 'policy_2026-09-14.json', M.root(tmp_path) / 'generations' / (previous['bundle_sha256']+'.json')]:
        M._atomic_write_json(path, previous)
    analysis = H.build_report([], parent=previous['machine_policy'], target_date='2026-10-02', data_root=tmp_path)
    analysis['observations'] = observations(('2026-09-29', '2026-10-02'))
    analysis = D.seal(analysis)
    report = C.build_winrate_policy_report([], source_receipt=dict(target_date='2026-10-02',
        machine_threshold_tuning_input_allowed=True), target_date='2026-10-02', data_root=tmp_path,
        publication_day='2026-10-05', admission_recipe_id=A.RECIPE_ID, admission_analysis=analysis)
    report_path = tmp_path / 'report.json'; M._atomic_write_json(report_path, report)
    M.stage_winrate_policy(report_path, data_root=tmp_path, now=NOW)
    before = M.load(data_root=tmp_path, target_date=D.TARGET)
    req = D.make_request(report_path, previous=previous, superseded=before,
        request_id='test-designation-1006', authorization=dict(user_instruction='계획 실행', plan_path='reviewed-plan'),
        review=dict(unresolved_in_scope_defects=0, targeted_validation='passed', evidence_sha256='a'*64))
    path = tmp_path / 'request.json'; M._atomic_write_json(path, req)
    return tmp_path, path, req, report, previous, before


def test_designation_preserves_auto_result_and_is_idempotent(staged_request):
    root, path, req, report, previous, before = staged_request
    result = D.stage(path, data_root=root, now=NOW)
    after = M.load(data_root=root, target_date=D.TARGET)
    assert result['status'] == 'designated_policy_staged'
    assert after['machine_policy'] == A.candidate_policy(previous['machine_policy'])
    assert after['ai_policy'] == before['ai_policy']
    assert M.load_effective(data_root=root, target_date='2026-10-05') == previous
    assert report['candidate_selected'] is False and report['fresh_validation'] == 'not_observed'
    assert D.stage(path, data_root=root, now=NOW)['status'] == 'already_staged'
    assert D.binding_valid(report, after, root)
    assert M.stage_winrate_policy(root/'report.json',data_root=root,now=NOW)['status'] == 'operator_designation_preserved'
    assert M._read(M.root(root)/'generations'/(before['bundle_sha256']+'.json')) == before


@pytest.mark.parametrize('broken', [False, True])
def test_designation_follows_dated_descendants_without_skipping_lineage(staged_request, broken):
    root, path, req, report, previous, before = staged_request
    descendant = deepcopy(before)
    descendant['previous_bundle_sha256'] = before['bundle_sha256'] if not broken else 'f'*64
    descendant['bundle_sha256'] = S.digest({k:v for k,v in descendant.items() if k != 'bundle_sha256'})
    M._atomic_write_json(M.root(root)/('policy_'+D.TARGET+'.json'), descendant)
    req['supersedes_bundle_sha256'] = descendant['bundle_sha256']
    M._atomic_write_json(path,D.seal(req))
    if broken:
        with pytest.raises(ValueError,match='lineage_generation_missing'):
            D.stage(path,data_root=root,now=NOW)
    else:
        result = D.stage(path,data_root=root,now=NOW)
        assert result['status']=='designated_policy_staged'
        assert M.load(data_root=root,target_date=D.TARGET)['ai_policy']==descendant['ai_policy']
        generation=M.root(root)/'generations'/(before['bundle_sha256']+'.json')
        generation.unlink()
        with pytest.raises(ValueError,match='lineage_generation_missing'):
            M.load(data_root=root,target_date=D.TARGET)


@pytest.mark.parametrize('field,value', [('target_date','2026-10-07'),('evidence_qualified_selection',True),
    ('supersedes_bundle_sha256','f'*64),('parent_bundle_sha256','f'*64),
    ('authorization',dict(user_instruction='no approval')), ('validation_status','passed')])
def test_invalid_request_rejected(staged_request, field, value):
    root,path,req,*_ = staged_request
    req[field]=value; M._atomic_write_json(path,D.seal(req))
    with pytest.raises(ValueError):D.stage(path,data_root=root,now=NOW)


def test_closed_window_rejects_new_designation(staged_request):
    root,path,*_ = staged_request
    with pytest.raises(ValueError,match='window_closed'):
        D.stage(path,data_root=root,now=NOW.replace(day=6))


def test_interrupted_pointer_write_blocks_load_and_recovers(staged_request, monkeypatch):
    root,path,*_ = staged_request
    original=M._atomic_write_json
    def fail(p,v):
        if p.name.startswith('test-designation') and v.get('state')=='committed':
            raise OSError('injected crash after pointer replace')
        return original(p,v)
    monkeypatch.setattr(M,'_atomic_write_json',fail)
    with pytest.raises(OSError):D.stage(path,data_root=root,now=NOW)
    with pytest.raises(ValueError,match='transaction_incomplete'):M.load(data_root=root,target_date=D.TARGET)
    monkeypatch.setattr(M,'_atomic_write_json',original)
    D.stage(path,data_root=root,now=NOW)
    assert M.load(data_root=root,target_date=D.TARGET)['machine_disposition']=='operator_designated'


def test_changed_request_cannot_resume(staged_request):
    root,path,req,*_ = staged_request
    D.stage(path,data_root=root,now=NOW)
    req['review']['evidence_sha256']='b'*64; M._atomic_write_json(path,D.seal(req))
    with pytest.raises(ValueError,match='reused'):D.stage(path,data_root=root,now=NOW)


def pair_rows(parent):
    p=D.pair(parent,parent_bundle_sha256='b'*64,request_id='fixed-pair-test')
    rows=observations(('2026-10-06','2026-10-07'))
    for row in rows:row.update(post_apply=True,actual_policy_sha256=p['candidate_sha256'],actual_action=row['candidate_action'],captured_action=row['candidate_action'],activation_receipt_sha256='c'*64)
    return p,rows


def test_fixed_pair_both_directions_and_no_preservation_veto(staged_request):
    parent=staged_request[4]['machine_policy'];p,rows=pair_rows(parent)
    result=D.evaluate(dict(observations=rows),p,parent,target_date='2026-10-07')
    assert result['candidate_selected'] and result['challenger_arm']=='candidate'
    assert result['windows']['latest']['retention_diagnostic']['excluded_wins']==1
    inverse=deepcopy(rows)
    for r in inverse:r['parent_action'],r['candidate_action']=r['candidate_action'],r['parent_action']
    reverse=D.evaluate(dict(observations=inverse),p,p['candidate_policy'],target_date='2026-10-07')
    assert reverse['candidate_selected'] and reverse['challenger_arm']=='baseline'
    assert reverse['cumulative_dates']==['2026-10-06','2026-10-07']


def test_missing_latest_or_cumulative_evidence_carries_actual_incumbent(staged_request):
    parent=staged_request[4]['machine_policy'];p,rows=pair_rows(parent)
    for r in rows:r['post_apply']=False
    result=D.apply(dict(target_date='2026-10-07'),dict(observations=rows),p['candidate_policy'],p)
    assert result['disposition']=='incumbent_carried' and result['candidate_policy'] is None
    assert result['activation_parent_sha256']==p['candidate_sha256']
    rows=observations(('2026-10-02',))
    for r in rows:r.update(post_apply=True,actual_policy_sha256=p['candidate_sha256'],actual_action=r['candidate_action'],captured_action=r['candidate_action'],activation_receipt_sha256='c'*64)
    assert not D.evaluate(dict(observations=rows),p,parent,target_date='2026-10-07')['candidate_selected']


def test_samsung_component_diff_exact(staged_request):
    parent=staged_request[4]['machine_policy'];candidate=A.candidate_policy(parent)
    assert D.samsung_equivalent(parent,candidate)
    candidate['unapproved_guard']=False
    assert not D.samsung_equivalent(parent,candidate)


def test_pair_ends_for_unregistered_c1(staged_request):
    parent=staged_request[4]['machine_policy'];p,rows=pair_rows(parent)
    changed={**parent,'unregistered':'C1'}
    with pytest.raises(ValueError,match='outside_registered_pair'):
        D.evaluate(dict(observations=rows),p,changed,target_date='2026-10-07')


def test_designated_activation_and_later_generator_publisher_loader(staged_request, monkeypatch):
    root,path,req,report,previous,_ = staged_request
    D.stage(path,data_root=root,now=NOW)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return datetime(2026,10,6,20,tzinfo=M.KST)
    monkeypatch.setattr(M,'datetime',Clock);monkeypatch.setattr(C,'datetime',Clock)
    activated=M.activate_dated_winrate_policy(data_root=root,target_date=D.TARGET,
        now=datetime(2026,10,6,9,tzinfo=M.KST))
    assert activated['status']=='activated'
    current=M.load_effective(data_root=root,target_date=D.TARGET);p=current['designated_pair']
    receipt=M._read(M.root(root)/'designated'/('activation_'+p['request_id']+'.json'))
    rows=observations(('2026-10-06',))
    for row in rows:
        row['parent_action'],row['candidate_action']=row['candidate_action'],row['parent_action']
        row.update(post_apply=True,actual_policy_sha256=p['candidate_sha256'],
            captured_action=row['candidate_action'],actual_action=row['candidate_action'],
            activation_receipt_sha256=receipt['artifact_content_sha256'],source_bundle_sha256=current['bundle_sha256'])
    analysis=H.build_report([],parent=current['machine_policy'],target_date='2026-10-06',data_root=root,designated_pair=p)
    analysis['observations']=rows;analysis=D.seal(analysis)
    result=C.build_winrate_policy_report([],source_receipt=dict(target_date='2026-10-06',machine_threshold_tuning_input_allowed=True),
        target_date='2026-10-06',data_root=root,publication_day='2026-10-06',admission_recipe_id=A.RECIPE_ID,admission_analysis=analysis)
    assert result['candidate_selected'] and result['candidate_policy']==p['baseline_policy']
    assert result['fixed_pair_comparison']['challenger_arm']=='baseline'
    report_path=root/'postapply.json';M._atomic_write_json(report_path,result)
    staged=M.stage_winrate_policy(report_path,data_root=root,publication_day='2026-10-06',now=Clock.now())
    assert staged['status']=='staged'
    loaded=M.load(data_root=root,target_date='2026-10-07')
    assert loaded['machine_policy']==p['baseline_policy']
    assert M.stage_winrate_policy(report_path,data_root=root,publication_day='2026-10-06',now=Clock.now())['status']=='already_staged'
    assert receipt['actual_pid_consumption'] is False
    assert M.activate_dated_winrate_policy(data_root=root,target_date=D.TARGET,now=Clock.now())['status']=='already_active'


def test_post_apply_cannot_be_asserted_from_calendar_alone(staged_request):
    parent=staged_request[4]['machine_policy'];p,rows=pair_rows(parent)
    rows[0].pop('activation_receipt_sha256')
    with pytest.raises(ValueError,match='consumption_unproven'):
        D.evaluate(dict(observations=rows),p,parent,target_date='2026-10-07')


def test_generation_cache_checks_every_bound_dependency(staged_request,monkeypatch):
    root,path,req,report,previous,_=staged_request
    D.stage(path,data_root=root,now=NOW)
    sha=previous['bundle_sha256']
    calls=[];original=M._validate_bundle_sources
    def counting(*args,**kwargs):
        calls.append(args[0]['bundle_sha256']);return original(*args,**kwargs)
    monkeypatch.setattr(M,'_validate_bundle_sources',counting)
    assert D.validated_generation(root,sha)['bundle_sha256']==sha
    assert D.validated_generation(root,sha)['bundle_sha256']==sha
    assert calls.count(sha)==1
    source=M.root(root)/'sources'/(previous['source_file_sha256']+'.json')
    source.write_text(source.read_text()+' ')
    with pytest.raises(ValueError,match='dependency_changed'):D.validated_generation(root,sha)


def test_operator_rollback_after_designation_drops_stale_selection_proof(staged_request,monkeypatch):
    root,path,req,report,previous,_=staged_request
    D.stage(path,data_root=root,now=NOW)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None):return datetime(2026,10,6,20,tzinfo=M.KST)
    monkeypatch.setattr(M,'datetime',Clock)
    adopted=M.activate_dated_winrate_policy(data_root=root,target_date=D.TARGET,now=Clock.now())
    result=M.rollback_machine_component(previous['bundle_sha256'],data_root=root,now=Clock.now())
    assert result['status']=='machine_component_rolled_back'
    current=M.load_effective(data_root=root,target_date=D.TARGET)
    assert current['machine_policy']==previous['machine_policy']
    assert current['ai_policy']==previous['ai_policy']
    assert 'designated_pair' not in current and 'winrate_selection' not in current
    assert current['strategy_activation']['rollback_scopes']==['KRX|KRX_REGULAR']

    M.rollback_machine_component(adopted['bundle_sha256'],data_root=root,now=Clock.now())
    restored=M.load_effective(data_root=root,target_date=D.TARGET)
    assert restored['machine_policy']==A.candidate_policy(previous['machine_policy'])
    assert restored['winrate_selection']['disposition']=='operator_designated'
