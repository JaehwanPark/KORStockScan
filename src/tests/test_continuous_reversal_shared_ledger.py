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
def comparison(native, monkeypatch):
    root, parent, _, _ = native
    machine, aux = migrated_reports(native)
    machine = copy.deepcopy(machine); base = copy.deepcopy(machine['cells'])
    bid, st = state('SA', monkeypatch)
    values = [row(i) for i in range(62)] + [row(62, 100.2)]
    for r in values: feed(st, r)
    event, source = st.snapshot(st.ready[-1]); signal = event['branch_signals'][bid]
    selected = next(c for c in machine['cells'] if c['key'] == 'samsung|REGULAR|ALL')['routes']['SOR']
    selected.update(payload=R.B.payload([C.branch(bid)]), local_metrics=dict(wins=1,resolved=1), branch_metrics={bid:dict(wins=1,resolved=1)})
    selected['payload_sha256'] = P.digest(selected['payload'])
    point = dict(canonical_id=event['canonical_opportunity_id'], event=event, entry_index=62,
                 branch_hits=[bid], confirmed_signals={bid:signal}, path_inputs={bid:source['branch_inputs'][bid]}, outcome=dict(status='WIN'))
    raw = root/'raw.gz'; raw.write_bytes(gzip.compress(json.dumps(dict(symbols={'005930':values})).encode()))
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
