# Tuning Automation Data Flow

작성 기준: `2026-05-28 KST`

이 문서는 튜닝 자동화체인의 현재 데이터 흐름, producer/consumer 계약, 적용 권한, 운영 체크포인트만 정리한다. 과거 실행 이력은 포함하지 않는다. 운영 원칙과 active/open 판정은 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 실행 항목은 [당일 checklist](./checklists/2026-05-28-stage2-todo-checklist.md), 시간대별 운영 확인은 [time-based operations runbook](./time-based-operations-runbook.md), 산출물 추적성은 [report-based automation traceability](./report-based-automation-traceability.md)를 우선한다.

## 핵심 원칙

- 자동화체인의 기본 흐름은 `R0_collect -> R1_daily_report -> R2_cumulative_report -> R3_manifest_only -> R4_preopen_apply_candidate -> R5_bounded_calibrated_apply -> R6_post_apply_attribution`이다.
- 목표는 손실 억제가 아니라 기대값과 순이익 극대화다. 승률은 `diagnostic_win_rate`이고 적용 판단은 `primary_ev`, source-quality, contract, rollback guard를 함께 본다.
- 장중 runtime threshold mutation은 금지한다. 적용 단위는 장후 report/calibration/AI review -> 다음 PREOPEN runtime env -> 장후 attribution이다.
- sim/probe/counterfactual은 후보 발굴과 source bundle에는 사용할 수 있지만 real execution 품질, 실주문 전환, cap release, provider route 변경 근거로 단독 사용할 수 없다.
- `workorder 승인`은 코드 구현 착수 승인이고, `approval artifact 승인`은 이미 구현된 approval contract의 다음 PREOPEN 적용 승인이다. 둘 다 `allowed_runtime_apply=true`, env mapping, runtime hook, rollback/post-apply attribution이 없으면 runtime 변경 권한이 없다.
- `selected` 또는 runtime env 반영은 real trading authority와 다르다. selected family라도 `runtime_effect=false`일 수 있고, sim-only/dry-run family는 실제 주문/청산 권한을 갖지 않는다.
- Project/Calendar 동기화는 사용자가 표준 명령으로 수행한다. AI는 직접 동기화하지 않는다.

## 현재 권한 경계

| 영역 | 현재 권한 | 금지선 |
| --- | --- | --- |
| Hard safety | broker submit guard, stale quote, price freshness, hard/protect/emergency stop, account/order/cooldown/quantity guard | LDM/ADM/discovery/runtime bridge가 우회할 수 없음 |
| Fixed threshold | score, VPW, strength, momentum, entry score cutoff는 baseline prior 또는 bounded tunable feature | score 단독 BUY/WAIT/DROP 결정 금지 |
| Scalping sim/probe | `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_observation_only` | real execution quality 또는 full-live 전환 근거 금지 |
| Swing dry-run | dry-run self-improvement, sim-auto, source-only workorder | full live conversion, dry-run 제거, cap/provider/bot 변경은 사용자 승인 필요 |
| Swing phase0 real canary | one-share initial/scale-in real canary만 bounded approval 가능 | full swing real-order conversion, cap release, provider/bot 변경으로 확장 금지 |
| Pattern lab | source-quality warning, source-only design input, code-improvement order | runtime env, order, provider, bot 변경 권한 없음 |
| Sentinel/panic/system detector | report-only/source-quality/incident input | threshold, order, provider, bot restart, automated liquidation 직접 변경 금지 |
| AI transport | provenance/transport quality 확인 | threshold 값, 주문가/수량 guard, strategy edge 판단과 분리 |

## 전체 흐름

