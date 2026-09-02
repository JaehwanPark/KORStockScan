# Threshold Cycle AI Correction - 2026-09-02 postclose

- AI status: `parsed`
- Authority: proposal-only; deterministic calibration guard is the source of truth.
- Runtime change: `false`
- Input context chars: `70450`
- Input context hash: `39d69400b88f14bd4b3e589fc9f0ff83a41c78870290ce77ad2da13600256318`
- Provider status: `openai / success`
- Usage: input_tokens=`25827`, output_tokens=`7574`, total_tokens=`33401`, elapsed_ms=`67594`
- Cost: estimated_cost_usd=`0.0`, status=`operator_zero_cost_default`

| family | ai_state | route | proposal | guard | reason |
| --- | --- | --- | --- | --- | --- |
| soft_stop_whipsaw_confirmation | correction_proposed | instrumentation_gap | state=hold_sample, value=60, window=rolling_10d | accepted=True, effective_state=hold_sample, effective_value=60, runtime_change=False | calibration_state='adjust_up' is not supported by included evidence: source_sample_count=0, post_sell_soft_stop_total=0.0, holding_exit_observation_total=0.0, and holding_exit_observation_whipsaw_signal conflicts between candidate true and bundle false. Hold at current_value 60 pending joined whipsaw evidence. |
| holding_flow_ofi_smoothing | agree | threshold_candidate | state=hold_sample, value=90, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=90, runtime_change=False | Agree with hold_sample: sample floor 미달(4/20); holding_flow_override_exit_confirmed=1 and holding_flow_ofi_smoothing_applied=1 are insufficient for adjustment. |
| protect_trailing_smoothing | agree | threshold_candidate | state=hold_sample, value=20, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=20, runtime_change=False | window_policy_blocks_single_case_live_candidate:2/20 |
| trailing_continuation | correction_proposed | threshold_candidate | state=freeze, value=0.4, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=0.4, runtime_change=False | window_policy_blocks_single_case_live_candidate:2/20 |
| market_regime_continuous_thresholds | agree | normal_drift | state=hold_sample, value=65, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=65, runtime_change=False | window_policy_blocks_single_case_live_candidate:8/10 |
| pre_submit_price_guard | agree | normal_drift | state=hold, value=True, window=daily_intraday | accepted=True, effective_state=hold, effective_value=True, runtime_change=False | Agree with hold: pre_submit_price_guard는 broker 제출 직전 hard safety/source-quality 감사 전용이며 runtime apply 후보에서 제외된 상태로 유지된다. |
| dynamic_entry_price_resolver | caution | instrumentation_gap | state=hold_sample, value=1, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=1, runtime_change=False | hold_sample is appropriate despite sample_count=37 because source_metrics_summary reports coverage_gap_type='counterfactual_join_gap' and counterfactual_join_gap_count=371; no bounded recommended value is present. |
| entry_split_order_plan | caution | threshold_candidate | state=adjust_up, value=True, window=rolling_10d | accepted=True, effective_state=adjust_up, effective_value=True, runtime_change=False | Adjust_up is acceptable only as a bounded qty-preserving structural exploration seed; included context omits sample_count and guard details, and calibration_reason states this is not split-variant 양의 EV 판단. |
| scale_in_split_order_plan | agree | threshold_candidate | state=hold_sample, value=False, window=rolling_10d | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Agree with hold_sample: 직접 AVG_DOWN/real+sim 표본이 초기 bounded floor에 미달(0/3) and recommended_value remains false. |
| entry_price_execution_quality | agree | normal_drift | state=hold, value=report_only, window=daily_intraday | accepted=False, effective_state=hold_sample, effective_value=report_only, runtime_change=False | proposed_value_not_numeric_or_bool |
| score65_74_recovery_probe | caution | threshold_candidate | state=adjust_up, value=True, window=rolling_5d | accepted=True, effective_state=adjust_up, effective_value=True, runtime_change=False | Adjust_up is supported as a bounded canary candidate by sentinel_primary='SUBMIT_DROUGHT_CRITICAL' and calibration_reason indicating rolling_5d positive missed EV, but included details are truncated and latency_root_cause_counts remain material. |
| strength_momentum_soft_gate_p1 | agree | normal_drift | state=hold, value=False, window=rolling_5d | accepted=True, effective_state=hold, effective_value=False, runtime_change=False | Agree with hold: strength_momentum_soft_gate_p1 is a pre-AI gate redesign family and calibration_reason states approval artifact 전까지 자동 runtime apply 금지. |
| overbought_pullback_guard_p1 | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold, effective_value=False, runtime_change=False | ai_proposal_missing_for_family |
| liquidity_pre_submit_guard_p1 | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold, effective_value=False, runtime_change=False | ai_proposal_missing_for_family |
| bad_entry_refined_canary | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold_sample, effective_value=False, runtime_change=False | ai_proposal_missing_for_family |
| holding_exit_decision_matrix_advisory | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold_no_edge, effective_value=False, runtime_change=False | ai_proposal_missing_for_family |
| lifecycle_decision_matrix_runtime | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=adjust_up, effective_value=False, runtime_change=False | ai_proposal_missing_for_family |
| scale_in_price_guard | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold_sample, effective_value=60, runtime_change=False | ai_proposal_missing_for_family |
| position_sizing_dynamic_formula | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold_sample, effective_value=entry_type_5stage_cap25_v1, runtime_change=False | ai_proposal_missing_for_family |
| scalping_avg_down_recovery_quality_gate | insufficient_context | - | state=-, value=-, window=- | accepted=False, effective_state=hold_no_edge, effective_value=-, runtime_change=False | ai_proposal_missing_for_family |
