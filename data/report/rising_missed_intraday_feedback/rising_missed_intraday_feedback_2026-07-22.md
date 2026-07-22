# 2026-07-22 Rising Missed Intraday Feedback

- generated_at: 2026-07-22T09:05:01+09:00
- decision_authority: source_only_intraday_feedback_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, intraday_runtime_apply, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, scale_in_guard_bypass, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Summary

- forced_rising_missed_record_count: 72
- holding_record_count: 5
- rising_missed_avg_down_ge2_count: 0
- rising_missed_submit_lineage_record_count: 3
- rising_missed_order_plan_forced_count: 0
- rising_missed_entry_submitted_count: 3
- rising_missed_order_bundle_submitted_count: 3
- rising_missed_order_leg_sent_count: 3
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
- submit_safety_block_count: 2
- submit_safety_source_quality_unknown_gate_counts: []
- submit_safety_source_quality_unknown_state_counts: []
- submit_safety_source_quality_unknown_missing_field_counts: []
- backoff_audit_symbol_count: 57
- backoff_recovered_eval_symbol_count: 8
- backoff_active_positive_delta_symbol_count: 0
- potential_backoff_opportunity_loss_count: 9
- latency_false_negative_review_count: 0
- latency_false_negative_true_ofi_count: 0
- latency_false_negative_spread_only_count: 0
- latency_false_negative_canary_candidate_count: 0
- latency_false_negative_canary_ready_count: 0
- latency_false_negative_canary_observe_wide_spread_count: 0
- latency_false_negative_canary_hold_sample_count: 0
- rising_missed_tp1_counterfactual_submit_safety_count: 13
- rising_missed_tp1_counterfactual_unique_symbol_count: 3
- rising_missed_tp1_counterfactual_action_counts: [{'action': 'RECHECK_REQUIRED', 'count': 5}, {'action': 'HARD_VETO_EXPECTED', 'count': 4}, {'action': 'INPUT_DEFER_EXPECTED', 'count': 4}]
- rising_missed_tp1_counterfactual_selector_reason_counts: [{'selector_reason': 'rising_missed_tp1_lane_not_eligible', 'count': 4}, {'selector_reason': 'rising_missed_tp1_insufficient_positive_support', 'count': 3}, {'selector_reason': 'tp1_freshness_envelope_unavailable', 'count': 3}, {'selector_reason': 'rising_missed_tp1_hard_negative_evidence', 'count': 2}, {'selector_reason': 'tp1_micro_ws_unavailable', 'count': 1}]
- rising_missed_tp1_counterfactual_risk_counts: [{'risk': 'pressure_below_prior', 'count': 12}, {'risk': 'depth_support_weak', 'count': 12}, {'risk': 'wait_without_bid_imbalance', 'count': 12}, {'risk': 'spread_above_candidate_caution', 'count': 11}, {'risk': 'momentum_support_weak', 'count': 9}, {'risk': 'true_ofi_nonpositive', 'count': 6}]
- rising_missed_tp1_counterfactual_gross_label_counts: [{'gross_first_hit_label': 'no_hit_within_20m', 'count': 8}, {'gross_first_hit_label': 'gross_target_first', 'count': 1}, {'gross_first_hit_label': 'adverse_stop_first', 'count': 1}]
- rising_missed_nxt_evaluation_count: 0
- rising_missed_nxt_unique_symbol_count: 0
- rising_missed_nxt_session_bucket_counts: []
- rising_missed_nxt_micro_state_counts: []
- rising_missed_nxt_input_ready_count: 0
- rising_missed_nxt_rest_quote_selected_count: 0
- rising_missed_nxt_order_request_count: 0
- rising_missed_nxt_order_type_remap_count: 0
- rising_missed_nxt_post_block_sampler_registered_count: 0
- rising_missed_nxt_post_block_source_block_stage_counts: []
- rising_missed_nxt_post_block_source_block_order_submitted_count: 0
- rising_missed_nxt_post_block_source_block_residual_submitted_qty: 0
- rising_missed_nxt_post_block_price_sample_count: 0
- rising_missed_nxt_post_block_fresh_price_sample_count: 0
- rising_missed_nxt_post_block_source_gap_sample_count: 0
- rising_missed_nxt_post_block_rest_fallback_attempted_count: 0
- rising_missed_nxt_post_block_rest_fallback_applied_count: 0
- rising_missed_nxt_post_block_rest_budget_deferred_count: 0
- rising_missed_nxt_post_block_sampler_completed_count: 0
- rising_missed_nxt_post_block_sampler_outcome_counts: []
- code_improvement_order_count: 0

