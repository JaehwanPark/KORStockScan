# Swing Lifecycle Audit - 2026-06-19

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `20`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `26`
- observation_axis_status: `{'ready': 10}`
- panic_state: `RECOVERY_WATCH`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': 0.2852, 'win_rate_pct': 42.9, 'wins': 3, 'losses': 3, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 2, 'avg_profit_rate_pct': -0.0377}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.0661}, 'market_regime_block': {'count': 2, 'avg_profit_rate_pct': 1.408}, 'market_regime_prior_observed': {'count': 2, 'avg_profit_rate_pct': -0.9798}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 4994 | 20 |
| `holding` | 201 | 60 |
| `scale_in` | 61 | 16 |
| `exit` | 29 | 12 |
| `other` | 1291 | 27 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 332 | 14 |
| `blocked_swing_gap` | 130 | 6 |
| `blocked_swing_score_vpw` | 682 | 19 |
| `gatekeeper_fast_reuse_bypass` | 335 | 14 |
| `gatekeeper_reject_cache_reuse` | 26 | 10 |
| `holding_flow_ofi_smoothing_applied` | 68 | 40 |
| `market_regime_block` | 104 | 19 |
| `market_regime_prior_observed` | 910 | 20 |
| `sell_order_sent` | 1 | 1 |
| `swing_entry_micro_context_observed` | 987 | 20 |
| `swing_entry_policy_evaluated` | 1014 | 20 |
| `swing_probe_discarded` | 1194 | 16 |
| `swing_probe_entry_candidate` | 14 | 9 |
| `swing_probe_exit_signal` | 14 | 11 |
| `swing_probe_holding_started` | 14 | 9 |
| `swing_probe_scale_in_order_assumed_filled` | 12 | 9 |
| `swing_probe_sell_order_assumed_filled` | 14 | 11 |
| `swing_probe_state_persisted` | 40 | 1 |
| `swing_probe_state_restored` | 57 | 1 |
| `swing_reentry_counterfactual_after_loss` | 84 | 7 |
| `swing_same_symbol_loss_reentry_blocked` | 28 | 7 |
| `swing_same_symbol_loss_reentry_cooldown` | 13 | 11 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 55 | 1 |
| `swing_scale_in_micro_context_observed` | 27 | 16 |
| `swing_sim_buy_order_assumed_filled` | 133 | 20 |
| `swing_sim_holding_started` | 133 | 20 |
| `swing_sim_order_bundle_assumed_filled` | 133 | 20 |
| `swing_sim_scale_in_order_assumed_filled` | 22 | 16 |

## OFI/QI Micro Context

- sample_count: `2438`
- stale_missing_unique_record_count: `21`
- stale_missing_ratio: `0.0689`
- stale_missing_reason_counts: `{'micro_missing': 168, 'micro_not_ready': 100, 'state_insufficient': 100}`
- stale_missing_reason_combination_counts: `{'micro_missing': 68, 'micro_missing+micro_not_ready+state_insufficient': 100}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 1, 'micro_missing+micro_not_ready+state_insufficient': 20}`
- stale_missing_reason_counts_by_group: `{'exit': {'micro_missing': 68}, 'entry': {'micro_missing': 100, 'micro_not_ready': 100, 'state_insufficient': 100}}`
- stale_missing_reason_unique_record_counts_by_group: `{'exit': {'micro_missing': 1}, 'entry': {'micro_missing': 20, 'micro_not_ready': 20, 'state_insufficient': 20}}`
- stale_missing_group_counts: `{'exit': 68, 'entry': 100}`
- stale_missing_group_unique_record_counts: `{'exit': 1, 'entry': 20}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- orderbook_micro_reason_counts_by_group: `{'exit': {'ready': 82}, 'scale_in': {'ready': 61}, 'entry': {'ready': 2195, 'insufficient_samples': 100}}`
- observer_missing_reason_counts_by_group: `{'exit': {'ok': 82}, 'scale_in': {'ok': 61}, 'entry': {'ok': 2295}}`
- source_quality_status_counts_by_group: `{'exit': {'UNKNOWN': 68, 'ok': 14}, 'scale_in': {'ok': 61}, 'entry': {'ok': 2195, 'source_quality_blocker': 100}}`
- ws_quote_source_counts_by_group: `{'exit': {'UNKNOWN': 68, 'missing': 14}, 'scale_in': {'last_ws_update_ts': 61}, 'entry': {'missing': 2295}}`
- ws_quote_stale_counts_by_group: `{'exit': {'UNKNOWN': 68, 'not_available_no_quote_age': 14}, 'scale_in': {'False': 49, 'True': 12}, 'entry': {'not_available_no_quote_age': 2295}}`
- entry_micro_state_counts: `{'neutral': 2073, 'bearish': 78, 'bullish': 44, 'insufficient': 100}`
- scale_in_micro_state_counts: `{'neutral': 61}`
- exit_micro_state_counts: `{'neutral': 73, 'bullish': 4, 'bearish': 5}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 68}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 61}`
- add_triggers: `{'swing_avg_down_ok': 34}`
- price_policies: `{'KEEP_EXISTING_PRICE': 27, 'market': 34}`
- add_ratio_summary: `{'count': 34, 'min': 0.018, 'max': 1.0, 'avg': 0.4606176470588235, 'mean': 0.4606176470588235, 'p50': 0.5, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 34}`
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
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 63 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 99 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 60 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 16 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 12 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 2295 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 61 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 68 | `ready` |

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
