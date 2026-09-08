# Runtime Approval Summary - 2026-09-08

- 목적: 스캘핑 threshold-cycle 판정과 스윙 runtime approval 판정을 한 화면에서 보는 읽기 전용 요약이다.
- runtime_mutation_allowed: `False`
- drought canonical handoff issues: `[]`
- drought EV previous-generation diagnostic diff: `{'missing_in_ev': ['order_observation_source_quality_raw_row_exclusion_producer_gap'], 'removed_from_current': ['order_threshold_window_policy_source_snapshot_alignment'], 'decision_changed': ['order_pattern_lab_ai_review_currentness_claude_small_net_generation_contract', 'order_pattern_lab_ai_review_currentness_pattern_lab_ai_review_contract']}`
- drought controller next-PREOPEN decision (not PID application): `{'bounded_calibration_candidate_count': 1, 'drought_activation_triggered': False, 'drought_desired_enabled': False, 'drought_stop_triggered': True, 'intraday_escalation_allowed': False, 'intraday_escalation_scopes': [], 'runtime_acceptance_state': 'runtime_not_evaluated', 'top_evaluation_reason': None}`
- target_date_runtime_selected_family_count_total: `20`
- scalping_reported_items/current_selected/current_enabled: `20` / `1` / `1`
- scalping_reported_current_selected_postclose_hold/next_preopen_candidate: `1` / `0`
- selected_auto_bounded_live: compatibility alias of current target-date runtime selection; it is not the postclose next-PREOPEN recommendation.
- scalping_legacy_hard_gate_risk_counts: `{'approval_or_contract_required': 1, 'intentional_safety_guard': 4, 'manual_review_required': 4, 'no_unreviewed_hard_gate': 11}`
- swing_blocked/requested/approved: `0` / `0` / `0`
- swing_legacy_archive/phase0_ignored: `0` / `0`
- swing_legacy_hard_gate_risk_counts: `{}`
- panic_approval_requested: `0`
- scalp_entry_adm_status: `None`
- lifecycle_matrix_status: `None`
- lifecycle_bucket_windows_promotion: `None` / `None`
- lifecycle_ai_context prompt/applied: `0` / `0`
- swing_strategy_discovery_labeled/pending: `None` / `None`
- swing_lifecycle_matrix_auto: `None`
- swing_lifecycle_bucket_auto: `None`
- institutional_flow_available/join_rate: `False` / `None`
- microstructure_reaction_available/ok: `True` / `665`
- pattern_lab_currentness_status: `pass`
- pattern_lab_ai_review_status: `warning`
- producer_gap_discovery_status: `disabled_by_default`
- pattern_lab_propagation_status: `pass`
- env_generated_at: `2026-09-08T07:35:03`
- first_bot_start_at: `2026-09-08T07:55:03`
- first_bot_start_after_env_at: `2026-09-08T07:55:03`
- pre_env_boot_gap: `False`

## Microstructure Reaction Context
- available: `True`
- authority: `diagnostic_source_only_with_fail_closed_holding_quality_consumer`
- rows ok/missing: `665` / `32714`
- real_submitted_count: `0`
- status_counts: `{'missing': 30986, 'not_evaluated': 1355, 'ok': 665, 'source_quality_partial': 105, 'stale': 268}`
- entry_reaction_quality_counts: `{'-': 30986, 'favorable_reaction': 28, 'mixed_reaction': 225, 'neutral_unusable': 1728, 'risk_context_only': 271, 'weak_reaction': 141}`
- avg_scores ask/hold/bid: `50.268` / `50.249` / `54.005`
- max_vi_proximity_risk: `30`
- warnings: `[]`

