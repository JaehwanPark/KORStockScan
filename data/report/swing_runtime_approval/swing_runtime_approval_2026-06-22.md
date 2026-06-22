# Swing Runtime Approval - 2026-06-22

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
| `swing_model_floor` | `hold_no_edge` | 0.3541 | `tradeoff_score_below_approval_threshold` |
| `swing_selection_top_k` | `hold_no_edge` | 0.3541 | `tradeoff_score_below_approval_threshold` |
| `swing_gatekeeper_accept_reject` | `freeze` | 0.3541 | `runtime_family_guard_missing` |
| `swing_gatekeeper_reject_cooldown` | `hold_no_edge` | 0.3541 | `tradeoff_score_below_approval_threshold` |
| `swing_market_regime_sensitivity` | `hold_no_edge` | 0.3541 | `tradeoff_score_below_approval_threshold` |
| `swing_pyramid_trigger` | `freeze` | 0.3541 | `runtime_family_guard_missing` |
| `swing_avg_down_eligibility` | `freeze` | 0.3541 | `runtime_family_guard_missing` |
| `swing_trailing_stop_time_stop` | `freeze` | 0.3541 | `runtime_family_guard_missing` |
| `swing_holding_flow_defer` | `freeze` | 0.3541 | `runtime_family_guard_missing` |
| `swing_entry_ofi_qi_execution_quality` | `freeze` | 0.3541 | `entry_ofi_qi_invalid_micro_context, runtime_family_guard_missing` |
| `swing_scale_in_ofi_qi_confirmation` | `freeze` | 0.3541 | `runtime_family_guard_missing` |
| `swing_exit_ofi_qi_smoothing` | `freeze` | 0.3541 | `runtime_family_guard_missing` |

## Source Quality Blockers

| family | stage | reasons | valid/invalid |
| --- | --- | --- | ---: |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `entry_ofi_qi_invalid_micro_context` | 1696/7 |
