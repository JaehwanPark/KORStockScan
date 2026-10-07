"""Durable migration, shared requests and provider crash/retry boundaries."""
import copy
import json
import sqlite3
from pathlib import Path
import pytest
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import ai_comparison_ledger_migration as M


def request(i=0, arm='a'):
    value = dict(paired_replay_parent_id=f'2026-10-07:SOR:REGULAR:005930:1:{i}', stage='entry',
                 micro_reversion_replay_arm=arm, candidate_input=dict(price=i, prefix=[1, 2, 3]),
                 candidate=dict(prompt=arm, schema={'answer': 'string'}), control=dict(model='fixture'))
    value['paired_replay_id'] = S.digest(value)
    return value


def response(identity, verdict='PASS'):
    return dict(result=dict(provider_provenance=dict(response_id='test-' + identity),
                            candidate_response=dict(risk_verdict=verdict)), validation_errors=[])


def activate(store):
    S.atomic_json(store.root / 'current.json', dict(schema=S.FORMAT, store_root=str(store.root.resolve()), writer_epoch='test', writer_enabled=True))


def legacy(path, rows, gen='g'):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript('''CREATE TABLE requests(identity TEXT PRIMARY KEY,request TEXT,state TEXT,result TEXT,reserved_at TEXT,priority INTEGER);
      CREATE TABLE owners(generation TEXT,comparison TEXT,opportunity TEXT,arm TEXT,identity TEXT,outcome TEXT,PRIMARY KEY(generation,comparison,opportunity,arm));''')
    for req, state, record in rows:
        db.execute('INSERT INTO requests VALUES(?,?,?,?,?,?)', (req['paired_replay_id'], json.dumps(req), state, json.dumps(record) if record else None, 'before-stop' if state == 'reserved' else None, 3))
        db.execute('INSERT INTO owners VALUES(?,?,?,?,?,?)', (gen, 'comparison', req['paired_replay_parent_id'], req['micro_reversion_replay_arm'], req['paired_replay_id'], 'WIN'))
    db.commit(); db.close()


def test_roundtrip_parts_shared_and_identity_conflict(tmp_path):
    with S.Store(tmp_path) as store:
        ids = [store.add_request(request(0, a))[0] for a in ('a','b','c','d','e')]
        assert len({r[0] for r in store.db.execute('SELECT input_obj FROM requests')}) == 1
        for ident, a in zip(ids, ('a','b','c','d','e')):
            assert store.request(ident) == request(0, a)
        before = store.db.execute('SELECT count(*) FROM objects').fetchone()[0]
        for a in ('a','b','c','d','e'): store.add_request(request(0, a))
        assert store.db.execute('SELECT count(*) FROM objects').fetchone()[0] == before
        bad = request(); bad['candidate_input']['price'] = 999
        with pytest.raises(ValueError, match='identity_conflict'): store.add_request(bad)


def test_cross_ledger_uncertain_import_idempotent_and_rollback(tmp_path):
    a, b = M.legacy_paths(tmp_path)
    req0, req1 = request(0), request(1)
    result = response(req0['paired_replay_id'])
    legacy(a, [(req0, 'completed', result), (req1, 'reserved', None)], 'v3')
    legacy(b, [(req0, 'completed', result), (req1, 'planned', None)], 'v4')
    receipt = M.migrate(tmp_path)
    assert receipt['requests'] == 2 and receipt['states'] == {'completed': 1, 'reserved': 1}
    assert M.migrate(tmp_path) == receipt
    M.activate(tmp_path)
    with S.Store(tmp_path) as store:
        assert store.db.execute('SELECT count(*) FROM attempts').fetchone()[0] == 2
        assert list(store.pending('v4')) == []
        for gen in ('v3', 'v4'):
            assert len(list(store.owners(gen))) == 2
    exported = tmp_path / 'rollback.sqlite3'
    M.export_legacy(tmp_path, 'v4', exported)
    db = sqlite3.connect(exported)
    assert dict(db.execute('SELECT identity,state FROM requests')) == {req0['paired_replay_id']: 'completed', req1['paired_replay_id']: 'reserved'}
    assert json.loads(db.execute('SELECT request FROM requests WHERE identity=?', (req1['paired_replay_id'],)).fetchone()[0]) == req1
    db.close()


