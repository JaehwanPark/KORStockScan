"""Offline canonical-archive reconstruction of the existing M1 exit classifier.

The original raw FID15 sign is the only recovered trade-side evidence. No
network, live state or policy publication. Collector identity is not Main PID
identity; default SCALP stops and event-time scheduling remain CF assumptions.
"""
from collections import Counter, defaultdict, deque
from datetime import datetime
import math
import re

from src.engine.scalping import entry_first_signal_exit_research as F
from src.engine.scalping.trailing_mechanical_strength import (
    HISTORY_LIMIT, classify_ws_history, normalize_config,
)
from src.engine.scalping.micro_reversion.contracts import registration_item_market_data_identity
from src.engine.trade_profit import calculate_net_profit_rate

AUTHORITY = {**F.AUTHORITY, 'decision_authority': 'offline_recovered_m1_price_path',
    'source_quality_gate': 'sealed_raw15_quantity_depth_item_epoch_sequence_clock',
    'full_operating_replay': False, 'actual_fill': False,
    'main_pid_consumption_verified': False}
MODES = ('weak', 'strong', 'mechanical')


def _number(value):
    return float(value) if type(value) in (int,float) and math.isfinite(value) else None


def recover_signed_trade(raw, quantity):
    """Official 0B/FID15: explicit +/- execution side, never cumulative FID13.

    Upstream 953e5dbff123f437ab4d11a78a95191a685eb51f reviewed 2026-10-05.
    The offline adapter is intentionally stricter than tolerant display parses.
    """
    missing = lambda why: dict(aggressor_side='UNKNOWN',aggressor_source=None,
        aggressor_quality=None,volume=quantity,recovery_status=why)
    if not isinstance(raw,str) or not re.fullmatch(r'[+-](?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)',raw.strip()):
        return missing('raw15_explicit_integer_sign_missing')
    value=int(raw.strip().replace(',',''));qty=_number(quantity)
    if value==0:
        return missing('raw15_zero_quantity')
    if qty is None or qty<=0 or not qty.is_integer() or qty!=abs(value):
        return missing('raw15_canonical_quantity_conflict')
    side='BUY' if value>0 else 'SELL'
    return dict(volume=abs(value),aggressor_side=side,
        aggressor_source='kiwoom_0b_signed_trade_volume',
        aggressor_quality='signed_trade_volume_positive' if value>0 else 'signed_trade_volume_negative',
        recovery_status='recovered_from_original_raw15')


def normalize_archive_point(payload, *, kind, source_valid):
    """Caller supplies the canonical validator/physical scope/exclusion result."""
    if kind not in {'trade','depth'}:
        raise ValueError('archive_kind_invalid')
    stamp=datetime.fromisoformat(payload['local_receive_timestamp'])
    if stamp.utcoffset() is None:
        raise ValueError('archive_clock_timezone_missing')
    point=dict(kind=kind,t=stamp.timestamp(),item=payload.get('source_item') if kind=='trade' else payload.get('item'),
        epoch=payload.get('sequence_epoch'),sequence=payload.get('series_sequence'),source_valid=source_valid is True,
        bid=payload.get('best_bid'),ask=payload.get('best_ask'),
        quote_age_ms=payload.get('quote_age_ms') if kind=='trade' else 0,
        trade_price=payload.get('trade_price') if kind=='trade' else None)
    if kind=='trade':
        point.update(recover_signed_trade(payload.get('trade_volume_raw'),payload.get('trade_qty')))
        point['trade_volume_raw']=payload.get('trade_volume_raw')
        point['recorded_aggressor_side']=payload.get('aggressor_side')
    else:
        for field in ('bid_levels','ask_levels'):
            levels=payload.get(field)
            point[field]=([dict(price=v[1],quantity=v[2]) for v in levels
                if isinstance(v,(list,tuple)) and len(v)==3] if isinstance(levels,list) else [])
    return point