| 단계 | 역할 | 주요 산출물 | 소비 주체 | 적용 여부 |
| --- | --- | --- | --- | --- |
| `R0_collect` | runtime, sim, broker, monitor event 수집 | `pipeline_events`, `threshold_events`, broker receipt, post-sell/sim state | R1 reports, LDM, detector | 없음 |
| `R1_daily_report` | 당일 source 정규화 | BUY/HOLD/EXIT sentinel, panic, openai/ws, swing/scalping reports | EV, LDM, workorder, verifier | 없음 |
| `R2_cumulative_report` | daily-only와 rolling/cumulative 대조 | cumulative reports, LDM history, bucket history | runtime apply bridge, preopen apply | 없음 |
| `R3_manifest_only` | 후보, source bundle, workorder 생성 | `threshold_cycle_ev`, LDM, Swing LDM, bucket discovery, workorder | runtime summary, bridge, verifier | 직접 없음 |
| `R4_preopen_apply_candidate` | guard, AI, contract, approval 확인 | `threshold_apply_YYYY-MM-DD.json` | runtime env generator | 조건부 후보 |
| `R5_bounded_calibrated_apply` | 다음 장전 env 생성 | `threshold_runtime_env_YYYY-MM-DD.env/json` | bot startup/runtime hooks | 있음 |
| `R6_post_apply_attribution` | 적용/미적용/차단 효과 평가 | post-apply attribution, EV, runtime summary, verifier | 다음 cycle 입력 | 다음 cycle |

## 수집 데이터 계층

| 데이터 종류 | 예시 | 수집 목적 | 소비 위치 | 금지선 |
| --- | --- | --- | --- | --- |
| Real execution | broker order, fill, sell receipt, completed trade | 실제 체결, 손익, execution 품질 평가 | EV, runtime approval, post-apply attribution | sim/probe와 섞어 real quality 주장 금지 |
| Sim/probe | `scalp_ai_buy_all`, `scalp_sim_*`, swing dry-run/probe | selection/entry/submit/holding/scale_in/exit 가상 표본 확대 | LDM, Swing LDM, EV, bucket discovery | 단독 실주문 승인 금지 |
| Counterfactual | missed entry, wait6579 EV, post-sell MFE/MAE | 놓친 기회, 회피손실, 후행성과 측정 | calibration, LDM bucket, bridge 후보 | 실현손익과 합산 금지 |
| Sentinel/report-only | BUY/HOLD/EXIT sentinel, panic sell/buying, error detector | 운영 이상치와 source-quality 감시 | incident, source bundle, workorder | threshold/order/provider 변경 금지 |
| AI transport | OpenAI WS, Bedrock override provenance | provider/transport 품질 확인 | checklist, AI transport report | strategy threshold 효과와 분리 |
| Runtime env/apply | selected family env, approval artifact | 다음 장전 적용 | bot runtime, post-apply attribution | artifact/contract 없는 수동 env 우회 금지 |

## 핵심 Producer/Consumer 계약

| Producer | 주요 산출 | Consumer | 소비 계약 |
| --- | --- | --- | --- |
| `lifecycle_decision_matrix` | scalping `entry/submit/holding/scale_in/exit/overnight` bucket attribution, `lifecycle_flow_bucket_attribution` | `lifecycle_bucket_discovery`, `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`, verifier | parent flow가 promotion EV owner다. stage-only holding/exit는 child evidence이며 단독 live/sim-auto 승격 금지 |
| `lifecycle_bucket_discovery` | `sim_auto_approved`, `live_auto_apply_ready`, `runtime_blocked_contract_gap`, `code_patch_required`, `source_contract_changes` | `runtime_apply_bridge`, sim-auto approval, runtime summary, workorder, verifier | deterministic 1차 분류 뒤 postclose AI Tier2 review가 명시적 gap만 차단한다. parsed가 아니면 pre-final live auto는 fail-closed |
| `runtime_apply_bridge` | entry/scale live-auto bridge, greenfield lifecycle policy candidate | `threshold_cycle_preopen_apply`, EV, runtime summary, verifier | discovery live candidate contract, Tier2 parsed, source-quality, env mapping, runtime hook, post-apply attribution 필요 |
| `swing_lifecycle_decision_matrix` | swing `selection/entry/holding/carry/scale_in/exit` row, bucket attribution, parent flow attribution | `swing_lifecycle_bucket_discovery`, EV, runtime summary, workorder, verifier | `swing_daily_simulation`은 forbidden legacy source다. Swing source는 source-only/sim-auto discovery 보강 범위 |
| `swing_lifecycle_bucket_discovery` | Swing parent flow/stage bucket 분류, sim-auto candidates, source-only workorders | EV, runtime summary, sim-auto approval, workorder, verifier | complete parent flow만 sim-auto 가능. stage-only entry/holding/scale-in/discovery-arm은 child evidence 또는 source-only |
| `threshold_cycle_ev` | real/sim/combined split, family EV, source warnings | runtime summary, control tower, workorder, verifier | combined는 diagnostic only. EV primary field는 `source_quality_adjusted_ev_pct`, `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct` 중 하나 |
| `runtime_approval_summary` | 사용자 개입 요구, blocked/observe/live 후보 요약 | checklist, runbook, verifier | downstream handoff 누락을 숨기지 않음 |
| `code_improvement_workorder` | implementation order, source-quality/order hook gap | 사용자 Codex 지시, checklist | workorder 자체는 runtime change가 아님 |
| `threshold_cycle_postclose_verification` | predecessor freshness, handoff, authority, verifier status | runbook, checklist, next-day work | 누락은 `automation_handoff_gap`, source/AI issue는 warning/fail로 표면화 |

