# Swing Lifecycle Audit - 2026-06-04

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `14`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `11`
- observation_axis_status: `{'ready': 9, 'instrumentation_gap': 1}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.196, 'win_rate_pct': 42.9, 'wins': 3, 'losses': 4, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 3, 'avg_profit_rate_pct': -1.1084}, 'blocked_swing_gap': {'count': 1, 'avg_profit_rate_pct': -0.7707}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.5796}, 'market_regime_prior_observed': {'count': 2, 'avg_profit_rate_pct': -0.1233}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 16871 | 14 |
| `holding` | 69 | 29 |
| `scale_in` | 12 | 5 |
| `exit` | 4 | 3 |
| `other` | 4547 | 15 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 829 | 3 |
| `blocked_swing_gap` | 923 | 5 |
| `blocked_swing_score_vpw` | 3678 | 12 |
| `gatekeeper_fast_reuse` | 12 | 1 |
| `gatekeeper_fast_reuse_bypass` | 818 | 3 |
| `gatekeeper_reject_cache_reuse` | 768 | 3 |
| `holding_flow_ofi_smoothing_applied` | 52 | 18 |
| `market_regime_prior_observed` | 4507 | 14 |
| `sell_order_sent` | 1 | 1 |
| `swing_entry_micro_context_observed` | 4484 | 11 |
| `swing_entry_policy_evaluated` | 4507 | 14 |
| `swing_probe_discarded` | 818 | 14 |
| `swing_probe_state_persisted` | 15 | 1 |
| `swing_probe_state_restored` | 9 | 1 |
| `swing_reentry_counterfactual_after_loss` | 8 | 1 |
| `swing_same_symbol_loss_reentry_blocked` | 2 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 1 | 1 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 5 | 1 |
| `swing_scale_in_micro_context_observed` | 6 | 5 |
| `swing_sim_buy_order_assumed_filled` | 17 | 11 |
| `swing_sim_holding_started` | 17 | 11 |
| `swing_sim_order_bundle_assumed_filled` | 17 | 11 |
| `swing_sim_scale_in_order_assumed_filled` | 6 | 5 |
| `swing_sim_sell_order_assumed_filled` | 3 | 2 |

## OFI/QI Micro Context

- sample_count: `9094`
- stale_missing_unique_record_count: `14`
- stale_missing_ratio: `0.0379`
- stale_missing_reason_counts: `{'micro_missing': 345, 'observer_unhealthy': 8, 'micro_not_ready': 294, 'state_insufficient': 294}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8, 'micro_missing+micro_not_ready+state_insufficient': 286, 'micro_missing': 51}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing': 1}`
- stale_missing_group_counts: `{'entry': 293, 'exit': 52}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'insufficient': 293, 'neutral': 8241, 'bearish': 287, 'bullish': 206}`
- scale_in_micro_state_counts: `{'neutral': 12}`
- exit_micro_state_counts: `{'neutral': 48, 'bullish': 3, 'bearish': 3, 'insufficient': 1}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 52}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 12}`
- add_triggers: `{'swing_avg_down_ok': 6}`
- price_policies: `{'KEEP_EXISTING_PRICE': 6, 'market': 6}`
- add_ratio_summary: `{'count': 6, 'min': 0.5, 'max': 1.0, 'avg': 0.5833333333333334, 'mean': 0.5833333333333334, 'p50': 0.5, 'p95': 0.875}`
- post_add_outcomes: `{'pending_followup': 6}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `42`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 14 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 14 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 11 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 25 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 42 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 29 | `instrumentation_gap` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 5 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 3 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 9027 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 12 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 52 | `ready` |

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
