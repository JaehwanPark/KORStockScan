# Main 진입 보조판정 시간초과 상세 보완계획 — 2026-10-13

상태: **구현·리뷰·수정과 새 시간초과 후속 보완 후 최종 v5를 배포·재기동했다. 10:13 PID2343133/start10331968의 정책 128경로·원 bootstrap/PREOPEN 소비를 검증했다.** [구현 리뷰](../audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md)와 [배포 완료 증빙](../../tmp/entry-shared-deadline-deployment-20261013/deployment-completion-v5.json)에 코드·실제 배포·새 로그·776건 검증·격리 성능과 미측정 범위를 구분했다. **전체 지연 목표와 자연 timeout 감소는 미검증이며 기동 직후 긴 Main 루프 관측도 남는다.** 아래 계획 단계의 미실행 표시는 원 설계 시점의 기록이다. 10/13 08:07 원천 대조에서 확인한 신호 전달, AI 전처리, 결과 기록의 지연을 줄인다. 원 native 신호의 5초 안에서 보조판정과 Main 소비까지 완료하는 것이 목표다. OpenAI의 응답시간이나 과거 미진입의 복구를 보장하는 계획은 아니다.

## 1. 근거와 기존 작업의 경계

근거는 [08:07 정확한 판정별 원천 대조](../../tmp/entry-timeout-diagnosis-20261013/summary.json), [AI trace](../../data/ai_decision_trace/ai_decision_trace_2026-10-13.jsonl), [pipeline](../../data/pipeline_events/pipeline_events_2026-10-13.jsonl)다. 이 수치는 해당 시점의 스냅샷이며 이후 운영 상태를 대신하지 않는다.

- 릴리스 `main-residual-reviewed-20261013-v6`, commit `2223ac9e948cdbf79bf2ed1e1b6c4c5d7f069df6`, PID `2164993`, start ticks `9505700`에서 발생했다.
- 실제 `analyze_target` 호출은 두산에너빌리티 6건, 시간초과 6건, provider response ID 0건이다. 마지막 1건은 새 적격 신호를 사용한 정상 recovery 호출이다. 보조판정 PASS/VETO나 증권사 주문 실패로 집계하지 않는다.
- entry 회로는 OPEN, 공통 provider 회로는 CLOSED다. 기존 entry 단일 recovery lease는 동작했으나 성공 응답을 얻지 못했다. 영구 중단 결함과 이번 지연 결함을 구분한다.

| 관측 구간 | 08:04:26 오류 | 08:04:30 오류 | 해석 |
|---|---:|---:|---|
| native 신호 anchor → preparation dispatch | 2.759초 | 1.060초 | Main 방문·claim·dispatch를 세분화해야 원인이 확정됨 |
| preparation queue / service | 0.018 / 0.082초 | 0.019 / 0.195초 | 뒤의 refresh·capacity·AI 전처리와 다른 구간 |
| AI dispatcher 대기 | 0.021초 | 0.021초 | 두 건에서 주된 지연은 아님 |
| `analyze_target` 시작 → `_call_openai_safe` 진입 | 0.967초 | 1.498초 | 정책·기계·경제 원천·prompt/schema·outbox의 합; 내부 원인 미확정 |
| safe adapter 진입 후 HTTP 이전 처리 | 0.011초 | 0.200초 | request capture 등을 포함하며 위 구간과 구별 |
| HTTP wall-clock budget / 실제 provider 계측 | 0.922 / 0.910초 | 1.997 / 1.796초 | HTTP lock 대기는 모두 0ms; provider 완료 응답은 없음 |
| 오류 annotation·cache 구간 | 0.415초 | 0.469초 | 함수 호출 구간 이름이며 개별 파일의 비용은 미확정 |
| 원 deadline 대비 worker 완료 초과 | 0.423초 | 0.470초 | Main은 `expired_after_response` 후 최종 거절 |

`annotation·cache`라는 clock 이름만으로 실제 cache write가 있었다고 단정하지 않는다. 기계 우선 경로의 결과 cache는 기존 코드에서 제한되며, annotation 내부 trace/outcome 저장을 별도로 측정해야 한다. 준비·refresh·복사 지표는 중첩될 수 있으므로 위 표의 모든 항목을 더해 전체 시간으로 사용하지 않는다.

`provider_returned_perf`는 `_call_openai_safe`의 반환 또는 예외를 호출자가 관측한 시각이다. HTTP executor의 실제 SDK 완료시각과 같다고 가정하지 않는다. wall-clock timeout 후 future가 살아 있으면 SDK 완료시간은 미관측/censored이며, 로그의 `provider_total_ms`도 서버 추론시간이 아니다.

HTTP lock wait 0ms는 HTTP executor queue wait 0ms를 증명하지 않는다. AI dispatcher의 21ms 대기와 SDK executor의 대기도 다른 구간이다. 기존 stage epoch가 제공하는 시작 사실과 추가로 필요한 queue/SDK 종료 clock을 구분해 원인을 확인한다.

