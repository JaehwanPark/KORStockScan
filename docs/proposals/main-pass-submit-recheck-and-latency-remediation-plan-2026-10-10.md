# Main PASS 이후 제출 경로 재점검·결함보완·성능개선 계획 — 2026-10-10

## 1. 결정과 현재 적용 상태

**다음 보완의 우선순위는 완료 결과를 꺼낸 뒤의 예외 처리와 정상 PASS의 실제 제출 경로 검증이다.** 기존 PB1~PB3의 구현을 출발점으로 하고, 남은 동기 기록 비용과 제출 사유 연결을 보완한다. 원 5초를 늘리거나 정상 안전 거절을 대기·재시도로 바꾸는 정책 변경은 이 계획에 포함하지 않는다.

§1–§9는 코드 재점검·성능개선 **계획 수립 당시**의 판단과 검증 기록이다. 당시 운영 원장을 재생성하거나 새 AI 표본을 만들지 않고 정적 대조·기존 격리 회귀·축소 반례를 수행했다. 이후 사용자의 구현 지시에 따른 결과는 §10과 연결 audit에 기록한다.

| 항목 | 10/10 재점검 근거 |
| --- | --- |
| 지난 영업일 | 10/8. 10/9는 저장소 운영 달력상 한글날 휴장 |
| 당시 관측 | PID 381039의 19:41:57 기준 정확 AI 시도 8, PASS 4, transport timeout 4. 해당 PASS의 intent/주문 API 시작은 0이며 전체 영업일의 주문 수를 뜻하지 않음 |
| 현재 선택 배포본 | `main-holding-profit-exit-20261009-v4`, commit `70945c53181320d9149ed95167c1e21a42be23d2` |
| 원 수정의 배포 | 10/9 통합 배포에서 PASS 우선 소비·증분 원장·계좌 수요 제한·이력 공유를 포함했고 이후 원장 mixed-row 결함도 보완 |
| 이번 source 대조 | Main·handler·coordinator·trace·dedup·monitor 6개 파일이 선택 배포본과 동일 |
| 실제 Main 소비 | selector의 `actual_pid_consumed=false`, 다음 예약기동 대기. 새 코드의 자연 PASS→제출 성공은 아직 미관측 |
| 다음 기동 준비 | 10/12. 직전 읽기 전용 `next_preopen_readiness --verify`는 최신 commit의 `current_full_contract=pass`, findings=[] |

근거: [원 PASS 4건 조사](../../data/report/auxiliary_compact_adoption/2026-10-08/pass-submit-bottleneck-381039-194157.json), [최초 구현](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md), [통합 배포](../audits/main-integrated-uncommitted-deployment-review-2026-10-09.md), [mixed-row 후속 수리](../audits/main-market-weakness-review-deployment-2026-10-09.md), [현재 selector](../../data/runtime/runtime_release_selection.json), [이번 source·검증 기준](../../tmp/main-pass-submit-recheck-20261010/baseline.json).

계획 수립 당시 10/10 checklist는 없었다. 구현 지시에 따라 [10/10 checklist](../checklists/2026-10-10-stage2-todo-checklist.md)의 `MainPassSubmitRecheckLatency1010`을 실행 owner로 연결했다. 10/9 완료 기록을 오늘 실행 owner로 대체하지 않는다. 다음 기동은 [10/12 checklist](../checklists/2026-10-12-stage2-todo-checklist.md)의 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다. 이 계획은 [통합 R계획](main-residual-capacity-budget-pass-history-bottleneck-implementation-plan-2026-10-08.md)과 [PB계획](main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md)의 후속 기술 범위다. 후속 구현 착수 때 해당 날짜의 Main 실행 owner와 연결하고, 이번 문서 작성에서는 준비에 봉인된 10/12 checklist를 수정하지 않는다.

## 2. 이번에 확인한 공백과 우선순위

아래 반례는 운영 사건의 원인을 사후 확정하는 자료가 아니다. 선택 배포본과 같은 함수의 실제 제어 흐름을 AST로 분리하고 외부 경계를 가짜 객체·clock·예외로 대체한 재현이다. 실제 주문/AI/운영 로그를 생성하지 않았다. [재현 결과](../../tmp/main-pass-submit-recheck-20261010/reproductions.json)에 입력 경계와 출력이 있다.