## Scalping Lifecycle Flow

Scalping lifecycle의 parent flow는 `entry -> submit -> holding -> optional scale_in -> exit` 구조다.

| 항목 | 현재 계약 |
| --- | --- |
| Producer | `src/engine/lifecycle_decision_matrix.py`의 `lifecycle_flow_bucket_attribution` |
| Identity 우선순위 | bridge key, ADM candidate bridge, sim record, candidate id, fallback identity |
| Required stages | `entry`, `submit`, `holding`, `exit` |
| Optional stage | `scale_in` |
| Parent bucket type | `combo_lifecycle_flow` |
| Metric scope | `lifecycle_bundle_ev` |
| Promotion owner | complete parent flow bucket |
| Stage-only bucket | child evidence. holding/exit 단독 live/sim-auto 승격 금지 |
| Greenfield live authority | complete parent flow가 discovery에서 `live_auto_apply_ready`가 되고 runtime bridge policy contract가 통과할 때만 다음 PREOPEN 후보 |
| Incomplete flow | join gap/source-quality workorder와 verifier fail/warning source |

## Swing Lifecycle Flow

Swing lifecycle의 parent flow는 scalping flow bucket 계약을 축소 이식한 구조다. 새 실주문 정책이 아니라 source-only/sim-auto discovery 보강이다.

| 항목 | 현재 계약 |
| --- | --- |
| Producer | `src/engine/swing_lifecycle_decision_matrix.py`의 `swing_lifecycle_flow_bucket_attribution` |
| Identity 우선순위 | `lifecycle_flow_bridge_key`, `lifecycle_join_bridge_key`, `join_bridge_key`, `swing_strategy_discovery_arm_id`, `candidate_id`, `stock_code + event_time` fallback |
| Required stages | `entry`, `holding` 또는 `carry`, `exit` |
| Optional stage | `scale_in` |
| Parent bucket type | `combo_swing_lifecycle_flow` |
| Metric scope | `swing_lifecycle_bundle_ev` |
| Promotion owner | complete parent flow bucket |
| Stage-only bucket | `entry_bucket_attribution`, `holding_exit_bucket_attribution`, `scale_in_bucket_attribution`, `discovery_arm_attribution`은 child evidence |
| Runtime authority | `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true` |
| Forbidden uses | real order, one-share canary, scale-in real canary, cap release, provider route, bot restart, threshold mutation |

## AI Reviewer 기준

