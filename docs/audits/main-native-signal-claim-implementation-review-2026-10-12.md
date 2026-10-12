# Native 신호 claim·보조 재검증 구현 리뷰 — 2026-10-12

[계획](../proposals/main-native-signal-claim-and-auxiliary-revalidation-remediation-plan-2026-10-12.md)을 리뷰·보완하고 작업본 구현을 검증했다. 배포·재기동·운영 장후 재생성은 실행하지 않았다. 아래 검증은 코드 범위이며 현재 PID 소비나 자연 진입/수익 결과를 의미하지 않는다.

## 수정한 결함과 소비 경로

| 범위 | 결함과 보완 | 직접 소비 |
| --- | --- | --- |
| S0 | 단순 age 만료가 유효 진입의 전달 실패처럼 보이던 집계에 별도 lifecycle 추가. FIRST 무효화/교체·source/epoch·Main 방문·정확 claim을 분리하고 불명 원천은 unobservable | `runtime_performance` → 기존 bounded observation queue → `native_signal_lifecycle` → `entry_mechanical_momentum` 분 partition |
| S1 | Main이 native guard의 오류 문자열만 남기던 경로에 scalar 실패 predicate·생존 branch·registration hash·원 clock 보존. rejection 뒤 ack 오류는 원 거부를 덮지 않음 | `reversal_source_diagnostics` → `sniper_state_handlers` → immutable result의 `entry_async_disposition` |
| N0 | EventBus 구독만으로 실제 소비 준비를 판단하던 결함. WS session/epoch·AI/token 존재·기계 family를 예약 전과 실제 callback 시작 전에 확인 | EventBus callback은 구독 lock 밖에서 실행. 미준비 시 물리 worker를 만들지 않음 |
| N1 | 필수 feature가 60초 이상인데 60초 슬롯에 반복 배정되는 경우를 분리. 활성 branch 정의의 backward history/hold로 60/150초 선택 | discovery queue → claim requirements → probe outcome. 5슬롯·긴 슬롯 최대2·기존 TTL 및 lease cleanup 유지 |
| S2 | AI client 전체와 HTTP 시간 차이만으로는 지연 위치를 확정할 수 없었음. Provider 전/호출/응답 후/annotation·cache의 비중첩 clock 추가 | AI 결과 → 기존 async disposition. 인과 증거 없는 scheduler/캐시 변경은 적용하지 않음 |
| S3 | callback 완료를 append 성공으로 해석할 수 없는 문제. 저장 확인·의도적 skip·미확인·실패를 구분하고 실제 checkpoint writer의 durable receipt 연결 | queue owner별 bounded 집계. 기존 source artifact와 실행 권한 유지 |
| S4 | native ask·정확 후행 quote·비용/stop/30분이 없는 일반 outcome을 승패로 사용하는 위험을 차단 | `continuous_reversal_shared_ledger.native_lifecycle_outcomes`; 기존 indexed window를 받는 offline reader, 새 자동 producer/AI 호출 없음 |

## 리뷰·보완 반복

1. 1차 리뷰에서 readiness 도입에 따른 기존 mock의 구독/준비 혼동을 수정하고 원 기한·정책·native branch 검증을 대조했다.
2. 2차 리뷰에서 새 정상 FALSE 사유가 감시기의 기존 증빙 검사와 연결되도록 보완했다. UNKNOWN은 정상 FALSE로 읽지 않는다. 실제 체크포인트 저장 결과도 큐에 저장 완료 영수증을 반환하도록 수정했다.
3. 3차 리뷰에서 selector의 소비 상태 갱신, 같은 opportunity의 충돌 복제본 제외, malformed identity의 행별 격리, 늦은 목표 도달과 주 승률의 분리를 보완했다.
4. 기동 시 기존 `reversal_evaluation_context.prepare`가 family를 준비함을 확인했다. N0가 첫 probe 완료를 기다리는 순환 조건은 없다. 해당 시작 경로는 기존 startup 회귀로 검증했다.

native/WS lock 안에는 scalar 관측만 두고 writer/hash/provider 작업을 추가하지 않았다. native→diagnostic lock 순서를 유지했다. 새로운 Python 파일은 기존 `src/tests` 역할 경계에만 만들었으며 engine root 모듈을 추가하지 않았다. Kiwoom 요청·응답/FID·REG/REMOVE/auth 프로토콜은 변경하지 않았다.

## 검증

