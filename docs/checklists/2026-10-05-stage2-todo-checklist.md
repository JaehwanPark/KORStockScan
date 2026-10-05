# 2026-10-05 Stage2 To-Do Checklist

## 오늘 목적

- 비삼성 고정 후보의 연구 결론을 보존하고,10/6 정책 적용·기동 및 디스크 정리 최종계획과 장후 생성 경로를 확정한다.

## 필수 규칙

- Plan Rebase §1–§8과 사용자 최신 지시를 따른다. 입력 날짜는9/29·9/30·10/2로 고정하며10/2를 새 독립 holdout으로 취급하지 않는다.
- 기계 후보 `pullback_p60_v0`를 고정한다. 성공100%/80% 보존 veto를 추가하지 않는다. 삼성전자와 보조 AI는 별도 정책/owner로 구분한다.
- 최신 요청은 두 계획의 실행과 코드리뷰·수정보완 반복이다. 후보 공용 판정/schema/생성·발행 연결, 현재 준비 결손 복구, 검증된 commit/release/정확일자 준비 및 참조·복원 검증을 통과한 정리를 실행한다. 기존 정책 선정 자격·custody/격리·hard guard를 유지한다.10/6 당일 activation/PID/자연 수용은 그 시간 창에 확인하며 오늘 증거로 합성하지 않는다.
- 10/5 문서는 작업 시작 시 없었다. 완료된10/4 항목을 현재 OPEN으로 복제하지 않고 이번 지시의 소유 항목만 등록한다. 다음 영업일 준비의 기존10/6 소유 항목은 유지한다.

## 실행 항목

- [x] `[NextSessionPolicyStoragePlan1005] 다음 영업일 정책·기동 및 디스크 정리계획 확정` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자10/6 최종 적용계획·디스크 정리계획·장후 기계 생성 설명 요청.
  - Acceptance: 실제 selector/장후 호출/준비 검증/PID·policy scope·디스크 상태 확인, 선행 결손/구현·선정·적용·기동·장후 단계/owner·정리 보호/중단 기준 및 현행/개선 후 생성 방식을 문서화. 문서 리뷰/수정/재리뷰·link/owner/diff/print-only parser.
  - Result: 선택9c0c0632의10/6 준비 검증 FAIL, collector `history_generation_changed`; Episode10/5 preflight source-quality hash 불일치 확인. 비삼성 pullback은 운영 연결 전이며 현행 자동 생성은 winrate VWAP veto 경로. 가용약16.95GiB·사용89%, 참조된 release/고유 연구 원천을 보호하는 정리 순서 확정. 현재 정상 기동/후보 적용 완료를 주장하지 않는다.
  - Evidence: [최종 적용·기동 계획](../proposals/next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md), [디스크 정리계획](../proposals/runtime-and-research-storage-cleanup-plan-2026-10-05.md), [검증 기록](../../tmp/next-session-policy-storage-plan-20261005/validation.json). parser 누락된10/4 미래 OPEN3건을동일ID/수용/이력으로이관해현재단일owner검증. 계획 작성이며 구현/배포/기동/삭제 미실행.

- [ ] `[MachinePolicyCutoverPreparation1005] 비삼성 후보 운영 연결·현재 준비 결손 복구 패키지` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [최종계획 P0~P4](../proposals/next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md), [고정 후보 구현계획](../proposals/non-samsung-pullback-candidate-implementation-plan-2026-10-05.md).
  - Acceptance: collector history 변동 대사와 영향 단계 복구, Episode profile별 hash 결손 분류, 공용 evaluator/schema/scope/publisher/loader/장후 registry 연결·발행 owner 단일화, 현재 parent/운영 자격 대사, 리뷰/수정/표적회귀/재리뷰. 실행 권한 안에서 불변 release·정확한 날짜 정책·동일 세대 strict/controller/prepared 수용 또는 후보 보류의 구체적 사유 확정.
  - Boundary: 사용자 두 계획 실행 지시로 준비 구현·결손 복구·검증된 배포를 실행한다. 연구 권고를 운영 자격으로 바꾸거나 probe를 native로 합성하지 않는다. 기존 winner retention veto 복구 금지. 삼성/보조/다른 session·custody/격리/guard 유지.10/6 실제 PID 수용은 기존 `DirectFamilyPreopenPolicyHandoff`/`WidgetEpisodeNextSessionStartup1006` 소유이며 중복 등록하지 않는다.
  - Intake: `tmp/policy-cutover-and-storage-execution-20261005/intake.json`. 작업본HEAD99cf22c1·선택9c0c0632·dirty patch와7개수정예정파일원bytes를보관했고63개연구frozen hash를검증했다. 역사원본과새공용kernel을별도세대로보존한다.
  - Stop:10/6 07:20 적용/적격 incumbent 승계/준비실패를 구분하여 인계. 새로운 자료 없이 과거 연구를 재개하지 않는다.

