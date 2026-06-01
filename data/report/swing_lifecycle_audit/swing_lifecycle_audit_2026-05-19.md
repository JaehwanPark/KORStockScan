# Swing Lifecycle Audit - 2026-05-19

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
- simulated_order_unique_records: `20`
- observation_axis_status: `{'ready': 9, 'hold_sample': 1}`
- panic_state: `RECOVERY_WATCH`
- panic_active_sim_probe: `{'active_positions': 9, 'profit_sample': 9, 'avg_unrealized_profit_rate_pct': -0.2903, 'win_rate_pct': 33.3, 'wins': 3, 'losses': 6, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 4, 'avg_profit_rate_pct': -0.5127}, 'blocked_swing_gap': {'count': 1, 'avg_profit_rate_pct': -0.6631}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.0253}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 302059 | 20 |
| `holding` | 463 | 50 |
| `scale_in` | 33 | 11 |
| `exit` | 30 | 16 |
| `other` | 447 | 11 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 40 | 8 |
| `blocked_swing_gap` | 14396 | 2 |
| `blocked_swing_score_vpw` | 279693 | 20 |
| `gatekeeper_fast_reuse_bypass` | 40 | 8 |
| `holding_flow_ofi_smoothing_applied` | 463 | 50 |
| `sell_order_blocked_market_closed` | 2 | 2 |
| `swing_probe_discarded` | 7864 | 20 |
| `swing_probe_entry_candidate` | 13 | 11 |
| `swing_probe_exit_signal` | 14 | 14 |
| `swing_probe_holding_started` | 13 | 11 |
| `swing_probe_scale_in_order_assumed_filled` | 11 | 11 |
| `swing_probe_sell_order_assumed_filled` | 14 | 14 |
| `swing_probe_state_persisted` | 38 | 1 |
| `swing_probe_state_restored` | 7 | 1 |
| `swing_reentry_counterfactual_after_loss` | 388 | 6 |
| `swing_same_symbol_loss_reentry_cooldown` | 9 | 9 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 5 | 1 |
| `swing_scale_in_micro_context_observed` | 11 | 11 |
| `swing_sim_scale_in_order_assumed_filled` | 11 | 11 |

## OFI/QI Micro Context

- sample_count: `510`
- stale_missing_unique_record_count: `5`
- stale_missing_ratio: `0.9216`
- stale_missing_reason_counts: `{'micro_missing': 470, 'micro_not_ready': 24, 'state_insufficient': 24, 'observer_unhealthy': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing': 446, 'micro_missing+micro_not_ready+state_insufficient': 23, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 4, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'exit': 467, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'exit': 4}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 27, 'bullish': 3, 'insufficient': 3}`
- exit_micro_state_counts: `{'neutral': 406, 'bearish': 45, 'insufficient': 21, 'bullish': 5}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 456, 'CONFIRM_EXIT': 7}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 33}`
- add_triggers: `{'swing_avg_down_ok': 22}`
- price_policies: `{'KEEP_EXISTING_PRICE': 9, 'market': 22, 'ALLOW_EXISTING_PRICE': 1, 'NO_CHANGE': 1}`
- add_ratio_summary: `{'count': 22, 'min': 0.4, 'max': 1.0, 'avg': 0.5211636363636364, 'mean': 0.5211636363636364, 'p50': 0.5, 'p95': 0.9749999999999996}`
- post_add_outcomes: `{'pending_followup': 22}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `51`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 51 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 19 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 53 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 50 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 11 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 16 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 33 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 463 | `ready` |

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