이번 범위는 [기존 회로·제출 증빙 계획](main-auxiliary-circuit-recovery-and-submit-receipt-remediation-plan-2026-10-12.md)의 **새 지연 결함 후속**이다. [native claim 계획](main-native-signal-claim-and-auxiliary-revalidation-remediation-plan-2026-10-12.md)의 S2, [readiness 계획](main-fixed-nonfixed-signal-readiness-and-latency-remediation-plan-2026-10-12.md)의 S2/S3 구현을 재사용한다. 배포된 wakeup, lifecycle, fixed/nonfixed identity, receipt binder, 회로를 다시 만드는 계획이 아니다.

## 2. 보존할 계약과 성능 목표

1. original deadline은 native snapshot epoch + 5초와 caller deadline 중 더 이른 값이다. claim·worker·refresh·response 시각으로 갱신하지 않는다. wall clock과 같은 PID monotonic deadline을 함께 유지한다.
2. 기계 ENTER_NOW만 현재 compact AI로 전달한다. model `gpt-5.4-nano`, prompt/schema/semantic 판정, transport·provider·key retry·실제 호출한도·inflight 제한을 보존한다. 이번 계획은 timeout 확대나 추가 호출을 해결책으로 사용하지 않는다.
3. source/item/route/session/epoch/sequence, 정책·registry·compatibility·PID/start/release 결속을 전송 직전과 Main 소비에서 검증한다. PRE NXT, REGULAR의 실제 경로, 통합 AFTER SOR를 서로 대체하지 않는다.
4. 주문·가격·수량·자금·custody·operator veto·cooldown·hard/protect/emergency와 보유/청산 우선순위를 유지한다. 과거 PASS 재사용, 원천 결손 보간, 퇴역 episode/widget 복원은 없다.

10/13 후속 검증은 마지막 provider 전 검증의 fresh immutable view와 짧은 signature pass까지만 공유한다. native claim·scope·registry/model·overlay/revocation·current-pointer/path 검사를 모두 실행하고 provider 전에 닫는다. `entry_native_load/claim/auxiliary`는 aggregate `entry_native_check`의 자식 구간이며 서로 p95를 합쳐 전체 비용으로 계산하지 않는다. 키움 source-only150ms·rate reserve·계좌/가격 증빙·2초 entry freshness·normal sizing과 필수 저장은 유지한다. 확인된 SDK timeout과 source TR timeout은 계속 실제 실패로 기록한다.

아래 수치는 **구현 후 성능 목표**다. 목표 미달 신호를 버리는 신규 entry gate나 provider 최소잔여시간 gate가 아니다.

| 서로 겹치지 않는 측정 구간 | warm p95 목표 | 변경 목적 |
|---|---:|---|
| 최초 관측된 eligible → Main claim·preparation dispatch | 0.50초 이하 | Main의 다음 방문까지 불필요하게 기다리지 않기 |
| dispatch → `analyze_target` 시작 | 0.30초 이하 | 준비 queue/service와 최종 refresh·capacity 비용 줄이기 |
| `analyze_target` 시작 → 실제 SDK 시작 | 0.50초 이하 | 기계·정책·경제 원천·request capture의 중복 로컬 작업 줄이기 |
| 호출자의 adapter 반환/예외 관측 → Main 최종 소비·거절 완료 | 0.30초 이하 | 의미검증·필수 저장·worker/inbox·Main commit 비용 줄이기 |

전체 로컬 비용의 warm p95 목표는 **1.60초 이하**다. 각 구간 p95를 합쳐 전체 p95로 계산하지 않고 attempt별 비중첩 elapsed를 따로 집계한다. 신호 anchor → 최초 eligible 시간도 별도로 보고한다. anchor가 이미 오래된 신호에는 HTTP 3.4초가 남는다고 보장하지 않는다. fresh eligible이 anchor와 같은 정상 workload에서는 로컬 처리 감소로 5초 중 약 3.4초를 HTTP에 남길 수 있는지 검증한다. cold start·정책 전환·수신 단절 구간은 따로 표시한다.

## 3. P0 — 전체 시간의 원인을 먼저 닫기

소유 위치는 [runtime_performance](../../src/engine/monitoring/runtime_performance.py), [Main handler](../../src/engine/sniper_state_handlers.py), [async coordinator](../../src/engine/scalping/scanner_async_eval.py), [AI engine](../../src/engine/ai_engine_openai.py)다.

- 한 attempt에 `source_anchor`, `eligible_first_observed`, `main_visit`, `claim`, `dispatch`, `prepare_start/end`, `refresh_start/end`, `capacity_start/end`, `analysis_start`, `sdk_start/return`, `worker_done`, `main_consume/terminal`을 연결한다. 기존 signal/request/snapshot/observation ID와 original deadline을 사용하고 진단용 새 거래 identity를 만들지 않는다.
- HTTP executor enqueue/start, 실제 SDK start/end, caller adapter end, future cancelled/settled를 별도 clock으로 남긴다. same PID monotonic을 추가하면서 기존 wall clock과 transport stage fields의 의미를 보존한다. SDK 시작은 물리 전송 확정이 아니며 response 수신 증거와 구분한다. timeout의 `caller_adapter_end`를 `sdk_end`로 채우지 않는다.
- source anchor와 eligible의 관측 시작이 다르면 각 값과 coverage를 보존한다. 정확한 시계가 없으면 null/관측 구간으로 남기며 dispatch age 전체를 scheduler 책임으로 계산하지 않는다.
- `analyze_target` 안에 policy resolve·source freeze·machine assessment·machine capture·economic observer·payload/prompt/schema 구성·최종 정책/claim 검증·outbox reserve를 계측한다. safe adapter 안의 payload build·identity 계산·request capture·HTTP lock·SDK를 분리한다.
- annotation은 result 구성·sanitize/serialize/hash·trace append·pending outcome append·index update를 분리한다. file lock wait와 실제 write/fsync도 분리한다. 통합 구간의 설명되지 않은 나머지는 `other_local_ms`로 유지한다.
- 각 clock은 parent interval을 명시한다. 성공/timeout/호출 전 만료/기계 BLOCK·RECHECK/정상 신호 종료에서 생산하며 누락·음수·중첩을 명시한다. phase 계측을 넣느라 파일을 추가로 fsync하지 않는다.
- hot path에는 기존 bounded deque/counter만 사용한다. 기존 pipeline/trace/heartbeat consumer로 생산하고 전일·당일 원장 전체 스캔, 매 tick 전체 정책 census, 별도 worker/timer/원장을 만들지 않는다.