| ID·우선순위 | 확인한 코드/검증 공백 | 재현·한계 | 구현 owner |
| --- | --- | --- | --- |
| F1·P0 | 결과를 pop한 뒤 예외가 나면 종료 처리가 빠짐 | `_log_entry_pipeline` 예외 주입 시 결과 retained=false·consumed=true·종료 이벤트 0·이전 stock request 필드 잔존. wrapper의 try/finally는 resolver 호출 뒤 시작 | `sniper_state_handlers._resolve_scanner_async_entry_ai`, `handle_watching_state`, coordinator take |
| F2·P0 검증 | 정상 PASS가 주문 의도/제출 함수까지 도달하는 통합 근거 부족 | 기존 bridge 회귀 하나는 `_entry_ai_contract_status` 도착 직후 예외로 끝나며, wrapper 회귀는 resolver를 대체함. 이번 164 PASS만으로 완전한 제출 경로를 인증할 수 없음 | 기존 `test_scanner_async_entry_bridge`, `test_main_integrated_bottlenecks` |
| F3·P1 | accepted 이후 조기 반환의 직접 이유가 누락될 수 있음 | `zero_base_pending_db` 조기 반환을 넣으면 `entry_path_returned_without_terminal_evidence`. 현재 guard 기록은 마지막 pipeline stage를 덮어쓰므로 그 stage가 실제 최종 차단이라는 보장도 없음 | WATCHING 반환 지점·`_async_consumption_guard`·기존 제출 funnel |
| F4·P1 | 서로 다른 전이 ID 사이의 원 판정 신원 충돌을 정상 수락으로 집계 | 같은 PID/start/request의 worker `trace-A`와 accepted `trace-B`를 넣어도 accepted=1·unobservable=0. 현재 충돌 검사는 주로 동일 event ID의 내용 비교 | `submission_bottleneck_monitor.async_disposition_coverage`와 cache reader |
| F5·P1 성능 | 완료 결과 게시 전에 진단 writer가 동기 실행 | 실제 `_finish`에 잔여 100ms·기록 200ms 가짜 clock을 넣으면 ready 게시가 deadline 이후. 이는 대기 의존성 입증이며 실제 디스크가 200ms 걸렸다는 측정은 아님 | coordinator `_finish`/Main poll·기존 pipeline writer |
| F6·P2 경계 | 완결 JSONL 한 행이 준비 chunk보다 크면 영원히 같은 위치에서 실패 | 정상 JSON 한 행 4,194,354bytes에서 2회 모두 offset=0·`partial_or_oversized_row`. 운영에서 이 크기의 행이 있다는 증거는 없음 | `trace_dedup.prepare`, 준비 worker, trace writer의 행 크기 계약 |

운영 파일은 크기와 앞/뒤 최대 2MiB 구간만 읽었다. 10/8 trace는 **416,513,843bytes**, 표본에서 확인한 완결 행 최대는 **1,386,892bytes**다. payload는 **150,913,154bytes**다. 전수 행 크기 조사가 아니므로 4MiB 초과 행의 존재/부재를 결론 내리지 않는다. 대형 파일 복제는 하지 않았다. [제한된 표본 근거](../../tmp/main-pass-submit-recheck-20261010/file-size-sample.json).

## 3. S1 — 원 결과의 예외 처리와 단일 실행 보장

1. Main이 원 request/generation/cache key/claim token과 결과 객체를 인수하는 순간부터 정리까지 하나의 예외 처리 범위를 둔다. resolver 호출 전후를 wrapper의 try/finally 밖에 나누지 않는다. 데이터 검증 거절과 내부 실행 예외의 이유를 구분한다.
2. pop 후 소비 완료 표시를 되돌려 같은 결과를 재실행하지 않는다. 실패 시 그 요청의 실행 상태와 원 custody를 대사하고, 아직 전달 전이면 명시적 비실행 종료, 전달 여부가 불확실하면 unobservable로 기록한다. 기록 실패 자체는 기존 bounded health counter에 남긴다.
3. stock 정리는 현재 request/generation/token이 원 객체와 일치할 때만 수행한다. 후속 claim·다른 종목/owner·기존 보유를 정리하지 않는다. 원 신호의 ack와 결과의 진단 기록은 서로의 실패를 숨기지 않는다.
4. `accepted_to_entry_path`는 기존 공통 WATCHING 후속 처리에 실제로 인계한 경계를 나타내야 한다. 그 전에 남아 있는 native ack·필수 상태 검증의 예외를 accepted로 닫지 않는다. accepted 이후 오류는 아래 S2의 후단 상태로 남긴다.
5. 진단 함수의 실패가 유효 실행을 막는 새로운 guard가 되지 않게 한다. 다만 필수 원천/outbox 저장·native/정책 검증 실패의 기존 의미는 보존한다. 예상하지 못한 실행 예외를 넓은 catch로 삼킨 뒤 BUY를 계속하는 수리는 금지한다.

닫힘: take 전/직후·검증·진단·native ack·공통 후속 진입·intent 전/후에 각각 예외를 넣어 결과 owner, 원 claim, stock 필드, 중복 실행 수를 대조한다. 후단 성공을 확인할 수 없는 경우 정상 terminal을 합성하지 않는다.

### 3.1 재리뷰 보완 — 결과 인수 경계와 모든 폐기 caller

