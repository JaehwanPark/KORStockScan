# Main 공통 시장원천 후속 코드 리뷰·배포 수용 점검

2026-10-09 KST. Owner: `MainMarketSourceConsolidation1009`.

사용자가 후속 코드 리뷰·수정보완과 배포를 승인했다. 추가 결함을 수정하고 불변 검증 후보를 만들었으나, **계획 §7.3/T8/G5 성능 수용이 아직 미완료여서 운영 릴리스를 선택하지 않았다.** 이전 [구현 리뷰](main-market-source-consolidation-implementation-review-2026-10-09.md)의 수치와 당시 미관측 범위는 역사적 기록이며, 아래가 후속 검증 상태다. 성능 실패를 canary 절대 기준 통과나 CPU 개선으로 상쇄하지 않는다.

## 반복 리뷰에서 보완한 결함

| 결함 | 수정 | 회귀/반례 |
|---|---|---|
| writer 시작이 producer의 상태 잠금을 점유하여 새 partition의 첫 수신과 snapshot을 지연 | writer 생성 직렬화와 짧은 registry 잠금을 분리. thread 시작은 수신 상태·registry 잠금 밖에서 수행 | 0B/0D writer 시작을 의도적으로 멈춰도 callback·snapshot 진행. close timeout 뒤 재시도에서 수락된 원천 모두 저장 |
| 진단 snapshot이 같은 latency 표본을 percentile마다 재정렬 | bounded copy 이후 한 번 정렬하여 p50/p95/p99 계산 | 이전 반올림·percentile 값과 정확히 일치. 진단 주기·표본 수 유지 |
| raw 모드가 퇴역 detector의 pre-event 틱을 계속 보관 | 순서·시각 watermark와 품질 계수만 유지. archive detector 주입은 종전 보관 유지 | 중복/역행/결손 판정 동등, symbol drop/reset 후 watermark 정리. raw 저장 행 수 불변 |
| 공통 helper 추가 후 과거 V4 정책을 현재 pin 목록으로 검증하면 원 세대의 유효성을 판단할 수 없음 | 명시적인 역사적 검증만 불변 원 릴리스의 validator로 실행. 일반 runtime은 현재 pin을 엄격히 검사 | 원 릴리스 검증 실패 전파, 과거 validator 호출 확인. 현재 코드 변경은 계속 거절 |
| 현재 V6 정책·미래 후보가 새 코드 pin과 달라 배포 후 PREOPEN 연결이 끊김 | `stage_code_refresh`로 미래의 이미 발행된 후보만 내용 동일성을 검증하며 재결속. 새 code hash·보고서 hash·세대만 갱신 | 원 정책/원천/current 불변, 패턴·AI payload 변경 거절, 후보 CAS, 원 primary source 변조 거절, 재실행 시 추가 파일 0 |
| 과거 정책의 최초 release가 없어도 검토된 후속 release가 같은 pin을 엄격히 검증하는 경우를 구분하지 못함 | 이전 검토 릴리스의 실제 strict current loader를 별도 interpreter에서 실행하여 활성 parent 검증 | dirty/다른 commit·loader 실패·잘못된 parent 거절. 활성화의 source 손상은 역사적 code 검사로 우회하지 않음 |

코드 결속 갱신은 정책 재선정·우월성 주장·Provider 재호출이 아니다. 기존 날짜, 기계 패턴 목록, 임계값, 보조판정 payload, 비교 결과, 등록 권한을 보존한다. 미래 후보만 CAS로 바꾸며 current는 정식 당일 PREOPEN 활성화까지 유지한다. 이 경로는 테스트에서 검증했으며 **실제 운영 정책에는 실행하지 않았다**. 실제 후보와 활성 정책은 기존 선택 릴리스의 loader에서 각각 유효함을 별도로 확인했다.

## 성능 측정과 남은 수용 조건

