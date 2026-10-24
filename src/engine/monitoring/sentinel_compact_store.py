"""Sentinel-owned compressed row index; never a policy or source authority.

The source cache remains authoritative. A transaction binds every indexed row
and cursor to the cache's verified generation. Large field strings are decoded
only by consumers that request them; every original field and row survives.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import os
import tempfile
import subprocess
import zlib
from collections.abc import Mapping
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

# Fields read on every population/scope pass. All other fields remain available.
HOT_KEYS = frozenset(('ai_call_trigger_reason', 'tuning_authority_excluded_reason',
    'decision_market_scope', 'market_data_route', 'effective_venue',
    'rising_missed_effective_venue', 'market_venue', 'entry_venue',
    'holding_context_venue', 'venue', 'market_session_regime', 'market_session_bucket',
    'rising_missed_market_session_bucket', 'session_bucket', 'session',
    'market_session', 'entry_session', 'holding_context_session', 'actual_execution_venue',
    'reason', 'block_reason', 'blocked_reason', 'decision', 'action', 'resolution_reason',
    'score', 'ai_score', 'current_ai_score', 'ai_score_50_buy_hold_override',
    'latency_danger_reasons', 'terminal_reason', 'source_stage',
    'entry_submit_attempt_id', 'main_lifecycle_attempt_id', 'scanner_promotion_id',
    'entry_submit_attempt_parent_promotion_id', 'evaluation_attempt_id',
    'entry_evaluation_attempt_id', 'entry_mechanistic_evaluation_id',
    'metric_role', 'decision_authority', 'runtime_effect', 'gate_action',
    'allowed_runtime_apply', 'hard_block_allowed', 'order_authority',
    'actual_order_submitted', 'trading_runtime_effect',
    'entry_primary_decision_owner', 'entry_mechanistic_action', 'watch_origin',
    'entry_execution_sizing_plan_id', 'policy_bundle_hash', 'machine_bundle_sha256',
    'entry_setup_live_policy_candidate_contract_sha256', 'watch_admission_id',
    'watch_generation_id'))


def stamp(path):
    st = Path(path).stat()
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


@lru_cache(maxsize=128)
def _small_decode(body):
    return json.loads(zlib.decompress(body))


@lru_cache(maxsize=2)
def _large_decode(body):
    return json.loads(zlib.decompress(body))


class _PayloadReader:
    def __init__(self, path):
        self.path = path
        self.connection = sqlite3.connect(f'file:{path}?mode=ro', uri=True, isolation_level=None)
        self.connection.execute('PRAGMA cache_size=-4096')
        self.recent = OrderedDict()
        self.recent_bytes = 0

    def read(self, offset, expected):
        # No long-lived read transaction can block the next append/rebuild.
        key = (offset, expected)
        if key in self.recent:
            self.recent.move_to_end(key)
            return self.recent[key]
        row = self.connection.execute('SELECT body FROM payloads WHERE offset=?', (offset,)).fetchone()
        if row is None or hashlib.sha256(row[0]).hexdigest() != expected:
            repair = sqlite3.connect(self.path, timeout=5)
            try:
                with repair:
                    repair.execute('DELETE FROM state')
            finally:
                repair.close()
            raise ValueError('sentinel_index_payload_corrupt')
        if len(row[0]) <= 8 * 1024 * 1024:
            self.recent[key] = row[0]
            self.recent_bytes += len(row[0])
            while len(self.recent) > 8192 or self.recent_bytes > 64 * 1024 * 1024:
                self.recent_bytes -= len(self.recent.popitem(last=False)[1])
        return row[0]

    def __del__(self):
        if hasattr(self, 'connection'):
            self.connection.close()


class CompactFields(Mapping):
    """Read-only string mapping with bounded shared decode storage."""
    __slots__ = ('reader', 'offset', 'digest', 'size', 'hot')

    def __init__(self, reader, offset, digest, size, hot):
        self.reader = reader
        self.offset = offset
        self.digest = digest
        self.size = size
        self.hot = hot

    @property
    def body(self):
        return self.reader.read(self.offset, self.digest)

    def _fields(self):
        # Bound retained decoded text to 128 * 64 KiB plus container overhead.
        return (_small_decode(self.body) if self.size <= 65536 else
                _large_decode(self.body) if self.size <= 8 * 1024 * 1024 else
                json.loads(zlib.decompress(self.body)))

    def __getitem__(self, key):
        if key in HOT_KEYS:
            value = self.hot[key]
            if value is not None:
                return value
        return self._fields()[key]

    def items(self):
        return self._fields().items()

    def __iter__(self):
        return iter(self._fields())

    def __len__(self):
        return len(self._fields())

    def __contains__(self, key):
        return key in self._fields()

    def __bool__(self):
        return True  # Avoid eagerly decoding every row during event loading.


def _pack(row):
    fields = row.get('fields') or {}
    if not isinstance(fields, dict):
        fields = {}
    fields = {str(k): str(v if v is not None else '').strip() for k, v in fields.items()}
    raw = json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    packed = zlib.compress(raw, 1)
    header = {k: v for k, v in row.items() if k != 'fields'}
    hot = {k: v if len(v.encode()) <= 512 else None for k, v in fields.items() if k in HOT_KEYS}
    digest = hashlib.sha256(packed).hexdigest()
    return json.dumps([header, len(raw), digest, hot], ensure_ascii=False, separators=(',', ':')), packed


class _FieldIdentity:
    __slots__ = ('source', 'digest')

    def __init__(self, source, digest):
        self.source, self.digest = source, digest

    def __hash__(self):
        return hash(self.digest)

    def __eq__(self, other):
        if not isinstance(other, _FieldIdentity) or self.digest != other.digest:
            return False
        left = self.source.body if isinstance(self.source, CompactFields) else self.source
        right = other.source.body if isinstance(other.source, CompactFields) else other.source
        return left == right


def fields_identity(fields):
    """Lossless canonical equality without retaining every decoded field tuple."""
    if isinstance(fields, CompactFields):
        return _FieldIdentity(fields, fields.digest)
    raw = json.dumps(dict(fields), sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    body = zlib.compress(raw, 1)
    return _FieldIdentity(body, hashlib.sha256(body).hexdigest())


def indexed_rows(cache_path, *, previous_stamp, expected_count):
    """Append verified new cache rows, otherwise replace the optional index.

    Call under the source-cache writer lock. Missing/corrupt index metadata
    cannot authorize an append cursor. SQLite commit precedes publication of
    its own complete generation; failed transactions leave the old generation.
    """
    cache_path = Path(cache_path)
    index_path = cache_path.with_suffix('.compact.sqlite')
    generation = stamp(cache_path)
    contract = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    connection = sqlite3.connect(index_path, timeout=5)
    from src.engine.sentinel_event_cache import _cache_object_decoder
    decode = _cache_object_decoder()
    try:
        connection.execute('PRAGMA journal_mode=DELETE')
        connection.execute('PRAGMA synchronous=FULL')
        connection.execute('PRAGMA cache_size=-4096')
        connection.execute('PRAGMA temp_store=FILE')
        connection.execute('CREATE TABLE IF NOT EXISTS rows (offset INTEGER PRIMARY KEY, body TEXT NOT NULL, sha TEXT NOT NULL)')
        connection.execute('CREATE TABLE IF NOT EXISTS payloads (offset INTEGER PRIMARY KEY, body BLOB NOT NULL)')
        connection.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)')
        saved = connection.execute('SELECT body FROM state WHERE id=1').fetchone()
        try:
            state = json.loads(saved[0]) if saved else {}
        except (TypeError, ValueError):
            state = {}
        same_contract = state.get('contract') == contract
        unchanged = same_contract and state.get('generation') == generation
        append = (same_contract and previous_stamp is not None
                  and state.get('generation') == previous_stamp
                  and state.get('offset') == previous_stamp[2]
                  and generation[:2] == previous_stamp[:2]
                  and generation[2] >= previous_stamp[2])
        with connection:
            if not unchanged:
                if not append:
                    connection.execute('DELETE FROM rows')
                    connection.execute('DELETE FROM payloads')
                offset = state['offset'] if append else 0
                with cache_path.open('rb') as source:
                    source.seek(offset)
                    while source.tell() < generation[2]:
                        line = source.readline()
                        if not line.endswith(b'\n') or source.tell() > generation[2]:
                            raise ValueError('sentinel_cache_partial_index_source')
                        try:
                            row = json.loads(line)
                        except ValueError:
                            continue  # Preserve the native cache's malformed-row exclusion.
                        if not isinstance(row, dict):
                            continue
                        body, payload = _pack(row)
                        sha = hashlib.sha256(body.encode()).hexdigest()
                        connection.execute('INSERT INTO rows VALUES (?, ?, ?)',
                                           (source.tell(), zlib.compress(body.encode(), 1), sha))
                        connection.execute('INSERT INTO payloads VALUES (?, ?)', (source.tell(), payload))
            count = (state.get('count') if unchanged else
                     connection.execute('SELECT count(*) FROM rows').fetchone()[0])
            if count != expected_count or stamp(cache_path) != generation:
                raise ValueError('sentinel_index_generation_or_population_changed')
            connection.execute('INSERT OR REPLACE INTO state VALUES (1, ?)',
                (json.dumps(dict(contract=contract, generation=generation,
                                 offset=generation[2], count=count)),))
        # Frozen result iterator, independent of a subsequent writer transaction.
        connection.execute('BEGIN')
        reader = _PayloadReader(index_path)
        cursor = connection.execute('SELECT offset, body, sha FROM rows ORDER BY offset')
        seen = 0
        for offset, body, sha in cursor:
            try:
                body = zlib.decompress(body)
            except (TypeError, zlib.error) as exc:
                raise ValueError('sentinel_index_row_corrupt') from exc
            if hashlib.sha256(body).hexdigest() != sha:
                raise ValueError('sentinel_index_row_corrupt')
            header, size, digest, hot = json.loads(body, object_pairs_hook=decode)
            header['fields'] = CompactFields(reader, offset, digest, size, hot)
            header['_sentinel_index_sha'] = sha
            seen += 1
            yield header
        if seen != count:
            raise ValueError('sentinel_index_population_corrupt')
    except (sqlite3.DatabaseError, ValueError):
        # Optional acceleration can be rebuilt; raw/cache custody is untouched.
        connection.rollback()
        try:
            with connection:
                connection.execute('DELETE FROM state')
        except sqlite3.DatabaseError:
            pass
        raise
    finally:
        connection.close()


def slim_summary_projection(path, loader, *, contract):
    """Reuse a content-bound small projection of an unchanged summary only."""
    path = Path(path)
    before = stamp(path)
    projection = path.with_name(path.name + '.sentinel-slim.json')
    try:
        # Optional cache corruption cannot hide a bad canonical summary.
        if projection.stat().st_size <= 32 * 1024 * 1024:
            value = json.loads(projection.read_text())
            body = value['body']
            encoded = json.dumps(body, sort_keys=True, separators=(',', ':')).encode()
            if (value['sha256'] == hashlib.sha256(encoded).hexdigest()
                    and body['source'] == str(path.resolve())
                    and body['generation'] == before and body['contract'] == contract
                    and isinstance(body['rows'], list) and stamp(path) == before):
                return body['rows']
    except (OSError, ValueError, KeyError, TypeError):
        pass
    rows = loader()
    if before != stamp(path):
        raise ValueError('summary_projection_source_changed_during_read')
    body = dict(source=str(path.resolve()), generation=before, contract=contract, rows=rows)
    encoded = json.dumps(body, sort_keys=True, separators=(',', ':')).encode()
    if len(encoded) > 32 * 1024 * 1024:
        return rows
    _optional_json_write(projection, dict(body=body, sha256=hashlib.sha256(encoded).hexdigest()))
    return rows


@lru_cache(maxsize=1)
def report_code_contract():
    """Bind pure report reuse to the process's complete source revision/delta."""
    root = Path(__file__).resolve().parents[3]
    digest = hashlib.sha256(Path(__file__).read_bytes())
    for arguments in (('rev-parse', 'HEAD'), ('diff', 'HEAD', '--', 'src')):
        result = subprocess.run(['git', *arguments], cwd=root, capture_output=True,
                                check=True, timeout=5)
        digest.update(result.stdout)
    # Untracked modules in an isolated reviewed checkout also own semantics.
    names = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '-z', '--', 'src'],
                           cwd=root, capture_output=True, check=True, timeout=5).stdout
    for name in names.split(b'\0'):
        if name.endswith(b'.py'):
            digest.update(name)
            digest.update((root / os.fsdecode(name)).read_bytes())
    return digest.hexdigest()


