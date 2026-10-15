"""Versioned PRE NXT / AFTER SOR definitions; immutable v4/v5 catalog remains intact."""
from __future__ import annotations
import copy
from src.engine.scalping import reversal_path_catalog as OLD
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = 'main_extended_session_catalog_v1'
BANDS, ROUTES, FIXED, LABEL = OLD.BANDS, OLD.ROUTES, OLD.FIXED, OLD.LABEL
cells, cell_key, group, band = OLD.cells, OLD.cell_key, OLD.group, OLD.band

RESEARCH_BATCH_SHA256 = '2c265e0cd522df4add5a24f94930fde0e82091e8a8f3cb071edd77a5a58036f5'
NEW_DEFINITIONS = {'manual_extended_27bebc59a6315682': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'ret_min': 0.2},
                                      'item_rule': 'symbol_AL',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'AFTER',
                                      'price_band': 'GE_100000',
                                      'root_confirmation': 'FIRST',
                                      'root_contract': {'confirmation': 'immediate',
                                                        'signal': 'native_first_turn'},
                                      'route': 'SOR',
                                      'symbol_group': '036930'},
 'manual_extended_2bc1d38c190297c6': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': '20000_TO_100000',
                                      'root_confirmation': 'PEAK_WAIT120_TOL0.2',
                                      'root_contract': {'allowed_below_original_low_pct': 0.2,
                                                        'breach_operator': 'strict_less',
                                                        'confirmation': 'PEAK',
                                                        'maximum_wait_seconds': 120,
                                                        'signal': 'native_first_turn',
                                                        'touch_operator': 'less_or_equal'},
                                      'route': 'NXT',
                                      'symbol_group': '034020'},
 'manual_extended_32242b888bb0a643': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'ret_max_exclusive': 0.2,
                                                  'ret_min': 0,
                                                  'session_max': -0.4,
                                                  'structure': 'MIXED'},
                                      'item_rule': 'symbol_AL',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'AFTER',
                                      'price_band': 'LT_20000',
                                      'root_confirmation': 'RETEST_FIRST_WAIT30_TOL0',
                                      'root_contract': {'allowed_below_original_low_pct': 0.0,
                                                        'breach_operator': 'strict_less',
                                                        'confirmation': 'RETEST_FIRST',
                                                        'maximum_wait_seconds': 30,
                                                        'signal': 'native_first_turn',
                                                        'touch_operator': 'less_or_equal'},
                                      'route': 'SOR',
                                      'symbol_group': 'other_non_fixed'},
 'manual_extended_4ea15de46e830760': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'buy10_min': 60,
                                                  'dd_max_exclusive': 0.4,
                                                  'dd_min': 0.2,
                                                  'session_max': -0.4},
                                      'item_rule': 'symbol_AL',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'AFTER',
                                      'price_band': '20000_TO_100000',
                                      'root_confirmation': 'FIRST',
                                      'root_contract': {'confirmation': 'immediate',
                                                        'signal': 'native_first_turn'},
                                      'route': 'SOR',
                                      'symbol_group': '403870'},
 'manual_extended_5c7e6db237e63de0': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'ret_max_exclusive': 0.2,
                                                  'ret_min': 0,
                                                  'session_max_exclusive': 0.4,
                                                  'session_min_exclusive': -0.4,
                                                  'structure': 'MIXED'},
                                      'item_rule': 'symbol_AL',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'AFTER',
                                      'price_band': 'GE_100000',
                                      'root_confirmation': 'RETEST_FIRST_WAIT30_TOL0.2',
                                      'root_contract': {'allowed_below_original_low_pct': 0.2,
                                                        'breach_operator': 'strict_less',
                                                        'confirmation': 'RETEST_FIRST',
                                                        'maximum_wait_seconds': 30,
                                                        'signal': 'native_first_turn',
                                                        'touch_operator': 'less_or_equal'},
                                      'route': 'SOR',
                                      'symbol_group': 'other_non_fixed'},
 'manual_extended_71b4600cddee3a22': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'dd_max_exclusive': 0.2,
                                                  'session_max': -0.4,
                                                  'vwap_min': 0},
                                      'item_rule': 'symbol_AL',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'AFTER',
                                      'price_band': 'ALL',
                                      'root_confirmation': 'MOMENTUM_0.05',
                                      'root_contract': {'condition_trigger': 'known_false_to_known_true',
                                                        'hold_seconds': 0,
                                                        'return_60s_min_pct': 0.05,
                                                        'signal': 'MOMENTUM',
                                                        'signal_buy10_min': None,
                                                        'structure_window_seconds': None,
                                                        'warmup_seconds': 60},
                                      'route': 'SOR',
                                      'symbol_group': 'samsung'},
 'manual_extended_95033e152c7e5287': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'dd_max': 0.8,
                                                  'dd_min': 0.4,
                                                  'session_max': -0.4,
                                                  'volume_min': 1},
                                      'item_rule': 'symbol_AL',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'AFTER',
                                      'price_band': '20000_TO_100000',
                                      'root_confirmation': 'MOMENTUM_0.2',
                                      'root_contract': {'condition_trigger': 'known_false_to_known_true',
                                                        'hold_seconds': 0,
                                                        'return_60s_min_pct': 0.2,
                                                        'signal': 'MOMENTUM',
                                                        'signal_buy10_min': None,
                                                        'structure_window_seconds': None,
                                                        'warmup_seconds': 60},
                                      'route': 'SOR',
                                      'symbol_group': 'other_non_fixed'},
 'manual_extended_a894da51c88c3ef2': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'session_min': 0.4},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'GE_100000',
                                      'root_confirmation': 'PEAK_WAIT120_TOL0.2',
                                      'root_contract': {'allowed_below_original_low_pct': 0.2,
                                                        'breach_operator': 'strict_less',
                                                        'confirmation': 'PEAK',
                                                        'maximum_wait_seconds': 120,
                                                        'signal': 'native_first_turn',
                                                        'touch_operator': 'less_or_equal'},
                                      'route': 'NXT',
                                      'symbol_group': '196170'},
 'manual_extended_b3f20a28786bbd4e': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'buy10_min': 60,
                                                  'dd_max_exclusive': 0.4,
                                                  'dd_min': 0.2,
                                                  'session_max': -0.4},
                                      'item_rule': 'symbol_AL',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'AFTER',
                                      'price_band': '20000_TO_100000',
                                      'root_confirmation': 'FIRST',
                                      'root_contract': {'confirmation': 'immediate',
                                                        'signal': 'native_first_turn'},
                                      'route': 'SOR',
                                      'symbol_group': '034020'},
 'manual_extended_c65c5fd0f5127f58': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'buy10_min': 60,
                                                  'dd_max_exclusive': 0.4,
                                                  'dd_min': 0.2,
                                                  'session_min': 0.4},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': '20000_TO_100000',
                                      'root_confirmation': 'RETEST_PEAK_WAIT120_TOL0.2',
                                      'root_contract': {'allowed_below_original_low_pct': 0.2,
                                                        'breach_operator': 'strict_less',
                                                        'confirmation': 'RETEST_PEAK',
                                                        'maximum_wait_seconds': 120,
                                                        'signal': 'native_first_turn',
                                                        'touch_operator': 'less_or_equal'},
                                      'route': 'NXT',
                                      'symbol_group': 'other_non_fixed'},
 'manual_extended_f34ce7788ddc4e13': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'ret_min': 0.2,
                                                  'session_max_exclusive': 0.4,
                                                  'session_min_exclusive': -0.4,
                                                  'structure': 'RISING'},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'GE_100000',
                                      'root_confirmation': 'MOMENTUM_0.2',
                                      'root_contract': {'condition_trigger': 'known_false_to_known_true',
                                                        'hold_seconds': 0,
                                                        'return_60s_min_pct': 0.2,
                                                        'signal': 'MOMENTUM',
                                                        'signal_buy10_min': None,
                                                        'structure_window_seconds': None,
                                                        'warmup_seconds': 60},
                                      'route': 'NXT',
                                      'symbol_group': 'other_non_fixed'},
 'manual_extended_f74502b35a4fae1f': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'dd_max': 0.8,
                                                  'dd_min': 0.4,
                                                  'session_max_exclusive': 0.4,
                                                  'session_min_exclusive': -0.4},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'LT_20000',
                                      'root_confirmation': 'FIRST',
                                      'root_contract': {'confirmation': 'immediate',
                                                        'signal': 'native_first_turn'},
                                      'route': 'NXT',
                                      'symbol_group': 'other_non_fixed'},
 'manual_extended_f9a43c88911fdc0b': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'dd_min': 1.2},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3,
                                                         'supplement': 'same item completed bars; explicit '
                                                                       'source cutoff only; later retained '
                                                                       'prices are allowed outcome evidence',
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'ALL',
                                      'root_confirmation': 'FIRST',
                                      'root_contract': {'confirmation': 'immediate',
                                                        'signal': 'native_first_turn'},
                                      'route': 'NXT',
                                      'symbol_group': 'samsung'}}