def test_response_landing_recovery_fence_and_no_error_chosen(tmp_path):
    with S.Store(tmp_path) as store:
        activate(store); rid, _ = store.add_request(request()); store.commit()
        with pytest.raises(ValueError, match='fenced'): store.reserve(rid, 'old')
        attempt = store.reserve(rid, 'test')
        store.land_response(attempt, response('landed'))
    with S.Store(tmp_path) as store:
        store.reconcile()
        state, result = store.db.execute('SELECT state,result_obj FROM requests').fetchone()
        assert state == 'completed' and store.get(result) == response('landed')
        assert not list((store.root/'landing').glob('*.json'))
        rid2, _ = store.add_request(request(2)); attempt2 = store.reserve(rid2, 'test')
        store.finish(attempt2, {'error_type': 'timeout'})
        assert store.db.execute('SELECT state,result_obj FROM requests WHERE id=?', (rid2,)).fetchone() == ('reserved', None)
        with pytest.raises(ValueError, match='not_available'): store.reserve(rid2, 'test')


def test_response_journal_commit_crash(tmp_path, monkeypatch):
    with S.Store(tmp_path) as store:
        activate(store); rid, _ = store.add_request(request()); attempt = store.reserve(rid, 'test')
        original = store._finish_record
        monkeypatch.setattr(store, '_finish_record', lambda *a: (_ for _ in ()).throw(RuntimeError('crash')))
        with pytest.raises(RuntimeError): store.finish(attempt, response('journal'))
        monkeypatch.setattr(store, '_finish_record', original)
        store.reconcile()
        assert store.db.execute('SELECT state FROM requests').fetchone()[0] == 'completed'


def test_snapshot_immutable_late_response_and_label_partition_reuse(tmp_path):
    with S.Store(tmp_path) as store:
        activate(store); rid, _ = store.add_request(request())
        member = store.add_member('c', 'o', 'a', rid, 'WIN')
        store.bind_generation('g1', {'day/symbol/c': [member]}, {'generation':'g1'}, 1)
        first = store.snapshot('g1'); before = copy.deepcopy(first)
        attempt = store.reserve(rid, 'test'); store.finish(attempt, response('late'))
        second = store.snapshot('g1')
        assert first == before and second['snapshot_sha256'] != first['snapshot_sha256']
        assert store.get(next(iter(first['partitions'].values())))[0][1:] == ['planned', None]
        store.bind_generation('g2', {'day/symbol/c': [member]}, {'generation':'g2'}, 1)
        assert store.db.execute('SELECT count(*) FROM partitions').fetchone()[0] == 1
        other = store.add_member('c', 'o', 'a', rid, 'FAIL')
        store.bind_generation('g3', {'day/symbol/c': [other]}, {'generation':'g3'}, 1)
        assert store.db.execute('SELECT count(*) FROM requests').fetchone()[0] == 1


def test_writer_and_legacy_locks(tmp_path):
    import fcntl
    with S.Store(tmp_path):
        with pytest.raises(BlockingIOError):
            with S.Store(tmp_path): pass
        for path in M.legacy_paths(tmp_path):
            with (path.parent/'provider-worker.lock').open('a') as f:
                with pytest.raises(BlockingIOError): fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB)


def test_legacy_journal_orphan_response_is_reconciled_without_transport(tmp_path):
    a, _ = M.legacy_paths(tmp_path); req = request()
    legacy(a, [(req,'reserved',None)])
    journal = a.parent/'provider-response-journal.jsonl'
    journal.write_text(json.dumps(dict(request_identity=req['paired_replay_id'], request=req, record=response('recovered'))) + '\n')
    receipt = M.migrate(tmp_path)
    assert receipt['states'] == {'completed': 1} and receipt['provider_calls'] == 0
    with S.Store(tmp_path) as store:
        assert store.db.execute("SELECT count(*) FROM attempts WHERE state='reserved'").fetchone()[0] == 0


