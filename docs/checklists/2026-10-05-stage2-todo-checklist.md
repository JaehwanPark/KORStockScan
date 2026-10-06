# 2026-10-05 Stage2 To-Do Checklist

## 오늘 목적

- 완료된 기계 수용 계약·삼성 검증·정리 증거를 보존하고, 승인된 의미감시·Widget/Episode 개선계획을 구현·리뷰·보완·기존 원천 연구로 검증한다.10/6 실제 기동과 생성 중인 장후 세대의 최종 수용은 기존 owner에 인계한다.

## 필수 규칙

- Plan Rebase §1–§8과 사용자 최신 지시를 따른다. 기존 Main/삼성 기계 연구 입력은9/29·9/30·10/2로 고정한다. 승인된 Widget17종목 기간 대사는9/29~10/2의 기존 완료 원천을 사용하며, 실행 점검에서 확인된10/1 분봉도 포함한다.10/2를 새 독립 holdout으로 취급하지 않는다.
- 기계 후보 `pullback_p60_v0`를 고정한다. 성공100%/80% 보존 veto를 추가하지 않는다. 삼성전자와 보조 AI는 별도 정책/owner로 구분한다.
- 종전 구현·지정·배포·준비 검증은 아래 완료 증거로 보존한다. 최신 `계획을 실행하고 코드리뷰후 수정보완 반복` 지시는 해당 코드·기존 원천의 유한 연구·검증을 승인했다. 실제 Main 당일 기동/PID는 기존 owner가 확인한다. 관측/최초 신호/native·비용/stop·독립 날짜와 지정 근거를 구분하고 삼성 최신 absorption과 과거 veto의 owner를 혼동하지 않는다.
- 10/5 문서는 작업 시작 시 없었다. 완료된10/4 항목을 현재 OPEN으로 복제하지 않고 이번 지시의 소유 항목만 등록한다. 다음 영업일 준비의 기존10/6 소유 항목은 유지한다.

## 실행 항목

- [x] `[WidgetResearchAdvisoryPlanning1005] 위젯 종목 수익성 선별·기간 및 자문 누적평가 진단계획 수립` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 두 계획 수립 요청, [종목 신호연구 재설계](../proposals/widget-symbol-profitability-research-redesign-plan-2026-10-05.md), [자문 누적평가 진단](../proposals/widget-advisory-cumulative-evaluation-diagnostic-plan-2026-10-05.md).
  - Acceptance: 현재 selected 코드·보고서·실행 receipt 기반의 대상/원천/기간/수익성·집계/선정/소비 연결 진단, 실행 owner·유한 산출물/종료·권한·기존 연구와의 중복 경계를 설계한다. 문서 리뷰/보완/재리뷰·link/owner/diff/print-only parser.
  - Result: selectede16ac48b와 작업공간의 영향 코드 bytes 일치. source10/2 연구100/636·prospective대기97/격리2/robust미확보1·passed0, 자문80/8/24누적 및 전session carry를 대사했다. 기존 등록 범위의 최대17종목/운영수 확대 없는 subset 선별,20/40일 상한과9/29 forward 경계, 자문 실행→행수→역사집계/paired20일→dated consumer 진단계획을 작성했다. [읽기 증빙](../../tmp/widget-research-and-advisory-planning-20261005/inspection.json).
  - Boundary: 계획/기존 파일 읽기만. 계산·정책 발행·원천 수집/삭제·collector/스케줄·배포/기동/PID 수용 미실행. 새 선별/기간 계약은 제안이며 아래 OPEN은 후속 실행계획이다. 준비에 결속된10/6 checklist/dated 정책/receipt를 변경하지 않는다.