계측은 동일한 parent interval의 누락분/overlap을 표시하고 자체 계측 overhead·file write 증가를 대조한다. record clock 필드가 없다고 실행을 차단하지 않는다. 성능 분모는 offered opportunity·dispatch·SDK started·completed·censored·Main disposition을 각각 보존한다. 무응답/기한 전 만료를 제외한 성공 호출만으로 p95를 계산해 전체 개선이라고 보고하지 않는다.

완료 기준: 제시된 두 attempt의 2.759/1.060초와 0.967/1.498초를 재현 가능한 경계로 설명한다. 복원 불가능한 과거 세부 시간은 추정하지 않고 새 코드의 격리 측정으로 검증한다. 큰 원인이 확인되면 해당 P1/P2 변경부터 진행하고 진단 항목 추가만으로 수리를 완료하지 않는다.

## 4. P1 — 신호 전달과 준비 비용 줄이기

### 4.1 Main 방문·claim

- [Main loop](../../src/engine/kiwoom_sniper_v2.py)의 기존 native-ready/completion Event를 유지한다. 새 native-ready가 발생했는데 Main이 실행 중인 동기 작업 때문에 방문하지 못한 구간을 P0로 특정한다.
- 확인된 긴 비필수 작업 사이에 bounded dispatch 확인 지점을 둔다. 알림 key를 coalesce하고 같은 canonical opportunity를 한 번만 claim한다. 진행 중 주문·보유 청산·broker reconciliation을 중단하지 않는다.
- 기존 전체 watch cursor와 비고정 감시 순환을 유지한다. 상시 5종목만 먼저 돌고 비상시가 굶는 개선, completion 수거·cleanup을 건너뛰는 개선은 거절한다.
- WS callback은 bounded 게시·notify만 한다. callback에서 policy/file/DB/REST/AI를 호출하거나 Main 외 thread에 claim·주문 권한을 넘기지 않는다.

### 4.2 준비·최종 refresh

- coordinator `_prepare` → `_evaluate_prepared` → `refresh_before_evaluate`의 immutable copy와 최종 WS refresh 비용을 따로 측정한다. 준비 source 중 cutoff/generation이 같은 candle·static derived data만 재사용한다.
- 최종 WS/item/route/epoch/sequence 검사는 유지한다. generation 변경, stale, 정규→통합 애프터 전환, 정책 교체에서는 준비물을 폐기한다. stale snapshot의 age를 현재 시각으로 덮지 않는다.
- capacity prefetch는 기존 exact account/route/price/quantity/expiry receipt 재사용 경로를 이용한다. 준비 단계와 `entry_economics_observer`가 같은 유효 receipt를 중복 요청하는 경우만 줄이며 다른 가격·수량·계정으로 재사용하지 않는다.
- 이미 적용된 prepared index/candle cache를 먼저 점검한다. cold initialization을 신호 budget 밖의 기존 초기화·maintenance에 둔다. source readiness 실패와 준비 queue admission 실패는 원 terminal로 남긴다.

## 5. P2 — AI 내부 전처리와 호환성 검증 비용 줄이기

소유자는 `ai_engine_openai`와 [reversal_evaluation_context](../../src/engine/scalping/reversal_evaluation_context.py), 기존 native loader·auxiliary registry/compatibility reader다.

