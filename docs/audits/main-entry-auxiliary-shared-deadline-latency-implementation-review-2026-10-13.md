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

## 최종 v5의 실제 소비와 잔여 자연 수용

10:13:19 ordered 전환 PASS: `main-entry-deadline-20261013-v5`, commit `d2eeb4b4ee1d2df8b5607651c55b66887a00a8e9`, PID `2343133`, start `10331968`, cwd selected release `/src`다. 원 Main 종료10:12:20.558→selector 게시10:12:20.573→prepared/native handoff→새 PID 검증 순서를 지켰다. 시작 hold 해제·정상 heartbeat와 machine/auxiliary 128경로를 확인했다. 원 정책 bundle·10/12→10/13 generation·5초·가격/자금/수량·custody는 보존했다. [완료 증빙](../../tmp/entry-shared-deadline-deployment-20261013/deployment-completion-v5.json)과 [읽기 전용 health·원 controller 재검증](../../tmp/entry-shared-deadline-deployment-20261013/post-deploy-v5-health.json)을 분리했다. 원 controller issues0; process/resource는 검사 당시 PASS이고 cron은 과거06:50 이후 복구 경고를 보존한다. 원 strict/PREOPEN·최종화나 EOD/장후 정책을 재생성하지 않았다.

이후 실제 자연 수용은 완료되지 않았다. 초기 [performance snapshot](../../tmp/entry-shared-deadline-deployment-20261013/successor-v5-performance.json)의 첫 루프 제외28회 중5초 초과2회, p95 7.217초·최대19.102초다. `loop_work_warm` 이름은 첫 루프 제외를 뜻하므로 완전한 steady-state/cold 분리 결과로 사용하지 않는다. [8MiB 제한 trace 대조](../../tmp/entry-shared-deadline-deployment-20261013/successor-v5-natural-trace.json)에서는 새 PID 실제 AI trace0건으로 provider timeout 개선을 평가할 수 없다. 별도 `buy_funnel_sentinel` 보고 프로세스 RSS 약3.3GiB도 관측했고 이는 동시 부하 근거일 뿐 Main/키움/AI 지연의 단독 원인 증명이 아니다. 현재 감시·보고 작업을 임의 종료하거나 trading 기한·guard를 늘리지 않았다.

검토한 코드 finding0은 776건 회귀검증과 위 source-exact 배포 범위에 한한다. 모든 외부 응답 실패와 모든 성능 목표의 해결을 뜻하지 않는다. 기존 `AuxiliaryCircuitRecoveryRepair1012`가 같은 attempt의 실제 로컬·SDK·Main clocks, kt00011 전송/실패/정확 재사용과 정상 recovery를 이어서 수용한다. `DirectFamilyPreopenPolicyHandoff`, `NonfixedDispatchReadinessReview1012`는 현재 parser에서 각각1개의 OPEN owner이며 생성/기동만으로 자연·경제성 완료를 체크하지 않는다. Python18개 compile·문서73 links·diff 검사와 print-only parser23개 항목을 검증했다. 별도 연구 audit/계획은 보존했으며 provider 강제호출·새 주문·패키지 변경·원장 복제0이다.


## 10:25 이후 시간초과·저장 증가·보고서 지연의 재리뷰

