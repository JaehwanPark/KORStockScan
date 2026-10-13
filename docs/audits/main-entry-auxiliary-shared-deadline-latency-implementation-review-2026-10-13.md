# Main 진입 보조판정 공유기한 지연 구현 리뷰 — 2026-10-13

[보완계획](../proposals/main-entry-auxiliary-shared-deadline-latency-remediation-plan-2026-10-13.md)의 구현·리뷰·수정·표적 검증을 완료했다. 아래 최초 구현 검증은 08:58의 코드 검증이며, 승인 후 실제 배포와 새 시간초과 점검은 문서 마지막에 구분해 기록한다. 원 native 5초, 모델·prompt/schema·판정·원천 검증·주문/수량·수탁·회로 계약은 유지했다.

## 구현과 소비 경로

| 범위 | 변경 | 보존·검증 |
|---|---|---|
| Main 방문 | `runtime_performance.record_native_ready`의 기존 wakeup에 128개 이하의 coalesced 방문 hint를 연결하고 `kiwoom_sniper_v2`가 작업 사이에 소비 | 기존 WATCHING 슬롯 안에서만 순서 변경. HOLDING·주문·COMMIT 슬롯과 전체 대상·native claim guard 유지. event/정책 generation 전환과 만료 시 hint 제거 |
| 정책 준비 | `reversal_evaluation_context.prepare`의 짧은 동기 검증에서 하나의 `signature_pass` 공유 | ancestor 탐색만 공유. 각 leaf signature·dependency·current pointer와 끝의 symlink/dir 검증 유지. 검증 실패 시 configuration/consumption cache 무효화. provider I/O와 다음 판정에 pass 공유0 |
| 경제 원천 복사 | 기존 `snapshot_copy` 패키지의 `snapshot_without_fields`를 observer에 연결 | 복사 후 버리던 root `_machine_observation_revision`만 처음부터 제외. 다른 원 입력, root self-cycle·alias·deque·unknown deepcopy protocol 보존 |
| provider payload | 명시적인 entry response schema가 있는 request에서 같은 envelope build 결과 재사용 | request-local cache. prompt/input/model/schema/metadata/tokens/reasoning/temperature/registry 사용 여부 변경 시 재구성. 반환값은 독립 copy. 일반 dynamic schema와 다른 request 사이 cache 공유0 |
| 로컬 계측 | async evaluation의 ContextVar frame → policy/machine/economics/wire/native check/annotation → result·기존 trace/pipeline | nested interval을 합산하지 않도록 표시. clock 실패는 gap counter이며 새 entry veto가 아님. 성공 경로의 기존 response reserve0/250ms는 변경0 |
| HTTP 완료 | executor enqueue/start·SDK start/end·caller timeout·future settlement를 구분 | late settlement는 기존 performance 진단의 bounded128 항목. 원 Future 결과·Main inbox·회로를 변경0. SDK 미시작과 시작 후 전송 불명 유지 |
| 저장 | trace JSON UTF-8 한 번만 encoding; serialization/fsync 시간 분리 | 필수 append/fsync·dedup conflict·partial tail·rotation/압축·index 진전 순서 유지. 새 원장·writer·진단 hard gate0 |
| 회로 health | 회로 관측시각/next-eligible 추정 원천을 생산하고 같은 PID/start consumer에서 관측 나이와 검사 시점 wait를 표시 | raw receipt 보존. 추정값은 admission authority가 아니며 reset/restart·공통 auth/unknown 실패 분류 변경0 |

수정 소유 위치는 기존 `src/engine/monitoring`, `scalping`, `infrastructure`, `ai`, `error_detectors`와 기존 Main caller다. 새 engine-root 파일은 없다. 새로운 테스트는 `src/tests/test_entry_shared_deadline_latency.py`에 두었다. Kiwoom request/parser/FID/REG/REMOVE/auth/continuation과 broker account/order call은 수정하지 않았다.

## 리뷰에서 수정한 결함

1. 제외할 필드를 제거한 임시 dict를 deepcopy하면 root self-reference가 다른 객체로 복제되는 문제를 발견했다. 원 root를 memo에 먼저 연결하는 복사로 보완하고 mutation/alias/cycle 반례를 추가했다.
2. 첫 payload cache는 deepcopy 비용으로 baseline보다 느렸다. immutable scalar와 normalized container의 copy primitive로 바꾼 뒤 같은 byte/소유권/변경 반례와 3회 비교를 다시 실행했다.
3. payload identity와 value를 따로 게시하는 대신 한 tuple로 게시해 다른 build가 불완전한 cache pair를 읽지 않게 했다. `dataclasses.replace`는 cache를 승계하지 않는다.
4. timeout 시 caller 종료를 SDK 종료로 기록하지 않는다. 실제 late SDK end/settled는 동일 request ID의 진단으로만 보존한다. enqueue 전에 만료하거나 queue에서 만료하는 경우도 구분한다.
5. 새 event/정책 namespace로 이전 방문 hint가 넘어가지 않게 했다. 실제 trading context를 바꾸지 않는 metric 실패도 실행 결과를 대체하지 않도록 gap 계수를 추가했다.
6. entry annotation 계측이 다른 endpoint의 결과를 불필요하게 변경하지 않도록 caller 범위를 제한했다. 진단 callback은 provider 결과·회로를 변경하지 않는다.

