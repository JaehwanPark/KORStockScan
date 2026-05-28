# Swing Runtime Approval - 2026-05-28

- Runtime change: `false`
- Approval state: `proposal -> approval_required -> approved_live_dry_run`; phase0 real canary: `auto_approved_real_canary -> preopen_bounded_real_canary`
- Broker order submission: `false`
- tradeoff_score_threshold: `0.68`
- EV calibration source: `combined_real_plus_sim`
- sim authority: `equal_for_ev_calibration_when_sim_lifecycle_closed`
- execution quality source: `real_only`
- real canary policy: `swing_one_share_real_canary_phase0`
- real canary allowed actions: `BUY_INITIAL, SELL_CLOSE`
- sim-only actions: `AVG_DOWN, PYRAMID, SCALE_IN`
- scale-in real canary policy: `swing_scale_in_real_canary_phase0`
- scale-in allowed actions: `PYRAMID, AVG_DOWN`
- requested/blocked/approved: `0` / `14` / `0`

## Approval Requests

| approval_id | family | stage | score | sample | target_env_keys |
| --- | --- | --- | ---: | ---: | --- |
| `-` | `none` | `-` | 0 | 0/0 | `-` |

## Blocked

| family | state | score | reasons |
| --- | --- | ---: | --- |
| `swing_model_floor` | `freeze` | 0.557 | `severe_downside_guard` |
| `swing_selection_top_k` | `freeze` | 0.557 | `severe_downside_guard` |
| `swing_gatekeeper_accept_reject` | `freeze` | 0.557 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_gatekeeper_reject_cooldown` | `freeze` | 0.557 | `severe_downside_guard` |
| `swing_market_regime_sensitivity` | `freeze` | 0.557 | `severe_downside_guard` |
| `swing_pyramid_trigger` | `freeze` | 0.557 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `freeze` | 0.557 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `freeze` | 0.557 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `freeze` | 0.557 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `freeze` | 0.557 | `entry_ofi_qi_invalid_micro_context, severe_downside_guard, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `freeze` | 0.557 | `scale_in_ofi_qi_invalid_micro_context, severe_downside_guard, runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `freeze` | 0.557 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_scale_in_real_canary_phase0` | `freeze` | None | `pyramid_sample_floor_not_met, scale_in_ofi_qi_invalid_micro_context, severe_downside_guard, final_exit_return_missing, exit_only_delta_missing, post_add_mae_missing, scale_in_ofi_qi_invalid_micro_context, severe_downside_guard, final_exit_return_missing, exit_only_delta_missing, post_add_mae_missing` |
| `swing_one_share_real_canary_phase0` | `freeze` | None | `runtime_approval_hard_floor_or_tradeoff_missing` |

## Source Quality Blockers

| family | stage | reasons | valid/invalid |
| --- | --- | --- | ---: |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `entry_ofi_qi_invalid_micro_context` | 35251/17 |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `scale_in_ofi_qi_invalid_micro_context` | 37/1 |
| `swing_scale_in_real_canary_phase0` | `scale_in` | `scale_in_ofi_qi_invalid_micro_context` | 37/1 |
