"""Read-only diagnostics for the pinned normalized reversal kernel.

Runtime source projection owns this module, independently of research kernel
and auxiliary input contracts. No price, feature, policy or decision mutation.
"""
from datetime import datetime
import math

from src.engine.scalping import continuous_reversal as K


def project(snapshot, *, symbol, venue, session, now, item, envelope=None):
    if snapshot is None:
        return {'status': 'not_observed', 'reason': 'no_current_reversal'}
    event, _ = snapshot
    market = K.market_bucket(session)
    key = (symbol, venue, item, market, datetime.fromtimestamp(now, K.KST).date())
    with K._LOCK:
        state = K._STATES.get(key)
        if (state is None or state.turn is None
                or state.turn['event_id'] != event['event_id']):
            return {'status': 'not_observed', 'reason': 'reversal_revision_changed'}
        start = state.segment_start
        # Native rows are append-only values; retain references briefly, then
        # compute diagnostics outside the ingestion lock.
        rows = list(state.rows)
    t = event['epoch']
    elapsed = max(0., t-start)
    reset = 'initial_observation_or_process_restart'
    for i, row in enumerate(rows):
        if row[0] == start and i and not K.connected(rows[i-1], row):
            previous = rows[i-1]
            reset = ('source_stale_or_invalid' if not row[8] or not previous[8]
                else 'transport_epoch_changed' if row[1] != previous[1]
                else 'sequence_or_clock_gap')
            break
    status = 'warmup_after_' + reset
    if elapsed >= 120:
        window = [r for r in rows if t-120 <= r[0] <= t]
        valid = all(type(r[6]) in (int,float) and math.isfinite(r[6]) and r[6] > 0 for r in window)
        status = ('quantity_missing_or_invalid' if not valid else
                  'ready' if event['volume_ratio_60s'] is not None else 'previous_window_empty')
    body = dict(schema='continuous_reversal_source_diagnostics_v1', status='observed',
        event_id=event['event_id'], volume_ratio_source_status=status,
        volume_ratio_observed_seconds=elapsed, runtime_effect=False)
    if (isinstance(envelope, dict) and envelope.get('observed_epoch') == t
            and envelope.get('item') == item
            and str(event['event_id']).endswith(
                ':' + str(envelope.get('transport_epoch')) + ':' + str(envelope.get('route_sequence')))
            and isinstance(envelope.get('market_source_latency'), dict)):
        body['source_latency'] = dict(envelope['market_source_latency'])
    return body
