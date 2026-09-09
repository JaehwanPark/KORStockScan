# 2026-09-09 장후 안전 수리 검증과 native intake 판정

## 검증 범위

- 사용자 명시 장후 모니터링의 source-only 복구/추천 검토. 매매 process·주문·custody·env·lock·threshold·provider·수량·target은 변경하지 않았다.
- 원천 세대: source9/9, 22:31~22:32 native74행, source12개. [Pass1 원장](2026-09-09-postclose-native-intake-pass1.json)에 owner/ID/행·원천 hash/결손 필드를 보존했다. 전체 canonical source는 `/tmp/korstockscan-postclose-recovery-20260909.XQD48N/pass1/home/ubuntu/KORStockScan/data/report/`에 복사 보존했다. tmp 이름으로 삭제하지 않는다.

## 코드 수리·검증 (22:33)

1. Source-quality workorder base의 `allowed_runtime_apply=False` 누락 수리. native ID/attach_existing_family/기존 격리 이력을 유지하고 실제 non-selected serialize→strict validator 회귀를 추가했다. main22:06 실패 후22:15 strict summary PASS, controller/follower22:25:46 DONE으로 직접 소비를 확인했다. 실제 격리의 원본 gzip/manifest는 유지한다.
2. Sentinel의 `blocked_gap_from_scan`은 명시적 baseline_prior_feature/source_quality_only/risk_context_only와 False 권한에 한해 인과 terminal에서 제외하고 관찰 수를 남긴다. 모순·unknown·null·임의 다른 blocked stage는 기존 결손을 유지한다. 기존 PipelineEvent의 str(bool) 캐시 경계까지 테스트했다. 첫 canonical 재생성에서 캐시 문자열 때문에 효과가 없음을 발견해 보완·재리뷰했다. 최종 같은 as-of19:20:05/KRX1111 attempt의 unclassified7→0, classified1104→1111, 관찰16이며 제출0이다. 기존 보고의 missing-key1→0은 audit 이후 cache/summary 원천 재대사 차이로 별도 보존하며 이7건 코드 수리의 효과나 과거 identity 복원으로 귀속하지 않는다.
3. EV는 count 일치라도 snapshot PnL을 실현손익 headline으로 사용하지 않는다. exact 비용 대사가 없는 headline은 null이고 원 status와 snapshot 값은 진단에 남긴다. 첫 출력 요약의 jq가 import banner를 파싱하지 못해 BrokenPipe/exit5가 발생했으며 stdout 전체를 소비하는 동일 CLI로 재실행하여 exit0과 파일을 확인했다. producer 전략 계산 실패나 첫 실패의 소급 성공으로 처리하지 않는다.
4. Controller follower는 fixed runner lock 해제 직후 batch/consumer terminal을 새로 읽는다. 완료된 경우 skip, 계속 미완료면 기존 bounded runner로 진행하는 shell 회귀를 추가했다.22:20 경계에서 실제로 발생한 불필요한 두 번째 실행은 당시 기록이며 코드 수리로 실행 사실을 지우지 않는다. 기존 wrapper 종료 후 수정했고, 다음 자연 race 검증은 별도다. 이번 복구 완료를 위해 추가 Provider replay를 실행하지 않는다.

검증: Sentinel/cache/EV/tower132건, workorder/runtime-summary/intake207건, raw-row strict12건, controller/follower wrapper6건 PASS. compile, bash -n, git diff --check와 print-only parser44행 PASS. 서로 겹치는 부분 실행16건을 별도 합산하지 않는다. 직접 producer/consumer·필드 null/false·원천 hash·nonblocking/unknown·full/partial 및 권한 경계를 재리뷰했고 수정 범위의 미해결 finding0이다. 남은 원천/경제성/권한 차단을 이 finding0으로 완료하지 않는다.

