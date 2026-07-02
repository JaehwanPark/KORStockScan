# 2026-07-02 Rising Missed Intraday Feedback

- generated_at: 2026-07-02T17:00:01+09:00
- decision_authority: source_only_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, intraday_runtime_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, scale_in_guard_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_rising_missed_record_count: 35
- holding_record_count: 29
- rising_missed_avg_down_ge2_count: 1
- initial_quality_fail_count: 1
- scale_in_rescue_warning_count: 0
- code_improvement_order_count: 1

## Records

- record_id=15084 code=001260 name=남광토건 label=rising_missed_initial_quality_fail avg_down=2 latest_profit=-4.65 min_profit=-4.65 max_profit=0.3 latest_gate=None
