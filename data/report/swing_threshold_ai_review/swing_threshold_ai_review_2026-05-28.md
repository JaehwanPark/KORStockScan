# Swing Threshold AI Review - 2026-05-28

- AI status: `parsed`
- Authority: proposal-only; deterministic guard and manual workorder remain the source of truth.
- Runtime change: `false`

| family | stage | deterministic | ai_state | proposal | guard |
| --- | --- | --- | --- | --- | --- |
| `swing_model_floor` | `selection` | `freeze` | `insufficient_context` | state=-, value=None | accepted=False, reason=ai_proposal_missing_for_family |
| `swing_selection_top_k` | `selection` | `freeze` | `correction_proposed` | state=hold_sample, value=None | accepted=True, reason=- |
| `swing_gatekeeper_accept_reject` | `entry` | `freeze` | `insufficient_context` | state=-, value=None | accepted=False, reason=ai_proposal_missing_for_family |
| `swing_gatekeeper_reject_cooldown` | `entry` | `freeze` | `insufficient_context` | state=-, value=None | accepted=False, reason=ai_proposal_missing_for_family |
| `swing_market_regime_sensitivity` | `entry` | `freeze` | `correction_proposed` | state=hold_sample, value=None | accepted=True, reason=- |
| `swing_pyramid_trigger` | `scale_in` | `freeze` | `insufficient_context` | state=-, value=None | accepted=False, reason=ai_proposal_missing_for_family |
| `swing_avg_down_eligibility` | `scale_in` | `freeze` | `insufficient_context` | state=-, value=None | accepted=False, reason=ai_proposal_missing_for_family |
| `swing_trailing_stop_time_stop` | `exit` | `freeze` | `insufficient_context` | state=-, value=None | accepted=False, reason=ai_proposal_missing_for_family |
| `swing_holding_flow_defer` | `holding_exit` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
| `swing_entry_ofi_qi_execution_quality` | `entry` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
| `swing_scale_in_ofi_qi_confirmation` | `scale_in` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
| `swing_exit_ofi_qi_smoothing` | `holding_exit` | `freeze` | `agree` | state=freeze, value=None | accepted=True, reason=- |