def phase(bid):
    root=NEW_DEFINITIONS[bid]['root_contract']
    if root['signal']=='MOMENTUM':return 'MOMENTUM_CROSS'
    return {'immediate':'FIRST_UPTICK','PEAK':'PEAK_RECLAIM',
            'RETEST_FIRST':'RETEST_RECLAIM_FIRST','RETEST_PEAK':'RETEST_RECLAIM_PEAK'}[root['confirmation']]

PHASES={bid:phase(bid) for bid in NEW_DEFINITIONS}
DEFINITIONS=dict(OLD.DEFINITIONS,**NEW_DEFINITIONS)
ALIASES=dict(OLD.ALIASES,**{'extended_'+bid[-16:]:bid for bid in NEW_DEFINITIONS})
MANIFEST=dict(schema=VERSION,parent_registry_sha256=OLD.SHA256,definitions=DEFINITIONS,
              phase_bindings=dict(OLD.PHASES,**PHASES),research_batch_sha256=RESEARCH_BATCH_SHA256)
SHA256=digest(MANIFEST)

def definition(bid):
    return copy.deepcopy(EXTENDED_DEFINITIONS[bid]) if bid in EXTENDED_DEFINITIONS else OLD.definition(bid)

def branch(bid):
    if bid not in EXTENDED_DEFINITIONS:return OLD.branch(bid)
    return dict(branch_id=bid,kind='registered_pattern',definition_sha256=digest(definition(bid)),decision_phase=PHASES[bid])

