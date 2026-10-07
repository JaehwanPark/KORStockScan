"""Content-addressed offline AI requests, durable attempts and frozen comparisons.

This store never grants live order authority. Writers hold one OS lock across
reservation and transport; immutable packs are durable before SQLite references.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid
import zlib

FORMAT = 'offline_comparison_store_v1'
NAMESPACE = 'main_normalized_native_v1'
PACK_LIMIT = 16 * 1024 * 1024


def encode(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('ascii')


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('.' + path.name + '-' + uuid.uuid4().hex)
    try:
        with tmp.open('xb') as f:
            f.write(encode(value) + b'\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        fsync_directory(path.parent)
    finally:
        tmp.unlink(missing_ok=True)


def store_root(data_root):
    return Path(data_root) / 'ai_comparison_store' / 'v1'


@contextlib.contextmanager
def writer_lock(data_root, *, legacy=True):
    """Also fence the frozen v3/v4 entrypoints, without editing pinned code."""
    root = store_root(data_root)
    paths = [root / 'writer.lock']
    if legacy:
        paths += [Path(data_root) / 'report/continuous_reversal_registered/provider-worker.lock',
                  Path(data_root) / 'report/continuous_reversal_registered/v4/provider-worker.lock']
    with contextlib.ExitStack() as stack:
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = stack.enter_context(path.open('a'))
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


SCHEMA = """
CREATE TABLE IF NOT EXISTS objects(id INTEGER PRIMARY KEY, hash TEXT NOT NULL UNIQUE,
 pack TEXT NOT NULL, offset INTEGER NOT NULL, length INTEGER NOT NULL, size INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY, namespace TEXT NOT NULL,
 identity TEXT NOT NULL, input_obj INTEGER NOT NULL, candidate_obj INTEGER NOT NULL,
 control_obj INTEGER NOT NULL, envelope_obj INTEGER NOT NULL, state TEXT NOT NULL,
 result_obj INTEGER, priority INTEGER NOT NULL DEFAULT 0, day TEXT NOT NULL, symbol TEXT NOT NULL,
 UNIQUE(namespace,identity));
