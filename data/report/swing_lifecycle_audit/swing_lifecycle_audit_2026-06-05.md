# Swing Lifecycle Audit - 2026-06-05

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `16`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `19`
- observation_axis_status: `{'ready': 10}`
- panic_state: `RECOVERY_WATCH`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': 0.0614, 'win_rate_pct': 42.9, 'wins': 3, 'losses': 3, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 2, 'avg_profit_rate_pct': -1.6997}, 'blocked_swing_gap': {'count': 2, 'avg_profit_rate_pct': -0.4007}, 'blocked_swing_score_vpw': {'count': 3, 'avg_profit_rate_pct': 0.0428}, 'market_regime_block': {'count': 2, 'avg_profit_rate_pct': 1.4227}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 81580 | 16 |
| `holding` | 497 | 64 |
| `scale_in` | 211 | 10 |
| `exit` | 45 | 16 |
| `other` | 23920 | 23 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 723 | 5 |
| `blocked_swing_gap` | 4854 | 6 |
| `blocked_swing_score_vpw` | 22972 | 16 |
| `gatekeeper_fast_reuse` | 28 | 2 |
| `gatekeeper_fast_reuse_bypass` | 695 | 5 |
| `gatekeeper_reject_cache_reuse` | 651 | 3 |
| `holding_flow_ofi_smoothing_applied` | 482 | 56 |
| `market_regime_block` | 23589 | 16 |
| `market_regime_prior_observed` | 106 | 16 |
| `sell_order_sent` | 1 | 1 |
| `swing_entry_micro_context_observed` | 23486 | 8 |
| `swing_entry_policy_evaluated` | 23695 | 16 |
| `swing_probe_discarded` | 4408 | 15 |
| `swing_probe_entry_candidate` | 19 | 12 |
| `swing_probe_exit_signal` | 19 | 14 |
| `swing_probe_holding_started` | 19 | 12 |
| `swing_probe_scale_in_order_assumed_filled` | 11 | 9 |
| `swing_probe_sell_order_assumed_filled` | 19 | 14 |
| `swing_probe_state_persisted` | 55 | 1 |
| `swing_probe_state_restored` | 53 | 1 |
| `swing_reentry_counterfactual_after_loss` | 46 | 7 |
| `swing_same_symbol_loss_reentry_blocked` | 6 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 14 | 12 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 51 | 1 |
| `swing_scale_in_micro_context_observed` | 186 | 10 |
| `swing_sim_buy_order_assumed_filled` | 15 | 8 |
| `swing_sim_holding_started` | 15 | 8 |
| `swing_sim_order_bundle_assumed_filled` | 15 | 8 |
| `swing_sim_scale_in_order_assumed_filled` | 14 | 9 |
| `swing_sim_sell_order_assumed_filled` | 6 | 4 |

## OFI/QI Micro Context

- sample_count: `47943`
- stale_missing_unique_record_count: `16`
- stale_missing_ratio: `0.0725`
- stale_missing_reason_counts: `{'micro_missing': 3474, 'micro_not_ready': 2999, 'state_insufficient': 2999, 'observer_unhealthy': 6}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2993, 'micro_missing': 475, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 14, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3, 'micro_missing': 1}`
- stale_missing_group_counts: `{'entry': 2992, 'exit': 482}`
- stale_missing_group_unique_record_counts: `{'entry': 15, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 41093, 'bearish': 1565, 'bullish': 1575, 'insufficient': 2992}`
- scale_in_micro_state_counts: `{'bearish': 14, 'neutral': 196, 'bullish': 1}`
- exit_micro_state_counts: `{'neutral': 465, 'bullish': 9, 'bearish': 26, 'insufficient': 7}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 478, 'CONFIRM_EXIT': 4}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 211}`
- add_triggers: `{'swing_avg_down_ok': 25}`
- price_policies: `{'WAIT_FOR_PULLBACK': 10, 'market': 25, 'KEEP_EXISTING_PRICE': 175, 'ALLOW_EXISTING_PRICE': 1}`
- add_ratio_summary: `{'count': 25, 'min': 0.4, 'max': 0.5, 'avg': 0.49028799999999995, 'mean': 0.49028799999999995, 'p50': 0.5, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 25}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `48`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 16 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 16 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 13 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 33 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 85 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 64 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 10 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 16 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 47225 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 211 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 482 | `ready` |

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