try/finally 안으로 resolver 호출만 옮기는 것으로는 충분하지 않다. 현재 `original_result`는 resolver가 정상 반환한 dict에만 들어 있으므로, pop 뒤 예외이면 wrapper는 여전히 원 객체를 받지 못한다. **결과를 실제 인수한 코드가 원 객체와 인수 여부를 먼저 보유하고 그 범위에서 종료를 책임진다.** wrapper에는 그 동일한 인수 context를 넘기며, peek만 성공했거나 take가 None인 호출은 다른 소비자의 결과를 닫지 않는다. 단순 stock 공용 플래그가 아닌 request/generation/token에 묶인 호출별 상태를 사용한다.

| 경계 | 실행·정리 계약 |
| --- | --- |
| take 전 / 다른 caller가 먼저 인수 | 기존 coordinator 소유 유지 또는 인수 실패 반환. 원 결과의 소비·ack·종료를 합성하지 않음 |
| take 성공 → 공통 경로 인계 전 | 원 객체로 검증·ack·필드 정리를 수행. 실패는 한 번의 비실행 종료 또는 미확정으로 남기고 재큐잉하지 않음 |
| 공통 경로 인계 → 제출 처리 | accepted는 Main 인계를 뜻함. 이후 반환·예외는 후단 결과로 연결하고 소비 전 rejected를 추가하지 않음 |
| intent 기록 또는 broker 경계 도달 후 | `False`/예외만으로 미제출을 단정하지 않음. 기존 intent/outbox/응답의 uncertain·reconciliation을 보존하고 재전송하지 않음 |

리뷰 대상은 WATCHING wrapper에 한정하지 않는다. `kiwoom_sniper_v2`의 target 부재/transport 거절·COMMIT enqueue 거절·commit 전 분기 종료·unused result, handler의 fixed-watch orphan/만료 정리, coordinator의 invalidate/overflow/shutdown에서 `take_completed`/`discard_completed` 결과를 어떻게 종료하는지 함께 연결한다. 해당 caller 중에는 scheduler 로그만 남기는 경로가 있으므로, 원 request의 동일 소비 종료로 연결하고 scheduler 종료와 중복 집계하지 않는다. 공통 API를 쓰는 opening-rotation 경로는 기존 동작 호환 회귀만 추가하며 새 진입 권한을 부여하지 않는다.

정리는 generation/key/token을 잠금 안에서 다시 대조한다. native ack 실패와 stock 정리 실패는 최초 예외를 덮어쓰지 않고 각각 진단하며, 새 claim을 지우지 않는다. 진단 실패만 좁게 격리하고 실행 검증 예외는 기존 상위 오류 처리로 전달한다. 프로세스 강제 종료는 Python finally로 보장할 수 없으므로 기존 영속 원천과 intent의 미확정 인계로 남긴다.

## 4. S2 — 직접 미제출 사유와 판정 신원 연결

- `zero_base_pending_db`, manual veto, 시장/전략 시각, cooldown, quote/source/native 변경, 자금/수량, 가격, 제출 함수 반환의 기존 종료 지점을 열거한다. 기존 guard가 이미 산출한 코드·시각·원천 참조를 작은 실행 결과로 전달한다. 무관한 마지막 로그 메시지를 종료 이유로 채택하지 않는다.
- `entry_path_returned_without_terminal_evidence`는 명시적 미확정이다. 조기 반환의 이유를 찾았다는 의미로 집계하지 않는다. 코드가 정상 반환하더라도 그 이유가 없으면 해당 후단의 결손으로 남긴다.
- 같은 PID/start/request에 속하는 전이들이 evaluation attempt·trace·generation·native 신호·종목/route·정책 hash·원 deadline의 동일한 원 identity를 가리키는지 검증한다. 아직 ID가 생성되기 전인 단계는 null의 허용 범위를 정하고, 이후 non-null 값이 충돌하면 unobservable로 격리한다. event ID만 다르다는 이유로 충돌 검사를 생략하지 않는다.
- 소비 집계는 `PASS = accepted + final rejected + pending + unobservable`의 상호배타적 attempt 수다. accepted 뒤에는 `intent/실제 submit/명시적 후단 차단/후단 미확정`을 기존 funnel로 연결한다. accepted 뒤 가격 거절을 소비 전 rejected에 다시 더하지 않는다. 체결·수익은 별도다.
- 실제 읽은 전이만의 현재 `loaded_evidence_only_full_denominator_unobservable` 상태를 숨기지 않는다. 기존 request/trace의 검증된 PASS ID projection을 같은 관측창에 결합해 전이 자체가 없는 PASS도 드러내며, bounded tail/cache가 창을 덮지 못하면 분모 partial을 명시한다. 새 대형 원장이나 장중 전수 재스캔을 만들지 않는다.
- producer→lossless compact→Sentinel slim cache→monitor에서 필드·원 event ID·단계별 source hash를 함께 검증한다. F4의 서로 다른 trace, duplicate/reordered event, missing receipt, conflicting terminal을 반례로 추가한다. 기존 알림 채널과 의미 기반 중복 제거를 재사용한다.

진단 계약은 기존 PB3의 `decision_authority=report_only`, `primary_decision_metric=pass_to_main_disposition_coverage`, `sample_floor=none`을 승계한다. 이 개선으로 새로운 정책/주문 승인 조건을 추가하지 않는다.

