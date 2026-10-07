"""Native v4 input, full owner census, incremental storage and report readers."""
import copy
import gzip
import json
from pathlib import Path
import pytest
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal_shared_ledger as L
from src.engine.scalping import continuous_reversal_path_postclose as PC
from src.engine.scalping import continuous_reversal_policy_v4 as V
from src.tests.test_reversal_path_policy import state, row, feed, C, R, P, AUX
from src.tests.test_continuous_reversal_policy_v3 import native, migrated_reports
from src.tests.test_offline_comparison_store import activate


@pytest.fixture
def comparison(native, monkeypatch, request):
    root, parent, _, _ = native
    machine, aux = migrated_reports(native)
    machine = copy.deepcopy(machine); base = copy.deepcopy(machine['cells'])
    alias = getattr(request, 'param', 'SA')
    bid = C.ALIASES[alias] if alias != 'legacy' else 'legacy_all_v1'
    monkeypatch.setattr(C,'matches',lambda *a:True)
    symbol = {'SA':'005930','SB':'005930','DA':'034020','HA':'403870',
              'HB':'403870','AA':'196170','JA':'036930','GA':'000001','legacy':'005930'}[alias]
    values = [row(i) for i in range(62)] + [row(62, 100.3)]
    if alias in {'SB','AA','HA','legacy'}:
        values = [row(i) for i in range(61)] + [row(61,102),row(62,100),row(63,101)]
        if alias not in {'HA','legacy'}:values += [row(64,100),row(65,102)]
    if alias == 'GA':values += [row(63,100.3)]
    for r in values:
        r[9] = symbol + '_AL'
        if alias == 'GA':
            for column in (3,4,5):r[column] *= 500
    st = R.State(branch_ids=[bid],offline=True,session_anchor=values[0])
    for r in values:st.observe(r,symbol=symbol,venue='SOR',session='SOR_REGULAR')
    event, source = st.snapshot(st.ready[-1]); signal = event['branch_signals'][bid]
    key = C.cell_key(symbol, 'REGULAR', event['confirmation_price'])
    selected = next(c for c in machine['cells'] if c['key'] == key)['routes']['SOR']
    selected.update(payload=R.B.payload([C.branch(bid)]), local_metrics=dict(wins=1,resolved=1), branch_metrics={bid:dict(wins=1,resolved=1)})
    selected['payload_sha256'] = P.digest(selected['payload'])
    point = dict(canonical_id=event['canonical_opportunity_id'], event=event, entry_index=len(values)-1,
                 branch_hits=[bid], confirmed_signals={bid:signal}, path_inputs={bid:source['branch_inputs'][bid]}, outcome=dict(status='WIN'))
    raw = root/'raw.gz'; raw.write_bytes(gzip.compress(json.dumps(dict(symbols={symbol:values})).encode()))
    part = root/'points.gz'; part.write_bytes(gzip.compress((json.dumps(point)+'\n').encode()))
    rec = dict(path=str(raw), sha256=P.file_hash(raw), day='2026-10-07', session='SOR_REGULAR', venue='SOR')
    population = P.seal(dict(partitions=[dict(path=str(part),sha256=P.file_hash(part),normalized_source=rec)]))
    pop = root/'population.json'; P.write(pop,population)
    machine = P.seal(dict(machine, schema=PC.SCHEMA, baseline_cells=base, baseline_auxiliary_cells=aux['cells'],
                         population_path=str(pop), applied_history=dict(consumed_versions=[])))
    P.write(root/'report/continuous_reversal_registered/v4/2026-10-07/current-run.json', P.seal(dict(run_sha256='e'*64)))
    P.write(PC.directory(root,'2026-10-07')/'machine-comparison.json', machine)
    with S.Store(root) as store: activate(store)
    return root, parent, machine, point


def transport(req, timeout_sec):
    return dict(provider_provenance=dict(response_id='fixture-'+req['paired_replay_id']), candidate_response=dict(
        schema='entry_setup_risk_adjudication_v1', risk_verdict='PASS', risk_codes=['NO_BLOCKING_RISK'],
        supporting_fact_ids=['observed_machine_signal'], contradicting_fact_ids=[], confidence=50))


