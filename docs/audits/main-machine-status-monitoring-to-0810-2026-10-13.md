# Main 기계판정 점검 — 2026-10-13 08:10 KST 종료

**Intraday Control State: RED.** 현재 PID의 기계판정·정책 소비는 확인됐지만, 두산의 보조판정은 원 예산 내 응답 timeout과 진입 전용 회로 OPEN으로 막혔고 비상시감시는 관측 ENTER 이후 Main 편입 최종화 실패가 남는다. warm Main loop 자체의 5초 초과는 관측되지 않았다.

관측은 08:03:13부터 08:10까지 수행하고 당일 기동 이후의 보존 근거를 함께 대사했다. 최종 읽기는 08:10:24이며 **08:10:00 이후 capture/trace/pipeline/performance 사건은 집계에서 제외**했다. 성능은 종료 전 마지막 주기 영수증 **08:09:51.369661** 기준이다. [최종 집계와 상세 근거](../../tmp/machine-status-monitor-20261013-0810/final-summary.json), [08:10 경계 표본](../../tmp/machine-status-monitor-20261013-0810/sample-081028.json).

## 1. 선택 릴리스·정책·실제 소비

- Main PID **2164993**, start ticks **9505700**, 실제 기동 07:55:10. 종료 경계까지 같은 PID/cwd를 반복 확인했다.
- cwd: `/home/ubuntu/KORStockScan-runtime-releases/main-residual-reviewed-20261013-v6/src`; selected commit `2223ac9e948cdbf79bf2ed1e1b6c4c5d7f069df6`와 일치.
- [당일 bootstrap PID 검증](../../data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-13.json)은 07:55:13 `pass`, PID/env mismatch 0, runtime policy fail 0이다. launcher 선택 영수증만으로 소비를 확정하지 않고 아래 자연 capture의 동일 PID/start/cwd를 대조했다.
- 자연 machine bundle `d906615b11d8d9175930a0c7e1bed3f7d7f1c7dd237a129814c7629de49f0a5b`, family `745df78f7234a6b02e2b57f6623ce31846e6f8dd642643a095648f8c4fd3be7c`. source/publication 10/12, effective 10/13. 보조 component `8820f40353ce96332aeb78ab5591d69b7a08cd16c64e67cef78be98c929ab04a`의 자연 소비 참조도 확인했다.
- 삼성·두산은 PRE 경로에 입장했으나 **HPSP 403870·알테오젠 196170·주성 036930**은 `fixed_watch_nxt_eligibility_unproven`으로 대기한다. 이 문구는 NXT 적격 근거 미확인이며 실제 비상장/등록불가를 확정하지 않는다. 삼성의 자연 기계 capture는 본 창에 없으므로 판정 소비를 두산의 근거로 대신하지 않는다.

## 2. 기계판정 분모

당일 payload 파일의 complete 행 중 exact PID이며 `evaluation_role=main_live|probe_observation`인 기계 action을 고유 attempt로 집계했다. source/preflight의 `unspecified_legacy` 행은 이 판정 분모에 중복 합산하지 않았다.

| 모집단 | 고유 판정 | ENTER_NOW | BLOCK | RECHECK / source-invalid |
|---|---:|---:|---:|---:|
| Main live — 두산 034020 | 99 | 99 | 0 | 0 / 0 |
| 비상시감시 probe — 10종목 | 17 | 14 | 3 | 0 / 0 |

이는 저장된 명시적 기계판정의 분모다. preflight에서 capture 이전에 끝난 준비 시도·guard·local 미평가를 전체 116개 평가와 같은 분모로 합산하지 않으며, 116건 전부 실주문 판정이라는 뜻도 아니다. probe의 `ENTER_NOW`는 관측이며 Main admission·execution claim·독립 live 판정이 필요하다.

비상시감시의 실제 matched branch에는 기존 branch와 새 `manual_residual_0d7e29b0230e5b49`, `manual_residual_bac0e83e966ed3ea`가 포함된다. 새 6정의/4scope 전체의 자연 소비가 끝났다는 뜻은 아니다. BLOCK 3건의 저장 사유는 `no_current_operating_signal`이다. pipeline에 `native_observation_no_matching_pattern`·`feature_window_incomplete`의 별도 진단도 있으며 둘을 정상 미충족 하나로 합치지 않는다.