1. **정책·호환성 준비:** 동일 PID/start/날짜/release/bundle/registry/schema/validator/compatibility generation의 검증된 immutable view만 기존 loader를 통해 재사용한다. static schema/prompt 준비와 index 초기화는 기존 기동/정책 refresh 경로로 옮긴다.
2. **전송 직전 재검증:** 현재 loader가 이미 캐시와 dependency 검사를 한다는 점을 전제로 한다. 캐시를 하나 더 만들지 않고 중복 decode/hash만 줄인다. content/stat/symlink 변경·삭제·같은 size/mtime 교체·code-pin·selector 변경·진단 cache failure 반례에서 기존 dependency 검증과 fail-closed가 유지되는지 시험한다. generation을 확인하지 않는 장기 TTL 캐시는 금지한다.
3. **기계·경제 원천:** `capture_machine_observation`과 `entry_economics_observer`의 실제 비용을 먼저 측정한다. 기계 판정, 모델 입력의 비용/source, 원 action receipt와 sizing·price가 요구하는 필수 입력은 유지한다. 같은 snapshot의 중복 복사·sanitize·계산·serialization을 immutable 산출물 한 번으로 공유한다. live decision 입력과 offline replay 부가 projection의 의존관계를 확인하기 전에는 callback 전체를 AI 뒤로 옮기지 않는다.
4. **payload:** 같은 request에서 provider payload를 반복 build/hash하는 부분을 하나의 immutable canonical envelope로 공유한다. 다른 attempt 사이에 payload·PASS를 공유하지 않는다. prompt/schema/model/max tokens/reasoning/strict flag와 비용·시장·패턴 정보의 의미를 보존한다.
5. **request capture:** [AI trace writer](../../src/engine/scalping/ai_decision_trace.py)의 prompt/payload/request 세 append와 payload에 포함된 replay context의 기존 dedup을 점검한다. 별도 replay 파일이나 원장을 만들지 않는다. 동일 해시의 이미 durable한 내용은 재저장하지 않고 참조하되 각 attempt의 request ID·원천 reference는 남긴다. before-send request 원천과 exact replay lineage를 유지하며 fsync 제거·축약 payload·capture 실패 은폐로 시간을 줄이지 않는다.
6. **outbox:** [operating outbox](../../src/engine/scalping/reversal_operating_outbox.py)의 reserved·legacy custody bridge·transmission_uncertain을 그대로 유지한다. 중복 write가 실제로 확인되면 같은 원자성·동시성·crash 복구를 갖는 쓰기 절차만 개선한다. 전송 후 예약, in-memory 예약만 사용, unknown transmission 재호출은 금지한다.

## 6. P3 — 응답·실패 기록과 Main 소비

- 성공과 실패의 semantic validation, mandatory trace/outcome/outbox, optional projection을 실제 reader 기준으로 분리한다. action receipt나 consumer가 요구하는 durable append는 Main accepted 전에 완료한다.
- 같은 frozen result에서 중복 serialize/sanitize/hash만 제거하고 immutable bytes를 writer에 전달한다. 새 append가 성공한 뒤에만 dedup/index를 전진시키며 short write·fsync 실패·회전·압축·날짜 전환·동시 writer 반례를 검증한다.
- 부가 projection의 지연 실행이 필요하면 기존 bounded observation sink를 재사용한다. queue-full·close·crash·drain 실패가 원 terminal에서 드러나야 하며 필수 원천의 메모리 enqueue를 durable 완료로 취급하지 않는다. 기존 경로로 안전하게 분리할 수 없다면 동기 저장을 유지한다.
- 결과 inbox 완료 알림과 Main completion 우선 소비를 유지한다. pending request/token/claim·원 정책 generation을 함께 소비하고 stock의 마지막 PASS로 대체하지 않는다. 최종 claim/source/quote 검증 뒤에도 원 deadline을 적용한다.
- trace annotation·pending label의 결과를 AI PASS, Main acceptance, intent, send, fill, terminal로 각각 연결한다. timeout 이후 기록은 historical evidence이며 늦은 응답을 주문에 사용하지 않는다.

구현 전에 저장 대상별 기존 권한과 완료 순서를 다음 기준으로 확인한다.

| 저장 대상 | 기존 소비·권한 경계 | 수리 요건 |
|---|---|---|
| machine action·revision·pre-AI source receipt | 현재 machine/submit/sizing consumer가 요구하는 실행 증빙 | 기존 필수 append 성공·해시 검증과 missing/stale 거절을 유지 |
| operating outbox·legacy reservation | 실제 SDK 시작 전 중복/불명 전송 수탁 | durable reservation 후 전송; 실패·partial transition은 fail closed |
| prompt/payload/request·decision trace·pending outcome | 실행 consumer가 참조하는 필드와 report-only 필드를 caller별로 확인 | 필수 reference를 먼저 보존하고 나머지 실패 상태도 그대로 보고; 진단 저장을 새 live veto로 승격하지 않음 |
| 부가 pipeline projection·요약·중복 설명 | report-only reader | 원 source/hash/attempt를 참조; 기존 bounded sink와 확정 append→reader 계약이 있을 때만 지연 실행 |

`capture_ai_request`는 일부 저장 실패를 상태 필드로 반환한다. 이번 최적화에서 모든 진단 capture를 일괄 필수 gate로 바꾸지 않는다. 실제 실행 consumer가 요구하는 증빙을 누락시키거나 report-only 실패를 숨기는 것도 허용하지 않는다. 구현 manifest에는 대상별 현재 caller·writer·reader, 필수 순서, failure 처리, append receipt를 적는다. 권한 분류가 불명확한 write는 그대로 유지하고 확인한 중복 비용부터 줄인다.

현재 `response_reserve()`는 성공 경로의 `response_validate` 최근 표본으로 추정하며 250ms 상한을 갖는다. 실패 annotation은 415/469ms인데 실패 경로에서는 같은 sample update가 없다. 이는 응답 후 비용 관측의 결손이며 최초 timeout의 단독 원인이라고 단정하지 않는다.

