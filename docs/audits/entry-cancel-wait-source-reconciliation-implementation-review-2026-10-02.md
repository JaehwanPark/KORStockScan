# BUY 취소 대기 원천 대사·의미감시 구현 리뷰

작성일: 2026-10-03 KST. 분석 대상: 2026-10-02. 소유자: [10/6 인계 checklist](../checklists/2026-10-06-stage2-todo-checklist.md)의 `EntryCancelWaitSourceReconciliation1002`.
근거: [보완구현 계획](../proposals/entry-cancel-wait-source-reconciliation-remediation-plan-2026-10-02.md). 사용자 추가 지시로 현재 작업본에 구현하고 반복 리뷰·보완·회귀검증했다.
판정: 검토한 구현·직접 소비 범위의 미해결 코드 finding 0. 실제 새 장후 세대 및 선택 실행본의 수용은 OPEN이다.

## 구현 결과

| 경로 | 보완 내용 |
| --- | --- |
| [생산자](../../src/engine/automation/entry_cancel_wait_tuning.py) | event-only 날짜도 원천 재검증한다. 중간 거래일의 보고서 부재는 bounded compact 원천과 봉인 census로 확인한다. 부분 실패 날짜는 quarantine 참조로 보존하고 검증된 날짜를 유지한다. legacy v2의 이벤트를 대사해 version 1 ledger를 새 상태에 발행한다. |
| 계산·custody | 당일 census와 과거 history를 분리한다. 미분류·결손 범위의 확정 과거 미해결 수는 null이고, known open·terminal 미검증·체결 cost 미완료는 관측 수로 따로 남긴다. registry 미등록 source-only child를 누락하지 않는다. truthy terminal flag 또는 취소 success/filled 0을 종료 증명으로 수용하지 않는다. portfolio 분모를 격리할 수 없는 미해결 custody/source는 비교·후보를 차단한다. |
| 공통 validator | report/state/date/ledger·분모·bool/정수·null/0·유한 경제성 수치·당일/과거 projection·carry·policy 날짜/proof/scope를 대사한다. 봉인 producer metadata의 count/hash로 coherent self-reseal도 검출한다. 원천을 읽는 중 변하면 unobservable이며 안정된 다른 세대는 stale finding이다. 전체 metadata 읽기 예산은 64MB, 캐시는 report/policy proof와 receipt/registry 세대에 결속한다. |
| [runtime summary](../../src/engine/runtime_approval_summary.py) | 같은 validated projection을 소비해 valid-empty, history source gap, waiting outcome 및 별도 순차 timeout owner를 구분한다. null을 0으로 바꾸거나 not_applicable로 결손을 숨기지 않는다. |
| [tower](../../src/engine/automation/tuning_performance_control_tower.py)·[summary handoff](../../src/engine/automation/postclose_summary_handoff.py)·[다음 checklist](../../src/engine/build_next_stage2_checklist.py) | 현재 direct-family 경로에도 cancel-wait report/policy의 세대 binding과 전용 tower 필드, 단일 checklist block을 발행한다. summary/tower/checklist projection 불일치와 block 중복을 scoped strict가 거부한다. |
| [artifact freshness](../../src/engine/error_detectors/artifact_freshness.py)·[장중 표시](../../src/engine/monitoring/submission_bottleneck_monitor.py) | 기존 native command metrics·reuse·run identity를 읽고 존재하지 않는 독립 stage-terminal을 요구하지 않는다. 새 계약 이전 보고서는 legacy 미검증이다. valid-empty·정상 carry·미도래·세대 전환에는 조치 알림이 없다. 자정을 넘긴 진행 run은 원 source date를 유지한다. 장중은 같은 진단을 표시하고 사고 알림은 artifact freshness가 소유한다. |
| [알림](../../src/engine/notify_error_detection_admin.py) | cancel-wait stage 허용·안정적인 incident fingerprint·중복 억제·동일 분석일 검증 회복을 연결했다. 자정 뒤 이전 분석일 알림은 정확한 native run/date 결속이 있을 때만 수용한다. 실제 발송 없이 mock으로 검증했다. |

