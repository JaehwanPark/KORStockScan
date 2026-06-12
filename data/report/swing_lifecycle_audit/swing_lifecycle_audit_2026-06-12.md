# Swing Lifecycle Audit - 2026-06-12

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `2`
- csv_rows: `2`
- db_rows: `26`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `33`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -1.1169, 'win_rate_pct': 14.3, 'wins': 1, 'losses': 6, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 1, 'avg_profit_rate_pct': None}, 'blocked_swing_gap': {'count': 3, 'avg_profit_rate_pct': -1.3524}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': -0.5614}, 'market_regime_prior_observed': {'count': 2, 'avg_profit_rate_pct': -2.0765}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 47119 | 26 |
| `holding` | 375 | 122 |
| `scale_in` | 363 | 18 |
| `exit` | 161 | 18 |
| `other` | 10529 | 28 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 5193 | 24 |
| `blocked_swing_gap` | 2761 | 20 |
| `blocked_swing_score_vpw` | 5198 | 23 |
| `gatekeeper_fast_reuse` | 62 | 12 |
| `gatekeeper_fast_reuse_bypass` | 5133 | 24 |
| `gatekeeper_reject_cache_reuse` | 3181 | 24 |
| `holding_flow_ofi_smoothing_applied` | 274 | 95 |
| `holding_started` | 27 | 1 |
| `market_regime_prior_observed` | 10392 | 26 |
| `sell_order_sent` | 139 | 6 |
| `swing_entry_micro_context_observed` | 10388 | 26 |
| `swing_entry_policy_evaluated` | 10392 | 26 |
| `swing_probe_discarded` | 4645 | 16 |
| `swing_probe_entry_candidate` | 9 | 8 |
| `swing_probe_exit_signal` | 9 | 9 |
| `swing_probe_holding_started` | 9 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 7 | 7 |
| `swing_probe_sell_order_assumed_filled` | 9 | 9 |
| `swing_probe_state_empty_overwrite_blocked` | 27 | 1 |
| `swing_probe_state_persisted` | 29 | 1 |
| `swing_probe_state_restored` | 32 | 1 |
| `swing_reentry_counterfactual_after_loss` | 16 | 3 |
| `swing_same_symbol_loss_reentry_blocked` | 4 | 3 |
| `swing_same_symbol_loss_reentry_cooldown` | 6 | 5 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 23 | 1 |
| `swing_scale_in_micro_context_observed` | 330 | 18 |
| `swing_sim_buy_order_assumed_filled` | 74 | 26 |
| `swing_sim_holding_started` | 74 | 26 |
| `swing_sim_order_bundle_assumed_filled` | 74 | 26 |
| `swing_sim_scale_in_order_assumed_filled` | 26 | 16 |
| `swing_sim_sell_order_assumed_filled` | 4 | 3 |

## OFI/QI Micro Context

- sample_count: `21582`
- stale_missing_unique_record_count: `28`
- stale_missing_ratio: `0.5685`
- stale_missing_reason_counts: `{'micro_missing': 12269, 'micro_not_ready': 12000, 'state_insufficient': 12000, 'observer_unhealthy': 22}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 11978, 'micro_missing': 269, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 22}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 25, 'micro_missing': 3, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- stale_missing_group_counts: `{'entry': 11832, 'exit': 274, 'scale_in': 163}`
- stale_missing_group_unique_record_counts: `{'entry': 23, 'scale_in': 2, 'exit': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 22, 'observer_unhealthy_with_other_reason': 22, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 8485, 'bearish': 394, 'bullish': 221, 'insufficient': 11832}`
- scale_in_micro_state_counts: `{'neutral': 187, 'insufficient': 163, 'bullish': 9, 'bearish': 4}`
- exit_micro_state_counts: `{'neutral': 258, 'bearish': 15, 'bullish': 9, 'insufficient': 5}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 274}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 363}`
- add_triggers: `{'swing_avg_down_ok': 33}`
- price_policies: `{'KEEP_EXISTING_PRICE': 157, 'market': 33, 'NO_CHANGE': 163, 'ALLOW_EXISTING_PRICE': 8, 'WAIT_FOR_PULLBACK': 2}`
- add_ratio_summary: `{'count': 33, 'min': 0.0069, 'max': 0.5, 'avg': 0.45790909090909093, 'mean': 0.45790909090909093, 'p50': 0.5, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 33}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `78`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 26 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 26 | 0 | 0 | 0 | None |
| `swing_model_floor` | 2 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 24 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 2 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 2 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 84 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 110 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 122 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 18 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 18 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 20932 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 363 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 274 | `ready` |

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
