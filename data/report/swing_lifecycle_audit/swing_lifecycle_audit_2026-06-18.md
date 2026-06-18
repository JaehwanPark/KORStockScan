# Swing Lifecycle Audit - 2026-06-18

- owner: `SwingFullLifecycleSelfImprovementChain`
- runtime_change: `false`
- selected_count: `3`
- csv_rows: `3`
- db_rows: `21`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- completed_rows: `0`
- submitted_unique_records: `0`
- simulated_order_unique_records: `27`
- observation_axis_status: `{'ready': 10}`
- panic_state: `NORMAL`
- panic_active_sim_probe: `{'active_positions': 11, 'profit_sample': 7, 'avg_unrealized_profit_rate_pct': -0.6318, 'win_rate_pct': 14.3, 'wins': 1, 'losses': 4, 'flat': 2}`
- panic_origin_outcome: `{'blocked_gatekeeper_reject': {'count': 3, 'avg_profit_rate_pct': -0.9804}, 'blocked_swing_score_vpw': {'count': 4, 'avg_profit_rate_pct': -0.7707}, 'market_regime_prior_observed': {'count': 3, 'avg_profit_rate_pct': -0.0749}, 'unknown': {'count': 1, 'avg_profit_rate_pct': None}}`

## Lifecycle Funnel

| group | raw | unique_records |
| --- | ---: | ---: |
| `entry` | 14271 | 21 |
| `holding` | 809 | 117 |
| `scale_in` | 202 | 21 |
| `exit` | 78 | 26 |
| `other` | 4057 | 26 |

## Key Stages

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 397 | 10 |
| `blocked_swing_gap` | 23 | 2 |
| `blocked_swing_score_vpw` | 3395 | 21 |
| `gatekeeper_fast_reuse` | 20 | 5 |
| `gatekeeper_fast_reuse_bypass` | 378 | 10 |
| `gatekeeper_reject_cache_reuse` | 278 | 9 |
| `holding_flow_ofi_smoothing_applied` | 459 | 97 |
| `market_regime_pass` | 158 | 21 |
| `market_regime_prior_observed` | 3634 | 21 |
| `sell_order_failed` | 34 | 1 |
| `sell_order_sent` | 8 | 8 |
| `swing_entry_micro_context_observed` | 3714 | 20 |
| `swing_entry_policy_evaluated` | 3792 | 21 |
| `swing_probe_discarded` | 1554 | 20 |
| `swing_probe_entry_candidate` | 10 | 9 |
| `swing_probe_exit_signal` | 10 | 10 |
| `swing_probe_holding_started` | 10 | 9 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 8 |
| `swing_probe_sell_order_assumed_filled` | 10 | 10 |
| `swing_probe_state_persisted` | 44 | 1 |
| `swing_probe_state_restored` | 58 | 1 |
| `swing_reentry_counterfactual_after_loss` | 74 | 7 |
| `swing_same_symbol_loss_reentry_blocked` | 21 | 6 |
| `swing_same_symbol_loss_reentry_cooldown` | 11 | 10 |
| `swing_same_symbol_loss_reentry_cooldowns_restored` | 57 | 1 |
| `swing_scale_in_micro_context_observed` | 141 | 21 |
| `swing_sim_buy_order_assumed_filled` | 350 | 20 |
| `swing_sim_holding_started` | 350 | 20 |
| `swing_sim_order_bundle_assumed_filled` | 350 | 20 |
| `swing_sim_scale_in_order_assumed_filled` | 53 | 19 |
| `swing_sim_sell_order_assumed_filled` | 16 | 7 |

## OFI/QI Micro Context