CREATE INDEX IF NOT EXISTS request_queue ON requests(state,priority DESC,id);
CREATE TABLE IF NOT EXISTS strings(id INTEGER PRIMARY KEY,value TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS members(id INTEGER PRIMARY KEY, comparison INTEGER NOT NULL,
 opportunity INTEGER NOT NULL, arm INTEGER NOT NULL, request_id INTEGER NOT NULL,
 outcome TEXT NOT NULL, result_override INTEGER NOT NULL DEFAULT 0,
 UNIQUE(comparison,opportunity,arm,request_id,outcome,result_override));
CREATE TABLE IF NOT EXISTS partitions(id INTEGER PRIMARY KEY,hash TEXT NOT NULL UNIQUE,count INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS partition_members(partition_id INTEGER NOT NULL,member_id INTEGER NOT NULL,
 PRIMARY KEY(partition_id,member_id)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS generations(generation TEXT PRIMARY KEY,descriptor_obj INTEGER NOT NULL,
 expected INTEGER NOT NULL,status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS generation_parts(generation TEXT NOT NULL,partition_id INTEGER NOT NULL,
 PRIMARY KEY(generation,partition_id)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS attempts(attempt TEXT PRIMARY KEY,request_id INTEGER NOT NULL,
 state TEXT NOT NULL,result_obj INTEGER,fence TEXT,created REAL NOT NULL,source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS attempt_responses(attempt TEXT NOT NULL,result_obj INTEGER NOT NULL,
 PRIMARY KEY(attempt,result_obj)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS aliases(source TEXT NOT NULL,request_id INTEGER NOT NULL,
 envelope_obj INTEGER NOT NULL,result_obj INTEGER,state TEXT NOT NULL,
 PRIMARY KEY(source,request_id)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS checkpoints(name TEXT PRIMARY KEY,value_obj INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS snapshots(hash TEXT PRIMARY KEY,manifest_obj INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS validations(identity TEXT PRIMARY KEY,result_obj INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS attempt_budgets(attempt TEXT PRIMARY KEY,budget_key TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS attempt_budget_key ON attempt_budgets(budget_key);
"""


class Store:
    def __init__(self, data_root, *, readonly=False, lock_held=False):
        self.root = store_root(data_root)
        self.readonly = readonly
        self._guard = None
        self._pack = None
        self._pack_name = None
        self._objects = {}
        self._strings = {}
        if not readonly and not lock_held:
            self._guard = writer_lock(data_root)
            self._guard.__enter__()
        try:
            if readonly:
                self.db = sqlite3.connect((self.root / 'metadata.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
                self.db.execute('PRAGMA query_only=ON')
            else:
                (self.root / 'packs').mkdir(parents=True, exist_ok=True)
                self.db = sqlite3.connect(self.root / 'metadata.sqlite3', timeout=30)
                self.db.execute('PRAGMA journal_mode=WAL')
                self.db.execute('PRAGMA synchronous=FULL')
                self.db.executescript(SCHEMA)
            self.db.execute('PRAGMA cache_size=-32768')
        except BaseException:
            if self._guard:
                self._guard.__exit__(None, None, None)
            raise

    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        try:
            if typ is None and not self.readonly:
                self.commit()
            else:
                self.db.rollback()
        finally:
            if self._pack:
                self._pack.close()
                (self.root / 'packs' / (self._pack_name + '.partial')).unlink(missing_ok=True)
            self.db.close()
            if self._guard:
                self._guard.__exit__(typ, value, tb)

    def _seal_pack(self):
        if self._pack is None:
            return
        self._pack.flush()
        os.fsync(self._pack.fileno())
        self._pack.close()
        directory = self.root / 'packs'
        os.replace(directory / (self._pack_name + '.partial'), directory / self._pack_name)
        fsync_directory(directory)
        self._pack = None
        self._pack_name = None

    def commit(self):
        self._seal_pack()
        self.db.commit()

    def put(self, value):
        raw = encode(value)
        h = hashlib.sha256(raw).hexdigest()
        if h in self._objects:
            return self._objects[h]
        found = self.db.execute('SELECT id FROM objects WHERE hash=?', (h,)).fetchone()
        if found:
            ident = found[0]
        else:
            packed = zlib.compress(raw, 6)
            if len(packed) > PACK_LIMIT:
                raise ValueError('comparison_object_exceeds_pack_limit')
            if self._pack and self._pack.tell() + len(packed) > PACK_LIMIT:
                self._seal_pack()
            if self._pack is None:
                self._pack_name = uuid.uuid4().hex + '.pack'
                self._pack = (self.root / 'packs' / (self._pack_name + '.partial')).open('xb')
            offset = self._pack.tell()
            self._pack.write(packed)
            ident = self.db.execute('INSERT INTO objects(hash,pack,offset,length,size) VALUES(?,?,?,?,?)',
                                    (h, self._pack_name, offset, len(packed), len(raw))).lastrowid
        if len(self._objects) >= 50000:
            self._objects.clear()
        self._objects[h] = ident
        return ident

    def get(self, ident):
        row = self.db.execute('SELECT hash,pack,offset,length,size FROM objects WHERE id=?', (ident,)).fetchone()
        if not row:
            raise ValueError('comparison_object_missing')
        h, pack, offset, length, size = row
        path = self.root / 'packs' / pack
        if pack == self._pack_name and self._pack is not None:
            self._pack.flush()
            path = path.with_suffix(path.suffix + '.partial')
        with path.open('rb') as f:
            f.seek(offset)
            raw = zlib.decompress(f.read(length))
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != h:
            raise ValueError('comparison_object_hash_changed')
        return json.loads(raw)

    def string(self, value):
        if value in self._strings:
            return self._strings[value]
        self.db.execute('INSERT OR IGNORE INTO strings(value) VALUES(?)', (value,))
        ident = self.db.execute('SELECT id FROM strings WHERE value=?', (value,)).fetchone()[0]
        if len(self._strings) >= 50000:
            self._strings.clear()
        self._strings[value] = ident
        return ident

    def checkpoint(self, name, value=None):
        if value is None:
            row = self.db.execute('SELECT value_obj FROM checkpoints WHERE name=?', (name,)).fetchone()
            return self.get(row[0]) if row else None
        self.db.execute('INSERT INTO checkpoints VALUES(?,?) ON CONFLICT(name) DO UPDATE SET value_obj=excluded.value_obj',
                        (name, self.put(value)))

    def add_request(self, req, *, namespace=NAMESPACE, priority=0):
        identity = req['paired_replay_id']
        parts = [self.put(req.get(k)) for k in ('candidate_input', 'candidate', 'control')]
        envelope = {k: v for k, v in req.items() if k not in ('candidate_input', 'candidate', 'control', 'paired_replay_id')}
        env = self.put(envelope)
        parent = str(req.get('paired_replay_parent_id', '')).split(':')
        day, symbol = (parent[0], parent[3]) if len(parent) >= 4 else ('unknown', 'unknown')
        old = self.db.execute('SELECT id,input_obj,candidate_obj,control_obj,envelope_obj FROM requests WHERE namespace=? AND identity=?',
                              (namespace, identity)).fetchone()
        if old:
            if list(old[1:4]) != parts:
                raise ValueError('comparison_request_identity_conflict')
            # Envelope provenance may differ; transport stage must not.
            if self.get(old[4]).get('stage') != envelope.get('stage'):
                raise ValueError('comparison_request_stage_conflict')
            ident = old[0]
            self.db.execute('UPDATE requests SET priority=max(priority,?) WHERE id=?', (priority, ident))
        else:
            ident = self.db.execute('INSERT INTO requests(namespace,identity,input_obj,candidate_obj,control_obj,envelope_obj,state,priority,day,symbol) VALUES(?,?,?,?,?,?,\'planned\',?,?,?)',
                                    (namespace, identity, *parts, env, priority, day, symbol)).lastrowid
        return ident, env

    def request(self, ident, *, envelope=None):
        row = self.db.execute('SELECT identity,input_obj,candidate_obj,control_obj,envelope_obj FROM requests WHERE id=?', (ident,)).fetchone()
        if not row:
            raise ValueError('comparison_request_missing')
        value = self.get(envelope or row[4])
        value.update(paired_replay_id=row[0], candidate_input=self.get(row[1]),
                     candidate=self.get(row[2]), control=self.get(row[3]))
        return value

    def add_member(self, comparison, opportunity, arm, request_id, outcome, *, result_override=0):
        values = (self.string(comparison), self.string(opportunity), self.string(arm), request_id, outcome, result_override or 0)
        self.db.execute('INSERT OR IGNORE INTO members(comparison,opportunity,arm,request_id,outcome,result_override) VALUES(?,?,?,?,?,?)', values)
        return self.db.execute('SELECT id FROM members WHERE comparison=? AND opportunity=? AND arm=? AND request_id=? AND outcome=? AND result_override=?', values).fetchone()[0]

    def bind_generation(self, generation, groups, descriptor, expected):
        """Groups contain one source date/symbol/comparison partition of member IDs."""
        parts = []
        count = 0
        for key, members in sorted(groups.items()):
            ids = sorted(set(members))
            if len(ids) != len(members):
                raise ValueError('comparison_duplicate_expected_member')
            h = digest([key, ids])
            row = self.db.execute('SELECT id,count FROM partitions WHERE hash=?', (h,)).fetchone()
            if row:
                part = row[0]
                if row[1] != len(ids):
                    raise ValueError('comparison_partition_count_conflict')
            else:
                part = self.db.execute('INSERT INTO partitions(hash,count) VALUES(?,?)', (h, len(ids))).lastrowid
                self.db.executemany('INSERT INTO partition_members VALUES(?,?)', ((part, i) for i in ids))
            parts.append(part)
            count += len(ids)
        if count != expected:
            raise ValueError('comparison_expected_member_missing')
        existing = self.db.execute('SELECT descriptor_obj,expected FROM generations WHERE generation=?', (generation,)).fetchone()
        desc = self.put(descriptor)
        if existing:
            old_parts = [r[0] for r in self.db.execute('SELECT partition_id FROM generation_parts WHERE generation=? ORDER BY partition_id', (generation,))]
            if existing != (desc, expected) or sorted(parts) != old_parts:
                raise ValueError('comparison_generation_conflict')
            return
        self.db.execute('INSERT INTO generations VALUES(?,?,?,?)', (generation, desc, expected, 'prepared'))
        self.db.executemany('INSERT INTO generation_parts VALUES(?,?)', ((generation, i) for i in parts))

    def owners(self, generation):
        return self.db.execute('''SELECT c.value,o.value,a.value,m.outcome,r.state,
          CASE WHEN m.result_override>0 THEN m.result_override ELSE r.result_obj END,r.id,m.id
          FROM generation_parts gp JOIN partition_members pm ON pm.partition_id=gp.partition_id
          JOIN members m ON m.id=pm.member_id JOIN requests r ON r.id=m.request_id
          JOIN strings c ON c.id=m.comparison JOIN strings o ON o.id=m.opportunity
          JOIN strings a ON a.id=m.arm WHERE gp.generation=? ORDER BY c.value,o.value,a.value''', (generation,))

    def states(self, generation):
        return dict(self.db.execute('''SELECT state,count(*) FROM requests WHERE id IN
          (SELECT m.request_id FROM generation_parts gp JOIN partition_members pm ON pm.partition_id=gp.partition_id
          JOIN members m ON m.id=pm.member_id WHERE gp.generation=?) GROUP BY state''', (generation,)))

    def pending(self, generation, *, preferred_comparisons=()):
        # Scheduling only: membership, identities, responses and eligibility
        # remain unchanged. A newly approved scope must not sit behind a large
        # historical population until the publication window expires.
        preferred = tuple(sorted(set(preferred_comparisons)))
        if preferred:
            slots=','.join('?' for _ in preferred)
            preference='''CASE WHEN id IN (
              SELECT m.request_id FROM generation_parts gp
              JOIN partition_members pm ON pm.partition_id=gp.partition_id
              JOIN members m ON m.id=pm.member_id JOIN strings c ON c.id=m.comparison
              WHERE gp.generation=? AND c.value IN ('''+slots+''')) THEN 1 ELSE 0 END DESC,'''
            args=(generation,generation,*preferred)
        else:
            preference='';args=(generation,)
        return self.db.execute('''SELECT id FROM requests WHERE state='planned' AND id IN
          (SELECT m.request_id FROM generation_parts gp JOIN partition_members pm ON pm.partition_id=gp.partition_id
          JOIN members m ON m.id=pm.member_id WHERE gp.generation=?) ORDER BY '''+
          preference+'priority DESC,id', args)

    def activation(self):
        path = self.root / 'current.json'
        value = json.loads(path.read_text())
        if value.get('schema') != FORMAT or value.get('store_root') != str(self.root.resolve()):
            raise ValueError('comparison_store_activation_invalid')
        return value

    def seed_call_budget(self, generation, budget_key, *, since_epoch):
        """Charge retained completed/uncertain attempts once, across restarts."""
        self.db.execute('''INSERT OR IGNORE INTO attempt_budgets
            SELECT DISTINCT a.attempt,? FROM attempts a
            JOIN members m ON m.request_id=a.request_id
            JOIN partition_members pm ON pm.member_id=m.id
            JOIN generation_parts gp ON gp.partition_id=pm.partition_id
            WHERE gp.generation=? AND a.source='provider' AND a.created>=?''',
            (budget_key,generation,since_epoch))
        self.commit()

    def budget_used(self, budget_key):
        return self.db.execute('SELECT count(*) FROM attempt_budgets WHERE budget_key=?',
                               (budget_key,)).fetchone()[0]

    def reserve(self, ident, fence, *, budget_key=None, call_limit=None, additional_budget_keys=()):
        activation = self.activation()
        if activation.get('writer_enabled') is not True:
            raise ValueError('comparison_cutover_fence_incomplete')
        if activation['writer_epoch'] != fence:
            raise ValueError('comparison_writer_fenced')
        budgets=set(additional_budget_keys)
        if budget_key is not None:budgets.add(budget_key)
        if budgets:
            if type(call_limit) is not int or call_limit < 0:
                raise ValueError('comparison_call_limit_invalid')
            if any(not isinstance(k,str) or not k for k in budgets):
                raise ValueError('comparison_call_budget_key_invalid')
            if any(self.budget_used(k) >= call_limit for k in budgets):
                raise ValueError('comparison_daily_call_budget_exhausted')
        attempt = uuid.uuid4().hex
        updated = self.db.execute("UPDATE requests SET state='reserved' WHERE id=? AND state='planned'", (ident,))
        if updated.rowcount != 1:
            raise ValueError('comparison_request_not_available')
        self.db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?)',
                        (attempt, ident, 'reserved', None, fence, time.time(), 'provider'))
        for key in sorted(budgets):
            self.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',(attempt,key))
        self.commit()
        return attempt

    def finish(self, attempt, record):
        row = self.db.execute('SELECT request_id,state,result_obj FROM attempts WHERE attempt=?', (attempt,)).fetchone()
        if not row:
            raise ValueError('comparison_attempt_missing')
        obj = self.put(record)
        self.commit()  # immutable response survives a later metadata failure
        journal = self.root / 'response-journal.jsonl'
        with journal.open('ab') as f:
            f.write(encode(dict(attempt=attempt, result_obj=obj)) + b'\n')
            f.flush()
            os.fsync(f.fileno())
        self._finish_record(attempt, obj)
        self.commit()
        (self.root / 'landing' / (attempt + '.json')).unlink(missing_ok=True)

    def land_response(self, attempt, record):
        # Called by transport threads before returning to the main writer.
        # Only in-flight responses use individual files; they are packed and
        # removed after the durable journal/metadata commit.
        atomic_json(self.root / 'landing' / (attempt + '.json'),
                    dict(attempt=attempt, record=record))

    def _finish_record(self, attempt, obj):
        row = self.db.execute('SELECT request_id,state,result_obj FROM attempts WHERE attempt=?', (attempt,)).fetchone()
        if not row:
            raise ValueError('comparison_journal_attempt_missing')
        record = self.get(obj)
        response = (record.get('result') or {}).get('provider_provenance', {}).get('response_id')
        self.db.execute('INSERT OR IGNORE INTO attempt_responses VALUES(?,?)', (attempt, obj))
        if row[2] and row[2] != obj:
            previous = self.get(row[2])
            old_response = (previous.get('result') or {}).get('provider_provenance', {}).get('response_id')
            if old_response:
                # Replay of an earlier uncertain record, or an extra late
                # response, cannot change the first actual chosen response.
                return
            if not response:
                return
        state = 'completed' if response else 'reserved'
        self.db.execute('UPDATE attempts SET state=?,result_obj=? WHERE attempt=?', (state, obj, attempt))
        if response:
            # First durable actual response wins; labels never select attempts.
            self.db.execute("UPDATE requests SET state='completed',result_obj=coalesce(result_obj,?) WHERE id=?", (obj, row[0]))
        else:
            self.db.execute("UPDATE requests SET state='reserved' WHERE id=? AND state!='completed'", (row[0],))

    def reconcile(self):
        for landed in sorted((self.root / 'landing').glob('*.json')):
            value = json.loads(landed.read_text())
            self.finish(value['attempt'], value['record'])
        path = self.root / 'response-journal.jsonl'
        if not path.exists():
            return
        cursor = self.checkpoint('journal_cursor') or {'offset': 0}
        with path.open('rb') as f:
            f.seek(cursor['offset'])
            while line := f.readline():
                if not line.endswith(b'\n'):
                    raise ValueError('comparison_journal_partial_tail')
                row = json.loads(line)
                self._finish_record(row['attempt'], row['result_obj'])
                cursor['offset'] = f.tell()
        self.checkpoint('journal_cursor', cursor)
        self.commit()

    def snapshot(self, generation):
        row = self.db.execute('SELECT expected FROM generations WHERE generation=?', (generation,)).fetchone()
        if not row:
            raise ValueError('comparison_generation_missing')
        groups = {}
        count = 0
        for p, in self.db.execute('SELECT partition_id FROM generation_parts WHERE generation=? ORDER BY partition_id', (generation,)):
            values = list(self.db.execute('''SELECT m.id,r.state,CASE WHEN m.result_override>0 THEN m.result_override ELSE r.result_obj END
              FROM partition_members pm JOIN members m ON m.id=pm.member_id JOIN requests r ON r.id=m.request_id
              WHERE pm.partition_id=? ORDER BY m.id''', (p,)))
            groups[str(p)] = self.put(values)
            count += len(values)
        if count != row[0]:
            raise ValueError('comparison_snapshot_expected_missing')
        manifest = dict(schema=FORMAT, generation=generation, expected=count, partitions=groups,
                        response_selection='first_durable_actual_or_preserved_legacy_selection')
        h = digest(manifest)
        self.db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?)', (h, self.put(manifest)))
        self.commit()
        return dict(snapshot_sha256=h, **manifest)

    def orphan_packs(self, *, remove=False):
        """Only unindexed crash debris; indexed/planned/snapshot objects persist.

        Call with the writer lock held. There is deliberately no age-based
        retirement of a comparison, request, attempt, or published object.
        """
        if self.readonly or self._guard is None:
            raise ValueError('comparison_gc_writer_lock_required')
        self.commit()
        referenced = {r[0] for r in self.db.execute('SELECT DISTINCT pack FROM objects')}
        candidates = []
        for path in sorted((self.root / 'packs').iterdir()):
            if path.name in referenced or path.is_symlink() or not path.is_file():
                continue
            if not (path.name.endswith('.pack') or path.name.endswith('.pack.partial')):
                continue
            stat = path.stat()
            candidates.append(dict(path=str(path), sha256=file_hash(path), bytes=stat.st_size))
        if remove:
            # A manifest is durable before destructive cleanup.
            atomic_json(self.root / 'orphan-gc-dry-run.json', candidates)
            for row in candidates:
                path = Path(row['path'])
                if file_hash(path) != row['sha256']:
                    raise ValueError('comparison_gc_source_changed')
                path.unlink()
            fsync_directory(self.root / 'packs')
            atomic_json(self.root / 'orphan-gc-removal.json', candidates)
        return candidates

    def verify_objects(self):
        count = 0
        for ident, in self.db.execute('SELECT id FROM objects ORDER BY id'):
            self.get(ident)
            count += 1
        return count