- [ ] `[VerifiedStorageCleanup1005] 참조·복구 검증 기반 운영 및 연구 저장공간 정리` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [디스크 정리계획](../proposals/runtime-and-research-storage-cleanup-plan-2026-10-05.md).
  - Acceptance: 최신 selector/previous/service/PID/FD/고유 Git·연구 참조 폐쇄 보호 목록, 파일별 dry-run manifest·복원 증거·실제 회수량 및 사후 보호 참조 검증. 검증된 후보 소진 또는 필요 여유 확보 시 종료.
  - Boundary: 사용자 정리계획 실행 지시 범위에서 검증된 대상만 정리한다. 고유 원천/정책/연구63파일 및 간접 참조·source-quality·custody 보호. 서비스/주문/패키지 변경 없음.25GiB는 관리 제안이며 삭제 확대·매매 중단 임계치가 아니다.

- [ ] `[NonSamsungMachineForwardComparison1006] 비삼성 고정 기계 후보의10/6 이후 날짜 비교` (`Due: 2026-10-06`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~23:59`, `Track: MainEntry`)
  - Source: [최종계획 §4](../proposals/next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md), `NonSamsungFinalPolicyDecision1005`의 종료된 고정 후보·부모·원천 계약.
  - Acceptance: 운영 연결 여부를 먼저 확인하고10/6 ENTER/BLOCK/RECHECK 관측을 삼성 제외·venue/session 분리하여 고정 후보와 부모 비교.10분 미도달은 이후 최대60분 경로로 보조 평가하되 순서/공백/검열 분리. 원천·군집/native 분모·주승률/지원조정·coverage/결손 민감도, source10/6→effective10/7 선정/승계/발행 여부를 정확히 기록. 당일 조건을 튜닝하면 동일 자료를 독립 검증으로 쓰지 않는다.
  - Boundary: 성공100%/80% 보존 탈락 조건 없음. 관측 승률/실제 경제성 분리. 자동화 미연결이면 별도 관측 비교와 자동 발행 미실행을 표시하며, 후속 실행 권한을 이 계획에서 새로 만들지 않는다. 운영 원천 경제성은 기존 `DirectFamilySourceRepairMainMechanisticEntry` 소유.
  - Stop: 고정 후보의 날짜별 비교·선정/승계 사유를 확정하면 종료. 원천이 없으면 `not_observed`, 계약 실패면 소유자·closure test를 명시하고 동일 입력 무한 재실행 금지.

- [ ] `[WidgetEpisodeNextSessionStartup1006] Widget/Episode 다음거래일 정책·preflight·PID 수용` (`Due: 2026-10-06`, `Slot: INTRADAY`, `TimeWindow: 07:32~20:00`, `Track: RuntimeStability`)
  - Source: [재점검리뷰§4–§5](../audits/source-repair-repeat-review-and-next-session-readiness-2026-10-04.md), 사용자다음영업일정상가동재점검지시.
  - Acceptance: Widget07:32정책반영/07:58기동경로와현재PID의10/6reload/행동policy hash·custody/source receipt를대조한다. 기존10/3 startup은당일reload증거로사용하지 않는다. Episode의10/4 역사 기준58격리제외profile을 출발 목록으로 하여 현재전체profile의당일applied/authority·research/Main/token preflight·실제unit/PID·자연원천을profile별로대조하고3격리를별도표시한다. 기존Main `DirectFamilyPreopenPolicyHandoff`·Episode sequence owner와증거를연결하되코드/준비/기동/주문/경제성을구분한다.
  - Boundary: read-only검증과결과기록. 실제가동/기동부작용이있는preflight/정책쓰기/재기동/API/token조회/주문/격리해제는자동실행하지 않는다. source없음은not_observed,미도래는not_yet_due이며source gap의0치환없음.
  - 이력:10/4 준비PASS.10/5 현재 Main prepared 재검증은collector history 변경으로FAIL이며, Episode cj_cgv_morning preflight의candidate_source_quality_hash_mismatch를확인했다. 당일profile별source-blocked/경제성격리/disabled/eligible을재분류한다. 기존독립e6d4d3b9 release/service pin을보존하고10/6 실제소비는별도수용한다.
  - 이관:10/5 print-only parser에서10/4 소유 항목이 제외됨을 확인하여 현재 문서로 이동. ID·기존 수용/권한·준비 이력 보존; 실행 완료 처리 아님.
  - 후속계획: [최종 적용·기동 계획](../proposals/next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md). 이전58/3 수치를현재가동PASS로사용하지 않는다.

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
