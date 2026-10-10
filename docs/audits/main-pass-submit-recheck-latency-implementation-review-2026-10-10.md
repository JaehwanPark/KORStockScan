# Main PASS 제출·인수·진단 지연 구현 리뷰 — 2026-10-10

## 범위와 결정

사용자 지시로 [S1–S4 계획](../proposals/main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md)을 구현하고 source→consumer를 반복 리뷰·보완했다. 실행 owner는 [10/10 checklist](../checklists/2026-10-10-stage2-todo-checklist.md)의 `MainPassSubmitRecheckLatency1010`이다. 기존 미커밋 계획 2개를 보존했다. 최초 구현 검증에서는 배포·재기동·정책 재선정·AI 연구 호출·장후 원장 재생성·Project/Calendar sync를 실행하지 않았다. 후속 승인 배포는 아래 별도 절에 기록한다.

Plan Rebase §1–§8 및 `korstockscan-review-gate`를 적용했다. 신규 engine-root 모듈이나 별도 production worker는 없다. Kiwoom 요청/응답 parser·FID·인증·REG/REMOVE·account/order wire 및 continuation은 변경하지 않았다. 주문 adapter 앞의 원 deadline·중복 소비 검사는 로컬 실행 계약이며 공식 API reference 재취득이 필요한 protocol 변경은 이번 범위에 없다.

## 구현과 반복 리뷰에서 닫은 결함

| 범위 | 수정한 producer→consumer 계약 |
| --- | --- |
| S1 인수 소유권 | coordinator take가 결과를 제거하는 순간 호출별 ContextVar에 원 객체를 보관한다. WATCHING resolver부터 후속 처리까지 finally로 연결하며 검증/native ack 예외도 원 결과로 종료한다. accepted는 ack·필수 상태 변환 이후에만 기록한다. |
| S1 폐기 caller | target/transport/enqueue 거절·분기 종료·unused·orphan·invalidate·overflow·shutdown을 원 객체 종료로 연결한다. cleanup은 ENTRY_LOCK 안에서 generation/key/token을 비교한다. 이전 결과로 후속 필드를 지우거나 recheck/park하지 않는다. native ack 실패는 재시도하지 않고 최초 예외를 보존한다. |
| S2 직접 사유 | WATCHING과 실제 제출 함수의 기존 반환 지점에 직접 이유·intent·응답·물리 호출 사실을 연결한다. 마지막 임의 로그를 차단 원인으로 사용하지 않는다. bool 반환과 기존 caller를 유지하고 legacy False 횟수와 adapter 호출 횟수를 분리한다. |
| S2 원천 신원 | coordinator request/PID/start ticks/original deadline/order route를 local AI capture와 trace에 보관한다. Provider 16-field metadata 한도로 원 연결이 사라지지 않게 local capture를 보완했다. wire metadata·prompt/model/retry는 변경하지 않았다. frozen 원 payload의 machine/auxiliary hash와 원 market route를 사용한다. |
| S2 집계 | monitor가 trace/attempt/generation/native/symbol/route/policy/deadline 충돌 및 후단 물리 사실 충돌을 unobservable로 처리한다. 검증된 PASS projection으로 전이가 없는 PASS를 드러낸다. tail·unmapped·projection 결손은 partial이며 과거 snapshot의 as-of를 재작성하지 않는다. |
| S3 전달 | ready 게시·completion wake를 report-only writer 접수보다 앞당겼다. 기존 단일 관측 executor와 3개 caller 모두 유한 queue를 사용한다. running 포함 1,024건/4MiB, 개별 64KiB이며 동기 fallback·새 worker는 없다. 전체 AI payload/mutable stock을 queue에 보관하지 않는다. |
| S3 관측 저장 | queued와 실제 append를 구분하고 health에 대기·포화·실패·append 미확인을 기록한다. hot failure는 동기 로그를 쓰지 않는다. 종료 drain은 최대 1초, timeout은 결손이다. 실제 저장 회귀에서 판정 종료/commit stage의 compact registry 누락을 발견해 기존 entry_mechanical_momentum family의 lossless 경로로 등록했다. 원 event identity·compact source fingerprint를 보존한다. |
| S3 stock 격리 | 원 결과 객체/sink는 호출별 context에만 두고 stock에는 작은 scalar 사실만 둔다. worker snapshot에서 임시 guard를 제외한다. opening-rotation 공통 API와 후속 snapshot/deepcopy로 queue lock/result 객체가 유출되지 않는다. |
| S3 trace index | 검증 offset과 조립 bytes를 분리하고 4MiB 여러 step으로 큰 완결 행을 준비한다. writer/reader 32MiB 행 한도, 전체 partial 64MiB·32 index 한도다. 동일 세대 partial을 반복 읽지 않고 다른 index를 계속 준비한다. rotation/축소/rewrite/조립 접두 변경은 이전 cache를 무효화한다. 세대 변경 후 조립 bytes 전체를 bounded하게 재검증하고 concurrent checkpoint 변경도 거절한다. |
| S4 실제 제출 | outer drain→take→실제 WATCHING→실제 제출 함수→receipt/price/sizing/final guards/intent→adapter spy를 연결한다. fixed/scanner × compact-v1/v2 × 정상/응답 없음/예외/최종 deadline의 16개 조합을 검증한다. 새 AI 호출은 금지 fixture로 검사한다. |
| S4 추가 결함 | 응답 없음/예외 후 cached PASS로 재호출되는 경로를 발견했다. exact attempt/trace의 물리 호출 소비를 보관해 재전송을 차단한다. adapter 직전에도 원 epoch/perf deadline을 재검사하며 이미 기록된 intent를 삭제하거나 broker 응답을 합성하지 않는다. 다중 leg의 기존 허용 순서는 보존한다. |