이를 보완할 때 success/failure의 `caller_adapter_end → worker_done → Main disposition`을 같은 기준으로 계측한다. 필수 local 비용과 optional projection을 구분하고, 기존 상한을 무작정 늘려 HTTP 시간을 더 줄이는 방법은 채택하지 않는다. 우선 필수 처리 비용을 줄인다. 실패 전체 처리시간을 성공 응답의 reserve 표본에 무조건 넣지 않는다. 공통 필수 처리 interval의 동일성·overlap·scope를 먼저 검증하고 실패의 추가 로깅 비용은 별도 진단한다. 기존 reserve의 최초 무표본0·250ms 상한·deadline 보존을 유지하면서 실제 비용이 범위를 넘으면 원인과 초과분을 명시한다. 숫자 상한 변경이 필요하면 별도 근거와 영향 검토를 계획에 반영한 뒤 결정한다.

`_call_openai_safe`는 현재 request 구성과 capture에 사용한 시간을 원 deadline에서 차감하고 SDK worker도 시작 직전에 remaining을 확인한다. 이 경계를 재사용한다. capture/lock/worker queue에서 기한을 소진하면 SDK 미시작과 시작 후 timeout을 구분하며 timeout 계산을 재시작하거나 최소 HTTP budget으로 늘리지 않는다.

## 7. P4 — 회로·상태 표시의 수용

기존 entry threshold5·30/60/120/240/300초 backoff·단일 recovery lease·공통 provider fail-closed를 유지한다. 계측 때문에 failure owner 또는 호출 수를 바꾸지 않는다.

- 신호 만료로 SDK 미시작인 경우와 SDK가 시작된 typed deadline timeout을 기존 transport observation으로 구분한다. unknown·401/403·429·5xx는 기존 공통 분류를 따른다.
- circuit OPEN 중 engine 자체는 enabled일 수 있다. UI/health는 같은 PID/start의 entry state, 공통 state, 마지막 timeout, 미평가 수, 정상 recovery 결과를 각각 표시한다. 과거 heartbeat의 `recovery_wait_seconds`를 현재 남은 시간으로 보고하지 않는다. 원 관측 시각·절대 next-eligible 시각 또는 관측 나이를 함께 소비한다.
- 미정산 future를 추적하고 완료 전 중복 recovery를 허용하지 않는다. cache·다른 endpoint·늦은 응답은 entry 회로를 닫지 않는다. 전송 불명·인증 장애를 reset/restart로 감추지 않는다.
- 자연 회로가 열리지 않거나 새 적격 신호가 없으면 복구 수용은 pending이다. 성공 샘플을 만들기 위한 health provider 호출은 하지 않는다.

현재 회로 성공 판단은 기한 내 semantic 유효 응답을 확인한 뒤 annotation보다 먼저 수행된다. 이후 필수 기록·Main 소비가 늦어지는 경우 `transport_recovered`와 `main_commit_rejected`를 별도로 남긴다. 모든 후속 처리가 끝나야 transport 회로가 복구되도록 새 조건을 붙이거나, 회로 CLOSED를 Main 수용 성공으로 표시하지 않는다.

## 8. 동작·성능 검증

### 8.1 고정 입력과 표적 회귀

baseline은 위 v6의 exact code/source hash다. candidate는 수정 source hash·policy/registry/compatibility hash를 함께 고정한다. 기존 6건과 정상 PASS/VETO fixture를 사용한다. 계속 append되는 원본은 필요한 행의 byte offset/length·행 해시·동결 prefix 길이/해시와 연결 payload/정책 해시를 manifest에 기록하고 읽기 전후 검증한다. `latest` 경로나 전체 당일 파일의 나중 해시를 동결 근거로 쓰지 않는다. 원 payload/replay가 없는 행은 정확히 제외하고 제외 이유·분모를 남긴다. 최적화 candidate의 입력을 baseline에 없는 최신 source로 채우지 않는다.

| 검증 대상 | 기존 테스트 확장과 통과 기준 |
|---|---|
| native/Main scheduling | [fixed watch](../../src/tests/test_main_fixed_watch.py), [native diagnostics](../../src/tests/test_native_signal_claim_diagnostics.py): wakeup 경합·coalesce·expired/replaced·동일 기회 복수 패턴·fixed/nonfixed fairness, claim 중복0 |
| async 준비·완료 | [async eval](../../src/tests/test_scanner_async_eval.py), [entry bridge](../../src/tests/test_scanner_async_entry_bridge.py): cold/warm·capacity refresh·cancel·late future·inbox cleanup·원 context 보존 |
| policy/request 호환성 | [reader readiness](../../src/tests/test_auxiliary_reader_readiness.py), [auxiliary contract](../../src/tests/test_reversal_auxiliary_contract.py), [OpenAI transport](../../src/tests/test_ai_engine_openai_transport.py): 마지막 pre-send 검증에서 관측된 source/selector/compatibility 변경은 SDK 시작0, 시작 후 변경은 전송/불명 전송 사실 보존·Main commit/order0; 같은 wire 의미·원 deadline |
| trace/durability | [AI trace](../../src/tests/test_ai_decision_trace.py), [pipeline logger](../../src/tests/test_pipeline_event_logger.py): dedup 충돌·partial tail·compress/rotate·동시 append·queue-full·fsync 실패·crash, 필수 원천 손실0 |
| circuit/timeout | [entry circuit](../../src/tests/test_entry_transport_circuit.py): 최초5회·single recovery·미정산 future·공통 auth/unknown 우선순위 유지, 늦은 응답/중복 전송0 |
| runtime 인계 | [ordered deploy](../../src/tests/test_ordered_intraday_deploy.py), [policy bootstrap](../../src/tests/test_runtime_policy_bootstrap.py): guard/hash/source 결속·stop→selection→start 순서 유지 |