기존 economic schema v2 및 runtime policy 구조, common timeout·적격 기존 scope 승계, 순차 첫 leg의 독립 timeout owner를 유지했다. pre-submit 가격 연구 계산이나 주문·provider·bot·hard safety 계약을 수정하지 않았다. 무표본·결손에 EV 0 또는 새 후보를 합성하지 않는다.

## 반복 리뷰에서 추가로 수정한 결함

1. 최초 P0 회귀 두 건은 원 코드에서 모두 실패했다. event-only 날짜의 원천 검증 누락과 당일 0에 의한 과거 미분류 소거를 고정했다.
2. 실제 tower 생산자 시험에서 direct 경로의 report/policy source receipt 누락을 찾았다. 실제 다음 checklist 생산자 시험에서 legacy 경로에만 있던 전용 handoff 발행 누락을 찾았다. 둘 다 직접 경로에 연결했다.
3. terminal boolean만으로 미체결 custody를 종료하는 분석 경로를 owner-issued 정확 terminal proof로 보완했다. source-only·partial/open·cost pending의 관측 분모를 유지했다.
4. 원천 재생/파일 write 없는 감시, metadata의 count/hash 대사, 전체 읽기 예산, 세대 캐시, 무관한 registry append의 조상 검증을 보완했다. manifest 재읽기까지 source metadata 예산에 포함했다. incumbent 재검증은 다른 모든 내용과 구현 SHA가 동일한 무관한 append만 허용하며 관련 Main 변경은 다시 검증한다.
5. 자정·휴장일 날짜 전파와 알림 filter를 회귀시험으로 연결하고 발견한 날짜 helper import 누락을 수정했다. 기존 시각 의존 시간창 시험 두 건이 00:00~00:01에 실패하는 것도 확인해 시험 시각을 고정했다. 마지막 공통 validator 리뷰에서는 읽기 예산 초과가 이미 확인한 허위 zero finding을 지우지 않도록 보완했다.

6. 최종 의미 리뷰에서는 새 후보 표시가 기존 actual model 20건·시간순 학습/독립 holdout·정확 paired count 및 양의 보수적 개선 증거와 일치하도록 검사했다. 기준을 새로 늘리지 않았고 정상 empty/carry의 코드 수리에는 이 조건을 적용하지 않는다.
7. 분석 범위의 최신 이전 상태가 심볼릭 링크이거나 64MB를 넘을 때 이전 상태를 건너뛰어 정상 무표본으로 보이던 경로를 차단했다. 두 경우 모두 원천 결손을 명시하며 격리 fixture로 회귀검증했다.

## 10/3 추가 코드리뷰·수정

사용자의 추가 반복 리뷰 지시에 따라 현재 변경과 직접 소비 경로를 다시 검토했다. 다음 세 결함군을 격리 시험으로 재현해 수정했고, 재리뷰 후 검토 범위 미해결 코드 finding은 0이다.

1. 자정 이후 원 native run이 `producers_completed`·`succeeded`·`failed`로 바뀌면 원 분석일 감시와 알림 filter에서 빠졌다. 완료/실패 run도 원 날짜·run identity를 보존하며, 당일의 새 run이 시작되면 그 날짜를 우선한다. 완료 영수증을 PID/경제성 증명으로 사용하지 않는다.
2. 완료 세대에서 summary·tower·checklist가 부재하거나 다른 날짜/hash를 가리켜도 영구 pending으로 보였다. report/policy/summary 물리 hash와 기존 source receipt, 단일 checklist block을 대조하고 완료된 native 세대의 불일치는 `cancel_wait_consumer_projection_invalid`로 남긴다. 진행 중 후행 미도래는 pending이다. 읽기 도중 파일 삭제·변조, native/원 report/registry 교체는 unobservable로 구분한다. 원 validator findings를 복사해 consumer findings 추가가 원 projection을 바꾸지 않게 했다.
3. 소비 결함 알림이 primary carry만 정상이고 후행은 pending인 상태에서 해제됐다. 동일 분석일 소비 projection이 모두 verified일 때 회복한다. 명령 실패/성공 후 report 부재의 사고는 현재 성공 command receipt가 있어야 회복하며, bounded log에서 영수증을 읽지 못한 것만으로 회복하지 않는다. 날짜가 자정을 넘은 완료 run의 실제 회복을 historical_unrecovered로 잘못 이전하지 않는다.

