# Threshold Cycle AI Correction - 2026-08-26 postclose

- AI status: `parsed`
- Authority: proposal-only; deterministic calibration guard is the source of truth.
- Runtime change: `false`
- Input context chars: `87643`
- Input context hash: `44d46f07dd6d4339dfa7a94186bf03fe13da7767f52c5582c9f1d0fd846bea3e`
- Provider status: `openai / success`
- Usage: input_tokens=`34064`, output_tokens=`7366`, total_tokens=`41430`, elapsed_ms=`79116`
- Cost: estimated_cost_usd=`0.0`, status=`operator_zero_cost_default`

| family | ai_state | route | proposal | guard | reason |
| --- | --- | --- | --- | --- | --- |
| soft_stop_whipsaw_confirmation | caution | threshold_candidate | state=adjust_up, value=60, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=60, runtime_change=False | runtime_apply_not_allowed_for_family |
| holding_flow_ofi_smoothing | agree | normal_drift | state=hold_sample, value=90, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=90, runtime_change=False | Sample floor is not met, so holding current value is appropriate. |
| protect_trailing_smoothing | agree | normal_drift | state=hold, value=20, window=rolling_10d | accepted=True, effective_state=hold, effective_value=20, runtime_change=False | Sample is ready, but EV edge and qualifying cohort are absent; hold is preferred. |
| trailing_continuation | agree | incident | state=freeze, value=0.4, window=rolling_10d | accepted=True, effective_state=freeze, effective_value=0.4, runtime_change=False | Freeze is appropriate because GOOD_EXIT harm risk remains unresolved and recommended_value exceeds daily step discipline if applied directly. |
| market_regime_continuous_thresholds | agree | normal_drift | state=hold_sample, value=65, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=65, runtime_change=False | window_policy_blocks_single_case_live_candidate:7/10 |
| pre_submit_price_guard | agree | normal_drift | state=hold, value=True, window=daily_intraday | accepted=True, effective_state=hold, effective_value=True, runtime_change=False | Hard safety/source-quality guard should remain unchanged and excluded from runtime threshold candidates. |
| dynamic_entry_price_resolver | agree | instrumentation_gap | state=hold_sample, value=1, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=1, runtime_change=False | Instrumentation exists, but counterfactual join coverage gap blocks bounded price resolver recommendation. |
| entry_split_order_plan | agree | threshold_candidate | state=adjust_up, value=True, window=rolling_10d | accepted=True, effective_state=adjust_up, effective_value=True, runtime_change=False | Adjustment is acceptable only as qty-preserving bounded exploration seed, not as EV-validated split superiority. |
| scale_in_split_order_plan | agree | normal_drift | state=hold_sample, value=False, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Direct AVG_DOWN/real+sim sample is zero, so PREOPEN application remains blocked. |
| entry_price_execution_quality | agree | normal_drift | state=hold, value=report_only, window=daily_intraday | accepted=False, effective_state=hold_sample, effective_value=report_only, runtime_change=False | proposed_value_not_numeric_or_bool |
| score65_74_recovery_probe | caution | threshold_candidate | state=adjust_up, value=True, window=rolling_5d | accepted=True, effective_state=adjust_up, effective_value=True, runtime_change=False | Positive missed-entry EV supports a bounded canary, but drought and source-quality risk require tight attribution and guard review. |
| strength_momentum_soft_gate_p1 | agree | instrumentation_gap | state=hold, value=False, window=rolling_5d | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Hold is appropriate until approval artifact and populated source metrics exist. |
| overbought_pullback_guard_p1 | agree | normal_drift | state=hold, value=False, window=rolling_5d | accepted=True, effective_state=hold, effective_value=False, runtime_change=False | Evidence favors preserving report-only status; avoided-loser benefit is visible and allowed_runtime_apply is false. |
| liquidity_pre_submit_guard_p1 | caution | normal_drift | state=hold, value=False, window=rolling_5d | accepted=True, effective_state=hold, effective_value=False, runtime_change=False | Hold remains safer because runtime apply is not allowed and evaluated candidate evidence is too sparse despite adverse missed-winner signal. |
| bad_entry_refined_canary | agree | instrumentation_gap | state=hold_sample, value=False, window=rolling_10d | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Runtime promotion is blocked by insufficient resolved sample and missing executable-price counterfactual EV contract. |
| holding_exit_decision_matrix_advisory | agree | instrumentation_gap | state=hold, value=False, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Advisory should hold because matrix and SAW contracts are missing and no clear edge exists. |
| lifecycle_decision_matrix_runtime | correction_proposed | instrumentation_gap | state=hold, value=False, window=rolling_5d | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Proposed correction: do not adjust up until runtime approval candidates are present; source summary shows policy_pass_count=5 but promote_ready_count=0 and runtime candidate lists are empty. |
| scale_in_price_guard | agree | normal_drift | state=hold_sample, value=60, window=rolling_10d | accepted=True, effective_state=hold_sample, effective_value=60, runtime_change=False | No resolved or executed scale-in cohort exists; hold sample is appropriate. |
| position_sizing_dynamic_formula | agree | instrumentation_gap | state=hold_sample, value=entry_type_5stage_cap25_v1, window=rolling_10d | accepted=True, effective_state=hold_sample, effective_value=entry_type_5stage_cap25_v1, runtime_change=False | Hold sample is appropriate because the formula candidate grid is not generated despite denominator sample. |
| scalping_avg_down_recovery_quality_gate | agree | threshold_candidate | state=hold, value=-, window=cumulative | accepted=True, effective_state=hold, effective_value=-, runtime_change=False | Hold is appropriate because shallow and deep post-add final EV are negative and recommended_values are unchanged. |
