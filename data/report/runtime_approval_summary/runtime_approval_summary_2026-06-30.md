# Runtime Approval Summary - 2026-06-30

- 목적: 스캘핑 threshold-cycle 판정과 스윙 runtime approval 판정을 한 화면에서 보는 읽기 전용 요약이다.
- runtime_mutation_allowed: `False`
- scalping_items/selected: `20` / `3`
- scalping_legacy_hard_gate_risk_counts: `{'approval_or_contract_required': 1, 'intentional_safety_guard': 4, 'manual_review_required': 2, 'no_unreviewed_hard_gate': 13}`
- swing_blocked/requested/approved: `12` / `0` / `0`
- swing_legacy_archive/phase0_ignored: `0` / `0`
- swing_legacy_hard_gate_risk_counts: `{'contract_gap': 4, 'no_unreviewed_hard_gate': 2, 'same_stage_deferred': 2, 'sample_or_contract_gap': 1, 'source_quality_or_contract_gap': 3}`
- panic_approval_requested: `0`
- scalp_entry_adm_status: `warning`
- lifecycle_matrix_status: `pass`
- lifecycle_bucket_windows_promotion: `pass` / `target_pass`
- lifecycle_ai_context prompt/applied: `3` / `330`
- swing_strategy_discovery_labeled/pending: `1254` / `3962`
- swing_lifecycle_matrix_auto: `21`
- swing_lifecycle_bucket_auto: `21`
- institutional_flow_available/join_rate: `True` / `100.0`
- microstructure_reaction_available/ok: `True` / `2265`
- pattern_lab_currentness_status: `pass`
- pattern_lab_ai_review_status: `pass`
- producer_gap_discovery_status: `pass`
- pattern_lab_propagation_status: `warning`
- env_generated_at: `2026-06-30T15:57:56`
- first_bot_start_at: `2026-06-30T07:55:02`
- first_bot_start_after_env_at: `2026-06-30T15:58:18`
- pre_env_boot_gap: `True`

## Microstructure Reaction Context
- available: `True`
- authority: `entry_confidence_modifier_source_only`
- rows ok/missing: `2265` / `4218`
- real_submitted_count: `39`
- status_counts: `{'insufficient_window': 23, 'not_evaluated': 877, 'ok': 2265, 'source_quality_missing': 12, 'stale': 3306}`
- entry_reaction_quality_counts: `{'favorable_reaction': 45, 'mixed_reaction': 613, 'neutral_unusable': 4218, 'risk_context_only': 576, 'weak_reaction': 1031}`
- avg_scores ask/hold/bid: `45.284` / `49.861` / `55.848`
- max_vi_proximity_risk: `53`
- warnings: `[]`

