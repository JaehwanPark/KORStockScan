# Threshold Cycle AI Correction - 2026-09-03 postclose

- AI status: `parsed`
- Family coverage: `complete` (reviewed `20` / expected `20`)
- Missing families: `-`
- Authority: proposal-only; deterministic calibration guard is the source of truth.
- Runtime change: `false`
- Input context chars: `104442`
- Input context hash: `62f031d713e871933e8ae54fd78d6e78bbc6ca59aeb844fc01d4bc530197ba7b`
- Provider status: `openai / success`
- Usage: input_tokens=`38530`, output_tokens=`9548`, total_tokens=`48078`, elapsed_ms=`89293`
- Cost: estimated_cost_usd=`0.0`, status=`operator_zero_cost_default`

| family | ai_state | route | proposal | guard | reason |
| --- | --- | --- | --- | --- | --- |
| soft_stop_whipsaw_confirmation | agree | threshold_candidate | state=hold_sample, value=60, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=60, runtime_change=False | window_policy_blocks_single_case_live_candidate:1/10 |
| holding_flow_ofi_smoothing | agree | normal_drift | state=hold_sample, value=90, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=90, runtime_change=False | Agree with hold_sample: sample_count is 5/20 and no holding_flow_ofi_smoothing_applied events were observed. |
| protect_trailing_smoothing | caution | threshold_candidate | state=hold_sample, value=20, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=20, runtime_change=False | window_policy_blocks_single_case_live_candidate:4/20 |
| trailing_continuation | caution | incident | state=freeze, value=0.4, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=0.4, runtime_change=False | window_policy_blocks_single_case_live_candidate:4/20 |
| market_regime_continuous_thresholds | agree | normal_drift | state=hold_sample, value=65, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=65, runtime_change=False | window_policy_blocks_single_case_live_candidate:9/10 |
| pre_submit_price_guard | agree | normal_drift | state=hold, value=True, window=daily_intraday | accepted=True, effective_state=hold, effective_value=True, runtime_change=False | Agree with hold: pre_submit_price_guard is a broker pre-submit hard safety/source-quality audit and not a runtime threshold candidate. |
| dynamic_entry_price_resolver | caution | instrumentation_gap | state=hold_sample, value=1, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=1, runtime_change=False | Hold sampling because instrumentation exists but counterfactual_join_gap_count is large and no bounded runtime value is available. |
| entry_split_order_plan | agree | threshold_candidate | state=adjust_up, value=True, window=rolling_10d | accepted=True, effective_state=adjust_up, effective_value=True, runtime_change=False | Agree with adjust_up as a bounded, qty-preserving structural exploration seed only; it is not EV validation of split variants. |
| scale_in_split_order_plan | agree | threshold_candidate | state=hold_sample, value=False, window=daily_intraday | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Agree with hold_sample: direct AVG_DOWN/real+sim sample is 0/3 and runtime_apply_allowed is false. |
| entry_price_execution_quality | agree | normal_drift | state=hold, value=report_only, window=daily_intraday | accepted=False, effective_state=hold_sample, effective_value=report_only, runtime_change=False | proposed_value_not_numeric_or_bool |
| score65_74_recovery_probe | agree | threshold_candidate | state=adjust_up, value=True, window=rolling_5d | accepted=True, effective_state=adjust_up, effective_value=True, runtime_change=False | Agree with adjust_up as a bounded probe: sample is sufficient and score65_74 EV is positive while submit drought remains critical. |
| strength_momentum_soft_gate_p1 | agree | normal_drift | state=hold, value=False, window=rolling_5d | accepted=True, effective_state=hold, effective_value=False, runtime_change=False | Agree with hold: approval artifact is required before any runtime use, and allowed_runtime_apply is false. |
| overbought_pullback_guard_p1 | agree | threshold_candidate | state=hold, value=False, window=rolling_5d | accepted=True, effective_state=hold, effective_value=False, runtime_change=False | Agree with hold: evidence supports continued study, but runtime apply is not allowed before approval artifact. |
| liquidity_pre_submit_guard_p1 | caution | instrumentation_gap | state=hold, value=False, window=rolling_5d | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Hold and route as instrumentation_gap because candidate metrics include missed_winner_count=8 while missed_winner_rate is reported as "0.0". |
| bad_entry_refined_canary | agree | incident | state=freeze, value=False, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=False, runtime_change=False | window_policy_blocks_single_case_live_candidate:3/10 |
| holding_exit_decision_matrix_advisory | insufficient_context | instrumentation_gap | state=hold, value=False, window=- | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Hold because the advisory matrix and SAW contract are missing, leaving no clear edge or counterfactual proxy evidence. |
| lifecycle_decision_matrix_runtime | correction_proposed | instrumentation_gap | state=hold, value=False, window=- | accepted=True, effective_state=hold_sample, effective_value=False, runtime_change=False | Propose hold instead of adjust_up because promote_ready_count and runtime candidate counts are zero despite recommended_value=true. |
| scale_in_price_guard | agree | threshold_candidate | state=hold_sample, value=60, window=rolling_10d | accepted=True, effective_state=hold_sample, effective_value=60, runtime_change=False | Agree with hold_sample: resolved/executed scale-in cohort is absent, so price and quantity guard values should remain sampled only. |
| position_sizing_dynamic_formula | agree | threshold_candidate | state=hold_sample, value=entry_type_5stage_cap25_v1, window=rolling_10d | accepted=False, effective_state=hold_sample, effective_value=entry_type_5stage_cap25_v1, runtime_change=False | proposed_value_not_numeric_or_bool |
| scalping_avg_down_recovery_quality_gate | safety_concern | incident | state=freeze, value=-, window=cumulative | accepted=True, effective_state=freeze, effective_value=-, runtime_change=False | Freeze promotion candidates: both shallow and deep primary evidence show negative final EV and downside_edge_ok=false while recommended_values_changed=false. |
