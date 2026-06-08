# Swing Selection Funnel Report - 2026-06-08

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `2`
- fallback_written_to_recommendations: `False`
- csv_rows: `2`
- db_rows: `22`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

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
| `swing_entry_micro_context_observed` | 13035 | 15 |
| `swing_probe_discarded` | 4586 | 18 |
| `swing_probe_entry_candidate` | 13 | 12 |
| `swing_probe_exit_signal` | 13 | 12 |
| `swing_probe_holding_started` | 13 | 12 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 8 |
| `swing_probe_sell_order_assumed_filled` | 13 | 12 |
| `swing_reentry_counterfactual_after_loss` | 30 | 3 |
| `swing_same_symbol_loss_reentry_blocked` | 7 | 2 |
| `swing_same_symbol_loss_reentry_cooldown` | 10 | 9 |
| `swing_scale_in_micro_context_observed` | 49 | 12 |
| `swing_sim_buy_order_assumed_filled` | 36 | 14 |
| `swing_sim_holding_started` | 36 | 14 |
| `swing_sim_order_bundle_assumed_filled` | 36 | 14 |
| `swing_sim_scale_in_order_assumed_filled` | 13 | 11 |
| `swing_sim_sell_order_assumed_filled` | 10 | 8 |

## Top Code Stage

- `swing_entry_micro_context_observed` 카카오뱅크(323410): 1906
- `market_regime_block` 카카오뱅크(323410): 1894
- `blocked_swing_score_vpw` 한국타이어앤테크놀로지(161390): 1889
- `swing_entry_micro_context_observed` 한국타이어앤테크놀로지(161390): 1889
- `market_regime_block` 한국타이어앤테크놀로지(161390): 1876
- `blocked_gatekeeper_reject` 카카오뱅크(323410): 1768
- `gatekeeper_fast_reuse_bypass` 카카오뱅크(323410): 1667
- `swing_entry_micro_context_observed` HJ중공업(097230): 1629
- `market_regime_block` HJ중공업(097230): 1616
- `swing_entry_micro_context_observed` 넷마블(251270): 1477

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
- exit_smoothing_action_counts: `{'NO_CHANGE': 689}`
