# Swing Lifecycle Audit - 2026-05-26

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `22`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `14`
- observation_axis_status: `{'ready': 9, 'hold_sample': 1}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 10, 'avg_unrealized_profit_rate_pct': -0.4114, 'win_rate_pct': 20.0, 'wins': 2, 'losses': 7, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 4, 'avg_profit_rate_pct': -0.0407}, 'blocked_swing_gap': {'count': 2, 'avg_profit_rate_pct': -0.6989}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': -0.6384}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 209378 | 22 |
| `holding` | 801 | 98 |
| `scale_in` | 57 | 13 |
| `exit` | 84 | 18 |
| `other` | 712 | 6 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 33 | 6 |
| `blocked_swing_gap` | 13766 | 5 |
| `blocked_swing_score_vpw` | 187457 | 22 |
| `gatekeeper_fast_reuse_bypass` | 33 | 6 |
| `holding_flow_ofi_smoothing_applied` | 794 | 97 |
| `holding_started` | 7 | 1 |
| `sell_order_sent` | 42 | 9 |
| `swing_probe_discarded` | 8029 | 22 |
| `swing_probe_entry_candidate` | 30 | 13 |
| `swing_probe_exit_signal` | 21 | 9 |
| `swing_probe_holding_started` | 30 | 13 |
| `swing_probe_scale_in_order_assumed_filled` | 19 | 13 |
| `swing_probe_sell_order_assumed_filled` | 21 | 9 |
| `swing_probe_state_empty_overwrite_blocked` | 4 | 1 |
| `swing_probe_state_persisted` | 73 | 1 |
| `swing_probe_state_restored` | 49 | 1 |
| `swing_reentry_counterfactual_after_loss` | 528 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 10 | 5 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 48 | 1 |
| `swing_scale_in_micro_context_observed` | 19 | 13 |
| `swing_sim_scale_in_order_assumed_filled` | 19 | 13 |

## OFI/QI Micro Context

- sample_count: `872`
- stale_missing_unique_record_count: `7`
- stale_missing_ratio: `0.9117`
- stale_missing_reason_counts: `{'micro_missing': 795, 'observer_unhealthy': 1, 'micro_not_ready': 4, 'state_insufficient': 4}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing': 791, 'micro_missing+micro_not_ready+state_insufficient': 3}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing': 6}`
- stale_missing_group_counts: `{'exit': 795}`
- stale_missing_group_unique_record_counts: `{'exit': 7}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 57}`
- exit_micro_state_counts: `{'insufficient': 4, 'neutral': 739, 'bearish': 60, 'bullish': 12}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 773, 'CONFIRM_EXIT': 12, 'DEBOUNCE_EXIT': 9}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 57}`
- add_triggers: `{'swing_avg_down_ok': 38}`
- price_policies: `{'KEEP_EXISTING_PRICE': 19, 'market': 38}`
- add_ratio_summary: `{'count': 38, 'min': 0.3333, 'max': 0.5, 'avg': 0.4543473684210526, 'mean': 0.4543473684210526, 'p50': 0.4972, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 38}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `66`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 22 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 22 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 19 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 19 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 54 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 98 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 13 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 18 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 57 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 794 | `ready` |

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
