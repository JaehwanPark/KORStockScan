# Tuning Automation Data Flow

작성 기준: `2026-05-22 KST`

이 문서는 튜닝 자동화체인의 데이터 수집, 소비/해석, 후보화, 승인/구현, 런타임 적용, 사후 attribution 흐름을 한 장으로 정리한다. 운영 원칙과 active/open 판정은 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md), 날짜별 실행 항목은 [당일 checklist](./checklists/2026-05-22-stage2-todo-checklist.md), 시간대별 운영 확인은 [time-based operations runbook](./time-based-operations-runbook.md), 산출물 추적성은 [report-based automation traceability](./report-based-automation-traceability.md)를 우선한다.

## 핵심 원칙

- 자동화체인의 기본 흐름은 `R0_collect -> R1_daily_report -> R2_cumulative_report -> R3_manifest_only -> R4_preopen_apply_candidate -> R5_bounded_calibrated_apply -> R6_post_apply_attribution`이다.
- 목표는 손실 억제가 아니라 기대값/순이익 극대화다. 승률은 보조 진단이고, runtime 적용 판단은 EV와 source-quality/contract/guard를 함께 본다.
- 장중 runtime threshold mutation은 금지한다. 기본 적용 단위는 장후 report/calibration/approval -> 다음 PREOPEN runtime env -> 장후 attribution이다.
- sim/probe/counterfactual은 후보 발굴과 source bundle에는 쓸 수 있지만 real execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
- `workorder 승인`은 코드 구현 착수 승인이고, `approval artifact 승인`은 이미 구현된 approval contract의 PREOPEN 적용 승인이다. 두 경로 모두 `allowed_runtime_apply=true`, preopen env mapping, runtime hook, rollback/post-apply attribution이 없으면 실매매 로직 변경으로 해석하지 않는다.
- 주요 사람 개입 지점은 one-day decider 판정/확인, real canary/provider/cap release처럼 discovery 범위 밖 approval 판단, Project/Calendar 수동 동기화다. lifecycle bucket discovery의 sim-auto/live-auto 분류와 entry/scale bridge 적용에는 사람 approval을 요구하지 않는다.
- `selected` 또는 runtime env 반영은 real trading authority와 다르다. selected family라도 runtime effect가 `false`일 수 있고, sim-only env는 실제 주문/청산 권한을 갖지 않는다.
- 2026-05-22 정책 변경 이후 `lifecycle_bucket_discovery`가 전체 lifecycle bucket 후보를 자동 발굴/분류한다. deterministic 1차 분류 뒤 tier3 OpenAI reviewer가 영어 프롬프트로 `1차 해석 -> 2차 감리 -> 최종 결론`을 검증한다. AI reviewer는 승격권은 없지만, 1% 수준의 효과, 낮은 confidence, 신규 bucket, 모호함만으로 deterministic live 후보를 막지 않는다. AI unavailable/parse fail 또는 모호한 판단은 `post_apply_verification` follow-up으로 넘기고, 명시적 source-quality/schema/env mapping/runtime hook/post-apply attribution/safety/broker/stale/qty/cooldown/provider/cap/forbidden-use gap만 block한다. `sim_auto_approved`는 사람 승인 없이 다음 PREOPEN sim policy에 들어가고, entry/scale bridge 후보가 `live_auto_apply_ready`이면 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비된다. 이 경우에도 hard safety, stale quote, broker/account/order/qty/cooldown guard, provider route, bot restart, position cap release는 우회하지 않는다.

## 현재 적용/대기/구현 스냅샷

이 표는 `2026-05-22` 장전 apply plan과 `2026-05-21` postclose 산출물을 기준으로 한다. 자동화 흐름을 이해한 뒤 “그래서 지금 무엇을 적용하고 무엇을 기다리는가”를 확인하는 운영용 요약이다.

### 적용/승인 완료 및 미반영 승인

