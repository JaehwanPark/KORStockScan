# Main 반복 검증·Sentinel I/O 구현 리뷰 — 2026-10-13

## 범위와 승인

사용자가 [개선계획](../proposals/main-io-contention-and-repeated-validation-remediation-plan-2026-10-13.md)의 리뷰·보완·구현·반복 코드리뷰와 배포·재기동을 승인했다. 실제 incumbent `932bb3a1294e3e5b318cdb565fefa87f11d6e28b`에서 격리 worktree를 만들고 다른 사용자 변경을 보존했다. 정책·PREOPEN·원5초·가격/계좌/주문/수량·Main/manual custody·episode/widget 퇴역을 유지한다.

## 구현과 리뷰 보완

- IO0: 물리 block/partition 중복 제거, 첫 표본/장치 교체는 null, PID birth·부모/owner와 논리/물리I/O·RSS·major fault, swap/PSI·await/queue. sampler 전체 구간을 잠가 동시 state race를 제거했다. 실제 Main은 선택 receipt와 cwd를 확인하고 start ticks를 직접 기록한다.
- IO1: historical health observer만 native full 검증 성공 세대를 process-local로 재사용한다. metadata/목록 변경·같은 크기 edit·누락/alias/late·날짜/코드 변화는 무효화한다. native 검증 전후 세대 확인·single-flight·실패300초 backoff·bounded lock을 적용했다. 임의 경로의 valid tree가 signature 밖으로 나가는 결함을 보완해 비표준 tree는 full을 유지한다. startup/prepare/public CLI는 full이며 exact source pair로 code handoff를 제한한다.
- IO2: SQLite 완결 offset/행/세대 transaction, source position 보존, lossless field payload와 작은 metadata 분리, 지연 decode와 bounded cache, 전체 필드 tuple 적재 없는 정확한 중복 비교, 동일 population/code/window 집계 재사용. native stage attribution/가장 가까운 scope/late terminal은 그대로 계산한다. 작은 summary projection은 Sentinel만 opt-in한다.
- IO2 실패 복구: 외부에서 바뀐 미검증 cache를 지우던 첫 시도의 결함을 수정했다. optional index 실패 전에 정상 cache metadata를 봉인해 재시도 때 중복 append를 막았다. payload/index corruption은 실패하며 optional 계산 memo 쓰기 실패는 native 결과를 유지한다. source cache 자체가 append와 metadata commit 사이에 중단되면 원본을 보존하고 실패한다.
- IO3: 로그 tail을 뒤에서64KiB씩 읽어 필요한 줄만 decode한다. UTF-8 경계·회전 marker/현재 run 판정은 유지한다. WS transport payload 재설계는 지배 잔여 비용이 입증되지 않아 조건부 후속으로 유지한다.
- IO4: 큰 frozen 성능 검증은 한 worker씩 nice/ionice로 실행했다. Main/사용자 작업을 중단하거나 우선순위/인프라를 변경하지 않았다.

## 검증 상태

검증 증빙은 `tmp/io-remediation-20261013/`에 보존한다. 실제 cache420,430행과 두 날짜 summary를 고정하고 기존/후보 전체 report JSON을 비교한다. 기준선은136.323초·2743.99MiB·논리 읽기2,155,628,211 bytes, 전체 출력1,747,296 bytes다. 첫 필드별 압축 시도는194.964초·2888.31MiB로 악화하여 채택하지 않았다. 후속 두 구현도 메모리/CPU 비용이 남아 자체 benchmark를 중단하고 원인을 보완했다. 최종 cold/warm 결과와 표적 시험·배포/PID receipt는 아래 완료 절에 기록한다.

## 자연 수용

당일19시 이후 Sentinel 정규 슬롯이 끝났으므로 cron3회와 다음 정상 Main 신호의 지연/guard 수용은10/14 기존 OPEN owner로 남긴다. frozen parity·코드·배포·실제 PID 소비는 각각 별도 증거다. 수익 개선·실주문 성공은 이 I/O 수리의 완료 조건이 아니며 미관측 성과를 만들지 않는다.


## 배포 전 최종 검증