- [x] `[WidgetSymbolProfitabilityResearchRedesign1006] 등록 범위의 위젯 종목 수익성 선별·자료 기간 재설계` (`Due: 2026-10-06`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: [종목 신호연구 재설계§3–§6](../proposals/widget-symbol-profitability-research-redesign-plan-2026-10-05.md).
  - Acceptance: R0seed4/등록watch13·catalog/주문집합과 exact source/parent/cost manifest→R1독립 사건·모형/실제 손익 대사→R2최대2subset 선별 방식·동일 자본/기회 비교→R3forward20/40일 지원/공통 검증·기간 처분→R4consumer/정확 재사용/비용·보관 인계. 기존16일/25일 gate와 한 달 지원 부족을 명시하고 source gap/null·역사/미래 holdout을 구분한다.
  - Boundary: 사용자 두 계획 실행 지시로 격리 코드/연구만 실행. 기존 등록17·고정kernel·종목수4상한·2subset 축. collector/운영/dated 정책/10/6 checklist·배포/기동/PID·API·삭제 없음.6~8월 새후보 학습/순위/승인 복원 없음. 기존6가설/leg결손은 `WidgetEpisodeMachineResearchContract1006` 소유다.
  - Result: R0~R4 완료.17 중 공통4일 가격 비교7·원천 불완전8·frozen kernel 결손2. seed 축소010140 및 등록 subset010140/047810은 학습 양수지만1틱 stress 음수·10/2 손실.16일 holdout/25일 gate 미충족, 기간 효과 미식별/지원 부족으로 유한 종료. 완성 분봉의10/1 추가 보유를 확인해 계획의3일을4일로 정정. exact/full 재사용과 hash별 kernel/day incremental 구현,6~8월5869파일133.03MiB 삭제 적격0 보존 manifest 인계.
  - Evidence: [실행 리뷰](../audits/widget-bounded-research-and-advisory-execution-review-2026-10-05.md), `tmp/widget-symbol-profitability-redesign-20261006/final/{report,reuse,storage-dry-run}.json`.
  - Stop: 선별 권고1개/개선 없음/지원 부족·기간 효과 미식별 및 owner/artifact/closure 인계. 같은 입력의100종목/grid·기간 조합 확대 금지. raw 삭제는 storage dry-run manifest 검증으로 별도 인계한다.

- [x] `[WidgetAdvisoryCumulativeDiagnostic1006] 위젯3종목 자문 누적평가 실행·원천·집계·선택 진단` (`Due: 2026-10-06`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [자문 누적평가 진단§3–§4](../proposals/widget-advisory-cumulative-evaluation-diagnostic-plan-2026-10-05.md).
  - Acceptance: D0attempt/code/source/publication/effective 세대→D1producer/마지막consumer 연결→D2독립 행수/성숙·중복·검열→D3누적112/8월79 및6/5·9/9·9/29 경계/paired20일→D4confirmation2/3·scale-in/장전/의도된baseline부재→D5결함/정상carry·개선 순서 대사. proxy와 실제Pnl·기회와반복·실행완료와후보지원 구분, 필요한 표적반례/리뷰계획.
  - Boundary: 격리 진단/결함 코드만 실행. done/exit0와 후보 지원/정책 개선 분리. 원천 합성/실거래baseline복원·정책쓰기/기동/격리해제/새수집 없음. existing leg원천·의미감시·당일PID는 기존 `WidgetEpisodeMachineResearchContract1006`/`SemanticPolicyCoverageRemediation1006`/`WidgetEpisodeNextSessionStartup1006` 소유다.
  - Result: D0~D5 완료. 누적80/8/24·8월79 및12개 일별 재생 차이0.10/1은1460개DATA_WAIT/가격 결손/WS stale·future로 valid zero-signal day 아님. 새paired에9/29하한 적용, 삼성 장전4역사경로→forward1경로(검열), 정규장5219행 원leg/guard 완전0·두산/한화baseline부재 관측전용. 전session confirmation3 승계. dated loader10/6 정상 read-only 수용. filename/date 결속·격리 incumbent·역사/신규선택 분리·wrapper publication 날짜·간접producer stage코드 지문 보완, 원receipt 보존.
  - Evidence: [실행 리뷰](../audits/widget-bounded-research-and-advisory-execution-review-2026-10-05.md), `tmp/widget-advisory-cumulative-diagnostic-20261006/final/{report,reuse,execution-context,connection-table}.json`, 공통검증 `tmp/widget-research-plan-execution-20261006/validation.json`.
  - Stop: session별 정상실행/계산/지원/소비·경제성 처분과 결함owner/artifact/수정/closure test 또는 원천불가의유한처분 인계. positiveEV/실제기동은 진단 완료 바닥으로 추가하지 않는다. 동일원천 무한재생 금지.

- [x] `[MachineEntryTimingSourceFloor1005] 기계진입 타이밍 6~7월 미소비 확인 및 원천 허용 하한 보완` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 조건부 하한 변경 지시, [원천 경계 리뷰](../audits/machine-entry-timing-source-floor-review-2026-10-05.md).
  - Acceptance: 현재 로더·10/2 발행 보고서의33개 원천 경로/SHA·앵커 시각·별도 완료 이력 대사.6~7월 미소비를 확인한 후8/1을 JSON 읽기 전 하한으로 고정하고8월 입력·기존 provenance/경제성/주문 guard 보존. 코드리뷰→보완→회귀→재리뷰·실제 입력 차등 검증.
  - Result:8월11·9월20·10월2보고서,6~7월0·SHA 차이0.8월 앵커28/적격26 보존.130회귀 PASS, 기존/수정 하한의 입력33·37cohort 계산/선정 동일. [차등 증빙](../../tmp/machine-entry-timing-source-floor-20261005/inspection-and-differential.json).
  - Boundary: 작업본 코드·운영 계약만 변경. 공식10/2보고서·runtime 정책·10/6체크리스트 bytes 보존. 운영 릴리스 배포·기동·전체 장후 재생성·원천 삭제·외부 sync 없음.

- [x] `[NextSessionSemanticWidgetEpisodePlanning1005] 다음 영업일 기동 잔여·의미감시 coverage·Widget/Episode 개선계획 수립` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자3개 계획/점검 요청, [통합 상세계획](../proposals/next-session-startup-semantic-coverage-and-widget-episode-improvement-plan-2026-10-05.md).
  - Acceptance: selected release와 독립 consumer pin·실제 PID/dated 정책·prepared 전체 계약, 의미감시 producer→validator→알림 coverage, Main 연구에서 family별 재사용 가능한 방법과 실제 미선정 원인·간접 성공 veto를 점검. source/as-of/target·역사/미래·격리/OFF를 구분하고 실행 owner/closure/검증을 명시한다.
  - Result:10/6 current_full_contract PASS·release-set PASS. 정상 designated binding True인데 의미감시의 winrate_candidate_bundle_or_scope_mismatch 경고 재현. 휴장일 handoff 사각·새 비교/삼성 소비자·Widget/Episode 결과/알림 coverage 보완계획, Widget180초 수익 종료 건수 비감소 veto 및 scale-in replay 결손 확인. Episode45 valid-empty/16 gap·연구admitted0/calibration0을 분리. [점검·수용 증빙](../../tmp/next-session-semantic-widget-episode-planning-20261005/inspection.json).
  - Boundary: 코드/자동화·정책 발행·배포·서비스 제어·API·주문·경제성 재생성 없음. 미래 기동/PID/새 날짜 성능은 미수용.10/6 준비에 결속된 checklist와 정책/receipt를 보존하고 print-only parser로 계획을 검증한다.

- [ ] `[SemanticPolicyCoverageRemediation1006] 지정·적용 후 비교 및 family 결과 의미감시 누락 보완` (`Due: 2026-10-06`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [상세계획§3](../proposals/next-session-startup-semantic-coverage-and-widget-episode-improvement-plan-2026-10-05.md), 현재 selected3d0e5106의 실제 지정 오탐 재현.
  - Acceptance: P0 S1/S2 정상 operator designation·fixed-pair native validator 연결/자기비교·activation·변조 반례, S3/S8 완료 source·다음 due target·휴장/자정·notification filter/mock 소비. P1 S5~S7 Widget/Episode 결과·profile별 기동·원천/leg/terminal 의미 projection은 기존 family validator와 정확 count/nullable 경제성으로 결속한다. 구현→review→보완→회귀→재리뷰 및 감시 비용/읽기 세대 대사를 수행한다.
  - Result:10/5 사용자 실행 지시로 native designation/fixed-pair·완료 source/휴장일 due target·family projection·61profile PID/source 행렬·알림 generation 분기를 구현하고 리뷰/보완했다. 지정 오탐만 제거, 운영 원천 결손3finding 유지. 생성 중 stage는unobservable이며 회복으로 처리하지 않는다. [실행 리뷰](../audits/next-session-semantic-coverage-widget-episode-review-2026-10-05.md). 코드 gate와 물리 release/자연 소비는 분리한다.
  - Boundary: 추가 거래 권한 없음. 새 삼성 장후 replay는 기존 SamsungFrozenCandidateValidation1006 소유. OFF·격리·order/provider/threshold·custody guard를 감시로 변경하지 않는다. 감시의120초 source 신선도 판정은 매매 guard가 아니다. 설치·자연 감시/알림 및 이후 날짜 fixed-pair 수용이 남아 있으므로 OPEN 유지.
  - 최종 추가 리뷰: collector 표시용 sentinel의 gzip 표현 변경을 원천 부재로 처리하는 결함을 발견했다. decoded logical SHA·내용 충돌/손상/실제 부재 및 표시용 empty shadow 제외를 검증해 경제 원천 guard를 보존한다. [대사 원본](../../tmp/next-session-semantic-widget-episode-implementation-20261005/collector-archive-logical-diagnosis.json).
  - 야간 수용: 통합코드e16ac48b배포·124owner pin PASS, source10/2 whole strict PASS/controllerDONE, target10/6 current_full_contract PASS/findings0. calendar/후행 감시76·release/family425·collector137회귀 PASS(합산 금지). [최종 실행 영수증](../../tmp/next-session-semantic-widget-episode-implementation-20261005/next-session-final-preparation.json). 자연 감시/알림·새 날짜 비교는 기존 OPEN에 유지.
  - 야간 준비:10/5 사용자 다음 액션 실행 승인으로 휴장일 Main/controller/Widget/final-refresh/후행 감시 wrapper 대기 결함 보완·검토 코드 통합 배포·10/2→10/6 최종 세대 재수용을 실행한다. [실행계획§7](../proposals/next-session-startup-semantic-coverage-and-widget-episode-improvement-plan-2026-10-05.md). 매매 프로세스 start/restart와 미래 PID 확인은 오늘 gate에서 제외한다.
  - Stop: P0는07:20까지 기동 전 관리 점검, P1은16:30~23:59에 같은 ID의 후속으로 유지한다. 정확한 구현/자연 소비 단계별 수용 또는 owner/artifact/closure test를 명시한 인계.07:20은 새 broker guard가 아니며 별도 중복 OPEN을 만들지 않는다.

- [ ] `[WidgetEpisodeMachineResearchContract1006] 기존 원천 기반 Widget/Episode 기계 연구·선정 계약 보완` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~23:59`, `Track: Research`)
  - Source: [상세계획§4](../proposals/next-session-startup-semantic-coverage-and-widget-episode-improvement-plan-2026-10-05.md), Main 전체 판정/기회·후속 가격·고정 후보 개선 결과 및 현재 Widget/Episode 미선정 원인.
  - Acceptance: W1/W2/E1/E2 기존 raw→독립 기회·정확 scale-in/2-leg 재현 가능 census, W3의180초 수익 종료 건수 비감소 veto와 family primary/진단 지표 역할 정리. 삼성/그 외·세션/profile 유형 분리, 최대Widget3/Episode3사전 가설·동결/새 날짜 검증 계약과 producer/consumer/version 회귀를 설계·보완한다. 지원 부족·source 결손·측정된 개선 없음·후보 권고를 구별한다.
  - Boundary: 신규 수집·OFF prospective 복원·실거래 승격/주문 권한 없음. report-only 패턴 검증에 실제 체결 바닥을 요구하지 않으며, runtime promotion은 기존 실행/custody/cost 계약으로 별도 수용한다. 성공100%/80%·간접 수익 건수 보존을 새 탈락 조건으로 넣지 않는다.
  - Stop: 가용 source census 및 계약/유한 가설의 개선·개선 없음·not_identifiable/지원 부족 처분 인계. 동일 입력의 무한 grid/기간 확장 금지. Episode 자연 sequence/운영 결손은 기존 EpisodeCaptureSequence1006/DirectFamilySourceRepairLowPriceTwoLeg 소유를 유지한다.
  - Result:10/5 W1~W5/E1~E5의 가용 census·Widget180초 수익 종료 건수 veto 제거/legacy validation·고정6가설 연구 완료. Widget삼성 정규장 exact add 원천 결손, NXT장전 독립4기회/학습comparable2·역사비교검열로 운영 후보 미확보. Episode58계산 중29전체창 outcome0·29부분창/비교불가,3bar없음;9/29 invalid1,204·10/2 conflict106 제외 유지. [최종 연구](../../tmp/next-session-semantic-widget-episode-implementation-20261005/existing-source-research-v3/result.json)의 원 보고서 bytes 보존·SHA 검증 완료.
  - Next: 기존 저장 Widget leg/guard 및 Episode29부분창·3bar없음의 완료 분봉을 exact identity/SHA로 재결속 가능한지 확인한다. 없는 자료의 합성/수집 확대 없이 동일6가설은 종료. 새 입력·후속 날짜 및 실제 selector/loader 소비가 남아 OPEN 유지.

- [x] `[SamsungTickForwardConsumer1005] 삼성1틱 전환 후보의 이후 날짜 소비자 연결` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 다음액션 실행, [소비자 실행 리뷰](../audits/samsung-tick-transition-forward-consumer-review-2026-10-05.md).
  - Acceptance: 원 frozen 불변·별도 소비자/code SHA 고정, 원판정/가격/기존 체결의11tick 결속·원 parent/cost/stop/native·새 날짜 guard,4정책/전체·상시감시 비교, 정상/거부·대기/empty/excluded·실제 과거 대사 및 코드리뷰·보완·회귀.
  - Result:103회귀 PASS·519관측 receipt/조건/행동/선택/지표 차이0. v2소비자 계약 등록,10/6 실제 root의 원판정·완료가격·체결manifest3경로 부재로 `waiting_new_source_date`.9보호 SHA 불변.
  - Boundary: 신규 성능 검증·자동 실행 편입·추가 수집/API·운영 정책/배포/기동 없음. 새 날짜 검증은 기존 `SamsungFrozenCandidateValidation1006`가 소유한다.

- [x] `[SamsungTickPlanningFixtureReview1005] 삼성 연속 tick 연구계획·역사 fixture 결함 보완` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 추가연구계획 및 결함 코드리뷰·수정보완 반복 요청, [리뷰](../audits/samsung-historical-fixture-review-and-tick-research-planning-2026-10-05.md).
  - Acceptance: 가용성 census→최대2신규 가설·대조·지표·유한 종료계획, 과거 dated 경로 충돌 fixture 수정·원 SHA 보존·정상/거부 회귀·재리뷰, 기존 정책/선택 release/준비 보존.
  - Result: 상세계획 작성, fixture 고정 사본·정확 archive SHA 검증 및 재리뷰 완료, 최종 관련3 suite72 PASS. 선택 release의 원 frozen 검증 PASS·H2새 날짜 대기·10/6준비 verify PASS. 신규 가설 계산 미착수.
  - Boundary: 신규 가설 계산·삼성 정책 지정·배포·기동은 이번 계획 작성/테스트 보완 결과로 주장하지 않는다.

- [x] `[SamsungContinuousTickWindowResearch] 삼성 연속 체결 구간의 압력 전환 추가연구` (`Due: 2026-10-06`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: [상세계획](../proposals/samsung-continuous-tick-window-transition-research-plan-2026-10-05.md).
  - Acceptance: R0원본/hash→R1실제 구간 식별 가능성→R2shift1/disjoint10 두 정의 고정→R3동일 진입/종료/비용 비교→R4후보1개/개선 없음/원천·지원 부족 확정, source/time/seq/epoch/unknown·미래 누출 회귀.
  - Boundary: 사용자 계획 실행으로10/5 조기 완료. 기존519/상시감시206·세 날짜만 사용, 수집/API/실정책 변경 없음. 원 frozen 불변. 최대신규2+대조3이며 임계값/기간/sector 조합 확대 없음.
  - Result: [실행 리뷰](../audits/samsung-continuous-tick-transition-research-review-2026-10-05.md). 1틱 이동430/519·상시감시204/206 식별, 공통2날짜 완전6경로에서 원흡수 대비 양수 비율+5pp·확정 승률+25pp로 전체 origin 후보1개 동결. 상시감시 개선 미입증·사건/날짜 민감. 비중복10tick 개선 없음.58회귀·859원구간 prefix/수량합·1,038 label독립 행동 검증 PASS,8보호 SHA 불변.
  - Stop: 계획§7의 유한 종료. 실제 권고 후보가 생긴 경우에만 별도 frozen을 기존 `SamsungFrozenCandidateValidation1006`로 인계한다.

- [x] `[SamsungHistoricalKernelRecovery1005] 과거 삼성2후보의 커널 원본 복구·후속연구 필요성 점검` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 원본 결손 즉시 처리 지적 및 삼성 추가연구 필요성 질문, [복구 리뷰](../audits/samsung-kernel-recovery-and-followup-assessment-2026-10-05.md).
  - Acceptance: 원 요구 SHA와 동일 bytes 복구/보존, 원 frozen 불변, 기존519관측 선택·지표 대사, 현재 consumer/이후 날짜 준비, 기존10/6 운영 정책·release·prepared 불변 검증.
  - Result: 미참조 Git blob `38c14bd5…`에서 원 test SHA `c165a509…` 복구·보존 ref 등록. 두 후보 migration validated,519관측 대사 및160행 역사 입력 왕복 PASS, 이후 날짜 준비 waiting. 현재 회귀57 PASS·1 dated 경로 충돌은 같은 SHA의 archive로 옮긴 별도 격리 입력으로 재현 검증; 과거 fixture 전체 PASS로 표기하지 않는다.
  - Boundary: 새 연구 후보/운영정책/원천수집/API/배포·재기동 변경 없음. 새 거래일 검증은 기존 `SamsungFrozenCandidateValidation1006` 소유. H2 연속 tick 구간 소비 연구는 제안이며 이번 작업에서 실행하지 않았다.

- [x] `[MachineDesignationSamsungResearchPlanning1005] 비삼성 지정 코드·삼성 추가연구 상세계획 수립` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: 사용자 코드보완 상세계획 및 삼성전자 후보 추가연구계획 요청.
  - Acceptance: 실제 지정 발행 부재·dated generation 불변·적용 후 자기비교·삼성 전체 parent hash 의존성 대사.1회 지정/후속 양방향 비교·producer/consumer·회귀·장전 준비 및 삼성 원천/유한 가설/연구 목적/이후 인계 계획, 문서 리뷰·보완·링크·단일 owner·print-only parser.
  - Result: [비삼성 상세계획](../proposals/non-samsung-designated-policy-and-postapply-comparison-implementation-plan-2026-10-05.md), [삼성 추가연구계획](../proposals/samsung-absorption-differential-and-path-research-plan-2026-10-05.md) 작성. 지정과 독립검증 상태 분리, B0/C0/I_t/P_t 분리, 삼성 동등성 및 최대7정책 유한 비교를 설계했다. 두 계획의 새 수용/연구 지표는 제안이며 현재 동작으로 표시하지 않는다.
  - Boundary: 문서만 수정. 코드·지정 발행·추가 연구 재계산·기동·원천 수집·10/6 준비 변경 없음. 보호 hash·문서 검증은 `tmp/designated-machine-and-samsung-planning-20261005/validation.json`에 기록한다.

- [x] `[NonSamsungDesignatedPolicyImplementation1005] 비삼성 고정 정책1회 지정·적용 후 비교 구현` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [지정·장후 비교 상세계획](../proposals/non-samsung-designated-policy-and-postapply-comparison-implementation-plan-2026-10-05.md).
  - Acceptance: C0~C7의 지정 schema/발행/activation·기존 dated supersession/CAS·원 세대 보관·B0/C0/I_t/P_t 구분·양방향 비교·삼성 component 동등성·summary/strict/prepared 연결, 정상/거부/재실행/부분실패 회귀·리뷰/수정/재리뷰. 구현·준비와 실제 당일 PID 각각 증빙.
  - Boundary: 사용자 계획 실행으로 승인된 구현·지정 발행·통합 배포·정확일자 준비 owner. 대상10/6·비삼성 KRX 정규장 `pullback_p60_v0` 고정, 독립 검증 미완료 유지. 삼성/보조/타 family·계좌/주문/수량/손절/custody guard 권한 확대 없음.
  - Stop: 구현/준비 결과 또는 날짜 종료·parent 충돌·source 결함의 구체적 사유 확정. target 날짜 자동 연장 없음. 장후 비교는 `NonSamsungMachineForwardComparison1006`, 실제 Main 소비는 `DirectFamilyPreopenPolicyHandoff`에 인계.
  - Result: [실행 리뷰](../audits/designated-machine-policy-and-samsung-differential-execution-review-2026-10-05.md). 코드 `3d0e5106` 배포,10/6 지정 bundle `8fb91f19…`/component `6b6fb204…`, 자동 selected=false·운영자 지정 분리.606개 표적 회귀·실제7,069관측 대사 차이0, strict PASS·DONE·prepared_verified. Main 실제 당일 PID/이후 성능은 후속 owner에 인계.

- [x] `[SamsungAbsorptionDifferentialResearch1005] 삼성 흡수 후보 원천 차이·가격경로 유한 추가연구` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: [삼성 추가연구계획](../proposals/samsung-absorption-differential-and-path-research-plan-2026-10-05.md).
  - Acceptance: R0중복 가설/원천 census→R1성공·손절·완전미도달/검열 차이→R2정책 전체/공통 사건→R3최대5변형과2대조 정책→R4권고/개선 없음/식별 불가·동결 인계. raw 시점/epoch/cost/stop·source 결손·metric/날짜 지원·표적 회귀/재리뷰 검증.
  - Boundary: 기존 원천만 소비하는 승인된 오프라인 연구. 전체519/fixed-watch206 구분, 삼성 양수 가격경로 지표는 신규 연구 제안이며 현재 운영 승률 계약 변경 아님. API·수집 확대·보조 AI 혼합·Widget 실현 수익 이식·삼성 정책 지정/발행/배포 없음.
  - Stop: 중복/원천 부재 가설을 닫고 최대7정책에서 후보1개 권고/개선 없음/판단 불가 확정. 임계값·종료기간 무한 추가 금지. 이후 자연 검증은 기존 `SamsungFrozenCandidateValidation1006` 소유.
  - Result: [실행 리뷰](../audits/designated-machine-policy-and-samsung-differential-execution-review-2026-10-05.md).5변형+2대조 완료, H2 하나 동결·waiting_new_source_date. 전체 날짜 가중 경계 승률55.56→61.11%이나9/29 손절1건 감소에 한정되고 fixed-watch 개선은 미입증. 삼성 운영 정책 유지. 과거 veto2개 kernel 원본 결손은 기존 후속 owner에 명시.

- [x] `[MachineAcceptanceRemediationSamsungPlan1005] 수용조건 결함보완계획 및 삼성 승계·추가 연구 필요성 점검` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: 사용자 결함보완계획 수립·삼성 정책 유지 사유 및 추가 연구 필요성 점검 요청.
  - Acceptance: 확정 결함/설계 변경 구분, 평가 단위·선정조건·영향 producer/publisher/loader·회귀·실행 순서·후속 owner 계획. 삼성 최신 후보·원 연구·운영 generation·미래 frozen 후보 대사 및 추가 연구의 유한 종료 기준. 문서 리뷰/보완/링크/단일 소유/diff/print-only parser.
  - Result: D1~D8/P0~P6 보완계획 확정. 삼성 absorption 학습21.43→50%,10/2 부모60분 미도달2·후보목표4/손절2/미도달2로 기존 binary null. 현재 생성기는 삼성519건의 부모 행동만 재생하고 운영 absorption은 미등록. 기존 미래 frozen에는 과거 veto2개만 있어 최신 후보 연결 누락 확인. 원 선택10건 identity/raw/경계결과 차이0; 알려진 종료가격 양수율은 부모1/2·후보4/8로 모두50%. S1최초 신호·S2미도달 포함 비교·S3원천/이후 날짜 인계가 필요한 것으로 판단.
  - Boundary: 계획·읽기 전용 점검. 코드·수용조건·runtime 정책·발행·배포·기동 변경 없음. 기존 보고서/원천을 수정하지 않고 현재와10/6 machine hash 일치를 확인했다. 정책의 우월성·새 독립 검증 완료는 미주장.
  - Evidence: [결함보완·삼성 연구계획](../proposals/machine-admission-acceptance-remediation-and-samsung-research-plan-2026-10-05.md), [직접 점검](../../tmp/machine-acceptance-remediation-samsung-review-20261005/inspection.json), [문서 검증](../../tmp/machine-acceptance-remediation-samsung-review-20261005/validation.json).

- [x] `[MachineAdmissionAcceptanceImplementation1005] 기계 admission 수용 계약·보고·발행 일치 보완` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [결함보완계획 §2~§4](../proposals/machine-admission-acceptance-remediation-and-samsung-research-plan-2026-10-05.md).
  - Acceptance: P0~P5의 새 계약·공용 validator·실제 계산 metric·날짜/coverage·winner 교집합·metric role·publisher/loader/summary 연결, 정상 선정 및 거부 회귀, 고정401선택·원 행동 차이0, 리뷰/수정/재리뷰/표적 검증. 현재 새 날짜 부재는 선정 대기로 정확히 표시.
  - Result: 새 observation acceptance 구현·360표적 회귀·실제 생성 완료.401선택 및 전체 연구7,069관측 차이0. 전체 탐색 학습45.75→70.20%, computed/train-qualified true, fresh-validation not_observed, selected false. native3건1승 진단과 retained0/new1/excluded17 보존. [실행 리뷰](../audits/machine-admission-remediation-and-samsung-execution-review-2026-10-05.md).
  - Boundary: 비삼성 고정 후보 수용 계약과 보고 소유. 삼성 후보 등록·운영 source 경제성 수리·새 원천 수집·매매 guard는 별도. 배포/정책 소비는 해당 실행 지시와 기존 Main PREOPEN owner에서 대사.
  - Stop: P0~P5 코드/격리 재생 결과를 확정하면 종료. 미래 source 대기와 재연구로 이 구현 owner를 무기한 연장하지 않는다. 자연 검증은 기존 `NonSamsungMachineForwardComparison1006` 소유.

- [x] `[SamsungAbsorptionOutcomeReview1005] 최신 삼성 흡수 후보의 최초 신호·미도달 평가 및 이후 날짜 인계` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: [삼성 유한 연구계획 §5~§6](../proposals/machine-admission-acceptance-remediation-and-samsung-research-plan-2026-10-05.md).
  - Acceptance: 고정 absorption 후보·519관측/206fixed-watch 구분, S1최초 신호와 점유·S2고정 선택의 target/stop/timeout·순이익 양수 가격 진단·S3원시각 feature/receipt 및 최신 후보 frozen/adapter 인계. 원watch/date를 독립 episode 수로 늘리지 않고 코드/산술/원천/문서 검증.
  - Result: S1~S3 완료.519/206관측·68/31신호 구간, 첫 신호 이후10/2 선택2/8 그대로. 목표 도달률0→50%, 비용 후 양수50→50%, binary 비교 미식별. 최신 absorption frozen/adapter 검증과10/6 waiting_new_source_date 인계. [실행 리뷰](../audits/machine-admission-remediation-and-samsung-execution-review-2026-10-05.md).
  - Boundary: 기존 원천·오프라인 평가. 임계값/청산 조합 재탐색, 신규 수집, 부분 feature로 과거 전체 최신 입력 합성, 장전/Widget 실제 손익 이식, 정책 발행/배포/기동은 이 연구 산출물에 포함하지 않는다.
  - Stop: S1~S3의 개선/개선 없음/판단 불가와 최신 후보 인계를 기록하면 종료. 이후 자연 날짜 검증은 `SamsungFrozenCandidateValidation1006` 하나로 연결한다.

- [x] `[MachineAdmissionAcceptanceReview1005] 연구 결과와 기계 admission 수용조건의 차이 재점검` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: 사용자 연구 결과와 기존 승계 차이·수용조건 재점검 요청.
  - Acceptance: 원401선택 identity/raw/action/binary 및 날짜별 주승률 일치, 현재 native 분모·hurdle·holdout·publisher 재검증, 성공100%/80% 보존 gate 유무, 삼성/비삼성 분리, 구체적인 계약 보완안과 설명 정정. 링크/소유/diff/print-only parser 및 원 정책/보고서 해시 보존 검증.
  - Result: 현재 nested 관측 비교에서도 학습42.59→67.75%,10/2 53.70→75.00%,전체45.75→70.20% 재현. 비용/stop/가격 확정4,368 중4,244가 native ID 결손으로 제외돼124개만 최종 자격 비교. 연구 첫 선택과 native 교차는 부모0/217·후보1/197; 정식 native는 부모32기회17승·후보3기회1승이다.30/10·50% coverage·raw/+5pp·새 날짜 조건이 원 승계 이유다. 전체 연구 후보가 더 나쁘다는 앞선 해석을 정정했고, 삼성은 이3개 비교 대상이 아니다.
  - Findings: `candidate_evaluated`가 계산 여부 대신 학습 적격 여부를 표시하고, 기존 승리 보존 diagnostic1건은 실제 교집합0건과 다르다. publisher의 학습 날짜 전부 포괄 조건도 생성기1날짜 조건과 차이가 있다. 관측/native 수용 계약 및 보고 필드의 후속 코드 보완 대상으로 기록하며 이번 점검에서 수정 완료 처리하지 않는다.
  - Boundary: 점검/문서 기록. 현재 정책 선정조건·policy·release/PREOPEN·주문·원천 수집 변경 없음.10/2를 새 holdout으로 재라벨링하지 않는다. 고정 후보 연구는 완료 상태를 유지하며 contract 보완이 필요하다.
  - Evidence: [수용조건 리뷰](../audits/main-machine-admission-acceptance-contract-review-2026-10-05.md), [원 집단·단위·선택 대사](../../tmp/machine-admission-acceptance-review-20261005/acceptance-reconciliation.json), [검증 기록](../../tmp/machine-admission-acceptance-review-20261005/validation.json).401선택 대사·가격 원천3/kernel8 hash·정책 hash 보존·링크/단일 소유/parser/diff 및 선택 release의10/6 `current_full_contract` PASS. 실제 당일 PID 소비는 미도래다.

- [x] `[NextSessionPolicyStoragePlan1005] 다음 영업일 정책·기동 및 디스크 정리계획 확정` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자10/6 최종 적용계획·디스크 정리계획·장후 기계 생성 설명 요청.
  - Acceptance: 실제 selector/장후 호출/준비 검증/PID·policy scope·디스크 상태 확인, 선행 결손/구현·선정·적용·기동·장후 단계/owner·정리 보호/중단 기준 및 현행/개선 후 생성 방식을 문서화. 문서 리뷰/수정/재리뷰·link/owner/diff/print-only parser.
  - Result: 선택9c0c0632의10/6 준비 검증 FAIL, collector `history_generation_changed`; Episode10/5 preflight source-quality hash 불일치 확인. 비삼성 pullback은 운영 연결 전이며 현행 자동 생성은 winrate VWAP veto 경로. 가용약16.95GiB·사용89%, 참조된 release/고유 연구 원천을 보호하는 정리 순서 확정. 현재 정상 기동/후보 적용 완료를 주장하지 않는다.
  - Evidence: [최종 적용·기동 계획](../proposals/next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md), [디스크 정리계획](../proposals/runtime-and-research-storage-cleanup-plan-2026-10-05.md), [검증 기록](../../tmp/next-session-policy-storage-plan-20261005/validation.json). parser 누락된10/4 미래 OPEN3건을동일ID/수용/이력으로이관해현재단일owner검증. 계획 작성이며 구현/배포/기동/삭제 미실행.

- [x] `[MachinePolicyCutoverPreparation1005] 비삼성 후보 운영 연결·현재 준비 결손 복구 패키지` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [최종계획 P0~P4](../proposals/next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md), [고정 후보 구현계획](../proposals/non-samsung-pullback-candidate-implementation-plan-2026-10-05.md).
  - Acceptance: collector history 변동 대사와 영향 단계 복구, Episode profile별 hash 결손 분류, 공용 evaluator/schema/scope/publisher/loader/장후 registry 연결·발행 owner 단일화, 현재 parent/운영 자격 대사, 리뷰/수정/표적회귀/재리뷰. 실행 권한 안에서 불변 release·정확한 날짜 정책·동일 세대 strict/controller/prepared 수용 또는 후보 보류의 구체적 사유 확정.
  - Boundary: 사용자 두 계획 실행 지시로 준비 구현·결손 복구·검증된 배포를 실행한다. 연구 권고를 운영 자격으로 바꾸거나 probe를 native로 합성하지 않는다. 기존 winner retention veto 복구 금지. 삼성/보조/다른 session·custody/격리/guard 유지.10/6 실제 PID 수용은 기존 `DirectFamilyPreopenPolicyHandoff`/`WidgetEpisodeNextSessionStartup1006` 소유이며 중복 등록하지 않는다.
  - Intake: `tmp/policy-cutover-and-storage-execution-20261005/intake.json`. 작업본HEAD99cf22c1·선택9c0c0632·dirty patch와7개수정예정파일원bytes를보관했고63개연구frozen hash를검증했다. 역사원본과새공용kernel을별도세대로보존한다.
  - Stop:10/6 07:20 적용/적격 incumbent 승계/준비실패를 구분하여 인계. 새로운 자료 없이 과거 연구를 재개하지 않는다.
  - Result: 공용 evaluator/생성기/dated publisher 연결 및 원천 결손 복구 완료. 통합 커밋3e982ece를 불변 release로 배포하고 영향 있는 inactive 장후 pin2개를 전환했다. 전체 표적1,033 PASS·물리 release200 PASS. native 부모32기회17승(53.125%), 후보3기회1승(33.333%)와 새 holdout 부재로 삼성/비삼성 모두 incumbent 승계.10/6 prepared 검증은 `current_full_contract` PASS, 실제 activation/PID는 미도래다. 최종 문서 고정 후 재검증 결과는 [실행 closure](../../tmp/policy-cutover-and-storage-execution-20261005/closure.json)에 봉인한다.
  - 재개: 사용자 보완계획 실행에 따른 새 acceptance 코드의 통합 배포·현재10/6 준비 재봉인을 수행한다. 종전3e982ece 완료는 이전 세대 증거이며 아래 실행 리뷰/closure의 최종 결과를 따른다.
  - 재완료: 새 acceptance 코드 `c8c00c06` 통합 커밋·불변 release 선택, inactive 장후 unit2개 pin 갱신. workspace595 PASS·물리 release97 PASS. 새 보고서의 비삼성 학습 적격/독립 날짜 대기와 삼성 미등록 상태를 정식 summary로 전달했다. 전체 strict PASS·controller done·10/6 `current_full_contract` PASS, findings0. 현재/예정 정책 bytes 보존, Main 당일 activation/PID는 미래 owner 소유. [현재 실행 closure](../../tmp/admission-remediation-execution-20261005/closure.json).
  - Residual: 기존 projection gzip3개 종전 압축 bytes 미보관. 원 capture·기존 연구/코드는 보존했고 비삼성6,550개 identity/raw SHA/부모·후보 행동 차이0을 확인했다. 역사 frozen manifest는 변경하지 않았으며 이후 cache 교체는 이전 세대를 먼저 보관한다.

- [x] `[VerifiedStorageCleanup1005] 참조·복구 검증 기반 운영 및 연구 저장공간 정리` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [디스크 정리계획](../proposals/runtime-and-research-storage-cleanup-plan-2026-10-05.md), 사용자 추가 최대 용량 확보 지시.
  - Acceptance: 최신 selector/previous/service/PID/FD/고유 Git·연구 참조 폐쇄 보호 목록, 파일별 dry-run manifest·복원 증거·실제 회수량 및 사후 보호 참조 검증. 검증된 후보 소진 또는 필요 여유 확보 시 종료.
  - Boundary: 사용자 정리계획 실행 지시 범위에서 검증된 대상만 정리한다. 고유 원천/정책/연구63파일 및 간접 참조·source-quality·custody 보호. 서비스/주문/패키지 변경 없음.25GiB는 관리 제안이며 삭제 확대·매매 중단 임계치가 아니다.
  - Result: Git blob/archive ref 복원 검증을 통과한 checkout 중복8,032파일과 종료 pytest fixture2개 정리. 고유16파일·현재/rollback/service/PID/연구 참조 worktree·raw 보존. 중복 정리 창 가용량 증가667,475,968 bytes; 재계산·archive·release 쓰기 포함 실측은 약16.89GiB로25GiB 미달. 검증된 후보 소진으로 종료하며 보호 원천 삭제로 목표를 강제하지 않는다. [정리·복원·최종 디스크 증빙](../audits/machine-policy-cutover-and-storage-execution-review-2026-10-05.md).
  - 추가 실행: 선택적 연구 캐시342,289 entry 정리, 과거 모니터5파일 및 profile checkpoint2,796파일 무손실 보관/검증, 미사용 bytecode10,648경로 정리. 중간 가용22.43GiB. 참조 worktree·원천·Parquet·정책 보존. [새 정리 증빙](../audits/machine-admission-remediation-and-samsung-execution-review-2026-10-05.md).
  - 최종 실측: optional catalog VACUUM·종료 pytest fixture1개 추가 정리 후, 재계산·배포 쓰기 포함 가용15.65→22.24GiB, 순증가약6.60GiB.25GiB에는 미달하나 검증된 삭제 후보를 소진했으며 보호 원천과 참조 release는 유지했다. 최종 bytes는 현재 실행 closure에 기록.

- [ ] `[NonSamsungMachineForwardComparison1006] 비삼성 고정 기계 후보의10/6 이후 날짜 비교` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~23:59`, `Track: MainEntry`)
  - Source: [최종계획 §4](../proposals/next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md), `NonSamsungFinalPolicyDecision1005`의 종료된 고정 후보·부모·원천 계약.
  - Acceptance: 운영 연결 여부를 먼저 확인하고10/6 ENTER/BLOCK/RECHECK 관측을 삼성 제외·venue/session 분리하여 고정 후보와 부모 비교.10분 미도달은 이후 최대60분 경로로 보조 평가하되 순서/공백/검열 분리. 원천·군집/native 분모·주승률/지원조정·coverage/결손 민감도, source10/6→effective10/7 선정/승계/발행 여부를 정확히 기록. 당일 조건을 튜닝하면 동일 자료를 독립 검증으로 쓰지 않는다.
  - Boundary: 성공100%/80% 보존 탈락 조건 없음. 관측 승률/실제 경제성 분리. 자동화 미연결이면 별도 관측 비교와 자동 발행 미실행을 표시하며, 후속 실행 권한을 이 계획에서 새로 만들지 않는다. 운영 원천 경제성은 기존 `DirectFamilySourceRepairMainMechanisticEntry` 소유.
  - Stop: 고정 후보의 날짜별 비교·선정/승계 사유를 확정하면 종료. 원천이 없으면 `not_observed`, 계약 실패면 소유자·closure test를 명시하고 동일 입력 무한 재실행 금지.
  - 후속 보완안: [지정 상세계획 §5](../proposals/non-samsung-designated-policy-and-postapply-comparison-implementation-plan-2026-10-05.md)의 구현·지정 receipt가 존재할 때만 고정 B0/C0의 적용 후 비교 분기를 사용한다. 기준 정책과 실제 incumbent를 분리하고 자기비교를 막는다. 새 고정-pair 계약을 구현했으며 지정 receipt와 실제 activation·관측 P_t가 있는 경우에만 적용 후 비교로 분류한다. 지정이 없으면 기존 acceptance 경로를 따른다.

- [ ] `[WidgetEpisodeNextSessionStartup1006] Widget/Episode 다음거래일 정책·preflight·PID 수용` (`Due: 2026-10-06`, `Slot: INTRADAY`, `TimeWindow: 07:32~20:00`, `Track: RuntimeStability`)
  - Source: [재점검리뷰§4–§5](../audits/source-repair-repeat-review-and-next-session-readiness-2026-10-04.md), 사용자다음영업일정상가동재점검지시.
  - 야간 준비 결과: selectede16ac48b Main/Widget/Episode 설정 배포·dated/native loader·07:32standing apply권한·122profile timer PASS. Episode10/6 native계획58carry/3격리 및58연구 preflight원천 valid, Widget2eligible/2blocked. 봇은 오늘 기동하지 않았고10/6 applied/authority/PID/source는미래수용이다.
  - 오늘 준비 경계:10/5에는 dated/native apply 계획과 설정·예약·strict/controller/prepared를 수용한다. 사용자 명시대로 실제 봇은10/6에 기동하며 PID 소비는 그때 확인한다. 기존58/3 계획을 실제 기동 수로 표기하지 않는다.
  - Acceptance: Widget07:32정책반영/07:58기동경로와현재PID의10/6reload/행동policy hash·custody/source receipt를대조한다. 기존10/3 startup은당일reload증거로사용하지 않는다. Episode의10/4 역사 기준58격리제외profile을 출발 목록으로 하여 현재전체profile의당일applied/authority·research/Main/token preflight·실제unit/PID·자연원천을profile별로대조하고3격리를별도표시한다. 기존Main `DirectFamilyPreopenPolicyHandoff`·Episode sequence owner와증거를연결하되코드/준비/기동/주문/경제성을구분한다.
  - Boundary: read-only검증과결과기록. 실제가동/기동부작용이있는preflight/정책쓰기/재기동/API/token조회/주문/격리해제는자동실행하지 않는다. source없음은not_observed,미도래는not_yet_due이며source gap의0치환없음.
  - 이력:10/4 준비PASS.10/5 현재 Main prepared 재검증은collector history 변경으로FAIL이며, Episode cj_cgv_morning preflight의candidate_source_quality_hash_mismatch를확인했다. 당일profile별source-blocked/경제성격리/disabled/eligible을재분류한다. 기존독립e6d4d3b9 release/service pin을보존하고10/6 실제소비는별도수용한다.
  - 이관:10/5 print-only parser에서10/4 소유 항목이 제외됨을 확인하여 현재 문서로 이동. ID·기존 수용/권한·준비 이력 보존; 실행 완료 처리 아님.
  - 후속계획: [최종 적용·기동 계획](../proposals/next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md). 이전58/3 수치를현재가동PASS로사용하지 않는다.
  - 잔여 순서 보완: [최신 점검·계획§1–§2](../proposals/next-session-startup-semantic-coverage-and-widget-episode-improvement-plan-2026-10-05.md).10/6 Episode applied는07:32 기존 owner apply 전 부재이며 future_due다. Widget의07:32 quiescent apply/restore 실제 terminal·당일 loaded-policy digest를 확인한다.3격리·관측 전용과 당일 기동 실패를 별도 집계한다.
  - 최신 준비 주의:10/5 20:10 기존 예약이Widget source10/2·Main/controller source10/5로 진행 중이다.20:38 selected cwd의10/6 native prepared 재검증은FAIL(`strict_stage_generation_stale:widget_policy`, tower/checklist/collector 세대 불일치 등).12보호 SHA 동일은 현재 PASS가 아니다. 진행 중 코드/입력/lock을 교체하지 않고 종료 후 실제 완료 source→target10/6 세대를 동결하여 summary/intake→strict→controller→prepared 재수용한다. [현재 증거](../../tmp/next-session-semantic-widget-episode-implementation-20261005/current-readiness-and-protection.json).
  - 후속 관측:Widget20:43 succeeded. 완료 report/native loader를 확인해 projection만 새 세대에 재결속했고 정책 파일은 그대로다.20:53 native prepared 재검증은여전히FAIL,Main/controller10/5는진행중. [최신 증거](../../tmp/next-session-semantic-widget-episode-implementation-20261005/post-widget-generation-readiness.json). 장후 전체 종료·최종 세대/strict/controller/prepared gate는 남겨둔다.

- [ ] `[SamsungPremarketForwardValidation1006] 고정 삼성전자 장전 두 관측 가설의 독립 날짜 검증` (`Due: 2026-10-06`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [계획§4–§6](../proposals/samsung-premarket-forward-validation-and-source-release-preparation-plan-2026-10-04.md), [준비리뷰§4](../audits/samsung-premarket-forward-validation-and-source-release-preparation-review-2026-10-04.md), 사용자 이후검증 준비 범위.
  - Acceptance:10/6이후 자연원천의exact parent/canonical/native/route/epoch/cost/label/원guard와kernel 검증, frozen두가설의Main 원binary/별도가격CF 소비 evaluator 구현·리뷰/회귀, 동일population parent 대비승률·비용·미확정 비교. 최초3적격날짜 한도·각binary3/독립2날짜 연구gate·parentempty 비교미식별·성공보존veto없음·조건재선정없음.
  - Boundary: 새tmp generation의오프라인 연구. source없음은waiting, canonical/route 결손은excluded/source_gap, parent/kernel변경은replan. archive CF는Main native/실현PnL을대체하지 않는다. 연구gate와정식publisher/운영경제성/runtime bridge를분리하며 실제매매/수집/배포/재기동권한없음.
  - 준비이력: `tmp/samsung-premarket-forward-preparation-20261004/final-v2-cold/source-inventory.json`의4경로부재·`waiting_new_source_date`였다. 기존정규장 `SamsungFrozenCandidateValidation1006`과별도소유다.
  - 현재: 통합배포후 `tmp/integrated-deployment-disk-cleanup-20261004/forward-release-bound/frozen-contract.json`의7a8ba145 계약을선택release 코드로소비한다. 원parent/두가설/조건/비용/기간/미래3날짜한도와kernel bytes는40f567d0 계약과동일하며차이는승인된불변release의물리코드경로뿐이다. 40f567d0/458ce71a는역사receipt로보존한다. 원천4경로는여전히waiting이고새날짜성과/정식candidate 미검증이다.
  - 이관:10/5 print-only parser에서10/4 소유 항목이 제외됨을 확인하여 현재 문서로 이동. ID·기존 수용/권한·준비 이력 보존; 실행 완료 처리 아님.

- [ ] `[SamsungFrozenCandidateValidation1006] 고정 삼성전자 후보의 이후 날짜 검증` (`Due: 2026-10-06`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [계획§6](../proposals/samsung-fixed-watch-evaluation-and-owner-comparison-plan-2026-10-04.md), [실행 리뷰§6/§8](../audits/samsung-fixed-watch-evaluation-and-owner-comparison-review-2026-10-04.md), 사용자 고정 후보 후속검증 준비 범위.
  - Acceptance: 자동 생성된10/4 이후 원천만 intake, 원parent/hash/trace/guard/native/cost/label·독립epoch 확인, 고정 두 후보의 삼성전자 전체origin/상시감시 성과·미확정 수 대조. 후보 재선정 및 source 수집 없이 연구 receipt와 처분 기록.
  - Boundary: 새tmp generation의 오프라인 검증. source없음은waiting, 식별 불량은excluded/valid-empty 구분, parent·전역 계약 변경은replan. 실제publisher/주문/API/provider·배포·기동 및10/6 기존owner 변경 없음.
  - 현재: `tmp/samsung-fixed-watch-evaluation-20261004/next-date-readiness/preparation-status.json`에서 필요한4경로 부재·`waiting_new_source_date`; 새 날짜 성능은 미검증.
  - 최신 후보 인계 보완: 기존 frozen의2개는 foreign/program veto이며 absorption 후보가 아니다. [10/5 계획 S3](../proposals/machine-admission-acceptance-remediation-and-samsung-research-plan-2026-10-05.md)에 따라 `SamsungAbsorptionOutcomeReview1005`가 준비한 최신 `absorption_p60_v10`의 별도 frozen/adapter를 이 owner에서 추가 검증한다. 기존 원 계약을 덮어쓰지 않으며 adapter 준비 여부를 먼저 확인한다. 준비되지 않았으면 `latest_candidate_adapter_not_ready`, 원천 부재는 `waiting_new_source_date`를 구분한다. 과거2후보 검증만으로 최신 후보 완료를 선언하지 않는다.
  - 최신 후보 준비 완료: `tmp/admission-remediation-execution-20261005/replay-v2/samsung-frozen.json`, `samsung-forward-readiness.json`과 새 `samsung_absorption_acceptance_research` CLI를 사용한다. after10/5 원 projection·완료 가격 및 원 raw exact receipt를 검증한다. 현재 두 자동 생산 경로 부재로 waiting이며 실제 검증/선정은 미실행. 기존 두 veto의4경로 계약과 구별한다.
  - 추가 계획 인계: `SamsungAbsorptionDifferentialResearch1005`가 실제 권고한 후보가 있을 때 별도 frozen을 추가한다. 비삼성 지정으로 전체 parent/kernel이 바뀌면 허용 diff의 삼성 component 동등성/migration receipt를 먼저 검증한다. 기존 frozen bytes는 변경하지 않으며 실제 삼성 동작 변화는 재계획한다.
  - 코드 경로: 과거 두 veto·원흡수·H2 frozen 후속 검증 CLI는 선택된 승인 release의 cwd에서 실행하고 `--root /home/ubuntu/KORStockScan`을 지정한다. 테스트 파일도 원 kernel 증거에 포함되므로 새 workspace 테스트를 배포 release의 증빙으로 혼용하지 않는다. 새 release 채택 시 대응 migration을 먼저 검증한다. 아래 신규1틱 소비자는 별도 검토된 workspace 코드·v2소비자 계약을 사용한다.
  - 연속 tick 후보 인계: [10/5 실행 리뷰](../audits/samsung-continuous-tick-transition-research-review-2026-10-05.md), `tmp/samsung-continuous-tick-transition-research-20261005/final/frozen-candidate.json`의 `absorption_p60_tick_shift1_v1`은 전체 origin 연구 권고다. 상시감시 개선·운영 적용은 미입증. 기존 H2 adapter로 읽지 않으며 `forward_adapter_status=not_implemented_for_new_tick_window_definition`이다. 이후 검증 전에 새11tick 구간/원흡수 결속 소비자 연결·코드리뷰가 필요하다. 같은6과거 관측을 새 날짜 검증으로 사용하지 않는다.
  - 연속 tick 최신 준비: 위 미구현 상태는 원 frozen 작성 이력이다. `SamsungTickForwardConsumer1005`가 [별도 연결](../audits/samsung-tick-transition-forward-consumer-review-2026-10-05.md)을 완료했다. 현재 `tmp/samsung-tick-forward-consumer-20261005/consumer-contract-v2.json`과 `samsung_tick_transition_forward_validation --contract <v2> --date 2026-10-06 --root /home/ubuntu/KORStockScan --output <new-generation>`를 사용한다. 실제 원천3경로 부재·waiting이며 신규 성능/정책 선택은 미검증. 원 frozen을 다시 발행하지 않는다.
  - 장후 연결 구현: [최신 계획§6](../proposals/next-session-startup-semantic-coverage-and-widget-episode-improvement-plan-2026-10-05.md)의 optional source-only sidecar·terminal/index·감시 연결을10/5 구현했다. 원 v2 bytes의 stable copy와 source10/6 waiting 세대를 보존했고 lock/재사용/변조/실패/wrapper native-exit 회귀를 검증했다. 현재 설치 unit은3d0e5106 wrapper이므로 새 코드의 자연 소비는 미수용이다. 원천 대기를 정책 기동 실패로 바꾸지 않으며 원 고정 후보/code SHA를 덮어쓰지 않는다.
  - 실행 인계: 최신 원흡수 migration 및 `tmp/samsung-absorption-differential-research-20261005/final/frozen-candidate.json`의 H2를 구분한다. H2는 `samsung_absorption_differential_research --forward-frozen <H2> --base-frozen tmp/admission-remediation-execution-20261005/replay-v2/samsung-frozen.json --date 2026-10-06 --root /home/ubuntu/KORStockScan --output <new-output>`로 검증한다. 둘 다 현재 waiting. 과거 veto2개는 `SamsungHistoricalKernelRecovery1005`에서 원 테스트 bytes c165a509를 정확 복구했다. 원 frozen을 보존한 migration validated,519관측 mask/metric 차이0·160행 역사 입력 왕복 PASS, 현재 선택 release의 준비 CLI는 `waiting_new_source_date`다. 최신 상태는 `tmp/samsung-kernel-recovery-20261005/next-date-readiness/preparation-status.json`을 따른다.
  - 이관:10/5 print-only parser에서10/4 소유 항목이 제외됨을 확인하여 현재 문서로 이동. ID·기존 수용/권한·준비 이력 보존; 실행 완료 처리 아님.

- [x] `[NonSamsungFinalPolicyDecision1005] 비삼성 고정 후보의 최종 비교·구현 판단·연구 종결` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 연구 종료 목표 확정 및 다음 액션 실행 요청, [연구 재정리 계획 §16](../proposals/main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md), [시간 연결 검증 결과](../audits/non-samsung-target-continuity-research-review-2026-10-05.md).
  - Acceptance: F1 고정 부모/후보 전체 선택의 날짜별·학습 합산 주승률/분모/미확정 민감도, F2 같은 선택의 목표·trailing 시작·조건부 청산 분리, F3 정확한 규칙·영향 producer/consumer·guard/검증/되돌림 구현계획 또는 비권고/판단 불가 결론. 삼성 상태는 별도 병기. 필요 수정은 리뷰/보완/표적 검증/재리뷰, 문서는 link/단일 owner/diff/print-only parser.
  - Boundary: 고정 `pullback_p60_v0`와 기존9/29·9/30·10/2 자료. 성공100%/80% 보존·미확정 전량 해소·양의 청산CF를 새 진입 후보 탈락 조건으로 추가하지 않는다. 과거 tick/depth 복구 재개·신규 원천 수집·삼성/보조 추가 탐색·정책 발행/배포/재기동 없음.
  - Stop: §16의 `candidate_recommended`/`no_improvement`/`not_identifiable` 중 하나와 F1~F3의 근거 또는 식별 불가 사유를 확정하면 종료. 동일 자료 재생·새 임계치 탐색·독립 자료 대기로 무기한 연장하지 않는다.
  - Result: F1~F3 완료, `candidate_recommended`로 연구 종료. 부모217·후보197선택/합집합401개, 목표80→93·손절75→48·미확정56→51, 주승률45.75→70.20%. 공통39군집52.47→53.24%와10/2 이진 가정 민감도-17.54~+41.23pp를 별도 공개. 전체 선택의 목표/시작선/청산 진단과 정확한 규칙·공용화·schema/loader·guard/회귀/rollback 구현계획 확정. 운영 적용은 미실행.
  - Evidence: [최종 리뷰](../audits/non-samsung-final-policy-decision-review-2026-10-05.md), [구현계획](../proposals/non-samsung-pullback-candidate-implementation-plan-2026-10-05.md), `tmp/non-samsung-final-policy-decision-20261005/{report,comparisons,candidate-recommendation,validation}.json`.71표적회귀,63개hash,독립승률10개·가상승패20개,compile/link/단일 소유 기록/diff/print-only parser. 기존10/6 운영 준비 owner를 변경하지 않는다.

- [x] `[NonSamsungTargetContinuity1005] 비삼성 목표22건 시간 연결 및 청산 검증` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 다음 액션 실행, [실행계획](../proposals/non-samsung-target-continuity-research-plan-2026-10-05.md), [이전 결과](../audits/non-samsung-mechanical-exit-reconstruction-review-2026-10-05.md).
  - Acceptance:22개 원 trace·정책 고정, canonical shard/등록/수집 전환/가격 원천 대사, 시간 공백·epoch·동시각 순서 분리, 연결 입증 경로 재생 또는 미복원 사유, 봉 진단 분리, 리뷰/표적 검증/hash/link/단일 owner/diff/print-only parser.
  - Boundary: 기존 자료 격리 연구. route·순서·tick/체결 합성 금지. 삼성/보조·신규 수집·API/provider·주문·운영 정책 발행/배포·재기동 없음.
  - Result:22건/21종목.20건 단기 probe 해제,043260 해제 초와 관측 겹침·후속 감시도 목표 이전 종료,010140 지속 관측의 동시각/재초기화 결손. 연속 경로 복원0·추가 shard0.001210/007810 종전 조건부 손절을 해제 이후 경로로 정정하고 수익률 null. 봉의 trailing 시작 가능17·미도달5,44기존 봉 재생 일치.
  - Evidence: [결과 리뷰](../audits/non-samsung-target-continuity-research-review-2026-10-05.md), `tmp/non-samsung-target-continuity-20261005/{report,lease-receipts,epoch-context,validation}.json`. 재기동 전후 epoch1 혼합을 수정,55표적회귀·compile/hash/link/단일 owner/diff/print-only parser. 기존 원천 복원 가설은 종료하며 운영 적용을 주장하지 않는다.

- [x] `[NonSamsungMechanicalExit1005] 비삼성 부호 거래량·depth 강약 복원 및 현행 청산 재생` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 다음액션 실행, [실행계획](../proposals/non-samsung-mechanical-exit-reconstruction-plan-2026-10-05.md), [이전 결과](../audits/non-samsung-first-signal-exit-research-review-2026-10-05.md).
  - Acceptance: 공식 raw15·canonical producer 결속,483첫 anchor 고정, 현행 분류기 상태 복원/고정 두 폭 paired 비교, 결손·검열·UNKNOWN 분리, 리뷰/보완·표적 회귀/compile/hash/link/owner/diff/print-only parser.
  - Boundary: 기존 자료 격리 연구. 강약 복원과 전체 보유/주문/PID 재현을 구분한다. 새 수집·실계좌/API·정책 발행/배포·재기동 없음.
  - Result: 유효 체결369,630 중369,593 부호 복원,37 UNKNOWN·별도 원천 부적격10 보존.483첫 anchor 중328에서 STRONG 관측.9/29 후보028670의 관측 이벤트 CF+0.1950→+0.7052%;9/30·10/2 청산 변화0.10/2 목표22건 중20건 연결 미확정, 조건부 손절2건도20~22분 보관 관측 공백으로 운영 첫 청산/이익 반납 미입증.
  - Evidence: [결과 리뷰](../audits/non-samsung-mechanical-exit-reconstruction-review-2026-10-05.md), `tmp/non-samsung-mechanical-exit-20261005/run-v2/{report,outcome-decomposition,source-continuity-diagnostics,validation}.json`. 초기 원천/청산 이후 통계 결함2건 수정,61표적회귀·966고정 폭 경로 차이0·compile/hash/link/단일 owner/diff/print-only parser. 운영 적용은 완료 범위가 아니다.

- [x] `[NonSamsungFirstSignalExit1005] 비삼성 최초 신호 사건·현행 청산 경로 검증` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: 사용자 다음액션 실행 지시, [실행계획](../proposals/non-samsung-first-signal-exit-research-plan-2026-10-05.md), [이전 생성 결과](../audits/machine-observation-generator-contract-review-2026-10-04.md).
  - Acceptance: 신호 사건·최초 관측/실행가능 증거·반복 영향 분해, 선택 release/준비 policy와 shared trailing kernel 결속, 원 비용/호가/체결의 청산 재생 및 불완전 범위 표시, 반복 리뷰/수정·표적 회귀/compile/hash/link/owner/diff/print-only parser.
  - Boundary: 고정 후보·기계 전용·격리 가격 CF. native 승격/실제 체결·주문/청산 상태를 만들지 않는다. 운영 정책 선정/발행·배포·기동과 경제성 승인을 분리한다.
  - Result: 460관측 사건·483첫 anchor. 최초 신호 제한 후 주승률9/29 46.25→62.92%,9/30 37.04→75.00%,10/2 53.70→75.00%.10/2 후보 목표22·손절8·미도달3·미확정14. 준비된 기본 SCALP 공용 trailing의 봉 조건부 결과는 약세12/47·평균-0.7459%,강세14/47·-0.7291%; 전체 운영/실현 성과가 아니다.
  - Evidence: [결과 리뷰](../audits/non-samsung-first-signal-exit-research-review-2026-10-05.md), `tmp/non-samsung-first-signal-exit-20261005/{report,archive-exit-report,validation}.json`. 보관 체결·bid 및 epoch/시각 순서 대사 완료, 실제 강약·보유/주문 상태 복원은 미완료로 표시.41표적회귀·compile·hash·link/단일 owner·diff·print-only parser. 기존10/6 운영 준비/자연 수용 완료를 주장하지 않는다.
