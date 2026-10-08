"""Exact-route existing WS tape reuse for entry preparation only.

This is a local receive-sequence check, not a broker gap-free guarantee. A
partial window returns None and retains the existing bounded REST path.
"""
from copy import deepcopy
from datetime import datetime
import math
from zoneinfo import ZoneInfo


def select_trade_history(ws, request_code, *, now, limit=10):
    from src.utils.kiwoom_transport_telemetry import demand
    demand('ka10003', 'prepare_logical_demand')
    suffix = '_AL' if request_code.endswith('_AL') else '_NX' if request_code.endswith('_NX') else ''
    route = {'_AL':'krx_nxt_integrated','_NX':'nxt_only','':'krx_only'}[suffix]
    epoch = ws.get('market_data_transport_epoch')
    types = ws.get('last_realtime_type_item') or {}
    stamps = ws.get('last_realtime_type_ts') or {}
    tick_stamp = stamps.get('0B')
    if (type(epoch) is not int or epoch <= 0 or types.get('0B') != request_code
            or type(tick_stamp) not in (int,float) or not 0 <= now-tick_stamp <= 2
            or ws.get('source_conflict') or ws.get('price_conflict')):
        demand('ka10003', 'ws_unusable_fallback')
        return None
    rows = (ws.get('recent_trade_ticks_by_route') or {}).get((suffix or 'KRX')+'|'+route)
    if not isinstance(rows, (list,tuple)) or len(rows) < limit:
        demand('ka10003', 'ws_history_insufficient')
        return None
    selected = rows[:limit]
    previous = None
    day = datetime.fromtimestamp(now,ZoneInfo('Asia/Seoul')).date()
    try:
        for row in selected:
            received = float(row['received_at_ms'])/1000.
            provider = float(row['provider_trade_epoch'])
            sequence = row['route_sequence']
            if (row['item'] != request_code or row['transport_epoch'] != epoch
                    or row['market_suffix'] != suffix or row['market_route'] != route
                    or type(sequence) is not int or sequence < 1
                    or previous is not None and sequence != previous-1
                    or not math.isfinite(received) or not math.isfinite(provider)
                    or not 0 <= now-received <= 120 or not 0 <= received-provider <= 5
                    or datetime.fromtimestamp(received,ZoneInfo('Asia/Seoul')).date() != day
                    or type(row['price']) not in (int,float) or not math.isfinite(row['price']) or row['price'] <= 0
                    or type(row['volume']) is not int or row['volume'] <= 0
                    or row.get('volume_source') not in {'15_abs','13_delta'}):
                return None
            previous = sequence
        if not 0 <= now-float(selected[0]['received_at_ms'])/1000. <= 2:
            return None
    except (KeyError,TypeError,ValueError,OverflowError):
        return None
    demand('ka10003', 'ws_selected_http0')
    return [dict(deepcopy(row), request_code=request_code,
                 _entry_ws_source=dict(schema='entry_ws_tape_v1', item=request_code,
                    transport_epoch=epoch, original_received_at_ms=row['received_at_ms'],
                    route_sequence=row['route_sequence'], source='WS_0B',
                    completeness='local_receive_sequence_only')) for row in selected]