def applicable(bid,key,route):
    if bid not in EXTENDED_DEFINITIONS:return OLD.applicable(bid,key,route)
    g,m,b=key.split('|');d=EXTENDED_DEFINITIONS[bid]
    return (g,m,route)==(d['symbol_group'],d['market'],d['route']) and d['price_band'] in ('ALL',b)

def validate_payload(p,key,route):
    if not isinstance(p,dict) or set(p)!={'composition','branches'} or p['composition']!='ANY_MATCH_ONE_INTENT' or not p['branches']:
        raise ValueError('extended_portfolio_invalid')
    ids=[b.get('branch_id') for b in p['branches']]
    if len(ids)!=len(set(ids)):raise ValueError('extended_duplicate_branch')
    if any(bid not in DEFINITIONS or b!=branch(bid) or not applicable(bid,key,route) for bid,b in zip(ids,p['branches'])):
        raise ValueError('extended_definition_or_scope_invalid')

def matches(bid,event,features):
    if bid in CUMULATIVE.DEFINITIONS:
        if not applicable(bid,cell_key(event['symbol'],event['market'],event['confirmation_price']),event['venue']):return False
        CUMULATIVE.validate_signal(event)
        return True
    if bid in JOINT.COMPOSED:
        if not applicable(bid,cell_key(event['symbol'],event['market'],event['confirmation_price']),event['venue']):return False
        JOINT.validate_composed(event)
        return True
    if bid not in EXTENDED_DEFINITIONS:return OLD.matches(bid,event,features)
    d=EXTENDED_DEFINITIONS[bid]
    if (not applicable(bid,cell_key(event['symbol'],event['market'],event['confirmation_price']),event['venue'])
            or event.get('source_item')!=event['symbol']+('_NX' if d['market']=='PRE' else '_AL')):return False
    values=dict(features);values.setdefault('spread', event.get('spread_pct'));results=[]
    for name,bound in d['filters'].items():
        op=next((s for s in ('_min_exclusive','_max_exclusive','_min','_max') if name.endswith(s)),None)
        value=values.get(name[:-len(op)] if op else name)
        results.append(None if value is None else value>bound if op=='_min_exclusive' else value<bound if op=='_max_exclusive' else value>=bound if op=='_min' else value<=bound if op=='_max' else value==bound)
    return False if False in results else None if None in results else True