### 4.1 재리뷰 보완 — 반환값·식별자·관측 시각

- `_submit_watching_triggered_entry`의 기존 bool 반환을 임의의 truthy dict로 바꾸지 않는다. 호출별 결과 context에 기존 직접 사유·intent 여부·물리 호출 여부·응답/미확정을 연결하고 기존 caller 계약을 유지한다. `False` 안에는 broker 호출 전 차단과 호출 후 성공 미확인이 모두 있으므로 기존 `broker_submit_attempt_count`, 영속 intent, 응답 근거를 먼저 사용한다. 추가 세부 분류 체계를 새로 만드는 작업은 아니다.
- fixed-watch는 watch admission/generation과 native claim을, 일반 scanner는 scanner generation/promotion을 각각 검증한다. fixed-watch에 scanner promotion을 필수로 요구하지 않는다. 원 `origin_fields`의 기계/보조 hash와 실제 trace/attempt binding을 비교하며 현재 stock의 새 hash로 보충하지 않는다. consumer가 관측하지 못한 identity는 추정 결합하지 않는다.
- coordinator request ID와 Provider request/AI attempt ID의 명시적 대응이 있어야 PASS 분모에 결합한다. 종목·시각 근접만으로 join하지 않는다. PASS 여부 자체가 검증되지 않은 행은 별도 source gap이며, 검증된 PASS의 종료 연결이 없을 때만 위 보존식의 unobservable이다. 알려진 부분 분모와 전체 분모를 섞지 않는다.
- 실행 발생 시각, worker 완료 시각, queue 접수 시각, 물리 기록 시각을 분리한다. 비동기 기록 시 `async_disposition_epoch`를 writer의 현재 시각으로 다시 만들지 않는다. monitor/cache는 정확한 원 발생 시각과 원 request로 관측창·carry-in/out을 판단하며, 기록이 늦게 도착했다고 deadline을 늘리지 않는다. 이전 as-of 산출물은 당시 관측된 근거로 보존하고 늦은 근거는 다음 산출물 세대에 반영한다.
- 현재 emitter의 `emitted_at`/파일 일자는 물리 기록 시각이다. 자정 지연은 원 요청 거래일과 기록일을 함께 보존하고 필요한 인접 일자만 bounded하게 읽는다. lifecycle 전용 날짜 예외를 허위 lifecycle 필드로 차용하지 않는다. 새 필드·구분이 없는 구버전 행은 기존 의미로 읽고 정밀 시각/identity 검증 불가를 명시한다.

## 5. S3 — 남은 처리 비용을 원 deadline 밖에서 준비

### 5.1 완료 전달과 진단 I/O

`_finish`의 worker 완료 기록, resolver의 `scanner_async_result_commit`, accepted 기록, wrapper의 반환 기록이 같은 요청의 critical path에 들어오는 위치를 계측한다. 현재 pipeline raw/compact는 모든 행마다 fsync하는 구조가 아니며 최초 생성/late partition 등 조건에 따라 달라진다. 따라서 모든 지연을 fsync로 묶지 않고 **직렬화·공유 lock·실제 write·해당 시 fsync·summary enqueue**를 나눈다.

ready map에 먼저 넣기만 하고 같은 Main poll 안에서 writer 완료를 계속 기다리면 F5는 해결되지 않는다. **기존 `_SCANNER_OBSERVATION_EXECUTOR`의 단일 관측 worker를 재사용하는 유한 진단 전달 경로**로 구체화한다. 현재 이 executor의 3개 caller는 직접 submit하므로 새 queue만 유한하게 만들어서는 공유 backlog가 제한되지 않는다. 기존 scheduler event·pipeline batch·skip batch를 포함해 접수 수/bytes·실행 중 작업을 제한하고, drain 작업은 동시에 하나만 예약한다. 새 worker를 만들거나 계좌 준비·post-sell BBO 관측 worker로 비용을 옮기지 않는다. 과부하를 Main의 동기 디스크 기록 fallback으로 해소하지 않는다.

비동기 대상은 우선 `entry_async_disposition`과 `scanner_async_result_commit`의 report-only 기록이다. Main이 필요한 내부 상태와 `_async_consumption_guard`의 호출별 사실은 동기적으로 확정하고, 직렬화할 작은 scalar envelope·원 identity·발생 시각을 snapshot으로 넘긴다. mutable stock 참조나 전체 AI payload를 queue에 보관하지 않는다. handler/coordinator에는 sink를 주입하며 Main 모듈을 역 import하지 않는다. 128개 결과 보존 상한과 요청별 최대 전이 수로 queue 상한을 산정하고 이벤트별 bytes·전체 bytes도 고정한다. 크거나 오래된 관측 batch가 원 결과 종료 기록을 무한히 밀어내지 않도록 drain batch를 제한하고 두 종류의 진행을 확인한다. 상한 초과/worker 미기동/종료 시 접수 실패는 명시적 관측 결손이다.

