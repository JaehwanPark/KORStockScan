# Swing Lifecycle Audit - 2026-05-20

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `25`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `13`
- observation_axis_status: `{'ready': 9, 'hold_sample': 1}`
- panic_state: `PANIC_SELL`
- panic_active_sim_probe: `{'active_positions': 9, 'profit_sample': 9, 'avg_unrealized_profit_rate_pct': -0.8274, 'win_rate_pct': 11.1, 'wins': 1, 'losses': 7, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 5, 'avg_profit_rate_pct': -0.8429}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': -0.8079}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 378328 | 25 |
| `holding` | 633 | 68 |
| `scale_in` | 27 | 8 |
| `exit` | 35 | 12 |
| `other` | 262 | 12 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 87 | 9 |
| `blocked_swing_gap` | 416 | 1 |
| `blocked_swing_score_vpw` | 368504 | 25 |
| `gatekeeper_fast_reuse_bypass` | 87 | 9 |
| `holding_flow_ofi_smoothing_applied` | 630 | 67 |
| `holding_started` | 3 | 1 |
| `sell_order_sent` | 17 | 4 |
| `swing_probe_discarded` | 9216 | 25 |
| `swing_probe_entry_candidate` | 9 | 7 |
| `swing_probe_exit_signal` | 9 | 8 |
| `swing_probe_holding_started` | 9 | 7 |
| `swing_probe_scale_in_order_assumed_filled` | 9 | 8 |
| `swing_probe_sell_order_assumed_filled` | 9 | 8 |
| `swing_probe_state_empty_overwrite_blocked` | 3 | 1 |
| `swing_probe_state_persisted` | 27 | 1 |
| `swing_probe_state_restored` | 11 | 1 |
| `swing_reentry_counterfactual_after_loss` | 204 | 6 |
| `swing_same_symbol_loss_reentry_cooldown` | 8 | 8 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 9 | 1 |
| `swing_scale_in_micro_context_observed` | 9 | 8 |
| `swing_sim_scale_in_order_assumed_filled` | 9 | 8 |

## OFI/QI Micro Context

- sample_count: `666`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.955`
- stale_missing_reason_counts: `{'micro_missing': 636, 'micro_not_ready': 20, 'state_insufficient': 20, 'observer_unhealthy': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing': 615, 'micro_missing+micro_not_ready+state_insufficient': 20, 'micro_missing+observer_unhealthy': 1}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'exit': 630, 'scale_in': 6}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 18, 'bearish': 3, 'insufficient': 6}`
- exit_micro_state_counts: `{'neutral': 551, 'bearish': 64, 'bullish': 10, 'insufficient': 14}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 619, 'CONFIRM_EXIT': 10, 'DEBOUNCE_EXIT': 1}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 27}`
- add_triggers: `{'swing_avg_down_ok': 18}`
- price_policies: `{'KEEP_EXISTING_PRICE': 6, 'market': 18, 'WAIT_FOR_PULLBACK': 1, 'NO_CHANGE': 2}`
- add_ratio_summary: `{'count': 18, 'min': 0.4667, 'max': 1.0, 'avg': 0.6009777777777778, 'mean': 0.6009777777777778, 'p50': 0.4928, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 18}`
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
| `swing_gatekeeper_reject_cooldown` | 56 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 10 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 16 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 46 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 68 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 8 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 12 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 27 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 630 | `ready` |

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
