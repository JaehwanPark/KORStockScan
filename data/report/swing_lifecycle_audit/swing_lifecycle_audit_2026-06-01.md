# Swing Lifecycle Audit - 2026-06-01

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `7`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `7`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.0404, 'win_rate_pct': 42.9, 'wins': 3, 'losses': 3, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 2, 'avg_profit_rate_pct': -0.4258}, 'blocked_swing_gap': {'count': 2, 'avg_profit_rate_pct': -0.1549}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.151}, 'market_regime_prior_observed': {'count': 2, 'avg_profit_rate_pct': 0.0}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 85160 | 7 |
| `holding` | 1173 | 116 |
| `scale_in` | 45 | 6 |
| `exit` | 48 | 18 |
| `other` | 23016 | 8 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 4136 | 2 |
| `blocked_swing_gap` | 4214 | 3 |
| `blocked_swing_score_vpw` | 18696 | 7 |
| `gatekeeper_fast_reuse` | 705 | 1 |
| `gatekeeper_fast_reuse_bypass` | 3431 | 2 |
| `gatekeeper_reject_cache_reuse` | 3171 | 2 |
| `holding_flow_ofi_smoothing_applied` | 1168 | 111 |
| `market_regime_prior_observed` | 22832 | 7 |
| `sell_order_sent` | 12 | 12 |
| `swing_entry_micro_context_observed` | 22783 | 5 |
| `swing_entry_policy_evaluated` | 22832 | 7 |
| `swing_probe_discarded` | 5132 | 7 |
| `swing_probe_entry_candidate` | 25 | 7 |
| `swing_probe_exit_signal` | 18 | 6 |
| `swing_probe_holding_started` | 25 | 7 |
| `swing_probe_scale_in_order_assumed_filled` | 15 | 6 |
| `swing_probe_sell_order_assumed_filled` | 18 | 6 |
| `swing_probe_state_persisted` | 58 | 1 |
| `swing_probe_state_restored` | 51 | 1 |
| `swing_reentry_counterfactual_after_loss` | 25 | 4 |
| `swing_same_symbol_loss_reentry_blocked` | 4 | 3 |
| `swing_same_symbol_loss_reentry_cooldown` | 5 | 4 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 41 | 1 |
| `swing_scale_in_micro_context_observed` | 15 | 6 |
| `swing_sim_buy_order_assumed_filled` | 5 | 5 |
| `swing_sim_holding_started` | 5 | 5 |
| `swing_sim_order_bundle_assumed_filled` | 5 | 5 |
| `swing_sim_scale_in_order_assumed_filled` | 15 | 6 |

## OFI/QI Micro Context

- sample_count: `46863`
- stale_missing_unique_record_count: `16`
- stale_missing_ratio: `0.0295`
- stale_missing_reason_counts: `{'micro_missing': 1383, 'micro_not_ready': 226, 'state_insufficient': 226}`
- stale_missing_reason_combination_counts: `{'micro_missing': 1157, 'micro_missing+micro_not_ready+state_insufficient': 226}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 5, 'micro_missing': 11}`
- stale_missing_group_counts: `{'exit': 1168, 'entry': 215}`
- stale_missing_group_unique_record_counts: `{'entry': 5, 'exit': 11}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 42130, 'bullish': 1569, 'bearish': 1718, 'insufficient': 215}`
- scale_in_micro_state_counts: `{'neutral': 45}`
- exit_micro_state_counts: `{'bearish': 58, 'neutral': 1096, 'bullish': 21, 'insufficient': 11}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 1157, 'CONFIRM_EXIT': 10, 'DEBOUNCE_EXIT': 1}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 45}`
- add_triggers: `{'swing_avg_down_ok': 30}`
- price_policies: `{'KEEP_EXISTING_PRICE': 15, 'market': 30}`
- add_ratio_summary: `{'count': 30, 'min': 0.4615, 'max': 1.0, 'avg': 0.5544733333333334, 'mean': 0.5544733333333334, 'p50': 0.5, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 30}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `21`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 7 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 7 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 4 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 19 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 31 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 116 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 6 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 18 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 45632 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 45 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 1168 | `ready` |

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
