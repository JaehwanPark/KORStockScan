"""Independent operating detectors, sealed opportunities and per-scope claims.

Normalized observation is CPU/memory only. Disk/provider custody belongs to the
consumer outbox, never this callback. Native v4 scopes remain native v4.
"""
from __future__ import annotations
import copy
import math
import threading
from datetime import datetime
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping import reversal_path_runtime as R
from src.engine.scalping import reversal_operating_auxiliary as A
from src.engine.scalping.continuous_reversal_postclose import digest

_LOCK = threading.RLock()
_STATES = {}; _CLAIMS = {}; _FAMILY = None; _GENERATION = None


def _latest_features(rows, segment_start):
    """Exact final element of the native prefix projector, without old outputs.

    Use the same cumulative arrays and subtraction order as build_features;
    replacing them with rolling sums changes floating-point request bytes.
    """
    np=K.np
    times=np.array([r[0] for r in rows]);starts,_,valid=K.segments(rows)
    prices=np.array([r[3] if r[3] is not None else np.nan for r in rows])
    qty=np.array([r[6] if r[6] is not None and r[6]>0 and r[8] else 0 for r in rows])
    sides=np.array([r[7] for r in rows])
    cumulative=lambda x:np.concatenate(([0.],np.cumsum(x)))
    q=cumulative(qty);buy=cumulative(np.where(sides==1,qty,0))
    bad_qty=cumulative(qty<=0);bad_side=cumulative((qty<=0)|(sides==0))
    pv=cumulative(np.where(qty>0,qty*np.nan_to_num(prices),0))
    out={k:None for k in K.FEATURES[:4]};i=len(rows)-1
    if not valid[i]:return out
    a=i-9
    if a>=starts[i]:
        if bad_side[i+1]==bad_side[a] and q[i+1]>q[a]:out['buy_pressure_10t']=float(100*(buy[i+1]-buy[a])/(q[i+1]-q[a]))
        out['return_10t_pct']=float(100*(prices[i]/prices[a]-1))
    epoch=segment_start if starts[i]==0 and segment_start is not None else times[starts[i]]
    a=int(np.searchsorted(times,times[i]-30))
    if times[i]-epoch>=30 and a>=starts[i] and bad_side[i+1]==bad_side[a] and q[i+1]>q[a]:
        out['buy_pressure_30s']=float(100*(buy[i+1]-buy[a])/(q[i+1]-q[a]))
    a=int(np.searchsorted(times,times[i]-60))
    if times[i]-epoch>=60 and a>=starts[i] and bad_qty[i+1]==bad_qty[a] and q[i+1]>q[a]:
        average=(pv[i+1]-pv[a])/(q[i+1]-q[a])
        out['vs_vwap_60s_pct']=float(100*(prices[i]/average-1))
    return {k:v if v is not None and math.isfinite(v) else None for k,v in out.items()}


def snapshot(state,ready):
    """Byte-equivalent native snapshot with one common prefix projection.

    Native carried scopes keep their original reader. New operating scopes
    share final features across the already confirmed, same-tick signals.
    """
    event=copy.deepcopy(ready['event']);inputs=copy.deepcopy(ready.get('path_inputs',{}))
    missing=[bid for bid in event['branch_signals'] if bid not in inputs]
    if missing:
        rows=sorted([r[:] for r in state.legacy.rows if r[1]==event['native_epoch']
            and r[2]<=event['native_sequence'] and r[0]<=event['epoch']],key=lambda r:(r[0],r[1],r[2]))
        if not rows or rows[-1][0]!=event['epoch']:raise ValueError('operating_snapshot_prefix_missing')
        features=None;volume=None;t=event['epoch']
        if t-state.legacy.segment_start>=120:
            window=[r for r in rows if r[0]>=t-120]
            if all(r[6] is not None and r[6]>0 for r in window):
                previous=sum(r[6] for r in window if r[0]<t-60)
                if previous>0:volume=sum(r[6] for r in window if r[0]>=t-60)/previous
        for bid in missing:
            signal=event['branch_signals'][bid];signal.pop('_recent_rows',None)
            if (signal['epoch']!=t or signal['event_id'].rsplit(':',1)[1]!=str(event['native_sequence'])):
                raise ValueError('operating_snapshot_signal_tick_conflict')
            if signal['entry_ask'] is None:inputs[bid]=None;continue
            if volume is not None:signal['volume_ratio_60s']=volume
            if features is None:features=_latest_features(rows,state.legacy.segment_start)
            values=dict(features,**{k:signal[k] for k in K.INPUT_FEATURES[4:]})
            signal['entry_index']=len(rows)-1
            inputs[bid]=K.make_input(signal,rows,values)
    return event,dict(branch_inputs=inputs)


