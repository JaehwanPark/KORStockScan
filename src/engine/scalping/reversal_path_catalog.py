"""Eight fixed research definitions; v3 registry remains immutable."""
from __future__ import annotations
import copy
from src.engine.scalping import reversal_registered_catalog as OLD
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = 'main_registered_path_catalog_v1'
REGISTERED_AT = '2026-10-07'
LABEL = OLD.LABEL
ROUTES = OLD.ROUTES
BANDS = OLD.BANDS
FIXED = OLD.FIXED
group = OLD.group
band = OLD.band
cell_key = OLD.cell_key
cells = OLD.cells
ALIASES = {'SA': 'manual_path_35c2d4b8fb178441',
 'SB': 'manual_path_918aff358c3edb8c',
 'DA': 'manual_path_ad9afa2f9f981689',
 'HA': 'manual_type_ae4445459dc942c8',
 'HB': 'manual_path_f37911fb56300f77',
 'AA': 'manual_path_9e8f22a0a77899e4',
 'JA': 'manual_path_7d9fd5ccc8bfe99b',
 'GA': 'manual_path_dca327a873720e53'}
NEW_DEFINITIONS = {'manual_path_35c2d4b8fb178441': {'kind': 'manual_path_pattern',
                                  'definition_version': 1,
                                  'symbol_group': 'samsung',
                                  'market': 'REGULAR',
                                  'route': 'SOR',
                                  'price_band': 'ALL',
                                  'item_rule': 'symbol_AL',
                                  'root_confirmation': 'MOMENTUM_0.1',
                                  'root_contract': {'signal': 'MOMENTUM',
                                                    'return_60s_min_pct': 0.1,
                                                    'structure_window_seconds': None,
                                                    'warmup_seconds': 60,
                                                    'condition_trigger': 'known_false_to_known_true',
                                                    'hold_seconds': 0,
                                                    'signal_buy10_min': None},
                                  'population': 'all_valid_ticks',
                                  'feature_time': 'actual_confirmation_received_prefix',
                                  'filters': {'session_trend': 'UP',
                                              'structure': 'FALLING',
                                              'ret_min': 0,
                                              'ret_max_exclusive': 0.2,
                                              'dd_min': 0.2,
                                              'dd_max_exclusive': 0.4},
                                  'confirmation_contract': {'native_sequence_continuity': True,
                                                            'fresh_actual_confirmation_quote': True,
                                                            'condition_unknown_does_not_rearm': True,
                                                            'same_confirmation_one_intent': True},
                                  'label_contract': {'target_net_pct': 0.4,
                                                     'stop_net_pct': -3.0,
                                                     'cost_rate': 0.0023,
                                                     'horizon_seconds': 1800},
                                  'feature_contract': {'dd': '100*(prior_300s_high/current_trade-1)',
                                                       'ret': '60s backward '
                                                              'predecessor '
                                                              'trade',
                                                       'structure': 'current_30s '
                                                                    'vs '
                                                                    'preceding_30s '
                                                                    'high/low; '
                                                                    '60s '
                                                                    'warmup',
                                                       'volume': 'current_60s/prior_60s '
                                                                 'qty; 120s '
                                                                 'warmup',
                                                       'buy10': '10 native '
                                                                'known-side '
                                                                'quantity '
                                                                'weighted '
                                                                'trades',
                                                       'session': 'first valid '
                                                                  'observed '
                                                                  'session '
                                                                  'trade'},
                                  'branch_id': 'manual_path_35c2d4b8fb178441'},
 'manual_path_918aff358c3edb8c': {'kind': 'manual_path_pattern',
                                  'definition_version': 1,
                                  'symbol_group': 'samsung',
                                  'market': 'REGULAR',
                                  'route': 'SOR',
                                  'price_band': 'ALL',
                                  'item_rule': 'symbol_AL',
                                  'root_confirmation': 'RETEST_PEAK_WAIT120_TOL0.2',
                                  'root_contract': {'signal': 'native_first_turn',
                                                    'confirmation': 'RETEST_PEAK',
                                                    'maximum_wait_seconds': 120,
                                                    'allowed_below_original_low_pct': 0.2,
                                                    'breach_operator': 'strict_less',
                                                    'touch_operator': 'less_or_equal'},
                                  'population': 'all_native_first_turns',
                                  'feature_time': 'actual_confirmation_received_prefix',
                                  'filters': {'session_trend': 'NEUTRAL',
                                              'structure': 'FALLING',
                                              'ret_max_exclusive': 0,
                                              'dd_min': 0.4,
                                              'dd_max': 0.8,
                                              'volume_min': 1},
                                  'confirmation_contract': {'native_sequence_continuity': True,
                                                            'fresh_actual_confirmation_quote': True,
                                                            'condition_unknown_does_not_rearm': True,
                                                            'same_confirmation_one_intent': True},
                                  'label_contract': {'target_net_pct': 0.4,
                                                     'stop_net_pct': -3.0,
                                                     'cost_rate': 0.0023,
                                                     'horizon_seconds': 1800},
                                  'feature_contract': {'dd': '100*(prior_300s_high/current_trade-1)',
                                                       'ret': '60s backward '
                                                              'predecessor '
                                                              'trade',
                                                       'structure': 'current_30s '
                                                                    'vs '
                                                                    'preceding_30s '
                                                                    'high/low; '
                                                                    '60s '
                                                                    'warmup',
                                                       'volume': 'current_60s/prior_60s '
                                                                 'qty; 120s '
                                                                 'warmup',
                                                       'buy10': '10 native '
                                                                'known-side '
                                                                'quantity '
                                                                'weighted '
                                                                'trades',
                                                       'session': 'first valid '
                                                                  'observed '
                                                                  'session '
                                                                  'trade'},
                                  'branch_id': 'manual_path_918aff358c3edb8c'},
 'manual_path_ad9afa2f9f981689': {'kind': 'manual_path_pattern',
                                  'definition_version': 1,
                                  'symbol_group': '034020',
                                  'market': 'REGULAR',
                                  'route': 'SOR',
                                  'price_band': 'ALL',
                                  'item_rule': 'symbol_AL',
                                  'root_confirmation': 'MOMENTUM_0.1',
                                  'root_contract': {'signal': 'MOMENTUM',
                                                    'return_60s_min_pct': 0.1,
                                                    'structure_window_seconds': None,
                                                    'warmup_seconds': 60,
                                                    'condition_trigger': 'known_false_to_known_true',
                                                    'hold_seconds': 0,
                                                    'signal_buy10_min': None},
                                  'population': 'all_valid_ticks',
                                  'feature_time': 'actual_confirmation_received_prefix',
                                  'filters': {'session_trend': 'NEUTRAL',
                                              'structure': 'MIXED',
                                              'ret_min': 0.2,
                                              'dd_min': 0.2,
                                              'dd_max_exclusive': 0.4,
                                              'vwap_min': 0},
                                  'confirmation_contract': {'native_sequence_continuity': True,
                                                            'fresh_actual_confirmation_quote': True,
                                                            'condition_unknown_does_not_rearm': True,
                                                            'same_confirmation_one_intent': True},
                                  'label_contract': {'target_net_pct': 0.4,
                                                     'stop_net_pct': -3.0,
                                                     'cost_rate': 0.0023,
                                                     'horizon_seconds': 1800},
                                  'feature_contract': {'dd': '100*(prior_300s_high/current_trade-1)',
                                                       'ret': '60s backward '
                                                              'predecessor '
                                                              'trade',
                                                       'structure': 'current_30s '
                                                                    'vs '
                                                                    'preceding_30s '
                                                                    'high/low; '
                                                                    '60s '
                                                                    'warmup',
                                                       'volume': 'current_60s/prior_60s '
                                                                 'qty; 120s '
                                                                 'warmup',
                                                       'buy10': '10 native '
                                                                'known-side '
                                                                'quantity '
                                                                'weighted '
                                                                'trades',
                                                       'session': 'first valid '
                                                                  'observed '
                                                                  'session '
                                                                  'trade'},
                                  'branch_id': 'manual_path_ad9afa2f9f981689'},
 'manual_path_f37911fb56300f77': {'kind': 'manual_path_pattern',
                                  'definition_version': 1,
                                  'symbol_group': '403870',
                                  'market': 'REGULAR',
                                  'route': 'SOR',
                                  'price_band': 'ALL',
                                  'item_rule': 'symbol_AL',
                                  'root_confirmation': 'BREAKOUT60',
                                  'root_contract': {'signal': 'prior_60s_high_breakout',
                                                    'lookback_seconds': 60,
                                                    'strict_greater': True,
                                                    'warmup_seconds': 60,
                                                    'condition_trigger': 'known_false_to_known_true',
                                                    'hold_seconds': 0,
                                                    'signal_buy10_min': None},
                                  'population': 'all_valid_ticks',
                                  'feature_time': 'actual_confirmation_received_prefix',
                                  'filters': {'session_trend': 'UP',
                                              'structure': 'RISING',
                                              'ret_min': 0.2,
                                              'dd_max_exclusive': 0.2},
                                  'confirmation_contract': {'native_sequence_continuity': True,
                                                            'fresh_actual_confirmation_quote': True,
                                                            'condition_unknown_does_not_rearm': True,
                                                            'same_confirmation_one_intent': True},
                                  'label_contract': {'target_net_pct': 0.4,
                                                     'stop_net_pct': -3.0,
                                                     'cost_rate': 0.0023,
                                                     'horizon_seconds': 1800},
                                  'feature_contract': {'dd': '100*(prior_300s_high/current_trade-1)',
                                                       'ret': '60s backward '
                                                              'predecessor '
                                                              'trade',
                                                       'structure': 'current_30s '
                                                                    'vs '
                                                                    'preceding_30s '
                                                                    'high/low; '
                                                                    '60s '
                                                                    'warmup',
                                                       'volume': 'current_60s/prior_60s '
                                                                 'qty; 120s '
                                                                 'warmup',
                                                       'buy10': '10 native '
                                                                'known-side '
                                                                'quantity '
                                                                'weighted '
                                                                'trades',
                                                       'session': 'first valid '
                                                                  'observed '
                                                                  'session '
                                                                  'trade'},
                                  'branch_id': 'manual_path_f37911fb56300f77'},
 'manual_path_9e8f22a0a77899e4': {'kind': 'manual_path_pattern',
                                  'definition_version': 1,
                                  'symbol_group': '196170',
                                  'market': 'REGULAR',
                                  'route': 'SOR',
                                  'price_band': 'ALL',
                                  'item_rule': 'symbol_AL',
                                  'root_confirmation': 'RETEST_FIRST_WAIT120_TOL0.2',
                                  'root_contract': {'signal': 'native_first_turn',
                                                    'confirmation': 'RETEST_FIRST',
                                                    'maximum_wait_seconds': 120,
                                                    'allowed_below_original_low_pct': 0.2,
                                                    'breach_operator': 'strict_less',
                                                    'touch_operator': 'less_or_equal'},
                                  'population': 'all_native_first_turns',
                                  'feature_time': 'actual_confirmation_received_prefix',
                                  'filters': {'session_trend': 'DOWN',
                                              'structure': 'MIXED',
                                              'ret_min': 0,
                                              'ret_max_exclusive': 0.2,
                                              'dd_min_exclusive': 0.8,
                                              'dd_max_exclusive': 1.2},
                                  'confirmation_contract': {'native_sequence_continuity': True,
                                                            'fresh_actual_confirmation_quote': True,
                                                            'condition_unknown_does_not_rearm': True,
                                                            'same_confirmation_one_intent': True},
                                  'label_contract': {'target_net_pct': 0.4,
                                                     'stop_net_pct': -3.0,
                                                     'cost_rate': 0.0023,
                                                     'horizon_seconds': 1800},
                                  'feature_contract': {'dd': '100*(prior_300s_high/current_trade-1)',
                                                       'ret': '60s backward '
                                                              'predecessor '
                                                              'trade',
                                                       'structure': 'current_30s '
                                                                    'vs '
                                                                    'preceding_30s '
                                                                    'high/low; '
                                                                    '60s '
                                                                    'warmup',
                                                       'volume': 'current_60s/prior_60s '
                                                                 'qty; 120s '
                                                                 'warmup',
                                                       'buy10': '10 native '
                                                                'known-side '
                                                                'quantity '
                                                                'weighted '
                                                                'trades',
                                                       'session': 'first valid '
                                                                  'observed '
                                                                  'session '
                                                                  'trade'},
                                  'branch_id': 'manual_path_9e8f22a0a77899e4'},
 'manual_path_7d9fd5ccc8bfe99b': {'kind': 'manual_path_pattern',
                                  'definition_version': 1,
                                  'symbol_group': '036930',
                                  'market': 'REGULAR',
                                  'route': 'SOR',
                                  'price_band': 'ALL',
                                  'item_rule': 'symbol_AL',
                                  'root_confirmation': 'MOMENTUM_0.2',
                                  'root_contract': {'signal': 'MOMENTUM',
                                                    'return_60s_min_pct': 0.2,
                                                    'structure_window_seconds': None,
                                                    'warmup_seconds': 60,
                                                    'condition_trigger': 'known_false_to_known_true',
                                                    'hold_seconds': 0,
                                                    'signal_buy10_min': None},
                                  'population': 'all_valid_ticks',
                                  'feature_time': 'actual_confirmation_received_prefix',
                                  'filters': {'session_trend': 'UP',
                                              'structure': 'RISING',
                                              'ret_min': 0.2,
                                              'dd_max_exclusive': 0.2},
                                  'confirmation_contract': {'native_sequence_continuity': True,
                                                            'fresh_actual_confirmation_quote': True,
                                                            'condition_unknown_does_not_rearm': True,
                                                            'same_confirmation_one_intent': True},
                                  'label_contract': {'target_net_pct': 0.4,
                                                     'stop_net_pct': -3.0,
                                                     'cost_rate': 0.0023,
                                                     'horizon_seconds': 1800},
                                  'feature_contract': {'dd': '100*(prior_300s_high/current_trade-1)',
                                                       'ret': '60s backward '
                                                              'predecessor '
                                                              'trade',
                                                       'structure': 'current_30s '
                                                                    'vs '
                                                                    'preceding_30s '
                                                                    'high/low; '
                                                                    '60s '
                                                                    'warmup',
                                                       'volume': 'current_60s/prior_60s '
                                                                 'qty; 120s '
                                                                 'warmup',
                                                       'buy10': '10 native '
                                                                'known-side '
                                                                'quantity '
                                                                'weighted '
                                                                'trades',
                                                       'session': 'first valid '
                                                                  'observed '
                                                                  'session '
                                                                  'trade'},
                                  'branch_id': 'manual_path_7d9fd5ccc8bfe99b'},
 'manual_path_dca327a873720e53': {'kind': 'manual_path_pattern',
                                  'definition_version': 1,
                                  'symbol_group': 'other_non_fixed',
                                  'market': 'REGULAR',
                                  'route': 'SOR',
                                  'price_band': '20000_TO_100000',
                                  'item_rule': 'symbol_AL',
                                  'root_confirmation': 'MOMENTUM_0.05_HOLD1',
                                  'root_contract': {'signal': 'MOMENTUM',
                                                    'return_60s_min_pct': 0.05,
                                                    'structure_window_seconds': None,
                                                    'warmup_seconds': 60,
                                                    'condition_trigger': 'known_false_to_known_true',
                                                    'hold_seconds': 1,
                                                    'signal_buy10_min': None},
                                  'population': 'all_valid_ticks',
                                  'feature_time': 'actual_confirmation_received_prefix',
                                  'filters': {'session_trend': 'DOWN',
                                              'structure': 'MIXED',
                                              'ret_min': 0,
                                              'ret_max_exclusive': 0.2,
                                              'dd_min_exclusive': 0.8,
                                              'dd_max_exclusive': 1.2,
                                              'vwap_min': 0},
                                  'confirmation_contract': {'native_sequence_continuity': True,
                                                            'fresh_actual_confirmation_quote': True,
                                                            'condition_unknown_does_not_rearm': True,
                                                            'same_confirmation_one_intent': True},
                                  'label_contract': {'target_net_pct': 0.4,
                                                     'stop_net_pct': -3.0,
                                                     'cost_rate': 0.0023,
                                                     'horizon_seconds': 1800},
                                  'feature_contract': {'dd': '100*(prior_300s_high/current_trade-1)',
                                                       'ret': '60s backward '
                                                              'predecessor '
                                                              'trade',
                                                       'structure': 'current_30s '
                                                                    'vs '
                                                                    'preceding_30s '
                                                                    'high/low; '
                                                                    '60s '
                                                                    'warmup',
                                                       'volume': 'current_60s/prior_60s '
                                                                 'qty; 120s '
                                                                 'warmup',
                                                       'buy10': '10 native '
                                                                'known-side '
                                                                'quantity '
                                                                'weighted '
                                                                'trades',
                                                       'session': 'first valid '
                                                                  'observed '
                                                                  'session '
                                                                  'trade'},
                                  'branch_id': 'manual_path_dca327a873720e53'},
 'manual_type_ae4445459dc942c8': {'kind': 'registered_pattern',
                                  'definition_version': 1,
                                  'symbol_group': '403870',
                                  'market': 'REGULAR',
                                  'route': 'SOR',
                                  'price_band': 'ALL',
                                  'item_rule': 'symbol_AL',
                                  'decision_phase': 'FIRST_UPTICK',
                                  'confirmation_seconds': 0,
                                  'filters': {'session_trend': 'DOWN',
                                              'structure': 'FALLING',
                                              'ret_max_exclusive': 0,
                                              'dd_min_exclusive': 0.8,
                                              'dd_max_exclusive': 1.2},
                                  'label_contract': {'target_net_pct': 0.4,
                                                     'stop_net_pct': -3.0,
                                                     'cost_rate': 0.0023,
                                                     'horizon_seconds': 1800},
                                  'branch_id': 'manual_type_ae4445459dc942c8'}}
