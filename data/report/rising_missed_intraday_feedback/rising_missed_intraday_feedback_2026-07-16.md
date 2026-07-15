# 2026-07-16 Rising Missed Intraday Feedback

- generated_at: 2026-07-16T08:50:01+09:00
- decision_authority: source_only_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, intraday_runtime_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, scale_in_guard_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_rising_missed_record_count: 57
- holding_record_count: 0
- rising_missed_avg_down_ge2_count: 0
- rising_missed_submit_lineage_record_count: 0
- rising_missed_order_plan_forced_count: 0
- rising_missed_entry_submitted_count: 0
- rising_missed_order_bundle_submitted_count: 0
- rising_missed_order_leg_sent_count: 0
- first_touch_regression_record_count: 0
- first_touch_entry_submitted_count: 0
- first_touch_avg_down_submitted_count: 0
- first_touch_avgdown_decision_blocked_count: 0
- first_touch_closed_count: 0
- first_touch_profitable_count: 0
- first_touch_loss_or_flat_count: 0
- first_touch_ai_provenance_missing_count: 0
- first_touch_ai_provenance_unusable_count: 0
- first_touch_pressure_provenance_missing_count: 0
- first_touch_pressure_provenance_unusable_count: 0
- first_touch_micro_provenance_missing_count: 0
- first_touch_micro_provenance_unusable_count: 0
- initial_quality_fail_count: 0
- scale_in_rescue_warning_count: 0
- submit_safety_block_count: 0
- submit_safety_source_quality_unknown_gate_counts: []
- submit_safety_source_quality_unknown_state_counts: []
- submit_safety_source_quality_unknown_missing_field_counts: []
- backoff_audit_symbol_count: 82
- backoff_recovered_eval_symbol_count: 13
- backoff_active_positive_delta_symbol_count: 0
- potential_backoff_opportunity_loss_count: 7
- latency_false_negative_review_count: 0
- latency_false_negative_true_ofi_count: 0
- latency_false_negative_spread_only_count: 0
- latency_false_negative_canary_candidate_count: 0
- latency_false_negative_canary_ready_count: 0
- latency_false_negative_canary_observe_wide_spread_count: 0
- latency_false_negative_canary_hold_sample_count: 0
- rising_missed_tp1_counterfactual_submit_safety_count: 0
- rising_missed_tp1_counterfactual_unique_symbol_count: 0
- rising_missed_tp1_counterfactual_action_counts: []
- rising_missed_tp1_counterfactual_selector_reason_counts: []
- rising_missed_tp1_counterfactual_risk_counts: []
- rising_missed_tp1_counterfactual_gross_label_counts: []
- rising_missed_nxt_evaluation_count: 0
- rising_missed_nxt_unique_symbol_count: 0
- rising_missed_nxt_session_bucket_counts: []
- rising_missed_nxt_micro_state_counts: []
- rising_missed_nxt_input_ready_count: 0
- rising_missed_nxt_rest_quote_selected_count: 0
- rising_missed_nxt_order_request_count: 0
- rising_missed_nxt_order_type_remap_count: 0
- rising_missed_nxt_post_block_sampler_registered_count: 0
- rising_missed_nxt_post_block_price_sample_count: 0
- rising_missed_nxt_post_block_fresh_price_sample_count: 0
- rising_missed_nxt_post_block_source_gap_sample_count: 0
- rising_missed_nxt_post_block_sampler_completed_count: 0
- rising_missed_nxt_post_block_sampler_outcome_counts: []
- code_improvement_order_count: 0

## Submit Safety Blockers


## Backoff Opportunity Audit

