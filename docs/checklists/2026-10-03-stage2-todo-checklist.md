# 2026-10-03 Stage2 To-Do Checklist

## 오늘 목적

- Main 기계·보조 정책 원천·승패 결함을 보완하고 리뷰·회귀 후 승인된 통합 배포와 장후 재생성을 완료한다.
- 다음 거래일 메인·위젯·에피소드의 정책 인계와 삼성전자/그 외 적용 범위를 재검증한다.

## 필수 규칙

- Plan Rebase §1–§8, 원천·비용·날짜·hash 및 기존 hard safety/owner 권한을 유지한다.
- 최신 사용자 지시로 보완분 커밋·배포·기동·정책 재생성을 승인받았다. 원천일10/2를 유지하고 기존 OFF·퇴역 및 주문/custody/hard safety를 보존한다.
- 10/6 자연 수용·PREOPEN stable ID는 해당 checklist에 남긴다. 출력은 검증과 실제 PID/경제성 증거를 구분한다.

## 실행 항목

- [ ] `[PostcloseOutcomeReadinessClosure1003] 승패 시간 비대칭·미평가 변경 탈락 보완, 통합 배포·재생성·다음 기동 준비 검증` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [실행계획](../proposals/postclose-outcome-readiness-closure-plan-2026-10-03.md), 최신 사용자 배포·기동 승인.
  - Acceptance: 동일10분 CF 목표/손절 비교, 미평가 원천 제외와 전체 후보 탈락 분리, 리뷰→보완→회귀; immutable release와 독립 service route/PID, 정확10/2 재생성→tower/checklist/strict/controller→10/6 준비 검증; 삼성005930/그 외의 실제 loader 정책/hash 구분. 새 정책 부재는 검증된 carry, 에피소드 연구 OFF는 OFF receipt로 표시한다.
  - Handoff: 10/6 PREOPEN·07:55 실제 PID·자연 체결/성과는 기존 `DirectFamilyPreopenPolicyHandoff` 및 source repair owner에서 확인한다. 현재 준비 검증으로 해당 미래 항목을 닫지 않는다.

- [x] `[PostcloseWinrateObjectiveMigration1003] 실제 기계·보조 승률 목적 이행 및 장후 성공 보존 제약 정리` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [W0~W4 실행계획](../proposals/postclose-policy-winrate-objective-migration-plan-2026-10-03.md).
  - Acceptance: 실제 생성기/검증기 100%·80% 보존 제약 정리, 목적/version/cache 회귀, 동일 보유 원천 격리 전후 비교, 전체 장후 정책 조사·후속계획, 두 기계 후보 custody/native/미평가 변경 검증, 반복 리뷰·보완·통합 커밋 준비·parser. 운영 발행·배포·재기동 대기; 기존10/6 자연 수용 owner 유지.
  - 완료: [반복 리뷰](../audits/postclose-policy-winrate-objective-migration-review-2026-10-03.md). 보존80% 제거로28.73bp 관측 후보 선택 후 native 분모 결함 보완. 최종 등록9·별도 기계88·보조 KRX12 후보에서 정식 신규 선정0, 개선 패턴/미평가/지원수 사유 분리. 삼성2건 exact 로그·주문 owner와 그 외17건 미평가를 확인. 통합1,460 tests·최종411 tests PASS, 격리 publisher가 중간 분모 보고서를 거부하고 최종 승계를 검증. 운영541 hash 보존 및 커밋 준비; 미커밋·미배포.