| 항목 | 현재 상태 | runtime 의미 | 다음 확인 |
| --- | --- | --- | --- |
| `soft_stop_whipsaw_confirmation` | `selected=true`, `calibration_state=adjust_up`, env 반영 | 스캘핑 holding/exit bounded tunable. hard/protect/emergency/order guard 우회 없음 | 장후 post-apply attribution과 HOLD/EXIT EV 확인 |
| `score65_74_recovery_probe` | `selected=true`, `calibration_state=adjust_up`, env 반영 | 스코어 65~74 회복 probe. entry hard safety, stale quote, broker/account/order/qty/cooldown guard 우선 | 장중 provenance와 장후 submitted drought/EV 확인 |
| `scalp_sim_candidate_window_expansion` | `operator_locked`, env 반영 | 스캘핑 sim 후보창 확대. score 55~100 WAIT/blocked 후보를 sim-only로 수집 | sim/probe source-quality와 open/closed count 확인 |
| `scalp_sim_ai_budget_manager` | `operator_locked`, env 반영 | 확대된 sim holding의 AI 호출 예산/쿨다운 제어 | OpenAI 호출량, deferred review, sim holding coverage 확인 |
| `lifecycle_decision_matrix_runtime` | `selected=true`, env 반영 | LDM/ADM advisory와 AI context 연결. `RUNTIME_EFFECT_ENABLED=false`, `PROMOTE_ENABLED=false`라 실매매 action 변경 권한 없음 | LDM entry/scale-in/holding bucket attribution과 bridge 후보 확인 |
| `scalp_sim_scale_in_window_expansion` | 사용자 approval artifact 승인, env 반영 | `PYRAMID,AVG_DOWN` scale-in window를 sim-only로 관찰. `actual_order_submitted=false`, `broker_order_forbidden=true` | scale-in sim row, 후행 MFE/MAE/exit label, LDM scale-in bucket join 확인 |
| `swing_gatekeeper_reject_cooldown` | 별도 approval artifact 승인, selected | 스윙 dry-run entry cooldown `7200 -> 6600` 적용 | swing dry-run attribution 확인 |
| `swing_one_share_real_canary_phase0` | 별도 real canary approval artifact 승인, selected | 승인된 3개 코드에 한해 1주 real canary `BUY_INITIAL/SELL_CLOSE` scope. non-canary/sim/scale-in action은 계속 차단 | real receipt/provenance, 1주 cap, daily/open position cap 확인 |
| `swing_model_floor` | approval artifact에는 포함됐지만 `selected=false` | `no_runtime_env_override`라 이번 apply에서는 env 변경 없음 | 다음 approval/apply에서 env override 필요 여부 확인 |

### 대기 중이지만 아직 승인 대상이 아닌 항목

