"""Causal registered roots on the existing rolling state, without I/O or AI."""
from __future__ import annotations

import copy
from collections import Counter
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_cumulative_catalog as C
from src.engine.scalping.continuous_reversal_postclose import digest


class Detector:
    def __init__(self,ids):
        self.ids=tuple(ids)
        self.roots={C.ROOTS[b]['root_confirmation'] for b in ids if b in C.ROOTS}
        self.previous={};self.pending={};self.last_turn=None;self.counts=Counter()
        self.coverage={}

    def reset(self):
        self.counts['source_censored']+=len(self.pending)
        self.previous.clear();self.pending.clear();self.last_turn=None
        self.coverage={}

    def observe(self,state,row,f,prior60,*,symbol,venue,session):
        """Consume each first confirmation even when its optional filter fails."""
        t=row[0];ready=[];self.coverage={b:'FALSE' for b in self.ids if b in C.ROOTS}
        for identity,p in tuple(self.pending.items()):
            root=p['root_confirmation']
            if root.startswith('RETEST'):
                if t>p['epoch']+30 or row[3]<p['low']*.998:
                    del self.pending[identity];continue
                p['minimum_price']=min(p['minimum_price'],row[3])
                if p.get('touch_sequence') is None and row[3]<=p['low']:
                    p.update(touch_sequence=row[2],touch_epoch=t,touch_price=row[3])
                if p.get('touch_sequence') is None or row[2]<=p['touch_sequence'] or row[3]<p['price']:
                    continue
            else:
                if row[3]<p['price']:
                    del self.pending[identity];continue
                p['minimum_price']=min(p['minimum_price'],row[3])
                seconds=int(root.rsplit('HOLD',1)[1])
                if t<p['epoch']+seconds:continue
            del self.pending[identity];ready.append(copy.deepcopy(p))
        turn=state.legacy.turn
        fresh=turn and turn['event_id']!=self.last_turn
        if fresh:self.last_turn=turn['event_id']
        for root in sorted(self.roots):
            yes=None;extra={}
            if root.startswith(('FIRST','RETEST')):
                if not fresh:continue
                yes=True;extra=dict(low=turn['low_price'],anchor_event_id=turn['event_id'])
            elif root.startswith('BREAKOUT'):
                yes=row[3]>prior60 if prior60 is not None and t-state.legacy.segment_start>=60 else None
                extra=dict(prior_high=prior60)
            elif root.startswith('MOMENTUM'):
                threshold=float(root.split('_')[1])
                yes=f['ret']>=threshold if f['ret'] is not None else None
                extra=dict(threshold=threshold,return_60s_pct=f['ret'])
            elif root.startswith('VWAP'):
                yes=f['vwap']>=0 if f['vwap'] is not None else None
                extra=dict(vwap_at_root=f['vwap'])
            elif root.startswith('RISING'):
                yes=f['structure']=='RISING' if f['structure'] is not None else None
                extra=dict(structure_at_root=f['structure'])
            before=self.previous.get(root)
            self.previous[root]=yes
            if yes is None:
                for bid in self.ids:
                    if bid in C.ROOTS and C.ROOTS[bid]['root_confirmation']==root:self.coverage[bid]='UNKNOWN'
            if root.startswith(('FIRST','RETEST')):
                crossed=yes
            else:
                crossed=yes is True and before is False
            if not crossed:continue
            p=dict(root_confirmation=root,root_contract=C.root_contract(root),feature_version=C.FEATURE_VERSION,epoch=t,price=row[3],
                native_epoch=row[1],native_sequence=row[2],previous_condition=before,
                minimum_price=row[3],**extra)
            if '_HOLD' in root or root.startswith('RETEST'):
                size=len(self.pending)+len(state.pending)+len(state.path_pending)+len(state.extended_pending)
                if not state.offline and size>=B.MAX_PENDING:
                    self.counts['pending_overload']+=1;continue
                self.pending[root+':'+str(row[2])]=p
            else:ready.append(p)
        emitted={}
        for p in ready:
            for bid in self.ids:
                if bid not in C.ROOTS:continue
                d=C.ROOTS[bid]
                if d['root_confirmation']!=p['root_confirmation']:continue
                from src.engine.scalping import reversal_extended_catalog as E
                if not E.applicable(bid,E.cell_key(symbol,K.market_bucket(session),row[3]),venue):continue
                matched=C.condition(f,d['filters'])
                self.coverage[bid]='UNKNOWN' if matched is None else 'FALSE'
                self.counts['filter_unknown' if matched is None else 'filter_false' if not matched else 'matched']+=1
                if matched is not True or not K.good_quote(row):continue
                eid=f'{K.iso(t)[:10]}:{venue}:{session}:{symbol}:{row[1]}:{row[2]}'
                event=dict(event_id=eid,signal_id=eid,symbol=symbol,venue=venue,session=session,
                    market=K.market_bucket(session),source_item=row[9],epoch=t,at=K.iso(t),
                    confirmation_price=row[3],entry_ask=row[5],spread_pct=f['spread'],
                    drawdown_5m_pct=f['dd'],volume_ratio_60s=f['volume'],branch_features=copy.deepcopy(f),
                    native_epoch=row[1],native_sequence=row[2],registry_generation=state.generation,
                    extended_definition_id=bid,branch_definition_sha256=digest(d),
                    decision_phase=C.PHASES[bid],signal_kind=C.PHASES[bid],signal_proof=copy.deepcopy(p))
                emitted[bid]=event
                self.coverage[bid]='TRUE'
        return emitted


def prefix_features(state,row,features):
    """Same windows as the manual study; no changes to old feature dictionaries."""
    f={k:features.get(k) for k in ('ret','session','vwap','buy10','volume','dd','structure')}
    f['spread']=100*(row[5]-row[4])/row[3] if K.good_quote(row) else None
    # All required fields stay optional here; an A requires TRUE, an F preserves UNKNOWN.
    return f


def hold_floor(event):
    bid=event.get('extended_definition_id')
    if bid in C.REFINEMENTS:
        return hold_floor(event['signal_proof']['original_confirmation'])
    if event.get('decision_phase') in {'FIRST_PRICE_HOLD','MOMENTUM_HOLD','HIGH_BREAKOUT_HOLD',
                                      'VWAP_RECLAIM_HOLD','RISING_STRUCTURE_HOLD'}:
        return (event.get('signal_proof') or {}).get('price')
    return None
