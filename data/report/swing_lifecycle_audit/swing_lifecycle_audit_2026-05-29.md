# Swing Lifecycle Audit - 2026-05-29

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `18`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `15`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.3369, 'win_rate_pct': 28.6, 'wins': 2, 'losses': 4, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 2, 'avg_profit_rate_pct': -1.5309}, 'blocked_swing_gap': {'count': 1, 'avg_profit_rate_pct': -0.4094}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.2089}, 'market_regime_prior_observed': {'count': 3, 'avg_profit_rate_pct': -0.5224}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 56824 | 18 |
| `holding` | 665 | 91 |
| `scale_in` | 61 | 12 |
| `exit` | 40 | 15 |
| `other` | 15069 | 19 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 2945 | 10 |
| `blocked_swing_gap` | 3512 | 8 |
| `blocked_swing_score_vpw` | 11877 | 17 |
| `gatekeeper_fast_reuse` | 101 | 5 |
| `gatekeeper_fast_reuse_bypass` | 2846 | 10 |
| `gatekeeper_reject_cache_reuse` | 2603 | 8 |
| `holding_flow_ofi_smoothing_applied` | 621 | 81 |
| `market_regime_prior_observed` | 14822 | 18 |
| `sell_order_sent` | 4 | 4 |
| `swing_entry_micro_context_observed` | 14638 | 12 |
| `swing_entry_policy_evaluated` | 14822 | 18 |
| `swing_probe_discarded` | 3350 | 15 |
| `swing_probe_entry_candidate` | 21 | 12 |
| `swing_probe_exit_signal` | 14 | 9 |
| `swing_probe_holding_started` | 21 | 12 |
| `swing_probe_scale_in_order_assumed_filled` | 11 | 8 |
| `swing_probe_sell_order_assumed_filled` | 14 | 9 |
| `swing_probe_state_persisted` | 60 | 1 |
| `swing_probe_state_restored` | 67 | 1 |
| `swing_reentry_counterfactual_after_loss` | 44 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 12 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 6 | 5 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 58 | 1 |
| `swing_scale_in_micro_context_observed` | 25 | 12 |
| `swing_sim_buy_order_assumed_filled` | 44 | 10 |
| `swing_sim_holding_started` | 44 | 10 |
| `swing_sim_order_bundle_assumed_filled` | 44 | 10 |
| `swing_sim_scale_in_order_assumed_filled` | 25 | 12 |
| `swing_sim_sell_order_assumed_filled` | 8 | 4 |

## OFI/QI Micro Context

- sample_count: `30264`
- stale_missing_unique_record_count: `20`
- stale_missing_ratio: `0.1157`
- stale_missing_reason_counts: `{'micro_missing': 3501, 'micro_not_ready': 2890, 'state_insufficient': 2890, 'observer_unhealthy': 8}`
- stale_missing_reason_combination_counts: `{'micro_missing': 611, 'micro_missing+micro_not_ready+state_insufficient': 2882, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 3, 'micro_missing+micro_not_ready+state_insufficient': 17, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'exit': 621, 'entry': 2880}`
- stale_missing_group_unique_record_counts: `{'exit': 3, 'entry': 17}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'bearish': 843, 'neutral': 25309, 'bullish': 528, 'insufficient': 2880}`
- scale_in_micro_state_counts: `{'neutral': 55, 'bearish': 4, 'bullish': 2}`
- exit_micro_state_counts: `{'neutral': 573, 'bearish': 52, 'bullish': 8, 'insufficient': 10}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 610, 'CONFIRM_EXIT': 11}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 61}`
- add_triggers: `{'swing_avg_down_ok': 36}`
- price_policies: `{'KEEP_EXISTING_PRICE': 22, 'market': 36, 'WAIT_FOR_PULLBACK': 2, 'ALLOW_EXISTING_PRICE': 1}`
- add_ratio_summary: `{'count': 36, 'min': 0.3333, 'max': 1.0, 'avg': 0.5031333333333333, 'mean': 0.5031333333333333, 'p50': 0.5, 'p95': 0.625}`
- post_add_outcomes: `{'pending_followup': 36}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `54`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 18 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 18 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 15 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 42 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 70 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 91 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 12 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 15 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 29560 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 61 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 621 | `ready` |

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