- [x] `[MachineDecisionCohortTargetFirstResearch1003] 현재 기계판정 집단 재분류 및 삼성전자·그 외 목표-first 재검증` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [1·2·3번 실행계획](../proposals/main-machine-decision-cohort-target-first-research-plan-2026-10-03.md).
  - Acceptance: 전체 동일 parent 재생·입력/비용/검열 분리·삼성 기존 후보 전체206감시행 검증·그 외 ENTER/soft-confirmation 내부 학습 고정/목표-first/후단 검증. 사용자 후속 기준에 따라 기계·보조 모두 기존 대비 승률을 우선하고 성공100% 보존을 후보 탈락 조건에서 제거한다. 성공/실패 제외·미평가 변경·순손익을 병기하고 보조 연구 selector/개선계획·보유 응답을 재검증한다. 표적회귀·원천/운영정책/기존 작업본 hash·문서 parser. 보조 production 통합·새 수집·정책 발행·커밋·배포·재기동 없음; 기존10/6 owner 유지.
  - 완료: [승률 우선 재검증 리뷰](../audits/main-machine-decision-cohort-target-first-research-review-2026-10-03.md). 전체7,069행 재생, 삼성 fixed-watch 목표2·미도달1 및 이전 ENTER 시간 가설 검증. 그 외 관측 필터의10/2 승률73.53→86.36%, 성공3/실패3 제외·절대 순경로 평균−0.0444%와 평가 제외17변경을 함께 기록했다. 보조 KRX43응답의 분리 재계산은 후단 승률 개선 미입증. 최종 기계run-04/보조auxiliary-winrate-02,109 tests PASS. 운영 장후100% 제약/목적 version 이행은 [보조 계획 A6](../proposals/auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md#a6-승률-우선-정책-선정-계약-이행--사용자-후속-기준)에 수립했다.

- [x] `[PartitionedContinuousPatternResearch1003] 삼성전자 연속 감시 및 삼성전자 제외 유형별 패턴 심화 연구` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [후속 상세계획](../proposals/partitioned-continuous-pattern-research-plan-2026-10-03.md).
  - Acceptance: Q0~Q6 분모·origin·관측 간격·과거 완료봉 특징·집단별 학습/시간순 검증·비용/과적합/실행성·검토수정·표적회귀·격리 결과·hash 보존·문서 parser. 기존60초 반복 노출0 해석을 정정하고 미도달과 결손을 분리한다. 새 수집/provider/정책 발행·배포·재기동 없음; 기존10/6 자연 owner 유지.
  - 완료: [분리 심화 연구 리뷰](../audits/partitioned-continuous-pattern-research-review-2026-10-03.md). 삼성519관측/fixed-watch206, 그 외6,550관측/702종목으로 분리했다. 과거 봉·흐름·유형·개별 horizon·원래 후보 유지·유형 조합·실제 간격 반복을 검증했다. 학습의 양의 성과는 후단에서 유지되지 않았고 추가 기계 ENTER0. 일부 유형 조합의 상대 손실 감소도 기존 ENTER 성공 보존에 실패했다. 86 tests 및541개 운영 정책 hash 보존; 신규 연구는 미커밋·미배포다.

- [x] `[SamsungPolicyScopeReplan1003] 삼성전자 전용 및 그 외 기계·보조 정책 연구 범위 재정리` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [세 범위 연구·계획 정리](../proposals/main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md).
  - Acceptance: native/AI 원천을 삼성전자와 그 외로 분리하고 기존 후보의 회수 여부·보조4개 규칙을 재확인한다. 삼성전자 기계/보조 연구→구현계획 확정 절차, 그 외 기계 변경 필요성, 그 외 보조 producer/consumer 계획을 정리한다. 링크/owner/권한·diff·print-only parser 검증. live 코드/정책·provider/주문·배포·재기동 없음.
  - 완료: 삼성전자 기계35시도/6기회·보조9응답/연결2, 그 외 기계64/63·보조34/연결12. 기존204개 후보에서 그 외 회수0, 보조4개 규칙의 그 외 재계산도 선정0. 삼성전자 연구는 별도 OPEN, 그 외 기계 규칙 변경계획은 보류, [그 외 보조 개선계획](../proposals/auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md)은 분모·cache·source 책임·검증을 보완했다. 근거는 `tmp/samsung-nonsamsung-policy-scope-replan-20261003/scope-census.json`이다.

- [x] `[SamsungDedicatedMachineAuxiliaryResearch1003] 삼성전자 전용 기계·보조 정책 연구와 구현계획 확정` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [삼성전자 S0~S5](../proposals/main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md).
  - Acceptance: 보유 원천으로 fixed-watch exact scope·native/episode 분모·새 기계 ENTER의 실제 auxiliary 응답 coverage를 고정하고, 기계/보조/결합 성과를 분리한다. 날짜·시간대 민감도·성공 보존·비용·결손·후단 재사용 한계를 보고하고 selector/parent/장후/loader/회귀/rollback 구현계획을 확정한다. synthetic native 기회·새 API/provider 수집·live 정책 적용 금지, 배포 대기 유지.
  - 완료: fixed-watch31시도/2기회·30조합, 기존2시도 회수와 정식 gate 미충족을 확인했다. 원응답 전수에서는 기존 PASS9 외 CAUTION1을 확인했고 fixed-watch PASS2·CAUTION1, 새 기계 ENTER의 exact AI 응답0이다. [전용 구현계획](../proposals/samsung-fixed-watch-machine-auxiliary-implementation-plan-2026-10-03.md)과 [실행 리뷰](../audits/samsung-auxiliary-scope-execution-review-2026-10-03.md)를 작성했다. 운영 정책/PREOPEN/PID 완료가 아니다.

- [x] `[NonSamsungAuxiliarySourceConsumerImplementation1003] 삼성전자 이외 보조판정 원천 생산자·장후 소비자 개선 구현` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: SourceQuality`)
  - Source: [삼성전자 이외 보조 AI 계획](../proposals/auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md).
  - Acceptance: A0~A5의 명시적 종목 분모·exact capsule·조건부 plan/stop·AI-stage/operating 분리·materiality/CAUTION 분석·cache 검증을 구현/리뷰/수정/표적 회귀/격리 재생성으로 닫는다. 공통 producer의 삼성전자 원천을 보존하며 source gap을0수익으로 만들지 않는다. 새 수집/provider·정책 배포·재기동 없음.
  - 완료: capsule/append/capacity 보존, 단계별 ledger, 조건부 plan·CAUTION·유형 진단, 비용 scope 표기 결함, 분리 cache/발행 차단을 구현·재리뷰했다. 원천42·유효응답34·exact 연결12·비용 결합 stage15, 보조12조합 행동 변화0. [실행 리뷰](../audits/samsung-auxiliary-scope-execution-review-2026-10-03.md)와 격리 cold/warm 일치·정책541개 hash 보존을 확인했다. 기존10/6 `DirectFamilySourceRepairCompactAuxiliary`는 자연 수용 owner로 유지한다.

- [x] `[MachineConfirmationCandidateResearch1003] 기계 확인 경로 후보 재생과 실제 선정 gate 검증` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [후속 연구계획](../proposals/main-machine-confirmation-candidate-research-plan-2026-10-03.md).
  - Acceptance: native 동일기회·학습 고정 후보의 실제 행동 변화, 비용 결합 승률·지원수·성공 보존·등록 gate·후단 재사용 한계·표적검증·hash 보존 audit. 보조 AI 생산자/장후 소비자 계획을 현재 최종 연구에 연결한다. 새 수집/provider/live 정책/배포/재기동 없음. 10/6 자연 수용 owner는 유지한다.
  - 완료: [후속 연구 리뷰](../audits/main-machine-confirmation-candidate-research-review-2026-10-03.md). 기존 확인 결합102개 변화0 후, setup 대체 가설을 포함한204개/2행동 vector에서 연구 후보1개를 찾았다. 삼성전자9/30·10/2 각각1시도 회수/목표-first, 기존 성공100% 보존. 삼성전자 제외 시 후보0, 후단 지원1<3 및 미등록 schema로 정식 선정0. 등록 VWAP 후보9개도 승계 유지. 241 tests PASS, 소스·정책 보존 검증 및 [보조 AI 생산자·소비자 계획](../proposals/auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md) 수립. 신규 작업은 미커밋·미배포다.

- [x] `[IntegratedWorkspaceBaseline1003] 기존 작업본 통합 commit·release 배포 및 기준선 청결 확인` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [통합 리뷰](../audits/integrated-workspace-baseline-review-2026-10-03.md).
  - Acceptance: 1945 tests PASS, compile/diff/parser PASS; immutable release HEAD/source/mount 검증, 공통 selector와 비활성 분석 service pin, cron/release-set PASS, 정책 hash 보존, trading PID 재기동 없음, git status 청결. 정확 commit/배포 결과는 `data/runtime/startup_readiness/2026-10-03/integrated_workspace_baseline/transition.json`에 보존한다.
  - 완료: 통합 commit `24a4658d`, 08:30 KST 공통 route·비활성 분석 service 2개 pin 배포 PASS, 541개 정책/override/bootstrap hash 보존, 배포 후 workspace clean. 실제 service 재기동 0. 미래 PREOPEN/PID는 이 항목의 완료 증거가 아니다. 신규 원천 보완분은 별도 diff·격리 재생성으로 진행하고 배포를 대기한다.


- [x] `[MainMachineAuxiliarySourceRepair1003] 기계·보조 정책 원천 결함 보완 및 격리 계산 검증` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: SourceQuality`)
  - Source: [상세 보완 계획](../proposals/main-machine-auxiliary-source-remediation-plan-2026-10-03.md).
  - Acceptance: R1/R2 regression·review/compile/diff/parser PASS; 동결 cache 비교/후보 hurdle 계산과 시간·RSS; auxiliary exact stop/full-cost 결손의 retained-source 판정; 정책 변경·carry와 원천 irrecoverable gap을 구분한 audit. 신규 코드/정책 배포는 별도 지시까지 대기한다.
  - Handoff: 10/6 `DirectFamilySourceRepairMainMechanisticEntry`와 `DirectFamilySourceRepairCompactAuxiliary`의 자연 owner acceptance를 중복 등록하거나 완료 처리하지 않는다.

  - 완료 증거: [보완·격리 계산 리뷰](../audits/main-machine-auxiliary-source-remediation-review-2026-10-03.md). placeholder/native lineage·완료 재개·후보 hurdle·조건부 source 진단을 보완했다. Main 후보0 유지, aux lossless metadata7행 복구/독립 진단17→20, full cost0/실행 경제성 미입증. 코드 및 격리 계산 범위 완료이며 자연 economic owner는 10/6 OPEN을 유지한다.
  - 배포 잔여: 기존 code24의 next startup 준비 검증은 checklist source generation 불일치로 fail. 기존 `DirectFamilyPreopenPolicyHandoff`의 summary/strict/controller 재봉인 소유자에 인계하며, 이번 신규 source 코드 배포와 구분한다.
  - 추가 리뷰: warm source cache의 metadata upgrade·checkpoint 보존을 수리하고 exact trace/충돌/세대/scan budget 회귀 및 retained source 비교를 진행했다. historical cumulative 재봉인은 수행하지 않는다.
  - 추가 연구 진단: [BLOCK 상승 경로·탐색 범위](../audits/main-machine-block-pattern-search-diagnosis-2026-10-03.md). KRX cache BLOCK849 중 목표-first564, 학습 비진입 목표38시도/29기회 존재; 당시 recovery budget의 새 유형 분기 할당0. 이 진단 자체는 구현/배포 승인이 아니다. 이후 사용자의 명시적 보유 원천 연구 요청은 아래 별도 항목에서 구현·격리 계산으로 수행했고 배포 대기를 유지한다.

