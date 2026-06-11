# Swing Lifecycle Audit - 2026-06-11

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `2`
- csv_rows: `2`
- db_rows: `31`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `37`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': 0.4258, 'win_rate_pct': 57.1, 'wins': 4, 'losses': 3, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 4, 'avg_profit_rate_pct': -0.0266}, 'blocked_swing_gap': {'count': 1, 'avg_profit_rate_pct': 1.1329}, 'blocked_swing_score_vpw': {'count': 3, 'avg_profit_rate_pct': 1.1334}, 'market_regime_prior_observed': {'count': 2, 'avg_profit_rate_pct': -0.3392}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 37166 | 31 |
| `holding` | 518 | 137 |
| `scale_in` | 70 | 13 |
| `exit` | 50 | 18 |
| `other` | 9062 | 35 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 2782 | 22 |
| `blocked_swing_gap` | 1169 | 12 |
| `blocked_swing_score_vpw` | 6025 | 27 |
| `gatekeeper_fast_reuse` | 31 | 9 |
| `gatekeeper_fast_reuse_bypass` | 2752 | 22 |
| `gatekeeper_reject_cache_reuse` | 1229 | 17 |
| `holding_flow_ofi_smoothing_applied` | 461 | 107 |
| `market_regime_block` | 1225 | 31 |
| `market_regime_prior_observed` | 7582 | 31 |
| `sell_order_sent` | 2 | 2 |
| `swing_entry_micro_context_observed` | 8770 | 31 |
| `swing_entry_policy_evaluated` | 8807 | 31 |
| `swing_probe_discarded` | 5449 | 19 |
| `swing_probe_entry_candidate` | 19 | 10 |
| `swing_probe_exit_signal` | 19 | 14 |
| `swing_probe_holding_started` | 19 | 10 |
| `swing_probe_scale_in_order_assumed_filled` | 12 | 7 |
| `swing_probe_sell_order_assumed_filled` | 19 | 14 |
| `swing_probe_state_empty_overwrite_blocked` | 4 | 1 |
| `swing_probe_state_persisted` | 78 | 1 |
| `swing_probe_state_restored` | 66 | 1 |
| `swing_reentry_counterfactual_after_loss` | 32 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 8 | 4 |
| `swing_same_symbol_loss_reentry_cooldown` | 9 | 7 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 58 | 1 |
| `swing_scale_in_micro_context_observed` | 36 | 13 |
| `swing_sim_buy_order_assumed_filled` | 57 | 30 |
| `swing_sim_holding_started` | 57 | 30 |
| `swing_sim_order_bundle_assumed_filled` | 57 | 30 |
| `swing_sim_scale_in_order_assumed_filled` | 22 | 12 |
| `swing_sim_sell_order_assumed_filled` | 10 | 5 |

## OFI/QI Micro Context

- sample_count: `18261`
- stale_missing_unique_record_count: `17`
- stale_missing_ratio: `0.0714`
- stale_missing_reason_counts: `{'micro_missing': 1303, 'observer_unhealthy': 3, 'micro_not_ready': 845, 'state_insufficient': 845}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3, 'micro_missing+micro_not_ready+state_insufficient': 842, 'micro_missing': 458}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 14, 'micro_missing': 2}`
- stale_missing_group_counts: `{'scale_in': 3, 'entry': 839, 'exit': 461}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'entry': 14, 'exit': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3, 'observer_unhealthy_with_other_reason': 3, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 15795, 'bearish': 625, 'bullish': 442, 'insufficient': 839}`
- scale_in_micro_state_counts: `{'insufficient': 3, 'neutral': 66, 'bearish': 1}`
- exit_micro_state_counts: `{'neutral': 463, 'bearish': 14, 'bullish': 10, 'insufficient': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 461}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 70}`
- add_triggers: `{'swing_avg_down_ok': 34}`
- price_policies: `{'NO_CHANGE': 1, 'market': 34, 'KEEP_EXISTING_PRICE': 34, 'WAIT_FOR_PULLBACK': 1}`
- add_ratio_summary: `{'count': 34, 'min': 0.4, 'max': 1.0, 'avg': 0.5731647058823529, 'mean': 0.5731647058823529, 'p50': 0.5, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 34}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `93`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 31 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 31 | 0 | 0 | 0 | None |
| `swing_model_floor` | 2 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 29 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 2 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 2 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 92 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 148 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 137 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 13 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 18 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 17701 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 70 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 461 | `ready` |

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