`ProducerSummaryCompactor`는 **raw append 이후의 요약 owner**이며 원문 writer가 아니다. 여기에 submit한 것만으로 raw/compact 저장 성공을 반환하지 않는다. 기존 `emit_pipeline_event`의 동기 caller와 `structured_append_succeeded` 의미는 보존하고, 별도 enqueue 결과는 queued/unavailable로 구분한다. worker에서 기존 raw→compact→summary 경로를 수행한 실제 append 결과만 저장 성공이다. 정상 부하에서는 원문/compact 전이 손실 0을 확인하고, 포화·crash·디스크 오류로 관측이 사라지면 unobservable이며 주문 재전송 권한은 생기지 않는다.

worker는 종료 시 새 접수를 닫고 원 request의 남은 진단을 기존 종료 시간 예산 안에서 drain한다. 종료 대기 초과·부분 저장·동일 event 중복을 대사하며 과거 거래를 재실행하지 않는다. 실패 계수의 hot-path 갱신 자체가 동기 로그/재귀 emitter를 호출하지 않게 한다. 현재 `runtime_performance.failure()`는 일부 호출에서 텍스트 로그를 쓰므로 그 함수 호출만으로 비동기화를 완료했다고 보지 않는다. queue 대기·포화·append 실패도 기존 성능/health 산출물에 남긴다.

필수 request/raw response/trace/outcome와 operating outbox의 정상 저장을 진단 이벤트와 혼동하지 않는다. 필수 저장을 생략하거나 저장 전 성공으로 반환하는 성능 개선은 하지 않는다.

### 5.2 trace 준비·직렬화·잠금

- 현재 개선된 4MiB 준비 chunk와 hot 64KiB suffix 제한을 출발점으로 삼는다. 준비 여부·진척·읽은 bytes·lock 대기·행 크기·첫 응답 비용을 기존 bounded 성능 계측으로 확인한다. 첫 사용/재기동/날짜 전환과 warm 응답을 나눠 보고한다.
- request capture와 response trace의 `_WRITE_LOCK` 내부 직렬화·중복 검사·fsync를 대조한다. 필수 hash/정규화가 동일함을 확인한 immutable bytes를 lock 밖에서 준비하고, writer 경계에서는 파일 generation·dedup·실제 append의 원자성을 보장하는 방법을 우선 검토한다. 준비 순서 변경으로 payload/prompt 저장 전 request가 게시되지 않게 한다.
- F6는 첫 index의 큰 행 때문에 뒤의 모든 index 준비가 굶지 않도록 파일별 진척/실패를 관리한다. 큰 완결 행은 bounded 여러 chunk로 조립하며 메모리·행 크기 상한과 writer/reader의 같은 지원 한도를 정한다. 미완성 행과 상한 초과의 원인을 분리하고 손상 행을 건너뛰어 ready로 만들지 않는다. 상한은 실제 소비 계약과 제한된 크기 조사로 결정한다. 원문 자르기·전체 파일 재읽기·무제한 메모리로 해결하지 않는다.
- 원 일자·inode/generation·완결 offset·namespace·동시 append·trace 성공/outcome 실패·원 행 이후 index 전진 계약을 보존한다. file-generation lease→공유 mutex의 역순 잠금을 다시 만들지 않는다.

큰 행 조립의 **읽은 위치와 검증 완료 offset은 별개**다. 완결·파싱·identity 검증 전에는 key/digest/ready를 게시하지 않는다. 같은 inode의 append는 기존 검증 접두와 조립 중 bytes의 일치가 확인될 때만 이어 읽는다. 파일 교체·축소·접두 변경이면 미완결 bytes뿐 아니라 key/digest/offset과 외부 cache의 이전 ready 참조도 무효화하고 새 세대를 bounded하게 준비한다. partial tail은 파일 크기/세대가 그대로일 때 매 tick 같은 bytes를 읽거나 같은 오류를 반복 기록하지 않는다. 다른 index의 준비는 계속하되 해당 index가 필요한 request/trace를 허위 ready로 만들지 않는다. writer의 행 크기 검증은 기존 지원 데이터와 호환되게 사전 확인하며 원문 저장 성공 후 새 제한 때문에 인덱스만 실패하는 불일치를 만들지 않는다.

### 5.3 성능 수용 기준

같은 입력·동시성·원 응답 도착 clock으로 기존 배포본과 후보를 비교한다. 정상/동시 완료/느린 진단 writer/느린 필수 저장/cold 준비의 부하를 분리하여 각각 3회 측정하고 N·p50/p95/p99/max·읽기/write bytes·미완료/만료 수를 함께 남긴다. 표본이 분위수 해석에 부족하면 개별값과 최대만 보고한다.