## Rising Missed Submit Lineage

- record_id=21847 code=102940 name=코오롱생명과학 entry_submitted=True plan_count=0 leg_request_count=1 leg_sent_count=1 bundle_count=1 primary_order_no=0001593 planned_price=- submitted_price=17190 reprice_block_count=0 reprice_reason=- cancel_confirmed_count=0 join=record_id
- record_id=21848 code=460930 name=현대힘스 entry_submitted=True plan_count=0 leg_request_count=1 leg_sent_count=1 bundle_count=1 primary_order_no=0002018 planned_price=- submitted_price=12710 reprice_block_count=0 reprice_reason=- cancel_confirmed_count=0 join=record_id
- record_id=21845 code=459510 name=나우로보틱스 entry_submitted=True plan_count=0 leg_request_count=1 leg_sent_count=1 bundle_count=1 primary_order_no=0002693 planned_price=- submitted_price=14220 reprice_block_count=0 reprice_reason=- cancel_confirmed_count=0 join=record_id

## Submit Safety Blockers

- ts=2026-07-22T08:05:25.393666 code=460930 name=현대힘스 stage=latency_block reason=latency_state_danger bucket=latency_true_ofi_below_floor components=spread_above_caution_below_guard_cap,true_ofi_below_floor delta=0.0 mfe_after=2.0095 mae_after=-0.1576 quote_age_sec=0.102 ai_action=None ai_score=0.0 true_ofi=0.0787 true_ofi_reason=true_ofi_below_floor spread_bps=55.162 source_quality_gate=None source_quality_state=None missing_fields=[] micro_state=insufficient
- ts=2026-07-22T08:05:33.103753 code=460930 name=현대힘스 stage=rising_missed_tick_speed_entry_block reason=tick_acceleration_ratio_lt_1 bucket=tick_acceleration_ratio_lt_1 components= delta=0.0 mfe_after=1.8489 mae_after=0.0 quote_age_sec=3.452 ai_action=None ai_score=None true_ofi=None true_ofi_reason=None spread_bps=None source_quality_gate=rising_missed_tick_context_present source_quality_state=None missing_fields=[] micro_state=neutral

## Backoff Opportunity Audit

