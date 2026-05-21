# Runtime Approval Summary - 2026-05-21

- 목적: 스캘핑 threshold-cycle 판정과 스윙 runtime approval 판정을 한 화면에서 보는 읽기 전용 요약이다.
- runtime_mutation_allowed: `False`
- scalping_items/selected: `19` / `3`
- scalping_legacy_hard_gate_risk_counts: `{'approval_or_contract_required': 2, 'intentional_safety_guard': 4, 'manual_review_required': 2, 'no_unreviewed_hard_gate': 11}`
- swing_blocked/requested/approved: `14` / `3` / `0`
- swing_legacy_hard_gate_risk_counts: `{'contract_gap': 4, 'no_unreviewed_hard_gate': 3, 'same_stage_deferred': 2, 'sample_or_contract_gap': 3, 'source_quality_or_approval_required': 1, 'source_quality_or_contract_gap': 1}`
- panic_approval_requested: `0`
- scalp_entry_adm_status: `pass`
- lifecycle_matrix_status: `pass`
- lifecycle_ai_context prompt/applied: `3` / `3196`
- swing_strategy_discovery_labeled/pending: `0` / `800`
- institutional_flow_available/join_rate: `True` / `100.0`
- pattern_lab_currentness_status: `pass`
- pattern_lab_propagation_status: `pass`
- env_generated_at: `2026-05-21T07:35:01`
- first_bot_start_at: `2026-05-21T07:40:04`
- first_bot_start_after_env_at: `2026-05-21T07:40:04`
- pre_env_boot_gap: `False`

