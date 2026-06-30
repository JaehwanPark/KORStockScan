# Swing Lifecycle Audit - 2026-06-30

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `2`
- csv_rows: `2`
- db_rows: `0`
- db_load_gap: `False`
- db_load_skip_reason: `swing_real_watching_disabled_by_policy`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `0`
- observation_axis_status: `{'ready': 5, 'hold_sample': 5}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 4, 'profit_sample': 0, 'avg_unrealized_profit_rate_pct': None, 'win_rate_pct': None, 'wins': 0, 'losses': 0, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 1, 'avg_profit_rate_pct': None}, 'blocked_swing_score_vpw': {'count': 1, 'avg_profit_rate_pct': None}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}, 'unknown': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 0 | 0 |
| `holding` | 165 | 29 |
| `scale_in` | 0 | 0 |
| `exit` | 75 | 38 |
| `other` | 0 | 0 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `holding_flow_ofi_smoothing_applied` | 165 | 29 |
| `sell_order_blocked_market_closed` | 31 | 4 |
| `sell_order_failed` | 1 | 1 |
| `sell_order_sent` | 43 | 34 |

## OFI/QI Micro Context

- sample_count: `165`
- stale_missing_unique_record_count: `18`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 165, 'micro_not_ready': 22, 'state_insufficient': 22, 'observer_unhealthy': 4}`
- stale_missing_reason_combination_counts: `{'micro_missing': 143, 'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 18, 'micro_missing+micro_not_ready+state_insufficient': 3, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_counts_by_group: `{'exit': {'micro_missing': 165, 'micro_not_ready': 22, 'state_insufficient': 22, 'observer_unhealthy': 4}}`
- stale_missing_reason_unique_record_counts_by_group: `{'exit': {'micro_missing': 18, 'micro_not_ready': 3, 'state_insufficient': 3, 'observer_unhealthy': 1}}`
- stale_missing_group_counts: `{'exit': 165}`
- stale_missing_group_unique_record_counts: `{'exit': 18}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}`
- orderbook_micro_reason_counts_by_group: `{'exit': {'ready': 143, 'insufficient_samples': 22}}`
- observer_missing_reason_counts_by_group: `{'exit': {'ok': 161, 'missing_trade': 4}}`
- source_quality_status_counts_by_group: `{'exit': {'UNKNOWN': 165}}`
- ws_quote_source_counts_by_group: `{'exit': {'UNKNOWN': 165}}`
- ws_quote_stale_counts_by_group: `{'exit': {'UNKNOWN': 165}}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_micro_state_counts: `{'neutral': 137, 'bearish': 4, 'insufficient': 22, 'bullish': 2}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 164, 'CONFIRM_EXIT': 1}`

## Scale-In Observation

- action_groups: `{}`
- add_triggers: `{}`
- price_policies: `{}`
- add_ratio_summary: `{'count': 0, 'min': None, 'max': None, 'avg': None, 'mean': None, 'p50': None, 'p95': None}`
- post_add_outcomes: `{}`
- guard_blockers: `{}`
- zero_sample_reason: `no_candidate`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `6`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 2 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 2 | 0 | 0 | 0 | None |
| `swing_model_floor` | 2 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 2 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 2 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 0 | `hold_sample` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 0 | `hold_sample` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 29 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 0 | `hold_sample` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 38 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 0 | `hold_sample` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 0 | `hold_sample` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 165 | `ready` |

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