- code=459510 name=나우로보틱스 last_backoff=2026-07-22T08:17:39.775116 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=10.02 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=2844.278 pass_after=0 promoted_after=0 heavy_after=0
- code=277810 name=레인보우로보틱스 last_backoff=2026-07-22T08:22:42.345909 reason=candidate_gate_backoff_active source=candidate_gate_feedback max_delta_after=7.56 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=2541.708 pass_after=0 promoted_after=0 heavy_after=0
- code=090360 name=로보스타 last_backoff=2026-07-22T08:16:07.092326 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=4.68 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=2936.961 pass_after=0 promoted_after=0 heavy_after=0
- code=108490 name=로보티즈 last_backoff=2026-07-22T08:21:48.420328 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=4.23 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=2595.633 pass_after=0 promoted_after=0 heavy_after=0
- code=307950 name=현대오토에버 last_backoff=2026-07-22T08:24:35.687381 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=3.94 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=2428.366 pass_after=0 promoted_after=0 heavy_after=0
- code=117730 name=티로보틱스 last_backoff=2026-07-22T08:17:39.782421 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=3.25 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=2844.271 pass_after=0 promoted_after=0 heavy_after=0
- code=126340 name=비나텍 last_backoff=2026-07-22T08:21:00.593319 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=1.85 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=2643.46 pass_after=0 promoted_after=0 heavy_after=0
- code=124500 name=아이티센글로벌 last_backoff=2026-07-22T08:21:00.578714 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=1.73 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=2643.475 pass_after=0 promoted_after=0 heavy_after=0
- code=089890 name=코세스 last_backoff=2026-07-22T08:34:41.452983 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=1.32 recovered_eval=False potential_loss=True state=mature_unrecovered age_sec=1822.601 pass_after=0 promoted_after=0 heavy_after=0
- code=012330 name=현대모비스 last_backoff=2026-07-22T08:21:48.412684 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.99 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2595.641 pass_after=0 promoted_after=0 heavy_after=0
- code=460930 name=현대힘스 last_backoff=2026-07-22T08:05:36.211395 reason=submit_safety_backoff_active source=submit_safety_feedback max_delta_after=0.95 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=3567.842 pass_after=2 promoted_after=2 heavy_after=3
- code=022100 name=포스코DX last_backoff=2026-07-22T08:24:02.714320 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.77 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2461.339 pass_after=0 promoted_after=0 heavy_after=0
- code=000500 name=가온전선 last_backoff=2026-07-22T08:35:11.540501 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.64 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=1792.513 pass_after=0 promoted_after=1 heavy_after=0
- code=476830 name=알지노믹스 last_backoff=2026-07-22T08:22:42.358865 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.38 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=2541.695 pass_after=0 promoted_after=1 heavy_after=0
- code=049070 name=인탑스 last_backoff=2026-07-22T08:21:48.409054 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=-0.15 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2595.645 pass_after=0 promoted_after=0 heavy_after=0
- code=222800 name=심텍 last_backoff=2026-07-22T08:23:11.975489 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=-0.47 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2512.078 pass_after=0 promoted_after=0 heavy_after=0
- code=314930 name=바이오다인 last_backoff=2026-07-22T08:14:21.636883 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=-11.22 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3042.417 pass_after=0 promoted_after=0 heavy_after=0
- code=000880 name=한화 last_backoff=2026-07-22T08:07:15.407169 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=3468.646 pass_after=0 promoted_after=1 heavy_after=0
- code=004000 name=롯데정밀화학 last_backoff=2026-07-22T08:08:13.456828 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=3410.597 pass_after=0 promoted_after=1 heavy_after=0
- code=001040 name=CJ last_backoff=2026-07-22T08:09:06.994172 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3357.059 pass_after=0 promoted_after=0 heavy_after=0
- code=001530 name=DI동일 last_backoff=2026-07-22T08:09:10.554608 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3353.499 pass_after=0 promoted_after=0 heavy_after=0
- code=034730 name=SK last_backoff=2026-07-22T08:09:26.956984 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=3337.097 pass_after=0 promoted_after=1 heavy_after=0
- code=000990 name=DB하이텍 last_backoff=2026-07-22T08:09:26.962289 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=3337.091 pass_after=0 promoted_after=1 heavy_after=0
- code=082740 name=한화엔진 last_backoff=2026-07-22T08:10:56.824146 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3247.229 pass_after=0 promoted_after=0 heavy_after=0
- code=009420 name=한올바이오파마 last_backoff=2026-07-22T08:11:49.379887 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3194.674 pass_after=0 promoted_after=0 heavy_after=0
- code=003090 name=대웅 last_backoff=2026-07-22T08:12:24.484495 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3159.569 pass_after=0 promoted_after=0 heavy_after=0
- code=452430 name=사피엔반도체 last_backoff=2026-07-22T08:12:41.600503 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=True potential_loss=False state=active_or_recovered age_sec=3142.453 pass_after=0 promoted_after=1 heavy_after=0
- code=008060 name=대덕 last_backoff=2026-07-22T08:13:12.671927 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3111.382 pass_after=0 promoted_after=0 heavy_after=0
- code=006110 name=삼아알미늄 last_backoff=2026-07-22T08:13:12.675658 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3111.378 pass_after=0 promoted_after=0 heavy_after=0
- code=001430 name=세아베스틸지주 last_backoff=2026-07-22T08:13:33.554781 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3090.499 pass_after=0 promoted_after=0 heavy_after=0
- code=298020 name=효성티앤씨 last_backoff=2026-07-22T08:14:13.096475 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3050.957 pass_after=0 promoted_after=0 heavy_after=0
- code=394280 name=오픈엣지테크놀로지 last_backoff=2026-07-22T08:14:23.995309 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3040.058 pass_after=0 promoted_after=0 heavy_after=0
- code=397030 name=에이프릴바이오 last_backoff=2026-07-22T08:14:31.894198 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3032.159 pass_after=0 promoted_after=0 heavy_after=0
- code=488900 name=비츠로넥스텍 last_backoff=2026-07-22T08:14:31.907071 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3032.147 pass_after=0 promoted_after=0 heavy_after=0
- code=388210 name=씨엠티엑스 last_backoff=2026-07-22T08:14:38.972379 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=3025.081 pass_after=0 promoted_after=0 heavy_after=0
- code=001460 name=BYC last_backoff=2026-07-22T08:16:23.760865 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2920.293 pass_after=0 promoted_after=0 heavy_after=0
- code=306200 name=세아제강 last_backoff=2026-07-22T08:16:23.764998 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2920.289 pass_after=0 promoted_after=0 heavy_after=0
- code=000120 name=CJ대한통운 last_backoff=2026-07-22T08:16:23.770570 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2920.283 pass_after=0 promoted_after=0 heavy_after=0
- code=270660 name=에브리봇 last_backoff=2026-07-22T08:17:39.778849 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2844.275 pass_after=0 promoted_after=0 heavy_after=0
- code=200710 name=에이디테크놀로지 last_backoff=2026-07-22T08:18:01.463957 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2822.59 pass_after=0 promoted_after=0 heavy_after=0
- code=003030 name=세아제강지주 last_backoff=2026-07-22T08:18:19.814153 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2804.239 pass_after=0 promoted_after=0 heavy_after=0
- code=005500 name=삼진제약 last_backoff=2026-07-22T08:18:30.421285 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2793.632 pass_after=0 promoted_after=0 heavy_after=0
- code=402340 name=SK스퀘어 last_backoff=2026-07-22T08:19:17.286858 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2746.767 pass_after=0 promoted_after=0 heavy_after=0
- code=066570 name=LG전자 last_backoff=2026-07-22T08:19:17.287631 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2746.766 pass_after=0 promoted_after=0 heavy_after=0
- code=199430 name=케이엔알시스템 last_backoff=2026-07-22T08:19:33.691663 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2730.362 pass_after=0 promoted_after=0 heavy_after=0
- code=003570 name=SNT다이내믹스 last_backoff=2026-07-22T08:19:33.697151 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2730.356 pass_after=0 promoted_after=0 heavy_after=0
- code=455900 name=엔젤로보틱스 last_backoff=2026-07-22T08:21:48.405825 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2595.648 pass_after=0 promoted_after=0 heavy_after=0
- code=473980 name=노머스 last_backoff=2026-07-22T08:21:48.416272 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2595.637 pass_after=0 promoted_after=0 heavy_after=0
- code=494120 name=큐리오시스 last_backoff=2026-07-22T08:22:42.353827 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2541.7 pass_after=0 promoted_after=0 heavy_after=0
- code=003240 name=태광산업 last_backoff=2026-07-22T08:22:59.558706 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2524.495 pass_after=0 promoted_after=0 heavy_after=0
- code=002240 name=고려제강 last_backoff=2026-07-22T08:23:05.918645 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2518.135 pass_after=0 promoted_after=0 heavy_after=0
- code=005070 name=코스모신소재 last_backoff=2026-07-22T08:23:05.921839 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2518.132 pass_after=0 promoted_after=0 heavy_after=0
- code=017800 name=현대엘리베이터 last_backoff=2026-07-22T08:24:44.606648 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2419.447 pass_after=0 promoted_after=0 heavy_after=0
- code=077970 name=STX엔진 last_backoff=2026-07-22T08:25:10.006528 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2394.047 pass_after=0 promoted_after=0 heavy_after=0
- code=486990 name=노타 last_backoff=2026-07-22T08:25:10.015780 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=2394.038 pass_after=0 promoted_after=0 heavy_after=0
- code=015760 name=한국전력 last_backoff=2026-07-22T08:34:59.945918 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1804.108 pass_after=0 promoted_after=0 heavy_after=0
- code=389650 name=넥스트바이오메디컬 last_backoff=2026-07-22T08:35:27.979556 reason=scanner_ws_stale_backoff_active source=ws_stale_feedback max_delta_after=0.0 recovered_eval=False potential_loss=False state=mature_unrecovered age_sec=1776.074 pass_after=0 promoted_after=0 heavy_after=0