FROZEN_BASELINES = {'samsung|REGULAR|ALL|SOR': ['legacy_dd5_ge_1_2_v1'],
 'samsung|REGULAR|ALL|KRX': ['legacy_dd5_ge_1_2_v1'],
 'samsung|REGULAR|ALL|NXT': ['legacy_dd5_ge_1_2_v1'],
 '034020|REGULAR|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '034020|REGULAR|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '034020|REGULAR|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '034020|REGULAR|20000_TO_100000|SOR': ['D1'],
 '034020|REGULAR|20000_TO_100000|KRX': ['legacy_dd5_ge_1_2_v1'],
 '034020|REGULAR|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '034020|REGULAR|GE_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '034020|REGULAR|GE_100000|KRX': ['legacy_dd5_0_8_vol_up_v1'],
 '034020|REGULAR|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '403870|REGULAR|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|REGULAR|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|REGULAR|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|REGULAR|20000_TO_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '403870|REGULAR|20000_TO_100000|KRX': ['legacy_dd5_ge_1_2_v1'],
 '403870|REGULAR|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '403870|REGULAR|GE_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '403870|REGULAR|GE_100000|KRX': ['legacy_dd5_0_8_vol_up_v1'],
 '403870|REGULAR|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '196170|REGULAR|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '196170|REGULAR|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '196170|REGULAR|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '196170|REGULAR|20000_TO_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '196170|REGULAR|20000_TO_100000|KRX': ['legacy_dd5_ge_1_2_v1'],
 '196170|REGULAR|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '196170|REGULAR|GE_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '196170|REGULAR|GE_100000|KRX': ['legacy_dd5_0_8_vol_up_v1'],
 '196170|REGULAR|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '036930|REGULAR|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '036930|REGULAR|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '036930|REGULAR|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '036930|REGULAR|20000_TO_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '036930|REGULAR|20000_TO_100000|KRX': ['legacy_dd5_ge_1_2_v1'],
 '036930|REGULAR|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '036930|REGULAR|GE_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '036930|REGULAR|GE_100000|KRX': ['legacy_dd5_0_8_vol_up_v1'],
 '036930|REGULAR|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 'other_non_fixed|REGULAR|LT_20000|SOR': ['G4'],
 'other_non_fixed|REGULAR|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 'other_non_fixed|REGULAR|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 'other_non_fixed|REGULAR|20000_TO_100000|SOR': ['G1'],
 'other_non_fixed|REGULAR|20000_TO_100000|KRX': ['legacy_dd5_ge_1_2_v1'],
 'other_non_fixed|REGULAR|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 'other_non_fixed|REGULAR|GE_100000|SOR': ['G2'],
 'other_non_fixed|REGULAR|GE_100000|KRX': ['legacy_dd5_0_8_vol_up_v1'],
 'other_non_fixed|REGULAR|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 'samsung|PRE|ALL|SOR': ['legacy_drop_ge_1_0_v1'],
 'samsung|PRE|ALL|NXT': ['legacy_drop_ge_1_0_v1'],
 'samsung|AFTER|ALL|SOR': ['legacy_dd5_ge_0_4_v1'],
 'samsung|AFTER|ALL|KRX': ['legacy_dd5_ge_1_2_v1'],
 'samsung|AFTER|ALL|NXT': ['legacy_dd5_ge_0_4_v1'],
 '034020|PRE|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '034020|PRE|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '034020|PRE|20000_TO_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '034020|PRE|20000_TO_100000|NXT': ['legacy_all_v1'],
 '034020|PRE|GE_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '034020|PRE|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '034020|AFTER|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '034020|AFTER|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '034020|AFTER|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '034020|AFTER|20000_TO_100000|SOR': ['legacy_dd5_ge_0_4_v1'],
 '034020|AFTER|20000_TO_100000|KRX': ['legacy_dd5_ge_0_4_v1'],
 '034020|AFTER|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '034020|AFTER|GE_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '034020|AFTER|GE_100000|KRX': ['legacy_dd5_0_8_vol_up_v1'],
 '034020|AFTER|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '403870|PRE|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|PRE|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|PRE|20000_TO_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '403870|PRE|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '403870|PRE|GE_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '403870|PRE|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '403870|AFTER|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|AFTER|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|AFTER|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|AFTER|20000_TO_100000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '403870|AFTER|20000_TO_100000|KRX': ['legacy_dd5_ge_1_2_v1'],
 '403870|AFTER|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '403870|AFTER|GE_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 '403870|AFTER|GE_100000|KRX': ['legacy_dd5_0_8_vol_up_v1'],
 '403870|AFTER|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '196170|PRE|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '196170|PRE|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '196170|PRE|20000_TO_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '196170|PRE|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '196170|PRE|GE_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '196170|PRE|GE_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '196170|AFTER|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '196170|AFTER|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '196170|AFTER|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '196170|AFTER|20000_TO_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '196170|AFTER|20000_TO_100000|KRX': ['legacy_dd5_ge_1_2_v1'],
 '196170|AFTER|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '196170|AFTER|GE_100000|SOR': ['legacy_dd5_ge_0_4_v1'],
 '196170|AFTER|GE_100000|KRX': ['legacy_dd5_0_8_vol_up_v1'],
 '196170|AFTER|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '036930|PRE|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '036930|PRE|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '036930|PRE|20000_TO_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '036930|PRE|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '036930|PRE|GE_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '036930|PRE|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 '036930|AFTER|LT_20000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '036930|AFTER|LT_20000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '036930|AFTER|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 '036930|AFTER|20000_TO_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 '036930|AFTER|20000_TO_100000|KRX': ['legacy_dd5_ge_1_2_v1'],
 '036930|AFTER|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 '036930|AFTER|GE_100000|SOR': ['legacy_dd5_ge_0_4_v1'],
 '036930|AFTER|GE_100000|KRX': ['legacy_dd5_ge_0_4_v1'],
 '036930|AFTER|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 'other_non_fixed|PRE|LT_20000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 'other_non_fixed|PRE|LT_20000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 'other_non_fixed|PRE|20000_TO_100000|SOR': ['legacy_dd5_0_8_vol_up_v1'],
 'other_non_fixed|PRE|20000_TO_100000|NXT': ['legacy_dd5_0_8_vol_up_v1'],
 'other_non_fixed|PRE|GE_100000|SOR': ['legacy_dd5_ge_1_2_v1'],
 'other_non_fixed|PRE|GE_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 'other_non_fixed|AFTER|LT_20000|SOR': ['legacy_drop_0_4_rebound_le_0_3_v1'],
 'other_non_fixed|AFTER|LT_20000|KRX': ['legacy_drop_0_4_rebound_le_0_3_v1'],
 'other_non_fixed|AFTER|LT_20000|NXT': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 'other_non_fixed|AFTER|20000_TO_100000|SOR': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 'other_non_fixed|AFTER|20000_TO_100000|KRX': ['legacy_dd5_0_8_rebound_le_0_3_v1'],
 'other_non_fixed|AFTER|20000_TO_100000|NXT': ['legacy_dd5_ge_1_2_v1'],
 'other_non_fixed|AFTER|GE_100000|SOR': ['legacy_dd5_ge_0_4_v1'],
 'other_non_fixed|AFTER|GE_100000|KRX': ['legacy_dd5_ge_0_4_v1'],
 'other_non_fixed|AFTER|GE_100000|NXT': ['legacy_dd5_0_8_vol_up_v1']}

