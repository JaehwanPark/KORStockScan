# Swing Threshold AI Review - 2026-06-01

- AI status: `parsed`
- Authority: proposal-only; deterministic guard and manual workorder remain the source of truth.
- Runtime change: `false`

| family | stage | deterministic | ai_state | proposal | guard |
| --- | --- | --- | --- | --- | --- |
| `swing_model_floor` | `selection` | `approval_required` | `unavailable` | state=adjust_up, value=0.35 | accepted=True, reason=- |
| `swing_selection_top_k` | `selection` | `freeze` | `unavailable` | state=hold, value=3 | accepted=True, reason=- |
| `swing_gatekeeper_accept_reject` | `entry` | `freeze` | `unavailable` | state=freeze, value=None | accepted=True, reason=- |
| `swing_gatekeeper_reject_cooldown` | `entry` | `hold_sample` | `unavailable` | state=hold_sample, value=7200 | accepted=True, reason=- |
| `swing_market_regime_sensitivity` | `entry` | `approval_required` | `unavailable` | state=adjust_up, value=relaxed_entry_observe | accepted=False, reason=missing_numeric_bounds_for_value_proposal |
| `swing_pyramid_trigger` | `scale_in` | `freeze` | `unavailable` | state=freeze, value=None | accepted=True, reason=- |
| `swing_avg_down_eligibility` | `scale_in` | `freeze` | `unavailable` | state=freeze, value=None | accepted=True, reason=- |
| `swing_trailing_stop_time_stop` | `exit` | `freeze` | `unavailable` | state=freeze, value=None | accepted=True, reason=- |
| `swing_holding_flow_defer` | `holding_exit` | `freeze` | `unavailable` | state=freeze, value=None | accepted=True, reason=- |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `freeze` | `unavailable` | state=freeze, value=None | accepted=True, reason=- |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `freeze` | `unavailable` | state=freeze, value=None | accepted=True, reason=- |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `freeze` | `unavailable` | state=freeze, value=None | accepted=True, reason=- |
