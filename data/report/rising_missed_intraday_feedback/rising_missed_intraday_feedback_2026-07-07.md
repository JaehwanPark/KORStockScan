# 2026-07-07 Rising Missed Intraday Feedback

- generated_at: 2026-07-07T16:15:01+09:00
- decision_authority: source_only_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, intraday_runtime_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, scale_in_guard_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_rising_missed_record_count: 29
- holding_record_count: 21
- rising_missed_avg_down_ge2_count: 0
- first_touch_regression_record_count: 6
- first_touch_avg_down_submitted_count: 0
- first_touch_avgdown_decision_blocked_count: 5
- first_touch_closed_count: 6
- first_touch_profitable_count: 2
- first_touch_loss_or_flat_count: 4
- first_touch_ai_provenance_missing_count: 1
- first_touch_ai_provenance_unusable_count: 3
- first_touch_pressure_provenance_missing_count: 1
- first_touch_pressure_provenance_unusable_count: 0
- first_touch_micro_provenance_missing_count: 1
- first_touch_micro_provenance_unusable_count: 4
- initial_quality_fail_count: 0
- scale_in_rescue_warning_count: 0
- code_improvement_order_count: 0

## First Touch Regression

- record_id=15633 code=004980 name=성신양회 label=first_touch_loss_or_flat submitted=False touch_profit=-4.58 touch_peak=-0.02 touch_ai=62.0 final_profit=-5.3 submitted_count=0 runtime_decision=ai_score_no_submit_authority:ai_score_unavailable|liquidity_or_spread_block|weak_strength_vpw_without_recovery shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_strength_momentum=4,blocked_vpw=2,blocked_liquidity=2,blocked_ai_score=2
- record_id=15634 code=037710 name=광주신세계 label=first_touch_loss_or_flat submitted=False touch_profit=-3.78 touch_peak=0.56 touch_ai=50.0 final_profit=-5.16 submitted_count=0 runtime_decision=ai_score_no_submit_authority:ai_score_unavailable shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_strength_momentum=4,blocked_vpw=2,blocked_ai_score=2
- record_id=15639 code=094360 name=칩스앤미디어 label=first_touch_recovered_profit submitted=False touch_profit=-3.14 touch_peak=-0.23 touch_ai=58.0 final_profit=0.13 submitted_count=0 runtime_decision=insufficient_first_touch_recovery_confirmation shadow_cap1=cap1_not_applicable_no_submit max_avg_down=1 blockers=blocked_liquidity=2,blocked_ai_score=2
- record_id=15647 code=399720 name=가온칩스 label=first_touch_recovered_profit submitted=False touch_profit=-3.13 touch_peak=-0.23 touch_ai=59.0 final_profit=3.31 submitted_count=0 runtime_decision=liquidity_or_spread_block shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=
- record_id=15699 code=002990 name=금호건설 label=first_touch_loss_or_flat submitted=False touch_profit=-6.3 touch_peak=1.2 touch_ai=50.0 final_profit=-6.8 submitted_count=0 runtime_decision=- shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_overbought=5,blocked_liquidity=6,blocked_ai_score=6
- record_id=15737 code=153890 name=져스텍 label=first_touch_loss_or_flat submitted=False touch_profit=-3.08 touch_peak=0.37 touch_ai=50.0 final_profit=-7.98 submitted_count=0 runtime_decision=ai_score_no_submit_authority:ai_score_unavailable|liquidity_or_spread_block shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_strength_momentum=4,blocked_vpw=1,blocked_liquidity=1,blocked_ai_score=1

## Records