## Scalping
| 항목 | 설명 | 현재 적용 | 현재 runtime 선택/활성 | 장후 상태 | 다음 PREOPEN 후보 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `soft_stop_whipsaw_confirmation` | soft stop 직후 반등 가능성이 큰 표본은 1회 확인 시간을 두고 성급한 청산을 줄이는 축 | 관찰/리포트 only: runtime 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `selected_runtime_canary` | threshold-cycle selected family attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | window_policy primary=rolling_10d 기준 재평가: post-sell/holding-exit soft-stop source sample floor 미달(1/10); 단일 사례로 live enable 금지, ai_review_item_missing |
| `holding_flow_ofi_smoothing` | 보유/청산 AI flow 결과에 OFI/QI 미시수급을 붙여 EXIT 확정 또는 보류를 다듬는 축 | 기존 적용 유지: holding_flow_override 내부 OFI/QI postprocessor ON | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `existing_runtime_guard` | holding/exit EV attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.1 | `-` | 표본 부족, sample floor 미달(2/20); 값 유지 후 다음 장후 재산정, ai_review_item_missing |
| `protect_trailing_smoothing` | protect/trailing 청산 후보에서 미시 반등 신호가 있으면 과조기 청산을 줄이는 축 | 기존 적용 유지: protect/trailing break confirmation guard ON; 값 변경은 PREOPEN bounded apply만 허용 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `existing_runtime_guard` | holding/exit EV attribution; threshold update is PREOPEN bounded only | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.25 | `-` | 표본 부족, protect trailing sample floor 미달(5/20); confirmation guard 값 유지, ai_review_item_missing |
| `trailing_continuation` | trailing 이후 추가 상승 여지가 큰 표본을 계속 보유할 수 있는지 보는 축 | 관찰/리포트 only: trailing 연장 live 미적용 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `holding_exit_safety_freeze` | source-quality and GOOD_EXIT risk review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | window_policy primary=rolling_10d 기준 재평가: GOOD_EXIT 훼손 리스크가 커서 1차 loop에서는 report/calibration만 수행하고 live apply는 금지한다., ai_review_item_missing |
| `market_regime_continuous_thresholds` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.7 | `-` | 표본 부족, market regime continuous rolling source sample floor 미달(7/10); context-only 유지, ai_review_item_missing |
| `pre_submit_price_guard` | broker 제출 직전 quote stale, spread, passive probe 가격품질 문제를 막는 hard safety 축 | 기존 적용/검증 유지: 제출 직전 hard safety guard이며 auto_bounded_live 후보 아님 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `intentional_pre_submit_safety_guard` | safety/source-quality report only | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0 | `-` | 표본 부족, pre_submit_price_guard는 broker 제출 직전 hard safety/source-quality 감사 전용으로 유지하며 runtime apply 후보에서 제외한다., ai_review_item_missing |
| `dynamic_entry_price_resolver` | bid-1/bid-2/bid-3/best_bid/AI/reference/timeout 후보별 체결품질과 EV를 비교하는 진입가 튜닝 축 | 선택 시 다음 PREOPEN dynamic entry price resolver env만 bounded 적용, submit safety guard 우선 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `entry_price_bounded_tunable` | threshold-cycle candidate fill/cancel/late-fill/source-quality adjusted EV attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | dynamic entry price 후보 지표는 준비됐지만 유효한 bounded 추천값 또는 runtime env 변경값이 없어 PREOPEN apply 보류, ai_review_item_missing |
| `entry_split_order_plan` | 기존 requested_qty를 보존하면서 planned_orders를 bucket별 leg/price offset/비중 policy로 분해하는 submit 직전 튜닝 축 | 선택 시 다음 PREOPEN entry split order policy env/file/version만 적용, requested_qty 산정과 broker/account/order/quantity/cooldown guard는 변경 없음 | `False` / `False` | `hold` | `hold_no_next_preopen_change` | `entry_submit_split_bounded_tunable` | entry_split_order_plan report -> threshold-cycle calibration -> next PREOPEN policy file | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | window_policy primary=rolling_10d 기준 재평가: entry_split_order_plan recommended policy is not runtime-apply allowed or its explicit authority contract is invalid; keep it out of PREOPEN env handoff. |
| `scale_in_split_order_plan` | 기존 scale-in qty를 보존하면서 AVG_DOWN 물타기 주문을 leg/price offset policy로 분해하는 scale-in 직전 튜닝 축 | 선택 시 다음 PREOPEN scale-in split order policy env/file/version만 적용, scale-in qty 산정과 broker/account/order/quantity/cooldown guard는 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0 | `-` | 표본 부족, scale-in split paired economic samples or source dates are insufficient (0/3, minimum two source dates); only a fresh validated prior policy may carry. |
| `entry_price_execution_quality` | real-only 제출/체결/취소/late-fill/partial/full fill 품질을 감사하는 실행품질 축 | real-only audit: submit/fill/cancel 품질 기록만 수행, runtime threshold apply 권한 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `real_execution_quality_audit` | real-only submit/fill/cancel/late-fill audit | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0 | `-` | 표본 부족, entry_price_execution_quality는 real-only 제출/체결/취소/late-fill 감사 전용이며 runtime threshold apply 권한이 없다., ai_review_item_missing |
| `score65_74_recovery_probe` | family id는 score65_74로 유지하지만 현 runtime floor 기준 AI 점수 60~74 WAIT 구간 중 수급/가속 조건이 좋은 후보를 기본 신규 BUY sizing으로 회수하는 축 | 현재 target-date PREOPEN env 적용: operator runtime lock 유지 | `True` / `True` | `hold_sample` | `hold_no_next_preopen_change` | `entry_unlock_probe` | runtime env/operator lock plus post-apply attribution | 현재 target-date runtime은 operator lock으로 활성 상태다. 장후 calibration 상태는 다음 PREOPEN 변경 판단이며 현재 runtime을 즉시 끄지 않는다. | 0 | `-` | 표본 부족, real_applied_evidence_missing, ai_review_item_missing, auto_bounded_live 선택 |
| `strength_momentum_soft_gate_p1` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `softened_pre_ai_gate` | AI/counterfactual risk context, source-quality exception only | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | 소스 표본 없음, strength_momentum_soft_gate_p1는 pre-AI gate 재설계 family 후보이며 approval artifact 전까지 자동 runtime apply 금지, ai_review_item_missing |
| `overbought_pullback_guard_p1` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `softened_pre_ai_plus_pre_submit_guard` | overbought risk bucket EV and pre-submit guard attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | window_policy primary=rolling_5d 기준 재평가: overbought_pullback_guard_p1는 pre-AI gate 재설계 family 후보이며 approval artifact 전까지 자동 runtime apply 금지, ai_review_item_missing |
| `liquidity_pre_submit_guard_p1` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `softened_pre_ai_plus_pre_submit_guard` | liquidity risk bucket EV and real submit guard attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | window_policy primary=rolling_5d 기준 재평가: liquidity_pre_submit_guard_p1는 pre-AI gate 재설계 family 후보이며 approval artifact 전까지 자동 runtime apply 금지, ai_review_item_missing |
| `bad_entry_refined_canary` | 진입 직후 never-green/AI fade 위험이 큰 표본을 조기 정리할 수 있는지 보는 축 | OFF/관찰 only: refined canary live 미적용 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `entry_quality_canary` | bad-entry cohort EV and rollback guard | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0 | `-` | 표본 부족, terminal counterfactual EV 계약 미완성, resolved terminal label은 있으나 executable-price counterfactual EV 계약이 없어 runtime 후보 승격 금지 |
| `scale_in_price_guard` | 추가매수 직전 best bid/defensive limit, spread, stale quote로 가격품질을 보장하는 축 | 기존 적용 유지: 추가매수 가격품질 guard ON | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `intentional_pre_submit_safety_guard` | scale-in price quality EV/source-quality only | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | 소스 표본 없음, window_policy primary=rolling_10d 기준 재평가: 물타기/불타기 resolved/executed cohort가 없어 가격·수량 guard 값은 유지하고 다음 장후 재산정, ai_review_item_missing |
| `position_sizing_dynamic_formula` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `candidate_grid_comparison_runtime_apply_blocked` | candidate grid comparison -> PREOPEN bounded candidate -> postclose attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.2667 | `-` | 표본 부족, position_sizing_dynamic_formula real denominator sample floor 미달(8/30); candidate grid 유지, ai_review_item_missing |
| `scalping_avg_down_recovery_quality_gate` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 없음 | `-` | 표본 부족, exact_route_contract_missing_or_conflicting_current, ai_review_item_missing |
| `scalping_pyramid_quality_gate` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `False` / `False` | `hold_sample` | `hold_no_next_preopen_change` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 없음 | `-` | 소스 표본 없음, threshold_replay_no_comparable_episodes, ai_review_item_missing |
| `latency_classifier_runtime_profile` | SAFE/CAUTION/DANGER runtime hard-safety 판정과 latency blocker를 기록하는 진입 실행품질 진단축 | 기존 SAFE/CAUTION/DANGER hard-safety 판정과 blocker 계측 유지; 독립 PREOPEN 추천·임계값 적용은 폐기 | `False` / `False` | `baseline_hard_safety` | `not_applicable_retired` | `entry_execution_quality_hard_safety_diagnostic` | BUY Funnel plus daily performance latency_block attribution; no independent PREOPEN candidate | SAFE/CAUTION은 slippage check 후 normal submit으로 보내고, DANGER/stale/broker safety만 submit 차단으로 유지한다. spread-only 완화는 별도 명시적 operator lock이 소유한다. | 367 | `-` | 독립 latency 추천 폐기·hard-safety 진단 유지 |