## 검증

- 최종 통합 **886건 PASS**, 실패0: [로그](../../tmp/entry-timeout-diagnosis-20261013/implementation-verified-final.log). native/main/async·trace·circuit·transport·process health·pipeline·reader compatibility·ordered deployment를 포함한다.
- 경제 observer·초기 수량의 실제 producer/consumer와 신규 소유권 반례 **76건 PASS**: [추가 검증](../../tmp/entry-timeout-diagnosis-20261013/implementation-regression-2.log). 다른 그룹과 겹치므로 합산하지 않는다.
- 수정 뒤 좁은 범위 closure **479건 PASS**: [closure 로그](../../tmp/entry-timeout-diagnosis-20261013/implementation-closure-regression.log). 이 역시 최종886건과 겹친다.
- warning1은 기존 `pandas_ta`의 Pandas4Warning이다. Python compile·`git diff --check`·문서 링크·print-only parser는 [완료 영수증](../../tmp/entry-timeout-diagnosis-20261013/implementation-completion.json)에 기록한다. wrapper 변경은 없어 `bash -n`·설치/예약 변경은 실행하지 않았다.

## 격리 성능 비교와 한계

[동결 입력](../../tmp/entry-timeout-diagnosis-20261013/frozen-input-manifest.json)은 08:07 진단의 실제 요청6건을 원 request/payload/prompt 행의 offset/length/hash와 원 prefix hash로 결속했다. 입력 문자열·prompt bytes를 복원한 요청6건을 사용했고 원천 결손 제외0이다. provider schema는 frozen facts에서 재구성했으며 실제 provider 호출은 없다. 이를 당시 provider의 실제 응답 또는 전체 Main 재생으로 취급하지 않는다.

[최종 비교](../../tmp/entry-timeout-diagnosis-20261013/benchmark.json)는 baseline v6와 최종 candidate를 B/C/B/C/B/C로 실행했다. 각 component100개 작업, 실제 append/fsync, 동일 provider payload와 append 분모를 검증했다. 아래는 각 회차 p95의 중앙값이며 전체 Main p95가 아니다.

| 격리 component | baseline | candidate | 판단 |
|---|---:|---:|---|
| 430행 stock의 복사와 버릴 진단 제거 | 2.820ms | 0.281ms | 3회 모두 개선; 실제 모든 stock의 같은 감소율을 보장하지 않음 |
| 같은 request의 provider envelope 3회 구성 | 0.139ms | 0.095ms | 3회 모두 개선, provider payload 동일 |
| 100개 dependency의 ancestor signature 검증 서비스 | 3.118ms | 2.975ms | 3회 모두 개선; 전체 policy loader 시간이 아님 |
| request capture·필수 파일 저장 | 11.363ms | 11.089ms | paired p95 개선은 1/3회뿐. 저장시간 개선 입증 안 됨 |

100개는 독립 거래 표본이 아니라 동결 fixture를 반복한 측정 작업이다. 실제 저장 행은 각 회차 `payload6 / prompt1 / request100`으로 동일했다. RSS 최대169.2MiB, CPU affinity1개, 메모리 상한1GiB, 임시 파일 약1.85MiB이며 temporary data는 종료 시 제거했다. 전체 AI 비교 원장·data 복제는 없다.

**전체 local p95 1.60초와 자연 timeout 감소는 미측정이다.** 과거0.967/1.498초의 세부 원인은 복원 불가능한 구간을 추정하지 않았고, 새 stage 계측을 소비한 뒤 확인해야 한다. HOLDING/COMMIT 슬롯 보존과 관련 동작은 시험했지만 운영 Main+장후 전체의 결합 성능은 측정하지 않았다. trace 저장의 개선 미입증과 provider 서버/네트워크 지연은 이 코드 리뷰의 성공으로 바꾸지 않는다.

08:58 구현 완료 시점에는 selected v6와 PID에 작업본 변경을 적용하지 않았다. 기존 owner `AuxiliaryCircuitRecoveryRepair1012`, `NonfixedDispatchReadinessReview1012`, `DirectFamilyPreopenPolicyHandoff`의 후속 배포·정책/호환성/code-pin·strict/PREOPEN·실제 PID·자연 수용은 별도 단계다. 검토한 코드 범위의 미해결 finding은0이며 경제성·실주문을 닫은 결과가 아니다.