- 통합 21개 테스트 파일: **1,207 passed**, 기존 `pandas_ta`의 pandas Copy-on-Write deprecation warning 1개. [로그](../../tmp/native-signal-claim-repair-20261012/pytest-final.txt)
- 추가 동시 native 관측/claim 보존식: **1 passed**. [로그](../../tmp/native-signal-claim-repair-20261012/pytest-concurrency.txt)
- 실제 native selector와 관측 adapter의 결과 parity, 동일 결과 재수거·successor/ack 실패, readiness 경합, 기존 슬롯/lease 한도, source/quote/epoch·row hash 불일치, stop-first/30분/후순위 늦은 결과를 검증했다.
- 실제 writer를 통한 JSONL append와 lossless 분 partition의 capsule/해시 보존을 확인했다. `queued = completed + failed + pending`, `completed = append_confirmed + intentionally_not_written + append_unobservable`을 구분한다. 큐 admission 거절은 별도 unavailable이다.
- [동일 입력 비용 비교](../../tmp/native-signal-claim-repair-20261012/diagnostic-overhead-benchmark.json): 5,000관측·500기회·1stream, 교대 3회. baseline callback p95 0.00484–0.00488ms, candidate 0.01548–0.01555ms. 모든 native 상태와 기회 수가 유지됐다. 추가 비용 약 0.011ms이며 full Main/장후 동시 부하나 실시간 성능 개선을 검증한 것은 아니다.
- compile, 현재/후보 checklist의 print-only parser, 문서 로컬 링크, `git diff --check` 결과와 파일 해시는 [완료 영수증](../../tmp/native-signal-claim-repair-20261012/completion.json)에 기록한다.

## 원천 연구 결과와 남은 인계

[source-only 결과](../../tmp/native-signal-claim-repair-20261012/historical-source-research.json)는 PID 981118의 기존 12,076바이트 요약과 37,995바이트 exact 종료 partition만 읽었다. 4건의 attempt/신호 종료를 대조했으나 native ask·scope/epoch·후행 window index가 이 원천에 결속되지 않아 **4건 제외, 승률 null**이다. 실제 raw 전체의 부재를 주장하는 것은 아니다. 새 원장 복제나 진행 중 대형 파일의 전수 스캔은 하지 않았다. 과거 age-only 30건은 계속 `historical_unresolved`다.

현재 봉인된 checklist는 변경하지 않았다. [후보 checklist](../../tmp/native-signal-claim-repair-20261012/2026-10-12-stage2-todo-checklist.md)에 기존 `MachineAuxiliarySignalDeliveryRepair1012`·`NonfixedDispatchReadinessReview1012`의 이번 보완 범위를 준비하고 이전 완료 근거를 보존했다. 장후 owner `DirectFamilySourceRepairCompactAuxiliary`·`continuous_reversal_postclose`, 배포 owner `OrderedIntradayDeploymentRepair1012`는 유지한다.

작업본 코드리뷰에서 미해결 결함은 없다. 배포 후 exact PID의 자연 lifecycle, 실제 PASS 재검증, writer→reader, 비상시 수신/feature 구간과 Main loop tail은 미관측이다. S2 scheduler 변경은 그 인과 증거가 확보되는 경우에만 진행한다. 원 5초·정책/FSM·호가/주문/custody/hard safety·episode/widget 퇴역 상태를 변경하지 않았다.

## 후속 재리뷰 연결

위 미배포/미관측 상태는 최초 구현 당시 기록이다. [통합 배포 리뷰](main-native-readiness-deployment-review-2026-10-12.md)의 배포 후 사용자가 재리뷰·결함 보완·배포·재기동을 승인했다. 원 claim/native 재검증과 scanner→Main 연결을 다시 대조해, 결과 inbox에서 잘못된 응답이 정상 결과/해제 ACK의 중복 키를 선점하는 결함을 확인했다. 원 claim의 시각·scope·원천 및 명시된 lease/판정 형식을 inbox 저장 전에 검사하고 정확한 해제 소비에도 같은 신원을 적용했다.

[상시·비상시 재리뷰](main-fixed-nonfixed-readiness-implementation-review-2026-10-12.md#배포-후-추가-코드리뷰결과-수신-보완)에 6개 실패 재현과 보완 후 **595건 회귀**를 기록했다. Native policy/FSM/5초·물리 cleanup·원 PREOPEN/정책 파일은 보존하며, [후속 배포 증빙](../../tmp/native-readiness-rereview-20261012/completion.json)이 새 PID 소비와 운영 결과를 소유한다.
