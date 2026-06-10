# Swing Lifecycle Audit - 2026-06-10

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `28`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `29`
- observation_axis_status: `{'ready': 10}`
- panic_state: `RECOVERY_WATCH`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': 0.8408, 'win_rate_pct': 57.1, 'wins': 4, 'losses': 3, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 2, 'avg_profit_rate_pct': -0.0048}, 'blocked_swing_gap': {'count': 1, 'avg_profit_rate_pct': 1.4374}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.9604}, 'market_regime_block': {'count': 2, 'avg_profit_rate_pct': 0.7859}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 65005 | 28 |
| `holding` | 973 | 126 |
| `scale_in` | 88 | 19 |
| `exit` | 41 | 25 |
| `other` | 18322 | 34 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 2769 | 20 |
| `blocked_swing_gap` | 963 | 4 |
| `blocked_swing_score_vpw` | 15322 | 27 |
| `gatekeeper_fast_reuse` | 177 | 5 |
| `gatekeeper_fast_reuse_bypass` | 2596 | 20 |
| `gatekeeper_reject_cache_reuse` | 2005 | 11 |
| `holding_flow_ofi_smoothing_applied` | 899 | 104 |
| `market_regime_block` | 16182 | 28 |
| `market_regime_prior_observed` | 1909 | 28 |
| `sell_order_sent` | 11 | 11 |
| `swing_entry_micro_context_observed` | 17895 | 24 |
| `swing_entry_policy_evaluated` | 18091 | 28 |
| `swing_probe_discarded` | 5017 | 20 |
| `swing_probe_entry_candidate` | 11 | 8 |
| `swing_probe_exit_signal` | 11 | 10 |
| `swing_probe_holding_started` | 11 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 7 | 7 |
| `swing_probe_sell_order_assumed_filled` | 11 | 10 |
| `swing_probe_state_empty_overwrite_blocked` | 6 | 1 |
| `swing_probe_state_persisted` | 37 | 1 |
| `swing_probe_state_restored` | 48 | 1 |
| `swing_reentry_counterfactual_after_loss` | 64 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 18 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 14 | 10 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 44 | 1 |
| `swing_scale_in_micro_context_observed` | 47 | 19 |
| `swing_sim_buy_order_assumed_filled` | 74 | 22 |
| `swing_sim_holding_started` | 74 | 22 |
| `swing_sim_order_bundle_assumed_filled` | 74 | 22 |
| `swing_sim_scale_in_order_assumed_filled` | 34 | 18 |
| `swing_sim_sell_order_assumed_filled` | 8 | 4 |

## OFI/QI Micro Context

- sample_count: `37158`
- stale_missing_unique_record_count: `36`
- stale_missing_ratio: `0.0945`
- stale_missing_reason_counts: `{'micro_missing': 3510, 'micro_not_ready': 2626, 'state_insufficient': 2626, 'observer_unhealthy': 16}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2610, 'micro_missing': 884, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 16}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 25, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 9, 'micro_missing': 9}`
- stale_missing_group_counts: `{'entry': 2608, 'exit': 900, 'scale_in': 2}`
- stale_missing_group_unique_record_counts: `{'entry': 26, 'exit': 10, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 16, 'observer_unhealthy_with_other_reason': 16, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 31327, 'bearish': 862, 'bullish': 1355, 'insufficient': 2608}`
- scale_in_micro_state_counts: `{'bearish': 8, 'neutral': 77, 'bullish': 1, 'insufficient': 2}`
- exit_micro_state_counts: `{'neutral': 828, 'bearish': 46, 'bullish': 28, 'insufficient': 16}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 898, 'CONFIRM_EXIT': 1}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 88}`
- add_triggers: `{'swing_avg_down_ok': 41}`
- price_policies: `{'WAIT_FOR_PULLBACK': 4, 'market': 41, 'KEEP_EXISTING_PRICE': 41, 'ALLOW_EXISTING_PRICE': 1, 'NO_CHANGE': 1}`
- add_ratio_summary: `{'count': 41, 'min': 0.4, 'max': 1.0, 'avg': 0.5366780487804879, 'mean': 0.5366780487804879, 'p50': 0.4976, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 41}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `84`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 28 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 28 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 25 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 72 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 124 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 126 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 19 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 25 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 36152 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 88 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 899 | `ready` |

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
