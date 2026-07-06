# 2026-07-06 Rising Missed Intraday Feedback

- generated_at: 2026-07-06T19:35:01+09:00
- decision_authority: source_only_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, intraday_runtime_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, scale_in_guard_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_rising_missed_record_count: 35
- holding_record_count: 24
- rising_missed_avg_down_ge2_count: 0
- first_touch_regression_record_count: 8
- first_touch_avg_down_submitted_count: 5
- first_touch_avgdown_decision_blocked_count: 4
- first_touch_closed_count: 6
- first_touch_profitable_count: 4
- first_touch_loss_or_flat_count: 2
- first_touch_ai_provenance_missing_count: 0
- first_touch_ai_provenance_unusable_count: 3
- first_touch_pressure_provenance_missing_count: 0
- first_touch_pressure_provenance_unusable_count: 0
- first_touch_micro_provenance_missing_count: 0
- first_touch_micro_provenance_unusable_count: 8
- initial_quality_fail_count: 0
- scale_in_rescue_warning_count: 0
- code_improvement_order_count: 0

## First Touch Regression

- record_id=15473 code=042700 name=한미반도체 label=first_touch_open_unresolved submitted=False touch_profit=-3.57 touch_peak=-0.02 touch_ai=58.0 final_profit=None submitted_count=0 runtime_decision=liquidity_or_spread_block|weak_strength_vpw_without_recovery shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_strength_momentum=1,blocked_ai_score=5
- record_id=15489 code=272210 name=한화시스템 label=first_touch_recovered_profit submitted=True touch_profit=-4.37 touch_peak=0.46 touch_ai=50.0 final_profit=0.59 submitted_count=1 runtime_decision=recovery_support_confirmed shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=3,blocked_ai_score=4,blocked_vpw=2
- record_id=15468 code=034020 name=두산에너빌리티 label=first_touch_loss_or_flat submitted=True touch_profit=-3.04 touch_peak=-0.23 touch_ai=61.0 final_profit=-3.16 submitted_count=1 runtime_decision=moderate_ai_with_limited_repeated_blockers shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=
- record_id=15526 code=002990 name=금호건설 label=first_touch_recovered_profit submitted=True touch_profit=-5.5 touch_peak=-0.23 touch_ai=50.0 final_profit=2.55 submitted_count=1 runtime_decision=recovery_support_confirmed shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=6,blocked_vpw=2,blocked_liquidity=2,blocked_ai_score=2
- record_id=15506 code=042660 name=한화오션 label=first_touch_recovered_profit submitted=True touch_profit=-3.02 touch_peak=-0.23 touch_ai=54.0 final_profit=0.45 submitted_count=1 runtime_decision=insufficient_first_touch_recovery_confirmation shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=1,blocked_vpw=1
- record_id=15536 code=001260 name=남광토건 label=first_touch_loss_or_flat submitted=False touch_profit=-3.62 touch_peak=-0.23 touch_ai=50.0 final_profit=-5.32 submitted_count=0 runtime_decision=liquidity_or_spread_block|weak_strength_vpw_without_recovery shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_overbought=5,blocked_liquidity=4,blocked_ai_score=3,blocked_strength_momentum=1
- record_id=15578 code=300720 name=한일시멘트 label=first_touch_recovered_profit submitted=True touch_profit=-3.47 touch_peak=0.41 touch_ai=57.0 final_profit=0.56 submitted_count=1 runtime_decision=recovery_support_confirmed shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=3,blocked_liquidity=2,blocked_ai_score=1
- record_id=15577 code=004980 name=성신양회 label=first_touch_open_unresolved submitted=False touch_profit=-3.01 touch_peak=-0.23 touch_ai=55.0 final_profit=None submitted_count=0 runtime_decision=insufficient_first_touch_recovery_confirmation shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_overbought=6,blocked_strength_momentum=2,blocked_ai_score=5,blocked_liquidity=1

## Records