실제 provider 호출 대신 deterministic clock/recorded provider stub으로 0.5/1/2/3/3.4초 응답과 timeout·late response를 시험한다. 마지막 pre-send 검증에서 관측된 원천 충돌·만료는 SDK 시작/order0, 시작 후 변경·기한 만료는 전송/불명 전송 증거를 보존하면서 Main commit/order0을 확인한다. 각 race fixture는 변경 주입 시점·마지막 검증 시점·SDK 시작 여부를 명시한다. SDK 시작 이후에는 cancel 반환값만으로 물리 전송0을 주장하지 않는다. deadline을 넘은 역사적 두 건을 새 코드에서 강제로 PASS시키는 시험은 금지한다. 원 신호·수신·정책 시퀀스를 유지한 replay에서 로컬 실행을 앞당겨 deadline 전에 유효 응답을 소비할 수 있게 된 결과는 의도한 개선으로 따로 집계한다. 과거 실제 전송·주문·수익을 복구했다고 보고하지 않는다.

### 8.2 비교 workload와 자원 제한

- baseline/candidate를 **B/C/B/C/B/C 3회씩** 교대 실행한다. 고정 100개 request-local fixture와 고정 100개 Main 방문/dispatch fixture를 각 workload에 사용하며 전체 runtime replay 가능 여부를 명시한다. 이 수는 100개 독립 거래가 아니라 같은 동결 fixture의 측정 작업 수다. 반복 mapping·순서·warm preconditioning·cold/transition 구간을 manifest에 고정한다. stub HTTP의 가상 대기시간은 로컬 실측 시간과 섞지 않는다.
- correctness replay는 가상 clock으로 deadline·순서를 검증하고, 성능시험은 실제 monotonic clock으로 로컬 함수를 측정한다. 필요한 I/O는 격리 tmp 아래 실제 쓰기·fsync를 수행하며 recorded read/stub service만 제공한다. 성능이 빨라진 것처럼 보이게 fsync·mandatory append를 mock하지 않는다. 가상 provider 지연을 실제 함수 elapsed에 더해 계산한 값은 modeled latency로 표시한다.
- workload는 단일 상시, 상시5+비상시5 probe 슬롯/long2, 같은 workload+trace writer 경합/rotation의 세 종류다. 보유·청산·completion·source refresh·필수 write 작업을 동일하게 포함한다. 실제 운영 Main과 장후 전체가 결합된 성능 증명으로 확대 해석하지 않는다.
- `.venv`와 기존 테스트 도구를 사용한다. 한 번에 격리 benchmark subprocess1개·1 CPU 상당의 제한·메모리1GiB·회차 wall 120초·임시 산출물 총256MiB를 설계 상한으로 둔다. 기존 worker 구조를 재현할 때 그 수를 늘리지 않는다. 상한 초과는 종료하고 결과를 censored로 표시하며 provider/REST/실주문/운영 DB·정책 파일 쓰기0을 검증한다.
- 자료는 기존 trace/request/payload·원장 pack의 exact 참조를 쓴다. 전체 AI 비교 원장이나 릴리스 data를 복제하지 않는다. 소규모 fixture·hash manifest·timing 요약만 보관하고 테스트 복제본은 검증 뒤 정리한다.
- 각 회차는 이전 회차의 executor/future·writer queue·temporary FD를 정산하고 동일 초기 상태로 시작한다. crash/late future 시험도 회차 경계를 넘겨 다음 candidate의 시간을 오염시키지 않는다. CPU affinity·부하·fsync 환경을 baseline/candidate에 똑같이 기록하고 강제 제한 때문에 timeout으로 끝난 회차는 정상 완료와 분리한다.
- source/quote/candle/기계/AI/필수 write/Main 소비의 작업량·bytes·request·terminal 수, 누락·drop·queue-full, CPU/RSS·파일 I/O·FD·thread·whole-loop p50/p95/p99/max를 동일 분모로 보고한다.
- 채택은 동일 frozen 입력의 기계 판정·AI 응답 의미·필수 원천과 guard 회귀0이 우선이다. 실제 실행이 빨라져 동일 offered opportunity의 expired가 유효 SDK 시작/완료로 바뀌는 것은 허용하며 그 증가를 별도로 보고한다. provider 호출 수까지 억지로 같게 맞춰 새 유효 기회를 제거하지 않는다. 순수 로컬 성능 비교는 같은 실제 작업을 수행한 paired subset에서 하고, 전체 offered/expired/censored 분모는 함께 보존한다.
- 지목한 병목의 paired median/p95가 3회 중 2회 이상 같은 방향으로 개선되는지 보고하고, 회차 간 변동·계측 overhead보다 작은 차이는 개선 입증 pending으로 둔다. 전체 local p95 20% 감소와 §2의 1.60초는 목표 도달 여부다. 명확한 병목 수리와 원 기한 내 유효 소비 개선을 일률적인 20% floor 때문에 거절하지 않는다. 특정 숫자를 맞추기 위해 작업을 버리지 않는다.
- 보유·청산/completion p95가 10%를 넘게 악화하거나 전체 loop p95·CPU/RSS가 10%를 넘게 악화하면 원인을 확인하고 해당 candidate를 채택하지 않는다. duplicate send/claim, 필수 write 손실, deadline 연장, authority leak은 수치와 무관하게 즉시 실패다.