## 승인 후 재리뷰와 배포 준비

사용자의 배포·재기동 승인 후 두 사항을 보완했다. 네 실행 파일의 변경이 원 제출지연·holding incumbent의 코드 검증과 연결되지 않아 기동이 거절되는 경로를 발견했다. `intraday_release_handoff.REVIEWED_ENTRY_LATENCY_SOURCES`에 검토한 원본→최종본의 정확한 SHA256 쌍만 추가했다. 기존 검토 쌍을 보존하고 원 정책·manifest·env·prepared source를 수정하지 않는다. 다른 bytes·dirty source·다른 원 generation·producer 변경은 계속 거절한다. 또한 실제 executor enqueue clock을 warmup bookkeeping 뒤에 기록해 로컬 준비시간을 queue 대기로 오인하지 않게 했다.

[최종 후속 검증](../../tmp/entry-timeout-diagnosis-20261013/deployment-review-regression.log)은 **553건 PASS**다. 앞선886건과 겹치므로 합산하지 않는다. 원 SDK 종료와 caller timeout 분리, queue clock, 두 검토 목록의 변조/dirty/origin 거절, native handoff·ordered deploy·bootstrap reader·회로·HTTP transport를 검증했다. 기존 격리 benchmark의 성능 수치는 당시 hash의 결과로 보존하며 이 clock 이동을 새 성능 측정으로 취급하지 않는다.

기동 owner의 운영 문서와 candidate checklist를 같은 릴리스에 포함한다. 공유 checklist는 incumbent이 종료될 때까지 보존하고 ordered publisher가 candidate Git bytes를 게시한다. strict에 결속된 원 checklist는 native 역사 snapshot으로 보존하며 경고를 억제하거나 기존 정책 원문을 재작성하지 않는다. 배포는 incumbent 검증→candidate delay-code·auxiliary reader 검증→graceful drain→선택·원 정책 인계→새 PID 검증 순서로 진행한다. 별도 감시 audit는 수정·배포 대상에서 제외한다. 실제 배포·기동과 자연 표본은 아래 후속 증빙으로 별도 기록한다.

첫 후보의 실제 preflight는 native PREOPEN commit에 존재하지 않는 장중 인계 영수증을 요구해 실패했다. 기존 PID·selector·checklist는 변경되지 않았다. 배포기의 incumbent 확인을 실제 PID 소비 검사로 바꾸고, 최초 native 기동의 검증된 live 소비·원 selector·5개 원천 해시를 `native-predecessor.json`으로 보존했다. 종료 후 새 인계는 이 실제 증빙만 검증한다. 이전 장중 consumed 영수증을 만들거나 stopped PID를 live로 주장하지 않는다. ContextVar는 prepare 범위에서만 유효하며 success/failure 뒤 초기화한다. 이후 장중 배포의 기존 consumed 경로도 유지한다. native proof·authority·date/origin·PID·hash·원천 변조·실행 중 predecessor·경로 이탈과 이후 소비를 포함한 회귀검증을 추가했다.

최초 native 릴리스의 Git에는 오늘 checklist 파일 자체가 없다는 점도 배포 전 확인했다. 배포기는 Main 종료 전에 native `preserve_checklist`로 strict 해시에 결속된 현재 bytes를 보존한다. `git show`에 파일이 없을 때도 이 정확한 snapshot을 이용하며 결손/변조된 snapshot이나 수정된 현재 문서로 대체하지 않는다. 이전 코드는 Git 조회 예외 때문에 이 허용된 원천 경로까지 도달하지 못했다.

v3의 실제 전환은 종료·선택 후 `main_stop_confirmation_invalid`로 새 기동을 차단했다. 손절 implementation digest에 진입 원천 복사를 수정한 `sniper_state_handlers` 전체가 포함돼 있었다. 자체 hold·원 selector/checklist·원천 hash·Main 부재를 대조하고 release-set/detector/selection lock 아래 native v6로 복구했다. **09:31 PID2252451**의 정상 소비로 복구됐으며 [복구 증빙](../../tmp/entry-shared-deadline-deployment-20261013/rollback.json)에 기록한다. 미완료 후보를 실제 적용으로 보고하지 않는다.

손절값·원 report/bundle·source generation을 바꾸지 않고, 이미 승인된 incumbent의 runtime reader/preload만 당일 원 manifest·native 소비·정확한 Git source 쌍으로 검증하도록 보완했다. 선택된 숫자 successor와 research/publication의 `verify_full=True`에는 이 예외를 허용하지 않는다. source-gap 행을 새 성과로 바꾸거나 비용/주문 증빙을 만들어내지 않는다. 신규 candidate-stop preflight는 이 오류를 Main 종료 전에 거절한다. 추가 native proof 두 파일은 기존 evaluation context의 dependency identity에도 포함해 변경/삭제 시 consumption cache를 다시 검증한다. 원 정책·bootstrap 원문과 별도 감시 audit는 보존한다.

