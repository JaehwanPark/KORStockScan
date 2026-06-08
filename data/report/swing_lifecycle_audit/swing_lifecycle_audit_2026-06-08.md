# Swing Lifecycle Audit - 2026-06-08

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
- simulated_order_unique_records: `24`
- observation_axis_status: `{'ready': 10}`
- panic_state: `RECOVERY_CONFIRMED`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.1689, 'win_rate_pct': 28.6, 'wins': 2, 'losses': 4, 'flat': 1}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 4, 'avg_profit_rate_pct': 0.1387}, 'blocked_swing_score_vpw': {'count': 3, 'avg_profit_rate_pct': -0.0378}, 'market_regime_block': {'count': 2, 'avg_profit_rate_pct': -0.7613}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 54861 | 22 |
| `holding` | 725 | 115 |
| `scale_in` | 70 | 12 |
| `exit` | 58 | 40 |
| `other` | 13382 | 29 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 5955 | 14 |
| `blocked_swing_score_vpw` | 7276 | 21 |
| `gatekeeper_fast_reuse` | 193 | 3 |
| `gatekeeper_fast_reuse_bypass` | 5761 | 14 |
| `gatekeeper_reject_cache_reuse` | 4726 | 10 |
| `holding_flow_ofi_smoothing_applied` | 689 | 101 |
| `market_regime_block` | 13053 | 22 |
| `market_regime_prior_observed` | 178 | 22 |
| `sell_order_sent` | 22 | 22 |
| `swing_entry_micro_context_observed` | 13035 | 15 |
| `swing_entry_policy_evaluated` | 13230 | 22 |
| `swing_probe_discarded` | 4586 | 18 |
| `swing_probe_entry_candidate` | 13 | 12 |
| `swing_probe_exit_signal` | 13 | 12 |
| `swing_probe_holding_started` | 13 | 12 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 8 |
| `swing_probe_sell_order_assumed_filled` | 13 | 12 |
| `swing_probe_state_persisted` | 44 | 1 |
| `swing_probe_state_restored` | 31 | 1 |
| `swing_reentry_counterfactual_after_loss` | 30 | 3 |
| `swing_same_symbol_loss_reentry_blocked` | 7 | 2 |
| `swing_same_symbol_loss_reentry_cooldown` | 10 | 9 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 30 | 1 |
| `swing_scale_in_micro_context_observed` | 49 | 12 |
| `swing_sim_buy_order_assumed_filled` | 36 | 14 |
| `swing_sim_holding_started` | 36 | 14 |
| `swing_sim_order_bundle_assumed_filled` | 36 | 14 |
| `swing_sim_scale_in_order_assumed_filled` | 13 | 11 |
| `swing_sim_sell_order_assumed_filled` | 10 | 8 |

## OFI/QI Micro Context

- sample_count: `27130`
- stale_missing_unique_record_count: `48`
- stale_missing_ratio: `0.6253`
- stale_missing_reason_counts: `{'micro_missing': 16964, 'observer_unhealthy': 3563, 'micro_not_ready': 16249, 'state_insufficient': 16249}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3528, 'micro_missing+observer_unhealthy': 35, 'micro_missing+micro_not_ready+state_insufficient': 12721, 'micro_missing': 680}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 22, 'micro_missing': 25}`
- stale_missing_group_counts: `{'scale_in': 39, 'entry': 16236, 'exit': 689}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2, 'entry': 22, 'exit': 25}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3563, 'observer_unhealthy_with_other_reason': 3563, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'insufficient': 16236, 'neutral': 9417, 'bullish': 420, 'bearish': 275}`
- scale_in_micro_state_counts: `{'insufficient': 4, 'neutral': 63, 'bearish': 3}`
- exit_micro_state_counts: `{'neutral': 652, 'bearish': 37, 'bullish': 14, 'insufficient': 9}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 689}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 70}`
- add_triggers: `{'swing_avg_down_ok': 21}`
- price_policies: `{'NO_CHANGE': 37, 'WAIT_FOR_PULLBACK': 1, 'market': 21, 'KEEP_EXISTING_PRICE': 11}`
- add_ratio_summary: `{'count': 21, 'min': 0.4286, 'max': 1.0, 'avg': 0.5118285714285714, 'mean': 0.5118285714285714, 'p50': 0.5, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 21}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `69`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 23 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 23 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 20 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 54 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 101 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 115 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 12 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 40 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 26348 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 70 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 689 | `ready` |

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
