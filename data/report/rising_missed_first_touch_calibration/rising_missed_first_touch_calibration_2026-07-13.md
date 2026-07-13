# 2026-07-13 Rising Missed First Touch Calibration

- generated_at: 2026-07-13T20:11:17+09:00
- family: rising_missed_first_touch_avgdown_decision_gate
- stage: scale_in
- decision_authority: postclose_calibration_candidate_preopen_only
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, real_execution_quality_approval

## Summary

- calibration_state: hold_sample
- calibration_reason: source_quality_not_pass
- sample_count: 39
- recovered_rate: 0.33
- loss_or_flat_rate: 0.67

## Candidate

- target_env_keys: -
- current_values: {"low_ai_block": 50.0, "max_repeated_blockers_without_support": 8, "max_spread_bps": 80.0, "min_ai_moderate": 60.0, "min_ai_support": 70.0, "min_prior_peak_pct": 0.3}
- recommended_values: {"low_ai_block": 50.0, "max_repeated_blockers_without_support": 8, "max_spread_bps": 80.0, "min_ai_moderate": 60.0, "min_ai_support": 70.0, "min_prior_peak_pct": 0.3}
