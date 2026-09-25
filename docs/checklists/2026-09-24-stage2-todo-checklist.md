# 2026-09-24 Stage2 To-Do Checklist

## 오늘 목적

- 9/23 원천일의 실패한 장후 chain을 영향 stage 복구와 전체 결과 의미 대사로 완결한다.
- 9/28 적용 정책의 검증된 후보 또는 incumbent carry와 다음 장전 준비 상태를 분리해 확인한다.

## 오늘 강제 규칙

- [전체 진단·복구 계획](../audit-reports/2026-09-24-postclose-whole-result-diagnosis-and-recovery-plan.md)의 원천일·세대·분모·비용·직접 소비 경계를 따른다. 기존 보유·청산, 위젯·에피소드, main·manual 소유권과 hard safety를 보존한다.
- `source_gap`·미성숙·격리·진단 전용 결과를 경제성 0 또는 승격으로 치환하지 않는다. 선택된 release, 설치 unit, 실제 PID, 다음 장전 소비와 자연 손익은 별도다.
- 이미 유효한 동일 hash stage는 재사용하고, 바뀐 producer부터 마지막 consumer까지만 복구한다. 봇 재기동·실주문·수동 threshold/provider/lock 변경은 이 checklist의 권한이 아니다.

## 실행 항목

- [x] `[PostcloseFinalizerControllerTerminalReceipt] 9/23 장후 최신 terminal·전체 결과·최종화 종결` (`Due: 2026-09-24`, `Slot: POSTCLOSE_RECOVERY`, `TimeWindow: 07:00~23:20`, `Track: RuntimeStability`)
  - Source: [전체 진단·복구 계획](../audit-reports/2026-09-24-postclose-whole-result-diagnosis-and-recovery-plan.md), [9/23 원 owner](2026-09-23-stage2-todo-checklist.md).
  - 이관된 완료 기준: exact-date main 및 설치된 widget/machine predecessor가 성공한 뒤 controller canonical/attempt 영수증이 이번 finalizer 실행 이후 생성되고 byte-identical이며, `status=done`, `whole_native_chain_done_claimed=true`, `require_independent_producers=true`, strict verifier `pass`임을 확인한다. Runtime summary와 checklist는 owner stage terminal 및 stale downstream 갱신 뒤 생성하고, blocking summary handoff 다음에 strict verifier를 실행한다. 정책 갱신으로 main auxiliary prerequisite가 stale이면 해당 owner를 다시 계산한다. Main machine 후보 정합성은 `entry_strategy_policy` 선택 결과와 `mechanistic_entry_runtime_policy`의 동일 scope activation hash로 비교한다. Immutable release 간 성공 stage 재사용은 동일 stage 코드와 artifact·input·prerequisite hash를 검증한다. 9/28 자동 블록은 최신 DirectFamily task projection과 일치하고 무관한 수동 항목은 보존한다. 최종 cleanup·detector terminal까지 확인한다.
  - 이번 복구 기준: 장후 전용 unit의 실제 immutable 실행 경로와 code hash, 15개 활성 최신 영수증 및 각 결과의 원천·제외·비용·정책·직접 소비를 기록한다. `machine_attribution`을 먼저 terminal로 닫은 뒤 `machine_timing`·`market_weakness`·`legacy_policy_approval`을 검사한다. 최신 full strict `--require-summary-handoff`를 통과시키고 `postclose_all_active_stages_complete`와 `next_session_policy_ready`를 따로 기록한다. 유효한 source gap/incumbent carry는 그대로 표시하며 이전 `summary_verified`·오래된 report로 완료를 합성하지 않는다.
  - 권한 이력: 9/23 checklist의 특정 detector 결함에 대해 검증된 main release 반영을 위한 정상 main bot 재기동 승인만 유지한다. 다른 bot/widget 재기동·주문·threshold/provider/정책 payload·hard safety 변경 권한으로 확대하지 않는다.
  - 완료 증거: 15개 활성 최신 stage 영수증 유효, strict 08:14:43 `pass`, controller 08:14:47 `done`, 설치 owned-log finalizer/cleanup/detector 08:16:18 `[DONE]`, 마지막 detector 08:16:31 `warning`·실패 0. 9/28 bootstrap verify `pass`, `postclose_all_active_stages_complete=true`, `next_session_policy_ready=true`; Main·episode loader 유효/위젯 관측 전용 97·live 0. 매매 release/PID는 별도이며 9/28 실제 소비는 [다음 장전 task](2026-09-28-stage2-todo-checklist.md)에서 확인한다.

