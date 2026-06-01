# Swing Runtime Approval - 2026-06-01

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
- requested/blocked/approved: `3` / `13` / `0`

## Approval Requests

| approval_id | family | stage | score | sample | target_env_keys |
| --- | --- | --- | ---: | ---: | --- |
| `swing_runtime_approval:2026-06-01:swing_model_floor` | `swing_model_floor` | `selection` | 0.8554 | 3/3 | `SWING_FLOOR_BULL, SWING_FLOOR_BEAR` |
| `swing_runtime_approval:2026-06-01:swing_market_regime_sensitivity` | `swing_market_regime_sensitivity` | `entry` | 0.8554 | 14/3 | `SWING_MARKET_REGIME_SENSITIVITY` |
| `swing_one_share_real_canary:2026-06-01:phase0` | `swing_one_share_real_canary_phase0` | `real_canary_entry` | 0.8554 | 17/3 | `SWING_ONE_SHARE_REAL_CANARY_ENABLED, SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES, SWING_ONE_SHARE_REAL_CANARY_MAX_QTY, SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY, SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS, SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW, SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT` |

## Blocked

| family | state | score | reasons |
| --- | --- | ---: | --- |
| `swing_model_floor` | `dry_run_auto_apply_ready` | 0.8554 | `ai_tier2_validated_pre_final_dry_run_auto_apply` |
| `swing_selection_top_k` | `freeze` | 0.8554 | `same_stage_owner_conflict:swing_model_floor` |
| `swing_gatekeeper_accept_reject` | `freeze` | 0.8554 | `runtime_family_guard_missing` |
| `swing_gatekeeper_reject_cooldown` | `hold_sample` | 0.8254 | `family_sample_floor_not_met` |
| `swing_market_regime_sensitivity` | `dry_run_auto_apply_ready` | 0.8554 | `ai_tier2_validated_pre_final_dry_run_auto_apply` |
| `swing_pyramid_trigger` | `freeze` | 0.8554 | `runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `freeze` | 0.8554 | `runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `freeze` | 0.8554 | `runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `freeze` | 0.8554 | `runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `freeze` | 0.8554 | `entry_ofi_qi_invalid_micro_context, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `freeze` | 0.8554 | `runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `freeze` | 0.8554 | `runtime_family_guard_missing` |
| `swing_scale_in_real_canary_phase0` | `freeze` | None | `pyramid_sample_floor_not_met, final_exit_return_missing, exit_only_delta_missing, post_add_mae_missing, final_exit_return_missing, exit_only_delta_missing, post_add_mae_missing` |

## Source Quality Blockers

| family | stage | reasons | valid/invalid |
| --- | --- | --- | ---: |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `entry_ofi_qi_invalid_micro_context` | 45417/5 |