필수 성공 기준은 hot 과거 전체 scan 0, 진단 writer 지연이 ready 전달을 선행 차단하지 않음, 정상 원 예산 fixture의 주문 adapter 경계 연결, 중복 실행/늦은 제출 0이다. 정상 부하의 진단 유실·무한 backlog·보호/holding·주문 callback의 반복적인 지연 악화가 없어야 한다. 물리 응답→필수 저장 완료→ready 게시→Main 인수→최종 제출 guard→adapter 호출의 각 구간을 같은 원 요청으로 측정한다. 총 지연도 함께 비교해 기록 지연을 다른 대기나 미집계 실패로 옮기지 않았는지 확인한다.

결정적 fake-clock 검사는 지연 주입 효과와 deadline 경계를 판정한다. 실시간 성능은 동일 환경에서 baseline/후보를 번갈아 반복하고 수요·성공/만료/실패 수·queue 최대 bytes를 같이 보고한다. 계측 잡음에 따른 단일 max 차이나 작은 N의 p99를 새 배포 차단선으로 삼지 않는다. 후처리·Main 전달의 반복적인 개선과 보호 경로의 회귀 부재로 판단하며, 성능이 개선되지 않은 후보는 채택하지 않는다. 이는 기존 거래 threshold 변경 요건이 아니다.

원 19:41 조사의 0.124/0.739/−0.100/0.143초는 **trace 생성 시각의 잔여**다. worker 반환 예산으로 재해석하지 않는다. 고정 입력을 이용한 4.999/5.000/5.001초 경계와 원 epoch/perf 양쪽 만료를 검증하며 새 거래 cutoff를 만들지 않는다. 물리 Provider 응답·필수 저장이 늦으면 정당한 만료로 종료될 수 있다.

## 6. S4 — 기존 검사에서 제출 함수까지 확장

첫 목표는 정상 제출 경로 한 개를 끝까지 닫는 것이다. 실제 outer 완료 수집→coordinator take→WATCHING 공통 처리→`_submit_watching_triggered_entry` **함수 내부**의 기계/AI 증빙·가격·자금·수량·분할/최종 guard→필요한 intent 영속화→`kiwoom_orders.send_buy_order` 경계까지 연결한다. 이 마지막 adapter에만 네트워크 없는 spy를 두며 고수준 `_submit_watching_triggered_entry`를 성공 stub으로 바꾸지 않는다. 계좌/원천/AI의 외부 응답은 고정 fixture, 정책·outbox·DB/파일은 격리 root를 사용하고 실제 판정/수량/증빙 validator를 우회하지 않는다. 주문 adapter 내부 안전 계약은 기존 별도 회귀로 확인하며 이 통합 검사가 broker 수락을 입증한다고 하지 않는다.

단일 initial leg fixture에서 adapter call count=1과 원 attempt/native/가격/수량·intent binding을 확인한다. 기존 여러 leg 또는 순차 정책은 해당 계획의 허용 leg 수·순서로 검사하며 모든 정책을 주문 한 번으로 바꾸지 않는다. fixed-watch와 scanner 및 현재 지원하는 compact-v1/v2 경로를 확장하되 실제 지원하지 않는 조합을 새로 활성화하지 않는다. 반환 False/예외·응답 불확실 사례는 같은 입력으로 재호출해 자동 중복 전송이 없는지 확인한다.

| 반례 | 닫힘 조건 |
| --- | --- |
| 유효 ENTER_NOW+PASS, 지원되는 fixed/scanner·v1/v2 | 단일 initial leg는 동일 원 요청의 adapter 1회; 실제 내부 guard/intent 검증, 새 평가/AI 요청 0 |
| F1 take 이후 예외와 후속 claim 교체 | 이전 객체의 실패/불확실 상태 기록, 후속 필드 삭제 0, 재실행 0 |
| target 제거·COMMIT enqueue 거절·unused result·shutdown | 원 요청의 단일 소비 종료와 scheduler 사유 연결; 폐기 후 silent loss 0 |
| accepted 뒤 manual/time/quote/native/가격/수량 거절 | 원 직접 사유 1개와 소비 상태 보존, submit 0 |
| 함수 내부 receipt 부재/AI 만료/분할 guard 및 intent 뒤 전송 예외 | 호출 전 차단과 호출 후 uncertain을 구분; 영속 intent 보존, broker 거절 합성/중복 송신 0 |
| F4 trace/attempt/hash/deadline 충돌, 역순·중복·tail 누락 | 잘못된 accepted 0, 해당 행/attempt의 결손 표기, 분모 coverage 명시 |
| F5 진단 writer 지연/실패·queue 포화 | 유효 결과의 소유권/전달이 진단 저장 대기를 선행 조건으로 삼지 않음; 진단 결손은 보고 |
| 기존 관측 backlog·worker 미기동·종료·자정 지연 | 접수/저장 성공 구분, bytes/작업 수 제한, 원 발생 시각·관측창 유지, Main 동기 fallback 0 |
| 필수 저장 지연·실패, 원 deadline 직전/직후 | 필수 저장 의미 보존, 만료 후 submit 0, Provider/주문 재전송 0 |
| F6 큰 완결 행·partial tail·다중 writer·rotation/축소/restart | 제한된 진척 또는 명시적 크기 결손, 교체 전 ready/cache 재사용 0, 같은 offset의 무한 재시도 0, 본문·ID 손실/충돌 은폐 0 |

