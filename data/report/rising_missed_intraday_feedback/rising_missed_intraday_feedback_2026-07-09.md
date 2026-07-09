# 2026-07-09 Rising Missed Intraday Feedback

- generated_at: 2026-07-09T16:10:01+09:00
- decision_authority: source_only_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, intraday_runtime_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, scale_in_guard_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_rising_missed_record_count: 114
- holding_record_count: 7
- rising_missed_avg_down_ge2_count: 0
- first_touch_regression_record_count: 2
- first_touch_entry_submitted_count: 2
- first_touch_avg_down_submitted_count: 0
- first_touch_avgdown_decision_blocked_count: 1
- first_touch_closed_count: 1
- first_touch_profitable_count: 0
- first_touch_loss_or_flat_count: 1
- first_touch_ai_provenance_missing_count: 1
- first_touch_ai_provenance_unusable_count: 0
- first_touch_pressure_provenance_missing_count: 0
- first_touch_pressure_provenance_unusable_count: 0
- first_touch_micro_provenance_missing_count: 0
- first_touch_micro_provenance_unusable_count: 1
- initial_quality_fail_count: 0
- scale_in_rescue_warning_count: 0
- code_improvement_order_count: 0

## First Touch Regression

- record_id=16230 code=477850 name=마키나락스 label=first_touch_open_unresolved entry_submitted=True avgdown_submitted=False touch_profit=-3.52 touch_peak=-0.23 touch_ai=61.0 final_profit=None entry_submit_count=1 avgdown_submitted_count=0 runtime_decision=liquidity_or_spread_block shadow_cap1=cap1_not_applicable_no_submit max_avg_down=1 blockers=
- record_id=16283 code=024060 name=흥구석유 label=first_touch_loss_or_flat entry_submitted=True avgdown_submitted=False touch_profit=-5.34 touch_peak=1.36 touch_ai=50.0 final_profit=-5.34 entry_submit_count=1 avgdown_submitted_count=0 runtime_decision=- shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_overbought=4,blocked_strength_momentum=2,blocked_vpw=2,blocked_ai_score=2

## Records
