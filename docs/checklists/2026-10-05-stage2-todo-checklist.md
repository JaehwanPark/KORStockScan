# 2026-10-05 Stage2 To-Do Checklist

## 오늘 목적

- 완료된 기계 수용 계약·삼성 검증·저장공간 정리 증거를 보존하고, 승인된 비삼성1회 지정·적용 후 비교 구현 및 삼성 유한 추가연구를 실행하고10/6 준비를 다시 검증한다.

## 필수 규칙

- Plan Rebase §1–§8과 사용자 최신 지시를 따른다. 입력 날짜는9/29·9/30·10/2로 고정하며10/2를 새 독립 holdout으로 취급하지 않는다.
- 기계 후보 `pullback_p60_v0`를 고정한다. 성공100%/80% 보존 veto를 추가하지 않는다. 삼성전자와 보조 AI는 별도 정책/owner로 구분한다.
- 기존 실행 결과는 아래 완료 기록으로 보존한다. 최신 사용자 `계획 실행` 지시로 두 상세계획의 구현·지정 stage·통합 배포·준비 검증을 실행한다. 실제 Main 당일 기동/PID는 기존 owner가 확인한다. 관측/최초 신호/native·비용/stop·독립 날짜와 지정 근거를 구분하고 삼성 최신 absorption과 과거 veto의 owner를 혼동하지 않는다.
- 10/5 문서는 작업 시작 시 없었다. 완료된10/4 항목을 현재 OPEN으로 복제하지 않고 이번 지시의 소유 항목만 등록한다. 다음 영업일 준비의 기존10/6 소유 항목은 유지한다.

## 실행 항목

- [x] `[MachineDesignationSamsungResearchPlanning1005] 비삼성 지정 코드·삼성 추가연구 상세계획 수립` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: 사용자 코드보완 상세계획 및 삼성전자 후보 추가연구계획 요청.
  - Acceptance: 실제 지정 발행 부재·dated generation 불변·적용 후 자기비교·삼성 전체 parent hash 의존성 대사.1회 지정/후속 양방향 비교·producer/consumer·회귀·장전 준비 및 삼성 원천/유한 가설/연구 목적/이후 인계 계획, 문서 리뷰·보완·링크·단일 owner·print-only parser.
  - Result: [비삼성 상세계획](../proposals/non-samsung-designated-policy-and-postapply-comparison-implementation-plan-2026-10-05.md), [삼성 추가연구계획](../proposals/samsung-absorption-differential-and-path-research-plan-2026-10-05.md) 작성. 지정과 독립검증 상태 분리, B0/C0/I_t/P_t 분리, 삼성 동등성 및 최대7정책 유한 비교를 설계했다. 두 계획의 새 수용/연구 지표는 제안이며 현재 동작으로 표시하지 않는다.
  - Boundary: 문서만 수정. 코드·지정 발행·추가 연구 재계산·기동·원천 수집·10/6 준비 변경 없음. 보호 hash·문서 검증은 `tmp/designated-machine-and-samsung-planning-20261005/validation.json`에 기록한다.