## Scalping
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `soft_stop_whipsaw_confirmation` | soft stop 직후 반등 가능성이 큰 표본은 1회 확인 시간을 두고 성급한 청산을 줄이는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `selected_runtime_canary` | threshold-cycle selected family attribution | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | `-` | auto_bounded_live 선택 |
| `holding_flow_ofi_smoothing` | 보유/청산 AI flow 결과에 OFI/QI 미시수급을 붙여 EXIT 확정 또는 보류를 다듬는 축 | 기존 적용 유지: holding_flow_override 내부 OFI/QI postprocessor ON | `hold` | `existing_runtime_guard` | holding/exit EV attribution | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `protect_trailing_smoothing` | protect/trailing 청산 후보에서 미시 반등 신호가 있으면 과조기 청산을 줄이는 축 | 관찰/리포트 only: protect/trailing live smoothing 미적용 | `adjust_down` | `report_only_holding_exit_candidate` | report-only until approval/rollback guard | 자동 반영 후보로 선택되면 PREOPEN env에 적용된다 | 1 | `-` | - |
| `trailing_continuation` | trailing 이후 추가 상승 여지가 큰 표본을 계속 보유할 수 있는지 보는 축 | 관찰/리포트 only: trailing 연장 live 미적용 | `freeze` | `holding_exit_safety_freeze` | source-quality and GOOD_EXIT risk review | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 1 | `-` | 동결 |
| `market_regime_continuous_thresholds` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 0.1 | `-` | 표본 부족 |
| `pre_submit_price_guard` | 주문 제출 직전 quote stale, spread, passive probe 가격품질 문제를 막는 진입 안전축 | 기존 적용/검증 유지: 제출 직전 가격품질 guard 계열 | `hold_sample` | `intentional_pre_submit_safety_guard` | pre_submit_price_guard EV/source-quality only | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 1 | `-` | 표본 부족 |
| `score65_74_recovery_probe` | AI 점수 65~74 WAIT 구간 중 수급/가속 조건이 좋은 후보를 1주/소액 canary로 회수하는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `entry_unlock_probe` | runtime env/operator lock plus post-apply attribution | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | `-` | auto_bounded_live 선택 |
| `strength_momentum_soft_gate_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_gate` | AI/counterfactual risk context, source-quality exception only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `overbought_pullback_guard_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_plus_pre_submit_guard` | overbought risk bucket EV and pre-submit guard attribution | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `liquidity_pre_submit_guard_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_plus_pre_submit_guard` | liquidity risk bucket EV and real submit guard attribution | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `bad_entry_refined_canary` | 진입 직후 never-green/AI fade 위험이 큰 표본을 조기 정리할 수 있는지 보는 축 | OFF/관찰 only: refined canary live 미적용 | `adjust_up` | `entry_quality_canary` | bad-entry cohort EV and rollback guard | 자동 반영 후보로 선택되면 PREOPEN env에 적용된다 | 1 | `-` | - |
| `holding_exit_decision_matrix_advisory` | 보유 중 가능한 행동(EXIT/HOLD/AVG_DOWN/PYRAMID)을 matrix 점수로 보조 판단하는 축 | 관찰/리포트 only: advisory live 적용 아님 | `hold_no_edge` | `advisory_report_only` | report-only decision support contract | 명확한 edge가 없어 runtime 변경은 하지 않는다 | 0 | `-` | edge 부족 |
| `scale_in_price_guard` | 추가매수 직전 best bid/defensive limit, spread, stale quote로 가격품질을 보장하는 축 | 기존 적용 유지: 추가매수 가격품질 guard ON | `hold` | `intentional_pre_submit_safety_guard` | scale-in price quality EV/source-quality only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `position_sizing_cap_release` | 신규/추가매수 1주 cap을 풀 수 있는지 EV와 downside 기준으로 보는 축 | 미적용: 1주 cap 유지 | `hold_sample` | `policy_approval_or_contract_gap` | separate approval artifact/workorder before runtime size change | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 1 | `-` | 표본 부족 |
| `position_sizing_dynamic_formula` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `policy_contract_gap` | notional/source-quality adjusted EV plus approval contract | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 0.1 | `-` | 표본 부족 |
| `scalp_entry_action_decision_matrix_advisory` | 스캘핑 entry action(BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE 등)을 matrix EV로 비교해 AI action을 보정하는 운영 override 축 | 운영 override runtime bias: AI BUY를 WAIT/DROP 또는 defensive bias로 보정, submit safety guard 우선 | `hold` | `entry_adm_runtime_bias_operator_override` | daily scalp_entry_action_decision_matrix -> threshold EV/runtime summary/workorder/pattern lab -> next runtime env | 운영 override runtime bias는 AI BUY를 WAIT/DROP 또는 defensive bias로 보정한다. daily action bucket EV와 runtime forced_action provenance가 충분해야 다음 env 튜닝 판단으로 넘어간다. | 없음 | `-` | 유지 |
| `lifecycle_decision_matrix_runtime` | 개별 후보 lifecycle row를 entry/submit/holding/scale-in/exit stage별 weighted ADM policy로 해석하는 umbrella runtime 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `umbrella_weighted_adm_runtime_policy` | postclose lifecycle_decision_matrix -> threshold EV/runtime summary -> next preopen bounded env | 선택 시 policy file/version만 다음 PREOPEN env로 연결한다. hard safety와 broker/account/order guard는 항상 matrix proposal보다 우선한다. | -0.2995 | `-` | auto_bounded_live 선택 |
| `latency_classifier_runtime_profile` | latency SAFE/CAUTION/DANGER classifier와 bounded submit recovery canary를 분리 적용하는 진입 실행품질 축 | 보류: 최신 recommendation 기준 다음 PREOPEN latency env 변경 없음 | `hold_sample` | `entry_execution_quality_bounded_tunable` | threshold-cycle latency recommendation plus post-apply latency_pass/order_bundle attribution | SAFE만 runtime pass로 보며 CAUTION은 기본 reject다. recovery canary가 명시되고 allowed_runtime_apply=true인 후보만 다음 PREOPEN bounded env로 연결한다. | 0 | `-` | latency_classifier_runtime_semantics_gap |
| `scalp_sim_overnight_ai_carry` | 장마감 후 open 스캘핑 sim 포지션을 overnight_v1로 SELL_TODAY/HOLD_OVERNIGHT 분리해 다음날 lifecycle/EV label로 연결하는 source-only 축 | source-only: sim 가상 청산/carry 기록만 수행, runtime threshold apply 권한 없음 | `observe_only` | `not_classified` | manual runtime approval review | runtime_effect=false source다. SELL_TODAY는 sim 가상 청산, HOLD_OVERNIGHT는 active_unrealized carry로만 남긴다. | - | `-` | 관찰 전용 |