def _snapshot(item,transport,buffers):
    _,route,_=registration_item_market_data_identity(item)
    suffix=item[-3:] if item.endswith(('_AL','_NX')) else 'KRX'
    key=suffix+'|'+route
    return dict(last_realtime_type_item={'0B':item,'0D':item},
        last_realtime_type_market_route={'0B':route,'0D':route},
        last_realtime_type_market_suffix={'0B':suffix,'0D':suffix},
        market_data_transport_epoch=transport,
        recent_depth_ticks_by_route={key:list(reversed(buffers['depth']))},
        recent_trade_ticks_by_route={key:list(reversed(buffers['trade']))})


def _history(point):
    row=dict(item=point['item'],transport_epoch=point['epoch'],route_sequence=point['sequence'],
        received_at_ms=round(point['t']*1000))
    if point['kind']=='depth':
        row.update(bid_levels=point.get('bid_levels'),ask_levels=point.get('ask_levels'))
    else:
        row.update(price=point['trade_price'],**{k:point.get(k) for k in
            ('volume','aggressor_side','aggressor_source','aggressor_quality')})
    return row


def replay_modes(row, points, *, policy, config):
    """One source clock, three frozen widths, position-local M1 initialization.

    UNKNOWN selects weak width as in the live Boolean adapter, but is retained
    as UNKNOWN evidence. Invalid archive continuity never fabricates a terminal.
    """
    F.validate_exit_policy(policy);normalize_config(config)
    if row.get('symbol')=='005930' or row.get('tags',{}).get('venue')!='KRX' or row.get('tags',{}).get('session')!='KRX_REGULAR':
        raise ValueError('non_samsung_regular_scope_required')
    start=F.epoch(row);entry=_number(row.get('reference_price'))
    cost=_number(row.get('features',{}).get('entry_cost_pct'))
    state_counts=Counter();reason_counts=Counter();transitions=Counter();journal=[]
    paths={};active={m:False for m in MODES};peak=entry;latest_trade=None
    last_quote=None;last={};buffers={k:deque(maxlen=HISTORY_LIMIT) for k in ('trade','depth')}
    state=None;previous_at=None;previous_effective=None
    def stats():
        return dict(state_counts=dict(state_counts),reason_counts=dict(reason_counts),
            transitions=dict(transitions),classifier_journal_count=len(journal))
    def missing(status, at=None):
        return dict(status=status,net_pct=None,exit_at=None,rule=None,blocked_at=at,
            completed_operating_exit=False,**stats())
    def finish():
        own=paths['mechanical']
        cutoff=own.get('exit_at') or own.get('blocked_at')
        own_journal=[j for j in journal if cutoff is None or j['evaluation_at_ms']<=round(cutoff*1000)]
        return dict(paths=paths,classifier={k:own[k] for k in
            ('state_counts','reason_counts','transitions','classifier_journal_count')},journal=own_journal)
    def stop(status, at=None):
        for mode in MODES:paths.setdefault(mode,missing(status,at))
        return finish()
    if cost is None or cost<0:return stop('cost_missing')
    if entry is None or entry<=0 or row.get('capture_valid') is not True or row.get('reference_type')!='executable_ask':
        return stop('entry_reference_missing')
    item=row['request_code']
    if row.get('quote_item') not in (None,item):return stop('entry_archive_item_conflict')
    end=min(start+3600,datetime.fromisoformat(row['ts']).replace(hour=15,minute=30,second=0,microsecond=0).timestamp())
    kinds_at=defaultdict(set)
    for p in points:
        if _number(p.get('t')) is not None:kinds_at[p['t']].add(p.get('kind'))
    for point in points:
        at=_number(point.get('t'));kind=point.get('kind');seq=point.get('sequence');transport=point.get('epoch')
        if at is None:return stop('archive_clock_invalid')
        if at>end:break
        if point.get('item')!=item:return stop('archive_item_mismatch',at)
        if kind not in buffers or type(seq) is not int or seq<=0 or type(transport) is not int or transport<=0:
            return stop('archive_sequence_invalid',at)
        if at<=start:
            last[kind]=point;buffers[kind].clear();buffers[kind].append(_history(point));continue
        if set(last)!={'trade','depth'}:return stop('archive_prefix_missing',at)
        if len(kinds_at[at])>1 or (previous_at is not None and at<previous_at):return stop('archive_clock_or_tie_ambiguous',at)
        previous_at=at
        if transport!=last[kind]['epoch']:return stop('archive_epoch_changed',at)
        if seq!=last[kind]['sequence']+1:return stop('archive_sequence_gap',at)
        if point.get('source_valid') is not True:return stop('archive_source_invalid',at)
        if last['trade']['epoch']!=last['depth']['epoch']:return stop('archive_prefix_epoch_conflict',at)
        if state is None:
            if any(p.get('source_valid') is not True for p in last.values()):
                return stop('archive_prefix_invalid',at)
            _,state=classify_ws_history(_snapshot(item,transport,buffers),None,
                now_ms=round(start*1000),max_quote_age_ms=700,market='REGULAR',config=config)
        last[kind]=point;buffers[kind].append(_history(point))
        if kind=='trade':
            price=_number(point.get('trade_price'))
            if price is None or price<=0:return stop('archive_trade_invalid',at)
            latest_trade=(at,price)
        decision,state=classify_ws_history(_snapshot(item,transport,buffers),state,
            now_ms=round(at*1000),max_quote_age_ms=700,market='REGULAR',config=config)
        bid,ask,age=(_number(point.get(k)) for k in ('bid','ask','quote_age_ms'))
        fresh=bid is not None and ask is not None and 0<bid<=ask and age is not None and 0<=age<=700
        touch=state.get('last_touch')
        quote_bound=bool(fresh and isinstance(touch,tuple) and len(touch)==4 and touch[1]>0 and touch[0]==bid)
        effective=decision.state if quote_bound else 'UNKNOWN'
        reason=decision.reason if quote_bound else 'quote_or_symbol_untrusted'
        if not quote_bound:state['strong']=False;state['adverse_count']=0
        state_counts[effective]+=1;reason_counts[reason]+=1
        if previous_effective is not None and previous_effective!=effective:
            transitions[previous_effective+'->'+effective]+=1
        previous_effective=effective
        for observation in decision.new_observations:
            journal.append(dict(**observation,effective_state=effective,effective_reason=reason,
                evaluation_at_ms=round(at*1000),item=item,collector_epoch=transport,
                main_epoch_binding_verified=False))
        if not fresh:continue
        last_quote=(at,bid)
        if latest_trade and 0<=at-latest_trade[0]<=.7:peak=max(peak,latest_trade[1])
        for mode in MODES:
            if mode in paths:continue
            strong=mode=='strong' or (mode=='mechanical' and effective=='STRONG')
            _,active[mode],rule=F._at_price(bid,peak,active[mode],entry,policy,strong,update_peak=False)
            if rule:
                paths[mode]=dict(status='conditional_archive_exit',net_pct=(bid/entry-1)*100-cost,
                    runtime_net_pct=calculate_net_profit_rate(entry,bid,cost_rate=policy['runtime_cost_rate']),
                    exit_at=at,exit_price=bid,rule=rule,peak_trade_price=peak,
                    classifier_state=effective,classifier_reason=reason,used_strong_width=strong,
                    classifier_recovered=mode=='mechanical',completed_operating_exit=False,**stats())
        if len(paths)==len(MODES):break
    if len(paths)<len(MODES):
        if not last_quote or end-last_quote[0]>.7:return stop('archive_endpoint_unobserved')
        for mode in MODES:
            paths.setdefault(mode,dict(**missing('archive_horizon_censored'),
                mark_to_close_cf_pct=(last_quote[1]/entry-1)*100-cost))
    return finish()
