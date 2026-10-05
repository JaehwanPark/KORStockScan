# 2026-10-04 Stage2 To-Do Checklist

## 오늘 목적

- 삼성전자 보관 체결에서 최초 회복 사건을 재구성하고 동일 사건의 진입 시점 효과를 검증한다.
- 진입 효과의 사전 조건을 만족하면 고정 신호의 종료 조건을 추가 연구한다.
- 기존 호가에서 bid/mid 실제 회복과 흡수 지속 가설을 검증한다.
- 기존 원천의 서로 다른 가설을 운영 패턴 확보 또는 의미 있는 가설 소진까지 순차 검증한다.
- 종목 방향·수급·당시 발행된 이전 일일 breadth를 분리해 조건부 가설을 검증한다.
- 삼성전자 장전 확인 조건과 원archive 결함을 분해하고 같은 가격·비용·종료로 검증한다.
- setup family/state producer 결함을 수리하고 별도 역사 복구 receipt를 격리 소비한다.
- 원천 수리의 release 기준 적용본을 검증하고 장전 두 관측 가설의 독립 날짜 계약을 고정한다.
- source 수리본을 반복리뷰·보완하고10/6 Main/Widget/Episode 가동준비를운영본으로재점검한다.
- 전체 작업본을 통합 커밋·배포하고 다음 세션 준비를 새 release에 결속하며, 불필요한 작업본·릴리스·임시 사본을 검증 후 정리한다.

## 필수 규칙

- Plan Rebase §1–§8, 보유9/29·9/30·10/2 원천·날짜·hash·비용·원래 native identity와 hard safety/owner 계약을 지킨다.
- 최신 사용자 지시는 전체 작업본 통합 배포·정상기동 가능여부 재점검·디스크 정리를 승인한다. 연구의 오프라인 경계와 기존 hard safety/custody/격리는 유지한다. 새 alpha 정책 발행·실제 주문·provider/API 호출·수집 확대 및 매매 프로세스 강제 기동·재기동을 추가하지 않는다.
- 학습에서 조건을 고정하고 후단에서 재선정하지 않는다. 성공100%/80% 보존 veto를 두지 않는다. 미도달·결손·경로 CF·실현 손익을 구분한다.
- 기존10/6 PREOPEN 및 자연 수용은 [10/6 checklist](2026-10-06-stage2-todo-checklist.md)의 소유 항목을 유지한다.

## 실행 항목

- [x] `[MachineObservationGenerator1004] 관측 평가 단위·기계 후보 생성기 연결 및 격리 재생성` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 다음액션 실행 지시, [계약·실행계획](../proposals/machine-observation-generator-contract-plan-2026-10-04.md).
  - Acceptance: native/probe 구분·반복 군집 평가·고정 삼성/비삼성 후보의 실제 생성기 연결, 원천/parent/kernel/경로 결속, 학습 선정·10/2 비교·9/29 민감도 분해, 반복 리뷰/수정·표적회귀/compile/diff/link/owner/print-only parser.
  - Boundary: 기존 원천 기계 전용 격리 생성. 성공100%/80% 보존 veto 없음. 관측 후보 선택·운영 승격·실현 성과 분리; 정책 발행/배포/기동·API/provider/주문/수집 확대 없음.
  - 완료: [생성 결과 리뷰](../audits/machine-observation-generator-contract-review-2026-10-04.md). 7,069건 parent 재현·32원천 hash·실제 생성기 격리 경로, 비삼성 군집 승률 학습42.59→68.45%/10월2일55.56→71.43% 관측 후보 선택; 삼성 학습 선정·후단 기존 경계결과 미확정으로 비교 보류. 9월29일600초 민감도54종목 분해·음수 가격CF 보존,159표적회귀/compile/hash/link/owner/diff/print-only parser 검증. 운영 등록·발행/배포/PID·독립 성능은 완료 범위에 포함하지 않는다.

- [x] `[MachineCandidateEvaluatorSourceExit1004] 기계 후보 실제 평가·삼성 원천 효과·고정 진입 청산 검증` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 다음액션1→2→3 실행 지시, [실행계획](../proposals/machine-candidate-evaluator-source-exit-verification-plan-2026-10-04.md).
  - Acceptance: 비삼성 실제 기계 제안/원 위험·native 결손 대사, 삼성 완전 입력 census와 가능한 source×rule 비교, 고정 진입 청산/비용 분해, 리뷰·수정·표적회귀/compile/hash/link/owner/diff/print-only parser.
  - Boundary: 기존 원천·기계 전용 격리 연구. 성공100%/80% 보존 veto 없음. 원천 결손·CF·실현 수익 분리; 정책 발행/배포/기동·API/provider/주문/수집 확대 없음.
  - 완료: [결과 리뷰](../audits/machine-candidate-evaluator-source-exit-verification-review-2026-10-04.md). 비삼성6,550 parent 일치·신규 ENTER 제안263관측·10/2 목표22/손절10/승률68.75%; pipeline308,408행 exact ID 대사·후단 native0은 probe 생산 경로로 확인. 삼성519 capture/228 pipeline 연결에서도 완전 feature 생성 입력0으로 source 수정의 과거 효과는 미입증. 고정 진입12청산 arm·공통 분모/중첩/비용 분해,223표적회귀·compile/hash/link/owner/diff/print-only parser 검증. 실제 운영 적용·독립 성능·실현경제성은 완료로 합산하지 않는다.