## 3. 판정 이후의 현재 병목

### 보조판정과 진입 회로

현재 PID의 `analyze_target` HTTP 예산 timeout 오류는 **7회**다. process 성능의 provider transport 표본도 7개이며 정상 응답 검증 `response_validate`는 0이다. 예산 오류의 실제 남은 HTTP budget은 **465~3404ms**, 마지막 오류는 08:07:20이다. 본 창에 자연 AI PASS는 확인되지 않았고 `submit_guard`·order acknowledgement 표본과 실제 Kiwoom order-start bucket은 **0**이다. 주문 거부/미체결로 해석하지 않는다.

08:09:51 snapshot은 **entry transport OPEN / generation 5 / failures 7 / local not-evaluated 82 / recovery lease inactive**, 미정산 future 0이다. **provider-common circuit은 CLOSED / failures 0**이다. 상위 legacy `state=enabled`만 읽어 진입 보조판정이 정상이라고 표시하지 않는다. 정상 자연 HALF_OPEN 회복은 이 종료 경계에 입증되지 않았다. 오류 7개·local 미평가 82개와 machine 99개의 exact attempt 보존식은 tail 밖 trace/미확정 시도가 있어 전수 closure로 선언하지 않는다.

### 신호 소비 시간

| 시계/지표 | N | p95 | p99 또는 최대 |
|---|---:|---:|---:|
| 기존 warm loop metric | 2,395 | 0.315초 | p99 0.639초 / max 1.259초 |
| native confirmation→claim | 225 | 4.933초 | max 4.995초 |
| Main capture 당시 signal age | 99 | 4.954초 | max 4.984초 |

warm loop 5초 초과는 **0회**다. 첫 loop/초기 기동은 별도 metric이며 반복 source 준비·신호 소비 비용은 운용 구간에 포함한다. warm loop가 빠르더라도 원 5초 신호의 claim·capture가 늦으면 후속 AI 여유가 줄어든다. 위 p95는 서로 다른 분모이며 최대값을 합산해 특정 timeout의 critical path로 만들지 않는다.

native lifecycle의 `claimed=225`는 기계 capture 99개와 같은 수가 아니다. `invalidated_before_claim=839`, `unobservable=447`, `not_yet_due=4`도 보존한다. 단순 age 집계의 expired 수를 놓친 실행 기회나 수익으로 바꾸지 않는다. FIRST/branch 생존·원천 준비·각 claim 실패의 직접 원인을 후속 exact timeline에서 확인해야 한다.

### 비상시감시 Main 편입

보존한 제한 pipeline 표본에서 고유 `zero_base_watch_attach` **5건**은 모두 `attach_or_db_finalize_failed`다. 실제 `scalping_scanner_runtime_target_attach`가 먼저 `new_watching_target_attached`를 남긴 뒤 최종 실패한 사례도 있다. 종료 전 other execution claim은 0이며 비상시감시의 Main live machine capture도 본 모집단에서 확인되지 않았다.

08:09:11의 010950 실패 영수증에서 `zero_base_finalize_receipt={}`다. selected 코드에서 finalize는 payload에 `_zero_base_finalize_receipt`를 붙이지만 해당 실패 caller는 result를 `_zero_base_attach_receipt`에 넘기는 경계가 있다. 이는 상세 원인 유실의 코드 근거이며 실제 DB/native 실패 원인을 대신 확정하지 않는다. 실패 사례의 원 capture→physical lease→record→PID/start와 첫 실패 영수증을 복원 가능한 현재 사실로 대조하는 것이 다음 수리 대상이다. 과거 원인을 추정해 쓰거나 target·주문을 다시 실행하지 않는다.

## 4. 원천·checklist owner 상태

관측 중 auth 8005 fresh 오류 없음과 process/thread 생존, 자원 health PASS를 확인했다. 건강한 프로세스와 실패한 진입 보조판정 회로를 같은 정상으로 합치지 않는다. 08:10 이전 health에는 10/12 `reversal_auxiliary_tuning/.../evaluation.json`의 `policy_generation_contract_invalid`와 holding semantic/report 경고가 남는다. 이 보고서 경고는 현재 bootstrap PID 검증 실패로 단정할 수 없다. 이 요청에서 비관련 holding/장후 producer를 실행하거나 정책을 다시 발행하지 않았다.