기존 `src/tests/test_scanner_async_entry_bridge.py`, `test_scanner_async_eval.py`, `test_main_integrated_bottlenecks.py`, `test_ai_decision_trace.py`, `test_submission_bottleneck_monitor.py`와 실제 영향받은 제출/수량·pipeline writer 회귀를 확장한다. queue 소유 코드는 기존 Main 관측 executor와 `src/utils/pipeline_event_logger.py`, 소비·종료는 scalping/handler, 집계는 monitoring에 둔다. 새 engine-root 모듈을 만들지 않는다. helper 검사나 고수준 제출 함수 진입에서 끊는 검사는 S4 완료 증거로 사용하지 않는다.

## 7. 구현 순서·배포·남은 자연 확인

1. **S1+S4 정상 경로**: 기존 실패 반례와 단일 initial leg 통합 fixture를 먼저 고정하고 예외/소유권을 수정한다. 정상 PASS가 실제 내부 guard를 거쳐 adapter에 연결되는 것을 먼저 닫는다. 추가 진단 분류의 완성을 기다리며 이 정상 경로 수리를 미루지 않는다.
2. **S2**: F3/F4 직접 이유·신원·분모를 writer와 monitor까지 연결한다. 기존 주문 custody와 관측 기록의 권한을 구분한다.
3. **S3**: F5 동기 진단 대기와 trace 비용을 같은 입력으로 개선한다. F6는 운영 발생을 주장하지 않는 저장 경계 수리로 검증하며 원장 재설계나 과거 전수 복제를 시작하지 않는다.
4. 영향 source→consumer 코드리뷰·반례 수정·재리뷰→표적 pytest/compile·diff 검증을 닫는다. protocol/계좌 call 변경이 실제 필요해지면 당시 공식 Kiwoom reference gate를 먼저 수행한다. 이 문서 작성에서는 wire/API 변경을 하지 않았다.
5. 후속 실행 지시의 배포 범위에 따라 최신 selector/dirty/PID·원 10/8 source·10/12 대상 정책을 다시 고정하고 불변 릴리스를 만든다. 동일 정책 code binding, 필요한 strict/finalization/PREOPEN을 정식 절차로 갱신한다. 과거 prepared PASS를 복사하지 않고 EOD/AI 비교 전수를 재실행하지 않는다. rollback에서도 퇴역 owner를 복원하지 않는다.
6. 예약기동 뒤 실제 PID/root/commit와 기계·보조 정책 소비를 먼저 확인한다. 삼성·비삼성 및 PRE/REGULAR/AFTER에서 **관측된** PASS만 원 요청으로 추적한다. 새 release에서 유효 PASS→제출 또는 정확한 기존 guard 종료를 확인할 때까지 자연 수용은 미관측으로 유지한다. 표본을 만들기 위한 수동 주문·AI 호출을 하지 않는다.

초기 정책 재선정·승률/EV 재승인·최소 실제 체결 수를 코드 수리의 추가 요건으로 두지 않는다. 지연 수리가 모든 PASS의 주문을 보장하지도 않는다. 아직 남은 것은 코드 경계 수정과 실제 장중 검증이며 이미 완료한 연구를 다시 실행하는 일이 아니다.

## 8. 이번 점검과 계획 검증

- 기존 격리 회귀: `test_main_integrated_bottlenecks.py`, `test_scanner_async_entry_bridge.py`, `test_ai_decision_trace.py` **164 passed / 5.10초**. 기존 검사의 성공과 새 반례의 발견은 양립한다.
- F1/F3/F4/F5는 실제 함수 제어 흐름의 축소 실행이며 전체 Main/실시장의 재현은 아니다. F6는 4MiB 합성 파일을 사용하고 바로 삭제했다. 근거 JSON은 작은 `tmp/main-pass-submit-recheck-20261010/`에만 보존한다.
- 오늘 실행 checklist 부재를 명시했으며 10/9·10/12 checklist 바이트는 보존한다. 10/12 SHA 기준은 `9e7d9f001a13cfac3b0fbd566bcfa860bd598ce41a9d1280437dcccaefff40a3`이다.
- 계획 3개를 재리뷰하고 로컬 링크/anchor **82개 결손 0**, print-only parser **20항목·10/12 `DirectFamilyPreopenPolicyHandoff` 1개·경고 0**, `git diff --check`를 확인했다. 위 6개 source와 10/9·10/12 checklist SHA도 재대조해 변경이 없음을 확인했다. 새 계획 파일의 공백 검사도 별도로 통과했다.
- 이번 변경은 계획 1개 신설과 기존 계획 2개의 상태·후속 범위 연결이다. 새 구현용 pytest/compile·실측 성능 비교·정책 발행·배포·재기동·장후 재생성·외부 sync는 실행하지 않았다. 기존 164건의 회귀와 축소 반례는 후속 S1~S4 구현 완료를 뜻하지 않는다.