def test_native_requests_shared_projection_reuse_and_no_repeat_calls(comparison, monkeypatch):
    root, parent, machine, point = comparison
    census = L.prepare_inputs(PC,root,'2026-10-07',machine)
    assert census['census']['eligible_requests'] == 5
    declarations=list(L.eligible(PC,machine,json.loads(Path(machine['population_path']).read_text())))
    expected=list(L.project_partition(PC,json.loads(Path(machine['population_path']).read_text())['partitions'][0],{point['canonical_id']:declarations},L.directory(PC,root,'2026-10-07')))[0]
    with S.Store(root) as store:
        before=store.db.execute('SELECT count(*) FROM objects').fetchone()[0]
        actual={r[2]:store.request(r[6]) for r in store.owners(machine['artifact_content_sha256'])}
        assert actual == {a:PC.request(expected,a) for a in AUX.ARMS}
    monkeypatch.setattr(L,'project_partition',lambda *a: (_ for _ in ()).throw(AssertionError('must use cached projection')))
    monkeypatch.setattr(PC,'request',lambda *a: (_ for _ in ()).throw(AssertionError('must use cached request refs')))
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    with S.Store(root) as store:
        assert store.db.execute('SELECT count(*) FROM objects').fetchone()[0] == before
    result=L.calls(PC,root,'2026-10-07',transport=transport)
    assert result['new_calls']==5 and result['call_limit'] is None
    assert L.calls(PC,root,'2026-10-07',transport=transport)['new_calls']==0


def test_missing_expected_input_cannot_publish_smaller_population(comparison,monkeypatch):
    root,_,machine,_=comparison
    monkeypatch.setattr(L,'project_partition',lambda *a:iter(()))
    with pytest.raises(ValueError,match='expected_population_input_mismatch'):L.prepare_inputs(PC,root,'2026-10-07',machine)
    assert not (L.directory(PC,root,'2026-10-07')/'input-census.json').exists()


def test_report_preserves_native_selection_and_frozen_reader(comparison):
    root,parent,machine,_=comparison
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    L.calls(PC,root,'2026-10-07',transport=transport)
    aux=L.auxiliary_report(PC,root,'2026-10-07','2026-10-07',parent,publish_policy=False)
    assert aux['comparison_complete'] and aux['owner_request_census']['expected']==5
    assert aux['owner_request_census']['completed']==5
    issued=json.loads((L.directory(PC,root,'2026-10-07')/'machine.json').read_text())
    bundle=V.stage(root,'2026-10-07','2026-10-07',issued,aux,target_date='2026-10-08',release_commit='a'*40)
    V.validate_sources(bundle,root)
    before=P.file_hash(Path(aux['results_sources'][0]['path']))
    # Mutable later census changes do not invalidate the frozen publication.
    P.write(L.directory(PC,root,'2026-10-07')/'input-census.json',{'later':'changed'})
    V.validate_sources(bundle,root)
    assert P.file_hash(aux['results_sources'][0]['path']) == before


def test_timeout_stays_uncertain_and_missing_census_fails_before_transport(comparison):
    root,_,machine,_=comparison
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    def timeout(*args,**kwargs): raise TimeoutError()
    result=L.calls(PC,root,'2026-10-07',transport=timeout)
    assert result['census']=={'reserved':5}
    assert L.calls(PC,root,'2026-10-07',transport=transport)['new_calls']==0
    census=L.directory(PC,root,'2026-10-07')/'input-census.json'
    value=json.loads(census.read_text()); value['machine_report_sha256']='0'*64; P.write(census,value)
    with pytest.raises((ValueError,FileNotFoundError)):L.calls(PC,root,'2026-10-07',transport=transport)


def test_label_revision_reuses_requests_and_replaces_counts(comparison):
    root,_,machine,point=comparison
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    L.calls(PC,root,'2026-10-07',transport=transport)
    with S.Store(root) as store:
        first=store.snapshot(machine['artifact_content_sha256'])
        metrics,*_=L.comparison_metrics(store,PC,first)
        assert sum(m['pass_wins'] for arms in metrics.values() for m in arms.values())==5
    poppath=Path(machine['population_path']); population=json.loads(poppath.read_text())
    point['outcome']['status']='FAIL'; part=Path(population['partitions'][0]['path'])
    part.write_bytes(gzip.compress((json.dumps(point)+'\n').encode()))
    population['partitions'][0]['sha256']=P.file_hash(part);P.write(poppath,P.seal(population))
    changed=P.seal(dict(machine,label_revision=2))
    L.prepare_inputs(PC,root,'2026-10-07',changed)
    assert L.calls(PC,root,'2026-10-07',transport=transport)['new_calls']==0
    with S.Store(root) as store:
        assert store.db.execute('SELECT count(*) FROM requests').fetchone()[0]==5
        metrics,*_=L.comparison_metrics(store,PC,store.snapshot(changed['artifact_content_sha256']))
        assert sum(m['pass_wins'] for arms in metrics.values() for m in arms.values())==0
        assert sum(m['pass_count'] for arms in metrics.values() for m in arms.values())==5
        original,*_=L.comparison_metrics(store,PC,first)
        assert sum(m['pass_wins'] for arms in original.values() for m in arms.values())==5


