# Swing Runtime Approval - 2026-06-09

- Runtime change: `false`
- Approval state: `proposal -> ai_tier2_auto_approved -> dry_run_auto_apply_ready`; final full live requires user approval
- Broker order submission: `false`
- tradeoff_score_threshold: `0.68`
- EV calibration source: `combined_real_plus_sim`
- sim authority: `equal_for_ev_calibration_when_sim_lifecycle_closed`
- requested/blocked/approved: `1` / `12` / `0`

## Approval Requests

| approval_id | family | stage | score | sample | target_env_keys |
| --- | --- | --- | ---: | ---: | --- |
| `swing_runtime_approval:2026-06-09:swing_gatekeeper_reject_cooldown` | `swing_gatekeeper_reject_cooldown` | `entry` | 0.955 | 8/5 | `ML_GATEKEEPER_REJECT_COOLDOWN` |

## Blocked

| family | state | score | reasons |
| --- | --- | ---: | --- |
| `swing_model_floor` | `hold_sample` | 0.9383 | `family_sample_floor_not_met` |
| `swing_selection_top_k` | `hold_sample` | 0.9383 | `family_sample_floor_not_met` |
| `swing_gatekeeper_accept_reject` | `freeze` | 0.955 | `runtime_family_guard_missing` |
| `swing_gatekeeper_reject_cooldown` | `dry_run_auto_apply_ready` | 0.955 | `ai_tier2_validated_pre_final_dry_run_auto_apply` |
| `swing_market_regime_sensitivity` | `freeze` | 0.955 | `same_stage_owner_conflict:swing_gatekeeper_reject_cooldown` |
| `swing_pyramid_trigger` | `freeze` | 0.955 | `runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `freeze` | 0.955 | `runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `freeze` | 0.955 | `runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `freeze` | 0.955 | `runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `freeze` | 0.955 | `entry_ofi_qi_invalid_micro_context, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `freeze` | 0.955 | `scale_in_ofi_qi_invalid_micro_context, runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `freeze` | 0.955 | `runtime_family_guard_missing` |

## Source Quality Blockers

| family | stage | reasons | valid/invalid |
| --- | --- | --- | ---: |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `entry_ofi_qi_invalid_micro_context` | 14217/4 |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `scale_in_ofi_qi_invalid_micro_context` | 85/1 |
