# Swing Runtime Approval - 2026-06-02

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
| `swing_model_floor` | `freeze` | 0.32 | `severe_downside_guard` |
| `swing_selection_top_k` | `freeze` | 0.32 | `severe_downside_guard` |
| `swing_gatekeeper_accept_reject` | `freeze` | 0.32 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_gatekeeper_reject_cooldown` | `freeze` | 0.32 | `severe_downside_guard` |
| `swing_market_regime_sensitivity` | `freeze` | 0.32 | `severe_downside_guard` |
| `swing_pyramid_trigger` | `freeze` | 0.32 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `freeze` | 0.32 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `freeze` | 0.32 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `freeze` | 0.32 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `freeze` | 0.32 | `entry_ofi_qi_invalid_micro_context, severe_downside_guard, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `freeze` | 0.32 | `severe_downside_guard, runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `freeze` | 0.32 | `severe_downside_guard, runtime_family_guard_missing` |

## Source Quality Blockers

| family | stage | reasons | valid/invalid |
| --- | --- | --- | ---: |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `entry_ofi_qi_invalid_micro_context` | 46222/16 |