# Explicit 2026-10-13 successor. Frozen base MANIFEST/SHA256 stay addressable.
ADDITIONAL_DEFINITIONS = {'manual_residual_0d7e29b0230e5b49': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'dd_max': 1.2, 'dd_min': 0.4, 'spread_max': 0.1},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3.0,
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'GE_100000',
                                      'root_confirmation': 'FIRST_HOLD1',
                                      'root_contract': {'comparison': 'greater_or_equal_original_first_price',
                                                        'confirmation': 'FIRST_PRICE_HOLD',
                                                        'confirmation_tick': 'first_received_at_or_after_hold',
                                                        'hold_seconds': 1,
                                                        'maximum_wait_seconds': None,
                                                        'pending_limit': 'existing_MAX_PENDING',
                                                        'signal': 'native_first_turn',
                                                        'source_continuity': 'same_native_interval_and_epoch'},
                                      'route': 'NXT',
                                      'symbol_group': 'other_non_fixed'},
 'manual_residual_29b499784843baed': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'buy10_min': 60,
                                                  'ret_max_exclusive': 0.2,
                                                  'ret_min': 0,
                                                  'session_max_exclusive': -0.4,
                                                  'vwap_min': 0},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3.0,
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'LT_20000',
                                      'root_confirmation': 'FIRST_HOLD3',
                                      'root_contract': {'comparison': 'greater_or_equal_original_first_price',
                                                        'confirmation': 'FIRST_PRICE_HOLD',
                                                        'confirmation_tick': 'first_received_at_or_after_hold',
                                                        'hold_seconds': 3,
                                                        'maximum_wait_seconds': None,
                                                        'pending_limit': 'existing_MAX_PENDING',
                                                        'signal': 'native_first_turn',
                                                        'source_continuity': 'same_native_interval_and_epoch'},
                                      'route': 'NXT',
                                      'symbol_group': 'other_non_fixed'},
 'manual_residual_410caad162a07c2c': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'buy10_min': 60,
                                                  'dd_max_exclusive': 0.4,
                                                  'ret_max_exclusive': 0.2,
                                                  'ret_min': -0.2,
                                                  'session_min': -0.4,
                                                  'vwap_min': 0},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3.0,
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'GE_100000',
                                      'root_confirmation': 'FIRST_HOLD1',
                                      'root_contract': {'comparison': 'greater_or_equal_original_first_price',
                                                        'confirmation': 'FIRST_PRICE_HOLD',
                                                        'confirmation_tick': 'first_received_at_or_after_hold',
                                                        'hold_seconds': 1,
                                                        'maximum_wait_seconds': None,
                                                        'pending_limit': 'existing_MAX_PENDING',
                                                        'signal': 'native_first_turn',
                                                        'source_continuity': 'same_native_interval_and_epoch'},
                                      'route': 'NXT',
                                      'symbol_group': '196170'},
 'manual_residual_503ffaf24ebfe783': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'buy10_min': 60,
                                                  'ret_max_exclusive': 0.2,
                                                  'ret_min': 0,
                                                  'session_max_exclusive': -0.4,
                                                  'vwap_min': 0},
                                      'item_rule': 'symbol_AL',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3.0,
                                                         'target_net_pct': 0.4},
                                      'market': 'AFTER',
                                      'price_band': 'LT_20000',
                                      'root_confirmation': 'FIRST_HOLD3',
                                      'root_contract': {'comparison': 'greater_or_equal_original_first_price',
                                                        'confirmation': 'FIRST_PRICE_HOLD',
                                                        'confirmation_tick': 'first_received_at_or_after_hold',
                                                        'hold_seconds': 3,
                                                        'maximum_wait_seconds': None,
                                                        'pending_limit': 'existing_MAX_PENDING',
                                                        'signal': 'native_first_turn',
                                                        'source_continuity': 'same_native_interval_and_epoch'},
                                      'route': 'SOR',
                                      'symbol_group': 'other_non_fixed'},
 'manual_residual_536f6d1c9b207d1d': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'dd_max': 0.2,
                                                  'ret_max_exclusive': 0.4,
                                                  'ret_min': 0,
                                                  'spread_max': 0.1,
                                                  'structure': 'RISING'},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3.0,
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'GE_100000',
                                      'root_confirmation': 'BREAKOUT60',
                                      'root_contract': {'comparison': 'strict_greater',
                                                        'condition_trigger': 'known_false_to_known_true',
                                                        'confirmation': 'HIGH_BREAKOUT',
                                                        'prior_high_window_seconds': 60,
                                                        'signal': 'BREAKOUT',
                                                        'warmup_seconds': 60},
                                      'route': 'NXT',
                                      'symbol_group': 'other_non_fixed'},
 'manual_residual_bac0e83e966ed3ea': {'definition_version': 1,
                                      'feature_contract': {'buy10': '10 native known-side quantity weighted '
                                                                    'trades',
                                                           'dd': '100*(prior_300s_high/current_trade-1)',
                                                           'ret': '60s backward predecessor trade',
                                                           'session': 'first valid observed session trade',
                                                           'structure': 'current_30s vs preceding_30s '
                                                                        'high/low; 60s warmup',
                                                           'volume': 'current_60s/prior_60s qty; 120s '
                                                                     'warmup'},
                                      'feature_time': 'actual_confirmation_received_prefix',
                                      'filters': {'dd_max': 1.2, 'dd_min': 0.4, 'spread_max': 0.1},
                                      'item_rule': 'symbol_NX',
                                      'kind': 'manual_path_pattern',
                                      'label_contract': {'cost_rate': 0.0023,
                                                         'horizon_seconds': 1800,
                                                         'stop_net_pct': -3.0,
                                                         'target_net_pct': 0.4},
                                      'market': 'PRE',
                                      'price_band': 'LT_20000',
                                      'root_confirmation': 'FIRST_HOLD1',
                                      'root_contract': {'comparison': 'greater_or_equal_original_first_price',
                                                        'confirmation': 'FIRST_PRICE_HOLD',
                                                        'confirmation_tick': 'first_received_at_or_after_hold',
                                                        'hold_seconds': 1,
                                                        'maximum_wait_seconds': None,
                                                        'pending_limit': 'existing_MAX_PENDING',
                                                        'signal': 'native_first_turn',
                                                        'source_continuity': 'same_native_interval_and_epoch'},
                                      'route': 'NXT',
                                      'symbol_group': 'other_non_fixed'}}
