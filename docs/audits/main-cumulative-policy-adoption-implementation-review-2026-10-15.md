# Main 누적 연구 후보 정책 반영 구현 검토 — 2026-10-15

## 1. 판단과 작업 경계

- 사용자 지시: [정책 반영 계획](../proposals/main-cumulative-research-policy-adoption-plan-2026-10-14.md)을 별도 작업본에 구현하고 코드 리뷰·보완을 반복한 뒤 **배포대기**로 준비한다.
- 작업본: `/home/ubuntu/KORStockScan-worktrees/cumulative-policy-adoption-20261015`; branch `codex/cumulative-policy-adoption-20261015`; base `c938ace0610aeec2e68dde9a024e0b82579a1c3b`.
- 원 작업본의 동시 변경과 운영 파일은 보존했다. private `data/`·`tmp/`를 사용했다. provider·Telegram·주문·운영 등록·정책 활성화·배포·재기동을 실행하지 않는다.
- 검토 단계: 구현 → 원천·consumer·권한 검토 → 반례 보완 → 재검토 → 표적 회귀 → 격리 원천 재생. 완료한 검증과 배포 이후의 자연 수용을 구분한다.

## 2. 구현 소유권과 선정 기준

| 소유 파일 | 구현 |
|---|---|
| [고정 catalog](../../src/engine/scalping/reversal_cumulative_catalog.py), [정의 resource](../../src/engine/scalping/reversal_cumulative_data.json) | 38개 수동 가설의 1,430개 exact-scope 정의, 22개 scope의 고정 A/F/J/current 표현. 원 joint v1·이전 registry 해시 보존 |
| [detector](../../src/engine/scalping/reversal_cumulative_runtime.py), [shared State](../../src/engine/scalping/reversal_extended_state.py) | FIRST/독립 상승 root, 확인 시점 필터, source break·hold 무효화, 의존성 순서와 내부 branch 제외 |
| [등록 owner](../../src/engine/scalping/reversal_cumulative_registration.py) | private prepare와 명시 승인 intake 분리, exact parent/code/date/source CAS, archive, 타 pending 충돌, consumed 재적용 방지 |
| [장후 owner](../../src/engine/scalping/reversal_cumulative_postclose.py) | 고정 원 root 1회 재생, F truth 재사용·정수 mask 비교, immutable checkpoint, 선정점만 materialize, 대용량 비교표 압축 |
| [v6 policy](../../src/engine/scalping/continuous_reversal_policy_v6.py), [운영 consumer](../../src/engine/scalping/continuous_reversal_operating_postclose.py), [기존 보조 consumer](../../src/engine/scalping/reversal_auxiliary_tuning.py) | 승인 manifest/선정 membership의 실제 소비, 기존 보조 registry/prompt 승계 또는 기존 bounded 비교 경로 연결 |

원칙은 실제 확인 ask·30분·비용률 0.0023·비용 후 목표 +0.4%/soft stop -3% 선도달의 **각 정책 자체의 누적 raw 승률**이다. 동률이면 W 수를 비교하고 실제 개선이 없으면 current를 유지한다. 성공 100%/80% 보존, 최소 표본/날짜, 새 holdout/EV gate를 추가하지 않는다. W·STOP·TIMEOUT·U, 확인점 CF·실제 ENTER_NOW·실현 손익을 구분한다.

- 초기 지정안: reviewed 결과의 변경 15개 scope·승계 7개 scope. 연구 parent `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`에 결속한다.
- 26,928개 고정 표현에는 원 연구에서 hit가 없던 A 등의 동일 결과 별칭도 있다. 실제 관측된 연구 대안은 19,892개다. 이 차이는 새 가설/임계값 추가가 아니다. live에서는 실제 선정 membership만 평가한다.
- 기계 후보 정제로 많은 기존 성공도 제외된다. 합산 CF 승률 67.80%→79.39%, W 2,579→905, target clock 288→117이라는 연구의 기회 감소를 숨기지 않는다. 이것은 실현 순이익 개선 증명이 아니다.

## 3. 코드 리뷰에서 찾아 보완한 사항

