# Swing Lifecycle Audit - 2026-05-27

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `19`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `18`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 11, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': 0.2227, 'win_rate_pct': 71.4, 'wins': 5, 'losses': 0, 'flat': 2}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 1, 'avg_profit_rate_pct': None}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.4284}, 'market_regime_prior_observed': {'count': 5, 'avg_profit_rate_pct': 0.0683}, 'unknown': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 118361 | 19 |
| `holding` | 737 | 104 |
| `scale_in` | 99 | 14 |
| `exit` | 97 | 12 |
| `other` | 35475 | 20 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 1091 | 12 |
| `blocked_swing_gap` | 4003 | 3 |
| `blocked_swing_score_vpw` | 33794 | 19 |
| `gatekeeper_fast_reuse` | 126 | 2 |
| `gatekeeper_fast_reuse_bypass` | 966 | 12 |
| `gatekeeper_reject_cache_reuse` | 699 | 5 |
| `holding_flow_ofi_smoothing_applied` | 638 | 90 |
| `holding_started` | 11 | 1 |
| `market_regime_block` | 9661 | 19 |
| `market_regime_prior_observed` | 25224 | 19 |
| `sell_order_sent` | 72 | 7 |
| `swing_entry_micro_context_observed` | 34630 | 18 |
| `swing_entry_policy_evaluated` | 34885 | 19 |
| `swing_probe_discarded` | 7715 | 19 |
| `swing_probe_entry_candidate` | 138 | 16 |
| `swing_probe_exit_signal` | 10 | 3 |
| `swing_probe_holding_started` | 138 | 16 |
| `swing_probe_scale_in_order_assumed_filled` | 25 | 13 |
| `swing_probe_sell_order_assumed_filled` | 10 | 3 |
| `swing_probe_state_empty_overwrite_blocked` | 8 | 1 |
| `swing_probe_state_persisted` | 312 | 1 |
| `swing_probe_state_restored` | 130 | 1 |
| `swing_reentry_counterfactual_after_loss` | 57 | 4 |
| `swing_same_symbol_loss_reentry_blocked` | 16 | 4 |
| `swing_same_symbol_loss_reentry_cooldown` | 6 | 4 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 61 | 1 |
| `swing_scale_in_micro_context_observed` | 37 | 14 |
| `swing_sim_buy_order_assumed_filled` | 88 | 13 |
| `swing_sim_holding_started` | 88 | 13 |
| `swing_sim_order_bundle_assumed_filled` | 88 | 13 |
| `swing_sim_scale_in_order_assumed_filled` | 37 | 14 |
| `swing_sim_sell_order_assumed_filled` | 5 | 2 |

## OFI/QI Micro Context

- sample_count: `70459`
- stale_missing_unique_record_count: `25`
- stale_missing_ratio: `0.0634`
- stale_missing_reason_counts: `{'micro_missing': 4470, 'micro_not_ready': 3835, 'state_insufficient': 3835, 'observer_unhealthy': 39}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 3796, 'micro_missing': 635, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 39}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 20, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 11, 'micro_missing': 5}`
- stale_missing_group_counts: `{'entry': 3825, 'exit': 640, 'scale_in': 5}`
- stale_missing_group_unique_record_counts: `{'entry': 19, 'exit': 6, 'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 39, 'observer_unhealthy_with_other_reason': 39, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 61655, 'bearish': 1804, 'insufficient': 3825, 'bullish': 2423}`
- scale_in_micro_state_counts: `{'neutral': 89, 'insufficient': 5, 'bullish': 3, 'bearish': 2}`
- exit_micro_state_counts: `{'neutral': 596, 'bearish': 40, 'insufficient': 5, 'bullish': 12}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 631, 'DEBOUNCE_EXIT': 5, 'CONFIRM_EXIT': 2}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 99}`
- add_triggers: `{'swing_avg_down_ok': 62}`
- price_policies: `{'KEEP_EXISTING_PRICE': 33, 'market': 62, 'NO_CHANGE': 2, 'ALLOW_EXISTING_PRICE': 1, 'WAIT_FOR_PULLBACK': 1}`
- add_ratio_summary: `{'count': 62, 'min': 0.3333, 'max': 1.0, 'avg': 0.48615161290322584, 'mean': 0.48615161290322584, 'p50': 0.4988, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 62}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `60`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 20 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 20 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 17 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 54 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 94 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 104 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 14 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 12 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 69707 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 99 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 638 | `ready` |

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