def configure(family, data_root, day):
    global _FAMILY, _GENERATION
    from src.engine.scalping.continuous_reversal_policy_v5 import validate_family
    validate_family(family)
    R.configure(family['native_parent_bundle']['continuous_reversal'])
    R.restore_session_anchors(data_root, day)
    with _LOCK:
        for key, state in list(_STATES.items()):
            cell = family['machine_cells'][key[-1]]['routes'][key[1]]
            if cell['backend'] != 'union_v5' or state.generation != cell['scope_execution_hash']:
                _STATES.pop(key)
        _FAMILY = copy.deepcopy(family); _GENERATION = family['family_sha256']
        for token, claim in list(_CLAIMS.items()):
            if claim['scope'] not in _STATES:
                _CLAIMS.pop(token)


def observe_normalized(symbol, session, envelope):
    if _FAMILY is None:
        return
    # Keep native carried paths warm, but only the scope selector can claim them.
    observe_native(symbol, session, envelope)
    venue = 'SOR' if envelope.get('market_route') == 'krx_nxt_integrated' else envelope.get('effective_venue')
    market = K.market_bucket(session)
    if venue not in C.ROUTES.get(market, ()):
        return
    from src.engine.scalping.micro_reversion.forward_collector import _explicit_item_venue
    item = envelope.get('item')
    if not isinstance(item,str) or item.split('_',1)[0] != symbol or _explicit_item_venue(item) != venue:
        return
    try:
        t,price = float(envelope['observed_epoch']),float(envelope['trade_price'])
        ex = envelope.get('provider_trade_epoch')
        row = [t,envelope['transport_epoch'],envelope['route_sequence'],price,
            envelope.get('inline_best_bid'),envelope.get('inline_best_ask'),envelope.get('trade_qty'),
            {'BUY':1,'SELL':-1}.get(envelope.get('aggressor_side'),0),
            int(math.isfinite(t) and math.isfinite(price) and price>0 and type(ex) in (int,float) and 0<=t-ex<=5),item,0]
        stream = symbol,venue,item,market,str(datetime.fromtimestamp(t,K.KST).date())
        with _LOCK:
            for band in (('ALL',) if C.group(symbol)=='samsung' else C.BANDS):
                cell_key = f'{C.group(symbol)}|{market}|{band}'
                cell = _FAMILY['machine_cells'][cell_key]['routes'][venue]
                if cell['backend'] != 'union_v5':
                    continue
                key = stream + (cell_key,)
                state = _STATES.get(key)
                if state is None:
                    state = _STATES[key] = R.State(branch_ids=[b['branch_id'] for b in cell['payload']['branches']],
                        session_anchor=R._ANCHORS.get(stream), generation=cell['scope_execution_hash'])
                state.observe(row,symbol=symbol,venue=venue,session=session)
            for key in list(_STATES):
                if key[:3] == stream[:3] and key[3:5] != stream[3:5]:
                    _STATES.pop(key)
    except (ValueError,KeyError,TypeError,OverflowError):
        return


def observe_native(symbol, session, envelope):
    """Compatibility fix: Samsung has one ALL cell, never three price bands.

    The frozen v4 callback iterates non-Samsung bands and silently catches that
    missing key. The successor dispatcher fixes only this address calculation;
    native definitions, state, primary and claims are untouched.
    """
    if symbol!='005930' or R._FAMILY is None:
        return R.observe_normalized(symbol,session,envelope)
    venue='SOR' if envelope.get('market_route')=='krx_nxt_integrated' else envelope.get('effective_venue')
    market=K.market_bucket(session)
    from src.engine.scalping.micro_reversion.forward_collector import _explicit_item_venue
    item=envelope.get('item')
    if venue not in C.ROUTES.get(market,()) or not isinstance(item,str) or item.split('_',1)[0]!=symbol or _explicit_item_venue(item)!=venue:return
    try:
        t,price=float(envelope['observed_epoch']),float(envelope['trade_price']);ex=envelope.get('provider_trade_epoch')
        row=[t,envelope['transport_epoch'],envelope['route_sequence'],price,envelope.get('inline_best_bid'),
            envelope.get('inline_best_ask'),envelope.get('trade_qty'),{'BUY':1,'SELL':-1}.get(envelope.get('aggressor_side'),0),
            int(math.isfinite(t) and math.isfinite(price) and price>0 and type(ex) in (int,float) and 0<=t-ex<=5),item,0]
        key=symbol,venue,item,market,str(datetime.fromtimestamp(t,K.KST).date())
        with R._LOCK:
            if key[4] in R._EMPTY_PREFIX_DAYS and row[8] and key not in R._ANCHORS:R._ANCHORS[key]=row[:4]
            ids=[b['branch_id'] for b in R._FAMILY['machine_cells'][C.cell_key(symbol,market,price)]['routes'][venue]['payload']['branches']]
            state=R._STATES.get(key)
            if state is None:state=R._STATES[key]=R.State(branch_ids=ids,session_anchor=R._ANCHORS.get(key),generation=R._GENERATION)
            else:state.selected_ids=tuple(ids)
            for old in list(R._STATES):
                if old[:3]==key[:3] and old!=key:R._STATES.pop(old)
            state.observe(row,symbol=symbol,venue=venue,session=session)
    except (ValueError,KeyError,TypeError,OverflowError):return