| 결함/위험 | 보완 및 재검토 |
|---|---|
| legacy 원 분기에 definition hash 필드가 없는데 필수 접근 | 기존 native의 optional branch hash 계약과 canonical definition ref를 함께 검증 |
| path 확인 신호에 `path_definition_id`가 없어 legacy로 오인 | 실제 확인 phase와 원 정의를 사용해 path proof 검증으로 연결 |
| HPSP 기존 type FIRST가 path catalog에도 있어 경로 phase로 오인 | FIRST/CONFIRMED는 원 native low/timeline 증빙을 사용. 기존 type FIRST 별도 반례 추가 |
| 여러 가격대를 한 번에 재생할 때 다른 가격대의 legacy branch 집계 | 실제 tick의 exact scope membership으로 집계·보조 materialize를 제한 |
| quote 없는 legacy FIRST를 신규 비교에 집계할 가능성 | 실제 유효 확인 호가를 요구하고 원 확인 ask를 보존 |
| 원 extended root 발행 전에 F를 적용하거나 내부 dependency가 OR로 누출 | 원 root 발행 후 F 평가, 마지막 단계에서 운영 membership만 남김 |
| 새 hold가 무효화돼도 다른 OR branch가 남은 ready에서 살아 보임 | 재귀 hold floor 및 exact ready membership으로 claim 재검증 |
| 모든 후보를 보조 AI 요청으로 확장할 위험 | 선정 membership 확인점만 bounded consumer에 전달. 보조 연구 미설정은 provider 0 호환 승계 |
| 대안별 반복 raw 읽기·대형 JSON의 8MiB reader 초과 | versioned partition checkpoint+bitmask; 전체 비교표는 immutable gzip, 운영 보고서는 current/selected 요약 |
| 준비안의 권한·날짜·코드·근거 변조 또는 parent 경합 | 별도 schema/authority, 봉인·코드 해시·정확한 날짜/원천 archive·publisher lock/CAS·타 요청 충돌 검증 |
| 소비한 등록안을 CLI가 원 코드 전이로 다시 여는 문제 | 현재 bundle의 consumed receipt 확인 후 일반 current 경로로 전달. override는 seed 쓰기 전에 거부 |
| 원 분기의 필수값 결손이 정제 분기에서 FALSE로 계측 | 원 legacy/기존 합성 coverage를 확정한 뒤 평가되지 않은 F에 UNKNOWN 전파. 실제 F FALSE와 구분 |
| 보조 승계 중 overlay 갱신으로 binding·근거 세대 혼합 | 기존 auxiliary publisher lock과 동일 overlay snapshot으로 binding/lineage/independent scope 결속 |
| future source·source 교체·캐시의 잘못된 재사용 | observation date 상한, 읽기 전후 hash, source/code/bar/label/parent fingerprint와 conflict 격리 |

기존 auxiliary prompt/input/response 원장과 5초 예산, broker/account/order/quantity/cooldown, source freshness/conflict, custody, retired widget/episode 경계는 보존했다. 이전 provider 응답 파일은 초기 승계를 이유로 비우지 않는다.

## 4. 검증 근거

### 4.1 표적 시험과 native consumer

- 최종 회귀 [final-source-coverage-tests.log](../../tmp/cumulative-adoption-review/final-source-coverage-tests.log): **246 passed**. 수정한 catalog/State/policy/등록/장후/보조와 bootstrap 계약, source UNKNOWN 전파·보조 snapshot 잠금 반례를 포함한다. 이전 242개·35개·74개 부분 회귀와 중복되므로 수를 합산하지 않는다.
- [native-reader.json](../../tmp/cumulative-adoption-review/native-reader.json): frozen parent의 실제 v6 family 구조 128개 scope·변경 15개 scope 검증, 새 A10의 native ENTER_NOW→typed request 확인, 원 parent 불변. **합성 등록 요청의 구조 시험**이며 stage/active/PID 소비 영수증이 아니다.
- [variant-validation.json](../../tmp/cumulative-adoption-review/variant-validation.json): 26,928개 표현 중 관측 연구 대안 **19,892개**와 W/STOP/TIMEOUT/U 계산 일치, 22개 scope의 선정 성적 일치, 오류 0. 빈 표현 별칭도 포함해 비교했다.

### 4.2 누적 원천 재생

- frozen manifest `b392804a89a3f1ffe2255529008b75ecc525e1e88adba19c7226f998f97607d2`, reviewed 결과 `2a0663bcf24378574d101371855266dd2bd6f9810dc80599f2aae68002eef956`를 고정했다.
- 27개 partition·9개 검사 날짜의 raw 5,587,427행을 대상으로 확인점/원 분기/A root/선정 membership/ask/F 삼치 결과/typed proof를 대조한다. 코드·원천 fingerprint가 다른 checkpoint는 재사용하지 않는다. 원 연구 실패 시도와 수정 전 재생 결과를 보존했다.
- 10/14의 325,775행은 epoch 계약으로 제외되고, 10/15 미입증 epoch도 연구에 편입하지 않는다. 적격은 기존 8개 날짜·3,831,217행이다. 과거 원천 결손을 현재 값으로 채우지 않는다.
- 최종 재생 **PASS, 불일치 0**: native 확인점 236,597개, 추가 root proof 253,758회, F 삼치 대조 329,802회, 선정 확인점 9,502개·신규 typed 선정 proof 9,005회. 27개 원천 SHA를 종료 후 다시 확인했다. 계수·코드 해시는 [native-parity.json](../../tmp/cumulative-adoption-review/native-parity.json), 배포대기 검증 종합은 [readiness.json](../../tmp/cumulative-adoption-review/deploy-wait/readiness.json)이 소유한다.

### 4.3 성능과 한계