## 9. 후속 계획 리뷰에서 보완한 사항

| 계획의 공백 | 보완 내용 |
| --- | --- |
| resolver를 try 안에 넣어도 예외 시 반환 dict의 원 객체를 받지 못함 | §3.1의 인수 context와 단계별 종료 책임, 모든 take/discard caller, 후속 claim의 잠금 안 비교 |
| 고수준 제출 함수를 spy로 바꾸면 내부 False 원인을 검증하지 못함 | §6의 실제 제출 함수 본문·intent·adapter 경계 검증과 단일/다중 leg 구분 |
| 기존 bool 반환을 변경하거나 False를 무조건 미제출로 집계할 위험 | §4.1의 caller 호환, 호출 전 차단/intent/물리 호출/응답 미확정 구분 |
| 비동기 원문 writer가 이미 있는 것으로 가정 | §5.1의 기존 관측 executor와 3개 caller의 유한 접수, 요약 owner와 raw append 성공 분리 |
| queue가 mutable stock·flush 시각을 사용하면 원 판정/관측창이 바뀜 | 고정 scalar envelope·원 시각·실제 기록 시각·구버전/자정 carry 처리 |
| 큰 행의 부분 읽기만 전진하면 검증되지 않은 index를 게시할 수 있음 | §5.2의 읽기 cursor/검증 offset 분리, 세대 변경·partial-tail 진척과 writer 호환 |
| 작은 표본의 p99/max가 새로운 자의적 차단 요건이 될 수 있음 | §5.3의 결정적 경계 시험과 동일 부하 반복 비교·실패/누락 분모 포함 |

이번 재리뷰는 위 구현 경계를 구체화한 문서 보완이다. §8의 164건은 앞선 점검 결과이며 이번 문서 리뷰에서 재실행한 수치가 아니다. 신규 코드 검증·성능 실측·배포/재기동은 후속 구현 단계에 남아 있다. 변경한 계획 3개의 로컬 링크/anchor **82개 결손 0**, print-only parser **20항목·10/12 handoff owner 1개·경고 0**, tracked/untracked 공백 검사를 재확인했다. 관련 6개 source와 봉인된 10/9·10/12 checklist 바이트도 동일하다. 10/10 checklist 부재는 §1처럼 남겨 두었으며 새 실행 owner나 런타임 권한을 만들지 않았다.

## 10. 구현·반복 리뷰 결과

사용자의 후속 구현 지시로 S1–S4를 구현하고 인수/폐기/원 판정 신원/직접 반환 사유/진단 저장/큰 행 준비/실제 제출 adapter 경계를 반복 리뷰·보완했다. [구현 리뷰·검증·성능 근거](../audits/main-pass-submit-recheck-latency-implementation-review-2026-10-10.md)와 [10/10 실행 owner](../checklists/2026-10-10-stage2-todo-checklist.md)에 최종 검증을 기록한다. §8·§9의 164건과 미구현 표현은 계획 수립 당시 기록이며 현재 구현 검증과 구분한다.

원 5초와 기존 안전 guard·필수 저장을 보존했다. 비동기 관측 접수와 실제 저장 성공을 구분하며 정상 부하의 원문/compact 유실을 검증한다. 응답 없음/예외 후 같은 PASS의 자동 재전송과 adapter 직전의 원 deadline 만료도 보완했다. 기계/보조 정책 재선정이나 AI 비교 원장 재생성은 수행하지 않았다.

최초 구현 지시는 구현·리뷰·수정보완까지였으며 봉인된 10/12 checklist를 변경하지 않았다. 후속 사용자 지시로 재리뷰 후 배포와 다음 영업일 정상기동 점검이 승인됐다. 같은 10/10 owner에서 불변 릴리스 배포, 동일 정책 코드 결속, 10/12 격리 PREOPEN 준비·전체 계약 및 예약 경로를 검증한다. 10/12 자연 PID·PASS 수용은 기존 DirectFamilyPreopenPolicyHandoff가 소유한다.

승인 배포를 `main-pass-submit-20261010-v1` / `b26aae701314d91a75056fac576b5f460beb3c06`으로 완료했다. 재리뷰 2,424건·릴리스 326건 통과, [최종 기동 준비](../../data/report/main_pass_submit_deployment/2026-10-10/final-readiness.json)의 10/12 전체 계약 PASS·finalization 결손 0·예약 8개 routing PASS를 확인했다. 기계/보조 정책 계약 코드가 그대로여서 code-refresh 후보를 새로 발행할 필요가 없었고 기존 정책·원 장후 결과·봉인 checklist를 보존했다. 웹은 같은 릴리스로 재기동했으며 Main은 10/12 07:55 예약기동 전으로 실제 PID·자연 PASS 수용을 주장하지 않는다.
