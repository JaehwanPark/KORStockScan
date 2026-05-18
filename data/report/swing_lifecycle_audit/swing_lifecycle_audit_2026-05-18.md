# Swing Lifecycle Audit - 2026-05-18

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `42`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `31`
- observation_axis_status: `{'ready': 9, 'hold_sample': 1}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 11, 'profit_sample': 10, 'avg_unrealized_profit_rate_pct': -0.5635, 'win_rate_pct': 40.0, 'wins': 4, 'losses': 6, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 2, 'avg_profit_rate_pct': -0.4138}, 'blocked_swing_gap': {'count': 4, 'avg_profit_rate_pct': -0.3808}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': -0.821}, 'unknown': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 662582 | 42 |
| `holding` | 62 | 2 |
| `scale_in` | 58 | 17 |
| `exit` | 76 | 28 |
| `other` | 576 | 15 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 140 | 20 |
| `blocked_swing_gap` | 96491 | 8 |
| `blocked_swing_score_vpw` | 550978 | 39 |
| `gatekeeper_fast_reuse_bypass` | 140 | 20 |
| `holding_flow_ofi_smoothing_applied` | 62 | 2 |
| `swing_probe_discarded` | 14757 | 42 |
| `swing_probe_entry_candidate` | 38 | 21 |
| `swing_probe_exit_signal` | 38 | 28 |
| `swing_probe_holding_started` | 38 | 21 |
| `swing_probe_scale_in_order_assumed_filled` | 19 | 16 |
| `swing_probe_sell_order_assumed_filled` | 38 | 28 |
| `swing_probe_state_persisted` | 95 | 1 |
| `swing_probe_state_restored` | 8 | 1 |
| `swing_reentry_counterfactual_after_loss` | 453 | 10 |
| `swing_same_symbol_loss_reentry_cooldown` | 13 | 13 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 7 | 1 |
| `swing_scale_in_micro_context_observed` | 20 | 17 |
| `swing_sim_scale_in_order_assumed_filled` | 19 | 16 |

## OFI/QI Micro Context

- sample_count: `158`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.4304`
- stale_missing_reason_counts: `{'micro_missing': 68, 'observer_unhealthy': 6, 'micro_not_ready': 6, 'state_insufficient': 6}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6, 'micro_missing': 62}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'scale_in': 6, 'exit': 62}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'insufficient': 6, 'neutral': 52}`
- exit_micro_state_counts: `{'neutral': 90, 'bearish': 8, 'bullish': 2}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 62}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 58}`
- add_triggers: `{'swing_avg_down_ok': 38}`
- price_policies: `{'NO_CHANGE': 2, 'market': 38, 'KEEP_EXISTING_PRICE': 18}`
- add_ratio_summary: `{'count': 38, 'min': 0.3333, 'max': 1.0, 'avg': 0.502821052631579, 'mean': 0.502821052631579, 'p50': 0.5, 'p95': 0.5749999999999993}`
- post_add_outcomes: `{'pending_followup': 38}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `126`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 42 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 42 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 39 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 41 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 99 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 2 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 17 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 28 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 58 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 62 | `ready` |

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
