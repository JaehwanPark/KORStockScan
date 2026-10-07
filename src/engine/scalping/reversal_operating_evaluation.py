"""Three-valued coverage and set contribution, separate from live authority."""
from collections import Counter
from fractions import Fraction
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping import reversal_path_auxiliary as OLD
from src.engine.scalping import reversal_operating_auxiliary as UNION


def validate_response(response, inp, *, arm, phase=None):
    if inp.get('schema') == UNION.VERSION:
        return UNION.validate_response(response,inp,arm=arm,phase=phase)
    return OLD.validate_response(response,inp,arm=arm,phase=phase)


def coverage(state, row, ids, hits, *, previous):
    """Conservative UNKNOWN masks. Absence of a signal alone is not FALSE."""
    result = {}
    features = state.features(row) if row[8] else {}
    for bid in ids:
        if not row[8] or not K.good_quote(row):
            result[bid]='UNKNOWN';continue
        if bid in hits:
            result[bid] = 'TRUE'; continue
        if not row[8] or previous is None or not K.connected(previous,row) or not state.legacy.last or not state.legacy.last[8]:
            result[bid] = 'UNKNOWN'; continue
        definition = C.definition(bid)
        required = set()
        for f in definition.get('filters',{}):
            suffix = next((s for s in ('_min_exclusive','_max_exclusive','_min','_max') if f.endswith(s)),None)
            required.add(f[:-len(suffix)] if suffix else f)
        # Drop/low values are conditional on a reversal root. A known absence
        # of that root is FALSE; unavailable rolling windows remain UNKNOWN.
        required -= {'drop','rebound','low_price'}
        if definition.get('kind')=='legacy_rule':
            rule=definition['rule']
            if 'VOL' in rule: required.add('volume')
            if rule.startswith('DD5'): required.add('dd')
        unknown = any(features.get(f) is None for f in required)
        phase = C.branch(bid)['decision_phase']
        if phase in {'MOMENTUM_CROSS','MOMENTUM_HOLD','HIGH_BREAKOUT'} and state.root_previous.get(bid) is None:
            unknown = True
        result[bid] = 'UNKNOWN' if unknown else 'FALSE'
    return result


def metric(counts):
    c = Counter(counts)
    resolved=c['WIN']+c['FAIL_STOP']+c['FAIL_TIMEOUT']
    return dict(wins=c['WIN'],resolved=resolved,unresolved=c['UNRESOLVED'],
                win_rate=c['WIN']/resolved if resolved else None,counts=dict(c))


def recommendation(old, new):
    if not old['resolved'] or not new['resolved']:
        return 'not_comparable'
    left,right=Fraction(old['wins'],old['resolved']),Fraction(new['wins'],new['resolved'])
    if right>left:
        return 'higher_cumulative_win_fraction'
    if right==left and new['resolved']>old['resolved'] and new['wins']>old['wins']:
        return 'equal_fraction_additional_resolved_success'
    return 'keep_current'


def summarize(points, operating, baseline):
    """Small fixture/reference reducer; streaming producer uses the same sets."""
    counters = {name:Counter() for name in ('union','baseline','common_union','common_baseline','excluded_baseline')}
    individual={bid:Counter() for bid in operating}
    exclusive={bid:Counter() for bid in operating}
    unproven={bid:Counter() for bid in operating}
    leave={bid:Counter() for bid in operating}
    seen={}
    for p in points:
        key=p['opportunity_key']; signature=(p['outcome'],p['truth'])
        if key in seen:
            if seen[key]!=signature:raise ValueError('operating_opportunity_conflict')
            continue
        seen[key]=signature
        accumulate(counters,individual,exclusive,unproven,leave,p['truth'],p['outcome'],operating,baseline)
    out={k:metric(v) for k,v in counters.items()}
    out.update(individual={k:metric(v) for k,v in individual.items()},exclusive={k:metric(v) for k,v in exclusive.items()},
               exclusive_unproven={k:metric(v) for k,v in unproven.items()},leave_one_out={k:metric(v) for k,v in leave.items()})
    out['recommendation']=recommendation(out['common_baseline'],out['common_union'])
    return out


def accumulate(counters,individual,exclusive,unproven,leave,truth,outcome,operating,baseline):
    hits={b for b in operating if truth.get(b)=='TRUE'}
    base={b for b in baseline if truth.get(b)=='TRUE'}
    known=all(truth.get(b) in {'TRUE','FALSE'} for b in set(operating)|set(baseline))
    if hits:counters['union'][outcome]+=1
    if base:counters['baseline'][outcome]+=1
    if known:
        if hits:counters['common_union'][outcome]+=1
        if base:counters['common_baseline'][outcome]+=1
    elif base:counters['excluded_baseline'][outcome]+=1
    for bid in operating:
        if bid in hits:
            individual[bid][outcome]+=1
            if hits=={bid}:
                (exclusive if known else unproven)[bid][outcome]+=1
        if known and hits-{bid}:leave[bid][outcome]+=1