- [x] `[SamsungFlatBuyFlowImplementation1004] 삼성전자 보합 수급 원천·report-only 평가 함수 구현 및 재생` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 다음액션 실행 지시, [구현계획 §7](../proposals/samsung-flat-buy-flow-source-and-evaluator-implementation-plan-2026-10-04.md), [실행 리뷰](../audits/samsung-source-recipe-and-non-samsung-horizon-review-2026-10-04.md).
  - Acceptance: exact-route/epoch/cutoff/window receipt·locked 관측/제출 분리·원 위험 fact 보존·미등록 보합 recipe·기존 ENTER 유지/교체 비교·519 parent 재현·첫 봉/native 민감도·반복 리뷰/수정·202회귀/compile/location/hash/link/owner/diff/print-only parser.
  - Boundary: 코드 및 격리 재생. 정책 등록/발행·배포·기동·주문/API/provider/수집 확대 없음. 과거 최신 snapshot 전체 feature 재구축과 자연 운영 소비는 미입증이며 기존10/6 owner를 변경하지 않는다. 성공100%/80% 보존 veto 없음.
  - 완료: source 유효430·조건76·신규 ENTER 제안54관측, 학습 교체형 연구 선택·10/2 비중복 목표4/손절2/시간종료2. 실제 전체 capture와 독립 archive 증명을 결속하고 완전한 최신 feature 재구축·독립 날짜·실현성과 한계는 리뷰에 남겼다.

- [x] `[NonSamsungMachineHorizonUnion1004] 삼성전자외 전체 기계 행동 상승 통합 및10분 이후 가격 연구` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 삼성전자외 ENTER/BLOCK/RECHECK 실제 상승 통합·미도달 이후 가격 보조 평가 지시, [실행 리뷰](../audits/samsung-source-recipe-and-non-samsung-horizon-review-2026-10-04.md).
  - Acceptance: 삼성전자 사전 제외8,109행/764종목·원천/가격/비용 hash·10/20/30/60분/세션종료·첫 봉/가격간격/손절후반등 분리·원천/유형 비교·66가설 학습 선정·종목제외/반복축소/native 민감도·표적회귀/문서 검증.
  - Boundary: 기계 전용 관측 연구. 실제 evaluator 신규 ENTER 변환·보조판정·운영정책/배포/기동·API/provider/주문 변경 없음. 성공100%/80% 보존 veto 없음; 가격CF와 실현손익을 구분한다.
  - 완료: 엄격 목표 선도달2,752(ENTER122/RECHECK1,904/BLOCK726),10분 이후 목표1,130. 학습 후보 `pullback_p60_v0`의10/2 경계확정 승률60.61→68.75%; 전체393종목 제외 민감도 개선 유지(선택 종목39개, 후속 리뷰에서 횟수 표기 정정).600초 축소 시9/29 개선 소멸·9/30/10/2 native-only 후보0·평균 가격CF 음수를 함께 보존했다.

- [x] `[SamsungFlatBuyFlowContract1004] 삼성전자 보합 수급 원천·기계 evaluator 대사와 구현계획` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 다음액션 실행 지시, [선행 리뷰 §7](../audits/samsung-machine-horizon-pattern-research-review-2026-10-04.md), [후속 구현계획](../proposals/samsung-flat-buy-flow-source-and-evaluator-implementation-plan-2026-10-04.md).
  - Acceptance: 고정 후보·519 parent 행동 재현·원24선택/10월2일8관측의 cutoff/receipt·보관0B/0D·전체 risk fact/기존 adapter 대사, 시점 민감도와 새 규칙/원천/shared evaluator 구현계획, 반복 리뷰·수정·14회귀/compile·47입력 seal·diff/link/owner/print-only parser.
  - Boundary: 기계 전용 격리 연구와 계획. 기존 raw/정책/배포/기동·API/provider/주문/수집 확대·10/6 준비 계약 변경 없음. 성공100%/80% 보존 veto 없음; partial feature 민감도와 실제 정책/성과를 구분한다.
  - 완료: [대사 결과](../audits/samsung-flat-buy-flow-source-and-evaluator-review-2026-10-04.md).10월2일 원8관측 체결값은 receipt 시점8/8·최신 cutoff4/8 일치. locked BBO4건의 이전 snapshot 소비를 확인했고 최신 체결3필드 민감도는 원시각 고정 목표3/손절2/종료2·전체 재점유 목표4/손절2/종료2.519행 원 행동 일치, 조건73행 기존 adapter 신규 ENTER0.9월29일2건 대사 미해결·독립 날짜/실행/경제성 한계를 보존하고 운영 P0–P3 구현은 후속 계획으로 남겼다.

