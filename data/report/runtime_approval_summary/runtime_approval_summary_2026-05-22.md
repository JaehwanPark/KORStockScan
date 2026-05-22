# Runtime Approval Summary - 2026-05-22

- 목적: 스캘핑 threshold-cycle 판정과 스윙 runtime approval 판정을 한 화면에서 보는 읽기 전용 요약이다.
- runtime_mutation_allowed: `False`
- scalping_items/selected: `3` / `1`
- scalping_legacy_hard_gate_risk_counts: `{'no_unreviewed_hard_gate': 3}`
- swing_blocked/requested/approved: `0` / `0` / `0`
- swing_legacy_hard_gate_risk_counts: `{}`
- panic_approval_requested: `0`
- scalp_entry_adm_status: `missing`
- lifecycle_matrix_status: `pass`
- lifecycle_ai_context prompt/applied: `0` / `0`
- swing_strategy_discovery_labeled/pending: `0` / `0`
- institutional_flow_available/join_rate: `False` / `0.0`
- pattern_lab_currentness_status: `missing`
- pattern_lab_propagation_status: `missing`
- env_generated_at: `2026-05-22T07:46:10`
- first_bot_start_at: `2026-05-22T07:40:04`
- first_bot_start_after_env_at: `2026-05-22T07:46:34`
- pre_env_boot_gap: `True`

## Scalping
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `scalp_entry_action_decision_matrix_advisory` | 스캘핑 entry action(BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE 등)을 matrix EV로 비교해 AI action을 보정하는 운영 override 축 | 운영 override runtime bias: AI BUY를 WAIT/DROP 또는 defensive bias로 보정, submit safety guard 우선 | `hold_sample` | `entry_adm_runtime_bias_operator_override` | daily scalp_entry_action_decision_matrix -> threshold EV/runtime summary/workorder/pattern lab -> next runtime env | 운영 override runtime bias는 AI BUY를 WAIT/DROP 또는 defensive bias로 보정한다. daily action bucket EV와 runtime forced_action provenance가 충분해야 다음 env 튜닝 판단으로 넘어간다. | 없음 | `-` | 소스 품질 차단, ADM prompt context 미적재 |
| `lifecycle_decision_matrix_runtime` | 개별 후보 lifecycle row를 entry/submit/holding/scale-in/exit stage별 weighted ADM policy로 해석하는 umbrella runtime 축 | PREOPEN env 적용: 당일 runtime 변경 대상 | `adjust_up` | `umbrella_weighted_adm_runtime_policy` | postclose lifecycle_decision_matrix -> threshold EV/runtime summary -> next preopen bounded env | 선택 시 policy file/version만 다음 PREOPEN env로 연결한다. hard safety와 broker/account/order guard는 항상 matrix proposal보다 우선한다. | 3.4568 | `-` | auto_bounded_live 선택 |
| `latency_classifier_runtime_profile` | latency SAFE/CAUTION/DANGER classifier와 bounded submit recovery canary를 분리 적용하는 진입 실행품질 축 | 보류: 최신 recommendation 기준 다음 PREOPEN latency env 변경 없음 | `hold_sample` | `entry_execution_quality_bounded_tunable` | threshold-cycle latency recommendation plus post-apply latency_pass/order_bundle attribution | SAFE만 runtime pass로 보며 CAUTION은 기본 reject다. recovery canary가 명시되고 allowed_runtime_apply=true인 후보만 다음 PREOPEN bounded env로 연결한다. | 0 | `-` | latency_classifier_runtime_semantics_gap |

## Scalp Entry ADM
- status: `missing`
- runtime_bias_scope: `force_wait_force_drop_buy_defensive_bias`
- joined_action_ev_pct: `None`
- joined_sample/sample_floor: `0` / `20`
- prompt_applied_count: `0`
- missing_actions: `[]`
- top_actions: `[]`
- ready_for_daily_policy_tuning: `False`
- warnings: `['source_quality_blocker', 'joined_sample_below_sample_floor', 'prompt_context_not_loaded']`

## Institutional Flow Context
- artifact: `-`
- authority: `source_only_lifecycle_feature`
- rows ok/partial/missing/token_error: `0` / `0` / `0` / `0`
- join_rate_pct: `0.0`
- source_mix: `{}`
- top_net_buy: `[]`
- warnings: `['institutional_flow_context_missing']`

## Lifecycle Decision Matrix
- status: `pass`
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-22`
- runtime_bias_scope: `stage_action_proposal_micro_canary`
- total/joined/floor: `9863` / `9641` / `20`
- policy_pass/promote_ready: `5` / `0`
- fixed_threshold_roles: `{'hard_safety': ['broker_submit_guard', 'stale_quote_submit_block', 'price_freshness_guard', 'hard_stop', 'protect_stop', 'emergency_stop', 'account_order_cooldown_qty_guard'], 'baseline_prior': ['BUY_SCORE_THRESHOLD', 'VPW_MIN_SCORE', 'strength_momentum_cutoff', 'entry_score_cutoff'], 'bounded_tunable': ['SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION', 'SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation', 'holding_flow_override', 'scale_in_price_guard'], 'legacy_archive': ['fallback_scout_main', 'fallback_single', 'latency_fallback_split_entry', 'legacy_latency_composite', 'closed_shadow_axes']}`
- ready_for_bounded_apply: `True`
- warnings: `[]`

## Lifecycle AI Context
- context_artifact: `-`
- context_version: `-`
- prompt_stage_count: `0`
- attribution_artifact: `-`
- attribution eligible/applied/skipped: `0` / `0` / `None`
- stage_attribution: `{}`

## Swing
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| - | - | - | - | - | - | - | - | - | - |

## Swing Strategy Discovery Sim
- artifact: `-`
- available: `False`
- candidate/arm/labeled: `0` / `0` / `0`
- pending_future_quote_count: `0`
- top_surviving_arm: `-`
- avoid_bucket_count: `0`
- runtime_effect: `False`
- interpretation: source-only exploration. Surviving arms can create future source-quality/workorder inputs but cannot apply runtime env.
- warnings: `['swing_strategy_discovery_ev_missing']`

## Panic
| 항목 | 설명 | 현재 적용 | 상태 | Gate 분류 | 튜닝 경로 | 판정 해석 | 점수 | 계약 | 차단/판정 사유 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| - | - | - | - | - | - | - | - | - | - |

## Pattern Lab Audits
- currentness: status=`missing` fail=`0` artifact=`-`
- propagation: status=`missing` fail=`0` warnings=`0` artifact=`-`

## Warnings
- `swing_runtime_approval_missing`
- `scalp_entry_action_decision_matrix_missing`
- `institutional_flow_context_missing`
- `pattern_lab_currentness_audit_missing`
- `pattern_lab_propagation_audit_missing`
