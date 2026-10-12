# 기계판정 입력 준비 기한 소진 보완 — 2026-10-12

## 범위와 원인

사용자가 지정한 `aims-6fc7342dd5946c19c948`의 입력 기한 만료를 점검하고, 입력 준비 비용·단계별 계측을 보완한다. 코드 리뷰 후 배포·재기동은 승인된 범위다. 원래 5초 기한과 정책·보호조건·원천 시각·주문 권한을 유지한다.

- 원 기한 `08:37:05.612735`, worker 완료 `08:37:05.695898`: **83.163ms 초과**. 신뢰 체결 10건의 사용 증빙이 있으며 provider 호출 전에 실패했다.
- pipeline의 같은 요청에는 preparation 대기 17.014ms, service 330.232ms, AI dispatch 대기 19.444ms, worker 단계 1,271.704ms, 결과 후 commit 71.903ms가 기록됐다. `ai_response_sec` 이름의 worker 시간은 이 건에서 실제 provider 응답 시간이 아니다. 당시 세부 복사/재검증 시간이 없어 가장 느렸던 입력 단계나 전체 5초의 원인을 확정할 수 없다.
- Main의 `expired_after_response`, 새 snapshot 재평가 대기와 Buy Funnel의 `historical_unresolved`를 보존한다. 과거 실패를 새 성공으로 변경하거나 외부 자료로 소급 복구하지 않는다.
- 작업 시작 시 선택 릴리스 `machine-auxiliary-path-20261012-v3`, PID 727995, start ticks 2236769를 기준으로 확인했다. 새 릴리스 소비는 아래 운영 영수증으로 별도 판정한다.

## 구현과 재검토

1. 최종 기계 입력 동결에서 이미 분리된 입력 그래프를 canonical 재검증이 다시 전체 복제하던 비용을 제거한다. 공개 호출의 기본 복제 계약은 그대로이며, 해당 최종 동결 소유자만 내부 옵션을 사용한다. callback에 전달하기 전 복제와 callback이 반환한 공유 객체를 분리하는 복제는 모두 유지한다. route/epoch/BBO·봉 시각·신선도 검사도 보존한다.
2. 최초 복사 전과 직후 원 기한을 검사한다. 복사 도중 만료되면 추가 refresher를 실행하지 않는다. 만료된 입력을 AI 호출이나 제출에 사용하지 않는다.
3. 최초/반환 입력 복사, local refresh, canonical 재검증, 기존 feature build, 동결 전후 잔여 기한과 실패 관측 단계를 기존 trace의 정확한 판정 ID에 보존한다. refresh 예외에서도 소요 시간을 남긴다. 실패 단계는 원인 확정값이 아니라 실패가 확인된 위치다. 새 대용량 원장은 만들지 않는다.
4. 당일 동일정책 인계의 허용 함수에 `_final_entry_machine_inputs`만 추가한다. 원 PREOPEN 정책/코드·실제 predecessor PID 소비·현재 불변 릴리스 bytes 및 나머지 AST 동일성을 검증한다. 제출지연/보유 incumbent만 같은 값으로 이어받으며 연구·신규 정책의 전체 코드 해시 계약을 완화하지 않는다.

상호 객체 격리, 정상/예외/복사 중 만료, source clock/route/epoch, trace 전달, 잘못된 승인·PID·정책·manifest·검증기 변경 및 비허용 함수 변경을 재검토했다. 검토 범위에 미해결 코드 결함은 발견되지 않았다. 과거 trace에 없는 세부 원인을 추정하여 채우지 않는다.

## 검증과 성능 범위

- 관련 pytest **723건 통과**. Python compile, diff, checklist print-only parser는 배포 전 수행하고 결과를 완료 영수증에 기록한다. 추가 provider/브로커 호출은 하지 않는다.
- frozen synthetic 입력 2종, 3회 교대 × arm별 15회, 총 180회. 430개 봉을 제공했으며 정상 context builder가 보존한 완료 봉은 **300개**다. 비교 범위는 최종 입력 동결 함수이고 전체 Main/AI 경로가 아니다. 모든 결과의 입력 값·원천·출력은 동일하고 호출자 객체는 변하지 않았다.

| 체결 수 | baseline 중앙값, 3회 (ms) | candidate 중앙값, 3회 (ms) |
|---|---|---|
| 10 | 7.948 / 7.902 / 8.042 | 6.107 / 6.215 / 6.201 |
| 1,000 | 15.049 / 15.186 / 15.235 | 11.712 / 11.668 / 11.632 |

1,000체결 후보의 두 번째 trial에는 96.529ms 이상치가 있었고 baseline p95는 약 15.2~15.4ms였다. 따라서 중앙값 복사 비용 감소만 확인했으며 tail latency 비열화나 전체 5초 내 완료를 입증하지 않는다. 당시 83ms 초과를 이번 약 2~4ms 절감만으로 해소했다고 주장하지 않는다. 실시간 신규 표본과 단계별 trace는 기존 자연 수용 owner에서 대조한다.

원천/benchmark/tests: [작업 증거](../../tmp/entry-input-deadline-repair-20261012/). 배포·정책값 보존·보조판정 호환성 128경로·새 PID/heartbeat: [완료 영수증](../../tmp/entry-input-deadline-repair-20261012/completion.json). 기존 장후 연구 OPEN owner는 유지한다.
