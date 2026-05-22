# Swing Lifecycle Audit - 2026-05-22

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `15`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `20`
- observation_axis_status: `{'ready': 9, 'hold_sample': 1}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 30, 'profit_sample': 30, 'avg_unrealized_profit_rate_pct': 0.4934, 'win_rate_pct': 76.7, 'wins': 23, 'losses': 5, 'flat': 2}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 1, 'avg_profit_rate_pct': 2.0}, 'blocked_swing_gap': {'count': 2, 'avg_profit_rate_pct': 0.6694}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 1.5377}, 'unknown': {'count': 13, 'avg_profit_rate_pct': 0.5795}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 143193 | 15 |
| `holding` | 523 | 75 |
| `scale_in` | 30 | 8 |
| `exit` | 66 | 16 |
| `other` | 116 | 2 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 113 | 11 |
| `blocked_swing_gap` | 58064 | 9 |
| `blocked_swing_score_vpw` | 80953 | 9 |
| `gatekeeper_fast_reuse_bypass` | 113 | 11 |
| `holding_flow_ofi_smoothing_applied` | 517 | 74 |
| `holding_started` | 6 | 1 |
| `sell_order_sent` | 30 | 2 |
| `swing_probe_discarded` | 3914 | 15 |
| `swing_probe_entry_candidate` | 18 | 12 |
| `swing_probe_exit_signal` | 18 | 14 |
| `swing_probe_holding_started` | 18 | 12 |
| `swing_probe_scale_in_order_assumed_filled` | 10 | 8 |
| `swing_probe_sell_order_assumed_filled` | 18 | 14 |
| `swing_probe_state_empty_overwrite_blocked` | 6 | 1 |
| `swing_probe_state_persisted` | 46 | 1 |
| `swing_probe_state_restored` | 3 | 1 |
| `swing_reentry_counterfactual_after_loss` | 59 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 1 | 1 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 1 | 1 |
| `swing_scale_in_micro_context_observed` | 10 | 8 |
| `swing_sim_scale_in_order_assumed_filled` | 10 | 8 |

## OFI/QI Micro Context

- sample_count: `565`
- stale_missing_unique_record_count: `0`
- stale_missing_ratio: `0.915`
- stale_missing_reason_counts: `{'micro_missing': 517, 'micro_not_ready': 1, 'state_insufficient': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing': 516, 'micro_missing+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_combination_unique_record_counts: `{}`
- stale_missing_group_counts: `{'exit': 517}`
- stale_missing_group_unique_record_counts: `{}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 27, 'bullish': 3}`
- exit_micro_state_counts: `{'neutral': 500, 'bullish': 9, 'bearish': 25, 'insufficient': 1}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 510, 'CONFIRM_EXIT': 7}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 30}`
- add_triggers: `{'swing_avg_down_ok': 20}`
- price_policies: `{'KEEP_EXISTING_PRICE': 9, 'market': 20, 'ALLOW_EXISTING_PRICE': 1}`
- add_ratio_summary: `{'count': 20, 'min': 0.4667, 'max': 0.5, 'avg': 0.49589999999999995, 'mean': 0.49589999999999995, 'p50': 0.5, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 20}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `45`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 15 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 15 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 12 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 23 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 50 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 75 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 8 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 16 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 30 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 517 | `ready` |

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