## Scalp Entry ADM
- status: `retired`
- runtime_bias_scope: `None`
- joined_action_ev_pct: `None`
- joined_sample/sample_floor: `None` / `None`
- prompt_applied_count: `None`
- missing_actions: `[]`
- top_actions: `[]`
- ready_for_daily_policy_tuning: `None`
- warnings: `[]`

## Institutional Flow Context
- artifact: `-`
- authority: `archive_only`
- rows ok/partial/missing/token_error: `None` / `None` / `None` / `None`
- join_rate_pct: `None`
- source_mix: `{}`
- top_net_buy: `[]`
- warnings: `[]`

## Lifecycle Decision Matrix
- status: `retired`
- matrix_version: `-`
- runtime_bias_scope: `None`
- total/joined/floor: `None` / `None` / `None`
- policy_pass/promote_ready: `None` / `None`
- lifecycle_flow buckets/complete/runtime/workorders: `None` / `None` / `None` / `None`
- holding/exit buckets: `None` / `None`
- holding/exit workorders: `None` / `None`
- lifecycle identity missing/join_rate: `None` / `None`
- lifecycle complete_flow_rate: `None`
- incomplete_flow_reason_counts: `{}`
- fixed_threshold_roles: `{}`
- ready_for_bounded_apply: `None`
- warnings: `[]`