- [x] `[RetainedSourceHypothesisResearch1003] 보유 원천 기계·보조 AI 가설 확대 및 정책 재생성 검증` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [상세 연구계획](../proposals/main-machine-auxiliary-retained-source-hypothesis-research-plan-2026-10-03.md).
  - Acceptance: source/code/parent 동결, M1~M6/A1~A5 가설 검증·불가 원인, 학습 선택/후단 날짜 진단·기회/종목 민감도, regression/review/compile/diff/parser, CF·actual·정책 승격 구분 audit. 새 원천수집/provider 호출/정책 배포/재기동 없이 수행한다.
  - 완료: [재생성 리뷰](../audits/main-machine-auxiliary-retained-source-hypothesis-research-review-2026-10-03.md). 기계11520 가설/209행동 vector/회수0, 방향 classifier47개에서 조건별 target-first 패턴 확인. 보조 soft438 changed0, feature-filter648개/481행동 vector에서 10분 손실 PASS 학습5·후단3 CAUTION 가설 확인; 날짜 재선정610 및 종목/horizon 민감도까지 검증했다. 새 prompt 비교는 exact retained variant 응답0으로 unsupported. actual EV/독립 holdout/등록 policy 승격0을 유지하며 code·연구 범위 완료, 신규 보완분 미배포다.

