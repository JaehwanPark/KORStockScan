"""Bounded client-attempt accounting. No payloads, credentials or disk I/O.

Started attempts include errors/timeouts. Followers and cache consumers never
claim a physical attempt. Unfinished transport work remains in-flight.
"""
from collections import Counter, OrderedDict, deque
from threading import Lock, local
from urllib.parse import urlsplit
import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LOCK = Lock()
_COUNTS = OrderedDict()
_DEMAND = Counter()
_RECENT = deque(maxlen=128)
_SERIAL = 0
_START = time.time()
_LIMIT = 256
_MINUTES = OrderedDict()
_MINUTE_LIMIT = 512
_KST = ZoneInfo('Asia/Seoul')
_LOCAL = local()
_RELEASE_ROOT = str(Path(__file__).resolve().parents[2])
try:
    _PROCESS_START_TICKS = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
except (OSError, IndexError):
    _PROCESS_START_TICKS = None


def demand(api_id, source):
    with _LOCK:
        key = (str(api_id)[:16], str(source)[:40])
        if key not in _DEMAND and len(_DEMAND) >= _LIMIT:
            key = ('overflow', 'unknown')
        _DEMAND[key] += 1


def measured_http_call(call, url, *, telemetry_owner, telemetry_class='runtime_required',
                       telemetry_code='not_applicable', telemetry_logical_id=None, **kwargs):
    global _SERIAL
    headers = kwargs.get('headers') or {}
    api = str(headers.get('api-id') or ('oauth' if '/oauth' in url else 'unknown'))[:16]
    origin = urlsplit(url).netloc
    token = str(headers.get('authorization') or '')
    scope = hashlib.sha256((origin + '|' + token).encode()).hexdigest()[:20]
    kind = 'auth' if api == 'oauth' else 'order' if api in {'kt10000','kt10001','kt10002','kt10003','kt10004','kt10005','kt10006','kt10007'} else 'read'
    code = str(telemetry_code)
    if not (len(code) in {6,9} and code[:6].isdigit()):
        code = 'not_applicable'
    key = (kind, api, str(telemetry_owner)[:80], str(telemetry_class)[:32], code, scope)
    started = time.time()
    started_kst = datetime.fromtimestamp(started, _KST)
    perf = time.perf_counter()
    with _LOCK:
        if key not in _COUNTS and len(_COUNTS) >= _LIMIT:
            key = (kind, 'overflow', 'unknown', 'unknown', 'not_applicable', 'unknown')
        counts = _COUNTS.setdefault(key, Counter())
        minute_key = (started_kst.strftime('%Y-%m-%dT%H:%M'), key)
        minute = _MINUTES.setdefault(minute_key, Counter())
        if len(_MINUTES) > _MINUTE_LIMIT:
            _MINUTES.popitem(last=False)
        _SERIAL += 1
        attempt = f'{os.getpid()}:{_START:.6f}:{_SERIAL}'
        counts['started'] += 1
        minute['started'] += 1
        record = dict(attempt_id=attempt, logical_id=telemetry_logical_id,
            started_epoch=started, started_kst_date=started_kst.date().isoformat(),
            process_start_ticks=_PROCESS_START_TICKS, release_root=_RELEASE_ROOT,
            request_code=code, route=('SOR' if code.endswith('_AL') else 'NXT' if code.endswith('_NX') else 'KRX' if code.isdigit() else 'unknown'),
            session='unknown_at_transport', kind=kind, api_id=api, owner=key[2], outcome='inflight_unknown')
        _RECENT.append(record)
    outcome = 'exception'
    status = None
    try:
        response = call(url, **kwargs)
        _LOCAL.response_id, _LOCAL.record = id(response), record
        status = getattr(response, 'status_code', None)
        outcome = 'response'
        return response
    except Exception as exc:
        outcome = 'timeout' if 'timeout' in type(exc).__name__.lower() else 'exception'
        raise
    finally:
        with _LOCK:
            counts['terminal'] += 1
            counts[outcome] += 1
            minute['terminal'] += 1
            minute[outcome] += 1
            record.update(completed_epoch=time.time(),outcome=outcome,http_status=status,
                          elapsed_sec=round(time.perf_counter()-perf,6),
                          body_return_code='unknown_at_transport', response_bytes='unknown_at_transport')


def record_decoded_response(response, data):
    """Join existing decode; never decode twice or retain response/body bytes."""
    if getattr(_LOCAL, 'response_id', None) != id(response) or not isinstance(data, dict):
        return
    value = data.get('return_code', data.get('rt_cd'))
    value = str(value) if type(value) in (int, str) else 'unknown'
    if len(value) > 12 or not value.lstrip('-').isdigit():
        value = 'unknown'
    raw = getattr(response, 'content', None)
    size = len(raw) if isinstance(raw, bytes) else 'unknown_at_transport'
    with _LOCK:
        _LOCAL.record.update(body_return_code=value, response_bytes=size)


def snapshot():
    with _LOCK:
        buckets = [dict(kind=k[0], api_id=k[1], owner=k[2], request_class=k[3],
            request_code=k[4], origin_token_digest=k[5], **dict(v),
            inflight_unknown=v['started']-v['terminal']) for k,v in _COUNTS.items()]
        return dict(schema='kiwoom_client_attempts_v1', pid=os.getpid(),
            process_start_ticks=_PROCESS_START_TICKS, release_root=_RELEASE_ROOT,
            started_epoch=_START, observed_epoch=time.time(), buckets=buckets,
            minute_buckets=[dict(started_kst_minute=k[0], kind=k[1][0],api_id=k[1][1],owner=k[1][2],
                request_class=k[1][3],request_code=k[1][4],origin_token_digest=k[1][5],**dict(v),
                inflight_unknown=v['started']-v['terminal']) for k,v in _MINUTES.items()],
            demands=[dict(api_id=k[0],source=k[1],count=v) for k,v in _DEMAND.items()],
            recent_attempts=[dict(r) for r in _RECENT], decision_authority='none',
            counting_basis='physical_client_start_not_server_receipt',
            terminal_equation='started=terminal+inflight_unknown',
            retained_attempt_limit=128, bucket_limit=_LIMIT, minute_bucket_limit=_MINUTE_LIMIT,
            unobserved_dimensions=['server_receipt','session_at_transport','undecoded_response_body'],
            admission_source='existing_kiwoom_read_request_control_receipts')
