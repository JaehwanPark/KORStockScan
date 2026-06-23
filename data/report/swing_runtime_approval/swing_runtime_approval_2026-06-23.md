# Swing Runtime Approval - 2026-06-23

- Runtime change: `false`
- Approval state: `proposal -> ai_tier2_auto_approved -> dry_run_auto_apply_ready`; final full live requires user approval
- Broker order submission: `false`
- tradeoff_score_threshold: `0.68`
- EV calibration source: `combined_real_plus_sim`
- sim authority: `equal_for_ev_calibration_when_sim_lifecycle_closed`
- requested/blocked/approved: `2` / `12` / `0`

## Approval Requests

| approval_id | family | stage | score | sample | target_env_keys |
| --- | --- | --- | ---: | ---: | --- |
| `swing_runtime_approval:2026-06-23:swing_model_floor` | `swing_model_floor` | `selection` | 0.7812 | 3/3 | `SWING_FLOOR_BULL, SWING_FLOOR_BEAR` |
| `swing_runtime_approval:2026-06-23:swing_market_regime_sensitivity` | `swing_market_regime_sensitivity` | `entry` | 0.7812 | 18/3 | `SWING_MARKET_REGIME_SENSITIVITY` |

## Blocked

| family | state | score | reasons |
| --- | --- | ---: | --- |
| `swing_model_floor` | `dry_run_auto_apply_ready` | 0.7812 | `ai_tier2_validated_pre_final_dry_run_auto_apply` |
| `swing_selection_top_k` | `freeze` | 0.7812 | `same_stage_owner_conflict:swing_model_floor` |
| `swing_gatekeeper_accept_reject` | `freeze` | 0.7812 | `runtime_family_guard_missing` |
| `swing_gatekeeper_reject_cooldown` | `hold_sample` | 0.7612 | `family_sample_floor_not_met` |
| `swing_market_regime_sensitivity` | `dry_run_auto_apply_ready` | 0.7812 | `ai_tier2_validated_pre_final_dry_run_auto_apply` |
| `swing_pyramid_trigger` | `freeze` | 0.7812 | `runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `freeze` | 0.7812 | `runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `freeze` | 0.7812 | `runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `freeze` | 0.7812 | `runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `freeze` | 0.7812 | `entry_ofi_qi_invalid_micro_context, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `freeze` | 0.7812 | `scale_in_ofi_qi_invalid_micro_context, runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `freeze` | 0.7812 | `runtime_family_guard_missing` |

## Source Quality Blockers

| family | stage | reasons | valid/invalid |
| --- | --- | --- | ---: |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `entry_ofi_qi_invalid_micro_context` | 588/6 |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `scale_in_ofi_qi_invalid_micro_context` | 33/2 |
