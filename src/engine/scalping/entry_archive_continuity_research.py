"""Offline linkage of local probe lease receipts to archived price research.

These are local application log records, not broker packet parsers. A lease
proves a registration lifetime, never complete market capture or a real fill.
Second-resolution log times are intervals; do not invent subsecond ordering.
"""
from datetime import datetime
import json
import re
from zoneinfo import ZoneInfo

KST = ZoneInfo('Asia/Seoul')
MARKER = '[ZERO_BASE_EXACT_WS_LEASE] '
ITEM = re.compile(r'[0-9]{6}(?:_AL|_NX)?')
AUTHORITY = {
    'runtime_effect': False, 'allowed_runtime_apply': False,
    'actual_order_submitted': False, 'broker_order_forbidden': True,
    'decision_authority': 'offline_archive_continuity_diagnostic',
    'metric_role': 'source_quality_gate',
    'primary_decision_metric': 'receipt_bound_archive_recovery_count',
    'window_policy': 'frozen_20261002_non_samsung_target_first_22',
    'sample_floor': 'all_22_frozen_traces_with_missing_denominators',
    'source_quality_gate': 'exact_item_lease_id_clock_epoch_and_sealed_sources',
    'forbidden_uses': ['runtime_apply', 'realized_pnl', 'lease_as_market_continuity',
                       'cross_route_imputation', 'independent_holdout_claim'],
}


def parse_lease_log(lines, *, day):
    """Reject malformed target-day lease records; preserve original line numbers."""
    datetime.strptime(day, '%Y-%m-%d')
    records = []
    instances = []
    for number, line in enumerate(lines, 1):
        if not line.startswith('['+day+' '):
            continue
        is_instance = '[WS] 웹소켓 매니저 초기화 완료' in line
        if MARKER not in line and not is_instance:
            continue
        stamp = datetime.strptime(line[1:20], '%Y-%m-%d %H:%M:%S').replace(tzinfo=KST)
        if is_instance:
            instances.append(dict(at_lower=stamp.timestamp(), at_upper=stamp.timestamp()+1,
                                  log_line=number))
            continue
        payload = json.loads(line.split(MARKER, 1)[1])
        item, lease = payload.get('item'), payload.get('lease_id')
        epoch = payload.get('transport_epoch')
        if (not isinstance(item, str) or not ITEM.fullmatch(item)
                or not isinstance(lease, str) or not lease
                or type(epoch) is not int or epoch <= 0):
            raise ValueError('lease_identity_invalid')
        if payload.get('phase') == 'released':
            if payload.get('actual_order_submitted') is not False:
                raise ValueError('lease_release_authority_invalid')
            phase = 'release'
        elif payload.get('created') is True and payload.get('registered') is True:
            phase = 'create'
        else:
            phase = 'unconfirmed'
        records.append(dict(item=item, lease_id=lease, transport_epoch=epoch,
            phase=phase, at_lower=stamp.timestamp(), at_upper=stamp.timestamp()+1,
            log_line=number, payload=payload, log_instance_index=len(instances)))
    for r in records:
        index = r['log_instance_index']
        r['next_instance'] = instances[index] if index < len(instances) else None
    return records


def lease_intervals(records):
    """Only matching create/release identity produces a closed interval."""
    groups = {}
    for r in records:
        if r['phase'] == 'unconfirmed':
            continue
        key = (r['item'], r['lease_id'], r['transport_epoch'], r['log_instance_index'])
        group = groups.setdefault(key, {})
        if r['phase'] in group:
            raise ValueError('duplicate_lease_phase')
        group[r['phase']] = r
    intervals = []
    for (item, lease, epoch, instance), g in groups.items():
        create, release = g.get('create'), g.get('release')
        if create and release and release['at_upper'] <= create['at_lower']:
            raise ValueError('lease_release_precedes_creation')
        intervals.append(dict(item=item, lease_id=lease, transport_epoch=epoch,
            create=create, release=release,
            log_instance_index=instance, next_instance=(create or release)['next_instance'],
            status='closed_receipt' if create and release else 'incomplete_receipt'))
    return intervals


def bind_anchor_lease(row, intervals, *, target_at):
    """Classify entry overlap without equating a collector epoch to a WS epoch."""
    stamp = datetime.fromisoformat(row['ts'])
    if stamp.utcoffset() is None or row.get('symbol') == '005930':
        raise ValueError('anchor_scope_invalid')
    if not ITEM.fullmatch(row['request_code']) or row['request_code'][:6] != row['symbol']:
        raise ValueError('anchor_item_invalid')
    start = stamp.timestamp()
    if target_at <= start:
        raise ValueError('target_must_follow_entry')
    possible = [x for x in intervals if x['item'] == row['request_code']
                and x['create'] and x['create']['at_lower'] <= start
                and (not x.get('next_instance') or start < x['next_instance']['at_upper'])
                and (not x['release'] or start < x['release']['at_upper'])]
    result = dict(status='entry_lease_not_proven', continuous_capture_verified=False,
                  collector_transport_epoch_binding_verified=False, lease=None)
    if len(possible) != 1:
        if possible:
            result['status'] = 'overlapping_lease_identity_ambiguous'
        return result
    lease = possible[0]
    result['lease'] = lease
    if not lease['release']:
        result['status'] = 'entry_lease_release_missing'
        return result
    c, r = lease['create'], lease['release']
    result.update(
        status='entry_within_closed_lease' if c['at_upper'] <= start < r['at_lower']
               else 'entry_lease_second_boundary_ambiguous',
        release_after_entry_lower_sec=r['at_lower']-start,
        release_after_entry_upper_sec=r['at_upper']-start,
        released_definitely_before_target=r['at_upper'] <= target_at,
        target_before_release_definite=target_at < r['at_lower'],
    )
    return result


def receipt_bound_exit(path, binding):
    """Withdraw observed-event terminal values reached after proven release.

    Other nonterminals keep their reason. Unchanged terminals remain conditional
    on archived events, never promoted to complete operating replay.
    """
    out = {**path, 'continuous_capture_verified': False,
           'completed_operating_exit': False, 'source_registration_binding': binding['status']}
    release = (binding.get('lease') or {}).get('release')
    if release and path.get('exit_at') is not None and path['exit_at'] >= release['at_lower']:
        out.update(status='probe_release_precedes_exit' if path['exit_at'] >= release['at_upper']
                   else 'probe_release_exit_order_ambiguous', net_pct=None, exit_at=None,
                   exit_price=None, runtime_net_pct=None, rule=None,
                   blocked_at=release['at_lower'], previous_conditional_path=path)
    return out
