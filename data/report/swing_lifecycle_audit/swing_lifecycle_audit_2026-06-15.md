# Swing Lifecycle Audit - 2026-06-15

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `17`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `20`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.3718, 'win_rate_pct': 14.3, 'wins': 1, 'losses': 6, 'flat': 0}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 3, 'avg_profit_rate_pct': 0.4057}, 'blocked_swing_gap': {'count': 2, 'avg_profit_rate_pct': -1.0213}, 'blocked_swing_score_vpw': {'count': 3, 'avg_profit_rate_pct': -0.5764}, 'market_regime_prior_observed': {'count': 2, 'avg_profit_rate_pct': -0.2186}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 76547 | 17 |
| `holding` | 288 | 89 |
| `scale_in` | 614 | 9 |
| `exit` | 22 | 9 |
| `other` | 16055 | 18 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 9920 | 15 |
| `blocked_swing_gap` | 9200 | 11 |
| `blocked_swing_score_vpw` | 6084 | 14 |
| `gatekeeper_fast_reuse` | 844 | 12 |
| `gatekeeper_fast_reuse_bypass` | 9083 | 15 |
| `gatekeeper_reject_cache_reuse` | 7633 | 15 |
| `holding_flow_ofi_smoothing_applied` | 217 | 71 |
| `holding_started` | 2 | 1 |
| `market_regime_prior_observed` | 16009 | 17 |
| `sell_order_sent` | 11 | 3 |
| `swing_entry_micro_context_observed` | 16009 | 17 |
| `swing_entry_policy_evaluated` | 16009 | 17 |
| `swing_probe_discarded` | 1619 | 11 |
| `swing_probe_entry_candidate` | 4 | 4 |
| `swing_probe_exit_signal` | 4 | 4 |
| `swing_probe_holding_started` | 4 | 4 |
| `swing_probe_scale_in_order_assumed_filled` | 3 | 3 |
| `swing_probe_sell_order_assumed_filled` | 4 | 4 |
| `swing_probe_state_empty_overwrite_blocked` | 2 | 1 |
| `swing_probe_state_persisted` | 14 | 1 |
| `swing_probe_state_restored` | 27 | 1 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 3 | 1 |
| `swing_scale_in_micro_context_observed` | 595 | 9 |
| `swing_sim_buy_order_assumed_filled` | 69 | 17 |
| `swing_sim_holding_started` | 69 | 17 |
| `swing_sim_order_bundle_assumed_filled` | 69 | 17 |
| `swing_sim_scale_in_order_assumed_filled` | 16 | 8 |
| `swing_sim_sell_order_assumed_filled` | 3 | 2 |

## OFI/QI Micro Context

- sample_count: `32994`
- stale_missing_unique_record_count: `13`
- stale_missing_ratio: `0.2009`
- stale_missing_reason_counts: `{'micro_missing': 6628, 'micro_not_ready': 6413, 'state_insufficient': 6413, 'observer_unhealthy': 18}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 6395, 'micro_missing': 215, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 12, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- stale_missing_group_counts: `{'entry': 6404, 'exit': 217, 'scale_in': 7}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 18, 'observer_unhealthy_with_other_reason': 18, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'bearish': 983, 'neutral': 23981, 'bullish': 788, 'insufficient': 6404}`
- scale_in_micro_state_counts: `{'insufficient': 7, 'bullish': 19, 'neutral': 569, 'bearish': 19}`
- exit_micro_state_counts: `{'neutral': 200, 'insufficient': 2, 'bearish': 17, 'bullish': 5}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 216, 'CONFIRM_EXIT': 1}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 614}`
- add_triggers: `{'swing_avg_down_ok': 19}`
- price_policies: `{'NO_CHANGE': 3, 'market': 19, 'ALLOW_EXISTING_PRICE': 18, 'KEEP_EXISTING_PRICE': 557, 'WAIT_FOR_PULLBACK': 17}`
- add_ratio_summary: `{'count': 19, 'min': 0.0093, 'max': 0.5, 'avg': 0.34279473684210526, 'mean': 0.34279473684210526, 'p50': 0.4, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 19}`
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
| `swing_gatekeeper_reject_cooldown` | 17 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 17 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 14 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 53 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 66 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 89 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 9 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 9 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 32156 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 614 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 217 | `ready` |

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