| 수정 코드 | SHA256 |
| --- | --- |
| buy_funnel_sentinel.py | `d5067f5c0477cc5e26ecd9014748b7499696ffb50e9156634fd7c041118d6525` |
| threshold_cycle_ev_report.py | `3cfb27789ccac405518f5c1118824b53234e4d7a4be8c058c8d4ab99f062ecb1` |
| build_code_improvement_workorder.py | `88d83eaf83ca75c8b0e852939afa56a07e62bd54f1a2cb965959c647db0304f5` |
| run_postclose_done_controller.sh | `df0f8747f7af4fac43bd1f61901e1bbec0de04450d931ee55a627a158a1d92ac` |

## 직접 결과와 경제성 경계

- Sentinel SHA256 `4152ac14b0a4dcb07e05eb2d20503065043065016fcd7cbd6ca88daed22750b7`; recheck `89289b471453776668b111fc1b97044d2743fffe97a4888ec22dfe9108f1e7f1`; EV `fb9945296ec3b29b8497ffb1b64ad7245476b7489a35cfc0078c56abb5b83454`. Recheck critical_day2/activation=false/desired=false/stop=drought_history_source_quality_gap이며9/7 구 schema를 현재 evidence로 바꾸지 않았다. Drought는 여전히 critical/실제submit0이다.
- Widget evaluation22:11:40 Result=success/네 단계 완료.9/9 source→9/10 dated policy verified,080220 selected/006800·010140·475150 withheld. 이는 기존 자동 계약의 발행 결과이지 trader 새 기동·정책 PID 소비·실수익의 완료가 아니다.
- Machine22:11:40~22:25:34 6단계 exit0. attribution109 anchors/matched0, timing actual-entry18/eligible0,35cohort4군 각각 paired0, baseline_immediate_entry_carry_forward/target9/10 scopes0. 마지막 epoch의 exact pre-enqueue receipt20과 당일 전체 원천 승인은 다르다. source exclusion manifest7scope는 과거8월이며9/9 오전 epoch 유실을 닫지 않는다. 현재 validator의 regression-only 계약에 단순 예외를 넣어 전체 날짜를 통과시키지 않는다. `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0908`와 `MachineLifecycleTurnoverObjectiveFollowup0909`에서 epoch별 원천/census·반영/정책·경제성을 구분한다.
- Adaptive-exit 연구 rows30/scope162는 비용 후 pair가 아니다. blocked_source_contract/not_evaluated, next=`bind_first_fill_lot_epoch_and_ordered_post_target_path_before_execution_replay`. 별도 numeric envelope/launcher/승인/주문 owner 미완료를 유지한다.

## Native 전수 disposition 근거

latest intake74=요청15+비요청59, 요청15=source-only15.13요청은 아래 명시 consumer/위치 결손이며 추정 구현하지 않는다. 두 새 prompt 초안은 parent V2.14 보존·영문 부록 내용/반례/비권한성을 검토했으나, 각각13건/2건의 cost_evidence가 모두 source_unavailable이다. source9/8·9/9의 후행 비용을 합성하거나 검증된 새 prompt 버전·동일부모 비용 비교 완료로 발표하지 않는다. 기존 AIDecisionActionOutcomeNaturalEvidence0908에서 exact payload/outcome/cost와 버전/hash 검토를 연결한다. 전세대7사례 ID는 superseded 이력이지 추가 고유 작업이 아니다.

아래 전수 행은 구현 완료가 아니라 현 세대의 판정이다. companion의 blocked receipt와 후행 strict는 별도로 대사한다. 변경 없는 기존 관찰/보류/거절은 코드 수리를 열지 않는다.