| 경로 | 현재 기준 |
| --- | --- |
| Postclose automation standard path | 표준 postclose wrapper가 OpenAI reviewer provider를 명시한다 |
| Direct Python/default lightweight path | 모듈별 기본값을 따른다. `none` 기본값으로 설계된 lightweight/direct module은 wrapper/env가 명시하지 않으면 OpenAI로 승격하지 않는다 |
| Prompt contract | 내부 reviewer/prompt/schema instruction은 English ASCII |
| AI authority | AI는 deterministic live 후보를 새로 승격하지 못한다 |
| Fail-closed | AI unavailable, timeout, parse reject, Tier2 missing은 pre-final live auto를 차단 |
| Ambiguity | 작은 효과, 낮은 confidence, 신규 bucket, 모호함만으로 deterministic live 후보를 차단하지 않는다 |
| Block reason | source-quality/schema/env mapping/runtime hook/post-apply attribution/safety/broker/stale/quantity/cooldown/provider/cap/forbidden-use gap만 명시 차단 |

## 결과 적용 경로

| 후보 유형 | 예시 | 적용되려면 필요한 것 | 적용 시점 | 결과 |
| --- | --- | --- | --- | --- |
| Auto bounded family | `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe` | deterministic guard, AI/source-quality guard, same-stage conflict 없음 | 다음 PREOPEN | env 자동 생성 |
| Runtime bridge live-auto | `scale_in_bucket_runtime_policy_v1`, complete greenfield lifecycle bundle | discovery `live_auto_apply_ready`, Tier2 parsed, env mapping, runtime hook, post-apply attribution | 다음 PREOPEN | targeted live auto env 후보 |
| Entry-only bridge metadata | `entry_wait6579_score66_69_recovery_gate_v1` | entry dimension/provenance only | 없음 | PREOPEN live env 후보 아님 |
| Sim-auto bucket | scalping/swing `sim_auto_approved` | source-quality pass, sim policy contract, forbidden-use 유지 | 다음 PREOPEN | sim policy input. real order 권한 없음 |
| Swing dry-run auto apply | swing dry-run env candidate | parsed Tier2, hard floors, source-quality gates | 다음 PREOPEN | dry-run env 후보 |
| Swing phase0 real canary | one-share initial/scale-in canary | parsed Tier2, source hard floors, allowlist, caps, source-quality gates | 다음 PREOPEN | bounded one-share scope |
| Approval artifact family | cap release, provider/bot change, full-live conversion, hard safety relaxation | user approval artifact, allowed runtime apply, env/runtime/post-apply contract | 다음 PREOPEN 또는 별도 승인 경로 | artifact scope로 제한 |
| Code workorder | instrumentation, handoff, taxonomy, source gap | 사용자가 Codex 구현 지시, 코드/테스트/검증 통과 | 구현 후 다음 cycle | 기능/계측/계약 보강 |
| Source-only bucket | stage-only bucket, pattern lab design input, report-only sentinel | rolling/source-quality 보강 또는 새 owner/contract 필요 | 없음 | 관찰/워크오더 유지 |

## 상태값 해석

| 상태/필드 | 현재 의미 | 운영 해석 |
| --- | --- | --- |
| `approval_required=true` | discovery 범위 밖 승인 경로가 필요할 수 있음 | 지금 승인 가능하다는 뜻은 아님 |
| `allowed_runtime_apply=false` | runtime apply 차단 | approval artifact가 있어도 env로 들어가면 안 됨 |
| `runtime_effect=false` | report/source/workorder 계층 | 실매매 로직 변경 아님 |
| `actual_order_submitted=false` | sim/probe/source-only provenance | real execution 품질 근거 아님 |
| `broker_order_forbidden=true` | broker order 금지 계약 | 실주문 또는 canary 권한 없음 |
| `classification_state=source_only_keep_collecting` | 관찰 유지 | 수동 env 적용 금지 |
| `classification_state=sim_auto_approved` | 다음 PREOPEN sim policy 자동 후보 | real order/provider/bot/cap/threshold 변경 권한 없음 |
| `classification_state=live_auto_apply_ready` | discovery/bridge가 닫힌 next PREOPEN live auto 후보 | hard/broker/stale/quantity/cooldown guard 우선 |
| `classification_state=runtime_blocked_contract_gap` | runtime contract 미완성 | workorder/source-quality follow-up |
| `classification_state=code_patch_required` | hook/taxonomy/consumer 구현 필요 | 구현, self review, tests 전 env 적용 금지 |
| `bridge_candidate_state=bootstrap_pending` | rolling/sample/confirmation 부족 | 승인하지 않고 다음 표본 확인 |
| `source_contract_changes` | source/bucket field/type/dimension 신규/삭제/변경 | 신규는 candidate, 삭제/field loss는 patch/source-quality blocker |
| `automation_handoff_gap` | producer 산출이 downstream에서 누락 | verifier fail/warning 및 workorder 대상 |
| `selected` in apply plan | PREOPEN env 반영 대상 | runtime effect/sim-only/dry-run authority 별도 확인 |
| `post_apply_attribution` | 적용 효과와 차단 사유 추적 | 다음 cycle 판단 입력 |