- [x] `[SamsungMachineHorizonPattern1004] 삼성전자 기계 전체 행동·관측기간별 원천 패턴 연구` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 기계 전용 통합 상승 비교·10분 이후 보조 평가·다음액션 실행 지시, [계획](../proposals/samsung-machine-horizon-pattern-research-plan-2026-10-04.md).
  - Acceptance: 전684관측 결과 유형 대사·원천/날짜/세션/native/반복 민감도·66고정가설 학습 선정→10/2 비교·동시 점유 배제·guard 보존·비용/첫 봉 리뷰·표적 회귀/compile/hash/link/diff/print-only parser.
  - Boundary: 기존 원천 격리 연구. 보조 AI·정책 발행/배포/기동/API/provider/주문/수집 확대 및10/6 준비 계약 변경 없음. 성공100%/80% 보존 veto 없음; 사후 유형을 진입 입력으로 사용하지 않는다.
  - 완료: [결과](../audits/samsung-machine-horizon-pattern-research-review-2026-10-04.md). 빠른 목표92·늦은 목표70·손절 후 반등85, `absorption_p60_v10` 학습 후보의10/2 비중복 재생 목표4/손절2/시간종료2. 비용·관측 시점·native/첫 봉 민감도와 기준선10/2 경계확정 승률 미산정을 공개했다.14표적 회귀·684행 원10분 대사·source/hash·문서 검증. 연구 후보를 보존하며 운영 선정/실현성과/독립 검증을 주장하지 않는다.

- [x] `[EntryObservationTypeExitResearch1004] 삼성전자 확정 원천 패턴 비교와 유형별 진입 청산 연구 실행` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 삼성전자 RECHECK/BLOCK 확정 관측 비교 및 계획 실행 지시, [실행계획](../proposals/entry-observation-type-utilization-and-exit-separation-research-plan-2026-10-04.md).
  - Acceptance: 삼성전자 미확정 제외 패턴·행동별/날짜별 대조, P0 원천/가설 봉인 → P1 A1 분해 → P2 동일 진입 청산 비교 → P3 동일 청산 진입 비교 → P4 삼성전자 차단 해소 → P5 parent 행동 재생, 반복 리뷰/수정·표적 회귀·원천 hash/미래 입력/비용/route/native·문서 parser 검증과 결론 기록.
  - Boundary: 기존 원천의 오프라인 연구. 정책 발행·선택·배포·기동·API/provider·주문·수집 확대·10/6 준비 계약 변경 없음. 성공100%/80% 보존 veto 없음; CF/실현손익 및 미도달/결손 분리.
  - 완료: [실행 리뷰](../audits/entry-observation-type-exit-separation-research-review-2026-10-04.md). 원 삼성전자724관측 중 source 부적격81·미확정507을 분리, 목표84/손절52의 판정별 원천 비교.8,793행 parent 재현 일치, A1 고정 진입 X1 청산은10/2 양수 종료14.57→20.18%이나 평균CF 악화; 실제 parent native 진입 후보0. BBO receipt2,591행 추출 복원·엄격/보충 진단 분리·15회귀·19원본/가설/기존연구 seal·compile/diff/link/print-only parser 검증. 고정 가설군 완료, runtime/정책/배포 변경0; 실제 exit/체결·독립 날짜 성능은 미검증.

- [x] `[IntegratedDeploymentDiskCleanup1004] 전체 작업본 통합 배포·다음세션 준비·검증된 사본 정리` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 전체 작업본 통합 배포·정상기동 가능여부 재점검·디스크 정리 지시, [통합 실행 기록](../audits/integrated-deployment-and-disk-cleanup-review-2026-10-04.md), [release routing](../runtime-release-routing.md).
  - Acceptance: 모든 변경 파일 census·통합 리뷰/보완·표적 회귀·compile/location/diff/link/parser, 통합 commit·clean immutable release·selector 원자 전환·예약 owner 경로·새 release exact10/6 isolated 준비/full 검증·Main/Widget/Episode 정책/타이머/PID·격리 대사, 현재/직전/서비스/원천/증거/롤백 보호·삭제 manifest/archive ref·사후 route/hash/free-space 검증.
  - Boundary: 코드 배포·격리 준비·read-only 가동 점검과 검증된 불필요 사본 삭제. 매매 프로세스 기동·재기동/주문·새 정책 선택·API/provider/수집 확대·격리해제 없음. 독립 Widget/Episode의 변경 없는 live 소비 경로와 pin/custody는 보존하며 준비·실제 PID·경제성을 구분한다.
  - 완료: 전체64파일 통합commit9c0c0632·1,006tests/물리release209tests PASS·compile/location/bash/diff/parser, clean 불변release 선택과 실제 장후2unit pin 보완·exact10/6 isolated 준비/full 계약PASS. Main/Widget/Episode loader·124owner·122Episode unit/366pins·125timer대사, 현재WidgetPID3137231/e6 startup PASS·61baseline/58격리제외·3격리유지. 98정책/handoff seal불변·원가설/kernel bytes불변이며 장전계약은아래승인된release 경로세대로이전했다. 21worktree와closed pytest2개삭제·archive refs/4고유source-log 사본복구검증, 순가용+1.81GB·등록56→새release1추가→36. 실제당일PID/성과는미도래이며 매매기동/재기동/API/provider/정책선택/주문0. 상세는통합실행기록과삭제manifest다.