v5 PID2343133의 새 실패를 [정확한 요청 기록](../../tmp/entry-shared-deadline-followup-20261013/exact-trace-excerpts.json)과 대조했다. Alteogen의 `aims-81a53134df65fe7ae4de`는 provider 전0.871초·HTTP budget2038ms/실제1999ms, `aims-82e9be014566e2026064`는 provider 전1.220초·HTTP budget836ms/실제1033ms다. HTTP lock 대기는0이다. native claim 확인 자체도221/288ms였고 경제 준비·policy/input/capture 비용이 따로 남는다. 원5초 안에서 provider 응답이 완성되지 않은 실제 실패이며 인증/주문 실패로 바꾸지 않는다. source-only kt00011의 실제 전송과 backoff에서 전송하지 않은 조회도 구분한다. [공식 키움 revision 재확인](../../tmp/entry-shared-deadline-followup-20261013/official-kiwoom-recheck.json)은 기존 `953e5dbff123f437ab4d11a78a95191a685eb51f`와 같다. 요청·parser·auth·rate·timeout은 변경하지 않았다. 공식 [OpenAI 지연 안내](https://developers.openai.com/api/docs/guides/latency-optimization)는 측정과 불필요한 처리 축소의 참고이며, 모델/prompt/schema 변경 또는 입력 기한 연장 근거로 사용하지 않았다.

[저장 census](../../tmp/entry-shared-deadline-followup-20261013/storage-census.json)에서 오늘 pipeline 약3.52GiB, threshold 약1.69GiB와 AI trace 약0.59GiB를 확인했다. 이는 10:37 snapshot이며 이후 증가했다. AI 비교 store 약3.1GiB를 매 요청마다 새로 복제한 상황은 아니다. `scalp_entry_action_decision_snapshot`의 약2.86MB 행에는 경제 seed와 operating context가 같은 frozen policy/code 문맥을 반복한다. canonical pre-AI economic event와 AI trace를 소비하는 replay는 원본을 계속 유지한다.

- 반복 ADM snapshot은 성공한 canonical append 영수증·64자리 capsule SHA·정확 attempt가 있을 때만 두 대형 문맥을 기존 원본의 attempt/hash 참조로 치환한다. canonical decision 객체는 변경하지 않는다. 실패/누락 append는 원래 문맥을 남긴다. raw 전체의 row나 판정 기록을 삭제하지 않는다.
- Buy Funnel은 경제 증빙 projection을 먼저 계산한 뒤 진단에 쓰지 않는 두 문맥만 cache에서 제외한다. 과거 projection 부재 경제 행은 유지한다. 다른 event/field/identity/분모와 원본 replay는 유지한다.
- event-cache의 선택적 representation migration은 한 행씩 읽고 임시 파일에 쓰며 identity/원천·cache inode/size/mtime/ctime/population을 검증하고 fsync 후 atomic replace한다. malformed/nonobject/encoding gap은 기존 파일을 보존하며 projector의 row 삭제나 identity 변경은 실패다. 기존 report caller는 모든 행을 materialize한다. maintenance-only `load_rows=False`는 원래 전체 row census를 metadata에 남기고 큰 리스트를 만들지 않는다.
- 최종 pre-provider guard는 loader-owned immutable v6 view·동일 configure/consumed key를 재확인한 경우에만 중복 static family/configure를 재사용한다. prepare에서 source/current pointer/PID/start/cwd/aux/handoff/backend generation을 재확인하고 매번 원 native claim·scope·requested refs·model/registry·overlay/revocation·exit 검증을 수행한다. v5·mutable·unverified·cold 경로는 원 validator를 수행한다. signal/result cache, clock 갱신, refs 추가는 없다.
- 5분 wrapper의 완료 후 기본240초 cooldown은 다음 예약을 건너뛰게 했다. 10:15 START→10:23 DONE→10:25 cooldown SKIP→10:30 START→10:40 DONE을 관측했다. 기본 cooldown을0으로 바꾸고 기존 flock와 명시적 환경 override를 유지한다. 600초 freshness/오류 검증은 그대로며 오래 걸리는 실행은 계속 경고할 수 있다.

자체 리뷰에서 cache projection의 malformed/encoding 보존, replace 전 source 검사, metadata 전체 분모와 낮은 메모리 maintenance 경로를 추가했다. [최종 consumer 검증](../../tmp/entry-shared-deadline-followup-20261013/final-reviewed-regression.log)은 **1306건 PASS**, wrapper 변경 뒤 [표적 재검증](../../tmp/entry-shared-deadline-followup-20261013/wrapper-cache-final-regression.log)은 **157건 PASS**다. 겹치는 시험은 합산하지 않는다. 기존 Pandas4Warning1건을 정책/성능 성공으로 취급하지 않는다. Python compile·shell 문법·diff·문서/parser 검사는 후속 completion에 기록한다. 검토한 scope의 미해결 code finding0은 외부 지연이나 전체 Main 성능 목표 해결을 뜻하지 않는다.

[캐시 정리 결과](../../tmp/entry-shared-deadline-followup-20261013/cache-compaction-result.json)에서 원본 pipeline은 유지했고 기존 lock을 보유해 두 캐시를 atomic compact했다. 10/12는181965행 그대로, 10/13는52333행에 신규2865행을 더해55198행이며 raw offset 증분만 소비했다. 약823537664bytes(0.767GiB)를 회수했다. 한 core/nice12/idle I/O·주소공간2GiB에서 최대RSS126.5MiB, 17.36/14.55초였다. 최초 memory-limited 실패는 기존 파일을 유지했고 성공으로 바꾸지 않았다. 새 cache 분모가 줄어서 빨라진 것으로 보고하지 않는다.

[퇴역 release cache 점검](../../tmp/entry-shared-deadline-followup-20261013/inactive-cache-cleanup.json)에서 현재/PID/서비스/정책/rollback 참조가 있는45개 release는 보존했다. [pytest 임시 점검](../../tmp/entry-shared-deadline-followup-20261013/pytest-temp-cleanup.json)에서도 활성/참조 데이터 삭제0이다. [과거 원장 보호 점검](../../tmp/entry-shared-deadline-followup-20261013/archive-protection-review.json)은 09/28·10/06·10/07·10/08의 native postclose 검증 결손과 아직 적용 중인10/12 원천을 식별했다. 원장 압축/삭제는 진행하지 않았다. 과거 검증의 current-code/checklist 연결 문제는 [원 issues](../../tmp/entry-shared-deadline-followup-20261013/archive-owner-issues.json)로 보존하며 이번 storage repair에서 controller 증빙을 조작하지 않는다. 공간 회수량과 동시 운영 기록 증가에 따른 df 변화는 구분한다.

일부 baseline cache의 대량 blocked row와 필수 canonical payload/trace는 여전히 남는다. 전체 report RSS·I/O wait·새 PID timeout 감소는 배포 후 자연 표본으로 확인해야 한다. 이번 변경은 새 비교 원장, package 변경, provider/order 강제호출, EOD/장후 정책 재생성을 하지 않는다. 검토된 exact source pair와 운영 계약을 candidate에 포함하고, 기존 owner의 ordered drain/선택/새 PID 소비 뒤 정상 예약 report로 수용한다.


## v6 실제 전환과 report 메모리 재보완

v6 commit `61dd72bafb5ad148e8b043a7417680baeb907a22`, PID2511867/start10796434는11:32:51 ordered 검증을 완료했다. [후속 health](../../tmp/entry-shared-deadline-followup-20261013/post-deploy-v6-health.json)에서 원 controller issues0·process/resource PASS, cron의06:50 이후 복구 이력 warning을 보존했다. 새 실제 예약 report는11:30:02 START→11:38:09 DONE이다. [격리 snapshot benchmark](../../tmp/entry-shared-deadline-followup-20261013/snapshot-benchmark.json)는 원 반복 snapshot에서 세 경제 필드를 typed input으로 복원한 같은 fixture로 각 arm30개 작업·3쌍을 비교했다. 나머지 output fields의 identity digest가 같고 snapshot 구성/JSON encoding p95 중앙값7.016ms→0.240ms, payload1415057→33318bytes다. 원 raw logger의 문자열화·escape·fsync 비용을 포함하지 않는 좁은 결과이며, 실제 원 raw 행 약2.86MB의 측정과 혼동하지 않는다. 전체 Main/AI 개선을 주장하지 않는다.

v6 report peak RSS 약3.6GiB와 실행 중11:38 sampler I/O wait37.26%도 관측해, storage snapshot 개선만으로 report 메모리 병목을 닫지 않았다. daily cache의 동일 field-name/짧은 string을 매 JSON 행마다 별도 객체로 생성하는 중복을 추가 보완했다. `sentinel_event_cache`의 read-local decoder는 key 최대2048개, value 최대8192개·길이192 이하의 immutable string만 공유한다. 초과/긴 값은 원 JSON decode 그대로이며 dict/list는 독립이다. enum·숫자·null·bool·unicode·중복 key의 마지막 값·row/field population·캐시/원본 bytes는 변경하지 않는다. 다른 판정/runtime policy 사이 객체 cache는 없다.

[메모리 benchmark](../../tmp/entry-shared-deadline-followup-20261013/cache-memory-benchmark.json)는10/12 cache의 같은 불변 prefix30000행을 B/C 3회 읽고 input/output digest와 row count를 비교했다. RSS 중앙값479896→162824KiB(약66% 감소), decode 전체 median0.888→1.530초로 CPU 비용은 늘었다. 최초 baseline3.298초의 cold/cache 차이는 별도 원인으로 확정하지 않았다. 따라서 전체 성능 개선 또는 결합 workload 입증으로 보고하지 않는다. 1core/nice10/idle I/O·주소공간2GiB이며 원장 복제/파일 수정·provider/order 호출0이다. 값/containers/duplicate key/unbounded-unique 반례와 Buy Funnel/entry/pipeline 소비의 [재검증253건](../../tmp/entry-shared-deadline-followup-20261013/cache-memory-consumer-regression.log)이 PASS다. 앞의 그룹과 합산하지 않는다.

v7은 이 lossless in-memory representation 보완과 운영 문서만 추가한다. v6의 machine/auxiliary guard, snapshot 참조·source code pair·원 bootstrap/정책을 유지한다. 같은 ordered 승인으로 원 PID 종료 후 전환하며 정상 예약의 row count·최대RSS·DONE/freshness와 자연 SDK 지연을 확인한다. 단일 성공 cron이나 짧은 prefix benchmark가 데이터 증가 후의 모든 성능 문제를 해결한 근거는 아니다.


## 최종 v7 소비·정규 보고·공간 정리 완료

최종 release `main-entry-deadline-20261013-v7`, commit `fbe42ca76cc46b5a3ebe3a00ee41eab0c878be38`, PID2535402/start10896411/cwd release `/src`의 실제 정책 소비를 확인했다. 배포기150초 attestation 창은 실제 PID 증빙11:48:55에 약12초 앞서 만료했다. [실패 원문](../../data/runtime/release_transitions/2026-10-13/fbe42ca76cc46b5a3ebe3a00ee41eab0c878be38/failure-before-attestation-recovery.json)을 보존하고 같은 새 PID·bootstrap·native handoff·원 source hashes를 새로 검증한 [복구 영수증](../../tmp/entry-shared-deadline-followup-20261013/attestation-recovery-v7.json)으로 닫았다. deployer 자신의 정확한 hold만 해제했고 추가 재기동/정책 재생성/5초 갱신은 하지 않았다. 이 검증 창은 trading deadline이 아니다.

전환 뒤에도 실행 중이던 구 v6 source-only report는13분 넘게 지연되고 kernel read6.7GB·swap page-wait를 관측했다. [정확한 PID/start/command 점검](../../tmp/entry-shared-deadline-followup-20261013/obsolete-report-cancellation.json) 후 이 구 report만 SIGTERM으로 종료했다. 원 cache/raw·lock inode·Main은 유지했고 native FAIL143 기록을 보존했다. 다음 변경 없는 정규5분 cron이 v7을 실행해11:55:01 START→11:55:58 DONE으로 복구했다. [정규 실행 관찰](../../tmp/entry-shared-deadline-followup-20261013/natural-report-v7.json)에서 관측한 kernel peak RSS는2134204KiB(약2.04GiB)다. 직전 완료된 v6의8분7초·관측RSS 약3.6GiB와 비교해 실제 report 완료와 메모리 사용이 개선됐지만, 입력 시점·host/cache 상태가 달라 frozen full-workload paired benchmark로 주장하지 않는다.

[완료 원천 대조](../../tmp/entry-shared-deadline-followup-20261013/natural-report-v7-terminal.json)의 baseline cache181965행은 그대로이고 오늘은70410행, 신규4000행이 추가됐다. 모두 materialize했고 원 offset과 projection version을 유지했다. [600초 freshness 검사](../../tmp/entry-shared-deadline-followup-20261013/freshness-v7.json)는 날짜별 monitor의 실제 mtime·notification status를 통과했다. report의 `unobservable` 진단은 그대로이며 freshness 복구를 주문/성과 성공으로 바꾸지 않는다. 정상 DONE이 이전 FAIL을 닫은 뒤 [마지막 health](../../tmp/entry-shared-deadline-followup-20261013/post-terminal-v7-health.json)는 process/resource PASS, cron은 기존 새벽 cutoff 이후 복구 이력 warning만 남는다.11:56 sampler I/O wait17.8%,11:59 최신 검사2.23%이며 전 시간대의 무경고를 보장하지 않는다. 원10/12 controller generation issues0이다.

[최종 완료](../../tmp/entry-shared-deadline-followup-20261013/completion.json)에 source-exact22개 compile·shell 문법·diff·문서65개 local link·print-only parser와 기존 OPEN owner 각각1개를 기록했다. 최신 consumer253건과 앞선1306건은 중복을 합산하지 않는다. 코드/정책/호환성·실제 PID와 정상 report의 수용을 분리했다. 새 자연 provider 호출 표본은 없어 AI timeout 감소는 미검증이다. 전체 Main의 모든 지연·시장 데이터 증가 이후의 영구 성능 목표나 경제성 수용을 완료하지 않는다.

직접 캐시 정리로0.767GiB를 회수했다.11:57 disk는사용률83%·여유 약25GiB이며, 동시 로그/원천·보고 교체가 있어 회수량과 df 순변화를 동일시하지 않는다. current/rollback/policy/custody와 과거 검증 결손 원장은 보존했고 대형 비교 원장/샘플 전체 복제·package 변경·manual provider/order 호출0이다. 미사용 benchmark 입력은 종료 시 제거했다. 새 report/canonical 원천의 장중 증가율은 자연 표본의 별도 수용이며, 무제한 호출 설정 자체를 이번 저장 폭증의 단독 원인으로 단정하지 않는다.

12:00 정규 예약도12:01:20에 DONE으로 완료했다(79초).12:06 재점검의 사용률은83%·여유 약25GiB다. 중간 df85% 관측은 당시 값으로 남기되 영구 증가의 단독 원인으로 확정하지 않는다. [최종 영수증](../../tmp/entry-shared-deadline-followup-20261013/completion.json)의 현재값과 직접 회수량을 구분한다.