| 항목 | 현재 상태 | 왜 바로 적용하지 않는가 | 다음 판정 |
| --- | --- | --- | --- |
| `entry_wait6579_score66_69_recovery_gate_v1` | discovery/bridge live-auto 대상 | score 66~69 wait6579 bucket은 source-quality/route와 runtime hook이 닫히고 AI가 명시적 gap을 찾지 않으면 `live_auto_apply_ready`로 PREOPEN 자동 소비 | blocked면 source-quality/표본 보강, AI 모호함은 post-apply verification, ready면 approval artifact 없이 env 후보 |
| `scale_in_bucket_runtime_policy_v1` | discovery/bridge live-auto 대상 | `PYRAMID`, `AVG_DOWN_ONLY` bucket은 route가 `candidate_tighten_or_exclude`이고 AI가 명시적 gap을 찾지 않은 경우에만 live-auto tighten 후보 | positive/reference bucket은 observe-only로 두고, hold_no_edge 또는 명시적 contract/safety gap은 live auto 금지 |
| `swing_scale_in_real_canary_phase0` | policy는 `approval_required`, `runtime_apply_allowed=false` | source-quality blocker, final exit/post-add MAE 등 승인 계약 미충족 | 별도 approval artifact 생성 전 source-quality/label 보강 |
| `BedrockNovaMicroOneDayDecision0522` | 05-22 POSTCLOSE one-day decider 예정 | provider 비교는 기존 threshold/LDM apply에 연결하지 않는 임시 판정 artifact | winner 확정 후 Micro shadow/duel OFF 또는 profile candidate 기록 |
| `BedrockNovaLiteTier2PromotionReview0522` | 05-22 POSTCLOSE one-day decider 예정 | Lite v1은 Tier2 route 후보만 만들며 즉시 provider route 변경 금지 | winner가 Lite이면 `tier2_nova_lite_v1` route 후보 기록, 별도 approval/workorder 필요 |
| `BedrockNovaLiteV2ShadowImplementation0522` | 05-26 report-only shadow 준비 판정 예정 | Lite v2는 v1 승격 판단과 별개인 future report-only 실험 | 05-26 시행 조건, model id, env toggle, artifact path 확정 |
| `ScalpSimOvernightPrecloseCron0522` | 15:20 첫 운영 확인 예정 | sim overnight action은 LDM feature/source row이며 hard gate가 아님 | active undecided/source-quality/OpenAI provenance/Bedrock shadow 확인 |
| `lifecycle_bucket_discovery` | 신규 구현 | 전체 lifecycle bucket을 deterministic 분류한 뒤 tier3 AI 2-pass review로 `existing_bucket_refinement`, `new_bucket_candidate`, `sim_auto_approved`, `live_auto_apply_ready`, `runtime_blocked_contract_gap`, `code_patch_required`, `automation_handoff_gap`을 최종화한다. AI prompt는 영어로 유지하고, 모호함/작은 효과는 차단 근거가 아니다. LDM source contract drift도 `source_contract_changes`로 표면화한다 | 다음 PREOPEN sim policy/live auto bridge와 postclose verifier handoff 확인 |

### 구현 예정 또는 구현 검토 항목

| 항목 | 현재 owner | 구현해야 할 것 | runtime 적용과의 관계 |
| --- | --- | --- | --- |
| `RuntimeApplyBridgeAutomationImplementation0522` | 05-22 POSTCLOSE checklist | `lifecycle_bucket_discovery`로 성과 후보 bucket 자동 발굴, tier3 AI 2-pass 검증, source contract drift 감지, sim-auto/live-auto/runtime-blocked/code-patch/new-bucket 자동 분류, surfaced 누락 시 `automation_handoff_gap` 처리 | 구현 후 sim-auto는 사람 승인 없이 적용되고, 명시적 AI gap이 없는 entry/scale `live_auto_apply_ready`는 approval artifact 없이 다음 PREOPEN live auto apply 후보가 된다 |
| `RuntimeApplyBridgeGapAudit0522` | 05-22 POSTCLOSE checklist | workorder/approval artifact가 `contract -> env mapping -> runtime hook -> post-apply attribution`까지 이어지는지 audit | audit 자체는 적용이 아니라 누락 탐지. 누락은 구현 workorder로 넘긴다 |
| `code_improvement_workorder_2026-05-21` implement_now 묶음 | code improvement workorder | selected 19건 중 `implement_now` 16건. entry bucket unknown/source-quality, holding-exit counterfactual, scale-in bucket handoff instrumentation/report/provenance 보강 | 대부분 `runtime_effect=false`, `allowed_runtime_apply=false`다. 코드 보강 후 bridge/approval 후보를 만드는 입력이 된다 |
| holding/exit, provider, position sizing, panic bucket bridge 확장 | 아직 별도 bridge owner 필요 | entry/scale-in 외 bucket에 대해 별도 owner, approval contract, env mapping, runtime hook, rollback/post-apply attribution 정의 | 현재 `runtime_apply_bridge` 범위 밖이다. 성과가 확인되면 새 workorder로 bridge 확장 |

### 현재 해석 요약

