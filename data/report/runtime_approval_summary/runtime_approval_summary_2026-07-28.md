# Runtime Approval Summary - 2026-07-28

- 목적: 스캘핑 threshold-cycle 판정과 스윙 runtime approval 판정을 한 화면에서 보는 읽기 전용 요약이다.
- runtime_mutation_allowed: `False`
- scalping_items/selected: `22` / `3`
- scalping_legacy_hard_gate_risk_counts: `{'approval_or_contract_required': 1, 'intentional_safety_guard': 4, 'manual_review_required': 3, 'no_unreviewed_hard_gate': 14}`
- swing_blocked/requested/approved: `0` / `0` / `0`
- swing_legacy_archive/phase0_ignored: `0` / `0`
- swing_legacy_hard_gate_risk_counts: `{}`
- panic_approval_requested: `0`
- scalp_entry_adm_status: `warning`
- lifecycle_matrix_status: `warning`
- lifecycle_bucket_windows_promotion: `pass` / `target_pass`
- lifecycle_ai_context prompt/applied: `3` / `2`
- swing_strategy_discovery_labeled/pending: `4428` / `5980`
- swing_lifecycle_matrix_auto: `25`
- swing_lifecycle_bucket_auto: `53`
- institutional_flow_available/join_rate: `True` / `100.0`
- microstructure_reaction_available/ok: `True` / `61`
- pattern_lab_currentness_status: `pass`
- pattern_lab_ai_review_status: `warning`
- producer_gap_discovery_status: `pass`
- pattern_lab_propagation_status: `warning`
- env_generated_at: `2026-07-28T07:35:01`
- first_bot_start_at: `-`
- first_bot_start_after_env_at: `-`
- pre_env_boot_gap: `False`

## Microstructure Reaction Context
- available: `True`
- authority: `entry_confidence_modifier_source_only`
- rows ok/missing: `61` / `4225`
- real_submitted_count: `24`
- status_counts: `{'missing': 4108, 'ok': 61, 'stale': 117}`
- entry_reaction_quality_counts: `{'-': 4108, 'favorable_reaction': 5, 'mixed_reaction': 22, 'neutral_unusable': 117, 'risk_context_only': 4, 'weak_reaction': 30}`
- avg_scores ask/hold/bid: `45.755` / `49.651` / `59.237`
- max_vi_proximity_risk: `0`
- warnings: `[]`