- [ ] `[NonSamsungDesignatedPolicyImplementation1005] 비삼성 고정 정책1회 지정·적용 후 비교 구현` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: MainEntry`)
  - Source: [지정·장후 비교 상세계획](../proposals/non-samsung-designated-policy-and-postapply-comparison-implementation-plan-2026-10-05.md).
  - Acceptance: C0~C7의 지정 schema/발행/activation·기존 dated supersession/CAS·원 세대 보관·B0/C0/I_t/P_t 구분·양방향 비교·삼성 component 동등성·summary/strict/prepared 연결, 정상/거부/재실행/부분실패 회귀·리뷰/수정/재리뷰. 구현·준비와 실제 당일 PID 각각 증빙.
  - Boundary: 사용자 계획 실행으로 승인된 구현·지정 발행·통합 배포·정확일자 준비 owner. 대상10/6·비삼성 KRX 정규장 `pullback_p60_v0` 고정, 독립 검증 미완료 유지. 삼성/보조/타 family·계좌/주문/수량/손절/custody guard 권한 확대 없음.
  - Stop: 구현/준비 결과 또는 날짜 종료·parent 충돌·source 결함의 구체적 사유 확정. target 날짜 자동 연장 없음. 장후 비교는 `NonSamsungMachineForwardComparison1006`, 실제 Main 소비는 `DirectFamilyPreopenPolicyHandoff`에 인계.

- [ ] `[SamsungAbsorptionDifferentialResearch1005] 삼성 흡수 후보 원천 차이·가격경로 유한 추가연구` (`Due: 2026-10-05`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: Research`)
  - Source: [삼성 추가연구계획](../proposals/samsung-absorption-differential-and-path-research-plan-2026-10-05.md).
  - Acceptance: R0중복 가설/원천 census→R1성공·손절·완전미도달/검열 차이→R2정책 전체/공통 사건→R3최대5변형과2대조 정책→R4권고/개선 없음/식별 불가·동결 인계. raw 시점/epoch/cost/stop·source 결손·metric/날짜 지원·표적 회귀/재리뷰 검증.
  - Boundary: 기존 원천만 소비하는 승인된 오프라인 연구. 전체519/fixed-watch206 구분, 삼성 양수 가격경로 지표는 신규 연구 제안이며 현재 운영 승률 계약 변경 아님. API·수집 확대·보조 AI 혼합·Widget 실현 수익 이식·삼성 정책 지정/발행/배포 없음.
  - Stop: 중복/원천 부재 가설을 닫고 최대7정책에서 후보1개 권고/개선 없음/판단 불가 확정. 임계값·종료기간 무한 추가 금지. 이후 자연 검증은 기존 `SamsungFrozenCandidateValidation1006` 소유.

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
  - 최신 후보 인계 보완: 기존 frozen의2개는 foreign/program veto이며 absorption 후보가 아니다. [10/5 계획 S3](../proposals/machine-admission-acceptance-remediation-and-samsung-research-plan-2026-10-05.md)에 따라 `SamsungAbsorptionOutcomeReview1005`가 준비한 최신 `absorption_p60_v10`의 별도 frozen/adapter를 이 owner에서 추가 검증한다. 기존 원 계약을 덮어쓰지 않으며 adapter 준비 여부를 먼저 확인한다. 준비되지 않았으면 `latest_candidate_adapter_not_ready`, 원천 부재는 `waiting_new_source_date`를 구분한다. 과거2후보 검증만으로 최신 후보 완료를 선언하지 않는다.
  - 최신 후보 준비 완료: `tmp/admission-remediation-execution-20261005/replay-v2/samsung-frozen.json`, `samsung-forward-readiness.json`과 새 `samsung_absorption_acceptance_research` CLI를 사용한다. after10/5 원 projection·완료 가격 및 원 raw exact receipt를 검증한다. 현재 두 자동 생산 경로 부재로 waiting이며 실제 검증/선정은 미실행. 기존 두 veto의4경로 계약과 구별한다.
  - 추가 계획 인계: `SamsungAbsorptionDifferentialResearch1005`가 실제 권고한 후보가 있을 때 별도 frozen을 추가한다. 비삼성 지정으로 전체 parent/kernel이 바뀌면 허용 diff의 삼성 component 동등성/migration receipt를 먼저 검증한다. 기존 frozen bytes는 변경하지 않으며 실제 삼성 동작 변화는 재계획한다.
  - 실행 인계: 최신 원흡수 migration 및 `tmp/samsung-absorption-differential-research-20261005/final/frozen-candidate.json`의 H2를 구분한다. H2는 `samsung_absorption_differential_research --forward-frozen <H2> --base-frozen tmp/admission-remediation-execution-20261005/replay-v2/samsung-frozen.json --date 2026-10-06 --root /home/ubuntu/KORStockScan --output <new-output>`로 검증한다. 둘 다 현재 waiting. 과거 veto2개는 원 테스트 파일 c165a509 bytes 부재로 `blocked_historical_kernel_source_gap`; 기존 frozen을 현재 hash로 덮지 않고 원본 복구 또는 별도 재동결 검토 후 소비한다.
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