## Scalping
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `soft_stop_whipsaw_confirmation` | soft stop 직후 반등 가능성이 큰 표본은 1회 확인 시간을 두고 성급한 청산을 줄이는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `selected_runtime_canary` | threshold-cycle selected family attribution | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | `-` | auto_bounded_live 선택 |
| `holding_flow_ofi_smoothing` | 보유/청산 AI flow 결과에 OFI/QI 미시수급을 붙여 EXIT 확정 또는 보류를 다듬는 축 | 기존 적용 유지: holding_flow_override 내부 OFI/QI postprocessor ON | `hold` | `existing_runtime_guard` | holding/exit EV attribution | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `protect_trailing_smoothing` | protect/trailing 청산 후보에서 미시 반등 신호가 있으면 과조기 청산을 줄이는 축 | 관찰/리포트 only: protect/trailing live smoothing 미적용 | `adjust_down` | `report_only_holding_exit_candidate` | report-only until approval/rollback guard | 자동 반영 후보로 선택되면 PREOPEN env에 적용된다 | 1 | `-` | - |
| `trailing_continuation` | trailing 이후 추가 상승 여지가 큰 표본을 계속 보유할 수 있는지 보는 축 | 관찰/리포트 only: trailing 연장 live 미적용 | `freeze` | `holding_exit_safety_freeze` | source-quality and GOOD_EXIT risk review | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 1 | `-` | 동결 |
| `market_regime_continuous_thresholds` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.7 | `-` | 표본 부족 |
| `pre_submit_price_guard` | broker 제출 직전 quote stale, spread, passive probe 가격품질 문제를 막는 hard safety 축 | 기존 적용/검증 유지: 제출 직전 hard safety guard이며 auto_bounded_live 후보 아님 | `hold` | `intentional_pre_submit_safety_guard` | safety/source-quality report only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 0 | `-` | 유지 |
| `dynamic_entry_price_resolver` | bid-1/bid-2/bid-3/best_bid/AI/reference/timeout 후보별 체결품질과 EV를 비교하는 진입가 튜닝 축 | 선택 시 다음 PREOPEN dynamic entry price resolver env만 bounded 적용, submit safety guard 우선 | `hold_sample` | `entry_price_bounded_tunable` | threshold-cycle candidate fill/cancel/late-fill/source-quality adjusted EV attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | counterfactual join gap, recovery floor 미달 |
| `entry_price_execution_quality` | real-only 제출/체결/취소/late-fill/partial/full fill 품질을 감사하는 실행품질 축 | real-only audit: submit/fill/cancel 품질 기록만 수행, runtime threshold apply 권한 없음 | `hold` | `real_execution_quality_audit` | real-only submit/fill/cancel/late-fill audit | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `score65_74_recovery_probe` | family id는 score65_74로 유지하지만 현 runtime floor 기준 AI 점수 60~74 WAIT 구간 중 수급/가속 조건이 좋은 후보를 기본 신규 BUY sizing으로 회수하는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `hold` | `entry_unlock_probe` | runtime env/operator lock plus post-apply attribution | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | `-` | auto_bounded_live 선택 |
| `strength_momentum_soft_gate_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_gate` | AI/counterfactual risk context, source-quality exception only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `overbought_pullback_guard_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_plus_pre_submit_guard` | overbought risk bucket EV and pre-submit guard attribution | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `liquidity_pre_submit_guard_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_plus_pre_submit_guard` | liquidity risk bucket EV and real submit guard attribution | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `bad_entry_refined_canary` | 진입 직후 never-green/AI fade 위험이 큰 표본을 조기 정리할 수 있는지 보는 축 | OFF/관찰 only: refined canary live 미적용 | `adjust_up` | `entry_quality_canary` | bad-entry cohort EV and rollback guard | 자동 반영 후보로 선택되면 PREOPEN env에 적용된다 | 1 | `-` | - |
| `holding_exit_decision_matrix_advisory` | 보유 중 가능한 행동(EXIT/HOLD/AVG_DOWN/PYRAMID)을 matrix 점수로 보조 판단하는 축 | 관찰/리포트 only: advisory live 적용 아님 | `hold_no_edge` | `advisory_report_only` | report-only decision support contract | 명확한 edge가 없어 runtime 변경은 하지 않는다 | 0 | `-` | edge 부족 |
| `scale_in_price_guard` | 추가매수 직전 best bid/defensive limit, spread, stale quote로 가격품질을 보장하는 축 | 기존 적용 유지: 추가매수 가격품질 guard ON | `hold` | `intentional_pre_submit_safety_guard` | scale-in price quality EV/source-quality only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `position_sizing_dynamic_formula` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `candidate_grid_comparison_runtime_apply_blocked` | candidate grid comparison -> PREOPEN bounded candidate -> postclose attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | 소스 표본 없음 |
| `scalp_entry_action_decision_matrix_advisory` | 스캘핑 entry action(BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE 등)을 matrix EV로 비교해 AI action을 보정하는 운영 override 축 | 운영 override runtime bias: AI BUY를 WAIT/DROP 또는 defensive bias로 보정, submit safety guard 우선 | `hold_sample` | `entry_adm_runtime_bias_operator_override` | daily scalp_entry_action_decision_matrix -> threshold EV/runtime summary/workorder/pattern lab -> next runtime env | 운영 override runtime bias는 AI BUY를 WAIT/DROP 또는 defensive bias로 보정한다. daily action bucket EV와 runtime forced_action provenance가 충분해야 다음 env 튜닝 판단으로 넘어간다. | 없음 | `-` | 표본 부족 |
| `lifecycle_decision_matrix_runtime` | 개별 후보 lifecycle row를 entry/submit/holding/scale-in/exit stage별 weighted ADM policy로 해석하는 umbrella runtime 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `umbrella_weighted_adm_runtime_policy` | postclose lifecycle_decision_matrix -> threshold EV/runtime summary -> next preopen bounded env | 선택 시 policy file/version만 다음 PREOPEN env로 연결한다. hard safety와 broker/account/order guard는 항상 matrix proposal보다 우선한다. | 1.0188 | `-` | auto_bounded_live 선택 |
| `latency_classifier_runtime_profile` | latency SAFE/CAUTION/DANGER classifier와 bounded submit recovery canary를 분리 적용하는 진입 실행품질 축 | 보류: 최신 recommendation 기준 다음 PREOPEN latency env 변경 없음 | `hold_sample` | `entry_execution_quality_bounded_tunable` | threshold-cycle latency audit plus post-apply latency_pass/order_bundle attribution | SAFE/CAUTION은 slippage check 후 normal submit으로 보내고, DANGER/stale/broker safety만 submit 차단으로 유지한다. | 0 | `-` | latency semantics gap |
| `scalp_sim_overnight_ai_carry` | 장마감 후 open 스캘핑 sim 포지션을 overnight_v1로 SELL_TODAY/HOLD_OVERNIGHT 분리해 다음날 lifecycle/EV label로 연결하는 source-only 축 | source-only: sim 가상 청산/carry 기록만 수행, runtime threshold apply 권한 없음 | `observe_only` | `not_classified` | manual runtime approval review | runtime_effect=false source다. SELL_TODAY는 sim 가상 청산, HOLD_OVERNIGHT는 active_unrealized carry로만 남긴다. | - | `-` | 관찰 전용 |

