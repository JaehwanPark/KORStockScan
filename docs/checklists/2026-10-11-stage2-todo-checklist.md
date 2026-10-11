# 2026-10-11 Stage2 TODO

## 오늘 목표

- 완료된 수량 배포 인계를 보존하고 의미적 감시기·Main 손절 구현과 반복 리뷰를 진행한다.

## 오늘 강제 규칙

- 원천 결손과 실현 0원을 구분하고 Main/manual 수탁·주문·수량·freshness·hard safety를 보존한다.
- episode/widget 퇴역 실행을 복원하지 않으며 공유 미커밋·원 EOD·현재 수량 정책을 보존하며, 봉인된10/12 인계는 승인된 native CAS successor로만 갱신한다.
- 기존 trailing/delay 완료 기록과 수량 작업을 구분하고 기능·성능 gate 후 Q8 승인 범위를 대사한다.
- Project/Calendar 동기화는 실행하지 않고 print-only parser로 현행 owner를 검증한다.

## 실행 항목

- [x] `[InitialQuantityProducerConsumerRepair1010] 최초 매수 수량 런타임·장후 생산자/소비자 결손 보완` (`Due: 2026-10-11`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - 재개 10/11: 새 코드리뷰에서 정확 시도별 capture queue/clock 결손의 후보 소비 누락과 캐시 읽기 상한/전이 reader 해시 결손을 확인했다. 이전 승인·완료 근거를 보존하고 이 신규 결함만 보완·재검증 후 successor 배포/10/12 PREOPEN을 갱신한다.
  - Source: [상세 보완계획 Q0–Q8](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md), [최초 수량 계획의 사용자 결정](../proposals/scalping-initial-entry-quantity-type-policy-closed-loop-plan-2026-09-26.md).
  - 현재 범위: 사용자의 계획 실행·반복 코드리뷰 요청에 따라 Q0–Q7 구현과 검증을 진행한다. 운영 복원·정식 배포/장후 인계는 기능·성능 gate 종료 후 Q8의 기존 승인 범위를 대사한다. 10/10에서 동일 stable ID·수용을 이전했으며 현재 owner는 이 항목 하나다.
  - 수용: 비용 NULL/누적 실제 비용 세대, 런타임/재생의 probe·수량·가격 의미·시간표와 주문 시작 기준 수집, epoch wire/보수적 부분 체결, forward 경계·경제/진단 모수·표본/PID 분리, 행별 결손 격리, 결합 후보 train 확정 후 독립 holdout, 버전 reader·동일 날짜 successor·정규 발행/감시 인계를 교차 회귀로 닫는다.
  - 실행 순서: Q0 실패 fixture·성능 기준 고정→Q1 비용 원천/저장→Q2·Q3 공통 실행/체결→Q4·Q5 창·선정→Q6·Q7 인계/전수 결과·성능→Q8 기존 승인 범위의 배포·PREOPEN/자연 수용. Q6 구 평가 reader/신규 세대 참조는 Q0 뒤에 선행 준비하고 각 단계에서 성능을 대사한다. 단계별 구현→리뷰→보완→재검증을 반복한다.
  - 성능 필수 수용: IQ-P1–P8의 장중 결정/기록/취소 비악화, 동일 전수·후보 cold 예산 준수, warm/비용 정정·증분의 중복 작업 및 wall/CPU 절감, 검증/PREOPEN 기한, 수량 wrapper/직접 CLI의 공통 admission·합산 RSS/디스크 예산을 입증한다. 기능 수리 기준본과 최적화본의 결과 동등성을 먼저 검증하며 빠른 0건 실행·일부 microbenchmark로 전체 성능을 대신하지 않는다.
  - 경계: 유효 최초 정책에 우월성·자연소비를 새 선행조건으로 붙이지 않는다. T≤1200초·실제 주문 시작 기준·probe 포함 순차 구간과 취소/확인 시간, Main/manual 수탁·전체 퇴역 경계를 보존한다. 수량 native 수리와 SemanticMonitorLatestReleaseRepair1010의 알림/복구 소유를 구분한다.
  - 종료: 미해결 구현 finding 0·실자료/실제 wire·ORM 연결 회귀·단독/결합 성능과 승인된 정식 인계 근거를 기록한다. 과거 회복 불가·표본 0·미래 PID/자연 terminal은 별도 상태이며 계획/코드/배포/경제성을 혼합하지 않는다. 봉인된 10/12 checklist/준비는 구현 중 보존하며 Q8 정식 successor 이외의 경로로 변경하지 않는다.
  - 계획 검증: 7개 결함·PID 진단의 단계/소유자/종료 조건과 6개 실행 지시문을 작성했다. 재리뷰에서 IQ-R1–R8의 수집 시계·누적 비용·분모/격리·과거 reader·stage 승계·공통 자원 연결을 보완하고 IQ-P1–P8 성능 보호/개선 및 Q0 선행 기준을 추가했다. 관련 4문서 로컬 링크 109개 결손 0, 공백·diff·print-only parser PASS, parsed 항목 25개 중 현행 수량 owner 1건을 확인했다. 문서 수용이며 구현·성능 실측·배포는 이 기록으로 완료 처리하지 않는다.

  - 착수: 선택 릴리스 main-trailing-delay-structural-20261010-v1·현재 수량 pointer·공통 미커밋 bytes를 고정했고 기존 영향 회귀 122 passed를 확인했다. Q1 NULL/provenance·Q2 공통 leg·Q3 typed epoch·Q5 train-first·Q6 v1 reader/세대 stage 및 shared admission을 구현 중이다. 전체 수용은 아직 OPEN이다.
  - 종료 10/11: [반복 리뷰·실측·운영 근거](../audits/initial-quantity-producer-consumer-implementation-review-2026-10-11.md). Q0–Q7 코드 결함을 보완했고 영향 회귀659·실제 제출 공유 분기599·bounded-source 최종362·불변 릴리스233 passed를 확인했다(묶음 간 중복 포함). 동일 전수240조합 반복에서 warm/cost-only CPU·wall 약33% 절감, cold fsync wall 증가·증분 I/O 경합은 공개했다.
  - 승인된 Q8: `initial-quantity-repair-20261011-v1` / commit `a0aec8e1608e810c4dae73f2b39bcf9439afd9f7` 선택. 첫 소비 검증 실패는 전체 CAS rollback과 구 PREOPEN PASS를 확인한 뒤 native 트레일링 코드 결속을 재생성해 보완했다. 초기수량 successor·제출지연→summary/checklist→strict/controller→finalization이 종료됐다. source10/8→target10/12 PREOPEN 준비는 전체 계약 PASS다. EOD·기계/보조 정책·현재 수량 parent를 보존했다.
  - 잔여 경계: 적격 경제 표본0·회복 불가 비용/큰 native projection 결손은 제외·원 원장 보존이다. 새 우월 정책·역사 DB 복원·실제 PID/자연 주문·경제성 개선은 주장하지 않는다. 10/12 기존 OPEN `DirectFamilyPreopenPolicyHandoff`의 별도 초기수량 수용 항목으로 실제 예약 기동·PID와 자연 수탁/terminal을 인계했다.
  - 추가 재리뷰 종료 10/11 08:52: queue/clock 결손 후보 소비·시계 유효성·캐시 bounded read/reader 결속·terminal 직렬화/재접수 6개 결함을 보완했다. 영향402·인계307·최종 신규51·불변 릴리스146 passed(중복 포함), 고정 source 성능24회 결과 동등·기존 예산을 확인했다. `initial-quantity-repair-20261011-v2` / `818e2f85c216336c9b927d9ae49aad35f0649af7`를 선택하고 `initial_quantity_rereview_20261011_v1` CAS verified, native finalization08:52:58 DONE, 10/12 current_full_contract PASS·marker issues0·cron8개/예약 경로 PASS를 확인했다. 원 EOD/수량 parent/기계·보조 정책·지연/트레일링 값은 보존했다. 현재 Main은 Sunday 정지이며 실제 인증/PID·자연 종결은 기존 10/12 owner가 확인한다.

- [ ] `[SemanticMonitorLatestReleaseRepair1010] 의미적 감시기 최신 릴리스 연계 보완` (`Due: 2026-10-11`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [상세 보완계획 M0–M8](../proposals/semantic-monitor-latest-release-followup-repair-plan-2026-10-10.md).
  - 현재 범위: 10/11 후속 요청으로 코드 재리뷰·결함 보완·배포와 10/12 정상기동 준비 점검을 승인받았다. 영향받은 native 장후 인계와 PREOPEN을 새 릴리스 기준으로 검증한다. Telegram 실발송과 휴일 봇 시험 기동은 하지 않는다. current parsed owner는 이 항목 하나다.
  - 수용: 청산/초기수량 구조화 알림, 정책 등록·승계의 정확 복구, 현행 담당 작업 연결, 상태별 producer→notifier→recovery 교차 회귀를 닫는다. 원천·lifecycle·경제성 및 역사적 미복구를 분리하고 state 삭제·가짜 종결·추가 매매 gate를 금지한다.
  - 연계: 제출 지연의 선택 due·원 PASS/claim/deadline, 전수 trailing/delay 장후 source/shard/global census·정책/준비/PID를 실제 설치 범위로 검사한다. 손절 정책화는 해당 owner 구현 후 연결하며 episode/widget 전체 자동 퇴역·수동 수탁을 보존한다. 기존 trailing/delay 승인과 자연 수용 owner를 대체하지 않는다.
  - 종료: M0 기준 고정→F1–F4 수리→영향 기능/성능 검증→반복 리뷰 후 승인된 배포 인계. 전체 연계 잔여·10/12 미래 자연 수용은 별도 표시하고 봉인된 체크리스트/준비는 승인된 native CAS successor로 갱신한다.
  - 계획 검증: 생산자/마지막 소비자 10경로·M0–M8·알림/복구 상태·owner 이전·성능/배포 수용을 재리뷰했다. 보조 AI의 기존 10/12 owner와 기계 owner 부재를 구분하고 유효 ancestor pin을 보존하도록 보완했다. 로컬 링크 23개 결손 0, 공백 검사·print-only parser PASS, 현재 owner 1건. 코드/운영 수리는 미착수다.
  - 계획 재리뷰 보완: R1–R6로 findings 공백과 비교 source gap 분리, 기한 후 관측 불능, 비기계 stage 복구·state 128건 상한, 필요 incident에만 current owner 요구, 읽기 세대·결손 identity를 구체화했다. 즉시 수리 A와 기능 연계 B의 성능/배포 gate를 분리해 전체 W4·미래 표본이 알림 수리를 막지 않도록 했으며, 기존 봉인·권한·퇴역 경계를 유지한다.

  - 실행 10/11: 사용자가 두 계획의 실행·반복 코드리뷰를 요청했다. 위 계획 수립 당시 권한 문구는 역사 기록이며 현재 범위는 구현·격리 회귀·성능·반복 보완이다. 현재 선택 릴리스·10/12 봉인 준비·operator 원본은 보존한다.

  - 구현 10/11: [구현·리뷰 근거](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md). 단독 stage 알림·native 복구·현재 owner·부분 batch 재시도·128건 상태 한도·선택 due 및 stop/수량 ancestor 연결을 보완했다. 통합2292 passed 뒤 구 owner 기대값1건을 수정했고 영향1088 passed, 최종 원천 목록/native 연결264 passed(묶음 중복 포함). A 격리 수리와 B/운영 자연 수용을 분리해 OPEN을 유지한다.

  - 후속 승인 배포 10/11: [리뷰 §7–§8](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md). 급락 경로의 새 원장 writer 지연을 보완하고 영향1057·불변 release187 passed(중복 포함), 격리3부하×3회 비교15% 예산을 검증했다. `main-stop-semantic-20261011-v1` / `91edc6284` 배포, source10/8 native finalization11:33:05 DONE·target10/12 PREOPEN 전체 계약PASS·예약경로PASS. 실제 PID/자연 청산은10/12 기존 `DirectFamilyPreopenPolicyHandoff`가 수용하며 전체 Main/동시 연구 성능·신규 보호선·vote 경제변경 잔여를 이번 배포로 닫지 않는다.

- [ ] `[MainStopLossRetirementRuntimeTuning1010] Main 손절 퇴역 제거·런타임 보완·정책화 및 장후 튜닝 후속 구현` (`Due: 2026-10-11`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [손절 구현·보완 및 연구계획 SL0–SL8](../proposals/main-stop-loss-retirement-runtime-policy-and-postclose-tuning-plan-2026-10-10.md).
  - 현재 범위: 10/11 후속 요청으로 손절 퇴역·런타임/장후 연결 재리뷰·결함 보완·배포와 10/12 정상기동 준비 점검을 승인받았다. 손절값은 현행 계승하며 변경 경제정책·새 보호선 생성은 별도 잔여 수용이다. 영향받은 native 장후 인계와 PREOPEN은 하나의 CAS 전환으로 갱신한다. current parsed owner는 이 항목 하나다.
  - 수용: holding score 손절·기타 OFF 전용 코드·whipsaw 실행/관측/추천/정책 의존을 전수 제거하고, fast/normal 수동 인계·role별 기준·quote/clock·pin/claim 결함을 보완한다. 기본 False지만 관측 계산 ON인 기능을 실매도와 구분하고 Main/manual 수탁·hard/protect/emergency 안전을 보존한다.
  - 정책/연구: 소프트 손절 기준선·60초 기본 유예·보호 트레일링 확인 파라미터를 현행값 계승 정책으로 구현한다. runtime/replay 공통 판단·forward train/holdout·실제 비용/검열·bounded 후보·부모 유지·exact key 승계·정식 장후/selector/PREOPEN/pin을 연결한다. whipsaw 추가 유예를 재도입하거나 hard safety·operator veto의 자동 변경 권한을 만들지 않는다.
  - 생성/성능: 시간 경과로 해소되지 않는 producer 부재·필드 누락·도달 불가능 경로·순환 선행조건·전역 표본 gate·schema/target 불일치를 SL0에서 대사하고 SL5에서 실제 producer→loader 성공/부분 결손/정정/재개 시험으로 닫는다. 정책 생성·경제값 변경·실제 소비를 구분하며 capture부터 발행/strict/PREOPEN/pin까지 구간별·전체 성능, 증분 재사용·합산 자원/기한을 검증한다.
  - 누락 재점검: 계획 §5.1의 17개 임계치 묶음·§5.2 실효 우선권·§6.5 생산/소비 이행표를 따른다. vote replay의 경제값 null/기본값 전용 publisher, preset·fast 차이, 선행 crossing/30초 원천, defensive unfilled no-op 잔여와 관측 ON 오해를 SL-F10–SL-F15로 반영한다. 새 stop stage/발행/strict/bootstrap/lookup이 현재 설치됐다고 간주하지 않는다.
  - 계획 검증: 후속 재점검의 임계치 17개 묶음·로컬 링크 62개 결손 0·공백/문서 재리뷰·diff·print-only parser PASS, 손절 현재 owner 1건. 계획 보완 완료이며 손절 코드 구현·정책 발행·성능 실측은 미착수다.
  - 종료: 삭제·consumer migration·런타임 회귀·단독/결합 성능·반복 리뷰의 미해결 구현 finding 0. 초기 부모 계승에 추가 경제 gate를 붙이지 않으며 정식 인계·실제 PID·자연 terminal/경제성은 각각 증거를 기록한다. 기존 trailing/delay owner의 승인·완료 범위를 소급 변경하지 않는다.

  - 실행 10/11: 사용자가 두 계획의 실행·반복 코드리뷰를 요청했다. 위 계획 수립 당시 권한 문구는 역사 기록이며 현재 범위는 구현·격리 회귀·성능·반복 보완이다. 현재 선택 릴리스·10/12 봉인 준비·operator 원본은 보존한다.

  - 구현 10/11: [구현·리뷰/성능 근거](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md). 퇴역 stop/score/whipsaw·프롬프트/schema 정리, fast/normal 수동 인계·시계/pin·shared queue, 7축/9cell 정책·원장 참조 분할/증분 재생·native stage/strict/bootstrap/PID receipt를 구현했다. fixture의 grace60→0은 loader/pin까지 검증했으며 운영값은 변경하지 않았다. 최종 안전/handler1000·원천 목록/native264 passed(중복 포함), Python77개 compile·shell/diff·print-only 검증을 마쳤다. later base/late 파일 발견은 handoff 무효화·재발행 전수 census에 반영한다. SL-F8은 Main 보호선 생성 provenance source-gap, SL-F11은 원 vote family baseline-only이며 값 변경 selector 완료로 표시하지 않는다. §7 전체 Main/동시 heavy-job 성능과 운영/자연 수용은 OPEN이다. 기존10/12 봉인 문서·selector·수량 pointer·Rebase의 작업 전 해시를 보존했다.

  - 후속 승인 배포 10/11: [리뷰 §7–§8](../audits/semantic-monitor-main-stop-implementation-review-2026-10-11.md). 급락 경로의 새 원장 writer 지연을 보완하고 영향1057·불변 release187 passed(중복 포함), 격리3부하×3회 비교15% 예산을 검증했다. `main-stop-semantic-20261011-v1` / `91edc6284` 배포, source10/8 native finalization11:33:05 DONE·target10/12 PREOPEN 전체 계약PASS·예약경로PASS. 실제 PID/자연 청산은10/12 기존 `DirectFamilyPreopenPolicyHandoff`가 수용하며 전체 Main/동시 연구 성능·신규 보호선·vote 경제변경 잔여를 이번 배포로 닫지 않는다.