- 10/7 두산 PRE 동일 10,000행·2개 branch, 첫 200행을 제외한 CPU 시간: 기존 코드 p50/p95/p99 약 **52.6/303.3/328.1µs**, 최종 코드의 동일 정책 **55.6/333.5/392.9µs**, 새 정제 정책 **65.0/650.1/789.1µs**. [기존](../../tmp/cumulative-adoption-review/benchmark-old.json), [동일 정책](../../tmp/cumulative-adoption-review/benchmark-unchanged.json), [신규 정제](../../tmp/cumulative-adoption-review/benchmark-selected.json).
- 기존 정책의 확인 수 2,052는 동일하다. 새 정제는 2,049다. 최종 동일 정책 대비 새 정제의 p95 CPU 증분은 약 0.32ms이며 peak RSS는 약 45→50MiB다. 실행 시점/동시 작업의 영향이 있는 단일 구간 측정이며, 실제 WS queue·전체 종목 부하를 대신하지 않는다.
- [family 평가 비용](../../tmp/cumulative-adoption-review/assessment-benchmark.json): incumbent family 검증 p95 40.55ms, 새 family 59.39ms, 새 평가·typed projection 59.82ms(22회). 추가 정의/승인 검증 비용도 별도 계측했다. provider 시간과 실제 5초 루프 전체 지연은 이 값에 포함하지 않는다.
- [최종 postclose 계산](../../tmp/cumulative-adoption-review/postclose-benchmark.json): 실제 52,267행 한 partition·6,013개 확인점·27,056개 표현(128개 actual-current 표현 포함), 새 checkpoint 계산 27.78초, 캐시 1.39초. State/raw 재생 0·동일 결과, peak RSS 약 201MiB, 운영 JSON 약 1.12MiB, 비교표 gzip 약 415KiB. 이전 코드의 29.97초/1.46초와 이미 warm한 1.53초/1.25초 시도도 원 로그로 보존했다.
- 콜백에는 새 디스크/API/provider 작업이 없다. 위 결과는 격리 CPU·장후 계산 시험이며 실제 PID queue/WS 지연·AI 응답·주문 처리시간을 입증하지 않는다.

## 5. 배포대기와 이후 수용

- [준비 등록안](../../tmp/cumulative-adoption-review/deploy-wait/prepared-registration.json)은 `prepared_waiting_deployment`, `operator_receipt=null`, runtime/order authority false다. private 준비와 source archive 검증이 운영 pending/current/candidate를 변경하지 않았는지 readiness에 기록한다.
- 준비 기준 publication `2026-10-15`, target `2026-10-16`. 사용자 배포 지시 후 검토된 release commit에서 준비안을 재검증한다. 다른 세션의 새 코드·정책과 통합하고 관련 계약을 검증한다. 원 작업본의 미커밋 변경을 함께 취급하지 않는다.
- 실제 parent가 `1f069c…`와 다르면 CAS를 우회하지 않는다. 새 current의 membership/코드/근거를 재비교하고 successor를 준비한다. 이는 경제성·독립 날짜 대기 gate가 아니라 잘못된 원 정책에 delta를 적용하지 않기 위한 기술 계약이다.
- 승인 후 durable archive intake→machine/auxiliary 동일 세대 stage→정확한 적용일 준비/활성→정상 PID 소비를 각각 확인한다. 자연 branch hit, dedup된 AI 요청, ENTER_NOW→보조→Main→제출/체결/비용 결과는 이후 자연 수용이다. 검증용 주문이나 provider 요청을 만들지 않는다.
- 배포대기 owner는 [현재 체크리스트](../checklists/2026-10-15-stage2-todo-checklist.md)의 `CumulativePolicyAdoptionDeployment1015`다. 준비 산출물과 작업본은 durable intake가 끝날 때까지 보존한다. 외부 Project/Calendar sync는 실행하지 않는다.

## 6. 최종 검토 결과

- 검토 범위 내 미해결 코드 결함 0. 최종 회귀 246개, 누적 27개 구간 재생, 19,892개 관측 대안 대조, native 128개 scope의 구조 검증을 통과했다.
- Python 14개 파일 compile, 소유 문서의 로컬 링크, 신규 owner의 print-only parser 1회 파싱, `git diff --check`를 검증한다. shell 변경이 없으므로 `bash -n`은 해당 없음이다. 최종 숫자/로그 hash는 readiness가 소유한다.
- 준비 등록안 content SHA는 [readiness의 prepared_artifact_content_sha256](../../tmp/cumulative-adoption-review/deploy-wait/readiness.json)에 고정한다. 작은 근거 5개를 private archive로 보존하고 private pending/current는 만들지 않는다. 수정 전 준비안도 superseded 시도로 보존한다.
- 종료 검토 중 운영을 읽은 snapshot은 다른 세션의 `hpsp-peak-outbox-source-recovery-20261015-v1`/`451b6c1ec84fafa563d95381e95c814ac2b2b18b`, 현재 policy는 연구 parent `1f069c…` 그대로였다. 이 작업의 배포/PID 영수증이 아니다. 배포 시점의 코드·parent·원천은 다시 결속한다.
- 상태: **별도 작업본 구현·리뷰·보완·격리 검증 완료 / 배포대기**. 운영 등록·활성화·기동/PID·자연 판정/실현 수익의 수용은 남는다.
