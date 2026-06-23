# Swing Lifecycle Audit - 2026-06-23

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `6`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `11`
- observation_axis_status: `{'ready': 10}`
- panic_state: `RECOVERY_WATCH`
- panic_active_sim_probe: `{'active_positions': 7, 'profit_sample': 4, 'avg_unrealized_profit_rate_pct': -1.1379, 'win_rate_pct': 25.0, 'wins': 1, 'losses': 3, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 1, 'avg_profit_rate_pct': None}, 'blocked_swing_score_vpw': {'count': 1, 'avg_profit_rate_pct': None}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}, 'unknown': {'count': 4, 'avg_profit_rate_pct': -1.1379}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 9202 | 6 |
| `holding` | 167 | 39 |
| `scale_in` | 39 | 8 |
| `exit` | 47 | 15 |
| `other` | 2378 | 11 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 87 | 3 |
| `blocked_swing_gap` | 184 | 1 |
| `blocked_swing_score_vpw` | 1996 | 6 |
| `gatekeeper_fast_reuse` | 1 | 1 |
| `gatekeeper_fast_reuse_bypass` | 86 | 3 |
| `gatekeeper_reject_cache_reuse` | 52 | 3 |
| `holding_flow_ofi_smoothing_applied` | 124 | 35 |
| `market_regime_block` | 1921 | 6 |
| `market_regime_prior_observed` | 162 | 6 |
| `sell_order_blocked_market_closed` | 22 | 5 |
| `sell_order_sent` | 1 | 1 |
| `swing_entry_micro_context_observed` | 2052 | 6 |
| `swing_entry_policy_evaluated` | 2083 | 6 |
| `swing_probe_discarded` | 2549 | 6 |
| `swing_probe_entry_candidate` | 13 | 6 |
| `swing_probe_exit_signal` | 12 | 9 |
| `swing_probe_holding_started` | 13 | 6 |
| `swing_probe_scale_in_order_assumed_filled` | 12 | 8 |
| `swing_probe_sell_order_assumed_filled` | 12 | 9 |
| `swing_probe_state_persisted` | 37 | 1 |
| `swing_probe_state_restored` | 67 | 1 |
| `swing_reentry_counterfactual_after_loss` | 94 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 31 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 9 | 8 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 57 | 1 |
| `swing_scale_in_micro_context_observed` | 15 | 8 |
| `swing_sim_buy_order_assumed_filled` | 43 | 4 |
| `swing_sim_holding_started` | 43 | 4 |
| `swing_sim_order_bundle_assumed_filled` | 43 | 4 |
| `swing_sim_scale_in_order_assumed_filled` | 12 | 8 |

## OFI/QI Micro Context

- sample_count: `4427`
- stale_missing_unique_record_count: `8`
- stale_missing_ratio: `0.8581`
- stale_missing_reason_counts: `{'micro_missing': 3799, 'micro_not_ready': 3676, 'state_insufficient': 3676, 'observer_unhealthy': 216}`
- stale_missing_reason_combination_counts: `{'micro_missing': 123, 'micro_missing+micro_not_ready+state_insufficient': 3460, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 216}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 8, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- stale_missing_reason_counts_by_group: `{'exit': {'micro_missing': 129, 'micro_not_ready': 6, 'state_insufficient': 6, 'observer_unhealthy': 1}, 'entry': {'micro_missing': 3664, 'micro_not_ready': 3664, 'state_insufficient': 3664, 'observer_unhealthy': 215}, 'scale_in': {'micro_missing': 6, 'micro_not_ready': 6, 'state_insufficient': 6}}`
- stale_missing_reason_unique_record_counts_by_group: `{'entry': {'micro_missing': 6, 'micro_not_ready': 6, 'state_insufficient': 6, 'observer_unhealthy': 4}, 'scale_in': {'micro_missing': 2, 'micro_not_ready': 2, 'state_insufficient': 2}, 'exit': {'micro_missing': 5, 'micro_not_ready': 5, 'state_insufficient': 5, 'observer_unhealthy': 1}}`
- stale_missing_group_counts: `{'exit': 129, 'entry': 3664, 'scale_in': 6}`
- stale_missing_group_unique_record_counts: `{'entry': 6, 'scale_in': 2, 'exit': 5}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 216, 'observer_unhealthy_with_other_reason': 216, 'observer_unhealthy_only': 0}`
- orderbook_micro_reason_counts_by_group: `{'exit': {'ready': 130, 'insufficient_samples': 6}, 'scale_in': {'ready': 33, 'insufficient_samples': 6}, 'entry': {'ready': 588, 'insufficient_samples': 3515, 'missing_best_qty': 149}}`
- observer_missing_reason_counts_by_group: `{'exit': {'ok': 135, 'missing_trade': 1}, 'scale_in': {'ok': 39}, 'entry': {'ok': 4037, 'missing_quote_and_trade': 148, 'missing_trade': 66, 'missing_quote': 1}}`
- source_quality_status_counts_by_group: `{'exit': {'UNKNOWN': 124, 'ok': 7, 'source_quality_blocker': 5}, 'scale_in': {'ok': 33, 'source_quality_blocker': 6}, 'entry': {'ok': 588, 'source_quality_blocker': 3664}}`
- ws_quote_source_counts_by_group: `{'exit': {'UNKNOWN': 124, 'missing': 12}, 'scale_in': {'last_ws_update_ts': 39}, 'entry': {'missing': 4252}}`
- ws_quote_stale_counts_by_group: `{'exit': {'UNKNOWN': 124, 'not_available_no_quote_age': 12}, 'scale_in': {'False': 30, 'True': 9}, 'entry': {'not_available_no_quote_age': 4252}}`
- entry_micro_state_counts: `{'neutral': 555, 'bearish': 22, 'bullish': 11, 'insufficient': 3664}`
- scale_in_micro_state_counts: `{'neutral': 29, 'bullish': 1, 'insufficient': 6, 'bearish': 3}`
- exit_micro_state_counts: `{'neutral': 120, 'bearish': 8, 'insufficient': 6, 'bullish': 2}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 123, 'CONFIRM_EXIT': 1}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 39}`
- add_triggers: `{'swing_avg_down_ok': 24}`
- price_policies: `{'KEEP_EXISTING_PRICE': 11, 'market': 24, 'ALLOW_EXISTING_PRICE': 1, 'NO_CHANGE': 2, 'WAIT_FOR_PULLBACK': 1}`
- add_ratio_summary: `{'count': 24, 'min': 0.4615, 'max': 1.0, 'avg': 0.5316833333333334, 'mean': 0.5316833333333334, 'p50': 0.49870000000000003, 'p95': 0.9249999999999989}`
- post_add_outcomes: `{'pending_followup': 24}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `18`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 6 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 6 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 3 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 17 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 36 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 39 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 8 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 15 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 4252 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 39 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 124 | `ready` |

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