def test_unrelated_report_day_reuses_request_and_membership_objects(comparison):
    root,_,machine,_=comparison
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    with S.Store(root) as store:
        before={t:store.db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('requests','members','partitions')}
    changed=P.seal(dict(machine,publication_date='2026-10-08'))
    L.prepare_inputs(PC,root,'2026-10-07',changed)
    with S.Store(root) as store:
        assert {t:store.db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in before}==before


def test_cutover_staging_cannot_call_provider(comparison):
    root,_,machine,_=comparison
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    with S.Store(root) as store:
        value=store.activation();value['writer_enabled']=False;S.atomic_json(store.root/'current.json',value)
    with pytest.raises(ValueError,match='fence_incomplete'):
        L.calls(PC,root,'2026-10-07',transport=lambda *a,**k:pytest.fail('provider must not be called'))


def test_v3_owner_contract_does_not_gain_v4_consumed_version_owners(monkeypatch):
    from src.engine.scalping import continuous_reversal_registered_postclose as old
    key='samsung|REGULAR|ALL';bid='legacy_all_v1';other=R.B.BRANCH
    cell=dict(payload=R.B.payload([old.C.branch(bid)]),branch_metrics={bid:dict(wins=1,resolved=1)})
    cells=[dict(key=key,routes=dict(SOR=cell))]
    consumed=dict(payload=R.B.payload([old.C.branch(other)]),branch_metrics={other:dict(wins=1,resolved=1)})
    machine=dict(cells=cells,baseline_cells=cells,applied_history=dict(consumed_versions=[dict(family_sha256='new',machine_cells={key:dict(routes=dict(SOR=consumed))})]))
    point=dict(canonical_id='point',event=dict(symbol='005930',market='REGULAR',confirmation_price=100,venue='SOR'),branch_hits=[bid,other],outcome=dict(status='WIN'))
    monkeypatch.setattr(old,'iter_points',lambda *a:iter([point]))
    values=list(L.eligible(old,machine,{}))
    assert len(values)==1 and values[0]['branch_id']==bid
    assert values[0]['owners']==['selected','applied_baseline']


def test_duplicate_native_point_does_not_expand_expected_requests(comparison):
    root,_,machine,point=comparison
    path=Path(machine['population_path']); pop=json.loads(path.read_text());part=Path(pop['partitions'][0]['path'])
    part.write_bytes(gzip.compress(((json.dumps(point)+'\n')*2).encode()))
    pop['partitions'][0]['sha256']=P.file_hash(part);P.write(path,P.seal(pop))
    machine=P.seal(dict(machine,duplicate_fixture=True))
    census=L.prepare_inputs(PC,root,'2026-10-07',machine)
    assert census['census']['eligible_requests']==5


def test_public_auxiliary_api_uses_shared_adapter(comparison,monkeypatch):
    root,parent,machine,_=comparison
    monkeypatch.setattr(PC,'active',lambda *a:parent)
    monkeypatch.setattr(L,'auxiliary_report',lambda backend,*a,**k:{'backend':backend.__name__,'storage':'shared'})
    result=P.auxiliary_report(root,'2026-10-07','2026-10-07',publish_policy=False)
    assert result=={'backend':PC.__name__,'storage':'shared'}


def test_stage_fingerprint_tracks_shared_storage_code(tmp_path,monkeypatch):
    from src.engine.automation import postclose_summary_handoff as H
    def paths_digest(paths):return {k:str(v) for k,v in paths.items()}
    monkeypatch.setattr(H,'_stage_sources',paths_digest)
    monkeypatch.setattr(H,'_stage_digest',lambda v:v)
    result=H._stage_code('main_auxiliary_policy',[],tmp_path)
    assert result['shared_comparison_adapter'].endswith('scalping/continuous_reversal_shared_ledger.py')
    assert result['offline_comparison_store'].endswith('ai/offline_comparison_store.py')
    assert 'offline_comparison_store' not in H._stage_code('main_machine_policy',[],tmp_path)