## 자동화체인이 닫아야 하는 질문

| 질문 | 닫는 artifact | PASS 조건 | FAIL/WARNING 조건 |
| --- | --- | --- | --- |
| 데이터가 수집됐나? | source reports, detector, freshness | 필수 source fresh/parse ok | missing/stale/parse fail |
| 데이터가 해석 가능한가? | source-quality audit, LDM, Swing LDM, EV | join/provenance/sample/source contract pass | source_quality_blocker, instrumentation_gap |
| 후보가 surfaced 됐나? | LDM, discovery, EV, workorder, bridge | 후보/blocked/workorder 상태가 downstream에 보임 | automation_handoff_gap |
| runtime 적용 가능한가? | runtime_apply_bridge, approval contracts | contract/env/hook/post-apply attribution ready | runtime_blocked_contract_gap |
| AI review가 닫혔나? | discovery AI review, threshold AI review | parsed 또는 explicit non-live/source-only 처리 | fail-closed, parse_rejected, unavailable |
| 실제 env에 들어갔나? | apply plan, runtime env | selected + env key present | blocked/no env |
| 봇이 env를 읽었나? | process env, startup log | env loaded | pre_env_boot_gap |
| 적용 효과가 추적되나? | post-apply attribution, EV | selected/applied cohort 기록 | provenance gap |

## 운영 체크포인트

| 시점 | 확인 항목 | 대표 artifact | 판정 |
| --- | --- | --- | --- |
| PREOPEN | 전일 산출물이 env로 반영됐는지 확인 | `threshold_apply_YYYY-MM-DD.json`, `threshold_runtime_env_YYYY-MM-DD.env/json` | applied, blocked, no-env 분리 |
| INTRADAY | selected family provenance와 safety guard 확인 | runtime events, detector, sentinel | runtime mutation 없이 관찰 |
| PRECLOSE | sim overnight/active state 같은 시간 기반 source 확인 | preclose reports, cron log | source-quality pass/fail |
| POSTCLOSE | 수집, 분석, 라우팅, workorder/approval, attribution 확인 | EV, runtime summary, LDM, discovery, workorder, verifier | GREEN/YELLOW/RED/GRAY |
| NEXT PREOPEN | approval/discovery/bridge 후보를 env 적용 | approval artifacts, sim-auto approvals, runtime bridge, apply plan | selected/env loaded |

## 현재 중요한 해석

- 후보 bucket 발굴/분류는 operator 기억이 아니라 postclose 자동화체인 책임이다.
- Parent lifecycle flow가 promotion EV owner다. Stage-only bucket은 child evidence이며 단독 live/sim-auto 승격 권한이 없다.
- `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`, `runtime_apply_bridge`, `swing_lifecycle_bucket_discovery`, `threshold_cycle_postclose_verification` 중 downstream 누락이 있으면 `automation_handoff_gap`으로 본다.
- `workorder`만 있어서는 runtime이 바뀌지 않는다. 구현, self review, supplemental fix, tests, report 재생성, approval/env/runtime/post-apply contract가 닫혀야 한다.
- New source/report/metric은 생성 시점에 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`, `runtime_effect`를 선언해야 한다. 계약이 없으면 `instrumentation_gap` 또는 `source_quality_blocker`로만 라우팅한다.
