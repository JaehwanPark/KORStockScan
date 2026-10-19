"""Bounded offline sort/dedup and immutable evidence shards.

SQLite is a disposable task-local sort/index, never an operational ledger or
source. Durable evidence is content-addressed JSON with bounded fanout. This
package owns storage constraints; it cannot publish policy or submit orders.
"""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import sqlite3
import stat
import tempfile
from .research_disk_budget import temporary, INDEX_LIMIT

from .research_input_budget import Claim
from .holding_window_generation import byte_generation, source_stat

SCHEMA = 'bounded_research_evidence_tree_v1'
RECORD_BYTES = 64 * 1024
LEAF_BYTES = 256 * 1024
FANOUT = 256
INDEX_CACHE_BYTES = 8 * 1024 * 1024
TEMP_DISK_BYTES = 4 * 1024 * 1024 * 1024
_INLINE = ContextVar('bounded_research_inline_tree',default=False)


@contextmanager
def compact_trees():
    """Small evidence lives inside its sealed parent; large trees stay shards."""
    token=_INLINE.set(True)
    try:yield
    finally:_INLINE.reset(token)


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(',', ':'), allow_nan=False).encode()


def logical_value(value):
    """Physical shard references cannot perturb a semantic generation."""
    if isinstance(value, dict):
        if value.get('schema') == SCHEMA and 'logical_sha256' in value:
            return {k:value[k] for k in ('schema','count','logical_sha256')}
        return {k:logical_value(v) for k,v in value.items()}
    if isinstance(value, list):
        return [logical_value(v) for v in value]
    return value


def safe_path(root, name):
    root, name = Path(root), Path(name)
    if name.is_absolute() or '..' in name.parts:
        raise ValueError('research_storage_path_invalid')
    path = root / name
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('research_storage_path_invalid')
    return path


def copy_tree(source_root,destination_root,reference):
    """Copy sealed evidence only, retaining both physical and logical hashes."""
    for _ in iter_tree(source_root,reference,copy_to=destination_root):pass


@contextmanager
def index(root, *, disk_limit=INDEX_LIMIT):
    root = Path(root)
    safe_path(root, 'scratch')
    root.mkdir(parents=True, exist_ok=True)
    # A private scratch database cannot be mistaken for a source or a resume
    # receipt. Completed JSON shards alone are reusable durable evidence.
    with temporary(disk_limit),Claim(INDEX_CACHE_BYTES), tempfile.TemporaryDirectory(prefix='.sort-', dir=root) as name:
        connection = sqlite3.connect(Path(name)/'index.sqlite')
        try:
            connection.execute('PRAGMA journal_mode=OFF')
            # This database is disposable sorting state, never a source or a
            # resume receipt. Only sealed JSON evidence needs fsync durability.
            connection.execute('PRAGMA synchronous=OFF')
            connection.execute('PRAGMA temp_store=FILE')
            connection.execute('PRAGMA mmap_size=0')
            connection.execute('PRAGMA cache_size=-4096')
            page_size = connection.execute('PRAGMA page_size').fetchone()[0]
            connection.execute(f'PRAGMA max_page_count={max(1, disk_limit//page_size)}')
            connection.execute('CREATE TABLE records (id TEXT PRIMARY KEY, sha TEXT NOT NULL, '
                               'body TEXT NOT NULL, conflicted INTEGER NOT NULL DEFAULT 0, '
                               'copies INTEGER NOT NULL DEFAULT 1) WITHOUT ROWID')
            yield connection
        finally:
            connection.close()


def put(connection, identity, value, *, content_sha=None):
    if not isinstance(identity, str) or not identity or len(identity.encode()) > 1024:
        raise ValueError('research_index_identity_invalid')
    raw = encoded(value)
    if len(raw) > RECORD_BYTES:
        raise ValueError('research_index_record_partition_required')
    sha = content_sha or hashlib.sha256(raw).hexdigest()
    try:
        connection.execute('INSERT INTO records(id,sha,body) VALUES (?,?,?) '
            'ON CONFLICT(id) DO UPDATE SET copies=copies+1, '
            'conflicted=CASE WHEN records.sha != excluded.sha THEN 1 ELSE conflicted END, '
            'body=CASE WHEN records.sha = excluded.sha AND excluded.body < records.body '
            'THEN excluded.body ELSE records.body END',
            (identity, sha, raw.decode()))
    except sqlite3.OperationalError as exc:
        if 'full' in str(exc).lower():
            raise ValueError('research_sort_disk_budget_exceeded') from exc
        raise