- native bootstrap/delay/source ledger·observer·Sentinel·artifact freshness·cron·ordered handoff 표적 시험 **1,226 passed (107.93초)**. 마지막 짧은 scope/identity 필드 projection을 포함한 Sentinel 영향 시험은 **209 passed (5.24초)**. 후자는 전체 시험과 중복되므로 합계를 고유 시험 수로 표현하지 않는다.
- 실제10/12 정책에 첫 native 전체 검증1회 후 observer5회를 수행했다. 첫 검증12,937.661ms/논리3,051,402,308 bytes/물리3,043,221,504 bytes. warm5회는7.652~7.758ms, 각논리103,604 bytes·물리읽기/쓰기0, full_count1 유지다. 원 full/startup 경계를 단축하지 않았으며 이것은 해당 stage의 격리 검증이지 전체 Main 비용이 아니다.
- 단계별 성능 회귀를 기록했다. 첫 압축 방식은 baseline보다 악화했고, lazy field만 둔 시도는480초에 중단됐다. 프로파일의 `_blocker_label`/identity 반복 복원을 줄인 후보는cold201.970초/766.81MiB, warm28.348초/719.02MiB로 전체 보고서 SHA가 기준과 일치했다. 이어 metadata 압축·중복 count scan 제거와 lazy payload 손상 후 재생성 결함을 보완했으며 최종 frozen 비용은 완료 절에 기록한다.
- 실제 기계/보조33 contract module은 incumbent와 동일하며, delay/stop exact source-pair pre-stop 및 보조128scope 검증이 통과했다. 신규 provider·주문·원 정책 재선택은 없다. 실제 릴리스와 PID는 ordered 전환 완료 후 별도 검증한다.
- print-only parser24항목, 연결된3개 stable owner 각1개, AUTO 봉인 bytes 동일. 변경 Python compile과 diff 공백 검사를 수행한다. wrapper/cron은 변경하지 않아 별도 shell 수리는 없다.

## 최종 동일 입력 성능과 의미 검증

producer summary 두 개를 작은 별도 파일로 복사해 고정했다. canonical cache/summary는 변경 없이 세대 signature를 전후 대조했다. `frozen-producer-manifest.json`, `sentinel-{baseline,candidate,warm}-benchmark.json`이 입력·코드·측정 증거다. OS page cache를 비우지 않았고 물리 읽기0은 디스크 요구량0의 일반적 보장이 아니다. cold는 새 파생 색인 생성, warm은 같은 색인/집계의 재사용이다.

| 구간 | wall | peak RSS | 논리 읽기 bytes | 물리 읽기 bytes | 물리 쓰기 bytes |
|---|---:|---:|---:|---:|---:|
| 기존 reader |95.548초|2798.96MiB|2,152,933,122|2,137,272,320|1,753,088|
| 후보 최초 색인 생성 |159.370초|858.36MiB|4,444,851,370|1,112,006,656|1,207,599,104|
| 후보 동일 입력 재사용 |18.492초|808.56MiB|445,630,521|0|1,798,144|

- 전체420,430행, report1,747,296 bytes, report SHA `a37154a6daf9c14667b7bd2a50d1b2a09458ac10c0dad6dee429f81ecc11fd77`가 세 실행에서 일치한다. count 일부만 비교하거나 source-gap/null을 지우지 않았다.
- warm wall80.6%, peak RSS71.1%, 논리 읽기79.3% 감소다. wall≤60초/RSS≤1GiB 목표는 충족한다. 읽기80% 목표는0.7%p 미달하며 완료 PASS로 바꾸지 않는다. 파생 색인 약1.12GiB와 cold 추가 비용을 포함해 운영 수용한다. 전체 원천/cache 보존 및 날짜별 파생 색인의 운영 보존주기는 기존 보존 owner의 후속이며,32개/64MiB 한도는 집계 memo에만 적용된다.
- native confirmation 별도 검증:128 scopes·76,800 ticks·614 hits의 signal SHA가 기존/후보 동일하다. provider 호출/실주문은0이다.
- 계측 부하2회: 기존 wall14.9~15.9ms/CPU1.14~1.37ms/기록1.85KiB 내외, 후보24.9~25.3ms/CPU2.52~2.81ms/기록3.7~4.0KB다. 표본2개의 격리 측정이며 p95 추정이 아니다. 종료된 Main은 `unobserved`로 기록했고0비용으로 표시하지 않았다.