@pytest.mark.parametrize('comparison',list(C.ALIASES),indirect=True)
def test_eight_registered_paths_keep_exact_native_requests_and_stage(comparison):
    root,parent,machine,point=comparison
    census=L.prepare_inputs(PC,root,'2026-10-07',machine)
    assert census['census']['eligible_requests']==5
    declarations=list(L.eligible(PC,machine,json.loads(Path(machine['population_path']).read_text())))
    projected=list(L.project_partition(PC,json.loads(Path(machine['population_path']).read_text())['partitions'][0],
                                       {point['canonical_id']:declarations},L.directory(PC,root,'2026-10-07')))[0]
    with S.Store(root) as store:
        assert {r[2]:store.request(r[6]) for r in store.owners(machine['artifact_content_sha256'])} == {
            arm:PC.request(projected,arm) for arm in AUX.ARMS}
    assert L.calls(PC,root,'2026-10-07',transport=transport)['new_calls']==5
    result=L.auxiliary_report(PC,root,'2026-10-07','2026-10-07',parent,publish_policy=False)
    issued=json.loads((L.directory(PC,root,'2026-10-07')/'machine.json').read_text())
    V.validate_sources(V.stage(root,'2026-10-07','2026-10-07',issued,result,
                              target_date='2026-10-08',release_commit='a'*40),root)
    assert len(issued['cells'])==48 and sum(len(c['routes']) for c in issued['cells'])==128
    states={r['status'] for r in result['branch_comparison_census']}
    assert {'completed','not_requested_machine_unselected','no_primary_points'} <= states
    assert L.calls(PC,root,'2026-10-07',transport=transport)['new_calls']==0


def test_partial_comparison_carries_whole_pair_even_with_prior_binding(comparison):
    root,parent,machine,point=comparison
    key='samsung|REGULAR|ALL';bid=point['branch_hits'][0]
    machine=copy.deepcopy(machine)
    prior=next(c for c in machine['baseline_cells'] if c['key']==key)['routes']['SOR']
    prior['payload']['branches'].append(C.branch(bid));prior['payload_sha256']=P.digest(prior['payload'])
    prior['branch_metrics'][bid]=None
    oldaux=next(c for c in machine['baseline_auxiliary_cells'] if c['key']==key)['routes']['SOR']
    policy=copy.deepcopy(next(iter(oldaux['payload']['branch_policies'].values())))
    policy['binding']=PC.A.binding(C.branch(bid)['decision_phase'],policy['arm'])
    oldaux['payload']['branch_policies'][bid]=policy;oldaux['payload_sha256']=P.digest(oldaux['payload'])
    machine=P.seal(machine);P.write(PC.directory(root,'2026-10-07')/'machine-comparison.json',machine)
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    with S.Store(root) as store:
        rid=next(store.owners(machine['artifact_content_sha256']))[6]
        attempt=store.reserve(rid,store.activation()['writer_epoch'])
        store.finish(attempt,dict(result=transport(store.request(rid),30)))
    result=L.auxiliary_report(PC,root,'2026-10-07','2026-10-07',parent,publish_policy=False)
    issued=json.loads((L.directory(PC,root,'2026-10-07')/'machine.json').read_text())
    selected=next(c for c in issued['cells'] if c['key']==key)['routes']['SOR']
    binding=next(c for c in result['cells'] if c['key']==key)['routes']['SOR']
    assert selected['payload']==prior['payload'] and selected['branch_metrics']==prior['branch_metrics']
    assert binding['payload']==oldaux['payload']
    pending=next(r for r in result['scope_pending'] if r['cell_key']==key and r['route']=='SOR')
    assert pending['reasons'][bid]=='evaluation_incomplete'
    assert pending['machine_winner_payload_sha256']!=pending['publishable_pair_payload_sha256']
    assert not result['comparison_complete']


