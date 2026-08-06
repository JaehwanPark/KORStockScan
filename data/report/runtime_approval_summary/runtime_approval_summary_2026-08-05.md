# Runtime Approval Summary - 2026-08-05

- 목적: 스캘핑 threshold-cycle 판정과 스윙 runtime approval 판정을 한 화면에서 보는 읽기 전용 요약이다.
- runtime_mutation_allowed: `False`
- scalping_items/selected: `23` / `2`
- scalping_legacy_hard_gate_risk_counts: `{'approval_or_contract_required': 1, 'intentional_safety_guard': 4, 'manual_review_required': 4, 'no_unreviewed_hard_gate': 14}`
- swing_blocked/requested/approved: `0` / `0` / `0`
- swing_legacy_archive/phase0_ignored: `0` / `0`
- swing_legacy_hard_gate_risk_counts: `{}`
- panic_approval_requested: `0`
- scalp_entry_adm_status: `warning`
- lifecycle_matrix_status: `pass`
- lifecycle_bucket_windows_promotion: `pass` / `too_broad`
- lifecycle_ai_context prompt/applied: `3` / `715`
- swing_strategy_discovery_labeled/pending: `None` / `None`
- swing_lifecycle_matrix_auto: `None`
- swing_lifecycle_bucket_auto: `None`
- institutional_flow_available/join_rate: `True` / `100.0`
- microstructure_reaction_available/ok: `True` / `885`
- pattern_lab_currentness_status: `pass`
- pattern_lab_ai_review_status: `pass`
- producer_gap_discovery_status: `disabled_by_default`
- pattern_lab_propagation_status: `pass`
- env_generated_at: `2026-08-05T08:28:11`
- first_bot_start_at: `-`
- first_bot_start_after_env_at: `-`
- pre_env_boot_gap: `False`

## Microstructure Reaction Context
- available: `True`
- authority: `entry_confidence_modifier_source_only`
- rows ok/missing: `885` / `29482`
- real_submitted_count: `0`
- status_counts: `{'missing': 27029, 'not_evaluated': 1300, 'ok': 885, 'source_quality_partial': 151, 'stale': 1002}`
- entry_reaction_quality_counts: `{'-': 27029, 'favorable_reaction': 27, 'mixed_reaction': 351, 'neutral_unusable': 2453, 'risk_context_only': 326, 'weak_reaction': 181}`
- avg_scores ask/hold/bid: `49.597` / `49.912` / `54.877`
- max_vi_proximity_risk: `35`
- warnings: `[]`