원 5초·quote/source/native·AI·broker/account/quantity/cooldown·Main/manual/retired custody·hard/protect/emergency guard를 보존했다. initial 등록·승률/EV·실제 체결 수에 새 승인 조건을 추가하지 않았다. opening-rotation 완료 context는 비실행 소비 종료이며 새 entry 권한을 부여하지 않는다.

## 오프라인 성능 비교

기준 commit `58c2a7c6e8aa4d54e9d5b2a47533a58b4f30713c`의 실제 coordinator/index와 후보를 같은 입력으로 번갈아 3회 비교했다. [script](../../tmp/main-pass-submit-recheck-20261010/benchmark.py), [개별값·분위수·SHA·bytes·실패 분모](../../tmp/main-pass-submit-recheck-20261010/performance.json), [실행 로그](../../tmp/main-pass-submit-recheck-20261010/performance-run.log)에 기록했다. 표의 시간은 **각 실행 전체 전달 시간의 3회 중앙값**이다.

| 부하 | N/회 | 기준 → 후보 | 결과 |
| --- | --- | --- | --- |
| 정상 | 32 | 261.943 → 185.142ms | 약 29.3% 단축, 양쪽 만료/미완료 0 |
| 동시 완료 | 32 | 60.596 → 49.021ms | 약 19.1% 단축, 양쪽 만료/미완료 0 |
| 진단 writer 200ms, 원 잔여 100ms | 8 | 1668.505 → 44.256ms | 기준 8/8 만료 → 후보 0/8, 3회 동일. 진단 drain 약 1.6초는 남음 |
| 필수 저장 200ms, 원 잔여 100ms | 8 | 1668.493 → 1646.010ms | 양쪽 8/8 만료, 3회 동일. 필수 저장/deadline 보존 |
| cold 128개 작은 행 | 128 | 양쪽 약 1ms | 읽기 38,162bytes 동일, 양쪽 3/3 ready |
| 4MiB 초과 합성 완결 행 | 1 | 읽기 12,582,912 → 4,195,364bytes | 기준 3/3 미완료 → 후보 3/3 ready. 후보 실제 parse 약 11ms |

