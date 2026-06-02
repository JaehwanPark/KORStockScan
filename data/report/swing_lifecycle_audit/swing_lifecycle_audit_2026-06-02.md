# Swing Lifecycle Audit - 2026-06-02

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `16`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `18`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 10, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.054, 'win_rate_pct': 28.6, 'wins': 2, 'losses': 3, 'flat': 2}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 4, 'avg_profit_rate_pct': -0.0633}, 'blocked_swing_score_vpw': {'count': 3, 'avg_profit_rate_pct': -0.1128}, 'market_regime_block': {'count': 2, 'avg_profit_rate_pct': 0.0187}, 'market_regime_prior_observed': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 100900 | 16 |
| `holding` | 945 | 118 |
| `scale_in` | 31 | 10 |
| `exit` | 53 | 31 |
| `other` | 26142 | 21 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 8916 | 7 |
| `blocked_swing_gap` | 713 | 3 |
| `blocked_swing_score_vpw` | 17032 | 15 |
| `gatekeeper_fast_reuse` | 955 | 3 |
| `gatekeeper_fast_reuse_bypass` | 7961 | 7 |
| `gatekeeper_reject_cache_reuse` | 7457 | 3 |
| `holding_flow_ofi_smoothing_applied` | 936 | 112 |
| `holding_started` | 1 | 1 |
| `market_regime_block` | 17588 | 16 |
| `market_regime_prior_observed` | 8359 | 16 |
| `sell_order_sent` | 21 | 18 |
| `swing_entry_micro_context_observed` | 25732 | 7 |
| `swing_entry_policy_evaluated` | 25947 | 16 |
| `swing_one_share_real_canary_blocked` | 8 | 5 |
| `swing_probe_discarded` | 6139 | 14 |
| `swing_probe_entry_candidate` | 16 | 10 |
| `swing_probe_exit_signal` | 16 | 13 |
| `swing_probe_holding_started` | 16 | 10 |
| `swing_probe_scale_in_order_assumed_filled` | 9 | 9 |
| `swing_probe_sell_order_assumed_filled` | 16 | 13 |
| `swing_probe_state_empty_overwrite_blocked` | 7 | 1 |
| `swing_probe_state_persisted` | 50 | 1 |
| `swing_probe_state_restored` | 39 | 1 |
| `swing_reentry_counterfactual_after_loss` | 42 | 6 |
| `swing_same_symbol_loss_reentry_blocked` | 5 | 3 |
| `swing_same_symbol_loss_reentry_cooldown` | 9 | 8 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 35 | 1 |
| `swing_scale_in_micro_context_observed` | 11 | 10 |
| `swing_sim_buy_order_assumed_filled` | 8 | 5 |
| `swing_sim_holding_started` | 8 | 5 |
| `swing_sim_order_bundle_assumed_filled` | 8 | 5 |
| `swing_sim_scale_in_order_assumed_filled` | 11 | 10 |

## OFI/QI Micro Context

- sample_count: `52692`
- stale_missing_unique_record_count: `32`
- stale_missing_ratio: `0.1219`
- stale_missing_reason_counts: `{'micro_missing': 6423, 'micro_not_ready': 5496, 'state_insufficient': 5496, 'observer_unhealthy': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing': 927, 'micro_missing+micro_not_ready+state_insufficient': 5495, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 16, 'micro_missing+micro_not_ready+state_insufficient': 16, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'exit': 936, 'entry': 5487}`
- stale_missing_group_unique_record_counts: `{'exit': 16, 'entry': 16}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 43485, 'bearish': 1489, 'bullish': 1248, 'insufficient': 5487}`
- scale_in_micro_state_counts: `{'neutral': 28, 'bullish': 3}`
- exit_micro_state_counts: `{'bullish': 21, 'neutral': 862, 'bearish': 60, 'insufficient': 9}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 928, 'CONFIRM_EXIT': 8}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 31}`
- add_triggers: `{'swing_avg_down_ok': 20}`
- price_policies: `{'KEEP_EXISTING_PRICE': 10, 'market': 20, 'ALLOW_EXISTING_PRICE': 1}`
- add_ratio_summary: `{'count': 20, 'min': 0.4, 'max': 1.0, 'avg': 0.51479, 'mean': 0.51479, 'p50': 0.4727, 'p95': 1.0}`
- post_add_outcomes: `{'pending_followup': 20}`
- guard_blockers: `{}`
- zero_sample_reason: `None`

## Simulation Opportunity

- available: `True`
- sample_state: `hold_sample`
- rows: `48`
- closed_count: `0`
- winner_count: `0`
- loser_count: `0`

| family | rows | closed | winner | loser | avg_net_ret |
| --- | ---: | ---: | ---: | ---: | ---: |
| `swing_gatekeeper_reject_cooldown` | 16 | 0 | 0 | 0 | None |
| `swing_market_regime_sensitivity` | 16 | 0 | 0 | 0 | None |
| `swing_model_floor` | 3 | 0 | 0 | 0 | None |
| `swing_selection_top_k` | 13 | 0 | 0 | 0 | None |

## Observation Axes

| axis | stage | family | sample | status |
| --- | --- | --- | ---: | --- |
| `swing_selection_model_floor` | `selection` | `swing_model_floor` | 3 | `ready` |
| `swing_recommendation_db_load` | `db_load` | `swing_selection_top_k` | 3 | `ready` |
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 27 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 78 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 118 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 10 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 31 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 51709 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 31 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 936 | `ready` |

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