def claim_snapshot(symbol, venue, session, *, now, item, family_sha256):
    stream = symbol,venue,item,K.market_bucket(session),str(datetime.fromtimestamp(now,K.KST).date())
    with _LOCK:
        if not _FAMILY or family_sha256 != _FAMILY['family_sha256']:
            return None
        for token, original in list(_CLAIMS.items()):
            if now-original['snapshot'][0]['epoch']>5:
                _CLAIMS.pop(token)
        ready_list = []
        for band in (('ALL',) if C.group(symbol)=='samsung' else C.BANDS):
            key = stream+(f'{C.group(symbol)}|{stream[3]}|{band}',)
            state = _STATES.get(key)
            if not state:
                continue
            for ready in state.ready:
                e = ready['event']
                if (not ready['claimed'] and 0<=now-e['epoch']<=5
                        and C.cell_key(symbol,session,e['confirmation_price']) == key[-1]):
                    ready_list.append((e['epoch'],e['native_sequence'],key,state,ready))
        for _,_,key,state,ready in sorted(ready_list,key=lambda x:x[:2]):
            ready['claimed'] = True
            event,source = snapshot(state,ready)
            confirmed = sorted(event['branch_signals'])
            _filter_first(event,source,state)
            if not event['branch_signals']:
                continue
            event['confirmed_set'] = confirmed
            event['opportunity_key'] = A.opportunity(event)
            snap = event,source
            token = digest([state.generation,event['signal_id'],snap])
            original = dict(snapshot=copy.deepcopy(snap),generation=state.generation,scope=key,
                            envelope_sha256=family_sha256)
            _CLAIMS[token] = original
            return dict(token=token,snapshot=snap,generation=state.generation,backend='operating_v5',
                        scope_execution_hash=state.generation)
        # The native primary/phase contract stays intact for carried scopes.
        claim = R.claim_snapshot(symbol,venue,session,now=now,item=item,
                                family_sha256=_FAMILY['native_parent_bundle']['continuous_reversal']['family_sha256'])
        if claim:
            e = claim['snapshot'][0]
            cell = _FAMILY['machine_cells'][C.cell_key(symbol,session,e['confirmation_price'])]['routes'][venue]
            if cell['backend'] == 'registered_v4':
                claim['operating_envelope_sha256'] = family_sha256
                return claim
    return None


def _filter_first(event, source, state):
    for bid, signal in list(event['branch_signals'].items()):
        if signal['decision_phase'] == B.FIRST and (not state.legacy.turn or state.legacy.turn['event_id'] != signal['event_id']):
            event['branch_signals'].pop(bid)
            source['branch_inputs'].pop(bid)


def validate_claim(claim, family_sha256, *, now):
    if not isinstance(claim,dict):
        raise ValueError('reversal_signal_claim_missing')
    if claim.get('backend') == 'registered_v4':
        with _LOCK:
            event = claim['snapshot'][0]
            cell = _FAMILY['machine_cells'][C.cell_key(event['symbol'],event['market'],event['confirmation_price'])]['routes'][event['venue']]
            if cell['backend'] != 'registered_v4':
                raise ValueError('reversal_signal_generation_changed')
        return R.validate_claim(claim,_FAMILY['native_parent_bundle']['continuous_reversal']['family_sha256'],now=now)
    with _LOCK:
        original = _CLAIMS.get(claim.get('token'))
        if not original or digest(original['snapshot']) != digest(claim.get('snapshot')):
            raise ValueError('reversal_signal_expired_or_changed')
        state = _STATES.get(original['scope'])
        if not state or state.generation != original['generation'] or claim.get('generation') != state.generation:
            raise ValueError('reversal_signal_generation_changed')
        event,source = copy.deepcopy(original['snapshot'])
        if not 0<=now-event['epoch']<=5:
            raise ValueError('reversal_signal_expired_or_changed')
        if (not state.legacy.last or not state.legacy.last[8] or not K.good_quote(state.legacy.last) or state.legacy.last[1] != event['native_epoch']
                or not any(r['event']['signal_id']==event['signal_id'] for r in state.ready)):
            raise ValueError('reversal_signal_path_changed')
        _filter_first(event,source,state)
        if not event['branch_signals']:
            raise ValueError('reversal_all_signals_invalidated')
        return event,source


def acknowledge(claim, *, status):
    if (claim or {}).get('backend') == 'registered_v4':
        return R.acknowledge(claim,status=status)
    with _LOCK:
        original = _CLAIMS.get((claim or {}).get('token'))
        if original:
            original['status'] = status