정상/동시 후보 finish p95는 0.087–0.196ms, 기준 2.918–7.205ms다. 후보 queue 최대 31,371bytes·22건, 실패/미완료 0. 양쪽 필수 response/outcome 2N 행과 진단 N 행을 보존했다. 추가 identity fields로 정상 회당 write는 약 47.5→51.5KiB다. 실제 emitter 정상 부하 32개의 원문/compact 전이 유실 0도 별도 회귀로 확인했다.

fixture는 실제 coordinator/commit validator/index와 임시 파일 필수 fsync를 쓰며 진단 callback을 제어한다. live Provider·full Main 보호/holding callback 실시간 지연·broker 성공·체결·경제성은 측정하지 않았다. 진단 I/O 비용을 제거했다는 의미도 아니다. 원 4.999/5.000/5.001초 epoch/perf 경계는 결정적 회귀로 검사했다. small-N p99/max는 설명용이며 새 배포 차단선이 아니다.

## 검증과 남은 수용

최종 코드를 고정한 19개 suite 결과를 [최종 회귀 로그](../../tmp/main-pass-submit-recheck-20261010/final-tests.log)에 기록한다. 실제 제출 내부/AI transport/trace/monitor/coordinator/관측 worker/price/sizing/broker safety/보유·청산/compact producer·backfill/Sentinel/위치 gate를 포함한다. 오래된 fixture의 퇴역 import와 현행 source-only capacity 인자를 정정했고 production validator를 우회하지 않았다.

최종 고정 코드 **19개 suite 2,424 passed / 139.65초**, 기존 Pandas4Warning 1건이다. 반복 리뷰에서 발견한 범위 내 미해결 구현 결함은 없다. **변경 Python 19파일 compile, 로컬 파일 링크 93개 결손 0, print-only parser 20항목·경고 0, 10/12 handoff owner 1개, git diff --check PASS**다. [원천 SHA·봉인 보존·검증 결과](../../tmp/main-pass-submit-recheck-20261010/final-validation.json), [parser 결과](../../tmp/main-pass-submit-recheck-20261010/print-backlog.log)에 기록했다. wrapper 변경이 없어 bash 검증을 제외하며 전체 repository pytest는 실행하지 않았다.

초기 sizing 연구 digest 오류는 코드 편집과 isolated subprocess 회귀가 겹친 실행에서 관측됐다. 당시 adapter 오류의 세부 원인을 확정한 근거로 쓰지 않는다. 최종 코드 고정 실행에서는 원 validator와 실제 isolated replay가 모두 통과했다. fixture에 adapter_error를 직접 확인하는 assertion도 추가했으며 digest 검사를 완화하지 않았다.

합성 데이터는 TemporaryDirectory로 삭제하고 작은 script/JSON/log만 보관한다. 신규 AI 호출·대형 원장 복제는 0이다. 10/9 checklist SHA `8eb45bab1300fdd67953739408fa60e7691c8e61afbaf4a5e999dd70055d462d`, 봉인된 10/12 SHA `9e7d9f001a13cfac3b0fbd566bcfa860bd598ce41a9d1280437dcccaefff40a3`를 보존했다. 이후 승인 배포 시 최신 release/PID·정식 policy/PREOPEN binding을 다시 확인하고, 10/12 기존 DirectFamilyPreopenPolicyHandoff의 자연 수용에서 관측된 PASS만 추적한다.

## 후속 재리뷰·승인 배포 및 다음 영업일 준비

10/10 후속 사용자 승인으로 take/finally·native ack 예외·후속 claim 보존·cached PASS 재제출·원 deadline·직접 종료 사유·관측 큐/compact 소비·trace index 세대 경계를 재리뷰했다. 추가 미해결 범위 내 코드 결함은 없었다. 같은 고정 코드의 [배포 전 재회귀](../../data/report/main_pass_submit_deployment/2026-10-10/rereview-tests.log)는 **2,424 passed / 139.44초**, 기존 Pandas 경고 1건이다. 새 불변 릴리스의 [기동·최종화·퇴역·PASS 경계 7개 suite](../../data/report/main_pass_submit_deployment/2026-10-10/release-tests.log)는 **326 passed / 9.25초**다. 두 결과는 중복을 포함하므로 독립 표본 합계로 집계하지 않는다.