## v4 배포와 새 시간초과 후속 검증

09:41 ordered 기동 후 `main-entry-deadline-20261013-v4`, commit `ed738749da7598355d909de9eb9b94420d510490`, PID `2273857`/start ticks `10144672`의 실제 소비를 검증했다. machine·auxiliary 128경로와 원 bootstrap/PREOPEN이 PASS다. 원 controller 최종화는 검증된 역사 checklist snapshot으로 재검사했고, EOD/장후 원장·정책을 재생성하지 않았다. v4 최종 코드의 후속 검증은 [732건 PASS](../../tmp/entry-shared-deadline-deployment-20261013/final-all-consumer-regression.log)다. 이전 그룹과 합산하지 않는다.

사용자가 전한 새 PID 시간초과도 실제 발생이다. 새 로그의 source-only `kt00011` 준비 조회와 AI provider 실패를 주문 실패나 인증 실패로 바꾸지 않는다. [8MiB bounded tail의 자금 준비 기록](../../tmp/entry-shared-deadline-deployment-20261013/capacity-followup.json)에는 현재 PID 144건 중 fresh success85, HTTP failed13, exact reused37, scope changed8, expired1이 있다. 각 실패는 실제 전송1회이며 성공 기록도 있어 API 전면 장애라고 결론짓지 않는다. admission 대기와 HTTP를 분리하며 서버 I/O wait·CPU scheduling·증권사/네트워크 원인을 하나로 단정하지 않는다.

공식 키움 현재 main은 `953e5dbff123f437ab4d11a78a95191a685eb51f`, 조회시각 `2026-10-13T01:01:19.426295+00:00`이다. `kiwoom_docs`는 없다. `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 kt00011, `kiwoom/core/client.py`, Postman의 PRD/MOCK·body 변환을 확인했다. POST `/api/dostk/acnt`, api-id `kt00011`, raw stock code, `uv` 원 단위·Bearer/continuation 계약은 현재 요청과 일치한다. [공식 revision·파일 hash](../../tmp/entry-shared-deadline-deployment-20261013/official-kiwoom-reference/revision.json)를 보존한다. 키움 request/parser/retry/auth/timeout와 5/4-reserve rate 계약은 이번 후속에서 변경0이다.

09:56 HPSP exact request의 `analyze_target` 전 처리1.637초 중 최종 native check622ms를 확인했다. 두 검증의 실제 guard는 유지하면서 `reversal_evaluation_context.validate_before_provider`가 짧은 독립 `verified_evaluation`/`signature_pass`에서 loader-owned immutable view를 사용하도록 보완했다. 전체 2,663,653-byte family를 read-only 검사 전에 다시 mutable로 복제하던 작업만 제거한다. 기존 family·configure·claim·requested refs·registry/model·overlay/revocation 검사와 exit current-pointer/symlink 검사 모두 실행한다. 이 view/pass는 provider 호출·응답 소비로 전달하지 않는다. 기존 response/Main/submit 재검증도 그대로다.

`entry_native_check`는 최종 guard 전체 구간으로 기록하고 load·claim·auxiliary를 자식 구간으로 나눴다. 새 exact source 쌍은 `REVIEWED_ENTRY_BOUNDARY_SOURCES`에 추가했으며 v4와 이전 immutable 소비 쌍을 보존한다. 모델 불일치·native 종료·refs 변경·overlay 철회·exit 검증 실패에서도 provider 전에 종료하고 context를 해제하는 v5/v6 반례를 확인했다. [후속 producer/consumer 검증](../../tmp/entry-shared-deadline-deployment-20261013/final-boundary-consumer-regression.log)은 **776건 PASS**다.

[격리 static 부분 비교](../../tmp/entry-shared-deadline-deployment-20261013/final-boundary-static-benchmark.json)는 같은 현재 bundle, family 검사2회·구성 결과 digest 동일, 각 arm25개 작업·B/C 3회다. p95 중앙값은164.21ms→129.95ms, 세 쌍 모두 개선했다. CPU affinity1개·RSS71.4MiB·memory cap1GiB, provider/order/policy writes0. 이는 native claim·filesystem·SDK·Main을 제외한 static 부분 결과이며 전체 local p95 또는 자연 timeout 감소를 입증하지 않는다. 원150ms source read, 계좌/가격/수량·2초 entry receipt·필수 trace fsync는 유지한다. 실제 SDK 응답이 남은 기한보다 길면 여전히 timeout으로 종료한다. 반복 알림을 숨기는 수정은 없다.