EXTENDED_DEFINITIONS = dict(NEW_DEFINITIONS, **ADDITIONAL_DEFINITIONS)
DEFINITIONS = dict(DEFINITIONS, **ADDITIONAL_DEFINITIONS)
PHASES = dict(PHASES, **{b: ('HIGH_BREAKOUT' if d['root_contract']['signal']=='BREAKOUT' else 'FIRST_PRICE_HOLD') for b,d in ADDITIONAL_DEFINITIONS.items()})
SUCCESSOR_MANIFEST = dict(schema='main_residual_session_catalog_v1', parent_registry_sha256=SHA256, additions=ADDITIONAL_DEFINITIONS)
SUCCESSOR_SHA256 = digest(SUCCESSOR_MANIFEST)

from src.engine.scalping import reversal_joint_catalog as JOINT
JOINT_DEFINITIONS = JOINT.DEFINITIONS
EXTENDED_DEFINITIONS = dict(EXTENDED_DEFINITIONS, **JOINT_DEFINITIONS)
DEFINITIONS = dict(DEFINITIONS, **JOINT_DEFINITIONS)
PHASES = dict(PHASES, **JOINT.PHASES)
JOINT_MANIFEST = dict(schema=JOINT.VERSION,parent_registry_sha256=SUCCESSOR_SHA256,
    additions=JOINT_DEFINITIONS)
JOINT_SHA256 = digest(JOINT_MANIFEST)

# Explicit cumulative successor. Earlier manifests and hashes stay frozen.
from src.engine.scalping import reversal_cumulative_catalog as CUMULATIVE
CUMULATIVE_DEFINITIONS = CUMULATIVE.DEFINITIONS
EXTENDED_DEFINITIONS = dict(EXTENDED_DEFINITIONS, **CUMULATIVE_DEFINITIONS)
DEFINITIONS = dict(DEFINITIONS, **CUMULATIVE_DEFINITIONS)
PHASES = dict(PHASES, **CUMULATIVE.PHASES)
CUMULATIVE_MANIFEST = dict(schema=CUMULATIVE.VERSION,parent_registry_sha256=JOINT_SHA256,
                          data_sha256=CUMULATIVE.DATA_SHA256,additions=CUMULATIVE.LEGACY_DEFINITIONS)
CUMULATIVE_SHA256 = digest(CUMULATIVE_MANIFEST)
PROGRESS_MANIFEST = dict(schema='main_price_progress_definition_catalog_v1',parent_registry_sha256=CUMULATIVE_SHA256,
                         data_sha256=CUMULATIVE.PROGRESS_DATA_SHA256,additions=CUMULATIVE.PROGRESS_DEFINITIONS)
PROGRESS_SHA256 = digest(PROGRESS_MANIFEST)

def registry_for(branch_ids):
    ids=tuple(branch_ids)
    if any(b in CUMULATIVE.PROGRESS_DEFINITIONS for b in ids):return PROGRESS_SHA256
    if any(b in CUMULATIVE_DEFINITIONS for b in ids):return CUMULATIVE_SHA256
    if any(b in JOINT_DEFINITIONS for b in ids):return JOINT_SHA256
    return SUCCESSOR_SHA256 if any(b in ADDITIONAL_DEFINITIONS for b in ids) else SHA256