[오늘 checklist](../checklists/2026-10-13-stage2-todo-checklist.md)의 OPEN 7개를 다음과 같이 분류했다. 원 checkbox/AUTO 봉인은 수정하지 않았다.

| 기존 owner | 08:10 상태·다음 경계 |
|---|---|
| DirectFamilyPreopenPolicyHandoff | Main 기동·PID/env·자연 machine 소비 근거 확인. 전체 family/보고서 수용은 원 Acceptance와 별도로 유지 |
| AuxiliaryCircuitRecoveryRepair1012 | 07:55~08:15 자연 수용 진행 중, entry circuit OPEN으로 회복 acceptance 미충족 |
| NonfixedDispatchReadinessReview1012 | 같은 08:15 경계 전이나 실제 편입 최종화 결손 확인. 5/long2 전체 수용과 6정의 전수 자연 소비 완료를 선언하지 않음 |
| DirectFamilySourceRepairCompactAuxiliary / EntryCancelWait / EntrySplit / MainMechanisticEntry | 16:30~21:40 POSTCLOSE `not_yet_due`. 현재 source gap/insufficient state 보존, 조기·중복 producer 실행 0 |

본 창은 PRE이고 30/60분 outcome·실현 terminal/cost의 충분한 성숙 전이다. 신호·원천·AI·실제 submit/fill·경제성은 별도 상태로 남긴다. Main-only/퇴역 자동 실행 경계를 적용했고 retired receipt 부재를 복구 대상으로 만들지 않았다.

## 5. 다음 액션과 점검 한계

1. **AuxiliaryCircuitRecoveryRepair1012:** same-attempt native event→Main 방문→claim→prepare→HTTP budget→회로 lease/terminal을 연결하여 원 5초를 소진한 최초 경계를 확인한다. 원 TTL·provider/주문 guard를 유지한 처리 수리와 자연 HALF_OPEN의 실제 결과를 검증한다. 회로 reset·provider 시험 호출·재기동으로 표본을 만들지 않는다.
2. **NonfixedDispatchReadinessReview1012:** 위 실패의 첫 native/DB 단계와 payload/result receipt 유실을 기존 ACK/rollback 경로에서 닫는다. 실제 Main claim·live 판정이 한 번 도달하고 실패 receipt가 원 record/lease/attempt에 연결되는 것이 closure test다. 성공 target 생성만으로 수용하지 않는다.
3. **기존 startup/readiness owner:** 3종목 PRE NXT 적격 근거의 producer/cache/consumer를 확인하고 source 부족과 실제 비적격을 구분한다. 10/12 보조 policy-generation 보고서 경고는 해당 보고서 계약 owner에 별도 인계한다.

이번에는 scratch의 bounded 읽기·집계와 본 감사 문서만 작성했다. trading code·설정·policy·selector·잠금·주문·provider 호출·재기동 변경은 0이다. 각 active writer는 stat 후 최대 16MiB tail만 읽었고, trace/pipeline의 **tail 사이 공백 때문에 전체 분모·전수 lineage 정상은 입증하지 않았다**. 완전한 작은 payload와 exact PID 성능 snapshot의 숫자, 제한된 실패 영수증의 숫자를 구분했다. 읽은 offset/end/hash는 각 표본에 보존했다.

문서 검증은 링크·print-only parser·diff 검사로 닫는다. 코드 수정이 없어 pytest/compile·광범위 보고서 재생성·외부 sync는 수행하지 않는다. 08:15 이후 모니터링은 이번 사용자 지정 08:10 종료 범위에 포함하지 않았다.

검증 결과: 로컬 링크 4개 결손 0, print-only parser 23항목·당일 startup/보조회로/비상시감시 owner 각 1개·경고 0, `git diff --check`·문서 공백 검사 PASS. checklist SHA `d78ceb2746413341c030744b4c0e3e7ebb09ad47eb9f26ebe9691941dcc56740`는 점검 중 유지했다. 동시에 진행 중인 별도 개선계획의 변경은 보존했다. 위 검사는 관측 문서의 유효성이며 진입 병목의 코드 수리 완료 증거가 아니다.
