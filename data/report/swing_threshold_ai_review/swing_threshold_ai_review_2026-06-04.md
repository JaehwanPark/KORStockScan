# Swing Threshold AI Review - 2026-06-04

- AI status: `parsed`
- Authority: proposal-only; deterministic guard and manual workorder remain the source of truth.
- Runtime change: `false`

| family | stage | deterministic | ai_state | proposal | guard |
| --- | --- | --- | --- | --- | --- |
| `swing_model_floor` | `selection` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
| `swing_selection_top_k` | `selection` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
| `swing_gatekeeper_accept_reject` | `entry` | `hold_sample` | `correction_proposed` | state=hold_sample, value=None | accepted=True, reason=- |
| `swing_gatekeeper_reject_cooldown` | `entry` | `hold_sample` | `correction_proposed` | state=hold_sample, value=None | accepted=True, reason=- |
| `swing_market_regime_sensitivity` | `entry` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
| `swing_pyramid_trigger` | `scale_in` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
| `swing_avg_down_eligibility` | `scale_in` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
| `swing_trailing_stop_time_stop` | `exit` | `hold_sample` | `correction_proposed` | state=hold_sample, value=None | accepted=True, reason=- |
| `swing_holding_flow_defer` | `holding_exit` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `freeze` | `correction_proposed` | state=freeze, value=None | accepted=True, reason=- |
