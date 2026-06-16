# Swing Lifecycle Audit - 2026-06-16

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `21`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `24`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.4075, 'win_rate_pct': 42.9, 'wins': 3, 'losses': 4, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 4, 'avg_profit_rate_pct': -0.2445}, 'blocked_swing_gap': {'count': 1, 'avg_profit_rate_pct': 0.1699}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': -0.763}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 85329 | 21 |
| `holding` | 362 | 107 |
| `scale_in` | 716 | 11 |
| `exit` | 15 | 7 |
| `other` | 20803 | 23 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 9422 | 15 |
| `blocked_swing_gap` | 2171 | 10 |
| `blocked_swing_score_vpw` | 11285 | 18 |
| `gatekeeper_fast_reuse` | 636 | 11 |
| `gatekeeper_fast_reuse_bypass` | 8790 | 15 |
| `gatekeeper_reject_cache_reuse` | 7383 | 15 |
| `holding_flow_ofi_smoothing_applied` | 283 | 86 |
| `market_regime_pass` | 5239 | 21 |
| `market_regime_prior_observed` | 15469 | 21 |
| `swing_entry_micro_context_observed` | 20702 | 21 |
| `swing_entry_policy_evaluated` | 20708 | 21 |
| `swing_probe_discarded` | 4064 | 17 |
| `swing_probe_entry_candidate` | 5 | 4 |
| `swing_probe_exit_signal` | 5 | 4 |
| `swing_probe_holding_started` | 5 | 4 |
| `swing_probe_scale_in_order_assumed_filled` | 3 | 3 |
| `swing_probe_sell_order_assumed_filled` | 5 | 4 |
| `swing_probe_state_persisted` | 18 | 1 |
| `swing_probe_state_restored` | 30 | 1 |
| `swing_reentry_counterfactual_after_loss` | 17 | 1 |
| `swing_same_symbol_loss_reentry_blocked` | 6 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 3 | 2 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 21 | 1 |
| `swing_scale_in_micro_context_observed` | 703 | 11 |
| `swing_sim_buy_order_assumed_filled` | 79 | 21 |
| `swing_sim_holding_started` | 79 | 21 |
| `swing_sim_order_bundle_assumed_filled` | 79 | 21 |
| `swing_sim_scale_in_order_assumed_filled` | 10 | 8 |
| `swing_sim_sell_order_assumed_filled` | 5 | 3 |

## OFI/QI Micro Context

- sample_count: `42582`
- stale_missing_unique_record_count: `18`
- stale_missing_ratio: `0.1875`
- stale_missing_reason_counts: `{'micro_missing': 7983, 'micro_not_ready': 7701, 'state_insufficient': 7701, 'observer_unhealthy': 25}`
- stale_missing_reason_combination_counts: `{'micro_missing': 282, 'micro_missing+micro_not_ready+state_insufficient': 7676, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 25}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 7}`
- stale_missing_group_counts: `{'exit': 283, 'entry': 7700}`
- stale_missing_group_unique_record_counts: `{'entry': 18}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 25, 'observer_unhealthy_with_other_reason': 25, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 31600, 'bullish': 1023, 'bearish': 1250, 'insufficient': 7700}`
- scale_in_micro_state_counts: `{'bearish': 20, 'neutral': 672, 'bullish': 24}`
- exit_micro_state_counts: `{'neutral': 273, 'bearish': 14, 'bullish': 5, 'insufficient': 1}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 283}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 716}`
- add_triggers: `{'swing_avg_down_ok': 13}`
- price_policies: `{'WAIT_FOR_PULLBACK': 19, 'market': 13, 'KEEP_EXISTING_PRICE': 660, 'ALLOW_EXISTING_PRICE': 24}`
- add_ratio_summary: `{'count': 13, 'min': 0.0092, 'max': 0.5, 'avg': 0.45155384615384614, 'mean': 0.45155384615384614, 'p50': 0.4971, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 13}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `63`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 21 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 21 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 18 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 82 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 98 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 107 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 11 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 7 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 41573 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 716 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 283 | `ready` |

## AI Contract Audit

- schema_valid_rate: `None`
- parse_fail_count: `0`
- decision_disagreement_count: `0`
- latency_ms: `{'count': 0, 'min': None, 'max': None, 'avg': None, 'mean': None, 'p50': None, 'p95': None}`
- estimated_cost_krw: `{'count': 0, 'min': None, 'max': None, 'avg': None, 'mean': None, 'p50': None, 'p95': None}`
- prompt_types: `{}`

- `swing_gatekeeper_free_text_label` stage=`entry` severity=`medium`: Gatekeeper entry is currently reconstructed from report labels instead of a strict swing entry schema.
- `swing_holding_flow_scalping_prompt_reuse` stage=`holding_exit` severity=`medium`: Swing sell candidates can pass through holding-flow review that is named and tuned for scalping.
- `swing_scale_in_ai_contract_missing` stage=`scale_in` severity=`low`: Swing PYRAMID/AVG_DOWN observation is not yet represented by a dedicated AI proposal contract.
