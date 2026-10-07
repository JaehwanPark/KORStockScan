"""Frozen Main definitions and finite portfolios; no daily hypothesis generation."""
from __future__ import annotations

import copy
from itertools import combinations
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = 'main_registered_reversal_catalog_v1'
REGISTERED_AT = '2026-10-07T15:21:39+09:00'
FIXED = {'005930': 'samsung', '034020': '034020', '403870': '403870',
         '196170': '196170', '036930': '036930'}
BANDS = ('LT_20000', '20000_TO_100000', 'GE_100000')
# Runtime session resolver plus normalized source inventory. KRX premarket
# observations are audit context, not a supported continuous execution market.
ROUTES = {'PRE': ('SOR', 'NXT'), 'REGULAR': ('SOR', 'KRX', 'NXT'),
          'AFTER': ('SOR', 'KRX', 'NXT')}
LABEL = dict(target_net_pct=.4, stop_net_pct=-3., cost_rate=.0023, horizon_seconds=1800)


def group(symbol):
    return FIXED.get(symbol, 'other_non_fixed')


def band(price):
    return BANDS[0] if price < 20000 else BANDS[1] if price < 100000 else BANDS[2]


def cell_key(symbol, market, price):
    g = group(symbol)
    return '|'.join((g, K.market_bucket(market), 'ALL' if g == 'samsung' else band(price)))


def cells():
    return [f'{g}|{m}|{b}' for g in (*FIXED.values(), 'other_non_fixed')
            for m in ROUTES for b in (('ALL',) if g == 'samsung' else BANDS)]


def _pattern(name, g, phase=B.FIRST, price_band='ALL', **filters):
    return dict(branch_id=name, kind='registered_pattern', definition_version=1,
                symbol_group=g, market='REGULAR', route='SOR', price_band=price_band,
                item_rule='symbol_AL', decision_phase=phase,
                confirmation_seconds=5 if phase == B.CONFIRMED else 0,
                filters=filters, label_contract=LABEL)


_DEFINITIONS = {b['branch_id']: b for b in (B.legacy_branch(r) for r in K.RULES)}
_DEFINITIONS[B.BRANCH] = dict(B.DEFINITION)
_DEFINITIONS.update({d['branch_id']: d for d in (
    _pattern('S1', 'samsung', B.CONFIRMED, drop_max=.4, dd_min=.4, dd_max=.8,
             ret_min=.2, session_min=.4, low_rising=True, buy10_min=60),
    _pattern('S2', 'samsung', B.CONFIRMED, drop_max=.4, dd_min=.4, dd_max=.8,
             ret_min=0, session_min=.4, low_rising=True, vwap_min=.1),
    _pattern('D1', '034020', drop_max=.4, dd_min=1.2, ret_min=0),
    _pattern('H1', '403870', drop_max=.4, dd_min=.4, dd_max=.8, ret_min=0,
             session_min=.4, low_rising=True),
    _pattern('A1', '196170', drop_max=.4, dd_min=1.2, ret_min=0, ret_max=.2),
    _pattern('J1', '036930', drop_max=.4, dd_max_exclusive=.4, ret_min=0,
             ret_max=.2, session_min=.4, low_rising=True),
    _pattern('G1', 'other_non_fixed', price_band=BANDS[1], session_trend='UP',
             ret_max_exclusive=0, structure='RISING', dd_min=.4, dd_max=.8),
    _pattern('G2', 'other_non_fixed', price_band=BANDS[2], session_trend='DOWN',
             ret_min=.2, structure='MIXED', dd_min_exclusive=.8, dd_max_exclusive=1.2),
    _pattern('G3', 'other_non_fixed', price_band=BANDS[1], session_trend='NEUTRAL',
             ret_min=.2, structure='RISING', dd_min_exclusive=.8,
             dd_max_exclusive=1.2, volume_min=1),
    _pattern('G4', 'other_non_fixed', price_band=BANDS[0], session_trend='UP',
             ret_min=.2, structure='FALLING', dd_min=.2, dd_max_exclusive=.4,
             spread_max=.1),
)})


def definition(branch_id):
    return copy.deepcopy(_DEFINITIONS[branch_id])


def branch(branch_id):
    if branch_id == B.BRANCH:
        return B.pattern_branch()
    d = definition(branch_id)
    if d['kind'] == 'legacy_rule':
        return d
    return dict(branch_id=branch_id, kind='registered_pattern',
                definition_sha256=digest(d), decision_phase=d['decision_phase'])


