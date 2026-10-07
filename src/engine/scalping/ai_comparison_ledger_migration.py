"""Streaming, resumable import of pinned Main v3/v4 offline ledgers.

No provider calls, policy activation, report regeneration or scheduler changes.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import time
import os
import subprocess

from src.engine.ai.offline_comparison_store import (
    Store, FORMAT, NAMESPACE, atomic_json, digest, file_hash, fsync_directory,
)


def legacy_paths(data_root):
    root = Path(data_root) / 'report/continuous_reversal_registered'
    return (root / 'request-ledger.sqlite3', root / 'v4/request-ledger.sqlite3')


def identity(path):
    s = path.stat()
    wal = path.with_name(path.name + '-wal')
    w = wal.stat() if wal.exists() else None
    return dict(path=str(path.resolve()), size=s.st_size, mtime_ns=s.st_mtime_ns,
                wal_size=w.st_size if w else 0, wal_mtime_ns=w.st_mtime_ns if w else 0)


def import_ledger(store, path):
    path = Path(path)
    source = str(path.resolve())
    name = 'import:' + source
    signature = identity(path)
    checkpoint = store.checkpoint(name)
    if checkpoint and checkpoint['signature'] != signature:
        raise ValueError('comparison_legacy_source_changed')
    if checkpoint and checkpoint['phase'] == 'complete':
        return checkpoint
    if not checkpoint:
        checkpoint = dict(signature=signature, source_sha256=file_hash(path), phase='requests',
                          request_cursor=0, owner_cursor=0, requests=0, owners=0)
        store.checkpoint(name, checkpoint)
        store.commit()
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.execute('PRAGMA query_only=ON')
    db.execute('BEGIN')
    store.db.execute('''CREATE TABLE IF NOT EXISTS migration_members(source TEXT,generation TEXT,
      group_key TEXT,member_id INTEGER,PRIMARY KEY(source,generation,group_key,member_id)) WITHOUT ROWID''')
    try:
        if checkpoint['phase'] == 'requests':
            cursor = db.execute('SELECT rowid,identity,request,state,result,reserved_at,priority FROM requests WHERE rowid>? ORDER BY rowid', (checkpoint['request_cursor'],))
            for ordinal, request_key, raw, state, result_raw, reserved_at, priority in cursor:
                req = json.loads(raw)
                if req['paired_replay_id'] != request_key:
                    raise ValueError('comparison_legacy_request_id_mismatch')
                rid, env = store.add_request(req, priority=priority)
                result = json.loads(result_raw) if result_raw else None
                result_obj = store.put(result) if result is not None else None
                store.db.execute('INSERT INTO aliases VALUES(?,?,?,?,?)', (source, rid, env, result_obj, state))
                # Verify the complete reconstructed envelope and transmission,
                # not a sampled input or only the shared digest.
                if store.request(rid, envelope=env) != req:
                    raise ValueError('comparison_legacy_roundtrip_changed')
                current = store.db.execute('SELECT state,result_obj FROM requests WHERE id=?', (rid,)).fetchone()
                response = ((result or {}).get('result') or {}).get('provider_provenance', {}).get('response_id')
                if state == 'completed':
                    if not response:
                        raise ValueError('comparison_legacy_completed_without_response')
                    attempt = digest(['provider', req['control'], request_key, response])
                    previous = store.db.execute('SELECT result_obj FROM attempts WHERE attempt=?', (attempt,)).fetchone()
                    if previous and store.get(previous[0]).get('result') != result.get('result'):
                        raise ValueError('comparison_legacy_response_conflict')
                    store.db.execute('INSERT OR IGNORE INTO attempts VALUES(?,?,?,?,?,?,?)',
                                     (attempt, rid, 'completed', result_obj, None, 0, 'legacy:' + source))
                    store.db.execute("UPDATE requests SET state='completed',result_obj=coalesce(result_obj,?) WHERE id=?", (result_obj, rid))
                elif state in ('reserved', 'failed'):
                    attempt = digest(['legacy-uncertain', source, request_key, reserved_at])
                    store.db.execute('INSERT OR IGNORE INTO attempts VALUES(?,?,?,?,?,?,?)',
                                     (attempt, rid, 'reserved', result_obj, None, 0, 'legacy:' + source))
                    if current[0] != 'completed':
                        store.db.execute("UPDATE requests SET state='reserved' WHERE id=?", (rid,))
                elif state != 'planned':
                    raise ValueError('comparison_legacy_unknown_state')
                checkpoint.update(request_cursor=ordinal, requests=checkpoint['requests'] + 1)
                if checkpoint['requests'] % 1000 == 0:
                    store.checkpoint(name, checkpoint)
                    store.commit()
                    if checkpoint['requests'] % 25000 == 0:
                        print('import requests', path.parent.name, checkpoint['requests'], flush=True)
            checkpoint['phase'] = 'owners'
            store.checkpoint(name, checkpoint)
            store.commit()
        if checkpoint['phase'] == 'owners':
            cursor = db.execute('SELECT rowid,generation,comparison,opportunity,arm,identity,outcome FROM owners WHERE rowid>? ORDER BY rowid', (checkpoint['owner_cursor'],))
            for ordinal, generation, comparison, opportunity, arm, key, outcome in cursor:
                row = store.db.execute('''SELECT r.id,r.day,r.symbol,CASE WHEN a.state='completed' THEN a.result_obj ELSE NULL END FROM requests r
                    JOIN aliases a ON a.request_id=r.id AND a.source=? WHERE r.namespace=? AND r.identity=?''',
                                       (source, NAMESPACE, key)).fetchone()
                if not row:
                    raise ValueError('comparison_legacy_owner_request_missing')
                rid, day, symbol, result_obj = row
                mid = store.add_member(comparison, opportunity, arm, rid, outcome, result_override=result_obj)
                group = json.dumps([comparison, day, symbol], separators=(',', ':'))
                store.db.execute('INSERT INTO migration_members VALUES(?,?,?,?)', (source, generation, group, mid))
                checkpoint.update(owner_cursor=ordinal, owners=checkpoint['owners'] + 1)
                if checkpoint['owners'] % 1000 == 0:
                    store.checkpoint(name, checkpoint)
                    store.commit()
            checkpoint['phase'] = 'bind'
            store.checkpoint(name, checkpoint)
            store.commit()
        groups = defaultdict(lambda: defaultdict(list))
        for generation, group, mid in store.db.execute('SELECT generation,group_key,member_id FROM migration_members WHERE source=?', (source,)):
            groups[generation][group].append(mid)
        for generation, partitions in groups.items():
            expected = db.execute('SELECT count(*) FROM owners WHERE generation=?', (generation,)).fetchone()[0]
            store.bind_generation(generation, partitions,
                                  dict(generation=generation, membership_contract='legacy_exact_owner_v1'), expected)
        if db.execute('SELECT count(*) FROM requests').fetchone()[0] != checkpoint['requests']:
            raise ValueError('comparison_legacy_request_census_changed')
        if db.execute('SELECT count(*) FROM owners').fetchone()[0] != checkpoint['owners']:
            raise ValueError('comparison_legacy_owner_census_changed')
        if identity(path) != signature:
            raise ValueError('comparison_legacy_source_changed_during_import')
        checkpoint['phase'] = 'complete'
        checkpoint['generations'] = sorted(groups)
        checkpoint['verified_all_requests_and_owners'] = True
        store.checkpoint(name, checkpoint)
        store.db.execute('DELETE FROM migration_members WHERE source=?', (source,))
        store.commit()
        return checkpoint
    finally:
        db.close()


def import_journal(store, path):
    if not path.exists():
        return None
    signature = identity(path)
    sha = file_hash(path)
    ck = 'legacy-journal:' + str(path.resolve())
    old = store.checkpoint(ck)
    if old:
        if old['signature'] != signature or old['sha256'] != sha:
            raise ValueError('comparison_legacy_journal_changed')
        return old
    count = 0; partial = 0
    with path.open('rb') as f:
        for line in f:
            if not line.endswith(b'\n'):
                partial = len(line)
                break  # preserved original tail; associated reservation stays uncertain
            value = json.loads(line); req = value['request']; record = value['record']
            key = value['request_identity']
            if req['paired_replay_id'] != key:
                raise ValueError('comparison_journal_identity_conflict')
            rid, env = store.add_request(req)
            source = str((path.parent / 'request-ledger.sqlite3').resolve())
            alias = store.db.execute('SELECT envelope_obj FROM aliases WHERE source=? AND request_id=?', (source, rid)).fetchone()
            if not alias or store.request(rid, envelope=alias[0]) != req:
                raise ValueError('comparison_journal_alias_missing')
            response = record.get('result', {}).get('provider_provenance', {}).get('response_id')
            attempt = digest(['provider', req['control'], key, response]) if response else digest(['legacy-journal', sha, count])
            obj = store.put(record)
            prior = store.db.execute('SELECT result_obj FROM attempts WHERE attempt=?', (attempt,)).fetchone()
            if prior and store.get(prior[0]).get('result') != record.get('result'):
                raise ValueError('comparison_journal_response_conflict')
            store.db.execute('INSERT OR IGNORE INTO attempts VALUES(?,?,?,?,?,?,?)',
                             (attempt, rid, 'completed' if response else 'reserved', obj, None, 0, 'journal:' + sha))
            if response:
                store.db.execute("UPDATE requests SET state='completed',result_obj=coalesce(result_obj,?) WHERE id=?", (obj, rid))
                # Exact original request and source journal attest this old
                # reservation. Other source attempts are never cleared.
                store.db.execute("UPDATE attempts SET state='completed',result_obj=? WHERE request_id=? AND source=? AND state='reserved'", (obj, rid, 'legacy:' + source))
            count += 1
    receipt = dict(signature=signature, sha256=sha, records=count, partial_tail_bytes=partial)
    store.checkpoint(ck, receipt); store.commit()
    return receipt


def migrate(data_root):
    with Store(data_root) as store:
        receipts = [import_ledger(store, p) for p in legacy_paths(data_root) if p.exists()]
        journals = [r for p in legacy_paths(data_root)
                    if (r := import_journal(store, p.parent / 'provider-response-journal.jsonl'))]
        result = dict(schema=FORMAT, status='imported', sources=receipts,
                      journals=journals,
                      requests=store.db.execute('SELECT count(*) FROM requests').fetchone()[0],
                      states=dict(store.db.execute('SELECT state,count(*) FROM requests GROUP BY state')),
                      generations=list(store.db.execute('SELECT generation,expected FROM generations')),
                      provider_calls=0)
        store.checkpoint('migration_receipt', result)
        store.commit()
        atomic_json(store.root / 'migration-receipt.json', result)
        return result


def activate(data_root):
    with Store(data_root) as store:
        receipt = store.checkpoint('migration_receipt')
        if not receipt or not all(s['verified_all_requests_and_owners'] for s in receipt['sources']):
            raise ValueError('comparison_migration_not_verified')
        for source in receipt['sources'] + receipt.get('journals', []):
            if identity(Path(source['signature']['path'])) != source['signature']:
                raise ValueError('comparison_activation_legacy_changed')
        existing = store.root / 'current.json'
        if existing.exists():
            return store.activation()
        value = dict(schema=FORMAT, store_root=str(store.root.resolve()), writer_epoch=digest([receipt, time.time_ns()]),
                     migration_sha256=digest(receipt), authority='offline_only', activated_at=time.time(), writer_enabled=False)
        atomic_json(existing, value)
        return value


def export_legacy(data_root, generation, output):
    """Explicit rollback export of CURRENT responses/reservations, never stale DBs."""
    output = Path(output)
    if output.exists():
        raise ValueError('comparison_rollback_output_exists')
    with Store(data_root) as store:
        store.reconcile()
        if not store.db.execute('SELECT 1 FROM generations WHERE generation=?', (generation,)).fetchone():
            raise ValueError('comparison_rollback_generation_missing')
        db = sqlite3.connect(output)
        try:
            db.executescript('''CREATE TABLE requests(identity TEXT PRIMARY KEY,request TEXT NOT NULL,state TEXT NOT NULL,result TEXT,reserved_at TEXT,priority INTEGER DEFAULT 0);
             CREATE TABLE owners(generation TEXT,comparison TEXT,opportunity TEXT,arm TEXT,identity TEXT,outcome TEXT,PRIMARY KEY(generation,comparison,opportunity,arm));''')
            for comparison, opportunity, arm, outcome, state, result_obj, rid, _ in store.owners(generation):
                req = store.request(rid)
                unresolved = store.db.execute("SELECT 1 FROM attempts WHERE request_id=? AND state='reserved' LIMIT 1", (rid,)).fetchone()
                # The legacy format cannot represent concurrent response and
                # uncertain attempts: block retry while retaining the response.
                exported_state = 'reserved' if unresolved else state
                result = json.dumps(store.get(result_obj)) if result_obj else None
                db.execute('INSERT OR IGNORE INTO requests VALUES(?,?,?,?,?,?)',
                           (req['paired_replay_id'], json.dumps(req), exported_state, result, 'shared-store-rollback' if unresolved else None, 0))
                db.execute('INSERT INTO owners VALUES(?,?,?,?,?,?)',
                           (generation, comparison, opportunity, arm, req['paired_replay_id'], outcome))
            db.commit()
        finally:
            db.close()
        return dict(output=str(output), sha256=file_hash(output), generation=generation)


def open_file_references(paths):
    """Privileged read-only FD census; inability to inspect is not clearance."""
    script = '''import json,os,sys
from pathlib import Path
targets=set(json.loads(sys.argv[1])); refs=[]; unknown=[]
for process in Path('/proc').iterdir():
 if not process.name.isdigit(): continue
 try:
  for fd in (process/'fd').iterdir():
   try: target=os.readlink(fd)
   except FileNotFoundError: continue
   if target.removesuffix(' (deleted)') in targets: refs.append(dict(pid=int(process.name),fd=fd.name,path=target))
 except FileNotFoundError: continue
 except PermissionError: unknown.append(process.name)
print(json.dumps(dict(references=refs,unobservable=unknown)))'''
    result = subprocess.run(['sudo', '-n', '/usr/bin/python3', '-c', script, json.dumps(paths)],
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def retire_legacy(data_root):
    """Verified duplicate body retirement; old writers fail at the DB path.

    Latest-state rollback uses export_legacy, never an old queue snapshot.
    Existing frozen exports, source evidence and legacy journals are retained.
    """
    with Store(data_root) as store:
        store.activation(); store.reconcile()
        receipt = store.checkpoint('migration_receipt')
        if not receipt or not all(s['verified_all_requests_and_owners'] for s in receipt['sources']):
            raise ValueError('comparison_retirement_migration_unverified')
        if store.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('comparison_retirement_metadata_invalid')
        validation = json.loads((store.root / 'verification-receipt.json').read_text())
        if validation.get('migration_sha256') != digest(receipt) or validation.get('status') != 'passed':
            raise ValueError('comparison_retirement_full_verification_missing')
        candidates = []
        for source in receipt['sources']:
            path = Path(source['signature']['path'])
            if path.is_dir() and (path / 'RETIRED.json').is_file():
                marker = json.loads((path / 'RETIRED.json').read_text())
                if marker.get('migration_sha256') != digest(receipt) or marker.get('common_store') != str(store.root.resolve()):
                    raise ValueError('comparison_retirement_marker_changed')
                temporary = path.with_name(path.name + '.verified-retirement')
                if temporary.exists():
                    if temporary.is_symlink() or temporary.stat().st_nlink != 1 or file_hash(temporary) != source['source_sha256']:
                        raise ValueError('comparison_retirement_interrupted_source_changed')
                    stat = temporary.stat()
                    candidates.append(dict(path=str(temporary), sha256=source['source_sha256'], size=stat.st_size,
                                           allocated=stat.st_blocks * 512, inode=stat.st_ino, device=stat.st_dev))
                continue
            if path.is_symlink() or path.stat().st_nlink != 1 or identity(path) != source['signature']:
                raise ValueError('comparison_retirement_source_changed')
            if file_hash(path) != source['source_sha256']:
                raise ValueError('comparison_retirement_source_hash_changed')
            for item in [path, path.with_name(path.name + '-wal'), path.with_name(path.name + '-shm')]:
                if item.exists():
                    st = item.stat()
                    candidates.append(dict(path=str(item), sha256=file_hash(item), size=st.st_size, allocated=st.st_blocks * 512, inode=st.st_ino, device=st.st_dev))
        census = open_file_references([r['path'] for r in candidates])
        dry = dict(candidates=candidates, process_census=census, migration_sha256=digest(receipt))
        atomic_json(store.root / 'legacy-retirement-dry-run.json', dry)
        if census['references'] or census['unobservable']:
            raise ValueError('comparison_retirement_process_reference')
        for item in candidates:
            path = Path(item['path']); stat = path.stat()
            if stat.st_ino != item['inode'] or stat.st_dev != item['device'] or file_hash(path) != item['sha256']:
                raise ValueError('comparison_retirement_recheck_changed')
        removed = []
        for item in candidates:
            path = Path(item['path'])
            if path.name == 'request-ledger.sqlite3':
                temporary = path.with_name(path.name + '.verified-retirement')
                if temporary.exists():
                    raise ValueError('comparison_retirement_interrupted_requires_reconcile')
                os.replace(path, temporary)
                path.mkdir()
                atomic_json(path / 'RETIRED.json', dict(schema=FORMAT, common_store=str(store.root.resolve()),
                                                       migration_sha256=digest(receipt), rollback='export-legacy-current-state'))
                temporary.unlink()
            else:
                path.unlink()
            removed.append(item); fsync_directory(path.parent)
            atomic_json(store.root / 'legacy-retirement-removal.json', dict(removed=removed, allocated_bytes=sum(r['allocated'] for r in removed)))
        # Also fence a version that had no legacy database at all.
        for path in legacy_paths(data_root):
            if not path.exists():
                path.mkdir(parents=True)
                atomic_json(path / 'RETIRED.json', dict(schema=FORMAT, common_store=str(store.root.resolve()),
                                                       migration_sha256=digest(receipt), rollback='export-legacy-current-state'))
            if not path.is_dir() or not (path / 'RETIRED.json').is_file():
                raise ValueError('comparison_retirement_legacy_path_not_fenced')
        current = store.activation()
        current.update(writer_enabled=True, legacy_writer_fenced=True)
        atomic_json(store.root / 'current.json', current)
        return dict(removed=len(removed), allocated_bytes=sum(r['allocated'] for r in removed))


def verify(data_root):
    with Store(data_root) as store:
        receipt = store.checkpoint('migration_receipt')
        if not receipt:
            raise ValueError('comparison_verification_migration_missing')
        objects = store.verify_objects()
        integrity = store.db.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity != 'ok':
            raise ValueError('comparison_metadata_integrity_failed')
        bad_requests = store.db.execute('''SELECT count(*) FROM requests r
          LEFT JOIN objects i ON i.id=r.input_obj LEFT JOIN objects c ON c.id=r.candidate_obj
          LEFT JOIN objects k ON k.id=r.control_obj LEFT JOIN objects e ON e.id=r.envelope_obj
          LEFT JOIN objects x ON x.id=r.result_obj WHERE i.id IS NULL OR c.id IS NULL OR k.id IS NULL
          OR e.id IS NULL OR (r.result_obj IS NOT NULL AND x.id IS NULL)
          OR (r.state='completed' AND r.result_obj IS NULL)''').fetchone()[0]
        bad_attempts = store.db.execute('''SELECT count(*) FROM attempts a LEFT JOIN requests r ON r.id=a.request_id
          LEFT JOIN objects o ON o.id=a.result_obj WHERE r.id IS NULL OR (a.result_obj IS NOT NULL AND o.id IS NULL)''').fetchone()[0]
        if bad_requests or bad_attempts:
            raise ValueError('comparison_verification_reference_missing')
        for source in receipt['sources']:
            aliases = store.db.execute('SELECT count(*) FROM aliases WHERE source=?', (source['signature']['path'],)).fetchone()[0]
            if aliases != source['requests']:
                raise ValueError('comparison_verification_alias_missing')
        # Every owner must resolve a request and label; counts are independent
        # of unique transport identities and actual attempt counts.
        for generation, expected in store.db.execute('SELECT generation,expected FROM generations'):
            if sum(1 for _ in store.owners(generation)) != expected:
                raise ValueError('comparison_verification_owner_missing')
        result = dict(status='passed', verified_objects=objects, integrity=integrity,
                      migration_sha256=digest(receipt), provider_calls=0,
                      requests=store.db.execute('SELECT count(*) FROM requests').fetchone()[0],
                      states=dict(store.db.execute('SELECT state,count(*) FROM requests GROUP BY state')),
                      attempt_states=dict(store.db.execute('SELECT state,count(*) FROM attempts GROUP BY state')),
                      owners=list(store.db.execute('SELECT generation,expected FROM generations')))
        atomic_json(store.root / 'verification-receipt.json', result)
        return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-root', type=Path, default=Path('data'))
    p.add_argument('--mode', choices=('import', 'activate', 'verify', 'export-legacy', 'retire-legacy'), required=True)
    p.add_argument('--generation')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if args.mode == 'import':
        result = migrate(args.data_root)
    elif args.mode == 'activate':
        result = activate(args.data_root)
    elif args.mode == 'export-legacy':
        if not args.generation or not args.output:
            p.error('export requires --generation and --output')
        result = export_legacy(args.data_root, args.generation, args.output)
    elif args.mode == 'retire-legacy':
        result = retire_legacy(args.data_root)
    else:
        result = verify(args.data_root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