- [x] `[DeepRetainedSourceResearch1003] 기계·보조 AI 유형·시점·보상 구조 심화 연구` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [심화 연구계획](../proposals/main-machine-auxiliary-deep-retained-research-plan-2026-10-03.md).
  - Acceptance: D1~D9 보유 원천의 정책 한계·관측 패턴·전체/미도달 분모·유형별 탐색·지연 CF·여러 horizon·순차/종목 제외 재선정·탐색 민감도 검증, 원천/코드 hash·실제 가설/분모/부작용 audit, review/test/compile/diff/parser PASS. native 기회와 관측 anchor를 구분하고 새 수집·provider·live 정책·배포·재기동 없이 종료한다.
  - 경계: 이전 원천 보완·기초 연구 diff와 완료 결과를 보존한다. 기존 10/6 자연 owner acceptance는 이 연구로 닫지 않는다.
  - 완료: [심화 연구 리뷰](../audits/main-machine-auxiliary-deep-retained-research-review-2026-10-03.md). 전체 cache7069행/고정10분 가격·비용6795행으로 확대하고 기존 evaluable2976행의 조건부 승률 해석을 보완했다. 유형6셀20940조건에서 양의 학습 후보4셀을 찾았으나10/2 모두 음수였고, 날짜 재선정20431조건에서도 후단 음수를 확인했다. 보조2010조건·정확 pre-AI 연결14·지연 CF까지 검증,40 tests PASS. 정책 승격0, 신규 코드는 미커밋·미배포다.

