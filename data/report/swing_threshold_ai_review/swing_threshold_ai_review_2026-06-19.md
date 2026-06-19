# Swing Threshold AI Review - 2026-06-19

- AI status: `unavailable`
- Authority: proposal-only; deterministic guard and manual workorder remain the source of truth.
- Runtime change: `false`

| family | stage | deterministic | ai_state | proposal | guard |
| --- | --- | --- | --- | --- | --- |
| `swing_model_floor` | `selection` | `hold_no_edge` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_selection_top_k` | `selection` | `hold_no_edge` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_gatekeeper_accept_reject` | `entry` | `freeze` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_gatekeeper_reject_cooldown` | `entry` | `hold_no_edge` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_market_regime_sensitivity` | `entry` | `hold_no_edge` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_pyramid_trigger` | `scale_in` | `freeze` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_avg_down_eligibility` | `scale_in` | `freeze` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_trailing_stop_time_stop` | `exit` | `freeze` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_holding_flow_defer` | `holding_exit` | `freeze` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `freeze` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `freeze` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `freeze` | `unavailable` | state=-, value=None | accepted=False, reason=ai_unavailable |