- [불변 build](../../data/report/main_pass_submit_deployment/2026-10-10/build.json): `main-pass-submit-20261010-v1`, commit `b26aae701314d91a75056fac576b5f460beb3c06`. 별도 Git index와 release 참조로 검토한 변경을 포장했으며 canonical HEAD/index/작업본을 지우거나 되돌리지 않았다. 공유 docs의 이후 완료 기록은 runtime source 변경과 구분한다.
- [소스/정책 격리 검증](../../data/report/main_pass_submit_deployment/2026-10-10/isolated-check.json): runtime 1,072개 파일과 작업본 일치, 선택 가능한 clean source. 10/12 기존 기계·보조 policy bundle `5038d3aa4d11e3285f51ea4c876d15ba2d14b48f5502b4ab8a247ac89cb16cc1` 및 정책 계약 module hash가 일치한다. 따라서 code-refresh 후보를 재발행하지 않고 원 정책/장후 summary/controller/10/9·10/12 checklist를 보존했다.
- 공통 deployment/selection lock에서 실행 중 Main·장후 계산 worker 부재와 원 selector를 재확인한 뒤 [새 selector](../../data/report/main_pass_submit_deployment/2026-10-10/selection-after.json)를 원자적으로 게시했다. Main은 휴장일 수동 기동하지 않았다. 이전 selector와 준비 index·web pin 사본을 보관했다.
- 웹의 실제 pin이 이전 `main-integrated-bottlenecks-20261009-v1`에 남아 있던 운영 불일치를 수정했다. 같은 승인 배포에서 web pin을 새 릴리스로 맞추고 재기동했다. 실제 PID **22143**, ubuntu, `/proc/PID/cwd`·commit 일치, HTTP **200**이다.
- [PREOPEN 새 준비](../../data/report/main_pass_submit_deployment/2026-10-10/prepared.json) 및 [전체 재검증](../../data/report/main_pass_submit_deployment/2026-10-10/prepared-verification.json): source 10/8 → target 10/12, 새 selected commit, `prepared_verified`·`current_full_contract=pass`·findings=[]다. active env·policy pointer·실제 PID receipt는 발행하지 않았다.
- [최종 준비 확인](../../data/report/main_pass_submit_deployment/2026-10-10/final-readiness.json): 기존 10/8 finalization DONE의 실제 chain/snapshot/strict/checklist 세대를 새 코드로 다시 검증해 issues=[]이며 `strict_checklist_generation_stale`가 없다. 기존 10/9 23:03 완료를 재검증한 것이며 오늘 finalization을 새로 실행했다고 주장하지 않는다. EOD·AI 비교·연구·장후 원장 재생성은 없다.
- [release-set](../../data/report/main_pass_submit_deployment/2026-10-10/release-set.json), [cron 8개](../../data/report/main_pass_submit_deployment/2026-10-10/cron-routing.json), [10/12 PREOPEN route](../../data/report/main_pass_submit_deployment/2026-10-10/preopen-routing.json), [Main route](../../data/report/main_pass_submit_deployment/2026-10-10/start-routing.json) PASS. cron active·KST·시간 동기화, startup hold 부재, native custody identity 유효, 퇴역 unit 복원 0을 확인했다. launcher/router/PREOPEN wrapper `bash -n`도 통과했다.

현재 검증 범위에서 **10/12 07:35 PREOPEN·07:55 Main 예약기동 준비는 정상**이다. target day의 실제 PREOPEN 활성화·Main PID 소비·WS/provider 연결·PASS/주문/체결은 아직 발생하지 않았으며 기존 `DirectFamilyPreopenPolicyHandoff`에서 자연 확인한다. 준비 PASS를 미래 외부 연결이나 자연 수익의 보장으로 쓰지 않는다. 실제 provider/주문 호출, 알림 수동 발송, 외부 Project/Calendar sync는 실행하지 않았다.