## Scalp Entry ADM
- status: `pass`
- runtime_bias_scope: `force_wait_force_drop_buy_defensive_bias`
- joined_action_ev_pct: `-0.0322`
- joined_sample/sample_floor: `175` / `20`
- prompt_applied_count: `1280`
- missing_actions: `[]`
- top_actions: `[{'action': 'WAIT_REQUOTE', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 1440, 'joined_sample': 174, 'source_quality_adjusted_ev_pct': -0.0322}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 2, 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 2.785}]`
- ready_for_daily_policy_tuning: `True`
- warnings: `[]`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-05-21.json`
- authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '005930', 'smart_money_net': 6190749, 'foreign_net_roll5': 0, 'inst_net_roll5': 9118293, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '034220', 'smart_money_net': 3326808, 'foreign_net_roll5': 6537917, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '088350', 'smart_money_net': 1371141, 'foreign_net_roll5': 6495422, 'inst_net_roll5': 4545869, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '125020', 'smart_money_net': 1324323, 'foreign_net_roll5': 852478, 'inst_net_roll5': 20649, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '003490', 'smart_money_net': 1281486, 'foreign_net_roll5': 1021374, 'inst_net_roll5': 783553, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '017900', 'smart_money_net': 871829, 'foreign_net_roll5': 641423, 'inst_net_roll5': 36444, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '357880', 'smart_money_net': 728621, 'foreign_net_roll5': 860590, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '067310', 'smart_money_net': 590582, 'foreign_net_roll5': 1761765, 'inst_net_roll5': 462107, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '033640', 'smart_money_net': 543559, 'foreign_net_roll5': 293673, 'inst_net_roll5': 222636, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '061970', 'smart_money_net': 482443, 'foreign_net_roll5': 661807, 'inst_net_roll5': 593696, 'regime': 'DUAL_ACCUMULATION'}]`
- warnings: `[]`

