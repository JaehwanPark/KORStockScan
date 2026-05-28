# Swing Lifecycle Audit - 2026-05-28

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `18`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `19`
- observation_axis_status: `{'ready': 10}`
- panic_state: `RECOVERY_WATCH`
- panic_active_sim_probe: `{'active_positions': 30, 'profit_sample': 26, 'avg_unrealized_profit_rate_pct': -0.8723, 'win_rate_pct': 0.0, 'wins': 0, 'losses': 25, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 2, 'avg_profit_rate_pct': -0.8558}, 'blocked_swing_score_vpw': {'count': 2, 'avg_profit_rate_pct': -0.3018}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': -1.0648}, 'unknown': {'count': 15, 'avg_profit_rate_pct': -0.5208}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 53660 | 18 |
| `holding` | 542 | 84 |
| `scale_in` | 38 | 11 |
| `exit` | 24 | 11 |
| `other` | 14363 | 20 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 3964 | 10 |
| `blocked_swing_gap` | 1105 | 4 |
| `blocked_swing_score_vpw` | 10296 | 18 |
| `gatekeeper_fast_reuse` | 463 | 4 |
| `gatekeeper_fast_reuse_bypass` | 3501 | 10 |
| `gatekeeper_reject_cache_reuse` | 3179 | 9 |
| `holding_flow_ofi_smoothing_applied` | 532 | 79 |
| `market_regime_block` | 10383 | 18 |
| `market_regime_prior_observed` | 3877 | 18 |
| `sell_order_failed` | 2 | 2 |
| `swing_entry_micro_context_observed` | 14194 | 13 |
| `swing_entry_policy_evaluated` | 14260 | 18 |
| `swing_probe_discarded` | 2658 | 15 |
| `swing_probe_entry_candidate` | 10 | 8 |
| `swing_probe_exit_signal` | 10 | 8 |
| `swing_probe_holding_started` | 10 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 8 |
| `swing_probe_sell_order_assumed_filled` | 10 | 8 |
| `swing_probe_state_persisted` | 30 | 1 |
| `swing_probe_state_restored` | 26 | 1 |
| `swing_reentry_counterfactual_after_loss` | 17 | 3 |
| `swing_same_symbol_loss_reentry_blocked` | 5 | 3 |
| `swing_same_symbol_loss_reentry_cooldown` | 5 | 4 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 20 | 1 |
| `swing_scale_in_micro_context_observed` | 15 | 11 |
| `swing_sim_buy_order_assumed_filled` | 10 | 5 |
| `swing_sim_holding_started` | 10 | 5 |
| `swing_sim_order_bundle_assumed_filled` | 10 | 5 |
| `swing_sim_scale_in_order_assumed_filled` | 15 | 11 |
| `swing_sim_sell_order_assumed_filled` | 2 | 1 |

## OFI/QI Micro Context

- sample_count: `29061`
- stale_missing_unique_record_count: `16`
- stale_missing_ratio: `0.1267`
- stale_missing_reason_counts: `{'micro_missing': 3682, 'micro_not_ready': 3154, 'state_insufficient': 3154, 'observer_unhealthy': 8}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 3146, 'micro_missing': 528, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing': 1, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- stale_missing_group_counts: `{'entry': 3147, 'exit': 532, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'entry': 14, 'exit': 1, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 23916, 'bearish': 826, 'insufficient': 3147, 'bullish': 590}`
- scale_in_micro_state_counts: `{'neutral': 35, 'insufficient': 3}`
- exit_micro_state_counts: `{'neutral': 504, 'bearish': 31, 'bullish': 5, 'insufficient': 4}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 532}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 38}`
- add_triggers: `{'swing_avg_down_ok': 23}`
- price_policies: `{'KEEP_EXISTING_PRICE': 14, 'market': 23, 'NO_CHANGE': 1}`
- add_ratio_summary: `{'count': 23, 'min': 0.4286, 'max': 1.0, 'avg': 0.5346260869565217, 'mean': 0.5346260869565217, 'p50': 0.5, 'p95': 0.9499999999999993}`
- post_add_outcomes: `{'pending_followup': 23}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `57`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 19 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 19 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 16 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 28 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 85 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 84 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 11 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 11 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 28479 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 38 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 532 | `ready` |

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
