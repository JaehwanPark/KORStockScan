# Runtime Apply Gap Audit 2026-05-21

## 판정

`workorder`와 `approval artifact`만으로 모든 튜닝 결과가 런타임 매매로직에 바로 적용되는 구조는 아니다.

현재 자동화 체인은 `보고서 후보 생성 -> workorder/source-only 분류 -> approval request -> preopen apply -> runtime env -> runtime hook -> post-apply attribution` 중 일부 family만 끝까지 연결되어 있다. 특히 LDM entry/scale-in bucket 후보는 `runtime_approval_candidates`와 code workorder까지 생성되지만, 모두 `allowed_runtime_apply=false`라 preopen apply가 런타임 env로 소비할 수 없다.

## 근거

- `runtime_approval_summary_2026-05-21.json`
  - LDM 상태는 `pass`, `ready_for_bounded_apply=true`.
  - `entry_bucket_runtime_candidate_count=10`, `scale_in_bucket_runtime_candidate_count=10`.
  - 두 bucket 후보 모두 `approval_required=true`, `allowed_runtime_apply=false`, `next_route=threshold_cycle_runtime_approval_request_after_rolling_confirmation`.
  - LDM 자체는 `runtime_effect=false`, `application_mode=auto_bounded_micro_canary`, `decision_authority=weighted_adm_source_bundle_for_auto_bounded_apply`.
- `code_improvement_workorder_2026-05-21.json`
  - selected order 19건 중 LDM entry/scale-in bucket 후속 workorder가 다수 포함된다.
  - 해당 workorder는 `runtime_effect=false`, `allowed_runtime_apply=false`.
  - 따라서 workorder는 Codex/개발 작업 지시 또는 source-quality 보강 지시이지 자동 repo 수정/자동 runtime 반영 지시가 아니다.
- `approval_contracts.py`
  - ready approval contract는 주로 `swing_model_floor`, `swing_selection_top_k`, `swing_gatekeeper_reject_cooldown`, `swing_market_regime_sensitivity`, `swing_one_share_real_canary_phase0`, `swing_scale_in_real_canary_phase0`다.
  - `position_sizing_cap_release`, `position_sizing_dynamic_formula`, `panic_entry_freeze_guard`, `panic_buy_runner_tp_canary`는 `contract_missing`.
  - unknown entry/scale bucket family는 기본적으로 `approval_contract_registry_entry`, `approval_artifact_loader`, `preopen_env_mapping`, `runtime_guard`, `rollback_tests`가 없는 상태로 판정된다.
- `threshold_cycle_preopen_apply.py`
  - preopen apply는 `allowed_runtime_apply=true`, 허용 state, AI guard, env override, same-stage owner guard를 통과한 family만 선택한다.
  - `allowed_runtime_apply=false` 또는 `family_type=sim_lifecycle_source`는 `runtime_apply_not_allowed` 또는 `non_live_selectable_sim_lifecycle_source`로 차단된다.
- `threshold_apply_2026-05-22.json`
  - `apply_mode=manifest_only`, `runtime_change=false`.
  - `swing_runtime_approval`은 requested 3, approved 3으로 별도 approval artifact가 소비된다.
  - scalping auto-apply selected는 0이며, LDM bucket 후보를 env로 바꾼 흔적은 없다.
- `threshold_runtime_env_2026-05-21.env`
  - `LIFECYCLE_DECISION_MATRIX_ENABLED=true`, `LIFECYCLE_AI_CONTEXT_ENABLED=true`.
  - 그러나 `LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED=false`, `SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=false`, `HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED=false`, `HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=false`.
  - 즉 LDM은 context/advisory로 로드되지만 bucket 성과가 곧바로 BUY/scale-in/exit action을 바꾸는 상태는 아니다.

## 런타임 적용 누락 지점

| 구분 | 현재 산출물 | 누락된 runtime bridge | 영향 |
|---|---|---|---|
| LDM entry bucket | `entry_bucket_runtime_approval_candidates`, code workorder | bucket을 named runtime family로 승격하는 decider, approval contract, env mapping, runtime hook, rollback/post-apply attribution | `score_66_69`, `wait6579_ev_cohort` 같은 신호가 실매매 entry gate에 바로 적용되지 않음 |
| LDM scale-in bucket | `scale_in_bucket_runtime_approval_candidates`, code workorder | arm/bucket별 scale-in runtime policy family, approval contract, env mapping, `sniper_scale_in` hook, rollback/post-apply attribution | `PYRAMID`, `AVG_DOWN_ONLY`, blocker별 성과가 실제 추가매수 정책으로 자동 전환되지 않음 |
| rolling confirmer | `next_route=threshold_cycle_runtime_approval_request_after_rolling_confirmation` 문자열 | daily bucket 후보를 rolling/cumulative 검증 후 approval request로 만드는 명시 decider | “언젠가 조건 충족 시 자동 승인 요청” 경로가 선언만 있고 실제 적용 family로 닫히지 않음 |
| code workorder | `implement_now`, `attach_existing_family`, `design_family_candidate` | 자동 코드 수정/테스트/리포트 재생성 executor | 사용자가 Codex 구현을 지시해야 코드가 바뀜 |
| approval artifact | 일부 swing contract ready | scalping bucket/position sizing/panic/provider route contract | 등록되지 않은 family는 artifact를 만들어도 preopen apply가 소비하지 못함 |
| Bedrock Lite/Micro one-day | 독립 decider/report-only artifact | provider route approval contract와 runtime route env apply | 의도적으로 기존 threshold/LDM/workorder 자동 apply와 분리되어 있음 |
| scalp sim overnight | 15:20 sim observation/LDM source row | live order authority, threshold apply authority | 튜닝 데이터 수집용이며 실주문/하드게이트로 직접 적용되지 않음 |