측정은 동일 host·동일 원본 source baseline과 후보를 새 프로세스에서 각각 3회 비교했다. queue/batch/fsync/canary 한도와 원 5초 TTL을 변경하지 않았다. 퇴역 작업 제거 전후의 임시 원장은 자동 삭제했고 운영 원장·AI 비교 원장을 복제하거나 실제 Provider/브로커를 호출하지 않았다.

초기 측정에서 같은 symbol의 여러 수신이 exit wake로 합쳐져 비교 분모가 달라졌다. 후속 harness는 순서가 고정된 18,200행(0B 12,133·0D 6,067), 세 route, 정확히 200개 packet fence를 사용한다. fence의 evaluator 확인 전 다음 행을 보내지 않아 두 버전의 청산 측정 분모가 같다. 저장 지연도 queue 종료가 아니라 각 행의 enqueue부터 실제 append·fsync 반환까지 측정한다. 따라서 아래 결과는 기존 2,400행 측정과 별개이며, 운영 처리량 또는 실거래 효과로 일반화하지 않는다.

| 시나리오 | 합성 스트레스 CPU 중앙값 감소 | 0B callback p95 ms | 0D callback p95 ms | exit evaluator 시작 p95 ms | enqueue→fsync p95 ms |
|---|---:|---:|---:|---:|---:|
| 정상 | 82.6% | 0.0982→0.0511 | 0.1375→0.0816 | 4.8125→0.1283 | 387.24→281.00 |
| burst | 82.0% | 0.0363→0.0353 | 0.0553→0.0534 | 5.7624→2.7521 | 12,048.94→1,787.53 |
| 느린 fsync | 80.9% | 0.0358→0.0351 | 0.0541→0.0536 | 5.6883→2.8386 | 12,066.94→1,797.10 |

표의 지연은 각 3회 p95의 중앙값이다. 모든 행은 durable 저장 수와 일치한다. 진단 snapshot은 stress harness에서 5ms 주기로 호출했으므로 CPU 개선율을 실제 운영 절감률로 주장하지 않는다. 정상 enqueue→fsync p50 및 burst/slow 0D p50은 개선되지 않은 경우도 있으며 원본에 그대로 남겼다. 계획의 필수 상대 판정은 p95/p99/max다.

**burst·느린 fsync의 필수 상대 p95/p99/max는 통과했지만, 정상 0D 최대 지연은 미통과다.** 기준선 3회 max는 2.3533/5.8110/7.1435ms, 후보는 1.9948/2.2703/35.7422ms다. 후보 중앙값은 통과하고 후보 최악값은 `7.1435 + (7.1435 - 2.3533) + clock resolution` 상한을 넘는다. 추가 진단 1회에서도 36.5464ms callback과 generation-2 GC 36.3812ms가 겹쳤다. 이 진단은 원인 식별용이며 실패한 수용 표본을 교체하지 않는다. 전역 GC를 끄거나 수신 시간에서 빼지 않았고 guard도 완화하지 않았다.

native 관찰→claim→machine 부분 경로는 세 종목·2,160행·각 3회에서 **199개 claim/회, 결과 SHA 동일, 새 5초 만료 0**이었다. p95/p99/max 상대 기준을 통과했다. 이는 실제 production native/claim/assessment 함수를 사용한 격리 재생이며 **전체 Main scanner loop 성능 측정이 아니다**. 전체 Main cold/warm loop와 장후 cold/warm 전체 wall-time 비교는 아직 미관측이다. 기존 같은 source 세대 observe/snapshot/Provider delta 0 회귀는 유지한다.

별도 현재 코드의 0B 절대 canary(3회×2,000 callback)는 내부 p95 최대 0.024492ms, p99 최대 0.032570ms, queue drop·worker error 0이었다. 기존 1ms/2ms·최소 1,000회 기준 그대로다. [canary와 측정 영수증](../audit-reports/2026-10-09-main-market-source-latency-validation.json.txt)의 PASS는 이 절대 guard에만 한정하고 전체 상대 성능은 `PARTIAL_NOT_APPROVED_FOR_RUNTIME_ADOPTION`으로 남긴다.