추가 30개 회귀는 stable missing/stale/date/JSON/duplicate, pending→verified, warning→dedupe→verified recovery, 명령 영수증 부재, 읽기 중 삭제·변조·세대 교체를 검증한다. 마지막 오류 경로 리뷰에서 consumer parse 실패가 이미 확인한 reuse 결함을 덮어쓰는 것을 재현해 두 finding을 함께 보존하도록 수정했다. 기존 두 Python source와 두 기존 시험 파일에만 추가 수정했다. 실제 API/알림/배포/보고서 재생성은 수행하지 않았다. 변경 전 스냅샷은 `tmp/entry-cancel-wait-followup-review-20261003/before`, 최종 시험 출력은 `tmp/entry-cancel-wait-followup-review-20261003/final-pytest.txt`다.

## 검증

초기 구현은 565 PASS(17.72초)였다. 추가 수정 후 11개 영향 suite 최종 **595 PASS**(18.71초), Python compile PASS. 문서·owner·link·diff·print-only parser 결과도 이 변경의 종료 근거다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short src/tests/test_entry_cancel_wait_tuning.py src/tests/test_entry_cancel_wait_runtime.py src/tests/test_entry_cancel_wait_attribution.py src/tests/test_runtime_approval_summary.py src/tests/test_submission_bottleneck_monitor.py src/tests/test_error_detector_artifact_freshness.py src/tests/test_notify_error_detection_admin.py src/tests/test_tuning_performance_control_tower.py src/tests/test_build_next_stage2_checklist.py src/tests/test_postclose_summary_handoff.py src/tests/test_verify_threshold_cycle_postclose_chain.py
```

시험은 temporary data/report/checklist와 실제 tower/checklist 생산자를 사용했다. cancel-wait scoped strict의 공통 validator·전용 last consumer를 검증했고, 그 통합 fixture에서 다른 family의 PREOPEN/PID gate는 mock으로 분리했다. 전체 native DONE, 실제 PREOPEN/PID, 새로운 수익 개선을 증명한 시험은 아니다.

## 실행 세대와 남은 수용

초기 23:50 이후 read-only 확인의 공통 selector는 별도 source 복구 작업의 `bd059f365b71dbf1fc297b659e514a7b5c19c916`였다. 추가 리뷰의 10/3 01:30:24 KST snapshot에서는 `63936cf18127cea77f074c56b4c5689a109445c9`, 경로 `/home/ubuntu/KORStockScan-runtime-releases/postclose-source-closure-20261002-63936cf1`이다. 이번 작업의 8개 producer/consumer 파일은 그 선택 실행본과 모두 SHA가 다르다. 10/2 운영 cancel-wait report는 23:40:48 생성된 v2이며 새 reconciliation contract가 없다. 따라서 이번 패치의 자연 수용은 not_observed다. 이 작업은 다른 작업의 release selection·불변 실행 코드·진행/종료 영수증을 교체하지 않았다. snapshot은 `tmp/entry-cancel-wait-followup-review-20261003/runtime-readonly-snapshot.json`에 남겼으며 PID/운영 수용을 주장하지 않는다.

다음 조치는 작업본 통합 범위가 확정된 실행 세대에서 고정 10/2 원천으로 새 ledger/report/policy를 생성한 뒤, 동일 generation의 summary→tower→10/6 checklist→cancel-wait strict 및 의미감시 projection을 한 번 대조하는 것이다. 이는 새 실행 세대 수용이며 이번 격리 코드 검증의 PASS와 구분한다. 원천 결손은 artifact/owner/closure test를 가진 source_gap/null로 유지한다. 무표본은 유효 empty/carry로 닫으며 실제 체결·양의 EV를 코드 수리 종료 조건으로 요구하지 않는다. 정책 준비·PREOPEN·PID 소비·경제성 승인은 기존 owner의 별도 수용이다.

10/3 현행 daily checklist는 존재하지 않는다. 승인된 10/2 분석 대상의 코드 마무리·검증만 수행했고 신규 운영 작업을 시작하지 않았다. 10/2 항목은 코드 종료와 이력으로 남기고 잔여 세대 수용을 기존 10/6 checklist의 동일 stable ID로 인계했다. 완료한 과거 항목을 현재 실행 소유자로 사용하지 않는다.