@pytest.mark.parametrize('corruption',['delete','substitute'])
def test_membership_corruption_rejected_before_transport_and_publication(comparison,corruption):
    root,parent,machine,_=comparison
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    with S.Store(root) as store:
        rows=list(store.owners(machine['artifact_content_sha256']))
        if corruption=='delete':store.db.execute('DELETE FROM partition_members WHERE member_id=?',(rows[0][7],))
        else:store.db.execute('UPDATE members SET request_id=? WHERE id=?',(rows[1][6],rows[0][7]))
    with pytest.raises(ValueError,match='expected_membership_changed'):
        L.calls(PC,root,'2026-10-07',transport=lambda *a,**k:pytest.fail('no provider authority'))
    with pytest.raises(ValueError,match='expected_membership_changed'):
        L.auxiliary_report(PC,root,'2026-10-07','2026-10-07',parent,publish_policy=False)
    with S.Store(root,readonly=True) as store:
        assert store.db.execute('SELECT count(*) FROM attempts').fetchone()[0]==0


def test_supported_prepare_cli_uses_shared_store_without_provider(comparison,monkeypatch):
    root,parent,machine,_=comparison
    monkeypatch.setattr(PC,'active',lambda *a:parent)
    monkeypatch.setattr(PC,'prepare_inputs',lambda *a:pytest.fail('retired writer'))
    monkeypatch.setattr(L,'calls',lambda *a,**k:pytest.fail('no provider at preparation'))
    assert P.main(['--date','2026-10-07','--data-root',str(root),'--mode','prepare-inputs'])==0
    assert L.validate_census(L.directory(PC,root,'2026-10-07'))[0]['input_refs_version']==2
    assert not (root/'report/continuous_reversal_registered/v4/request-ledger.sqlite3').exists()


@pytest.mark.parametrize('mode',['calls','machine','prepare-inputs'])
def test_evaluate_only_never_silently_calls_or_publishes(tmp_path,mode):
    with pytest.raises(SystemExit) as error:
        P.main(['--date','2026-10-07','--data-root',str(tmp_path),'--mode',mode,'--evaluate-only'])
    assert error.value.code==2 and not list(tmp_path.iterdir())


@pytest.mark.parametrize('comparison',['legacy'],indirect=True)
def test_v3_and_v4_share_actual_requests_with_separate_comparison_generations(comparison):
    from src.engine.scalping import continuous_reversal_registered_postclose as old
    root,_,machine,_=comparison
    previous=P.seal(dict(machine,schema=old.SCHEMA))
    L.prepare_inputs(old,root,'2026-10-07',previous)
    assert L.calls(old,root,'2026-10-07',transport=transport)['new_calls']==5
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    assert L.calls(PC,root,'2026-10-07',transport=transport)['new_calls']==0
    with S.Store(root) as store:
        assert store.db.execute('SELECT count(*) FROM requests').fetchone()[0]==5
        assert store.db.execute('SELECT count(*) FROM attempts').fetchone()[0]==5
        assert store.db.execute('SELECT count(*) FROM generations').fetchone()[0]==2
        assert list(store.owners(previous['artifact_content_sha256']))==list(store.owners(machine['artifact_content_sha256']))


def test_all_veto_is_completed_no_pass_and_keeps_explicit_pair_carry(comparison):
    root,parent,machine,_=comparison
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    def veto(req,timeout_sec):
        value=transport(req,timeout_sec);value['candidate_response']['risk_verdict']='VETO';return value
    L.calls(PC,root,'2026-10-07',transport=veto)
    result=L.auxiliary_report(PC,root,'2026-10-07','2026-10-07',parent,publish_policy=False)
    assert result['comparison_complete']
    assert set(result['comparison_statuses'].values())=={'completed_no_pass'}
    assert any('no_comparable_auxiliary_arm' in r['reasons'].values() for r in result['scope_pending'])


def test_publication_freezes_census_before_preparer_can_advance(comparison,monkeypatch):
    root,parent,machine,_=comparison
    L.prepare_inputs(PC,root,'2026-10-07',machine)
    L.calls(PC,root,'2026-10-07',transport=transport)
    original=L.branch_comparison_census
    def next_preparation(*args):
        # Another preparation may advance this mutable receipt after the
        # response-selection lock has closed, but the issued source is frozen.
        P.write(L.directory(PC,root,'2026-10-07')/'input-census.json',{'new_generation':'fixture'})
        return original(*args)
    monkeypatch.setattr(L,'branch_comparison_census',next_preparation)
    result=L.auxiliary_report(PC,root,'2026-10-07','2026-10-07',parent,publish_policy=False)
    issued=json.loads((L.directory(PC,root,'2026-10-07')/'machine.json').read_text())
    V.validate_sources(V.stage(root,'2026-10-07','2026-10-07',issued,result,
                              target_date='2026-10-08',release_commit='a'*40),root)