- [x] `[HoldingExitPositionOutcomeLineageClosure] 9/23 완료 포지션 청산·비용·후행관측 원천 연결` (`Due: 2026-09-24`, `Slot: POSTCLOSE_RECOVERY`, `TimeWindow: 07:00~23:20`, `Track: RuntimeStability`)
  - Source: [보유·청산 원 owner](../proposals/holding-exit-position-outcome-runtime-threshold-lineage-implementation-plan-2026-09-23.md), [9/23 수용 기준](2026-09-23-stage2-todo-checklist.md).
  - 완료 기준: 새 `trade_review`의 당일 `sell_completed` 전량 ID·수량·원천 날짜를 DB terminal과 대사하고 `holding_exit_observation`의 비용 확정/결손·명시적 `exit_signal`/추정·유효 임계치/AI/flow 실제 개입·정확한 fill time·1/3/5/10분 후행창 품질을 포지션별로 확인한다. 직접 체결 6건의 비용 후 부분합 -4,621원과 잔고대사 2건의 모델 +5,900원을 분리한다. 재구성할 수 없는 원천은 격리하고 전체 exact-cost 및 paired/holdout EV는 null로 유지한다. 영향 장후 산출물 hash/strict terminal, 선택 release/PID 소비와 신규 자연 표본을 별도로 확인한다. 추정 규칙·partial window를 실제 개입/완전 관측으로 승격하지 않는다.
  - 9/24 진단·격리 완료: 완료 8건의 event ID·원천일을 대사했고 직접체결 6건은 수량 1/1·정확 비용, 잔고대사 2건은 정확 매도 체결·비용 없음으로 구분했다. 사후 6건의 1/3/5/10분 bar는 있으나 전부 `partial_window`, 2건은 정확 체결시각 결손이다. exit rule 8건 전부 추정, 유효 threshold/flow 개입 0, 전체 비용 후 EV null. 복원 불가 원천과 9/28 신규 자연 표본/PID 확인의 미완료 수용 조건은 [동일 ID의 다음 영업일 owner](2026-09-28-stage2-todo-checklist.md)로 이관한다.

- [x] `[PostcloseWidgetEodSlotAdmission] 위젯 EOD·장후 계산 슬롯과 source quarantine 검증` (`Due: 2026-09-24`, `Slot: POSTCLOSE_RECOVERY`, `TimeWindow: 07:00~23:20`, `Track: RuntimeStability`)
  - Source: [9/23 원 owner](2026-09-23-stage2-todo-checklist.md), [장시간 작업 최적화 계획](../proposals/postclose-long-running-work-quality-preserving-optimization-plan-2026-09-23.md).
  - 완료 기준: EOD 미준비 시 stage가 계산 슬롯을 잡지 않고 `waiting_for_source`로 대기하며, 완료 후 기존 worker의 날짜·행수 검사를 통과해 같은 모집단·grid·정책 hash를 산출한다. 9/23 EOD 선행·widget 100개 선택과 476개 deferred·source 적격 97개/격리 3개의 날짜와 제외 사유를 확인한다. 신규 원천 실행의 stage wall/child CPU/RSS·EOD 대기·source hash·최종 validator receipt를 구분하고 설치 unit의 검증된 경로를 확인한다. 9/22 복구 성공은 신규 성능 증거가 아니며 관측 전용 정책을 live 승격으로 표기하지 않는다.
  - 9/24 복구·이관: 9/23 EOD `completed_with_warnings`, widget 100개 선택/476개 deferred·적격 97/격리 3과 EOD `UNKNOWN` 44의 교집합 0을 대사했다. 두 장후 unit은 release `484129dc` 경로/commit으로 수정·검증했고 9/23 stage 재사용은 hash 검사 통과다. EOD 미준비 대기·새 자연일 wall/CPU/RSS와 관측 전용 정책의 실제 소비는 [동일 ID의 다음 영업일 owner](2026-09-28-stage2-todo-checklist.md)에서 검증한다.

- [x] `[MachineResultSemanticMonitorRepair0924] 기계 판정 결과 의미 감시 누락 수리` (`Due: 2026-09-24`, `Slot: POSTCLOSE_RECOVERY`, `TimeWindow: 12:00~23:20`, `Track: RuntimeStability`)
  - Source: [기계 판정 전수 필드·시장층 감사](../audit-reports/2026-09-24-machine-judgement-horizon-and-field-association-audit.md), [운영 산출물 추적](../report-based-automation-traceability.md).
  - 완료 기준: 기존 `artifact_freshness`가 exact-date hash 검증 보고서의 scope별 구조 적격·운영 paired·원천 계약 제외 및 compact 운영 행 전량 제외를 `warning`과 원래 분모로 노출한다. `source_gap`을 경제성 0이나 자동 승격으로 바꾸지 않고, before-window와 보고서 부재에는 잘못된 의미 경고를 내지 않는다.
  - 작업본 검증: 9/23 원천에서 `machine_operating_paired_unbound`, `machine_operating_economics_incomplete`, `machine_source_contract_exclusions`, `machine_current_structure_empty`, `compact_operating_rows_all_excluded` 탐지. 감시기 관련 103개 pytest·compile·diff 검사를 통과했다. 이 수리는 작업본 코드 검증이며 기존 설치 release·최종화 영수증·다음 자연일 PID 소비를 갱신한 증거가 아니다. 74개 compact 행의 과거 terminal/stop 원천 결손은 보간하지 않았다.

## Project/Calendar 동기화

문서 parser만 실행한다. 외부 동기화는 사용자가 표준 명령으로 수행한다.