def test_pack_corruption_and_gc_do_not_drop_referenced_pending(tmp_path):
    with S.Store(tmp_path) as store:
        rid, _ = store.add_request(request()); store.commit()
        orphan = store.root/'packs'/'orphan.pack.partial'; orphan.write_bytes(b'crashed')
        assert len(store.orphan_packs(remove=True)) == 1 and not orphan.exists()
        assert store.request(rid) == request()
        pack = next((store.root/'packs').glob('*.pack')); pack.write_bytes(b'corrupt')
        with pytest.raises(Exception): store.request(rid)


def test_late_actual_response_after_uncertainty_is_preserved_and_not_rechosen(tmp_path):
    with S.Store(tmp_path) as store:
        activate(store); rid,_=store.add_request(request()); attempt=store.reserve(rid,'test')
        store.finish(attempt, {'error_type':'timeout'})
        store.land_response(attempt,response('late')); store.reconcile()
        first=store.db.execute('SELECT result_obj FROM requests').fetchone()[0]
        assert store.get(first)==response('late')
        store.finish(attempt,response('extra','BLOCK'))
        store.reconcile()
        assert store.db.execute('SELECT result_obj FROM requests').fetchone()[0]==first
        assert store.db.execute('SELECT count(*) FROM attempt_responses').fetchone()[0]==3


def test_retirement_fences_old_sqlite_and_latest_rollback_remains(tmp_path,monkeypatch):
    a,_=M.legacy_paths(tmp_path); req=request(); legacy(a,[(req,'planned',None)])
    M.migrate(tmp_path); M.verify(tmp_path); M.activate(tmp_path)
    monkeypatch.setattr(M,'open_file_references',lambda paths:dict(references=[],unobservable=[]))
    result=M.retire_legacy(tmp_path)
    assert result['allocated_bytes']>0 and a.is_dir()
    with pytest.raises(sqlite3.OperationalError):sqlite3.connect(a)
    with S.Store(tmp_path) as store:
        fence=store.activation()['writer_epoch']; rid=store.db.execute('SELECT id FROM requests').fetchone()[0]
        attempt=store.reserve(rid,fence);store.finish(attempt,response('after-cutover'))
    output=tmp_path/'rollback-current.sqlite3';M.export_legacy(tmp_path,'g',output)
    db=sqlite3.connect(output)
    record=json.loads(db.execute('SELECT result FROM requests').fetchone()[0])
    assert record==response('after-cutover');db.close()


def test_source_mutation_after_import_blocks_activation(tmp_path):
    a,_=M.legacy_paths(tmp_path);legacy(a,[(request(),'planned',None)])
    M.migrate(tmp_path)
    db=sqlite3.connect(a);db.execute("UPDATE requests SET state='reserved'");db.commit();db.close()
    with pytest.raises(ValueError,match='legacy_changed'):M.activate(tmp_path)


def test_import_interruption_resumes_without_duplicate_requests(tmp_path,monkeypatch):
    a,_=M.legacy_paths(tmp_path); rows=[(request(i),'planned',None) for i in range(12)];legacy(a,rows)
    original=S.Store.add_request;seen=[]
    def interrupted(self,req,**kw):
        seen.append(req['paired_replay_id'])
        if len(seen)==4:raise RuntimeError('interruption')
        return original(self,req,**kw)
    monkeypatch.setattr(S.Store,'add_request',interrupted)
    with pytest.raises(RuntimeError,match='interruption'):M.migrate(tmp_path)
    monkeypatch.setattr(S.Store,'add_request',original)
    receipt=M.migrate(tmp_path)
    assert receipt['requests']==12 and receipt['states']=={'planned':12}
    assert receipt['generations']==[('g',12)]