- [x] `[PathSequenceValidation1003] 기계·보조 AI 결과 분류·관측 순서·장기 경로 검증` (`Due: 2026-10-03`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [상세 검증 계획](../proposals/main-machine-auxiliary-path-sequence-validation-plan-2026-10-03.md).
  - Acceptance: P1~P5 분모/분류 교차표·과거 순서 feature·장기 horizon·시간순 고정 가설·aux 성공 제외와 CF 비교, source/code/policy hash, review/test/compile/diff/parser 증거. 새 수집·provider·정책 발행·배포·재기동 없이 종료한다.
  - 경계: 이전 작업본과 기존 10/6 자연 수용·PREOPEN owner를 보존한다. 연구 CF를 실제 실현 수익이나 운영 정책 승격으로 표현하지 않는다.
  - 완료: [검증 결과](../audits/main-machine-auxiliary-path-sequence-validation-review-2026-10-03.md). 전체7069행의 도달/미도달/결손 분리, 반복 snapshot1684행 및 기존 완료봉6810행의 순서 feature, 날짜별56개 순서/21개 static 조건과 개별 horizon을 검증했다. 10분 미도달 중60분 비교1259건에서 고점 목표528·종료 순 CF 양수287을 확인했으나 양의 학습 후보들의 후단 성능은 음수였다. 보조4개 위험 가설의 성공 제외·변경0을 검증하고 개선 후보0. 66 tests PASS, 정책 승격·배포·재기동0.