## Lifecycle Decision Matrix
- status: `pass`
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-21`
- runtime_bias_scope: `stage_action_proposal_micro_canary`
- total/joined/floor: `40910` / `39149` / `20`
- policy_pass/promote_ready: `5` / `0`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- ready_for_bounded_apply: `True`
- warnings: `[]`

## Lifecycle AI Context
- context_artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-21.json`
- context_version: `lifecycle_ai_context_v1_2026-05-21`
- prompt_stage_count: `3`
- attribution_artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-21.json`
- attribution eligible/applied/skipped: `3196` / `3196` / `0`
- stage_attribution: `{'entry': {'context_contribution_score': 0.3478, 'bounded_auxiliary_weight': 0.0522, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.9969, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Swing
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `swing_selection_top_k` | 스윙 추천 후보 수(top-k)를 늘리거나 줄일 수 있는지 보는 선택 폭 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `same_stage_deferred_selection_axis` | same-stage owner conflict 해소 후 approval route | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | same_stage_owner_conflict:swing_model_floor |
| `swing_gatekeeper_accept_reject` | 스윙 gatekeeper가 accept/reject한 후보의 후행 성과를 비교하는 진입 판단 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `legacy_hard_gate_contract_gap` | workorder로 accept/reject policy guard를 만들거나 reject cooldown family로 우회 조정 | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | runtime guard 없음 |
| `swing_market_regime_sensitivity` | 시장 regime에 따라 스윙 진입 민감도를 완화/강화할지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `same_stage_deferred_entry_axis` | same-stage owner conflict 해소 후 SWING_MARKET_REGIME_SENSITIVITY route | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | same_stage_owner_conflict:swing_gatekeeper_reject_cooldown |
| `swing_pyramid_trigger` | 스윙 보유 후 불타기(PYRAMID) 조건이 유효한지 보는 추가매수 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `runtime_contract_gap_scale_in_axis` | scale-in runtime guard/workorder before approval | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | runtime guard 없음 |
| `swing_avg_down_eligibility` | 스윙 보유 후 물타기(AVG_DOWN) 조건이 유효한지 보는 추가매수 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `runtime_contract_gap_scale_in_axis` | policy/workorder first, real canary approval later | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | runtime guard 없음 |
| `swing_trailing_stop_time_stop` | 스윙 trailing/time stop 청산 조건의 적정성을 보는 exit 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `runtime_contract_gap_exit_axis` | exit runtime guard/workorder before approval | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | runtime guard 없음 |
| `swing_holding_flow_defer` | 스윙 보유/청산 AI가 청산 보류를 결정한 뒤 성과가 개선되는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `sample_or_contract_gap_holding_axis` | sample floor + runtime guard contract | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | runtime guard 없음 |
| `swing_entry_ofi_qi_execution_quality` | 스윙 진입 시 OFI/QI와 주문품질이 실제 성과에 도움이 되는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `hold_sample` | `sample_or_contract_gap_entry_quality_axis` | OFI/QI source-quality close, then approval/workorder | 축은 유지/관찰하지만 표본 부족으로 runtime 변경은 하지 않는다 | 0.905 | `-` | 표본 부족, runtime guard 없음 |
| `swing_scale_in_ofi_qi_confirmation` | 스윙 추가매수 직전 OFI/QI 확인 신호가 유효한지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `source_quality_contract_gap_scale_in_axis` | source-quality blocker close, then scale-in guard contract | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | scale_in_ofi_qi_invalid_micro_context, runtime guard 없음 |
| `swing_exit_ofi_qi_smoothing` | 스윙 청산 직전 OFI/QI로 EXIT 확정/보류를 다듬을 수 있는지 보는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `freeze` | `sample_or_contract_gap_exit_quality_axis` | exit smoothing sample floor + guard contract | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.955 | `-` | runtime guard 없음 |
| `swing_scale_in_real_canary_phase0` | 승인된 실제 스윙 보유분에 한해 PYRAMID/AVG_DOWN 1주 추가매수 canary를 열 수 있는지 보는 정책 축 | 미적용: approval artifact 없이는 실주문 추가매수 금지 | `freeze` | `policy_source_quality_block` | scale-in approval artifact after source-quality pass | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 없음 | `-` | PYRAMID 표본 부족, scale_in_ofi_qi_invalid_micro_context, 최종 exit 수익률 누락, exit-only 비교 누락, 추가매수 MAE 누락 |
| `swing_model_floor` | 스윙 추천 모델 floor 값을 올리거나 낮출 수 있는지 보는 선택 기준 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `approval_required` | `approval_route_available` | swing_runtime_approvals artifact -> next PREOPEN dry-run env | approval artifact가 있어야 다음 PREOPEN env 반영 후보가 된다 | 0.955 | `ready` | approval artifact 없음 |
| `swing_gatekeeper_reject_cooldown` | gatekeeper reject 이후 같은 후보를 다시 볼 cooldown 시간을 조정하는 축 | 스윙 dry-run/probe 관찰: 실주문 변경 없음 | `approval_required` | `approval_route_available` | ML_GATEKEEPER_REJECT_COOLDOWN approval/env route | approval artifact가 있어야 다음 PREOPEN env 반영 후보가 된다 | 0.955 | `ready` | approval artifact 없음 |
| `swing_one_share_real_canary_phase0` | 승인된 스윙 후보에 한해 초기 BUY/SELL 1주 real canary execution 품질을 수집하는 정책 축 | 미적용: approval artifact 없이는 초기 BUY 실주문 금지 | `approval_required` | `approval_route_available_policy_axis` | one-share approval artifact, global dry-run guard retained | approval artifact가 있어야 다음 PREOPEN env 반영 후보가 된다 | 0.955 | `ready` | 1주 real canary approval artifact 없음 |

## Swing Strategy Discovery Sim
- artifact: `/home/ubuntu/KORStockScan/data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_2026-05-21.json`
- available: `True`
- candidate/arm/labeled: `100` / `800` / `0`
- pending_future_quote_count: `800`
- top_surviving_arm: `-`
- avoid_bucket_count: `0`
- runtime_effect: `False`
- interpretation: source-only exploration. Surviving arms can create future source-quality/workorder inputs but cannot apply runtime env.
- warnings: `['pending_future_quotes']`

## Panic
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `panic_entry_freeze_guard` | 패닉셀 구간에서 scalping 신규 BUY pre-submit freeze canary를 열 수 있는지 보는 축 | 계약 미준비: approval artifact를 만들어도 live 반영 불가 | `approval_contract_missing` | `-` | - | approval artifact를 만들어도 소비할 코드 계약이 없어 live 반영할 수 없다 | 0.37 | `contract_missing` | approval 계약 미준비 |
| `panic_buy_runner_tp_canary` | 패닉바잉 구간에서 fixed TP 전량청산 대비 runner 유지가 missed upside를 줄이는지 보는 축 | report-only: TP/trailing/live exit 변경 없음 | `freeze` | `-` | - | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 0.45 | `contract_missing` | 소스 품질 차단, panic_buy_orderbook_collector_coverage_gap |

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-05-21.json`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-05-21.json`