def summary_memo(directory, key, calculate):
    """At most 32 small exact-population results; failed readers recompute."""
    directory = Path(directory)
    path = directory / (key + '.json')
    try:
        if path.stat().st_size <= 32 * 1024 * 1024:
            stored = json.loads(path.read_text())
            body = stored['body']
            raw = json.dumps(body, sort_keys=True, separators=(',', ':')).encode()
            if stored['key'] == key and stored['sha256'] == hashlib.sha256(raw).hexdigest():
                return body
    except (OSError, ValueError, KeyError, TypeError):
        pass
    body = calculate()
    raw = json.dumps(body, sort_keys=True, separators=(',', ':')).encode()
    if len(raw) <= 32 * 1024 * 1024:
        _optional_json_write(path, dict(key=key, sha256=hashlib.sha256(raw).hexdigest(), body=body))
        try:
            _trim_summaries(directory, path)
        except OSError:
            pass  # Optional retention cannot invalidate a computed report.
    return body


def _trim_summaries(directory, path):
    candidates = [p for p in directory.glob('*.json') if len(p.stem) == 64
                  and all(c in '0123456789abcdef' for c in p.stem)]
    total = 0
    for position, old in enumerate(sorted(candidates, key=lambda p: p.stat().st_mtime_ns, reverse=True)):
        total += old.stat().st_size
        if total > 64 * 1024 * 1024 or position >= 32:
            if old != path:
                old.unlink(missing_ok=True)


def _optional_json_write(path, value):
    name = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.sentinel-', dir=path.parent)
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, separators=(',', ':'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    except OSError:
        pass  # Native computation already succeeded; this cache is optional.
    finally:
        if name is not None:
            try:
                Path(name).unlink(missing_ok=True)
            except OSError:
                pass
