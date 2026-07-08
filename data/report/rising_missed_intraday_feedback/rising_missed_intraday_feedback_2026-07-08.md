# 2026-07-08 Rising Missed Intraday Feedback

- generated_at: 2026-07-08T10:00:01+09:00
- decision_authority: source_only_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, intraday_runtime_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, scale_in_guard_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_rising_missed_record_count: 14
- holding_record_count: 11
- rising_missed_avg_down_ge2_count: 0
- first_touch_regression_record_count: 8
- first_touch_avg_down_submitted_count: 2
- first_touch_avgdown_decision_blocked_count: 6
- first_touch_closed_count: 7
- first_touch_profitable_count: 1
- first_touch_loss_or_flat_count: 6
- first_touch_ai_provenance_missing_count: 1
- first_touch_ai_provenance_unusable_count: 3
- first_touch_pressure_provenance_missing_count: 3
- first_touch_pressure_provenance_unusable_count: 0
- first_touch_micro_provenance_missing_count: 4
- first_touch_micro_provenance_unusable_count: 3
- initial_quality_fail_count: 0
- scale_in_rescue_warning_count: 0
- code_improvement_order_count: 0

## First Touch Regression

- record_id=15960 code=042660 name=한화오션 label=first_touch_loss_or_flat submitted=True touch_profit=-3.93 touch_peak=-0.23 touch_ai=69.0 final_profit=-4.6 submitted_count=1 runtime_decision=moderate_ai_with_limited_repeated_blockers shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=4,blocked_ai_score=2
- record_id=15969 code=226320 name=잇츠한불 label=first_touch_loss_or_flat submitted=False touch_profit=-4.23 touch_peak=0.39 touch_ai=62.0 final_profit=-4.32 submitted_count=0 runtime_decision=ai_score_no_submit_authority:ai_score_unavailable|liquidity_or_spread_block shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_strength_momentum=3,blocked_liquidity=5,blocked_ai_score=3,blocked_gap_from_scan=1
- record_id=15964 code=114840 name=아이패밀리에스씨 label=first_touch_loss_or_flat submitted=False touch_profit=-5.29 touch_peak=0.29 touch_ai=58.0 final_profit=-5.39 submitted_count=0 runtime_decision=- shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_overbought=4,blocked_strength_momentum=1,blocked_liquidity=3,blocked_gap_from_scan=1
- record_id=15973 code=008930 name=한미사이언스 label=first_touch_loss_or_flat submitted=False touch_profit=-3.69 touch_peak=-0.15 touch_ai=57.0 final_profit=-3.17 submitted_count=0 runtime_decision=ai_score_no_submit_authority:ai_score_unavailable|liquidity_or_spread_block|weak_strength_vpw_without_recovery shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_strength_momentum=5,blocked_liquidity=1,blocked_overbought=3,blocked_ai_score=3
- record_id=15986 code=078160 name=메디포스트 label=first_touch_open_unresolved submitted=False touch_profit=-3.16 touch_peak=0.76 touch_ai=59.0 final_profit=None submitted_count=0 runtime_decision=ai_score_no_submit_authority:ai_score_unavailable|liquidity_or_spread_block shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_liquidity=2,blocked_gap_from_scan=1,blocked_ai_score=1
- record_id=15970 code=018260 name=삼성에스디에스 label=first_touch_loss_or_flat submitted=False touch_profit=-3.6 touch_peak=-0.23 touch_ai=54.0 final_profit=-4.56 submitted_count=0 runtime_decision=liquidity_or_spread_block shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_strength_momentum=3,blocked_ai_score=1
- record_id=15984 code=399720 name=가온칩스 label=first_touch_recovered_profit submitted=True touch_profit=-3.23 touch_peak=-0.23 touch_ai=57.0 final_profit=1.35 submitted_count=1 runtime_decision=insufficient_first_touch_recovery_confirmation shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=3,blocked_vpw=1,blocked_liquidity=1,blocked_ai_score=1
- record_id=16000 code=365660 name=레몬헬스케어 label=first_touch_loss_or_flat submitted=False touch_profit=-4.21 touch_peak=-0.23 touch_ai=56.0 final_profit=-5.69 submitted_count=0 runtime_decision=insufficient_first_touch_recovery_confirmation shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=

## Records