## Latency False Negative Review


## Latency False Negative Canary Candidates


## TP1 Counterfactual First-hit Labels

- ts=2026-07-22T08:08:41.131938 code=460930 name=현대힘스 selector=rising_missed_tp1_hard_negative_evidence action=HARD_VETO_EXPECTED risks=['spread_above_candidate_caution', 'momentum_support_weak'] label=gross_target_first entry=12765.0 source=ka10004_rest_orderbook ws_age_ms=52.244 rest_age_ms=0.0 gap_bps=3.917 spread=0.00235 true_ofi=0.16593035137271636 pressure=69.30431917789306 depth=0.3860863835578612 tick_accel=0.0 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:19:14.671326 code=307950 name=현대오토에버 selector=rising_missed_tp1_insufficient_positive_support action=RECHECK_REQUIRED risks=['spread_above_candidate_caution', 'pressure_below_prior', 'depth_support_weak', 'momentum_support_weak', 'wait_without_bid_imbalance'] label=adverse_stop_first entry=412000.0 source=ws ws_age_ms=0.0 rest_age_ms=0.0 gap_bps=6.064 spread=0.00605 true_ofi=0.009530476392230196 pressure=37.580879211726575 depth=-0.24838241576546874 tick_accel=0.0 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:19:21.795044 code=307950 name=현대오토에버 selector=rising_missed_tp1_insufficient_positive_support action=RECHECK_REQUIRED risks=['spread_above_candidate_caution', 'true_ofi_nonpositive', 'pressure_below_prior', 'depth_support_weak', 'wait_without_bid_imbalance'] label=no_hit_within_20m entry=411000.0 source=ws ws_age_ms=0.0 rest_age_ms=0.0 gap_bps=6.083 spread=0.007282 true_ofi=-0.060429896626135696 pressure=35.359664578340215 depth=-0.29280670843319595 tick_accel=1.474938 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:19:26.354296 code=307950 name=현대오토에버 selector=rising_missed_tp1_lane_not_eligible action=HARD_VETO_EXPECTED risks=['spread_above_candidate_caution', 'pressure_below_prior', 'depth_support_weak', 'momentum_support_weak', 'wait_without_bid_imbalance'] label=no_hit_within_20m entry=410000.0 source=ws ws_age_ms=0.0 rest_age_ms=0.0 gap_bps=12.18 spread=0.00729 true_ofi=0.008743542558601316 pressure=32.80665263882727 depth=-0.34386694722345473 tick_accel=0.977409 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:19:34.764745 code=307950 name=현대오토에버 selector=tp1_micro_ws_unavailable action=INPUT_DEFER_EXPECTED risks=['true_ofi_nonpositive', 'pressure_below_prior', 'depth_support_weak', 'momentum_support_weak', 'wait_without_bid_imbalance'] label=no_hit_within_20m entry=410750.0 source=ka10004_rest_orderbook ws_age_ms=4591.847 rest_age_ms=0.0 gap_bps=18.259 spread=0.001217 true_ofi=-0.07629843667881321 pressure=33.61701934739805 depth=-0.3276596130520393 tick_accel=0.0 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:19:52.555700 code=307950 name=현대오토에버 selector=rising_missed_tp1_lane_not_eligible action=RECHECK_REQUIRED risks=['spread_above_candidate_caution', 'pressure_below_prior', 'depth_support_weak', 'momentum_support_weak', 'wait_without_bid_imbalance'] label=no_hit_within_20m entry=410000.0 source=ws ws_age_ms=0.0 rest_age_ms=0.0 gap_bps=0.0 spread=0.006079 true_ofi=0.003740139489521414 pressure=34.836155510968034 depth=-0.30327688978063966 tick_accel=0.716897 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:19:58.360505 code=307950 name=현대오토에버 selector=rising_missed_tp1_lane_not_eligible action=HARD_VETO_EXPECTED risks=['spread_above_candidate_caution', 'pressure_below_prior', 'depth_support_weak', 'momentum_support_weak', 'wait_without_bid_imbalance'] label=no_hit_within_20m entry=410000.0 source=ws ws_age_ms=0.0 rest_age_ms=0.0 gap_bps=6.094 spread=0.006079 true_ofi=0.012383126256552987 pressure=35.25829749663598 depth=-0.2948340500672805 tick_accel=0.548033 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:20:07.347486 code=307950 name=현대오토에버 selector=rising_missed_tp1_lane_not_eligible action=RECHECK_REQUIRED risks=['spread_above_candidate_caution', 'pressure_below_prior', 'depth_support_weak', 'momentum_support_weak', 'wait_without_bid_imbalance'] label=no_hit_within_20m entry=409000.0 source=ws ws_age_ms=0.0 rest_age_ms=0.0 gap_bps=18.304 spread=0.007308 true_ofi=0.003986681866397051 pressure=38.47455278765109 depth=-0.2305089442469782 tick_accel=0.637877 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:20:15.027191 code=307950 name=현대오토에버 selector=rising_missed_tp1_hard_negative_evidence action=HARD_VETO_EXPECTED risks=['spread_above_candidate_caution', 'pressure_below_prior', 'depth_support_weak', 'wait_without_bid_imbalance'] label=no_hit_within_20m entry=410000.0 source=ws ws_age_ms=0.0 rest_age_ms=0.0 gap_bps=6.098 spread=0.006086 true_ofi=0.001229037283041771 pressure=42.90538061582389 depth=-0.14189238768352247 tick_accel=1.05277 micro_state=fresh_ws_order_flow_delta
- ts=2026-07-22T08:24:41.345022 code=483650 name=달바글로벌 selector=rising_missed_tp1_insufficient_positive_support action=RECHECK_REQUIRED risks=['spread_above_candidate_caution', 'true_ofi_nonpositive', 'pressure_below_prior', 'depth_support_weak', 'momentum_support_weak', 'wait_without_bid_imbalance'] label=no_hit_within_20m entry=236500.0 source=ws ws_age_ms=0.0 rest_age_ms=0.0 gap_bps=10.571 spread=0.010515 true_ofi=-0.07871632431631492 pressure=46.13699219332214 depth=-0.07726015613355737 tick_accel=0.0 micro_state=fresh_ws_order_flow_delta

## First Touch Regression


## Records