## Scalping
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `soft_stop_whipsaw_confirmation` | soft stop 직후 반등 가능성이 큰 표본은 1회 확인 시간을 두고 성급한 청산을 줄이는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `selected_runtime_canary` | threshold-cycle selected family attribution | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | `-` | auto_bounded_live 선택 |
| `holding_flow_ofi_smoothing` | 보유/청산 AI flow 결과에 OFI/QI 미시수급을 붙여 EXIT 확정 또는 보류를 다듬는 축 | 기존 적용 유지: holding_flow_override 내부 OFI/QI postprocessor ON | `hold_sample` | `existing_runtime_guard` | holding/exit EV attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.6 | `-` | 표본 부족 |
| `protect_trailing_smoothing` | protect/trailing 청산 후보에서 미시 반등 신호가 있으면 과조기 청산을 줄이는 축 | 관찰/리포트 only: protect/trailing live smoothing 미적용 | `hold` | `report_only_holding_exit_candidate` | report-only until approval/rollback guard | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `trailing_continuation` | trailing 이후 추가 상승 여지가 큰 표본을 계속 보유할 수 있는지 보는 축 | 관찰/리포트 only: trailing 연장 live 미적용 | `freeze` | `holding_exit_safety_freeze` | source-quality and GOOD_EXIT risk review | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 1 | `-` | 동결 |
| `market_regime_continuous_thresholds` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.8 | `-` | 표본 부족 |
| `pre_submit_price_guard` | broker 제출 직전 quote stale, spread, passive probe 가격품질 문제를 막는 hard safety 축 | 기존 적용/검증 유지: 제출 직전 hard safety guard이며 auto_bounded_live 후보 아님 | `hold` | `intentional_pre_submit_safety_guard` | safety/source-quality report only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 0 | `-` | 유지 |
| `dynamic_entry_price_resolver` | bid-1/bid-2/bid-3/best_bid/AI/reference/timeout 후보별 체결품질과 EV를 비교하는 진입가 튜닝 축 | 선택 시 다음 PREOPEN dynamic entry price resolver env만 bounded 적용, submit safety guard 우선 | `hold_sample` | `entry_price_bounded_tunable` | threshold-cycle candidate fill/cancel/late-fill/source-quality adjusted EV attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.6 | `-` | 표본 부족, counterfactual join gap, recovery floor 미달 |
| `entry_split_order_plan` | 기존 requested_qty를 보존하면서 planned_orders를 bucket별 leg/price offset/비중 policy로 분해하는 submit 직전 튜닝 축 | 선택 시 다음 PREOPEN entry split order policy env/file/version만 적용, requested_qty 산정과 broker/account/order/quantity/cooldown guard는 변경 없음 | `adjust_up` | `entry_submit_split_bounded_tunable` | entry_split_order_plan report -> threshold-cycle calibration -> next PREOPEN policy file | 자동 반영 후보로 선택되면 PREOPEN env에 적용된다 | 1 | `-` | - |
| `scale_in_split_order_plan` | 기존 scale-in qty를 보존하면서 AVG_DOWN 물타기 주문을 leg/price offset policy로 분해하는 scale-in 직전 튜닝 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `not_classified` | manual runtime approval review | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 0 | `-` | auto_bounded_live 선택 |
| `entry_price_execution_quality` | real-only 제출/체결/취소/late-fill/partial/full fill 품질을 감사하는 실행품질 축 | real-only audit: submit/fill/cancel 품질 기록만 수행, runtime threshold apply 권한 없음 | `hold` | `real_execution_quality_audit` | real-only submit/fill/cancel/late-fill audit | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `score65_74_recovery_probe` | family id는 score65_74로 유지하지만 현 runtime floor 기준 AI 점수 60~74 WAIT 구간 중 수급/가속 조건이 좋은 후보를 기본 신규 BUY sizing으로 회수하는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `hold_sample` | `entry_unlock_probe` | runtime env/operator lock plus post-apply attribution | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 0 | `-` | 표본 부족, auto_bounded_live 선택 |
| `strength_momentum_soft_gate_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_gate` | AI/counterfactual risk context, source-quality exception only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `overbought_pullback_guard_p1` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `softened_pre_ai_plus_pre_submit_guard` | overbought risk bucket EV and pre-submit guard attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0 | `-` | 표본 부족 |
| `liquidity_pre_submit_guard_p1` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `softened_pre_ai_plus_pre_submit_guard` | liquidity risk bucket EV and real submit guard attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0 | `-` | 표본 부족 |
| `bad_entry_refined_canary` | 진입 직후 never-green/AI fade 위험이 큰 표본을 조기 정리할 수 있는지 보는 축 | OFF/관찰 only: refined canary live 미적용 | `adjust_up` | `entry_quality_canary` | bad-entry cohort EV and rollback guard | 자동 반영 후보로 선택되면 PREOPEN env에 적용된다 | 1 | `-` | - |
| `holding_exit_decision_matrix_advisory` | 보유 중 가능한 행동(EXIT/HOLD/AVG_DOWN/PYRAMID)을 matrix 점수로 보조 판단하는 축 | 관찰/리포트 only: advisory live 적용 아님 | `hold_no_edge` | `advisory_report_only` | report-only decision support contract | 명확한 edge가 없어 runtime 변경은 하지 않는다 | 0 | `-` | edge 부족 |
| `scale_in_price_guard` | 추가매수 직전 best bid/defensive limit, spread, stale quote로 가격품질을 보장하는 축 | 기존 적용 유지: 추가매수 가격품질 guard ON | `hold` | `intentional_pre_submit_safety_guard` | scale-in price quality EV/source-quality only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `position_sizing_dynamic_formula` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `candidate_grid_comparison_runtime_apply_blocked` | candidate grid comparison -> PREOPEN bounded candidate -> postclose attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | 소스 표본 없음 |
| `scalp_entry_action_decision_matrix_advisory` | 스캘핑 entry action(BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE 등)을 matrix EV로 비교해 AI action을 보정하는 운영 override 축 | 운영 override runtime bias: AI BUY를 WAIT/DROP 또는 defensive bias로 보정, submit safety guard 우선 | `hold_sample` | `entry_adm_runtime_bias_operator_override` | daily scalp_entry_action_decision_matrix -> threshold EV/runtime summary/workorder/pattern lab -> next runtime env | 운영 override runtime bias는 AI BUY를 WAIT/DROP 또는 defensive bias로 보정한다. daily action bucket EV와 runtime forced_action provenance가 충분해야 다음 env 튜닝 판단으로 넘어간다. | 없음 | `-` | 표본 부족 |
| `lifecycle_decision_matrix_runtime` | 개별 후보 lifecycle row를 entry/submit/holding/scale-in/exit stage별 weighted ADM policy로 해석하는 umbrella runtime 축 | 기본 OFF: 선택 시 micro canary env로 policy file/version만 연결, hard safety/submit guard 우선 | `hold_sample` | `umbrella_weighted_adm_runtime_policy` | postclose lifecycle_decision_matrix -> threshold EV/runtime summary -> next preopen bounded env | 선택 시 policy file/version만 다음 PREOPEN env로 연결한다. hard safety와 broker/account/order guard는 항상 matrix proposal보다 우선한다. | -0.7692 | `-` | 표본 부족 |
| `latency_classifier_runtime_profile` | latency SAFE/CAUTION/DANGER classifier와 bounded submit recovery canary를 분리 적용하는 진입 실행품질 축 | 보류: 최신 recommendation 기준 다음 PREOPEN latency env 변경 없음 | `hold_sample` | `entry_execution_quality_bounded_tunable` | threshold-cycle latency audit plus post-apply latency_pass/order_bundle attribution | SAFE/CAUTION은 slippage check 후 normal submit으로 보내고, DANGER/stale/broker safety만 submit 차단으로 유지한다. | 0 | `-` | latency semantics gap |
| `scalp_sim_overnight_ai_carry` | 장마감 후 open 스캘핑 sim 포지션을 overnight_v1로 SELL_TODAY/HOLD_OVERNIGHT 분리해 다음날 lifecycle/EV label로 연결하는 source-only 축 | source-only: sim 가상 청산/carry 기록만 수행, runtime threshold apply 권한 없음 | `observe_only` | `not_classified` | manual runtime approval review | runtime_effect=false source다. SELL_TODAY는 sim 가상 청산, HOLD_OVERNIGHT는 active_unrealized carry로만 남긴다. | - | `-` | 관찰 전용 |