| Owner / native ID | 원 decision | 최종 disposition / 직접 사유 |
| --- | --- | --- |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:0bdfc39c76573e968028e3e36bea0f840b8249c225566ea71ae456c3c248b563` | `source_only_requires_review_and_user_approval` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:2c12077e277ea743fbc2add1007b002a6d0fd3412fc31fa51a91d064914412d8` | `source_only_requires_review_and_user_approval` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:3287c340cabe4b868a3283e957a49c5ae5bf8494fb936d371c8bd5f20b934400` | `null` | `blocked_missing_evidence` — missing implementation_location |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:3bc85678dbc2764e53d5f6cad6f7260a6d89c4c3bee03a285e3e1833d339cfe6` | `recommend_cumulative_logic_candidate_review` | `blocked_missing_evidence` — missing implementation_location |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:6f447ce5aec156daf03395cbc89a91f2d8c97e715fbe67245965d37bda05fe9d` | `source_only_requires_review_and_user_approval` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:9b2e7d6953b3f4baf6c727f181d09d434099204ed42ebf818b77c22b54e1f128` | `source_only_requires_review_and_user_approval` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:ddd325314a2acd64163c73098992259186175a6adc9ef54e26ce99dca713eaa1` | `source_only_requires_review_and_user_approval` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:e258b542608904b9402438aa95401da37c96bed038129ab4d2cd6acaeb4d80c5` | `source_only_requires_review_and_user_approval` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| low_price_two_leg_expanded_candidate_research / `low_price_two_leg_expanded_candidate_research:fd2ddd6ce29e85a68adb8327292d8aef75d33ed1d2f0770aeb7c7e3aeaa546be` | `source_only_requires_review_and_user_approval` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| machine_microstructure_attribution / `machine_lifecycle_turnover_policy_research_v1` | `EVIDENCE_ACCUMULATING` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_ai_threshold_miss_ev_recovery` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_budget_pass_without_submit` | `design_family_candidate` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_conversion_lane_submit_drought_submit_drought_entry_ai_authority_revalidation` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_conversion_lane_submit_drought_submit_drought_latency_pre_submit` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_conversion_lane_submit_drought_submit_drought_price_revalidation` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_conversion_lane_submit_drought_submit_drought_upstream_gate` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_entry-prompt-revision-8d1f2fb1740c1769eec7ede1` | `implement_now` | `blocked_missing_evidence` — verified exact cost evidence absent (all source_unavailable); no reviewed new-version contract |
| main / `order_entry-prompt-revision-f7e1931a9128531084ba87ac` | `implement_now` | `blocked_missing_evidence` — verified exact cost evidence absent (all source_unavailable); no reviewed new-version contract |
| main / `order_entry_broker_receipt_contract_gap_review` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_entry_fill_quality_contract_gap_review` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_entry_post_submit_contract_gap_review` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_entry_recheck_bounded_maintenance_review` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_entry_recheck_history_transition_review` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_entry_source_taxonomy_contract_gap_review` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_entry_submit_drought_auto_resolution` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_entry_telegram_post_submit_contract_gap_review` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_latency_guard_miss_ev_recovery` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_market_census_krx_krx_regular` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_market_census_nxt_nxt_aftermarket` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_market_census_nxt_nxt_premarket` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_market_census_nxt_nxt_regular_overlap` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_microstructure_v3_evaluation_anchor_contract_missing` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_microstructure_v3_evaluation_venue_missing_or_conflicting` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_microstructure_v3_required_holding_payload_missing` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_observation_source_quality_raw_row_exclusion_producer_gap` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_observation_source_quality_unknown_token_provenance_gap` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_one_share_threshold_ai_score_near_buy_entry_hook_review` | `implement_now` | `blocked_missing_evidence` — missing consumer, implementation_location |
| main / `order_one_share_threshold_strength_momentum_vpw_entry_hook_review` | `implement_now` | `blocked_missing_evidence` — missing consumer, implementation_location |
| main / `order_overbought_gate_miss_ev_recovery` | `design_family_candidate` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_panic_sell_defense_lifecycle_transition_pack` | `attach_existing_family` | `invalid_or_missing_authority` — allowed_runtime_apply strict false missing; no inferred authority |
| main / `order_partial_fill_quality_source_attribution` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_ai_review_followup_2026_09_09` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_active_source_forbidden_terms` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_claude_empty_trade_fact_overwrite_guard` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_claude_scalping_manifest_freshness` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_claude_scalping_metric_contract` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_claude_scalping_observability_metric_contract` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_claude_scalping_observability_source_contract` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_claude_small_net_generation_contract` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_pattern_lab_ai_review_contract` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pattern_lab_ai_review_currentness_scalping_ldm_threshold_reentry_sources` | `defer_evidence` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_pipeline_event_compaction_v2_shadow` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_rising_missed_classifier_prior_bridge` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_rising_missed_classifier_prior_feedback_bridge` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_rising_missed_entry_turn_bbo_coverage` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_same_symbol_repeat_source_attribution` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_scanner_eligible_no_heavy_closed_loop` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_scanner_funnel_executable_bbo_join` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_scanner_scan_generation_conservation_gap` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_split_entry_rebase_수량_정합성_report_only_감사` | `attach_existing_family` | `observed_no_patch` — existing native decision preserved; no live mutation/economic completion implied |
| main / `order_ws_decision_stage_stale_backoff_attribution` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_ws_total_stale_escalation` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| main / `order_ws_trade_tick_quiet_low_liquidity_classification` | `implement_now` | `blocked_missing_evidence` — missing consumer |
| widget_collector_expansion_recommendation / `widget_collector_expansion_recommendation:1876a96dff2b6afebb1f445538c9a487def36028174fe64880e497c68d19745a` | `research_watch` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| widget_collector_expansion_recommendation / `widget_collector_expansion_recommendation:1ed187a6c7bf27db9dd41bb361c3005e4bc961b64036fa65e2159e926ed22322` | `research_watch` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| widget_collector_expansion_recommendation / `widget_collector_expansion_recommendation:2eaf06787075f5631a2790102165df3f4813b7c8778c2d1e0bd34d9d264c9334` | `research_watch` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| widget_collector_expansion_recommendation / `widget_collector_expansion_recommendation:519bad7f319ed282a6130f6ef2c55cc353c5cbf7f1de96bea8e07b8448bef3e3` | `research_watch` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| widget_collector_expansion_recommendation / `widget_collector_expansion_recommendation:7ff28758a02a80ced86c9d279c6b46cb0b02a95a5eb6186245551a68d8ee66d2` | `research_watch` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| widget_collector_expansion_recommendation / `widget_collector_expansion_recommendation:d3845195b73790a6428270bb61f84eaaa065879844b08240e9995643f52e2b88` | `research_watch` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| widget_collector_expansion_recommendation / `widget_collector_expansion_recommendation:eb4436766d789ebf29bbd6af11c61eee7341b44a041c5d4280403a6291d009f2` | `research_watch` | `deferred` — existing native decision preserved; no live mutation/economic completion implied |
| widget_symbol_signal_policy_research / `widget_symbol_signal_policy_research:1a6aebfa63c42f751b0242e3e18a558d326ca01f58eb3055c6b699316120f216` | `holdout_failed_no_widget_runtime_promotion` | `rejected` — existing native decision preserved; no live mutation/economic completion implied |
| widget_symbol_signal_policy_research / `widget_symbol_signal_policy_research:2991bcc69c56990b25c4b08aaf4fdd60e5d3173a67c6592ec632d5328db3c16d` | `holdout_failed_no_widget_runtime_promotion` | `rejected` — existing native decision preserved; no live mutation/economic completion implied |
| widget_symbol_signal_policy_research / `widget_symbol_signal_policy_research:814eab726593d89d0288fe3ad6a3d6fcb3d3dbc4fe5a1d6dff5ca6d17b32d0a0` | `holdout_failed_no_widget_runtime_promotion` | `rejected` — existing native decision preserved; no live mutation/economic completion implied |
| widget_symbol_signal_policy_research / `widget_symbol_signal_policy_research:f4ef9259aaa1ee8420d52ce4303595054ec87d2981b617f425739820921042b3` | `holdout_pass_widget_signal_policy_candidate` | `blocked_missing_evidence` — missing implementation_location |