## Scalping
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `soft_stop_whipsaw_confirmation` | soft stop 직후 반등 가능성이 큰 표본은 1회 확인 시간을 두고 성급한 청산을 줄이는 축 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `selected_runtime_canary` | threshold-cycle selected family attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | 표본 부족 |
| `holding_flow_ofi_smoothing` | 보유/청산 AI flow 결과에 OFI/QI 미시수급을 붙여 EXIT 확정 또는 보류를 다듬는 축 | 기존 적용 유지: holding_flow_override 내부 OFI/QI postprocessor ON | `hold_sample` | `existing_runtime_guard` | holding/exit EV attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.05 | `-` | 표본 부족 |
| `protect_trailing_smoothing` | protect/trailing 청산 후보에서 미시 반등 신호가 있으면 과조기 청산을 줄이는 축 | 기존 적용 유지: protect/trailing break confirmation guard ON; 값 변경은 PREOPEN bounded apply만 허용 | `hold_sample` | `existing_runtime_guard` | holding/exit EV attribution; threshold update is PREOPEN bounded only | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.55 | `-` | 표본 부족 |
| `trailing_continuation` | trailing 이후 추가 상승 여지가 큰 표본을 계속 보유할 수 있는지 보는 축 | 관찰/리포트 only: trailing 연장 live 미적용 | `freeze` | `holding_exit_safety_freeze` | source-quality and GOOD_EXIT risk review | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 1 | `-` | 동결 |
| `market_regime_continuous_thresholds` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.8 | `-` | 표본 부족 |
| `pre_submit_price_guard` | broker 제출 직전 quote stale, spread, passive probe 가격품질 문제를 막는 hard safety 축 | 기존 적용/검증 유지: 제출 직전 hard safety guard이며 auto_bounded_live 후보 아님 | `hold` | `intentional_pre_submit_safety_guard` | safety/source-quality report only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 0 | `-` | 유지 |
| `dynamic_entry_price_resolver` | bid-1/bid-2/bid-3/best_bid/AI/reference/timeout 후보별 체결품질과 EV를 비교하는 진입가 튜닝 축 | 선택 시 다음 PREOPEN dynamic entry price resolver env만 bounded 적용, submit safety guard 우선 | `hold_sample` | `entry_price_bounded_tunable` | threshold-cycle candidate fill/cancel/late-fill/source-quality adjusted EV attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | none, recovery floor 미달 |
| `entry_split_order_plan` | 기존 requested_qty를 보존하면서 planned_orders를 bucket별 leg/price offset/비중 policy로 분해하는 submit 직전 튜닝 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `entry_submit_split_bounded_tunable` | entry_split_order_plan report -> threshold-cycle calibration -> next PREOPEN policy file | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | `-` | auto_bounded_live 선택 |
| `scale_in_split_order_plan` | 기존 scale-in qty를 보존하면서 AVG_DOWN 물타기 주문을 leg/price offset policy로 분해하는 scale-in 직전 튜닝 축 | 선택 시 다음 PREOPEN scale-in split order policy env/file/version만 적용, scale-in qty 산정과 broker/account/order/quantity/cooldown guard는 변경 없음 | `hold_sample` | `not_classified` | manual runtime approval review | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0 | `-` | 표본 부족 |
| `entry_price_execution_quality` | real-only 제출/체결/취소/late-fill/partial/full fill 품질을 감사하는 실행품질 축 | real-only audit: submit/fill/cancel 품질 기록만 수행, runtime threshold apply 권한 없음 | `hold` | `real_execution_quality_audit` | real-only submit/fill/cancel/late-fill audit | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 0 | `-` | 유지 |
| `score65_74_recovery_probe` | family id는 score65_74로 유지하지만 현 runtime floor 기준 AI 점수 60~74 WAIT 구간 중 수급/가속 조건이 좋은 후보를 기본 신규 BUY sizing으로 회수하는 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `entry_unlock_probe` | runtime env/operator lock plus post-apply attribution | threshold-cycle guard 통과로 당일 PREOPEN env에 반영됨 | 1 | `-` | auto_bounded_live 선택 |
| `strength_momentum_soft_gate_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_gate` | AI/counterfactual risk context, source-quality exception only | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `overbought_pullback_guard_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_plus_pre_submit_guard` | overbought risk bucket EV and pre-submit guard attribution | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `liquidity_pre_submit_guard_p1` | 설명 미등록 | 기존 상태 유지: runtime 변경 없음 | `hold` | `softened_pre_ai_plus_pre_submit_guard` | liquidity risk bucket EV and real submit guard attribution | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 1 | `-` | 유지 |
| `bad_entry_refined_canary` | 진입 직후 never-green/AI fade 위험이 큰 표본을 조기 정리할 수 있는지 보는 축 | OFF/관찰 only: refined canary live 미적용 | `adjust_up` | `entry_quality_canary` | bad-entry cohort EV and rollback guard | 자동 반영 후보로 선택되면 PREOPEN env에 적용된다 | 1 | `-` | - |
| `holding_exit_decision_matrix_advisory` | 보유 중 가능한 행동(EXIT/HOLD/AVG_DOWN/PYRAMID)을 matrix 점수로 보조 판단하는 축 | 관찰/리포트 only: advisory live 적용 아님 | `hold_no_edge` | `advisory_report_only` | report-only decision support contract | 명확한 edge가 없어 runtime 변경은 하지 않는다 | 1 | `-` | edge 부족 |
| `scale_in_price_guard` | 추가매수 직전 best bid/defensive limit, spread, stale quote로 가격품질을 보장하는 축 | 기존 적용 유지: 추가매수 가격품질 guard ON | `hold_sample` | `intentional_pre_submit_safety_guard` | scale-in price quality EV/source-quality only | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 0.1 | `-` | 표본 부족 |
| `position_sizing_dynamic_formula` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_sample` | `candidate_grid_comparison_runtime_apply_blocked` | candidate grid comparison -> PREOPEN bounded candidate -> postclose attribution | 축은 유지/관찰하지만 표본/소스 계약 미충족으로 runtime 변경은 하지 않는다 | 1 | `-` | 소스 표본 없음 |
| `scalping_avg_down_recovery_quality_gate` | 설명 미등록 | 관찰/리포트 only: runtime 변경 없음 | `hold_no_edge` | `not_classified` | manual runtime approval review | 명확한 edge가 없어 runtime 변경은 하지 않는다 | 없음 | `-` | edge 부족 |
| `scalp_entry_action_decision_matrix_advisory` | 스캘핑 entry action(BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE 등)을 matrix EV로 비교해 AI action을 보정하는 운영 override 축 | 운영 override runtime bias: AI BUY를 WAIT/DROP 또는 defensive bias로 보정, submit safety guard 우선 | `hold_sample` | `entry_adm_runtime_bias_operator_override` | daily scalp_entry_action_decision_matrix -> threshold EV/runtime summary/workorder/pattern lab -> next runtime env | 운영 override runtime bias는 AI BUY를 WAIT/DROP 또는 defensive bias로 보정한다. daily action bucket EV와 runtime forced_action provenance가 충분해야 다음 env 튜닝 판단으로 넘어간다. | 없음 | `-` | 표본 부족 |
| `lifecycle_decision_matrix_runtime` | 개별 후보 lifecycle row를 entry/submit/holding/scale-in/exit stage별 weighted ADM policy로 해석하는 umbrella runtime 축 | 기본 OFF: 선택 시 micro canary env로 policy file/version만 연결, hard safety/submit guard 우선 | `hold` | `umbrella_weighted_adm_runtime_policy` | postclose lifecycle_decision_matrix -> threshold EV/runtime summary -> next preopen bounded env | 선택 시 policy file/version만 다음 PREOPEN env로 연결한다. hard safety와 broker/account/order guard는 항상 matrix proposal보다 우선한다. | -0.7348 | `-` | 유지 |
| `latency_classifier_runtime_profile` | latency SAFE/CAUTION/DANGER classifier와 bounded submit recovery canary를 분리 적용하는 진입 실행품질 축 | 보류: 최신 recommendation 기준 다음 PREOPEN latency env 변경 없음 | `hold_sample` | `entry_execution_quality_bounded_tunable` | threshold-cycle latency audit plus post-apply latency_pass/order_bundle attribution | SAFE/CAUTION은 slippage check 후 normal submit으로 보내고, DANGER/stale/broker safety만 submit 차단으로 유지한다. | 0 | `-` | latency semantics gap |
| `scalp_sim_overnight_ai_carry` | 장마감 후 open 스캘핑 sim 포지션을 overnight_v1로 SELL_TODAY/HOLD_OVERNIGHT 분리해 다음날 lifecycle/EV label로 연결하는 source-only 축 | source-only: sim 가상 청산/carry 기록만 수행, runtime threshold apply 권한 없음 | `observe_only` | `not_classified` | manual runtime approval review | runtime_effect=false source다. SELL_TODAY는 sim 가상 청산, HOLD_OVERNIGHT는 active_unrealized carry로만 남긴다. | - | `-` | 관찰 전용 |

## Scalp Entry ADM
- status: `warning`
- runtime_bias_scope: `force_wait_force_drop_buy_defensive_bias`
- joined_action_ev_pct: `0.0023`
- joined_sample/sample_floor: `4` / `20`
- prompt_applied_count: `478`
- missing_actions: `[]`
- top_actions: `[{'action': 'WAIT_REQUOTE', 'sample_count': 1, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'BUY_DEFENSIVE', 'sample_count': 2, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'NO_BUY_AI', 'sample_count': 578, 'joined_sample': 1, 'source_quality_adjusted_ev_pct': 0.0023}, {'action': 'SKIP_SOURCE_QUALITY', 'sample_count': 8, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': 0.0}, {'action': 'SKIP_PRE_SUBMIT_SAFETY', 'sample_count': 51, 'joined_sample': 3, 'source_quality_adjusted_ev_pct': -0.1247}]`
- ready_for_daily_policy_tuning: `False`
- warnings: `['joined_sample_below_sample_floor']`

## Institutional Flow Context
- artifact: `/home/ubuntu/KORStockScan/data/report/institutional_flow_context/institutional_flow_context_2026-08-05.json`
- authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `120` / `0` / `0` / `0`
- join_rate_pct: `100.0`
- source_mix: `{'ka10059+ka10061': 120}`
- top_net_buy: `[{'stock_code': '233740', 'smart_money_net': 3660809, 'foreign_net_roll5': 3210746, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '069540', 'smart_money_net': 1946915, 'foreign_net_roll5': 3143362, 'inst_net_roll5': 72711, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '229200', 'smart_money_net': 1530038, 'foreign_net_roll5': 0, 'inst_net_roll5': 0, 'regime': 'UNKNOWN'}, {'stock_code': '005930', 'smart_money_net': 1417149, 'foreign_net_roll5': 8054292, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '271050', 'smart_money_net': 1380437, 'foreign_net_roll5': 0, 'inst_net_roll5': 1847764, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '073240', 'smart_money_net': 1263454, 'foreign_net_roll5': 5312171, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '122630', 'smart_money_net': 1095182, 'foreign_net_roll5': 322744, 'inst_net_roll5': 62193, 'regime': 'DUAL_ACCUMULATION'}, {'stock_code': '477850', 'smart_money_net': 613957, 'foreign_net_roll5': 671113, 'inst_net_roll5': 0, 'regime': 'FOREIGN_ACCUMULATION'}, {'stock_code': '006360', 'smart_money_net': 600064, 'foreign_net_roll5': 0, 'inst_net_roll5': 1249592, 'regime': 'INSTITUTION_ACCUMULATION'}, {'stock_code': '000660', 'smart_money_net': 488245, 'foreign_net_roll5': 957487, 'inst_net_roll5': 814997, 'regime': 'DUAL_ACCUMULATION'}]`
- warnings: `[]`

## Lifecycle Decision Matrix
- status: `pass`
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-05`
- runtime_bias_scope: `stage_action_proposal_micro_canary`
- total/joined/floor: `835` / `100` / `20`
- policy_pass/promote_ready: `1` / `0`
- lifecycle_flow buckets/complete/runtime/workorders: `25` / `4` / `0` / `20`
- holding/exit buckets: `7` / `27`
- holding/exit workorders: `5` / `5`
- lifecycle identity missing/join_rate: `0` / `1.0`
- lifecycle complete_flow_rate: `0.0105`
- incomplete_flow_reason_counts: `{'missing_submit': 378, 'missing_holding': 378, 'missing_exit': 317, 'missing_entry': 141, 'candidate_id_only': 175, 'scale_in_noise_only': 80, 'postclose_exit_without_entry': 61, 'sim_record_id_only': 4}`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- ready_for_bounded_apply: `True`
- warnings: `[]`

## Lifecycle Bucket Windows
- promotion_window: `mtd`
- confirmation_windows: `['rolling5d', 'rolling10d']`
- windows: `{'rolling5d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-05_rolling5d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling5d', 'status': 'pass', 'parent_bucket_count': 27, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 70, 'absorbed_sample_count': 2550, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'rolling10d': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-05_rolling10d.json', 'window_role': 'rolling_confirmation', 'window_policy': 'rolling10d', 'status': 'pass', 'parent_bucket_count': 38, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'target_pass', 'absorbed_child_count': 101, 'absorbed_sample_count': 3617, 'child_conflict_warning_count': 1, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}, 'mtd': {'available': True, 'artifact': '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-05_mtd.json', 'window_role': 'promotion_confirmation', 'window_policy': 'mtd', 'status': 'pass', 'parent_bucket_count': 27, 'selected_parent_level': 'L2_default', 'parent_granularity_status': 'too_broad', 'absorbed_child_count': 70, 'absorbed_sample_count': 2550, 'child_conflict_warning_count': 0, 'live_auto_apply_ready_count': 0, 'source_contract_status': 'pass', 'ai_two_pass_review_status': 'parsed'}}`
- warnings: `[]`

## Lifecycle AI Context
- context_artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context/lifecycle_ai_context_2026-08-05.json`
- context_version: `lifecycle_ai_context_v1_2026-08-05`
- prompt_stage_count: `3`
- attribution_artifact: `/home/ubuntu/KORStockScan/data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-08-05.json`
- attribution eligible/applied/skipped: `715` / `715` / `0`
- stage_attribution: `{'entry': {'context_contribution_score': -0.349, 'bounded_auxiliary_weight': -0.0523, 'attribution_quality_status': 'observational_only_pending_outcome', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': 0.0014, 'no_context_replay_observed': 0}, 'submit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'holding': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'scale_in': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}, 'exit': {'context_contribution_score': 0.0, 'bounded_auxiliary_weight': 0.0, 'attribution_quality_status': 'hold_sample', 'source_quality_adjusted_ev_pct': None, 'ai_action_alignment_rate': None, 'no_context_replay_observed': 0}}`

## Swing
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| - | - | - | - | - | - | - | - | - | - |

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
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `panic_entry_freeze_guard` | 패닉셀 구간에서 scalping 신규 BUY pre-submit freeze canary를 열 수 있는지 보는 축 | 계약 미준비: approval artifact를 만들어도 pre-submit freeze runtime 반영 불가 | `hold` | `-` | - | 현재 적용 상태와 값을 유지하고 추가 env 변경은 하지 않는다 | 0.3 | `contract_missing` | 유지 |
| `panic_buy_runner_tp_canary` | 패닉바잉 구간에서 fixed TP 전량청산 대비 runner 유지가 missed upside를 줄이는지 보는 축 | report-only: TP/trailing/live exit 변경 없음 | `freeze` | `-` | - | 계측/DB/safety 문제로 runtime 변경을 금지한다 | 없음 | `contract_missing` | runtime_effect_not_report_only |

## Pattern Lab Audits
- currentness: status=`pass` fail=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-08-05.json`
- ai_review: status=`pass` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-08-05.json`
- producer_gap_discovery: status=`disabled_by_default` artifact=`-`
- propagation: status=`pass` fail=`0` warnings=`0` artifact=`/home/ubuntu/KORStockScan/data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_2026-08-05.json`