PHASES = {ALIASES['SA']: 'MOMENTUM_CROSS', ALIASES['DA']: 'MOMENTUM_CROSS',
          ALIASES['JA']: 'MOMENTUM_CROSS', ALIASES['HB']: 'HIGH_BREAKOUT',
          ALIASES['GA']: 'MOMENTUM_HOLD', ALIASES['SB']: 'RETEST_RECLAIM_PEAK',
          ALIASES['AA']: 'RETEST_RECLAIM_FIRST', ALIASES['HA']: B.FIRST}

def definition(bid):
    return copy.deepcopy(NEW_DEFINITIONS[bid]) if bid in NEW_DEFINITIONS else OLD.definition(bid)

def branch(bid):
    if bid not in NEW_DEFINITIONS:
        return OLD.branch(bid)
    d = definition(bid)
    return dict(branch_id=bid, kind='registered_pattern', definition_sha256=digest(d),
                decision_phase=PHASES[bid])

def applicable(bid, key, route):
    if bid not in NEW_DEFINITIONS:
        return OLD.applicable(bid,key,route)
    g,m,b=key.split('|');d=NEW_DEFINITIONS[bid]
    return g==d['symbol_group'] and m==d['market'] and route==d['route'] and d['price_band'] in ('ALL',b)

def validate_payload(p,key,route):
    if not isinstance(p,dict) or set(p)!={'composition','branches'} or p['composition']!='ANY_MATCH_ONE_INTENT' or not isinstance(p['branches'],list) or not p['branches']:
        raise ValueError('v4_portfolio_invalid')
    if any(not isinstance(b,dict) for b in p['branches']):raise ValueError('v4_portfolio_invalid')
    ids=[b.get('branch_id') for b in p['branches']]
    if len(set(ids))!=len(ids):raise ValueError('v4_duplicate_branch')
    for b in p['branches']:
        if b.get('branch_id') not in DEFINITIONS or b!=branch(b['branch_id']) or not applicable(b['branch_id'],key,route):
            raise ValueError('v4_definition_or_scope_invalid')