def applicable(branch_id, key, route):
    g, market, b = key.split('|')
    if route not in ROUTES[market]:
        return False
    d = _DEFINITIONS[branch_id]
    if d['kind'] == 'legacy_rule':
        return True
    if branch_id == B.BRANCH:
        return key == 'samsung|REGULAR|ALL' and route == 'SOR'
    return (g == d['symbol_group'] and market == d['market'] and route == d['route']
            and d['price_band'] in ('ALL', b))


def validate_payload(payload, key, route):
    if (set(payload) != {'composition', 'branches'} or
            payload['composition'] != 'ANY_MATCH_ONE_INTENT' or not payload['branches']):
        raise ValueError('v3_portfolio_invalid')
    ids = [b.get('branch_id') for b in payload['branches']]
    if len(set(ids)) != len(ids):
        raise ValueError('v3_duplicate_branch')
    for b in payload['branches']:
        if b['branch_id'] not in _DEFINITIONS or b != branch(b['branch_id']) or not applicable(b['branch_id'], key, route):
            raise ValueError('v3_definition_or_scope_invalid')


def _portfolios(key, route):
    legacy = [B.legacy_branch(r)['branch_id'] for r in K.RULES]
    special = [i for i in _DEFINITIONS if i not in legacy and applicable(i, key, route)]
    lists = [[i] for i in legacy]
    if not special:
        lists += [list(c) for c in combinations(legacy, 2)]
    else:
        # Enumerated once at registration, never inside a daily selector.
        subsets = [list(c) for n in range(1, len(special)+1) for c in combinations(special, n)]
        lists += subsets + [[i]+s for i in legacy for s in subsets]
    return [dict(portfolio_id=digest(ids), branch_ids=ids) for ids in lists]


PORTFOLIOS = {k: {r: _portfolios(k, r) for r in ROUTES[k.split('|')[1]]} for k in cells()}
MANIFEST = dict(schema=VERSION, registered_at=REGISTERED_AT, definitions=_DEFINITIONS,
                support_routes={m:list(routes) for m,routes in ROUTES.items()}, portfolios=PORTFOLIOS,
                fixed_symbols=FIXED, origin='manual_research_and_existing_runtime_policy')
MANIFEST['entries']={bid:dict(definition_version=1,definition_sha256=digest(d),registered_at=REGISTERED_AT,
    origin='existing_runtime_policy' if bid.startswith('legacy_') or bid==B.BRANCH else 'manual_research',status='registered',
    research_result_sha256='1aab06151e576a571e5edf3d4186e3b6d21d1b074ff2045dee59ba4e9d6a8695',
    supplement_result_sha256='b57d0a911318bca38224a00942cccd4c701ff8dd0dbd8add7de4ce6ab45f5632',
    research_code_sha256='b7c47cc872c3cff6fe80292f2906011e6bd8a929453003b242fd7147d1b2e6d1',
    source_prefix_sha256='99a2fd7a4e48e4ce9edbb3a899f39dc65f9d412fe55a140edb4ff8a5faa35b36') for bid,d in _DEFINITIONS.items()}
SHA256 = digest(MANIFEST)


def matches(branch_id, event, f):
    """None means required feature absent; False is a resolved condition miss."""
    if not applicable(branch_id, cell_key(event['symbol'], event['market'], event['confirmation_price']), event['venue']):
        return False
    d = _DEFINITIONS[branch_id]
    if d['kind'] != 'legacy_rule' and event.get('source_item') != event['symbol']+'_AL':
        return False
    if d['kind'] == 'legacy_rule':
        rule = d['rule']
        if ('VOL' in rule and event.get('volume_ratio_60s') is None) or (rule.startswith('DD5') and event.get('drawdown_5m_pct') is None):
            return None
        return K.conditions(event)[rule]
    if branch_id == B.BRANCH:
        filters = dict(drop_max=.4, dd_min=.4, dd_max=.8, ret_min=.2, session_min=.4, low_rising=True)
    else:
        filters = d['filters']
    values = dict(drop=event.get('drop_pct'), dd=event.get('drawdown_5m_pct'),
                  volume=event.get('volume_ratio_60s'), spread=event.get('spread_pct'), **f)
    results = []
    for name, bound in filters.items():
        op = next((s for s in ('_min_exclusive', '_max_exclusive', '_min', '_max') if name.endswith(s)), None)
        v = values.get(name[:-len(op)] if op else name)
        if v is None:
            results.append(None)
        elif op:
            results.append(v > bound if op == '_min_exclusive' else v < bound if op == '_max_exclusive' else v >= bound if op == '_min' else v <= bound)
        else:
            results.append(v == bound)
    return False if False in results else None if None in results else True