## 10/13 최초 적용 시도와 배포 보류 기록

- 코드·시험·문서는 실제 incumbent932bb 위에 격리했으며 immutable candidate와 source hash를 `release-build.json`에 봉인한다. 운영 checklist는 원본/봉인/검토 편집본을 따로 보존하고 실제 전환 때 발행한다. 나머지 작업공간 반영과 workspace 소유 sampler 자연 실행은 `workspace-published.json`/`sampler-live-validation.json`로 별도 기록한다. selected runtime 전환이나 Main 소비로 해석하지 않는다.
- 배포 직전 Main PID3517912는 이미20:00 장 마감으로 종료했다.21:18:12 threshold postclose는 `initial_entry_quantity_refresh`의 `research_resource_admission_timeout`으로 실패했고 controller·tuning은 같은 이전 릴리스에서 선행 복구 대기 중이다. 원인 확인은 로그/프로세스와 현재 stage 상태만 읽었으며 이 실패를 I/O 변경의 결과라고 단정하지 않는다.
- `korstockscan-review-gate`의 활성 wrapper 코드/산출물 보존, `runtime-release-routing.md`의 활성 wrapper 중 selector 전환 금지, native ordered driver의 실제 predecessor 조건을 따른다. selector·당일 policy pointer·익일 candidate·PREOPEN과 운영 checklist 봉인은 아직 변경하지 않는다. 배포·재기동 승인은 유지되지만 **배포 및 새 Main PID 소비는 미완료**다.
- 후속은 기존 `DirectFamilyPreopenPolicyHandoff`: 장후 owner의 실패 복구/terminal 및 wrapper 부재 확인 후 실제 날짜·정책/후보·selection을 재고정하고 native 배포/기동을 수행한다. expired 당일 handoff나 종료 PID를 live로 바꾸지 않는다. `NonfixedDispatchReadinessReview1012`/`AuxiliaryCircuitRecoveryRepair1012`는 다음 정규 cron3회와 Main 자연 신호의 분모·지연을 확인한다. 장후 전체 재계산, 외부 sync, provider/주문, 인프라 변경, WS 재설계는 수행하지 않았다.

## 10/14 장후 완료 후 배포

최종 결과: `373d5f10f` 배포 후 controller whole-chain DONE, 새 prepared 생성, 기본 full `verify_prepared` PASS(`current_full_contract`, findings 0)를 확인했다. 05:35 최종화·07:35 PREOPEN·07:55 Main 정규 기동의 라우팅은 검증했으며 실제 PID 소비와 자연 I/O 수용은 해당 실행 이후의 기존 OPEN이다. 아래 과정의 최종 증거는 연결된 감사 문서와 `tmp/io-postclose-deployment-20261013/completion.json`에 기록했다.

사용자의 장후 완료 후 배포 지시에 따라 Main 성공·whole-chain controller DONE/strict PASS·tuning 성공과 해당 프로세스 종료를 확인했다. 최종 수리 `5cffbc22a` 위에 I/O 변경을 합친 `373d5f10f3aecf2c31e5a6b8864080e6760c2263`를 선택했다. 결합 시험 202 PASS, 정책 계약 33개 동일, auxiliary 128 scopes PASS다. 활성 policy pointer는 불변이고, 10/14 미활성 후보의 behavioral family를 보존한 native code binding을 수행했다. 실제 전환과 다음 기동 준비 결과는 [장후 배포·기동 준비 감사](main-io-postclose-deployment-and-next-session-readiness-2026-10-13.md)가 소유한다. 원 10/13 delay 계약을 변경 코드로 재발행한 뒤 새 summary/consumer/controller/prepared를 검증하며, 이전 준비 receipt를 새 코드의 PASS로 사용하지 않는다. 야간에 새 Main을 시작하지 않고 07:35 PREOPEN·07:55 정규 기동의 실제 PID 소비를 기존 owner에 인계한다.
