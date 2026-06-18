# Swing Lifecycle Audit - 2026-06-17

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
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -1.6317, 'win_rate_pct': 0.0, 'wins': 0, 'losses': 7, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 4, 'avg_profit_rate_pct': -1.5592}, 'blocked_swing_gap': {'count': 1, 'avg_profit_rate_pct': -1.3839}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': -1.7867}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 155469 | 16 |
| `holding` | 400 | 125 |
| `scale_in` | 76 | 7 |
| `exit` | 9 | 6 |
| `other` | 44809 | 19 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 8769 | 10 |
| `blocked_swing_gap` | 2104 | 4 |
| `blocked_swing_score_vpw` | 35987 | 16 |
| `gatekeeper_fast_reuse` | 738 | 6 |
| `gatekeeper_fast_reuse_bypass` | 8031 | 10 |
| `gatekeeper_reject_cache_reuse` | 7402 | 10 |
| `holding_flow_ofi_smoothing_applied` | 369 | 109 |
| `market_regime_pass` | 44756 | 16 |
| `swing_entry_micro_context_observed` | 44754 | 16 |
| `swing_entry_policy_evaluated` | 44756 | 16 |
| `swing_probe_discarded` | 2860 | 12 |
| `swing_probe_entry_candidate` | 3 | 3 |
| `swing_probe_exit_signal` | 3 | 3 |
| `swing_probe_holding_started` | 3 | 3 |
| `swing_probe_scale_in_order_assumed_filled` | 3 | 3 |
| `swing_probe_sell_order_assumed_filled` | 3 | 3 |
| `swing_probe_state_persisted` | 12 | 1 |
| `swing_probe_state_restored` | 16 | 1 |
| `swing_reentry_counterfactual_after_loss` | 6 | 1 |
| `swing_same_symbol_loss_reentry_blocked` | 2 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 3 | 3 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 14 | 1 |
| `swing_scale_in_micro_context_observed` | 62 | 7 |
| `swing_sim_buy_order_assumed_filled` | 31 | 16 |
| `swing_sim_holding_started` | 31 | 16 |
| `swing_sim_order_bundle_assumed_filled` | 31 | 16 |
| `swing_sim_scale_in_order_assumed_filled` | 11 | 7 |
| `swing_sim_sell_order_assumed_filled` | 3 | 3 |

## OFI/QI Micro Context

- sample_count: `90023`
- stale_missing_unique_record_count: `13`
- stale_missing_ratio: `0.1407`
- stale_missing_reason_counts: `{'micro_missing': 12670, 'micro_not_ready': 12312, 'state_insufficient': 12312, 'observer_unhealthy': 4}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 12308, 'micro_missing': 358, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_counts_by_group: `{'entry': {'micro_missing': 12294, 'micro_not_ready': 12294, 'state_insufficient': 12294, 'observer_unhealthy': 4}, 'exit': {'micro_missing': 369, 'micro_not_ready': 11, 'state_insufficient': 11}, 'scale_in': {'micro_missing': 7, 'micro_not_ready': 7, 'state_insufficient': 7}}`
- stale_missing_reason_unique_record_counts_by_group: `{'entry': {'micro_missing': 13, 'micro_not_ready': 13, 'state_insufficient': 13, 'observer_unhealthy': 1}, 'scale_in': {'micro_missing': 1, 'micro_not_ready': 1, 'state_insufficient': 1}}`
- stale_missing_group_counts: `{'entry': 12294, 'exit': 369, 'scale_in': 7}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}`
- orderbook_micro_reason_counts_by_group: `{'entry': {'ready': 77278, 'insufficient_samples': 12290, 'missing_best_qty': 4}, 'exit': {'ready': 364, 'insufficient_samples': 11}, 'scale_in': {'ready': 69, 'insufficient_samples': 7}}`
- observer_missing_reason_counts_by_group: `{'entry': {'ok': 89568, 'missing_quote_and_trade': 4}, 'exit': {'ok': 375}, 'scale_in': {'ok': 76}}`
- source_quality_status_counts_by_group: `{'entry': {'ok': 77278, 'source_quality_blocker': 12294}, 'exit': {'UNKNOWN': 369, 'ok': 6}, 'scale_in': {'ok': 69, 'source_quality_blocker': 7}}`
- ws_quote_source_counts_by_group: `{'entry': {'missing': 89572}, 'exit': {'UNKNOWN': 369, 'missing': 6}, 'scale_in': {'last_ws_update_ts': 76}}`
- ws_quote_stale_counts_by_group: `{'entry': {'not_available_no_quote_age': 89572}, 'exit': {'UNKNOWN': 369, 'not_available_no_quote_age': 6}, 'scale_in': {'True': 30, 'False': 46}}`
- entry_micro_state_counts: `{'neutral': 72604, 'bullish': 2645, 'insufficient': 12294, 'bearish': 2029}`
- scale_in_micro_state_counts: `{'neutral': 63, 'bearish': 5, 'insufficient': 7, 'bullish': 1}`
- exit_micro_state_counts: `{'neutral': 342, 'bearish': 13, 'insufficient': 11, 'bullish': 9}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 368, 'CONFIRM_EXIT': 1}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 76}`
- add_triggers: `{'swing_avg_down_ok': 14}`
- price_policies: `{'KEEP_EXISTING_PRICE': 49, 'market': 14, 'WAIT_FOR_PULLBACK': 5, 'NO_CHANGE': 7, 'ALLOW_EXISTING_PRICE': 1}`
- add_ratio_summary: `{'count': 14, 'min': 0.4, 'max': 0.5, 'avg': 0.47717142857142864, 'mean': 0.47717142857142864, 'p50': 0.4959, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 14}`
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
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 61 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 58 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 125 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 7 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 6 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 89572 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 76 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 369 | `ready` |

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
