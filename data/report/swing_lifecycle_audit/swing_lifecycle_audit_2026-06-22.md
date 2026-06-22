# Swing Lifecycle Audit - 2026-06-22

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `26`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `13`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.7319, 'win_rate_pct': 14.3, 'wins': 1, 'losses': 6, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 3, 'avg_profit_rate_pct': -0.7071}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': -0.1453}, 'market_regime_block': {'count': 1, 'avg_profit_rate_pct': -2.0592}, 'market_regime_prior_observed': {'count': 2, 'avg_profit_rate_pct': -1.2136}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 4286 | 8 |
| `holding` | 169 | 56 |
| `scale_in` | 24 | 7 |
| `exit` | 18 | 8 |
| `other` | 997 | 13 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 201 | 4 |
| `blocked_swing_gap` | 69 | 1 |
| `blocked_swing_score_vpw` | 612 | 6 |
| `gatekeeper_fast_reuse_bypass` | 201 | 4 |
| `gatekeeper_reject_cache_reuse` | 50 | 3 |
| `holding_flow_ofi_smoothing_applied` | 103 | 52 |
| `market_regime_prior_observed` | 813 | 8 |
| `swing_entry_micro_context_observed` | 779 | 7 |
| `swing_entry_policy_evaluated` | 813 | 8 |
| `swing_probe_discarded` | 1413 | 8 |
| `swing_probe_entry_candidate` | 8 | 7 |
| `swing_probe_exit_signal` | 8 | 7 |
| `swing_probe_holding_started` | 8 | 7 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 7 |
| `swing_probe_sell_order_assumed_filled` | 8 | 7 |
| `swing_probe_state_persisted` | 26 | 1 |
| `swing_probe_state_restored` | 51 | 1 |
| `swing_reentry_counterfactual_after_loss` | 45 | 2 |
| `swing_same_symbol_loss_reentry_blocked` | 12 | 2 |
| `swing_same_symbol_loss_reentry_cooldown` | 6 | 5 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 44 | 1 |
| `swing_scale_in_micro_context_observed` | 8 | 7 |
| `swing_sim_buy_order_assumed_filled` | 66 | 4 |
| `swing_sim_holding_started` | 66 | 4 |
| `swing_sim_order_bundle_assumed_filled` | 66 | 4 |
| `swing_sim_scale_in_order_assumed_filled` | 8 | 7 |
| `swing_sim_sell_order_assumed_filled` | 2 | 2 |

## OFI/QI Micro Context

- sample_count: `1873`
- stale_missing_unique_record_count: `7`
- stale_missing_ratio: `0.0769`
- stale_missing_reason_counts: `{'micro_missing': 144, 'micro_not_ready': 42, 'state_insufficient': 42}`
- stale_missing_reason_combination_counts: `{'micro_missing': 102, 'micro_missing+micro_not_ready+state_insufficient': 42}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 7}`
- stale_missing_reason_counts_by_group: `{'exit': {'micro_missing': 104, 'micro_not_ready': 2, 'state_insufficient': 2}, 'entry': {'micro_missing': 40, 'micro_not_ready': 40, 'state_insufficient': 40}}`
- stale_missing_reason_unique_record_counts_by_group: `{'entry': {'micro_missing': 7, 'micro_not_ready': 7, 'state_insufficient': 7}, 'exit': {'micro_missing': 1, 'micro_not_ready': 1, 'state_insufficient': 1}}`
- stale_missing_group_counts: `{'exit': 104, 'entry': 40}`
- stale_missing_group_unique_record_counts: `{'entry': 7, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- orderbook_micro_reason_counts_by_group: `{'scale_in': {'ready': 24}, 'entry': {'ready': 1696, 'insufficient_samples': 40}, 'exit': {'ready': 111, 'insufficient_samples': 2}}`
- observer_missing_reason_counts_by_group: `{'scale_in': {'ok': 24}, 'entry': {'ok': 1736}, 'exit': {'ok': 113}}`
- source_quality_status_counts_by_group: `{'scale_in': {'ok': 24}, 'entry': {'ok': 1696, 'source_quality_blocker': 40}, 'exit': {'UNKNOWN': 103, 'ok': 9, 'source_quality_blocker': 1}}`
- ws_quote_source_counts_by_group: `{'scale_in': {'last_ws_update_ts': 24}, 'entry': {'missing': 1736}, 'exit': {'UNKNOWN': 103, 'missing': 10}}`
- ws_quote_stale_counts_by_group: `{'scale_in': {'False': 12, 'True': 12}, 'entry': {'not_available_no_quote_age': 1736}, 'exit': {'UNKNOWN': 103, 'not_available_no_quote_age': 10}}`
- entry_micro_state_counts: `{'neutral': 1576, 'bullish': 80, 'bearish': 40, 'insufficient': 40}`
- scale_in_micro_state_counts: `{'neutral': 24}`
- exit_micro_state_counts: `{'neutral': 106, 'bearish': 3, 'bullish': 2, 'insufficient': 2}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 103}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 24}`
- add_triggers: `{'swing_avg_down_ok': 16}`
- price_policies: `{'KEEP_EXISTING_PRICE': 8, 'market': 16}`
- add_ratio_summary: `{'count': 16, 'min': 0.4857, 'max': 0.5, 'avg': 0.4982125, 'mean': 0.4982125, 'p50': 0.5, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 16}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `closed`
- rows: `78`
- closed_count: `9`
- winner_count: `6`
- loser_count: `3`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 32 | 9 | 6 | 3 | 0.021033 |
| `swing_market_regime_sensitivity` | 23 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 23 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 19 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 35 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 56 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 7 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 8 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 1736 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 24 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 103 | `ready` |

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
