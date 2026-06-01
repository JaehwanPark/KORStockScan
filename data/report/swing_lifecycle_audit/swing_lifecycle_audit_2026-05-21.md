# Swing Lifecycle Audit - 2026-05-21

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `24`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `13`
- observation_axis_status: `{'ready': 9, 'hold_sample': 1}`
- panic_state: `PANIC_SELL`
- panic_active_sim_probe: `{'active_positions': 11, 'profit_sample': 11, 'avg_unrealized_profit_rate_pct': 0.0875, 'win_rate_pct': 54.5, 'wins': 6, 'losses': 5, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 3, 'avg_profit_rate_pct': 0.0271}, 'blocked_swing_gap': {'count': 3, 'avg_profit_rate_pct': 0.0007}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': 0.0182}, 'unknown': {'count': 1, 'avg_profit_rate_pct': 0.8065}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 262584 | 24 |
| `holding` | 745 | 86 |
| `scale_in` | 27 | 8 |
| `exit` | 70 | 13 |
| `other` | 76 | 2 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 143 | 19 |
| `blocked_swing_gap` | 119651 | 17 |
| `blocked_swing_score_vpw` | 134755 | 18 |
| `gatekeeper_fast_reuse_bypass` | 143 | 19 |
| `holding_flow_ofi_smoothing_applied` | 732 | 85 |
| `holding_started` | 13 | 1 |
| `sell_order_blocked_market_closed` | 10 | 2 |
| `sell_order_sent` | 42 | 3 |
| `swing_probe_discarded` | 7872 | 24 |
| `swing_probe_entry_candidate` | 10 | 8 |
| `swing_probe_exit_signal` | 9 | 9 |
| `swing_probe_holding_started` | 10 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 9 | 8 |
| `swing_probe_sell_order_assumed_filled` | 9 | 9 |
| `swing_probe_state_empty_overwrite_blocked` | 10 | 1 |
| `swing_probe_state_persisted` | 31 | 1 |
| `swing_probe_state_restored` | 18 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 1 | 1 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 16 | 1 |
| `swing_scale_in_micro_context_observed` | 9 | 8 |
| `swing_sim_scale_in_order_assumed_filled` | 9 | 8 |

## OFI/QI Micro Context

- sample_count: `768`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.957`
- stale_missing_reason_counts: `{'micro_missing': 735, 'micro_not_ready': 6, 'state_insufficient': 6}`
- stale_missing_reason_combination_counts: `{'micro_missing': 729, 'micro_missing+micro_not_ready+state_insufficient': 6}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 1, 'micro_missing': 1}`
- stale_missing_group_counts: `{'exit': 732, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 24, 'insufficient': 3}`
- exit_micro_state_counts: `{'bullish': 8, 'neutral': 675, 'bearish': 55, 'insufficient': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 717, 'CONFIRM_EXIT': 15}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 27}`
- add_triggers: `{'swing_avg_down_ok': 18}`
- price_policies: `{'KEEP_EXISTING_PRICE': 8, 'market': 18, 'NO_CHANGE': 1}`
- add_ratio_summary: `{'count': 18, 'min': 0.4, 'max': 1.0, 'avg': 0.5984111111111111, 'mean': 0.5984111111111111, 'p50': 0.5, 'p95': 1.0}`
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
| `swing_gatekeeper_reject_cooldown` | 52 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 14 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 27 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 56 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 86 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 8 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 13 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 27 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 732 | `ready` |

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