- sample_count: `8917`
- stale_missing_unique_record_count: `31`
- stale_missing_ratio: `0.2014`
- stale_missing_reason_counts: `{'micro_missing': 1796, 'observer_unhealthy': 444, 'micro_not_ready': 1101, 'state_insufficient': 1101}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 200, 'micro_missing': 451, 'micro_missing+micro_not_ready+state_insufficient': 901, 'micro_missing+observer_unhealthy': 244}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 16, 'micro_missing+micro_not_ready+state_insufficient': 22, 'micro_missing': 8, 'micro_missing+observer_unhealthy': 22}`
- stale_missing_reason_counts_by_group: `{'exit': {'micro_missing': 467, 'observer_unhealthy': 10, 'micro_not_ready': 8, 'state_insufficient': 8}, 'entry': {'micro_missing': 1328, 'micro_not_ready': 1092, 'state_insufficient': 1092, 'observer_unhealthy': 434}, 'scale_in': {'micro_missing': 1, 'micro_not_ready': 1, 'state_insufficient': 1}}`
- stale_missing_reason_unique_record_counts_by_group: `{'exit': {'micro_missing': 14, 'observer_unhealthy': 7, 'micro_not_ready': 3, 'state_insufficient': 3}, 'entry': {'micro_missing': 21, 'micro_not_ready': 21, 'state_insufficient': 21, 'observer_unhealthy': 21}, 'scale_in': {'micro_missing': 1, 'micro_not_ready': 1, 'state_insufficient': 1}}`
- stale_missing_group_counts: `{'exit': 467, 'entry': 1328, 'scale_in': 1}`
- stale_missing_group_unique_record_counts: `{'exit': 14, 'entry': 21, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 444, 'observer_unhealthy_with_other_reason': 444, 'observer_unhealthy_only': 0}`
- orderbook_micro_reason_counts_by_group: `{'exit': {'insufficient_samples': 8, 'ready': 477}, 'entry': {'ready': 7138, 'insufficient_samples': 1047, 'missing_best_qty': 45}, 'scale_in': {'ready': 201, 'insufficient_samples': 1}}`
- observer_missing_reason_counts_by_group: `{'exit': {'missing_trade': 10, 'ok': 475}, 'entry': {'ok': 7796, 'missing_quote_and_trade': 40, 'missing_quote': 5, 'missing_trade': 389}, 'scale_in': {'ok': 202}}`
- source_quality_status_counts_by_group: `{'exit': {'source_quality_blocker': 8, 'ok': 18, 'UNKNOWN': 459}, 'entry': {'ok': 6902, 'source_quality_blocker': 1328}, 'scale_in': {'ok': 201, 'source_quality_blocker': 1}}`
- ws_quote_source_counts_by_group: `{'exit': {'missing': 26, 'UNKNOWN': 459}, 'entry': {'missing': 8230}, 'scale_in': {'last_ws_update_ts': 202}}`
- ws_quote_stale_counts_by_group: `{'exit': {'not_available_no_quote_age': 26, 'UNKNOWN': 459}, 'entry': {'not_available_no_quote_age': 8230}, 'scale_in': {'False': 133, 'True': 69}}`
- entry_micro_state_counts: `{'neutral': 6677, 'bearish': 155, 'bullish': 306, 'insufficient': 1092}`
- scale_in_micro_state_counts: `{'neutral': 187, 'bullish': 7, 'insufficient': 1, 'bearish': 7}`
- exit_micro_state_counts: `{'insufficient': 8, 'neutral': 443, 'bearish': 29, 'bullish': 5}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 457, 'CONFIRM_EXIT': 2}`

## Scale-In Observation

- action_groups: `{'AVG_DOWN': 202}`
- add_triggers: `{'swing_avg_down_ok': 61}`
- price_policies: `{'KEEP_EXISTING_PRICE': 129, 'market': 61, 'ALLOW_EXISTING_PRICE': 6, 'NO_CHANGE': 1, 'WAIT_FOR_PULLBACK': 5}`
- add_ratio_summary: `{'count': 61, 'min': 0.0208, 'max': 1.0, 'avg': 0.48983770491803275, 'mean': 0.48983770491803275, 'p50': 0.4973, 'p95': 0.5}`
- post_add_outcomes: `{'pending_followup': 61}`
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
| `swing_gatekeeper_accept_reject` | `entry` | `swing_gatekeeper_accept_reject` | 80 | `ready` |
| `swing_gap_market_budget_price_qty` | `entry` | `swing_market_regime_sensitivity` | 101 | `ready` |
| `swing_holding_mfe_mae_defer` | `holding` | `swing_holding_flow_defer` | 117 | `ready` |
| `swing_scale_in_avg_down_pyramid` | `scale_in` | `swing_pyramid_trigger` | 21 | `ready` |
| `swing_exit_post_sell_attribution` | `exit` | `swing_trailing_stop_time_stop` | 26 | `ready` |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `swing_entry_ofi_qi_execution_quality` | 8230 | `ready` |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `swing_scale_in_ofi_qi_confirmation` | 202 | `ready` |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `swing_exit_ofi_qi_smoothing` | 459 | `ready` |

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