검증 통과와 자연 provider 응답은 별도다. 후속 코드 단계에서는 targeted pytest·compile·`git diff --check`, wrapper 변경이 있으면 `bash -n`·운영 문서/contract 검증을 수행한다. 문서 단계에서는 링크·owner·권한·print-only parser만 검증한다.

## 9. 구현 순서와 종료 조건

| 순서 | 결과물 | 다음 단계 조건 |
|---|---|---|
| R0 | v6·6건 frozen source/reference manifest, 필요한 clock의 최소 보강 | 과거 관측과 새 실측 구분, 원인 미확정 비용 식별 |
| R1 | P1 Main 방문·최종 준비 중 확인된 긴 구간 수리 | 원 priority/전체 감시 분모·original claim 유지 |
| R2 | P2 정책·경제 원천·payload·필수 request/outbox 중복 비용 수리 | wire/판정 동등, compatibility/durability negative 통과 |
| R3 | P3 응답 기록·worker/inbox/Main 소비 수리, P4 상태 시각 보강 | 필수 기록 손실0·late response0·공통 회로 비퇴행 |
| R4 | 자기 리뷰 → 수정 → 재리뷰 → 표적 회귀 → 교대 benchmark | 검토 범위 미해결 finding0, 성능·분모 보고 |
| R5 | 허용된 배포 시 불변 릴리스·정책/호환/PREOPEN·기동 receipt | 새 PID/cwd/start·현재 source hash와 실제 소비 확인 |
| R6 | 정상 새 신호의 자연 수용 기록 | SDK budget·유효 응답·Main terminal을 같은 attempt로 연결 |

R1/R2/R3은 P0에서 확인된 비용 순으로 수행한다. 작은 policy decode 하나를 줄였다는 이유로 0.967/1.498초 전체를 해결했다고 보고하지 않는다. 구현 완료와 성능 목표·자연 수용·실주문·경제성의 완료를 각각 표시한다.

## 10. 기존 owner와 배포·자연 수용

현재 [10/13 체크리스트](../checklists/2026-10-13-stage2-todo-checklist.md)의 stable ID를 재사용한다. `AuxiliaryCircuitRecoveryRepair1012`가 entry 회로·이번 후속 지연 수용, `NonfixedDispatchReadinessReview1012`가 비고정 준비·순환 비퇴행, `DirectFamilyPreopenPolicyHandoff`가 정책/릴리스/기동 인계를 소유한다. 구현 시작 시 이 새 결함의 범위·Due/TimeWindow와 완료 기준을 해당 owner에 명시하며 중복 owner를 만들지 않는다. 기존 일정이 이미 지난 경우 미래 실행 시간을 별도로 정하고 과거 07:55~08:15를 새 실행 시간처럼 사용하지 않는다.

**이번 요청은 상세계획 수립이다.** 운영에 결속된 오늘 checklist의 bytes·일정·기존 Acceptance를 지금 변경하지 않는다. 기존 계약의 자동 runtime 허용을 확대하지 않으며 제안 목표를 live block으로 추가하지 않는다. 후속 구현·운영 작업이 허용되면 바뀐 checklist/consumer/code-pin의 영향을 확인해 필요한 exact-date strict verifier→controller/finalization·PREOPEN/장중 인계를 다시 닫는다. 현재 성공 영수증을 새 코드의 배포 근거로 재사용하지 않는다.

배포 수용 절차는 다음과 같다.

1. 새 릴리스에서 policy·registry·auxiliary compatibility 원천/reader hash를 검사한다. native pinned 코드가 변경되면 같은 정책의 행동 동등성과 정상 publisher/handoff를 검증한다. 정책 선택 기준을 이번 성능 수리로 다시 연구하지 않는다.
2. 기존 ordered deployment를 사용한다. 기존 PID/launcher의 종료를 확인한 뒤 selector를 전환하고 새 PID를 시작한다. 옛 PID가 새 selector를 소비하는 `auxiliary_pid_release_mismatch` 구간을 만들지 않는다.
3. 재생성이 필요한 장후·strict·PREOPEN source-date는 **2026-10-12 원천 / 2026-10-13 적용**을 보존한다. 무관한 대형 AI 비교를 재실행하지 않고 승인된 최소 closure만 수행한다. 후속 실행일이 바뀌면 그 날의 현행 계약을 먼저 확인한다.
4. 새 PID/cwd/start·bundle/registry·compatibility·native/auxiliary consumer를 확인한다. 처음5개 자연 적격 호출을 요청별로 보고하고 이후20개가 쌓이면 p50/p95·timeout 비율·원 guard 종료를 같은 scope/입력 분모로 대조한다. 표본을 만들기 위한 추가 AI 호출은 없다. 이 5/20건은 관측 보고 주기이며 정책 적용의 신규 표본 gate가 아니다. 시장·입력·provider latency가 다른 자연 before/after 비율을 코드의 인과 효과로 단정하지 않는다.
5. 표본 부족·반전 무효화·quiet 시장에서는 자연 성능 수용 pending이다. HALF_OPEN 성공은 새 lease의 기한 내 schema/semantic 유효 응답으로만 인정한다. PASS를 주문·fill·수익으로 대신하지 않는다.