## 런타임 적용이 이미 연결된 축

- `soft_stop_whipsaw_confirmation`: calibration metadata, target env, runtime env, runtime consumer가 연결되어 있다.
- `score65_74_recovery_probe`: broad score 65~74 canary 축은 env/runtime hook이 있다. 다만 `score_66_69 + wait6579_ev_cohort` 같은 LDM bucket별 정밀 승격과는 별개다.
- `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `scalp_sim_scale_in_window_expansion`: sim 관찰 확대 축으로 runtime env가 있으나 real order authority는 없다.
- `lifecycle_decision_matrix_runtime`: policy/context load와 advisory prompt overlay는 연결되어 있다. 현재는 `runtime_effect=false`로 bucket action mutation은 꺼져 있다.
- `swing_*` approval: ready contract가 있는 dry-run env 및 one-share/scale-in real canary 범위만 별도 artifact로 적용 가능하다.

## 다음 액션

1. `LDM bucket -> runtime family` bridge를 별도 workorder로 만든다.
   - 첫 후보: `entry_wait6579_score66_69_recovery_gate_v1`
   - 입력: LDM entry bucket daily + rolling/cumulative confirmation
   - 출력: named approval request, approval contract, preopen env keys, runtime guard/hook, rollback/post-apply attribution
2. `scale_in_bucket_runtime_policy_v1` bridge를 별도 설계한다.
   - `PYRAMID`, `AVG_DOWN_ONLY`, blocker reason별로 real/sim 권한을 분리한다.
   - 실주문 scale-in은 별도 approval artifact 없이 열지 않는다.
3. `runtime_apply_gap`을 postclose checklist owner로 둔다.
   - workorder/approval artifact가 실제 런타임 적용 가능한지 매일 `contract_ready`, `env_mapping_ready`, `runtime_hook_ready`, `post_apply_attribution_ready`로 닫는다.
4. 사용자 승인 문구를 분리한다.
   - `workorder 승인`: Codex 구현/수정 착수 승인.
   - `approval artifact 승인`: 이미 구현된 contract의 다음 PREOPEN 적용 승인.
   - `runtime route/threshold 변경 승인`: provider/order/threshold/bot 변경을 별도로 지시하는 승인.

## 구현 후 bridge 상태

- 신규 bridge owner: `runtime_apply_bridge`
  - 출력: `data/report/runtime_apply_bridge/runtime_apply_bridge_YYYY-MM-DD.{json,md}`
  - 적용 권한: report 자체는 `runtime_effect=false`이며, `bridge_candidate_state=ready_for_approval`와 별도 approval artifact가 모두 있을 때만 다음 PREOPEN env 후보가 된다.
- Entry bridge: `entry_wait6579_score66_69_recovery_gate_v1`
  - approval artifact: `data/threshold_cycle/approvals/ldm_entry_runtime_bridge_YYYY-MM-DD.json`
  - runtime hook: 기존 `score65_74_recovery_probe`/`wait6579_probe` env 경로를 재사용하며, 승인 후 score range를 `66~69`로 좁힌다.
  - guard: hard safety, stale quote, liquidity, overbought, latency, broker/account/order/qty/cooldown guard 우선순위는 유지된다.
- Scale-in bridge: `scale_in_bucket_runtime_policy_v1`
  - approval artifact: `data/threshold_cycle/approvals/ldm_scale_in_runtime_bridge_YYYY-MM-DD.json`
  - runtime hook: `SCALPING_ENABLE_PYRAMID`, `REVERSAL_ADD_MIN_*`, `SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP` env 경로를 사용한다.
  - guard: `can_consider_scale_in`, buy-side pause, pending/cooldown, near-close, price resolver, dynamic qty cap을 우회하지 않는다.
- preopen apply 보강:
  - contract 없는 unknown family artifact는 소비하지 않는다.
  - artifact가 있어도 `ready_for_approval`이 아니면 `runtime_apply_blocked_bridge_not_ready`로 닫는다.
  - 선택된 bridge에는 `runtime_apply_bridge_family`, `bridge_candidate_id`, `source_bucket_key`, `approval_id`, `actual_runtime_effect` provenance를 남긴다.
