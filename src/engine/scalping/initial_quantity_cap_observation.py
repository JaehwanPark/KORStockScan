"""Bounded Main quantity evidence on the existing observation executor.

Owns source-only capture, never orders, subscriptions, workers or custody.
Enqueue is explicitly separate from durable append confirmation.
"""
from collections import Counter
from threading import Lock
import re

_SINK=None
_LOCK=Lock()
_COUNTS=Counter()


def quote_route_binding(item, market_route, *, legacy=False):
    """Bind an existing local quote receipt without inferring fill venue.

    These are the local session/entry snapshot owner's route names, not API
    request or FID mappings. Legacy artifact rows retain their old names.
    """
    routes = {
        'krx_only': ('KRX', ''), 'nxt_only': ('NXT', '_NX'),
        'krx_nxt_integrated': ('SOR', '_AL'),
    }
    if legacy:
        routes.update(KRX=('KRX', ''), NXT=('NXT', '_NX'), SOR=('SOR', '_AL'))
    value = routes.get(market_route)
    if not value or not isinstance(item, str):
        return None
    route, suffix = value
    if not re.fullmatch(r'[0-9]{6}' + suffix, item):
        return None
    return dict(order_route=route, market_data_route=market_route, item=item,
                fill_venues=('KRX', 'NXT') if route == 'SOR' else (route,),
                underlying_event_venue_proven=route != 'SOR')


def configure_sink(sink):
    global _SINK
    _SINK=sink


def append(*, code, name, record_id, stage, fields, observed_at_epoch):
    from src.utils.pipeline_event_logger import emit_pipeline_event
    if _SINK is None:
        with _LOCK:_COUNTS['writer_not_prepared']+=1
        return False
    try:
        result=_SINK(emit_pipeline_event,'HOLDING_PIPELINE',str(name or code),str(code),stage,
                     record_id=record_id,fields=fields,observed_at_epoch=observed_at_epoch,
                     observation_category='initial_quantity')
        accepted=isinstance(result,dict) and result.get('status')=='queued'
    except Exception:
        accepted=False
    with _LOCK:_COUNTS['queued' if accepted else 'queue_rejected']+=1
    return accepted


def snapshot():
    with _LOCK:return dict(_COUNTS)
