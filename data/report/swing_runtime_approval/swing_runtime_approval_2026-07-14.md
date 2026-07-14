# Swing Runtime Approval - 2026-07-14

- Runtime change: `false`
- Approval state: `proposal -> ai_tier2_auto_approved -> dry_run_auto_apply_ready`; final full live requires user approval
- Broker order submission: `false`
- tradeoff_score_threshold: `0.68`
- EV calibration source: `combined_real_plus_sim`
- sim authority: `equal_for_ev_calibration_when_sim_lifecycle_closed`
- requested/blocked/approved: `0` / `12` / `0`

## Approval Requests

| approval_id | family | stage | score | sample | target_env_keys |
| --- | --- | --- | ---: | ---: | --- |
| `-` | `none` | `-` | 0 | 0/0 | `-` |

## Blocked

| family | state | score | reasons |
| --- | --- | ---: | --- |
| `swing_model_floor` | `hold_sample` | 0.7406 | `family_sample_floor_not_met` |
| `swing_selection_top_k` | `hold_sample` | 0.7406 | `family_sample_floor_not_met` |
| `swing_gatekeeper_accept_reject` | `hold_sample` | 0.7073 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_gatekeeper_reject_cooldown` | `hold_sample` | 0.7073 | `family_sample_floor_not_met` |
| `swing_market_regime_sensitivity` | `hold_sample` | 0.7073 | `family_sample_floor_not_met` |
| `swing_pyramid_trigger` | `hold_sample` | 0.7073 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `hold_sample` | 0.7073 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `hold_sample` | 0.7273 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `hold_sample` | 0.7073 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `hold_sample` | 0.7073 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `hold_sample` | 0.7073 | `family_sample_floor_not_met, runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `hold_sample` | 0.7073 | `family_sample_floor_not_met, runtime_family_guard_missing` |

## Source Quality Blockers

| family | stage | reasons | valid/invalid |
| --- | --- | --- | ---: |
| `-` | `-` | `none` | 0/0 |