- 스캘핑 실매매 영향 후보는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`처럼 apply plan에서 selected되고 runtime hook이 있는 bounded family다. 스윙 실매매 영향은 `swing_one_share_real_canary_phase0`의 승인된 1주 canary scope로 제한된다.
- 이미 적용됐지만 실매매 권한이 없는 항목은 `scalp_sim_candidate_window_expansion`, `scalp_sim_ai_budget_manager`, `scalp_sim_scale_in_window_expansion`, `lifecycle_decision_matrix_runtime`의 advisory/context 부분이다.
- 이미 승인됐지만 이번 env에 실제 값이 안 들어간 항목도 있다. `swing_model_floor`가 그 경우다.
- `approval_required=true`는 discovery 범위 밖에서 “나중에 approval route가 필요할 수 있다”는 뜻이다. entry/scale discovery bridge는 `approval_required=false`, `live_auto_apply_ready`일 때 사람 승인 없이 다음 PREOPEN 후보로 소비된다.
- “무엇을 적용할 것인가”는 매일 POSTCLOSE에서 후보 surfaced, bridge/approval readiness, source-quality, sample/EV를 닫고, 다음 PREOPEN에서 apply plan이 최종 결정한다.

## 전체 흐름

| 단계 | 역할 | 주요 산출물 | 소비 주체 | 결과 적용 여부 | 사람 개입 |
| --- | --- | --- | --- | --- | --- |
| `R0_collect` | 런타임, 시뮬레이션, 감시 이벤트 수집 | `pipeline_events`, `threshold_events`, `post_sell_*`, sim state, broker receipt | 장중/장후 리포트 | 없음 | 없음 |
| `R1_daily_report` | 당일 source를 report로 정규화 | `buy_funnel_sentinel`, `holding_exit_sentinel`, `panic_*`, `swing_*`, `openai_ws`, `threshold_cycle_*` | threshold-cycle, runtime summary | 없음 | 장애 시 확인 |
| `R2_cumulative_report` | daily-only를 rolling/cumulative와 대조 | `threshold_cycle_cumulative`, LDM history, bucket history | preopen apply, bridge, EV report | 없음 | 없음 |
| `R3_manifest_only` | 후보 family와 source bundle 생성 | `threshold_cycle_YYYY-MM-DD.json`, calibration, AI review | `threshold_cycle_preopen_apply` | 직접 적용 없음 | workorder 검토 가능 |
| `R4_preopen_apply_candidate` | guard, contract, approval, artifact 확인 | `threshold_apply_YYYY-MM-DD.json` | runtime env 생성기 | 조건부 적용 후보 | approval artifact 승인 |
| `R5_bounded_calibrated_apply` | 다음 장전 env 생성 | `threshold_runtime_env_YYYY-MM-DD.env/json` | `run_bot.sh`, runtime hooks | 있음 | 승인된 경우만 |
| `R6_post_apply_attribution` | 적용/미적용/차단 결과를 장후 평가 | `threshold_cycle_ev`, `runtime_approval_summary`, LDM, workorder | 다음날 튜닝 입력 | 다음 cycle 입력 | workorder 구현 지시 |

## 수집 데이터 계층

| 데이터 종류 | 예시 | 수집 목적 | 소비 위치 | 금지선 |
| --- | --- | --- | --- | --- |
| Real execution | broker order, fill, sell receipt, completed trade | 실제 체결, 손익, execution 품질 평가 | `threshold_cycle_ev`, runtime approval, post-apply attribution | sim/probe와 섞어 real quality 주장 금지 |
| Sim/probe | `scalp_ai_buy_all`, `scalp_sim_*`, swing dry-run/probe | 진입, 보유, scale-in, exit 가상 표본 확대 | LDM, EV report, workorder, approval request | 단독 실주문 승인 금지 |
| Counterfactual | missed entry, wait6579 EV, post-sell MFE/MAE | 놓친 기회, 회피손실, 후행성과 측정 | calibration, LDM bucket, bridge 후보 | 실현손익과 합산 금지 |
| Sentinel/report-only | BUY/HOLD/EXIT sentinel, panic sell/buying | 운영 이상치와 source-quality 감시 | incident, source bundle, workorder | threshold/order/provider 변경 금지 |
| AI transport/shadow | OpenAI WS, Bedrock Micro/Lite shadow | transport/provenance/provider 후보 비교 | one-day decider, AITransport checklist | 장중 provider route 변경 금지. 2026-05-22 기준 Micro one-day, Lite v1 Tier2, Lite v2 report-only 준비는 서로 다른 판정 경로다 |
| Runtime env/apply | selected family env, approval artifact | 실제 다음 장전 적용 | bot runtime, post-apply attribution | artifact/contract 없는 수동 env 우회 금지 |

## 소비와 해석 계층

| 소비 계층 | 입력 | 하는 일 | 산출 | 적용 권한 |
| --- | --- | --- | --- | --- |
| `threshold_cycle_ev` | threshold report, runtime summary, sim/real split | family별 EV, selected/blocked/hold 판단 | daily EV report | 직접 없음 |
| `runtime_approval_summary` | EV, swing approval, LDM bucket | 사용자 승인 필요, 차단, observe-only 분류 | approval summary | 직접 없음 |
| `lifecycle_decision_matrix` | entry/submit/holding/scale_in/exit source | bucket attribution, source-only 후보 생성 | LDM report | 기본 없음 |
| `runtime_apply_bridge` | LDM entry/scale-in bucket | discovery에서 AI 2-pass를 통과한 bucket 후보를 runtime family 후보로 정규화 | bridge report | 직접 없음 |
| `code_improvement_workorder` | pattern lab, EV, LDM, source-quality gaps | 코드 구현 필요 항목 생성 | workorder md/json | 직접 없음 |
| `threshold_cycle_preopen_apply` | threshold report, approval artifact, bridge, AI guard | 다음 장전 env 생성 여부 결정 | apply plan, runtime env | 있음 |
| Runtime hooks | env file, bot startup | 실제 매매 로직에서 feature/guard 반영 | runtime events | 있음 |
| Post-apply attribution | runtime events, completed trades | 적용 효과, 부작용, 차단 사유 평가 | 다음날 tuning source | 다음 cycle 입력 |

## 결과 적용 경로

| 후보 유형 | 예시 | 적용되려면 필요한 것 | 적용 시점 | 결과 |
| --- | --- | --- | --- | --- |
| Auto bounded family | `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe` | deterministic guard, AI/source-quality guard, same-stage conflict 없음 | 다음 PREOPEN | env 자동 생성. 단 selected env가 곧 real trading authority는 아님 |
| Approval artifact family | swing dry-run approval, one-share canary, scalp sim scale-in window | approval contract + user-approved artifact + `allowed_runtime_apply=true` + env mapping/runtime hook/rollback/post-apply attribution | 다음 PREOPEN | env 생성. scope는 artifact와 contract 범위로 제한 |
| Runtime Apply Bridge 후보 | `entry_wait6579_score66_69_recovery_gate_v1`, `scale_in_bucket_runtime_policy_v1` | `live_auto_apply_ready`, `allowed_runtime_apply=true`, env mapping, runtime hook, post-apply attribution, AI 명시적 gap 없음 | 다음 PREOPEN | approval artifact 없이 targeted env 생성. 현재 live-auto bridge 범위는 LDM entry/scale-in bucket |
| Lifecycle Bucket Discovery 후보 | `sim_auto_approved`, `live_auto_apply_ready` | discovery report, 영어 AI 2-pass review, bucket catalog, sim-auto approval, bridge contract/env/runtime hook/post-apply attribution | 다음 PREOPEN | sim policy 또는 entry/scale live auto env 생성. 사람 approval artifact 없음 |
| Code workorder | pattern lab/workorder `implement_now` | 사용자가 Codex 구현 지시, 코드/테스트 통과 | 구현 후 다음 cycle | 기능, 계측, 계약 보강 |
| Source-only bucket | LDM score/scale bucket, sim-only EV | rolling/source-quality 충족 후 bridge/workorder로 승격 필요. holding/exit, provider, position sizing, panic bucket은 별도 owner/contract/env hook이 있어야 bridge 확장 대상 | 없음 | 관찰 유지 |
| Shadow/provider 후보 | Nova Micro/Lite 비교 | one-day decider + 별도 approval/workorder. Micro, Lite v1, Lite v2는 합산하지 않고 profile/scope별로 판정 | 다음 PREOPEN 이후 | route 후보 기록, 즉시 변경 아님 |

## 승인과 구현의 차이

| 구분 | 의미 | 예시 | 사용자가 하는 일 | 바로 runtime 적용? |
| --- | --- | --- | --- | --- |
| Workorder 승인 | 코드를 구현해도 된다는 지시 | bucket 자동 발굴, bridge gap 보강 | Codex에 구현 지시 | 아님 |
| Approval artifact 승인 | 이미 구현된 contract를 다음 PREOPEN에 적용 승인 | `scalp_sim_scale_in_window_expansion`, swing canary | artifact 승인 | 조건부 가능. `allowed_runtime_apply=true`, env mapping, runtime hook, rollback/post-apply attribution, artifact/contract scope match가 모두 필요 |
| Bridge ready 확인 | approval 전에 runtime 연결 계약 확인 | `runtime_apply_bridge` | ready 후보만 승인 판단 | 자체 적용 아님 |
| Operator override | 사용자가 명시적으로 runtime env/bot 적용 지시 | 장중 특수 override | 명시 지시 필요 | 가능하지만 예외 |

## 자동화체인이 닫아야 하는 질문

| 질문 | 닫는 artifact | PASS 조건 | FAIL/WARNING 조건 |
| --- | --- | --- | --- |
| 데이터가 수집됐나? | source reports, detector, freshness | 필수 source fresh/parse ok | missing/stale/parse fail |
| 수집 데이터가 해석 가능한가? | source-quality audit, LDM, EV | join/provenance/sample pass | source_quality_blocker |
| 성과 후보가 surfaced 됐나? | LDM, EV, workorder, bridge | 후보가 분류됨 | automation_handoff_gap |
| runtime 적용 가능한가? | runtime_apply_bridge, approval_contracts | contract/env/hook/attribution ready | blocked_contract_gap |
| 사용자가 승인했나? | approval artifact | approved=true, policy match | missing/mismatch/not approved |
| 실제 env에 들어갔나? | apply plan, runtime env | selected + env key present | blocked/no env |
| 봇이 env를 읽었나? | `/proc/<pid>/environ`, startup log | env loaded | pre_env_boot_gap |
| 적용 효과가 추적되나? | post-apply attribution, EV | selected/applied cohort 기록 | provenance gap |

## 상태값 해석

| 상태/필드 | 현재 의미 | 운영 해석 |
| --- | --- | --- |
| `approval_required=true` | 언젠가 승인 경로가 필요하다는 뜻 | 지금 승인 가능하다는 뜻은 아님 |
| `allowed_runtime_apply=false` | runtime apply 차단 | approval artifact가 있어도 env로 들어가면 안 됨 |
| `runtime_apply_allowed=false` | swing policy 계층의 runtime apply 차단 필드 | threshold/bridge 계층은 주로 `allowed_runtime_apply`, swing policy 계층은 `runtime_apply_allowed`를 쓴다 |
| `runtime_effect=false` | report/source/workorder 계층 | 실매매 로직 변경 아님 |
| `bridge_candidate_state=bootstrap_pending` | 후보는 발견됐지만 rolling/confirmation 부족 | 승인하지 않고 다음 표본 확인 |
| `bridge_candidate_state=live_auto_apply_ready` | AI 2-pass, contract/env/hook/attribution이 닫힌 적용 후보 | approval artifact 없이 다음 PREOPEN env 후보 |
| `classification_state=sim_auto_approved` | discovery가 다음 PREOPEN sim policy에 자동 적용할 bucket | 실주문/청산/provider/bot/cap 변경 권한 없음 |
| `classification_state=live_auto_apply_ready` | discovery/bridge가 다음 PREOPEN live auto apply 후보로 소비할 bucket | AI는 승격권이 없고 명시적 gap만 차단한다. AI 모호함/미응답은 post-apply verification follow-up이며 hard/broker/stale/qty/cooldown guard는 그대로 우선 |
| `classification_state=code_patch_required` | generic hook으로 적용할 수 없는 bucket | 자동 patch 후보를 만들고 self review + fix 2-pass + tests 전에는 env 적용 금지 |
| `ai_two_pass_review_status` | discovery의 AI 검증 상태 | `parsed`가 아니어도 deterministic live 후보는 유지하고 post-apply verification을 남긴다. 명시적 contract/safety/source-quality gap만 live-auto 차단 |
| `source_contract_changes` | LDM이 소비하는 수집계층 source/bucket field/type/dimension 신규/삭제/변경 | 신규는 `new_bucket_candidate`, 삭제/field loss는 `code_patch_required` 또는 source-quality blocker로 라우팅 |
| `source_quality_blocker` | stale/missing/duplicate/provenance 결함 | threshold candidate 제외, instrumentation 보강 |
| `instrumentation_gap` | 필요한 관찰 필드/계약 부족 | 코드/계측 workorder 대상 |
| `selected` in apply plan | PREOPEN env 반영 대상 | runtime env와 봇 env uptake 확인. `selected_env != real trading authority`이며 runtime effect, sim-only authority, dry-run guard를 별도 확인 |
| `runtime env loaded` | 봇이 env를 읽음 | 이후 post-apply attribution 필요 |
| `post_apply_attribution` | 적용 효과와 차단 사유 추적 | 다음 cycle의 판단 입력 |

## 데이터에서 runtime 적용까지의 상세 경로

| 흐름 | 입력 source | 중간 판단 | 적용 gate | 최종 결과 |
| --- | --- | --- | --- | --- |
| Entry bucket tuning | wait6579 EV, missed entry, buy funnel, LDM entry attribution, lifecycle bucket discovery | score/source/stale/liquidity/time bucket EV + tier3 AI 명시적 gap review | `live_auto_apply_ready` + preopen apply | entry probe/env 조정 |
| Scale-in bucket tuning | LDM scale-in attribution, sim scale-in rows, post-sell labels, lifecycle bucket discovery | `PYRAMID`, `AVG_DOWN_ONLY`, blocker reason EV + tier3 AI 명시적 gap review | `live_auto_apply_ready` + safety guard 유지 | scale-in tighten/env 조정 |
| Holding/exit tuning | holding_exit_sentinel, post_sell_feedback, holding_exit_matrix, SAW | HOLD/EXIT/TRIM/defer/late rebound 판단 | selected family guard + runtime env | holding/exit bias 또는 soft-stop 조정 |
| Swing dry-run tuning | swing lifecycle audit, swing approval, swing simulation | dry-run floor/cooldown/canary 후보 | separate approval artifact | dry-run env 또는 one-share canary |
| Provider/AI transport | OpenAI WS, Bedrock Micro/Lite shadow rows, one-day decider | profile별 outcome-linked EV/MFE/MAE. Micro one-day는 winner 강제, Lite v1은 `gpt-5.4-mini` Tier2 profile별 판정, Lite v2는 2026-05-26 report-only 준비로 분리 | 별도 approval/workorder | route 후보 기록 또는 shadow OFF |
| Source-quality/instrumentation | detector, source-quality audit, pattern lab currentness/propagation | parse/stale/join/downstream gap | workorder 구현 | 계측/리포트/consumer 보강 |

## 사람 개입 지점

| 자동화 분류 | 사람의 역할 | 하면 안 되는 일 |
| --- | --- | --- |
| `source_only_keep_collecting` | 관찰 유지 여부만 확인 | 수동 env 적용 금지 |
| `bootstrap_pending` | 다음 rolling/표본 확인 | approval artifact 생성 금지 |
| `workorder_needs_codex_implementation` | Codex 구현 지시 여부 결정 | 구현 승인과 runtime 적용 승인 혼동 금지 |
| `approval_contract_ready` | discovery 범위 밖 approval artifact 생성 여부 결정 | contract 범위 밖으로 해석 금지 |
| `live_auto_apply_ready` | discovery/bridge 자동 적용 판단 | hard/broker/stale/qty/cooldown guard 우회 금지 |
| one-day decider 판정/확인 | Micro/Lite 같은 임시 비교 artifact를 실행하고 winner/next action을 확인 | latency/cost/parse/action match만으로 1차원 판정 금지 |
| Project/Calendar 수동 동기화 | 문서 backlog를 외부 Project/Calendar에 반영 | AI가 직접 동기화 실행 금지 |
| `runtime_apply_blocked_contract_gap` | 구현 workorder로 넘김 | 수동 env override 금지 |
| `automation_handoff_gap_candidate_not_surfaced` | 자동화체인 gap으로 fail/warning 처리 | operator 기억으로 수동 관리 금지 |

## 운영 체크포인트

| 시점 | 확인 항목 | 대표 artifact | 판정 |
| --- | --- | --- | --- |
| PREOPEN | 전일 산출물이 env로 반영됐는지 확인 | `threshold_apply_YYYY-MM-DD.json`, `threshold_runtime_env_YYYY-MM-DD.env` | `applied_guard_passed_env` 또는 blocked reason |
| INTRADAY | selected family provenance와 safety guard 확인 | runtime event, detector, sentinel | runtime mutation 없이 관찰. selected family도 runtime effect/sim-only/dry-run 여부를 분리 |
| PRECLOSE | sim overnight/active state 같은 시간 기반 source 확인 | `scalp_sim_overnight_*`, cron log | source-quality pass/fail |
| POSTCLOSE | 수집, 분석, 라우팅, workorder/approval, attribution 확인 | `threshold_cycle_ev`, `runtime_approval_summary`, LDM, workorder | GREEN/YELLOW/RED/GRAY |
| NEXT PREOPEN | 승인된 artifact와 discovery auto policy/live-auto 후보를 env 적용 | approval artifacts, discovery sim-auto, runtime_apply_bridge live-auto, apply plan | selected/env loaded |

## 현재 중요한 해석

- `approval_required`는 후보를 surfaced 했다는 뜻이지, 즉시 승인하라는 뜻이 아니다.
- `runtime_apply_bridge`는 사용자 승인 단계가 하나 늘어난 것이 아니라, discovery가 AI 명시적 gap review까지 거친 후보가 실제 runtime까지 연결 가능한지 자동으로 증명하는 중간 계약이다.
- 현재 `runtime_apply_bridge` 구현 범위는 LDM entry/scale-in bucket이다. holding/exit, provider route, position sizing, panic bucket은 별도 owner, approval contract, env mapping, runtime hook, rollback/post-apply attribution이 정의된 경우에만 bridge 확장 대상으로 본다.
- 후보 bucket 발굴/분류는 operator 기억이 아니라 postclose 자동화체인 책임이다.
- surfaced 되어야 할 후보가 `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`, `runtime_apply_bridge`, `threshold_cycle_postclose_verification` 중 어디에도 나타나지 않으면 `automation_handoff_gap`으로 봐야 한다. 수집계층 신규/삭제/변경은 LDM source contract drift로 따로 surfaced 되어야 한다.
- `workorder`만 있어서는 runtime이 바뀌지 않는다. 코드 구현, 테스트, report 재생성, approval contract/env mapping/runtime hook/post-apply attribution이 닫혀야 한다.
- discovery 범위 밖 approval artifact는 `allowed_runtime_apply=false`, contract mismatch, env mapping missing이면 apply가 차단되어야 정상이다. discovery entry/scale bridge는 `bridge_candidate_state=live_auto_apply_ready`일 때 approval artifact 없이 적용된다.
- 새 source/report/metric을 추가할 때는 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`, `runtime_effect`를 선언해야 한다. 계약이 없으면 `instrumentation_gap` 또는 `source_quality_blocker`로만 라우팅한다.