def matches(bid,event,f):
    if bid not in NEW_DEFINITIONS:return OLD.matches(bid,event,f)
    if not applicable(bid,cell_key(event['symbol'],event['market'],event['confirmation_price']),event['venue']) or event.get('source_item')!=event['symbol']+'_AL':return False
    values=dict(f,dd=event.get('drawdown_5m_pct'),volume=event.get('volume_ratio_60s'),spread=event.get('spread_pct'))
    results=[]
    for name,bound in definition(bid)['filters'].items():
        op=next((s for s in ('_min_exclusive','_max_exclusive','_min','_max') if name.endswith(s)),None)
        v=values.get(name[:-len(op)] if op else name)
        results.append(None if v is None else v>bound if op=='_min_exclusive' else v<bound if op=='_max_exclusive' else v>=bound if op=='_min' else v<=bound if op=='_max' else v==bound)
    return False if False in results else None if None in results else True

def _portfolios(key,route):
    values=copy.deepcopy(OLD.PORTFOLIOS[key][route]);seen={tuple(x['branch_ids']) for x in values}
    ids=[bid for bid in NEW_DEFINITIONS if applicable(bid,key,route)]
    new=[[bid] for bid in ids]+([ids] if len(ids)>1 else [])
    incumbent=FROZEN_BASELINES[key+'|'+route]
    new += [incumbent+[bid] for bid in ids]+([incumbent+ids] if ids else [])
    for branches in new:
        branches=list(dict.fromkeys(branches))
        if tuple(branches) in seen:continue
        values.append(dict(portfolio_id=digest(branches),branch_ids=branches));seen.add(tuple(branches))
    return values

DEFINITIONS = dict(OLD.MANIFEST['definitions'],**NEW_DEFINITIONS)
PORTFOLIOS={k:{r:_portfolios(k,r) for r in ROUTES[k.split('|')[1]]} for k in cells()}
MANIFEST=dict(schema=VERSION,registered_at=REGISTERED_AT,parent_registry_sha256=OLD.SHA256,
              definitions=DEFINITIONS,phase_bindings=PHASES,portfolios=PORTFOLIOS,
              frozen_incumbent_portfolios=FROZEN_BASELINES,support_routes=OLD.MANIFEST['support_routes'],
              fixed_symbols=FIXED,origin='exact_eight_manual_research_definitions')
SHA256=digest(MANIFEST)