## Scalp Entry ADM
- status: `warning`
- runtime_bias_scope: `force_wait_force_drop_buy_defensive_bias`
- joined_action_ev_pct: `None`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `2`
- missing_actions: `[]`
- top_actions: `[{'action': 'BUY_NOW', 'sample_count': 14, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'WAIT_REQUOTE', 'sample_count': 46, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 9, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 8, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}]`
- ready_for_daily_policy_tuning: `False`
- warnings: `['joined_sample_below_sample_floor', 'unknown_bucket_source_quality_gap']`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-07-28.json`
- authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '073240', 'smart_money_net': 805979, 'foreign_net_roll5': 2087212, 'inst_net_roll5': 56206, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '131970', 'smart_money_net': 267130, 'foreign_net_roll5': 414731, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '032350', 'smart_money_net': 125450, 'foreign_net_roll5': 324175, 'inst_net_roll5': 218720, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '222800', 'smart_money_net': 114412, 'foreign_net_roll5': 448523, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '319660', 'smart_money_net': 95961, 'foreign_net_roll5': 569664, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '214450', 'smart_money_net': 93987, 'foreign_net_roll5': 0, 'inst_net_roll5': 373173, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '028300', 'smart_money_net': 69223, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '281820', 'smart_money_net': 58641, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '018260', 'smart_money_net': 58136, 'foreign_net_roll5': 0, 'inst_net_roll5': 327042, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '089970', 'smart_money_net': 51526, 'foreign_net_roll5': 593237, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}]`
- warnings: `[]`