## Lifecycle Bucket Windows
- promotion_window: `-`
- confirmation_windows: `[]`
- windows: `{}`
- warnings: `[]`

## Lifecycle AI Context
- context_artifact: `-`
- context_version: `-`
- prompt_stage_count: `None`
- attribution_artifact: `-`
- attribution eligible/applied/skipped: `None` / `None` / `None`
- stage_attribution: `{}`

## Swing
| 항목 | 설명 | 현재 적용 | 현재 runtime 선택/활성 | 장후 상태 | 다음 PREOPEN 후보 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| - | - | - | - | - | - | - | - | - | - | - | - |

## Swing Strategy Discovery Sim
- artifact: `-`
- available: `False`
- candidate/arm/labeled: `None` / `None` / `None`
- pending_future_quote_count: `None`
- top_surviving_arm: `-`
- avoid_bucket_count: `None`
- runtime_effect: `False`
- interpretation: -
- warnings: `[]`

## Swing Lifecycle Matrix
- artifact: `-`
- available: `False`
- total/probe/discovery: `None` / `None` / `None`
- sim_auto_candidate_count: `None`
- workorder_count: `None`
- daily_simulation_consumed: `None`
- runtime_effect: `False`
- warnings: `[]`

## Swing Lifecycle Bucket Discovery
- artifact: `-`
- available: `False`
- source_contract_status: `None`
- surfaced/sim_auto/code_patch: `None` / `None` / `None`
- runtime_effect: `False`
- warnings: `[]`

## Panic
| 항목 | 설명 | 현재 적용 | 현재 runtime 선택/활성 | 장후 상태 | 다음 PREOPEN 후보 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `panic_entry_freeze_guard` | 패닉셀 구간에서 scalping 신규 BUY pre-submit freeze canary를 열 수 있는지 보는 축 | 계약 미준비: approval artifact를 만들어도 pre-submit freeze runtime 반영 불가 | `None` / `None` | `hold` | `-` | `-` | - | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 0.3 | `contract_missing` | 유지 |

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-09-08.json`
- ai_review: status=`warning` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-09-08.json`
- producer_gap_discovery: status=`disabled_by_default` artifact=`-`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-09-08.json`

## Warnings
- `scalp_entry_action_decision_matrix_missing`
- `lifecycle_decision_matrix_missing`
- `lifecycle_bucket_discovery_missing`