- code=382900 name=범한퓨얼셀 last_backoff=2026-07-16T08:32:21.747163 reason=signed_tape_sell_dominated source=market_data_signed_tape_feedback max_delta_after=13.05 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=1059.185 pass_after=0 promoted_after=0 heavy_after=0
- code=394800 name=쓰리빌리언 last_backoff=2026-07-16T08:31:47.955034 reason=signed_tape_sell_dominated_backoff_active source=market_data_signed_tape_feedback max_delta_after=8.2 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=1092.978 pass_after=0 promoted_after=0 heavy_after=0
- code=222800 name=심텍 last_backoff=2026-07-16T08:20:41.095733 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=6.48 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=1759.837 pass_after=0 promoted_after=0 heavy_after=0
- code=336260 name=두산퓨얼셀 last_backoff=2026-07-16T08:20:41.101963 reason=signed_tape_sell_dominated source=market_data_signed_tape_feedback max_delta_after=5.51 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=1759.831 pass_after=4 promoted_after=0 heavy_after=3
- code=476830 name=알지노믹스 last_backoff=2026-07-16T08:25:12.507605 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=3.88 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=1488.425 pass_after=0 promoted_after=0 heavy_after=0
- code=087010 name=펩트론 last_backoff=2026-07-16T08:39:21.316694 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=2.98 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=639.616 pass_after=0 promoted_after=0 heavy_after=0
- code=028300 name=HLB last_backoff=2026-07-16T08:40:24.209423 reason=signed_tape_sell_dominated source=market_data_signed_tape_feedback max_delta_after=2.18 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=576.723 pass_after=0 promoted_after=0 heavy_after=0
- code=086520 name=에코프로 last_backoff=2026-07-16T08:25:04.162571 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=1.27 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=1496.77 pass_after=79 promoted_after=1 heavy_after=34
- code=018290 name=브이티 last_backoff=2026-07-16T08:35:58.074360 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=1.15 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=842.858 pass_after=5 promoted_after=1 heavy_after=5
- code=476060 name=온코닉테라퓨틱스 last_backoff=2026-07-16T08:26:32.351536 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=1.12 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=1408.581 pass_after=0 promoted_after=0 heavy_after=0
- code=399720 name=가온칩스 last_backoff=2026-07-16T08:10:42.782563 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.58 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2358.15 pass_after=0 promoted_after=0 heavy_after=0
- code=084110 name=휴온스글로벌 last_backoff=2026-07-16T08:30:05.820231 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.53 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1195.112 pass_after=0 promoted_after=0 heavy_after=0
- code=042700 name=한미반도체 last_backoff=2026-07-16T08:30:35.857727 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.38 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=1165.075 pass_after=4 promoted_after=1 heavy_after=1
- code=096770 name=SK이노베이션 last_backoff=2026-07-16T08:37:17.530626 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.34 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=763.402 pass_after=19 promoted_after=1 heavy_after=19
- code=010950 name=S-Oil last_backoff=2026-07-16T08:33:27.389012 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.21 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=993.544 pass_after=46 promoted_after=1 heavy_after=45
- code=319660 name=피에스케이 last_backoff=2026-07-16T08:35:35.751321 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.05 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=865.181 pass_after=19 promoted_after=1 heavy_after=19
- code=131290 name=티에스이 last_backoff=2026-07-16T08:37:17.531186 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=-0.35 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=763.401 pass_after=0 promoted_after=0 heavy_after=0
- code=376900 name=로킷헬스케어 last_backoff=2026-07-16T08:30:35.857281 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=-0.56 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1165.075 pass_after=0 promoted_after=0 heavy_after=0
- code=460930 name=현대힘스 last_backoff=2026-07-16T08:10:42.692676 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=2358.24 pass_after=38 promoted_after=1 heavy_after=37
- code=226950 name=올릭스 last_backoff=2026-07-16T08:10:49.868171 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2351.064 pass_after=0 promoted_after=0 heavy_after=0
- code=042660 name=한화오션 last_backoff=2026-07-16T08:10:49.870673 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=2351.062 pass_after=8 promoted_after=1 heavy_after=7
- code=439090 name=마녀공장 last_backoff=2026-07-16T08:10:49.873386 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=2351.059 pass_after=72 promoted_after=2 heavy_after=73
- code=007660 name=이수페타시스 last_backoff=2026-07-16T08:11:46.022984 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2294.91 pass_after=0 promoted_after=0 heavy_after=0
- code=082740 name=한화엔진 last_backoff=2026-07-16T08:11:56.875483 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=2284.057 pass_after=29 promoted_after=2 heavy_after=29
- code=000670 name=영풍 last_backoff=2026-07-16T08:12:02.002388 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2278.93 pass_after=0 promoted_after=0 heavy_after=0
- code=023160 name=태광 last_backoff=2026-07-16T08:12:03.699157 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2277.233 pass_after=0 promoted_after=0 heavy_after=0
- code=007390 name=네이처셀 last_backoff=2026-07-16T08:13:52.031478 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2168.901 pass_after=0 promoted_after=0 heavy_after=0
- code=310210 name=보로노이 last_backoff=2026-07-16T08:13:52.036559 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2168.896 pass_after=0 promoted_after=0 heavy_after=0
- code=086450 name=동국제약 last_backoff=2026-07-16T08:14:15.848811 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=2145.084 pass_after=4 promoted_after=1 heavy_after=3
- code=445680 name=큐리옥스바이오시스템즈 last_backoff=2026-07-16T08:15:27.097985 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2073.835 pass_after=0 promoted_after=0 heavy_after=0
- code=058970 name=엠로 last_backoff=2026-07-16T08:15:34.913481 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2066.019 pass_after=0 promoted_after=0 heavy_after=0
- code=199800 name=툴젠 last_backoff=2026-07-16T08:15:38.923654 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2062.009 pass_after=0 promoted_after=0 heavy_after=0
- code=035760 name=CJ ENM last_backoff=2026-07-16T08:15:56.547721 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2044.385 pass_after=0 promoted_after=0 heavy_after=0
- code=003670 name=포스코퓨처엠 last_backoff=2026-07-16T08:19:13.643411 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1847.289 pass_after=0 promoted_after=0 heavy_after=0
- code=017670 name=SK텔레콤 last_backoff=2026-07-16T08:24:55.148456 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1505.784 pass_after=0 promoted_after=0 heavy_after=0
- code=078600 name=대주전자재료 last_backoff=2026-07-16T08:24:55.153175 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=1505.779 pass_after=3 promoted_after=1 heavy_after=3
- code=441270 name=파인엠텍 last_backoff=2026-07-16T08:25:04.179161 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1496.753 pass_after=0 promoted_after=0 heavy_after=0
- code=006110 name=삼아알미늄 last_backoff=2026-07-16T08:26:38.265992 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1402.667 pass_after=0 promoted_after=0 heavy_after=0
- code=365340 name=성일하이텍 last_backoff=2026-07-16T08:26:50.834723 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1390.098 pass_after=0 promoted_after=0 heavy_after=0
- code=468530 name=프로티나 last_backoff=2026-07-16T08:27:01.434810 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1379.498 pass_after=0 promoted_after=0 heavy_after=0
- code=078520 name=에이블씨엔씨 last_backoff=2026-07-16T08:27:01.440149 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1379.492 pass_after=0 promoted_after=0 heavy_after=0
- code=194700 name=노바렉스 last_backoff=2026-07-16T08:27:01.443733 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1379.489 pass_after=0 promoted_after=0 heavy_after=0
- code=397030 name=에이프릴바이오 last_backoff=2026-07-16T08:28:01.668438 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1319.264 pass_after=0 promoted_after=0 heavy_after=0
- code=488280 name=에스투더블유 last_backoff=2026-07-16T08:28:14.048246 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1306.884 pass_after=0 promoted_after=0 heavy_after=0
- code=298040 name=효성중공업 last_backoff=2026-07-16T08:28:14.052353 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1306.88 pass_after=0 promoted_after=0 heavy_after=0
- code=416180 name=신성에스티 last_backoff=2026-07-16T08:28:14.061874 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1306.871 pass_after=0 promoted_after=0 heavy_after=0
- code=373220 name=LG에너지솔루션 last_backoff=2026-07-16T08:28:38.435710 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1282.497 pass_after=0 promoted_after=0 heavy_after=0
- code=067080 name=대화제약 last_backoff=2026-07-16T08:28:38.444551 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1282.488 pass_after=0 promoted_after=0 heavy_after=0
- code=000240 name=한국앤컴퍼니 last_backoff=2026-07-16T08:28:47.780898 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1273.152 pass_after=0 promoted_after=0 heavy_after=0
- code=281820 name=케이씨텍 last_backoff=2026-07-16T08:28:56.080359 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1264.852 pass_after=0 promoted_after=0 heavy_after=0
- code=115180 name=큐리언트 last_backoff=2026-07-16T08:29:13.517795 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1247.415 pass_after=0 promoted_after=0 heavy_after=0
- code=092460 name=한라IMS last_backoff=2026-07-16T08:30:05.815446 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1195.117 pass_after=0 promoted_after=0 heavy_after=0
- code=032350 name=롯데관광개발 last_backoff=2026-07-16T08:30:41.171906 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1159.761 pass_after=0 promoted_after=0 heavy_after=0
- code=251970 name=펌텍코리아 last_backoff=2026-07-16T08:31:05.672666 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1135.26 pass_after=0 promoted_after=0 heavy_after=0
- code=086790 name=하나금융지주 last_backoff=2026-07-16T08:31:54.966941 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1085.966 pass_after=0 promoted_after=0 heavy_after=0
- code=064820 name=케이프 last_backoff=2026-07-16T08:31:54.967579 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1085.965 pass_after=0 promoted_after=0 heavy_after=0
- code=089970 name=브이엠 last_backoff=2026-07-16T08:32:30.719543 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1050.213 pass_after=0 promoted_after=0 heavy_after=0
- code=004170 name=신세계 last_backoff=2026-07-16T08:32:50.570424 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1030.362 pass_after=0 promoted_after=0 heavy_after=0
- code=272210 name=한화시스템 last_backoff=2026-07-16T08:33:27.380292 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=993.552 pass_after=0 promoted_after=0 heavy_after=0
- code=483650 name=달바글로벌 last_backoff=2026-07-16T08:33:27.385496 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=993.547 pass_after=0 promoted_after=0 heavy_after=0
- code=257720 name=실리콘투 last_backoff=2026-07-16T08:33:27.387540 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=993.545 pass_after=0 promoted_after=0 heavy_after=0
- code=095610 name=테스 last_backoff=2026-07-16T08:33:27.388053 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=993.545 pass_after=0 promoted_after=0 heavy_after=0
- code=161890 name=한국콜마 last_backoff=2026-07-16T08:33:27.388487 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=993.544 pass_after=0 promoted_after=0 heavy_after=0
- code=004990 name=롯데지주 last_backoff=2026-07-16T08:34:19.590983 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=941.342 pass_after=0 promoted_after=0 heavy_after=0
- code=137400 name=피엔티 last_backoff=2026-07-16T08:34:46.168474 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=914.764 pass_after=0 promoted_after=0 heavy_after=0
- code=066970 name=엘앤에프 last_backoff=2026-07-16T08:35:35.744815 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=865.188 pass_after=0 promoted_after=0 heavy_after=0
- code=114090 name=GKL last_backoff=2026-07-16T08:35:35.756965 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=865.176 pass_after=0 promoted_after=0 heavy_after=0
- code=075580 name=세진중공업 last_backoff=2026-07-16T08:37:17.529946 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=763.403 pass_after=0 promoted_after=0 heavy_after=0
- code=051910 name=LG화학 last_backoff=2026-07-16T08:37:17.531721 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=763.401 pass_after=0 promoted_after=0 heavy_after=0
- code=107640 name=한중엔시에스 last_backoff=2026-07-16T08:38:54.223434 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=666.709 pass_after=0 promoted_after=0 heavy_after=0
- code=079550 name=LIG디펜스앤에어로스페이스 last_backoff=2026-07-16T08:39:00.734804 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=660.198 pass_after=0 promoted_after=0 heavy_after=0
- code=039200 name=오스코텍 last_backoff=2026-07-16T08:39:03.565616 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=657.367 pass_after=0 promoted_after=0 heavy_after=0
- code=267980 name=매일유업 last_backoff=2026-07-16T08:39:13.909503 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=647.023 pass_after=0 promoted_after=0 heavy_after=0
- code=144510 name=지씨셀 last_backoff=2026-07-16T08:39:50.116306 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=610.816 pass_after=0 promoted_after=0 heavy_after=0
- code=183300 name=코미코 last_backoff=2026-07-16T08:40:36.110514 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=564.822 pass_after=0 promoted_after=0 heavy_after=0
- code=488900 name=비츠로넥스텍 last_backoff=2026-07-16T08:40:36.115843 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=564.817 pass_after=0 promoted_after=0 heavy_after=0
- code=005440 name=현대지에프홀딩스 last_backoff=2026-07-16T08:40:43.846160 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=557.086 pass_after=0 promoted_after=0 heavy_after=0
- code=196170 name=알테오젠 last_backoff=2026-07-16T08:40:49.655391 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=551.277 pass_after=0 promoted_after=0 heavy_after=0
- code=011780 name=금호석유화학 last_backoff=2026-07-16T08:40:56.024136 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=544.908 pass_after=0 promoted_after=0 heavy_after=0
- code=014820 name=동원시스템즈 last_backoff=2026-07-16T08:40:56.027305 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=544.905 pass_after=0 promoted_after=0 heavy_after=0
- code=036530 name=SNT홀딩스 last_backoff=2026-07-16T08:40:56.031447 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=544.901 pass_after=0 promoted_after=0 heavy_after=0
- code=237690 name=에스티팜 last_backoff=2026-07-16T08:42:34.147911 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=446.785 pass_after=0 promoted_after=0 heavy_after=0

## Latency False Negative Review


## Latency False Negative Canary Candidates


## TP1 Counterfactual First-hit Labels


## First Touch Regression


## Records
