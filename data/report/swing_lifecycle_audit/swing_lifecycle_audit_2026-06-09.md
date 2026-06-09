# Swing Lifecycle Audit - 2026-06-09

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `2`
- csv_rows: `2`
- db_rows: `9`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `16`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': 0.3057, 'win_rate_pct': 57.1, 'wins': 4, 'losses': 3, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 1, 'avg_profit_rate_pct': None}, 'blocked_swing_gap': {'count': 4, 'avg_profit_rate_pct': 0.4289}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.1414}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 71326 | 9 |
| `holding` | 670 | 111 |
| `scale_in` | 97 | 9 |
| `exit` | 38 | 15 |
| `other` | 13254 | 11 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 8377 | 8 |
| `blocked_swing_gap` | 11055 | 7 |
| `blocked_swing_score_vpw` | 4720 | 7 |
| `gatekeeper_fast_reuse` | 321 | 5 |
| `gatekeeper_fast_reuse_bypass` | 8057 | 8 |
| `gatekeeper_reject_cache_reuse` | 7359 | 7 |
| `holding_flow_ofi_smoothing_applied` | 657 | 104 |
| `market_regime_prior_observed` | 13097 | 9 |
| `sell_order_sent` | 2 | 2 |
| `swing_entry_micro_context_observed` | 13049 | 7 |
| `swing_entry_policy_evaluated` | 13097 | 9 |
| `swing_probe_discarded` | 5229 | 8 |
| `swing_probe_entry_candidate` | 18 | 8 |
| `swing_probe_exit_signal` | 18 | 13 |
| `swing_probe_holding_started` | 18 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 12 | 7 |
| `swing_probe_sell_order_assumed_filled` | 18 | 13 |
| `swing_probe_state_persisted` | 48 | 1 |
| `swing_probe_state_restored` | 52 | 1 |
| `swing_reentry_counterfactual_after_loss` | 15 | 2 |
| `swing_same_symbol_loss_reentry_blocked` | 1 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 3 | 3 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 38 | 1 |
| `swing_scale_in_micro_context_observed` | 70 | 9 |
| `swing_sim_buy_order_assumed_filled` | 13 | 7 |
| `swing_sim_holding_started` | 13 | 7 |
| `swing_sim_order_bundle_assumed_filled` | 13 | 7 |
| `swing_sim_scale_in_order_assumed_filled` | 15 | 8 |

## OFI/QI Micro Context

- sample_count: `26948`
- stale_missing_unique_record_count: `6`
- stale_missing_ratio: `0.4687`
- stale_missing_reason_counts: `{'micro_missing': 12630, 'micro_not_ready': 11983, 'state_insufficient': 11983}`
- stale_missing_reason_combination_counts: `{'micro_missing': 647, 'micro_missing+micro_not_ready+state_insufficient': 11983}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 4, 'micro_missing': 2}`
- stale_missing_group_counts: `{'exit': 659, 'entry': 11959, 'scale_in': 12}`
- stale_missing_group_unique_record_counts: `{'entry': 4, 'scale_in': 1, 'exit': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 13236, 'bearish': 666, 'bullish': 315, 'insufficient': 11959}`
- scale_in_micro_state_counts: `{'neutral': 80, 'insufficient': 12, 'bearish': 4, 'bullish': 1}`
- exit_micro_state_counts: `{'neutral': 623, 'bullish': 11, 'bearish': 29, 'insufficient': 12}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 648, 'CONFIRM_EXIT': 1, 'DEBOUNCE_EXIT': 8}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 97}`
- add_triggers: `{'swing_avg_down_ok': 27}`
- price_policies: `{'KEEP_EXISTING_PRICE': 61, 'market': 27, 'NO_CHANGE': 4, 'WAIT_FOR_PULLBACK': 4, 'ALLOW_EXISTING_PRICE': 1}`
- add_ratio_summary: `{'count': 27, 'min': 0.4444, 'max': 1.0, 'avg': 0.5306518518518518, 'mean': 0.5306518518518518, 'p50': 0.4995, 'p95': 0.8499999999999996}`
- post_add_outcomes: `{'pending_followup': 27}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `27`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 9 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 9 | 0 | 0 | 0 | None |
| `swing_model_floor` | 2 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 7 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 2 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 2 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 30 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 47 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 111 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 9 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 15 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 26176 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 97 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 657 | `ready` |

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
