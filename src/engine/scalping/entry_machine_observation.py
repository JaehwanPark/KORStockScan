"""Exact local Samsung observation selection; no submit or policy authority.

The observation consumer can retain a locked BBO as a measured state. The
submission refresh and all executable quote checks keep their own contract.
"""
from copy import deepcopy
import hashlib
import json
import math

from src.engine.scalping.ai_market_snapshot import route_partitioned_ws_view

SCHEMA = 'samsung_flat_buy_flow_observation_v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def samsung_scope(code, context):
    snapshot = context.get('ai_market_snapshot_v1') or {}
    return (str(code) == '005930' and snapshot.get('stock_code') == '005930'
            and str(snapshot.get('effective_venue') or '').upper() == 'KRX'
            and str(snapshot.get('session_bucket') or '').upper() == 'KRX_REGULAR')


def select_local_observation(base, latest, context, *, now, max_age_ms, preserve_keys=()):
    """Pure selection of one already received route; invalid sources raise.

    This function never calls WS/REST, changes clocks, or marks a quote executable.
    The caller still performs the canonical input preflight after this selection.
    """
    if not samsung_scope('005930', context):
        raise ValueError('machine_observation_scope_invalid')
    if number(now) is None or number(max_age_ms) is None or max_age_ms <= 0:
        raise ValueError('machine_observation_clock_contract_invalid')
    epoch = latest.get('market_data_transport_epoch')
    if type(epoch) is not int or epoch <= 0 or epoch != base.get('market_data_transport_epoch'):
        raise ValueError('machine_observation_transport_epoch_changed')
    view, partition = route_partitioned_ws_view(deepcopy(latest), context)
    if partition.get('used') is not True:
        raise ValueError('machine_observation_exact_route_missing')
    key = partition['selected_key']
    rows = latest['realtime_type_snapshots_by_route'][key]
    suffix, route = key.split('|', 1)
    item = '005930' + ('' if suffix == 'KRX' else suffix)
    for kind in ('0B', '0D'):
        row = rows[kind]
        at = number(row.get('observed_epoch'))
        if (row.get('item') != item or row.get('market_route') != route
                or type(row.get('transport_epoch')) is not int
                or row.get('transport_epoch') != epoch or at is None
                or not 0 <= (now - at) * 1000 <= max_age_ms):
            raise ValueError('machine_observation_route_or_source_clock_invalid')
    asks = (view.get('orderbook') or {}).get('asks') or []
    bids = (view.get('orderbook') or {}).get('bids') or []
    ask = number(asks[0].get('price')) if asks else None
    bid = number(bids[0].get('price')) if bids else None
    price = number(view.get('curr'))
    if price is None or price <= 0 or bid is None or ask is None or not 0 < bid <= ask:
        raise ValueError('machine_observation_price_or_crossed_bbo')
    # Compare the same route's clock. A newer concurrent subscription in the
    # aggregate view must not make a fresh selected route look regressive.
    base_view, base_partition = route_partitioned_ws_view(base, context)
    old_time = number((base_view if base_partition.get('used') else base).get('last_ws_update_ts'))
    if old_time is not None and (old_time > now or view['last_ws_update_ts'] < old_time):
        raise ValueError('machine_observation_snapshot_time_regression')
    # An exact window has no substitution from the aggregate or REST tape.
    ticks = list(view.get('recent_trade_ticks') or [])
    for tick in ticks[:10]:
        at = number(tick.get('received_at_ms'))
        if (tick.get('item') != item or tick.get('market_route') != route
                or type(tick.get('transport_epoch')) is not int
                or tick.get('transport_epoch') != epoch or at is None or at > now * 1000
                or type(tick.get('route_sequence')) is not int):
            raise ValueError('machine_observation_tick_scope_or_clock_invalid')
    if any(a['route_sequence'] != b['route_sequence']+1 or a['received_at_ms'] < b['received_at_ms']
           for a,b in zip(ticks[:10],ticks[1:10])):
        raise ValueError('machine_observation_tick_sequence_invalid')
    selected = {k: deepcopy(base[k]) for k in preserve_keys if k in base}
    selected.update(view)
    selected['entry_machine_exact_tick_source'] = key
    selected['entry_machine_observation_selection'] = 'latest_exact_route'
    return selected, dict(selected_key=key, source_item=item, transport_epoch=epoch,
        selected_at=now, source_observed_at={k:rows[k]['observed_epoch'] for k in ('0B','0D')},
        quote_state='locked' if bid == ask else 'nonlocked',
        executable_quote_verified=False)


def build_receipt(ws, packet, payload, *, cutoff):
    """Bind the actual feature window, not an assumed latest ten trades."""
    ticks = packet.get('_feature_tick_diagnostic_window') or []
    key = ws.get('entry_machine_exact_tick_source') or ws.get('zero_base_probe_exact_tick_source')
    epochs = {t.get('transport_epoch') for t in ticks}
    items = {t.get('item') for t in ticks}
    sequences = [t.get('route_sequence') for t in ticks]
    times = [number(t.get('received_at_ms')) for t in ticks]
    sequence_ok = (len(sequences) == 10 and all(type(v) is int for v in sequences)
                   and all(a == b + 1 for a,b in zip(sequences, sequences[1:])))
    scope_ok = (bool(key) and len(epochs) == 1 and len(items) == 1
                and next(iter(epochs), None) == ws.get('market_data_transport_epoch')
                and next(iter(items), None) == '005930' + ('' if key.split('|')[0] == 'KRX' else key.split('|')[0])
                and all(t.get('market_route') == key.split('|',1)[1] for t in ticks))
    clock_ok = (len(times) == 10 and all(t is not None and 0 <= cutoff * 1000 - t for t in times)
                and cutoff * 1000 - times[0] <= 5000
                and all(a >= b for a,b in zip(times,times[1:])))
    usable = bool(scope_ok and clock_ok and sequence_ok and packet.get('feature_tick_source') == 'ws_exact_route'
                  and packet.get('tick_aggressor_pressure_usable') is True
                  and packet.get('tick_aggressor_trusted_count') == 10)
    body = dict(schema=SCHEMA, stock_code=payload.get('stock_code'), effective_venue=payload.get('effective_venue'),
        session_bucket=payload.get('session_bucket'), cutoff=cutoff,
        payload_sha256=digest({k:v for k,v in payload.items() if k != 'entry_machine_observation_receipt'}),
        source_item=next(iter(items)) if len(items)==1 else None,
        source_route=key, transport_epoch=next(iter(epochs)) if len(epochs)==1 else None,
        snapshot_selection=ws.get('entry_machine_observation_selection','retained_or_existing_snapshot'),
        feature_source=packet.get('feature_tick_source'), window=ticks, window_sha256=digest(ticks),
        usable=usable, scope_ok=scope_ok, clock_ok=clock_ok, sequence_ok=sequence_ok,
        observed_values={k:packet.get(k) for k in ('buy_pressure_10t','net_aggressive_delta_10t',
            'price_change_10t_pct','curr_vs_micro_vwap_bp','micro_vwap_available')},
        quote=deepcopy(payload.get('quote') or {}), decision_authority='source_receipt_only',
        runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False)
    body['receipt_sha256'] = digest(body)
    return body