def records(connection, *, conflicts=False):
    for identity, body, copies in connection.execute(
            'SELECT id,body,copies FROM records WHERE conflicted=? ORDER BY id', (int(conflicts),)):
        yield identity, json.loads(body), copies


def compact_outcomes(root, value):
    """Large candidate sets remain evidence trees, never oversized index rows."""
    if len(encoded(value))<=RECORD_BYTES: return value
    outcomes=value.get('outcomes')
    if not isinstance(outcomes,dict): raise ValueError('research_index_record_partition_required')
    ref=write_tree(root,({'key':key,'value':row} for key,row in sorted(outcomes.items())))
    result={k:v for k,v in value.items() if k!='outcomes'};result['outcomes_ref']=ref
    if len(encoded(result))>RECORD_BYTES: raise ValueError('research_index_context_partition_required')
    return result


def expand_outcomes(root, value):
    if 'outcomes_ref' not in value: return value
    result={k:v for k,v in value.items() if k!='outcomes_ref'}
    result['outcomes']={row['key']:row['value'] for row in iter_tree(root,value['outcomes_ref'])}
    return result


def _write(root, body, quota=None):
    from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
    raw = encoded(body)
    sha = hashlib.sha256(raw).hexdigest()
    name = 'shards/' + sha + '.json'
    path = safe_path(root, name)
    if path.exists():
        if byte_generation(path)['sha256'] != sha:
            raise ValueError('research_immutable_shard_changed')
    else:
        if quota is not None:
            if quota['used']+len(raw)>quota['limit']:
                raise ValueError('research_cache_budget_exceeded')
            quota['used']+=len(raw)
        _atomic(path, body)
    return {'path': name, 'sha256': sha, 'count': body['count'], 'size': len(raw)}


def write_tree(root, rows, *, quota=None, inline=None):
    """Canonical row stream digest does not depend on physical leaf sizes."""
    root = Path(root)
    logical = hashlib.sha256()
    levels, chunk, size, total = [[]], [], 0, 0

    def append(reference, level=0):
        if level == len(levels):
            levels.append([])
        levels[level].append(reference)
        if len(levels[level]) == FANOUT:
            refs = levels[level]; levels[level] = []
            append(_write(root, {'schema':SCHEMA, 'kind':'node',
                                'count':sum(r['count'] for r in refs), 'children':refs},quota), level+1)

    def flush():
        nonlocal chunk, size
        if chunk:
            append(_write(root, {'schema':SCHEMA, 'kind':'leaf', 'count':len(chunk), 'rows':chunk},quota))
            chunk, size = [], 0

    with Claim(LEAF_BYTES*8):
        for row in rows:
            raw = encoded(row)
            if len(raw) > RECORD_BYTES:
                raise ValueError('research_shard_record_partition_required')
            if chunk and size + len(raw) + 1 > LEAF_BYTES:
                flush()
            chunk.append(row); size += len(raw)+1; total += 1
            logical.update(encoded(logical_value(row))+b'\n')
        if (_INLINE.get() if inline is None else inline) and not any(levels):
            body={'schema':SCHEMA,'kind':'inline','count':total,'rows':chunk}
            raw=encoded(body)
            if len(raw)<=8192:
                return {**body,'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw),
                        'logical_sha256':logical.hexdigest()}
        flush()
        # Drain the lower levels in order. A completed higher block precedes
        # any unfinished lower block; never flatten the global reference list.
        for level in range(len(levels)-1):
            if levels[level]:
                refs = levels[level]; levels[level] = []
                append(_write(root, {'schema':SCHEMA, 'kind':'node',
                                    'count':sum(r['count'] for r in refs), 'children':refs},quota), level+1)
        refs = levels[-1]
        reference = _write(root, {'schema':SCHEMA, 'kind':'node', 'count':total, 'children':refs},quota)
    return {**reference, 'schema':SCHEMA, 'logical_sha256':logical.hexdigest()}