## Scalp Entry ADM
- status: `warning`
- runtime_bias_scope: `force_wait_force_drop_buy_defensive_bias`
- joined_action_ev_pct: `0.1461`
- joined_sample/sample_floor: `13` / `20`
- prompt_applied_count: `93`
- missing_actions: `[]`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 18, 'joined_sample': 2, 'source_quality_adjusted_ev_pct': 0.1461}, {'action': 'WAIT_REQUOTE', 'sample_count': 22, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_STALE', 'sample_count': 9, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 57, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 129, 'joined_sample': 7, 'source_quality_adjusted_ev_pct': -0.0095}]`
- ready_for_daily_policy_tuning: `False`
- warnings: `['joined_sample_below_sample_floor', 'unknown_bucket_source_quality_gap']`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-06-30.json`
- authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 1011281, 'foreign_net_roll5': 0, 'inst_net_roll5': 4186756, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '018000', 'smart_money_net': 696314, 'foreign_net_roll5': 853738, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '093370', 'smart_money_net': 566635, 'foreign_net_roll5': 336275, 'inst_net_roll5': 17905, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '036930', 'smart_money_net': 416204, 'foreign_net_roll5': 170855, 'inst_net_roll5': 1031589, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '009150', 'smart_money_net': 338053, 'foreign_net_roll5': 299247, 'inst_net_roll5': 198721, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '025320', 'smart_money_net': 282881, 'foreign_net_roll5': 0, 'inst_net_roll5': 347199, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '006800', 'smart_money_net': 118826, 'foreign_net_roll5': 1275464, 'inst_net_roll5': 3277001, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '290690', 'smart_money_net': 105031, 'foreign_net_roll5': 138004, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '281820', 'smart_money_net': 103826, 'foreign_net_roll5': 0, 'inst_net_roll5': 212434, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '153890', 'smart_money_net': 62002, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}]`
- warnings: `[]`

## Lifecycle Decision Matrix
- status: `pass`
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-30`
- runtime_bias_scope: `stage_action_proposal_micro_canary`
- total/joined/floor: `5831` / `3233` / `20`
- policy_pass/promote_ready: `5` / `1`
- lifecycle_flow buckets/complete/runtime/workorders: `77` / `10` / `0` / `20`
- holding/exit buckets: `25` / `43`
- holding/exit workorders: `8` / `10`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0018`
- incomplete_flow_reason_counts: `{'missing_exit': 3232, 'missing_entry': 5299, 'missing_holding': 5432, 'missing_submit': 5407, 'postclose_exit_without_entry': 2236, 'candidate_id_only': 5340, 'scale_in_noise_only': 3036, 'sim_record_id_only': 54}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- ready_for_bounded_apply: `True`
- warnings: `[]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-30_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 32, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 161, 'absorbed_sample_count': 18704, 'child_conflict_warning_count': 7, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-30_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 41, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 349, 'absorbed_sample_count': 40285, 'child_conflict_warning_count': 16, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-30_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 39, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 500, 'absorbed_sample_count': 212611, 'child_conflict_warning_count': 17, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`
- warnings: `['lifecycle_bucket_discovery:source_contract_drift_warning']`

## Lifecycle AI Context
- context_artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-06-30.json`
- context_version: `lifecycle_ai_context_v1_2026-06-30`
- prompt_stage_count: `3`
- attribution_artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-06-30.json`
- attribution eligible/applied/skipped: `330` / `330` / `0`
- stage_attribution: `{'entry': {'context_contribution_score': -0.2948, 'bounded_auxiliary_weight': -0.0442, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0788, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Swing
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `swing_model_floor` | 스윙 추천 모델 floor 값을 올리거나 낮출 수 있는지 보는 선택 기준 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `approval_route_available` | swing_runtime_approvals artifact -> next PREOPEN dry-run env | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.6883 | `-` | 표본 부족, 심각한 하방위험 guard |
| `swing_selection_top_k` | 스윙 추천 후보 수(top-k)를 늘리거나 줄일 수 있는지 보는 선택 폭 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `same_stage_deferred_selection_axis` | same-stage owner conflict 해소 후 approval route | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.6883 | `-` | 표본 부족, 심각한 하방위험 guard |
| `swing_gatekeeper_accept_reject` | 스윙 gatekeeper가 accept/reject한 후보의 후행 성과를 비교하는 진입 판단 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `legacy_hard_gate_contract_gap` | workorder로 accept/reject policy guard를 만들거나 reject cooldown family로 우회 조정 | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.655 | `-` | 표본 부족, 심각한 하방위험 guard, runtime guard 없음 |
| `swing_gatekeeper_reject_cooldown` | gatekeeper reject 이후 같은 후보를 다시 볼 cooldown 시간을 조정하는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `approval_route_available` | ML_GATEKEEPER_REJECT_COOLDOWN approval/env route | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.655 | `-` | 표본 부족, 심각한 하방위험 guard |
| `swing_market_regime_sensitivity` | 시장 regime에 따라 스윙 진입 민감도를 완화/강화할지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `same_stage_deferred_entry_axis` | same-stage owner conflict 해소 후 SWING_MARKET_REGIME_SENSITIVITY route | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.655 | `-` | 표본 부족, 심각한 하방위험 guard |
| `swing_pyramid_trigger` | 스윙 보유 후 불타기(PYRAMID) 조건이 유효한지 보는 추가매수 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `runtime_contract_gap_scale_in_axis` | scale-in runtime guard/workorder before approval | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.655 | `-` | 표본 부족, 심각한 하방위험 guard, runtime guard 없음 |
| `swing_avg_down_eligibility` | 스윙 보유 후 물타기(AVG_DOWN) 조건이 유효한지 보는 추가매수 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `runtime_contract_gap_scale_in_axis` | policy/workorder first; final full-live approval path only after complete LDM parent evidence | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.655 | `-` | 표본 부족, 심각한 하방위험 guard, runtime guard 없음 |
| `swing_trailing_stop_time_stop` | 스윙 trailing/time stop 청산 조건의 적정성을 보는 exit 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `runtime_contract_gap_exit_axis` | exit runtime guard/workorder before approval | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.755 | `-` | 심각한 하방위험 guard, runtime guard 없음 |
| `swing_holding_flow_defer` | 스윙 보유/청산 AI가 청산 보류를 결정한 뒤 성과가 개선되는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `source_quality_and_runtime_contract_gap_holding_axis` | hold-defer component decomposition before runtime guard approval | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.755 | `-` | 심각한 하방위험 guard, runtime guard 없음 |
| `swing_entry_ofi_qi_execution_quality` | 스윙 진입 시 OFI/QI와 주문품질이 실제 성과에 도움이 되는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `sample_or_contract_gap_entry_quality_axis` | OFI/QI source-quality close, then approval/workorder | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.655 | `-` | 표본 부족, 심각한 하방위험 guard, runtime guard 없음 |
| `swing_scale_in_ofi_qi_confirmation` | 스윙 추가매수 직전 OFI/QI 확인 신호가 유효한지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `source_quality_contract_gap_scale_in_axis` | source-quality blocker close, then scale-in guard contract | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.655 | `-` | 표본 부족, 심각한 하방위험 guard, runtime guard 없음 |
| `swing_exit_ofi_qi_smoothing` | 스윙 청산 직전 OFI/QI로 EXIT 확정/보류를 다듬을 수 있는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `source_quality_or_contract_gap_exit_quality_axis` | exit smoothing sample floor + guard contract | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.755 | `-` | 심각한 하방위험 guard, runtime guard 없음 |

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-06-30.json`
- available: `True`
- candidate/arm/labeled: `1406` / `9219` / `1254`
- pending_future_quote_count: `3962`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- runtime_effect: `False`
- interpretation: source-only exploration. Surviving arms can create future source-quality/workorder inputs but cannot apply runtime env.
- warnings: `['pending_future_quotes']`

## Swing Lifecycle Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-30.json`
- available: `True`
- total/probe/discovery: `11727` / `0` / `11727`
- sim_auto_candidate_count: `21`
- workorder_count: `25`
- daily_simulation_consumed: `False`
- runtime_effect: `False`
- warnings: `[]`

## Swing Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-30.json`
- available: `True`
- source_contract_status: `pass`
- surfaced/sim_auto/code_patch: `647` / `21` / `73`
- runtime_effect: `False`
- warnings: `[]`

## Panic
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `panic_entry_freeze_guard` | 패닉셀 구간에서 scalping 신규 BUY pre-submit freeze canary를 열 수 있는지 보는 축 | 계약 미준비: approval artifact를 만들어도 pre-submit freeze runtime 반영 불가 | `hold` | `-` | - | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 0.3 | `contract_missing` | 유지 |
| `panic_buy_runner_tp_canary` | 패닉바잉 구간에서 fixed TP 전량청산 대비 runner 유지가 missed upside를 줄이는지 보는 축 | report-only: TP/trailing/live exit 변경 없음 | `freeze` | `-` | - | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.45 | `contract_missing` | 소스 품질 차단, panic_buy_orderbook_collector_coverage_gap |

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-06-30.json`
- ai_review: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-06-30.json`
- producer_gap_discovery: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-06-30.json`
- propagation: status=`warning` fail=`0` warnings=`2` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-06-30.json`