- [x] `[SourceRepairNextSessionReview1004] 원천 수리 반복리뷰·다음세션 Main/Widget/Episode 준비 재점검` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자반복리뷰/다음영업일정상가동재점검지시, [재리뷰·준비검증](../audits/source-repair-repeat-review-and-next-session-readiness-2026-10-04.md), [선행준비계획](../proposals/samsung-premarket-forward-validation-and-source-release-preparation-plan-2026-10-04.md).
  - Acceptance: 실제physical SHA/동시archive변경·validator kernel·파일종류 결함재현→수정→재리뷰→선택base patch/회귀·실원천재생·hash보존, exact10/6 current_full_contract/loader·cron/unit/timer/pin/PID·quarantine 대조·compile/diff/link/owner/parser.
  - Boundary: 코드수리·격리검증과read-only운영점검. 실제commit/배포/재기동/정책발행·API/provider/주문/수집확대·10/6체크리스트세대변경없음. 격리3개/OFF권한보존.
  - 완료: C1 457/C2 36, 고유493tests PASS. actual재생5→6·원watch2/원5행SHA 및RECHECK/경제성동일, 재생/재검토계약cold/warm bytes일치. 운영선택a17bd6d2의준비current_full_contract·Main/Widget/Episode loader PASS·등록cron8개·Episode122unit/366pins·125timerenabled/active. 실제Widget3137231 cwd/startup대사PASS(10/3증거). Episode61baseline valid/58격리제외·3격리유지, 당일applied/PREOPEN/PID는미도래. 수리본미배포·미래가동/성과미검증; Main은기존10/6owner, Widget/Episode는아래owner.

- 이관 기록: `[WidgetEpisodeNextSessionStartup1006] Widget/Episode 다음거래일 정책·preflight·PID 수용` (`Due: 2026-10-06`, `Slot: INTRADAY`, `TimeWindow: 07:32~20:00`, `Track: RuntimeStability`)
  - Source: [재점검리뷰§4–§5](../audits/source-repair-repeat-review-and-next-session-readiness-2026-10-04.md), 사용자다음영업일정상가동재점검지시.
  - Acceptance: Widget07:32정책반영/07:58기동경로와현재PID의10/6reload/행동policy hash·custody/source receipt를대조한다. 기존10/3 startup은당일reload증거로사용하지 않는다. Episode58격리제외profile의당일applied/authority·research/Main/token preflight·실제unit/PID·자연원천을profile별로대조하고3격리를별도표시한다. 기존Main `DirectFamilyPreopenPolicyHandoff`·Episode sequence owner와증거를연결하되코드/준비/기동/주문/경제성을구분한다.
  - Boundary: read-only검증과결과기록. 실제가동/기동부작용이있는preflight/정책쓰기/재기동/API/token조회/주문/격리해제는자동실행하지 않는다. source없음은not_observed,미도래는not_yet_due이며source gap의0치환없음.
  - 현재:10/4 준비PASS이며당일적용/PID/자연소비는미도래. 기존독립e6d4d3b9 release/service pin을보존한다.
  - 현재 owner: [10/5 체크리스트](2026-10-05-stage2-todo-checklist.md)의 동일 ID로 이관. 아래 수용/이력은 보존하며 이 문서는 현재 OPEN 또는 실행 완료 소유자가 아니다.

- [x] `[SamsungPremarketForwardPreparation1004] 원천 수리 release 준비·장전 독립 검증 계약 고정` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [준비계획](../proposals/samsung-premarket-forward-validation-and-source-release-preparation-plan-2026-10-04.md), 사용자 다음액션 실행 지시.
  - Acceptance: 선택release base/C1 정확한patch·6개파일 byte 일치·producer→기본/독립 public loader9회귀·rollback 준비, 장전2가설 exact parent/kernel/조건/가격비용/native/미확정/중단 계약, 리뷰/보완·표적회귀·격리출력 일치·기존source/policy/selector보존·compile/diff/link/owner/print-only parser.
  - Boundary: 커밋·배포 준비와오프라인 계약/소비 test/inventory. 실제commit/배포/재기동·정책발행/API/provider/주문/수집확대 및기존10/6owner 변경없음.
  - 완료: [실행리뷰](../audits/samsung-premarket-forward-validation-and-source-release-preparation-review-2026-10-04.md). 선택a17bd6d2 기준 최종격리C1 455/C2 33, 고유488tests PASS. default 경제성결손 제외·독립미확정 보존·warmcache 검증. 고정두가설 contract/inventory 재실행 bytes 일치,10/6 원천4경로부재.185기존seal/98policy·selector·10/3/10/6checklist보존. 실제PID consumption미입증; 미래성능은 아래별도owner 대기.