## Lifecycle Decision Matrix
- status: `warning`
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-28`
- runtime_bias_scope: `stage_action_proposal_micro_canary`
- total/joined/floor: `83` / `6` / `20`
- policy_pass/promote_ready: `0` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `13` / `0` / `0` / `20`
- holding/exit buckets: `5` / `5`
- holding/exit workorders: `0` / `0`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_holding': 38, 'missing_exit': 38, 'missing_entry': 8, 'missing_submit': 14, 'candidate_id_only': 5, 'scale_in_noise_only': 5, 'sim_record_id_only': 1, 'postclose_exit_without_entry': 1, 'identity_namespace_mismatch': 1, 'join_contract_blocked': 1}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- ready_for_bounded_apply: `False`
- warnings: `['joined_sample_below_sample_floor', 'policy_pass_arm_missing']`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-28_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 12, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 34, 'absorbed_sample_count': 162, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-28_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 28, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 84, 'absorbed_sample_count': 1187, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-28_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 37, 'selected_parent_level': 'L1_broad', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 240, 'absorbed_sample_count': 12675, 'child_conflict_warning_count': 8, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`
- warnings: `['lifecycle_bucket_discovery:source_contract_drift_warning']`

## Lifecycle AI Context
- context_artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-07-28.json`
- context_version: `lifecycle_ai_context_v1_2026-07-28`
- prompt_stage_count: `3`
- attribution_artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-07-28.json`
- attribution eligible/applied/skipped: `2` / `2` / `0`
- stage_attribution: `{'entry': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Swing
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| - | - | - | - | - | - | - | - | - | - |

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-07-28.json`
- available: `True`
- candidate/arm/labeled: `3172` / `21401` / `4428`
- pending_future_quote_count: `5980`
- top_surviving_arm: `arm05_breakout_conf_trailing`
- avoid_bucket_count: `20`
- runtime_effect: `False`
- interpretation: source-only exploration. Surviving arms can create future source-quality/workorder inputs but cannot apply runtime env.
- warnings: `['pending_future_quotes']`

## Swing Lifecycle Matrix
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-07-28.json`
- available: `True`
- total/probe/discovery: `30257` / `0` / `30257`
- sim_auto_candidate_count: `25`
- workorder_count: `25`
- daily_simulation_consumed: `False`
- runtime_effect: `False`
- warnings: `[]`

## Swing Lifecycle Bucket Discovery
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-07-28.json`
- available: `True`
- source_contract_status: `pass`
- surfaced/sim_auto/code_patch: `674` / `53` / `72`
- runtime_effect: `False`
- warnings: `[]`

## Panic
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `panic_entry_freeze_guard` | 패닉셀 구간에서 scalping 신규 BUY pre-submit freeze canary를 열 수 있는지 보는 축 | 계약 미준비: approval artifact를 만들어도 pre-submit freeze runtime 반영 불가 | `hold_sample` | `-` | - | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.45 | `contract_missing` | 표본 부족 |
| `panic_buy_runner_tp_canary` | 패닉바잉 구간에서 fixed TP 전량청산 대비 runner 유지가 missed upside를 줄이는지 보는 축 | report-only: TP/trailing/live exit 변경 없음 | `freeze` | `-` | - | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 없음 | `contract_missing` | runtime_effect_not_report_only |

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-07-28.json`
- ai_review: status=`warning` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-07-28.json`
- producer_gap_discovery: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/producer_gap_discovery/producer_gap_discovery_2026-07-28.json`
- propagation: status=`warning` fail=`0` warnings=`1` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-07-28.json`

## Warnings
- `swing_runtime_approval_missing`