def iter_tree(root, reference, *, copy_to=None):
    """Validate every consumed leaf and root count; bounded depth/fanout."""
    logical, total = hashlib.sha256(), 0

    def walk(ref, depth=0):
        if depth > 16:
            raise ValueError('research_tree_depth_invalid')
        if ref.get('kind')=='inline':
            if set(ref)!={'schema','kind','count','rows','sha256','size','logical_sha256'}:
                raise ValueError('research_inline_contract_invalid')
            raw=encoded({k:ref[k] for k in ('schema','kind','count','rows')})
            if (len(raw)>8192 or len(raw)!=ref['size'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']
                or ref['schema']!=SCHEMA or type(ref['count']) is not int
                or not isinstance(ref['rows'],list) or len(ref['rows'])!=ref['count']):
                raise ValueError('research_inline_generation_invalid')
            for row in ref['rows']:
                if len(encoded(row))>RECORD_BYTES:raise ValueError('research_shard_record_invalid')
                yield row
            return
        path = safe_path(root, ref['path'])
        before = path.stat()
        if (type(ref.get('size')) is not int or not 0 <= ref['size'] <= 4*1024*1024
                or not stat.S_ISREG(before.st_mode) or before.st_size != ref['size']):
            raise ValueError('research_shard_generation_changed')
        with Claim(before.st_size*8):
            # Validate the actual bounded bytes once. A grown or replaced file
            # cannot turn a small sealed reference into an unbounded hash/read.
            with path.open('rb') as handle:
                raw = handle.read(ref['size'] + 1)
            if (len(raw) != ref['size'] or hashlib.sha256(raw).hexdigest() != ref['sha256']
                    or source_stat(path.stat()) != source_stat(before)):
                raise ValueError('research_shard_generation_changed')
            body = json.loads(raw)
            if body.get('schema') != SCHEMA or body.get('count') != ref['count']:
                raise ValueError('research_shard_contract_invalid')
            count = 0
            if body.get('kind') == 'leaf':
                if not isinstance(body.get('rows'), list) or len(body['rows']) != body['count']:
                    raise ValueError('research_shard_census_invalid')
                for row in body['rows']:
                    if len(encoded(row)) > RECORD_BYTES:
                        raise ValueError('research_shard_record_invalid')
                    count += 1
                    yield row
            elif body.get('kind') == 'node':
                children = body.get('children')
                if not isinstance(children, list) or len(children) > FANOUT:
                    raise ValueError('research_shard_fanout_invalid')
                for child in children:
                    for row in walk(child, depth+1):
                        count += 1
                        yield row
            else:
                raise ValueError('research_shard_kind_invalid')
            if count != body['count']:
                raise ValueError('research_shard_census_invalid')
            if source_stat(path.stat()) != source_stat(before):
                raise ValueError('research_shard_generation_changed')
            if copy_to is not None:
                from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
                target=safe_path(copy_to,ref['path'])
                existing=target.exists()
                error='research_immutable_shard_changed' if existing else 'research_copied_shard_changed'
                if not existing:
                    _atomic(target,body)
                target_before=target.stat()
                if not stat.S_ISREG(target_before.st_mode) or target_before.st_size!=len(raw):
                    raise ValueError(error)
                with Claim(len(raw)*2):
                    with target.open('rb') as handle:
                        copied=handle.read(len(raw)+1)
                    if copied!=raw or source_stat(target.stat())!=source_stat(target_before):
                        raise ValueError(error)

    for row in walk(reference):
        logical.update(encoded(logical_value(row))+b'\n'); total += 1
        yield row
    if total != reference['count'] or logical.hexdigest() != reference['logical_sha256']:
        raise ValueError('research_tree_logical_generation_invalid')