- 이관 기록: `[SamsungPremarketForwardValidation1006] 고정 삼성전자 장전 두 관측 가설의 독립 날짜 검증` (`Due: 2026-10-06`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [계획§4–§6](../proposals/samsung-premarket-forward-validation-and-source-release-preparation-plan-2026-10-04.md), [준비리뷰§4](../audits/samsung-premarket-forward-validation-and-source-release-preparation-review-2026-10-04.md), 사용자 이후검증 준비 범위.
  - Acceptance:10/6이후 자연원천의exact parent/canonical/native/route/epoch/cost/label/원guard와kernel 검증, frozen두가설의Main 원binary/별도가격CF 소비 evaluator 구현·리뷰/회귀, 동일population parent 대비승률·비용·미확정 비교. 최초3적격날짜 한도·각binary3/독립2날짜 연구gate·parentempty 비교미식별·성공보존veto없음·조건재선정없음.
  - Boundary: 새tmp generation의오프라인 연구. source없음은waiting, canonical/route 결손은excluded/source_gap, parent/kernel변경은replan. archive CF는Main native/실현PnL을대체하지 않는다. 연구gate와정식publisher/운영경제성/runtime bridge를분리하며 실제매매/수집/배포/재기동권한없음.
  - 준비이력: `tmp/samsung-premarket-forward-preparation-20261004/final-v2-cold/source-inventory.json`의4경로부재·`waiting_new_source_date`였다. 기존정규장 `SamsungFrozenCandidateValidation1006`과별도소유다.
  - 현재: 통합배포후 `tmp/integrated-deployment-disk-cleanup-20261004/forward-release-bound/frozen-contract.json`의7a8ba145 계약을선택release 코드로소비한다. 원parent/두가설/조건/비용/기간/미래3날짜한도와kernel bytes는40f567d0 계약과동일하며차이는승인된불변release의물리코드경로뿐이다. 40f567d0/458ce71a는역사receipt로보존한다. 원천4경로는여전히waiting이고새날짜성과/정식candidate 미검증이다.
  - 현재 owner: [10/5 체크리스트](2026-10-05-stage2-todo-checklist.md)의 동일 ID로 이관. 아래 수용/이력은 보존하며 이 문서는 현재 OPEN 또는 실행 완료 소유자가 아니다.

- [x] `[EntrySetupSourceRepair1004] Entry setup family/state producer 수리·별도 역사 복구 소비 검증` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [수리계획](../proposals/entry-setup-family-state-source-repair-plan-2026-10-04.md), 사용자 다음액션 실행 지시 및 선행 확인연구 리뷰§7.
  - Acceptance: unsupported/micro/supported family grammar·hard BLOCK/local RECHECK 보존, 원canonical/raw/parent/kernel/source-bound 별도 receipt 및 uncached opt-in 마지막 소비 검증, 기본5/복구6·원watch2·원cost null/source-bound 추정·결과미확정 분리, 원전체pricecache 검증 후exactroute subset·리뷰/보완/재리뷰·표적 pytest/compile/diff·cold/warm·원정책/미변경seal·문서parser.
  - Boundary: 오프라인 코드 보완·격리 재생. 원archive/projection/선행연구/정책 덮어쓰기·ENTER 승격·합성native·API/provider/수집/주문/배포/재기동 없음. 승인코드 old/new ledger와 나머지seal 보존·10/6owner 유지.
  - 완료: [실행 리뷰](../audits/entry-setup-family-state-source-repair-review-2026-10-04.md). unsupported/micro 정합성 수리·08:33 exact raw/원parent 재생4필드 변화·최종RECHECK불변, 별도receipt 명시적소비로5→6·기존5행/원watch2불변. 원전체price분모2,065/2,309·NX가격각50행 검증; 복구관측비용추정0.32075%·10분MFE+0.181488%로gross목표0.42075%미도달·새적격binary0.446tests·compile/diff·최종cold/warm·22source·178미변경seal/98정책·변경2kernel old/new·문서parser.정책/배포/기동변경0,기존10/6owner유지.

- [x] `[SamsungPremarketConfirmation1004] 삼성전자 장전 확인 조건 분해·동일 가격 재생 연구` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [상세 연구계획](../proposals/samsung-premarket-confirmation-component-research-plan-2026-10-04.md), 사용자 상세계획 수립·실행 지시.
  - Acceptance: 원장전3일 전체canonical/parent 재현·결손/유효0 분리,9확인 가설 단일요소 대조·동일 가격/비용/종료·원native/연속CF 분모,학습 고정/10/2진단·리뷰/보완/회귀·실prefix/cold-warm/source·정책hash 보존·문서parser.
  - Boundary: 보유 원천 오프라인 연구. hard safety 우회·성공보존veto·native합성 및API/provider/수집/주문/실정책 발행·배포/재기동 없음.10/6 기존owner와 선행봉인 자료 보존.
  - 완료: [확인 조건 연구 리뷰](../audits/samsung-premarket-confirmation-component-research-review-2026-10-04.md).canonical6/projection5·원watch2와41,243체결/36,392호가·유효feature5,527을 대사했다.08:13의distribution/가격0·매수우세에서고정CF+0.134299% 목표1건 확인,같은가격조건의9/30손실·08:36원stop손실도 대조.9확인 가설 학습binary최대1로미선정·10/2사후진단/10초gap민감도 개선미재현.원archive08:33의family/state검증결함·연구consumer의unused scanner null오제외를 분리하고후자를수정.51tests·compile/diff·실4prefix·cold/warm4파일 일치·180source/kernel/98정책hash 및10/3·10/6checklist보존·문서parser.공식candidate=null·운영변경0;원producer결함 보완과 장전독립검증은 리뷰§7의 잔여이며 기존10/6owner확대없음.

- [x] `[SamsungFixedWatchEvaluation1004] 고정감시 평가·Main/Widget 대조·고정 후보 재생 준비` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [실행계획](../proposals/samsung-fixed-watch-evaluation-and-owner-comparison-plan-2026-10-04.md), 사용자 진행·검증 지시.
  - Acceptance: 원watch/day와 가격 episode 분리, 실제 Widget custody/정책/체결/설정비용 및 동일 가격 종료 비교, 기존 두 후보 고정·fixed-watch 이식과 이후 날짜 replay adapter, 리뷰/수정/회귀·cold/warm·source/정책hash 보존·문서parser.
  - Boundary: 보유 원천 오프라인 구현·검증. 성공100%/80% 보존 veto 및 native 합성 없음. 원수집/API/provider·주문·실정책 발행·배포/재기동·10/6 기존owner 변경 없음. 이후 날짜 실제 검증 대기와 코드 준비 완료를 구분한다.
  - 완료: [평가·owner 대조 리뷰](../audits/samsung-fixed-watch-evaluation-and-owner-comparison-review-2026-10-04.md). 전용206관측·원watch2개와 전체519를 분리; 전체학습60%/66.67% 후보는 전용에서0%/선택0으로 개선 미재현. 원watch 연결 회복/흡수9/30 각각확정1/2 양수·검열1,10/2 최초검열로 뒤 admission 보류. 실제Widget10주275,500→277,000·동일custody 확인; 설정비용 후8,629원·+0.313212% 추정. Main장전RECHECK2개 canonical 연결, 동일종료가격에서08:13 진입가격효과+0.36544%p·08:36가격효과0, 정규장 종료수식 확정paired0. frozen후보/자동원천later adapter·285개 고유tests/compile/diff·6prefix·cold/warm3파일·176source/98정책 보존. 운영후보미확보·배포/기동0; 이후 성능은 아래owner에서 대기.

- 이관 기록: `[SamsungFrozenCandidateValidation1006] 고정 삼성전자 후보의 이후 날짜 검증` (`Due: 2026-10-06`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [계획§6](../proposals/samsung-fixed-watch-evaluation-and-owner-comparison-plan-2026-10-04.md), [실행 리뷰§6/§8](../audits/samsung-fixed-watch-evaluation-and-owner-comparison-review-2026-10-04.md), 사용자 고정 후보 후속검증 준비 범위.
  - Acceptance: 자동 생성된10/4 이후 원천만 intake, 원parent/hash/trace/guard/native/cost/label·독립epoch 확인, 고정 두 후보의 삼성전자 전체origin/상시감시 성과·미확정 수 대조. 후보 재선정 및 source 수집 없이 연구 receipt와 처분 기록.
  - Boundary: 새tmp generation의 오프라인 검증. source없음은waiting, 식별 불량은excluded/valid-empty 구분, parent·전역 계약 변경은replan. 실제publisher/주문/API/provider·배포·기동 및10/6 기존owner 변경 없음.
  - 현재: `tmp/samsung-fixed-watch-evaluation-20261004/next-date-readiness/preparation-status.json`에서 필요한4경로 부재·`waiting_new_source_date`; 새 날짜 성능은 미검증.
  - 현재 owner: [10/5 체크리스트](2026-10-05-stage2-todo-checklist.md)의 동일 ID로 이관. 아래 수용/이력은 보존하며 이 문서는 현재 OPEN 또는 실행 완료 소유자가 아니다.

- [x] `[SamsungEnvironmentConditionedResearch1004] 삼성전자 방향·수급 조건부 가설 연구` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [환경·수급 연구계획](../proposals/samsung-environment-conditioned-pattern-research-plan-2026-10-04.md), [프로그램 구간 변화 보완](../proposals/samsung-program-sequence-research-plan-2026-10-04.md), 사용자 환경별 가설 확대 및 연구계획 실행 지시.
  - Acceptance: 당시 외부 시장/업종·프로그램/투자자 가용성 census, source timestamp/expiry/route/epoch 대사, 고정 종목 방향·수급 조건의 학습 선정/후단 재생 및 Main 원 binary/native 비교, source·정책 hash 보존, 리뷰/수정/표적 회귀·cold/warm·compile/diff·문서 parser.
  - Boundary: 보유3일의 오프라인 연구. 종목 방향을 외부 시장 방향으로 치환하지 않는다. 성공100%/80% 보존 veto, API/provider·수집 확대·주문·실정책 발행·배포·재기동 및10/6 owner 변경 없음.
  - 완료: [환경·수급 연구 리뷰](../audits/samsung-environment-conditioned-pattern-research-review-2026-10-04.md). 원capture519/프로그램519·투자자221 유효 및expiry/epoch join455/212 확인.51조건·3,672가격조합에서학습3/3 개선1건은후단0/1·CF−0.59232%로실패. 환경단독Main학습66.67%(2/3) 후보는후단선택0. 과거프로그램60/180/300/900초 및state_failure1,272조합도실행했고승률개선10계산조합의평균CF양수0. 구간수급Main학습60%(3/5)·support-adjusted+5.122%p지만후단원binary미도달로공식candidate=null. 외부intraday지수/업종미실행·이전발행pool breadth는두유효일모두하락으로환경간효과미식별.232tests·실9prefix/77,412분류·24과거sequenceprefix 비교·compile/diff·격리재생/hash보존·문서parser. 매매/정책/배포/기동변경0 및10/6owner유지.

- [x] `[SamsungOpportunityContract1004] 삼성전자 기회 계약 복구·고정 패턴 재검증` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [실행계획](../proposals/samsung-opportunity-contract-reconciliation-plan-2026-10-04.md), 사용자 계약 보완 후속계획 실행 지시.
  - Acceptance: 원trace/attempt/snapshot/hash/scope exact join·결손298건 처분, 원owner 기반 종료/재진입·native cluster 계약, 고정 회복/흡수와 기존Main 재검증·publisher 적격성, 리뷰/보완/회귀·격리 재실행·기존source/정책hash 보존·문서parser.
  - Boundary: 기존 원천과read-only DB snapshot의 오프라인 source capsule/consumer·연구. 실제 publisher/주문/API/provider/수집 확대/배포/재기동 없음. 성공100%/80% 보존veto 없음.10/6 기존owner 보존.
  - 완료: [기회 계약 복구·고정 후보 재검증 리뷰](../audits/samsung-opportunity-contract-reconciliation-review-2026-10-04.md).519 capture·209,908 pipeline/496 trace 대사, 결손298건 중 probe exact 연결12건·새 native복구0. 실제 삼성전자 Main closed episode 지원0 및 Widget custody 분리. 전체 native 상한 학습16/후단1·전용 fixed-watch1/1로 공통 publisher30/10 불충족의 구조적 제약 확인. 고정 회복/흡수10/2 각각2양수·1검열 재현, 동일2상승구간이며 Main binary 비교는 개선되지 않음.205 tests·compile/diff·cold/warm3파일 일치·155source/98정책hash 및 선행131/142source 보존·local link/owner·print-only parser. 공식candidate=null, 정책 발행/매매/배포/기동 변경0. 후속은 추가raw수집이 아닌 fixed-watch 평가·발행 계약 설계이며10/6 기존owner 유지.

- [x] `[SamsungPolicyEpisodeReplay1004] 삼성전자 현재 정책 직접 비교·연속 기회 재생 연구` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [새 실행계획](../proposals/samsung-policy-episode-replay-research-plan-2026-10-04.md), 사용자 유효 정책 확보 또는 가설 소진까지 실행 지시.
  - Acceptance: 현재 parent hash 재검증·captured setup 직접 재판정, 가격 왕복/미도달/결손 census, native/trace/비중첩 episode 분모, 고정6상태·8종 종료·재진입·학습/후단·관측 간격·기존9/28 원천 비교, 전체 가설의 disposition과 종료 근거, 코드리뷰/보완·표적 회귀·재실행/hash 보존·문서 parser.
  - Boundary: 보관3일 및 기존9/28 삼성전자 오프라인 연구·구현. 기존 성공100%/80% 보존 veto 없음. 실제 publisher·주문·수집 확대·배포·재기동 및10/6 owner 변경 없음.
  - 완료: [직접 비교·연속 기회 연구 리뷰](../audits/samsung-policy-episode-replay-research-review-2026-10-04.md). 현재/10/6 machine parent 동일 및519 captured 재판정 일치.6상태·8종료·3관측 모델34,560조합, 기존9/28 추가768조합·지연/비용72평가.10/2 회복/흡수는 각각 확정2건 양수·1건 검열, 같은 상승구간이며 기존Main 후단 비교 결과0. 원native 상한 학습16/후단1로 해당publisher30/10에 미달. 봉인 자료·native 계약에서 구별되는 가설 검증 완료로 종료하며 운영 유효 정책 미확보를 표시한다.158 tests·실source 인과성144비교·2재실행 일치·원source/신규kernel131 및prior-day142hash·기존정책/인계98hash 보존·compile/diff·문서parser. 후속은 리뷰§8의 원receipt 기반 기회 단위/소비 계약 보완이며 실제정책/매매/배포 변경0.

- [x] `[SamsungPatternCampaign1004] 삼성전자 기존 원천 가설 소진 연속 연구` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [연속 연구계획](../proposals/samsung-pattern-campaign-plan-2026-10-04.md), [개장 초기](../proposals/samsung-opening-regime-research-plan-2026-10-04.md), [관측 간격](../proposals/samsung-quote-continuity-sensitivity-research-plan-2026-10-04.md), [5단/전체 잔량](../proposals/samsung-depth-profile-research-plan-2026-10-04.md), 사용자 운영 패턴 확보 또는 가설 소진까지 계속 연구 지시.
  - Acceptance: 기존8가설군에서3단·5단/전체 잔량까지18가설군 및 고정 subgroup/창 확장, 종료 이전 원천 유효성·학습 고정·후단·native guard bridge·후보 안정성 검증. 패턴 확보 또는 기존 원천의 의미 있는 가설 소진 근거, 리뷰/보완/표적 회귀·재실행/hash 보존·문서 parser.
  - Boundary: 기존3일 삼성전자 원천의 오프라인 연구. 성공100%/80% 보존 veto 없음. 실제 정책 발행·수집 확대·주문·배포·재기동과10/6 기동 owner 변경 없음.
  - 완료: [연속 심화 연구 리뷰](../audits/samsung-pattern-campaign-research-review-2026-10-04.md).5개 exact scope의718,558체결/637,611호가·100,603frame,18가설군/11,952조건·관측 간격3모델의35,856계산 조합.5단을 제외하던 소비 결함·invalid prefix를 보완하고 다시 계산했다.500원 낮은 진입의 동일 종료 효과+0.1842%p는1건 확인했지만, 기본/3초/10초 모델의학습 적격291/306/309조건 중 학습·후단binary≥3 및 양쪽 평균CF양수는0. 보관3일의 의미 있는 가설군 소진으로 종료하며 운영 후보 미확보를 표시한다.144 tests·compile·4재실행 일치·실제6prefix 인과성·127source/kernel/plan 및98정책/인계hash 보존·문서 parser. 새 정책/배포/기동 변경0.

- [x] `[SamsungQuoteRecovery1004] 삼성전자 호가 회복·흡수 지속 후속 연구` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [후속 실행계획](../proposals/samsung-quote-recovery-and-absorption-research-plan-2026-10-04.md), 사용자 다음 연구 진행 지시.
  - Acceptance: 선행 shock identity와 원천/가격 기준 봉인, 고정4가설·동일 anchor 분모·과거 quote join·학습 전용 선택·기준 대비 승률·CF/미도달/결손 분석, strict quote 민감도, 리뷰/수정/재검증·재실행 일치·정책 보존·문서 parser. 성공100%/80% 보존 veto 없음.
  - Boundary: 원래3일 자료의 오프라인 연구. 현재 Main 정책 비교/정식 정책/실현 손익/배포/PID 적용을 주장하지 않으며10/6 기동 owner를 보존한다.
  - 완료: [후속 연구 리뷰](../audits/samsung-quote-recovery-and-absorption-research-review-2026-10-04.md). 기존334,124호가의bid==ask46,110행을 관측 가격에 포함한 별도 민감도에서bid 회복498·흡수 지속398개 확인.10/2 흡수 자체600초17개 중 목표1·미도달16, 공통 종료15개 가격 차이+0.0121%p·추가 목표0으로 진입 효과/종료 시각 효과를 분리했다. 학습 기준 대비 지원/승률이 부족해 모든 fold 미선정.123 tests·compile/diff·문서 parser·재실행/hash보존 검증. 정책/매매/배포 변경0.

- [x] `[SamsungEventTimingIsolation1004] 삼성전자 사건 직후 진입 시점 분리 및 조건부 종료 연구` (`Due: 2026-10-04`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [실행계획](../proposals/samsung-event-timing-isolation-and-exit-research-plan-2026-10-04.md), 사용자 1·2번 실행 및 결과에 따른3번 진행 지시.
  - Acceptance: 원천·kernel 봉인, 과거 정보로 매도/첫 회복 사건 생성, 동일 사건 즉시/분 경계/기존 분봉 확인 비교, 순서·epoch·결손·후단 검증, 사전3번 진입 조건의 PASS/미충족 판단과 해당 종료 연구, 리뷰→수정→재리뷰→표적 회귀·compile/diff·문서 parser. 결과 결손에 따라 최초 신호를 성공 신호로 교체하거나 합성 native 지원수를 늘리지 않는다.
  - Boundary: 독립 가격 경로 진단. 정책/실행 권한 및10/6 기동 owner를 바꾸지 않는다. 이미 탐색한3일 자료를 새 독립 holdout이라고 표시하지 않는다.
  - 완료: [연구 리뷰](../audits/samsung-event-timing-isolation-and-exit-research-review-2026-10-04.md).1,026개 사건·고정4개 가설의 날짜별 비교, 학습 선정 sell_decay 후단 paired21개 CF−0.1295%p·추가 목표0으로3번 조건 미충족/종료 조합 실행0. 호가 비교20개는 같은 bid/ask 내 체결가 이동과 일치했고, 같은15개를 ask 진입/bid 공통 종료로 맞추면 차이+0.0002%p로 시점 우위 미입증. 리뷰/보완·97 tests·compile/diff·문서 parser·재계산 일치·hash 보존; 실제 정책/매매/배포 변경0.