## 검증 후보와 운영 보존

- 최종 검증 후보: `main-market-source-20261009-review-v2`, commit `9d6cff39d0c9455386647612c18055d6825944d6`. 현재 선택 릴리스 commit `7e1a826318e7b8418afd2e2436b79bf2febf8f67` 위에 이번 범위 Python 36파일만 반영했다. `sniper_state_handlers.py`는 Main 공통 helper import만 옮겼고 별도 HP 미커밋 변경은 섞지 않았다.
- 최종 불변 후보의 통합 회귀 **1,436건 통과, 실패 0**(146.86초). 기존 pandas 경고와 multithread fork 테스트 경고 2건은 남았다. Python 36파일 compile 통과. wrapper 변경은 이번 후속 범위에 없어 기존 HP/MW wrapper 변경을 보존했다.
- 선택 릴리스는 `main-market-weakness-20261009-v1` 그대로다. 기존 릴리스에서 10/12 `next_preopen_readiness --verify`는 source 10/8·현재 전체 계약 `pass`, findings 0이었다. `actual_pid_consumed=false`; 휴장일 강제 기동을 하지 않았다.
- candidate 생성은 운영 배포 완료가 아니다. selector·실제 current/candidate 정책·봉인된 10/12 checklist·Rebase·기존 미커밋 작업을 보존한다. 코드 갱신 정책 발행·선택 변경·PREOPEN 재생성·장후 재실행·실제 주문·외부 알림/sync·운영 원천 삭제는 수행하지 않았다.

재현 근거는 `tmp/main-market-source-review-deployment-20261009/`에 있다. `candidate-v2-build.json`, `candidate-v2-integrated-tests.log`, `compiled-v2-files.json`, `raw-history-v4/performance-summary.json`, `raw-history-v4/gc-diagnostic.json`, `native-summary.json`, `selected-preopen-verify.log`가 각각 코드·회귀·성능·기존 준비 상태를 소유한다. 검증 중 만든 review-v1은 운영 선택 이력이 없으며 후속 candidate와 구분한다.

최종 문서 검사에서 상대 링크 84개, fence·공백·`git diff --check`를 통과했다. print-only parser exit 0, backlog 23건 중 현 stable owner는 1개다. 첫 구현 시작의 기존 변경 58개 중 54개는 byte 동일하며, 의도된 겹침 4개(owning 계획·현 checklist·runbook·state handler helper import)를 별도 기록했다. 최종 후보 36파일 hash와 runtime source clean 상태, selector·10/12 checklist·Rebase 보존도 확인했다. `final-review-checks.json`이 이 검사의 영수증이다.

완료한 최종 후보 회귀의 전용 pytest 임시 디렉터리만 lock 부재·해당 회귀 fixture·실행 종료를 확인한 뒤 정리했다. 회수한 논리 파일 크기는 1,285,067,452 bytes다. 운영 raw·정책·Provider 원장·검증 로그는 삭제하지 않았다. `test-temp-cleanup.json`에 정확 경로와 범위를 기록했다.

## 미완료 owner와 종료 검사

기존 `MainMarketSourceConsolidation1009` 하나를 OPEN으로 유지한다. 다음 조치는 정상 0D global-GC tail의 실제 원인/영향을 격리하고, 전체 Main loop와 장후 cold/warm의 같은 입력 성능 비교를 완료하는 것이다. 종료 검사는 계획 §7.3/T8/G5다. 유효한 수용 검증 뒤에만 승인된 정책 코드 결속 갱신→릴리스 선택→정식 PREOPEN 재준비/검증을 진행한다. 이미 승인된 배포를 다시 요청하는 항목이 아니며, 추가 경제성 gate도 아니다. 자연 세션/PID/장후 소비는 그 이후 별도 MS6 증거다.