rollback은 duplicate claim/send, original deadline 연장, source/compatibility 검증 누락, 필수 증빙 유실, crash, 보유/청산 지연, 동일 workload의 확인된 성능 회귀일 때 기존 승인 경로로 수행한다. 이전 릴리스 선택만 바꾸지 않고 함께 결속된 정책·호환성·인계가 유효한 조합으로 복구한다. 과거 PASS·퇴역 episode/widget은 복원하지 않는다. 정상 신호 종료 또는 좋은 후보 부재 자체는 rollback 근거가 아니다.

## 11. 현재 검토 결론

상세계획은 원인 계측 → 실제로 느린 로컬 경로 수리 → 동일 작업량 검증 → 릴리스 인계 → 정상 새 신호 수용 순으로 정리했다. 현행5초·기계/보조 정책·회로·호환성·주문 guard와 필수 기록을 유지한다. 코드 구현·성능 측정·배포·실제 수용은 미실행이며, provider 응답시간 자체의 해결 여부는 이 계획의 로컬 검증으로 확정할 수 없다.

### 후속 계획 리뷰의 보완

실제 `_create_openai_response_with_deadline`, `OpenAITransportObservation`, `capture_ai_request`, `_annotate_analysis_result`, entry circuit 성공 시점과 대조해 다음을 보완했다.

- caller timeout 관측·SDK 실제 완료·미정산 future와 두 queue의 시간을 분리했다.
- 3개 request capture 파일과 payload 내 replay context 구조로 정정하고 필수 실행 증빙/report-only write의 기존 failure 처리·권한을 구분했다.
- response reserve에 실패 전체 시간을 무조건 합산하지 않도록 했으며 transport recovery와 뒤의 Main 거절을 분리했다.
- 전송 전/후 변경의 회귀 기대값과 늦은 물리 전송의 불명 상태를 바로잡았다.
- 기계/AI 의미 동등성과 처리 지연 변화로 인한 유효 소비 증가를 구분했다. 20%는 성능 목표로 두고 신규 보편적 배포 gate로 사용하지 않는다.
- 100개 측정 작업의 독립 표본 오해, 가상 clock과 실측 성능의 혼합, I/O mock 및 이전 회차 future로 인한 측정 오염을 제거했다.

문서 검증과 해시·owner 확인 근거는 [후속 계획 리뷰 영수증](../../tmp/entry-timeout-diagnosis-20261013/plan-review-v2.json)에 남긴다. 실행 코드·운영 checksum·sealed checklist와 다른 작업의 감시 audit는 변경하지 않는다.


## 저장 증가·보고서 freshness를 포함한 후속 구현 범위

10/13 후속 실패와 저장 증가를 함께 재점검한 [구현 리뷰](../audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md)를 현행 실행 근거로 사용한다. 앞의 미실행 표기는 최초 계획 시점이다. 원5초·모델/prompt/schema·원천/계좌/주문/수량/custody guard는 유지한다.

canonical economic append가 성공한 동일 attempt의 반복 ADM snapshot에서 경제 seed/operating context의 frozen code 중복만 attempt/hash 참조로 바꾼다. replay 원본과 failed append는 보존한다. Buy Funnel cache도 proof projection을 유지한 unused-body representation migration만 하며 source/row population·identity·atomic fsync와 변경 감지로 닫는다. 유지보수는 streaming/full census, report는 원 전체 population으로 수행한다. wrapper는 기본 cooldown0과 flock을 사용하고 명시 override 및600초 freshness는 유지한다. 현재/PID/rollback/policy/unique/unverified 원장을 삭제하지 않는다.

최종 v6 guard의 중복 static/configure 재사용은 현재 loader-owned immutable view와 configure/consumed identity가 확인된 경로만 허용한다. fresh prepare와 기존 native claim·scope·requested ref/registry/model/overlay·end pointer 검증은 매번 실행한다. 판정 결과 cache 또는5초 갱신은 금지한다. current source/pointer 변경·cold/unverified 객체는 원 full guard로 돌아간다.

검토한 exact code pair와 wrapper 계약을 같은 immutable candidate에 포함한다. 기존 `DirectFamilyPreopenPolicyHandoff`가 ordered 전환과 machine/auxiliary128경로 소비를, 기존 `AuxiliaryCircuitRecoveryRepair1012`가 같은 attempt의 provider 전·SDK/HTTP/settlement·Main 소비를 확인한다. 정상 cron DONE/report freshness와 cache row parity·바이트 증가율을 함께 확인하고, 전체 Main 성능이나 외부 timeout을 좁은 component benchmark로 완료 처리하지 않는다. EOD와 원10/12→10/13 policy/bootstrap는 재생성하지 않는다.
