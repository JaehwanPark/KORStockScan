"""REST-adjusted minute history: immutable completed revisions, fresh forming.

A daily derived SQLite store deduplicates bars across revisions and consumers.
Readers pin private snapshots; corrections never alter returned inputs. There
is no order authority, raw WS composition, or deletion of referenced revisions.
"""
from copy import deepcopy
from contextlib import closing
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo
import zlib

KST = ZoneInfo('Asia/Seoul')
SCHEMA = 'main_rest_minute_history_v2'
MAX_ROWS = 900
MAX_DATABASE_BYTES = 128 * 1024 * 1024
MAX_REVISIONS_PER_SCOPE = 2048


def key(scope, item, date, session='unspecified'):
    return dict(schema=SCHEMA, auth_scope=list(scope), item=item, date=date,
                session=session, interval_sec=60, adjustment='ka10080:upd_stkpc_tp=1',
                time_basis='provider_bar_open_kst')


def _bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True,
                      separators=(',', ':'), allow_nan=False).encode()


def _digest(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _path(root, identity):
    day = identity['date']
    datetime.strptime(day, '%Y%m%d')
    return Path(root) / 'runtime' / 'main_minute_history' / day / 'completed.sqlite3'


def _unpack(raw):
    decoder = zlib.decompressobj()
    body = decoder.decompress(raw, 2 * 1024 * 1024 + 1)
    if len(body) > 2 * 1024 * 1024 or not decoder.eof or decoder.unused_data:
        raise ValueError('invalid history manifest')
    sealed = json.loads(body)
    if _digest(sealed['value']) != sealed['sha256']:
        raise ValueError('history receipt checksum mismatch')
    return sealed['value']


def _pack(value):
    return zlib.compress(_bytes(dict(value=value, sha256=_digest(value))))


def _completed(rows, now):
    cutoff = datetime.fromtimestamp(now, KST).strftime('%Y%m%d%H%M00')
    completed, forming, seen = [], [], set()
    for row in rows:
        stamp = row['source_timestamp']
        datetime.strptime(stamp, '%Y%m%d%H%M%S')
        if stamp in seen or stamp > cutoff:
            raise ValueError('duplicate or future source bar')
        seen.add(stamp)
        for field in ('시가', '고가', '저가', '현재가', '거래량'):
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError('invalid source OHLCV')
        if not (0 < row['저가'] <= min(row['시가'], row['현재가'])
                <= max(row['시가'], row['현재가']) <= row['고가']):
            raise ValueError('invalid source OHLC bounds')
        (forming if stamp == cutoff else completed).append(deepcopy(row))
    return sorted(completed, key=lambda r: r['source_timestamp']), forming


def read(root, identity, *, now, limit, include_forming=True, revision=None):
    """Read a provider-verified cutoff or an available named historical revision."""
    try:
        path = _path(root, identity)
        if not path.exists() or not math.isfinite(now) or limit < 1:
            return None
        with closing(sqlite3.connect(path.absolute().as_uri()+'?mode=ro', uri=True, timeout=.025)) as db:
            db.execute('BEGIN')
            current = db.execute('SELECT revision, receipt FROM current WHERE scope=?',
                                 (_digest(identity),)).fetchone()
            if current is None:
                return None
            selected = revision or current[0]
            stored = db.execute('SELECT manifest, available FROM revisions WHERE hash=? AND scope=?',
                                (selected, _digest(identity))).fetchone()
            if stored is None or stored[1] > now:
                return None
            manifest = _unpack(stored[0])
            if _digest(manifest) != selected or manifest['identity'] != identity:
                return None
            receipt = _unpack(current[1]) if revision is None else manifest['first_receipt']
            if receipt['received_at'] > now:
                return None
            if revision is None and int(now//60) != receipt['verified_cutoff']:
                return None
            if include_forming and (revision is not None or now >= receipt['forming_expires_at']):
                return None
            hashes = manifest['bar_hashes']
            if len(hashes) > MAX_ROWS:
                return None
            rows = {}
            if hashes:
                query = 'SELECT hash, content FROM bars WHERE hash IN ('+','.join('?' for _ in hashes)+')'
                for fingerprint, content in db.execute(query, hashes):
                    row = json.loads(content)
                    if _digest(row) != fingerprint:
                        return None
                    rows[fingerprint] = row
            values = [rows[h] for h in hashes]
            if include_forming:
                values += receipt['forming']
            if len(values) < limit:
                return None
            meta = dict(receipt['source_meta'], shared_history_schema=SCHEMA,
                shared_history_revision_sha256=selected,
                shared_history_available_at=stored[1],
                shared_history_completed_cutoff=receipt['verified_cutoff'],
                shared_history_reused=True, requested_limit=limit,
                shared_history_forming_included=include_forming,
                shared_history_completed_count=len(hashes), shared_history_selected_at=now,
                shared_history_source_method='rest_adjusted_completed_revision',
                read_response_cache_status='hit', read_response_cache_caller_http_attempt_count=0,
                read_singleflight_caller_http_attempt_count=0)
            return deepcopy(values[-limit:]), meta
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError, zlib.error):
        return None


def publish(root, identity, rows, source_meta, *, now, consumption_receipt=None):
    """Publish with CAS; recheck the full returned overlap on every refresh."""
    received = source_meta.get('rest_received_ts_ms')
    if (not rows or len(rows) > MAX_ROWS or type(received) is not int
            or not 0 <= now-received/1000 <= 5
            or source_meta.get('request_code') != identity['item']):
        return False
    completed, forming = _completed(rows, now)
    if not completed:
        return False
    path = _path(root, identity)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size >= MAX_DATABASE_BYTES:
        return False
    receipt = dict(received_at=received/1000, verified_cutoff=int(now//60),
        forming=forming, forming_expires_at=min(received/1000+3,
            source_meta.get('read_response_cache_expires_at', received/1000+3)),
        source_meta=deepcopy(source_meta), source_rows_sha256=_digest(rows))
    scope = _digest(identity)
    with closing(sqlite3.connect(path, timeout=.025)) as db, db:
        os.chmod(path, 0o600)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA wal_autocheckpoint=64')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS bars(hash TEXT PRIMARY KEY, content BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS revisions(hash TEXT PRIMARY KEY, scope TEXT NOT NULL,
                available REAL NOT NULL, manifest BLOB NOT NULL);
            CREATE INDEX IF NOT EXISTS revision_scope ON revisions(scope);
            CREATE TABLE IF NOT EXISTS current(scope TEXT PRIMARY KEY, revision TEXT NOT NULL,
                received REAL NOT NULL, receipt BLOB NOT NULL);
        ''')
        db.execute('BEGIN IMMEDIATE')
        if db.execute('PRAGMA page_count').fetchone()[0] * db.execute('PRAGMA page_size').fetchone()[0] >= MAX_DATABASE_BYTES:
            return False
        old = db.execute('SELECT received, revision FROM current WHERE scope=?', (scope,)).fetchone()
        if old and old[0] > receipt['received_at']:
            return False
        previous = db.execute('SELECT manifest FROM revisions WHERE hash=?', (old[1],)).fetchone() if old else None
        previous_manifest = _unpack(previous[0]) if previous else None
        prefix = []
        if previous_manifest:
            if _digest(previous_manifest) != old[1] or previous_manifest['identity'] != identity:
                raise ValueError('history parent revision mismatch')
            old_hashes = previous_manifest['bar_hashes']
            if old_hashes:
                query = 'SELECT hash, content FROM bars WHERE hash IN ('+','.join('?' for _ in old_hashes)+')'
                previous_rows = {}
                for fingerprint, content in db.execute(query, old_hashes):
                    row = json.loads(content)
                    if _digest(row) != fingerprint:
                        raise ValueError('history parent bar mismatch')
                    previous_rows[fingerprint] = row
                prefix = [previous_rows[h] for h in old_hashes
                          if previous_rows[h]['source_timestamp'] < completed[0]['source_timestamp']]
            prefix = prefix[-max(0, MAX_ROWS-len(completed)):] if len(completed) < MAX_ROWS else []
            completed = prefix + completed
        hashes = [_digest(row) for row in completed]
        if previous_manifest and previous_manifest['bar_hashes'] == hashes:
            revision = old[1]
        else:
            count = db.execute('SELECT count(*) FROM revisions WHERE scope=?', (scope,)).fetchone()[0]
            if count >= MAX_REVISIONS_PER_SCOPE:
                return False
            # Forming is a separate fresh receipt, never part of a completed revision.
            first_receipt = dict(receipt, forming=[])
            manifest = dict(schema=SCHEMA, identity=identity, bar_hashes=hashes,
                first_receipt=first_receipt, first_completed=completed[0]['source_timestamp'],
                last_completed=completed[-1]['source_timestamp'],
                prefix_revision_sha256=old[1] if prefix else None, prefix_count=len(prefix),
                adjustment_equivalence_to_ws='unproven',
                gap_policy='observed_provider_rows_no_synthetic_fill')
            revision = _digest(manifest)
            db.executemany('INSERT OR IGNORE INTO bars VALUES (?,?)',
                           [(h, _bytes(row)) for h, row in zip(hashes, completed)])
            db.execute('INSERT OR IGNORE INTO revisions VALUES (?,?,?,?)',
                       (revision, scope, receipt['received_at'], _pack(manifest)))
        db.execute('INSERT OR REPLACE INTO current VALUES (?,?,?,?)',
                   (scope, revision, receipt['received_at'], _pack(receipt)))
    if consumption_receipt is not None:
        consumption_receipt.update(shared_history_schema=SCHEMA,
            shared_history_revision_sha256=revision,
            shared_history_completed_cutoff=receipt['verified_cutoff'],
            shared_history_completed_count=len(hashes), shared_history_reused=False,
            shared_history_selected_at=now, shared_history_source_rows_sha256=_digest(rows),
            shared_history_source_method='rest_adjusted_completed_revision')
    return True
