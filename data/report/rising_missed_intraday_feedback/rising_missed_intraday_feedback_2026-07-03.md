# 2026-07-03 Rising Missed Intraday Feedback

- generated_at: 2026-07-03T16:20:03+09:00
- decision_authority: source_only_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, intraday_runtime_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, scale_in_guard_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_rising_missed_record_count: 37
- holding_record_count: 26
- rising_missed_avg_down_ge2_count: 4
- first_touch_regression_record_count: 11
- first_touch_avg_down_submitted_count: 10
- first_touch_avgdown_decision_blocked_count: 0
- first_touch_closed_count: 7
- first_touch_profitable_count: 4
- first_touch_loss_or_flat_count: 3
- initial_quality_fail_count: 3
- scale_in_rescue_warning_count: 1
- code_improvement_order_count: 1

## First Touch Regression

- record_id=15211 code=484810 name=티엑스알로보틱스 label=first_touch_recovered_profit submitted=True touch_profit=-3.42 touch_peak=-0.23 touch_ai=65.0 final_profit=1.09 submitted_count=1 runtime_decision=- shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=3,blocked_vpw=2,blocked_liquidity=2,blocked_ai_score=1
- record_id=15203 code=094360 name=칩스앤미디어 label=first_touch_loss_or_flat submitted=True touch_profit=-3.89 touch_peak=-0.1 touch_ai=66.0 final_profit=-5.51 submitted_count=3 runtime_decision=- shadow_cap1=cap1_extra_avg_down_would_block max_avg_down=3 blockers=blocked_strength_momentum=8,blocked_vpw=1,blocked_liquidity=1,blocked_ai_score=1
- record_id=15206 code=042660 name=한화오션 label=first_touch_loss_or_flat submitted=True touch_profit=-3.1 touch_peak=-0.23 touch_ai=65.0 final_profit=-3.64 submitted_count=3 runtime_decision=- shadow_cap1=cap1_extra_avg_down_would_block max_avg_down=3 blockers=blocked_strength_momentum=3,blocked_ai_score=1
- record_id=15213 code=037710 name=광주신세계 label=first_touch_recovered_profit submitted=True touch_profit=-3.85 touch_peak=-0.23 touch_ai=45.0 final_profit=0.34 submitted_count=2 runtime_decision=- shadow_cap1=cap1_extra_avg_down_would_block max_avg_down=2 blockers=blocked_liquidity=2,blocked_ai_score=1
- record_id=15227 code=376900 name=로킷헬스케어 label=first_touch_recovered_profit submitted=True touch_profit=-3.44 touch_peak=-0.23 touch_ai=71.0 final_profit=1.86 submitted_count=1 runtime_decision=- shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=5,blocked_liquidity=4,blocked_ai_score=3
- record_id=15217 code=441270 name=파인엠텍 label=first_touch_loss_or_flat submitted=True touch_profit=-3.33 touch_peak=-0.23 touch_ai=67.0 final_profit=-4.64 submitted_count=3 runtime_decision=- shadow_cap1=cap1_extra_avg_down_would_block max_avg_down=3 blockers=blocked_overbought=13,blocked_strength_momentum=10,blocked_vpw=1,blocked_liquidity=3
- record_id=15224 code=090460 name=비에이치 label=first_touch_open_unresolved submitted=True touch_profit=-3.07 touch_peak=-0.23 touch_ai=51.0 final_profit=None submitted_count=1 runtime_decision=- shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=23,blocked_vpw=1,blocked_liquidity=2,blocked_ai_score=1
- record_id=15233 code=095500 name=미래나노텍 label=first_touch_recovered_profit submitted=True touch_profit=-4.16 touch_peak=0.75 touch_ai=62.0 final_profit=4.13 submitted_count=1 runtime_decision=- shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=11
- record_id=15231 code=486990 name=노타 label=first_touch_open_unresolved submitted=True touch_profit=-3.2 touch_peak=-0.23 touch_ai=43.0 final_profit=None submitted_count=1 runtime_decision=- shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=12,blocked_ai_score=3,blocked_vpw=1,blocked_liquidity=1
- record_id=15212 code=009520 name=포스코엠텍 label=first_touch_open_unresolved submitted=True touch_profit=-4.17 touch_peak=0.26 touch_ai=50.0 final_profit=None submitted_count=1 runtime_decision=- shadow_cap1=cap1_first_avg_down_allowed max_avg_down=1 blockers=blocked_strength_momentum=11,blocked_vpw=3,blocked_liquidity=3,blocked_ai_score=3
- record_id=15219 code=010120 name=LS ELECTRIC label=first_touch_open_unresolved submitted=False touch_profit=-4.47 touch_peak=-0.23 touch_ai=50.0 final_profit=None submitted_count=0 runtime_decision=- shadow_cap1=cap1_not_applicable_no_submit max_avg_down=0 blockers=blocked_strength_momentum=4

## Records

- record_id=15203 code=094360 name=칩스앤미디어 label=rising_missed_initial_quality_fail avg_down=3 latest_profit=-5.51 min_profit=-5.51 max_profit=0.93 latest_gate=None
- record_id=15206 code=042660 name=한화오션 label=rising_missed_initial_quality_fail avg_down=3 latest_profit=-3.64 min_profit=-5.23 max_profit=0.67 latest_gate=None
- record_id=15213 code=037710 name=광주신세계 label=rising_missed_scale_in_rescue_warning avg_down=2 latest_profit=0.34 min_profit=-3.85 max_profit=1.46 latest_gate=None
- record_id=15217 code=441270 name=파인엠텍 label=rising_missed_initial_quality_fail avg_down=3 latest_profit=-4.64 min_profit=-20.46 max_profit=0.95 latest_gate=None
