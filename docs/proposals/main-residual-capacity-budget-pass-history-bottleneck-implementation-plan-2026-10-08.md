# Main 잔여 병목 통합 개선계획 — 용량 조회·5초 예산·PASS 소비·430봉

**2026-10-08 후속 구현 상태:** PASS 소비·잔여 병목·430봉·비상시감시를 통합 구현하고 반복 리뷰·회귀를 수행했다. 10/8 구현 완료 때는 배포를 보류했으며, **10/9 후속 사용자 지시로 전체 미커밋 통합 배포가 승인됐다**. 현재 배포·준비 검증 상태는 [통합 배포 리뷰](../audits/main-integrated-uncommitted-deployment-review-2026-10-09.md)에서 확인한다. H4의 수정주가/WS 동등성 미입증 범위는 REST를 유지한다. [구현·검증·한계 기록](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)을 현재 실행 결과로 사용하며 아래의 계획 작성 당시 승인·미실행 문구는 그 시점의 이력이다.

작성일: 2026-10-08 KST. 상태: **코드·관측 근거를 대조한 구현계획**. 사용자의 후속 지시에 따라 430봉 단독 개선에서 아래 네 병목 전체로 범위를 확대했다.

## 1. 목표·owner·범위

정상 원천과 유효한 원 신호를 가진 기계 `ENTER_NOW`·보조 `PASS`가 기존 5초 예산 안에 Main의 최종 검증·주문 의도 경로까지 전달되도록 한다. 무신호 계좌 조회와 중복 분봉 조회를 줄이고, 모든 실제 비진입 결과를 해당 판정의 명시적인 소비·거절 영수증으로 연결한다.

실행 owner는 [10/8 체크리스트](../checklists/2026-10-08-stage2-todo-checklist.md)의 기존 `DirectFamilySourceRepairMainMechanisticEntry` 하나다. [B0~B7 계획](main-post-warmup-latency-rest-ws-bottleneck-remediation-implementation-plan-2026-10-08.md)의 완료 구현을 재실행하지 않고, 19:30 관측으로 확인한 후속 결함을 R0~R5로 인계한다. [430봉 상세계획](main-430-bar-shared-history-and-incremental-refresh-implementation-plan-2026-10-08.md)은 본 계획 R4의 구현 명세다. 기존 [지연 계획](main-evaluation-loop-latency-remediation-plan-2026-10-08.md), [REST/WS 계획](main-rest-api-ws-substitution-and-load-reduction-plan-2026-10-08.md), [compact 인계](main-auxiliary-compact-contract-intraday-adoption-implementation-plan-2026-10-08.md)의 별도 승인과 진행 작업을 보존한다.

작업 중 같은 B0~B7 문서에 추가된 **§15 PB0~PB4 PASS 연결 계획**도 대조했다. 본 문서는 네 병목의 통합 순서·capacity·신호 준비·430봉을 소유하고, PB 명세는 같은 변경을 구현하는 세부 계약으로 재사용한다. 대응은 `R0↔PB0/PB3`, `R2a↔PB1/PB3`, `R3↔PB2`, `R5↔PB4`다. 별도 worker·terminal writer·시험/배포 작업을 중복 생성하지 않는다. PB의 기존 안전 우선순위, Main 차례 전의 deferred 관측, writer→projection→monitor 소비 계약을 함께 따른다. quote/source 거절 후 대기·재시도 기능은 추가하지 않는다.

이번 산출물은 계획·문서 검증이다. 원 신호 TTL·정책 조건·provider 모델/횟수/간격·API quota·실시간 원천·broker/account/order/수량/cooldown/manual veto/custody·hard safety를 변경하지 않는다. Main-only와 퇴역 위젯·에피소드 OFF를 유지한다. 실제 배포·재기동은 구현 검증 후 당시 유효한 사용자 승인과 기존 handoff로 처리한다.

## 2. 근거와 아직 확정하지 않은 부분

기준은 [19:30 REST/WS·지연 관측](../audits/main-latest-release-post-warmup-rest-ws-monitoring-2026-10-08-1930.md)과 [별도 PID/소비 점검](../audits/main-latest-release-pid-monitoring-to-1930-2026-10-08.md)이다. 주 계수 창은 19:05:06~19:29:19, release `main-retired-postclose-cleanup-20261008-v1`, Main PID `381039`다. 이는 당시 관측 영수증이며 구현 시 선택 릴리스·PID·작업본 차이를 다시 확인한다.

| 병목 | 확인한 사실 | 코드상 보완 지점 / 확정 한계 |
|---|---|---|
| 무신호 용량 사전 조회 | `kt00011` source-only prefetch 1,403/1,849회, 75.88%. 별도 bounded tail의 1,497 read 중 1,479회는 만료/무효 receipt 재충전 | `_resolve_scanner_async_entry_ai`의 `waiting_native_signal` 반환 직전에도 `_request_entry_capacity_preparation` 호출. pending deadline이 예약 시각+5초이며 native claim과 결속되지 않음 |
| 신호별 예산 부족 | 워밍업 이후 ENTER 8건의 기계 캡처 시 신호 나이 1.780~2.646초. native→claim 최대 2.490초, source 준비 최대 1.307초, capacity 최대 .678초 | 서로 다른 건의 최대값은 합산하지 않는다. 실제 critical path·queue/전송/계산 분리 필요 |
| PASS 이후 소비 연결 | PASS trace 나이 약 4.261~5.100초. 네 건 모두 보존 outbox는 `response_received`; `intent_assigned` 미관측 | 기록 시각은 함수 완료/최종 Main 소비 시각이 아니다. 네 건 모두 TTL 탈락이라고 단정할 수 없음. 최종 소비·거절 연결 보강 필요 |
| 430봉 REST 의존 | WS 체결 재사용 11/12, 분봉은 REST 유지. 주 창 `ka10080` source-only 73회 + runtime-required 14회 | 공통 430 하한, 한 세션 WS capacity, raw/adjusted 의미 차이. R4에서 실제 소비 window와 저장·갱신 계약을 구분 |

소스 재검토에서 두 가지를 추가 확인했다.

- Main에는 이미 `coordinator.completion_event.wait()`가 있다. 따라서 “1초 sleep을 없애면 해결”로 설계하지 않는다. signal-ready의 전달, 완료 결과 drain 이후 fixed-watch handler까지의 우회, 이벤트 clear 경합·실제 queue 체류를 검사한다.
- outer drain은 fixed-watch 결과를 native WATCHING handler에 맡긴다. 그 전에 `main_fixed_watch.observation_ready`가 `continue`할 수 있고, handler에서도 결과 소비 전에 원천 gate가 반환할 수 있다. 완료 결과의 **최종 검증을 실행하는 진입로**를 독립시켜야 한다. 최종 원천·주문 검증 자체는 보존한다.

최초 `response_validate=4.422초`에는 일일 약 416MB trace의 `_load_seen`이 유력한 기여 요인이다. 현재 request/payload/prompt 초기화 함수는 있으나 response trace/outcome ID 초기화는 별도다. 하위 계측 없이 4.422초 전체를 원장 읽기 비용으로 귀속하지 않는다. 초기 기동/첫 사용 비용과 이후 steady-state 표본을 별도로 보고한다.

## 3. 실행 순서와 의존성

| 단계 | 우선순위 | 작업·선행 관계 | 종료 증거 |
|---|---|---|---|
| R0 | P0 | 네 자연 PASS·native claim·outbox·물리 전송과 caller 목록을 고정하고 최소한의 단계/terminal 계측 추가 | 정확 attempt 단위 clock·guard·미관측 상태. 과거 미보존 사유는 `unknown` 유지 |
| R1 | P0 | 무신호 capacity 예약 차단. R0 식별자와 기존 source-only worker 재사용 | 무신호/무수요 fixture prefetch HTTP 0, 실제 유효 신호의 exact capacity 보존 |
| R2a | P0 | 완료 결과를 독립된 Main 소비 경로로 전달. R0 계측과 함께 구현 | 유효 결과는 기존 guard까지 도달, 거절도 동일 attempt terminal. 중복 의도/재전송 0 |
| R2b | P1 | native-ready→claim 지연·source 준비 중복·deadline 전달 개선 | 같은 원 5초 내 준비시간 감소. Main/WS callback blocking·순서 역전 없음 |
| R3 | P1 | response/outcome dedup 초기 전체 읽기를 신호 경로에서 제거 | 원 증빙·중복 방지 보존, 첫 응답/정상 응답의 로컬 처리 분리 및 감소 |
| R4 | P2 | 430봉 H0~H5: REST 공통 이력/분 갱신→실제 consumer 필요 window→검증된 WS | 동등한 특징/기계판정, 중복 호출 감소, freshness·provenance 보존 |
| R5 | 통합 | 반복 리뷰·회귀·실제 launch 계약·기존 handoff·자연 관측 인계 | 코드/배포/PID/자연 소비/성능을 각각 입증 |

첫 구현 단위는 **R0+R1+R2a**다. 불필요한 조회와 PASS 소비 누락을 먼저 해결하고 R2b/R3/R4를 작은 변경으로 연결한다. R4의 WS 합성이 미지원이어도 앞선 수리와 동일 REST 재사용은 진행한다. 아래 단계별 수용은 성능·계약 검증이며 새 정책 선발 기준이 아니다.

이는 묶음 전체를 기다리는 배포 조건이 아니다. PB1/PB3의 결과 소비 수리가 먼저 닫히면 독립 인계할 수 있다. R1은 호출 부담 때문에 통합 우선순위를 P0로 두지만 PASS 처리 수리를 지연시키지 않는다. 첫 응답 후처리 R3/PB2가 미해결인 상태는 전체 PASS 경로 완료로 표시하지 않는다.

## 4. R1 — 용량 조회를 실제 수요에 결속

### 4.1 예약 조건과 caller 전수 연결

[sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py)의 `_request_entry_capacity_preparation`, `_prefetch_entry_capacity_for_async_evaluation`, `prepare_pending_entry_capacity`, `_read_entry_capacity_snapshot` 및 resolver·inflight 재예약·경제성 observer의 모든 caller를 함께 수정한다.

1. `waiting_native_signal`의 무조건 예약을 제거한다. coordinator/generation 미지원인 `not_enabled` 경로도 예약을 기본값으로 두지 않는다. legacy caller는 생존하는 실제 initial-entry 수요 증거를 명시적으로 전달해야 한다.
2. 예약에는 `demand kind + 원 claim/generation + exact attempt/request ID + 원 deadline(epoch/monotonic) + item/route/session + 현재 price/account/deposit/inventory identity`를 연결한다. fixed-watch는 native claim/opportunity, 일반 scanner는 기존 `ScannerGeneration`과 실제 승인된 평가 context를 사용한다. scanner에 존재하지 않는 native token을 새 필수값으로 요구하지 않는다. source-only probe는 실주문 claim으로 승격하지 않는다. 아직 만들지 않은 evaluation ID는 null+생산 전 상태로 두고 기존 request ID를 사용한다. 원 수요를 잃은 예약에 `now+5초`를 새로 부여하지 않는다. 동일 native 기회의 복수 정책 hit는 예약 하나로 결합한다.
3. 가격 변경 coalescing은 **같은 살아 있는 수요**에서만 수행하고 이전 가격의 미전송 예약을 대체한다. claim 취소/만료·session/route/재고 변경은 미전송 예약을 폐기한다. 이미 전송한 read는 결과·시각을 보존하되 만료 claim을 부활시키지 않는다.
4. inflight-other-frame 재예약과 ENTER 경제성 observer의 후속 예약에도 원 claim/수요를 전달한다. `{}`와 가격만으로 독립 예약을 되살리지 않는다. 이미 동결된 판정의 경제성 결손을 뒤늦은 조회로 소급 보충하지 않는다.
5. BLOCK/RECHECK·무신호 관측은 현재 허용된 정확한 기존 receipt만 재사용한다. receipt 부재는 원 관측 결손으로 남고 cache를 채우기 위한 반복 HTTP를 만들지 않는다. initial sizing·pre-submit·residual·scale-in의 기존 필수 계좌 조회는 이 차단 조건에 넣지 않는다.

### 4.2 어느 시점에 조회할 것인가

초기 변경은 **기존 live 평가 context가 유효한 worker의 최종 입력 refresh 시점**에 source-only prefetch를 수행한다. fixed-watch의 native claim과 일반 scanner의 승인된 generation/context를 각각 검증한다. 이 경로는 이미 있으므로 무신호 예약 제거를 이유로 새로운 직렬 조회를 추가하지 않는다. R0에서 이 read가 기계/보조 입력·경제성 기록 중 무엇의 선행 조건인지 구분한다.

기계 계산과 무관한 observer-only 증거임이 코드로 확인된 부분만 후속으로 critical path 밖에 둘 수 있다. 실제 필수 입력은 준비 전에 확보한다. AI 전송 중 capacity를 미리 다시 조회하는 주기 작업은 만들지 않는다. 주문 직전 2초를 넘은 증빙은 기존 sizing/pre-submit의 fresh read 대상이며, 이를 없애려고 TTL을 늘리지 않는다.

기존 exact 재사용은 가격·계좌·deposit·재고/custody·source hash를 모두 검증한다. source-only entry receipt의 2초와 non-entry reuse-only의 기존 5초는 별개다. 5초짜리 관측용 자료를 initial execution 승인에 쓰지 않는다. signal/frame별 single-flight는 보존하며 재시도·defer는 기존 source-only 예산/우선순위를 따른다. 필수 read가 speculative read 뒤에서 무제한 기다리지 않게 한다.

수용: 무신호 fixture에서 `entry_capacity_prefetch` physical=0, 유효 claim별 중복=0, 가격·계좌·재고 변경 시 stale reuse=0. 자연 비교는 동일 watch/session·claim 수와 관련 필수 요청량을 함께 보고한다. 감소율 75.9%를 확정 절감량으로 약속하지 않는다. 실제 신호/필수 조회와 시장 부하에 따라 달라진다.

### 4.3 관측 경로의 추가 조회와 예산 전달

코드 대조에서 `_resolve_scalp_cash_budget_context`는 `_read_entry_capacity_snapshot`에 preparation deadline을 전달하지 않으며, `_observe_entry_economics_before_ai`의 ENTER_NOW 경로는 캐시 miss 시 추가 source-only HTTP가 가능하다. 또한 공통 transport의 `_ENTRY_SOURCE_BUDGET` 적용은 현재 `api_id.startswith('ka')`에 한정된다. **기존 context manager로 감싸기만 하면 `kt00011`까지 제한된다고 가정하지 않는다.**

| 경로 | 허용 수요·deadline | 보완 |
|---|---|---|
| fixed-watch/scanner 최종 입력 준비 | 원 live request context의 epoch/perf, 검증된 source-only purpose | 최종 exact price에서 prefetch 또는 유효 receipt 재사용 |
| pre-AI 경제성 ENTER 관측 | 같은 입력·평가 request, 경제성 관측 봉인 전 원 budget의 남은 부분 | 정확히 일치하는 준비 증거를 우선 사용. 기존 원천 계약이 허용하는 추가 조회에도 원 budget과 실제 수신 시각을 전달; 없거나 만료되면 결손 기록. 이미 봉인한 경제성 기록은 소급 보완하지 않음 |
| BLOCK/RECHECK 또는 과거 동결 관측 | 기존 reuse-only 계약 | 새로운 계좌 HTTP·만료 후 재예약·현재 가격으로 소급 보완 없음 |
| detached pending worker | 원 request와 수요 생존·generation 대조 | pop 후 실제 전송 직전에도 재확인; 예약 payload가 `code/price/deadline`만인 옛 형식이면 새 신호 권한으로 사용하지 않음 |
| live sizing/pre-submit/residual/scale-in | 기존 필수 계좌·주문 단계 계약 | source-only 준비 제한을 전역 적용하지 않고 기존 실행 guard/조회 유지 |

명시적 capacity 준비 budget 인자를 wrapper→read coordinator→물리 전송 경계까지 전달한다. 적용 범위는 exact live 준비/관측의 `source_only kt00011`로 제한하고, `kt` 전체나 BUY/SELL/CANCEL·잔고/exit 호출에 entry TTL을 씌우지 않는다. admission 대기·connect/read·retry 직전과 응답 반환 시 epoch/perf 잔여를 검사한다. 전송 후 deadline을 넘긴 응답은 물리 결과로 보존하되 해당 claim의 fresh 증거로 승격하지 않는다. 예외 상태는 `deadline expired`, `local deferred`, `HTTP attempted`, `contract invalid`로 구분한다.

route/item/session은 로컬 수요 binding이다. 현 `kt00011` wire는 정규화된 6자리 종목과 가격을 사용하므로 `_AL`/`_NX` 또는 새 route 필드를 계좌 API payload에 임의 추가하지 않는다. 동일 receipt를 재사용해도 각각의 consumer가 현재 수요 binding과 계좌/가격/재고 identity를 검증한다.

## 5. R2 — 원 5초 안의 전달·준비·최종 소비

### 5.1 R0에서 고정할 시계와 영수증

`native event → ready publication → Main claim → prepare queue/start/end → final source refresh → capacity read → machine capture → provider enqueue/HTTP start/end → response validate/durable append → coordinator ready → Main take → guard result → intent assignment`를 같은 attempt로 결속한다. `decision_ts`·HTTP 응답 수신·worker 완료·Main 처리 시각을 별도 필드로 남긴다.

KST epoch는 원 사건 연결에, monotonic은 프로세스 내 예산/경과에 사용한다. PID/start identity를 기록해 다른 프로세스의 monotonic 값을 직접 빼지 않는다. 준비 단계의 병렬 구간은 중복 합산하지 않고 실제 critical path를 계산한다. 기존 계측에 식별자/누락 경계만 추가하고 per-tick 대형 로그·새 대형 원장을 만들지 않는다.

### 5.2 R2a 독립 Main 완료 소비

소유 코드는 [Main loop](../../src/engine/kiwoom_sniper_v2.py), [coordinator/commit guard](../../src/engine/scalping/scanner_async_eval.py), `sniper_state_handlers`다. 새로운 동시 주문 thread를 만들지 않는다.

1. outer drain에서 fixed-watch 결과를 단순히 WATCHING 재평가로 넘기는 경로를 **Main 전용 완료 처리 함수**로 연결한다. 신규 signal의 source gate·스캔·반복 준비 앞에서 결과를 take하고 최종 guard로 진입한다. 기존 handler의 완료 처리도 같은 함수로 위임하여 실행 owner를 하나로 만든다.
2. take→guard→terminal/commit의 소유권을 원자적으로 정한다. `drain_completed`의 알림 목록과 `take_completed`의 pop 저장소를 구분한다. 저장된 원 request ID/generation/cache key로 take하며 새 trigger/last-AI-time으로 key를 다시 만들지 않는다. Main으로 이관 중인 결과도 기존 미처리 용량과 동일 요청 재dispatch 차단에 포함한다. 동일 결과를 loop/handler/orphan 처리에서 두 번 소비하거나 조용히 제거하지 않는다. 정리/ack는 꺼낸 객체의 token과 현재 필드를 비교해 그 요청의 필드만 제거한다. bounded ready cache의 eviction도 exact terminal 사유를 남긴다.
3. 이미 만료된 결과를 식별하기 위해 신규 `FixedWatchGeneration.from_claim` 성공부터 요구하지 않는다. 결과가 보존한 원 identity로 수신 증거를 연결한 뒤, 기존 `validate_scanner_async_commit`와 native 검증으로 `expired/superseded/source-invalid`를 명시한다. 만료 identity를 정상 current generation으로 만들어 주문시키는 우회는 금지한다.
4. 현재 WATCHING 상태·활성 policy/generation·native path 생존·exact route·fresh quote·position/pending order·cooldown·manual veto 등 기존 검사를 그대로 수행한다. 현 `validate_scanner_async_commit`의 `quote_stale_or_missing`, `cooldown_active`, state/route/native 불일치는 최종 거절이며 fresh quote를 기다리는 재검증으로 바꾸지 않는다. `deferred`는 아직 Main 차례를 기다리는 원 완료 객체의 관측 상태만 뜻한다. Main이 가져오면 accepted/rejected를 정하고, 원 deadline 만료는 expired로 처리한다. 신규 신호에 대한 AI 분석 cooldown과 주문 cooldown을 분리해 후자는 유지한다.
5. 통과한 결과는 기존 async/inline 판정이 합류하는 후속 처리로 전달한다. prepared context·raw/decoded binding·last-AI/provenance 갱신과 기존 sizing/최종 submit guard/intent 생성까지 같은 owner를 사용한다. handler가 동일 AI를 다시 호출하거나 Main 소비 전 상태를 먼저 바꾸어 자기 결과를 무효화하지 않게 한다. 완료 처리 후 같은 loop의 신규 평가 분기로 재진입하거나 수량 계산·의도 생성을 두 번 수행하지 않는다. 후단 계좌·가격·수량 guard의 정당한 거절은 유지한다.
6. 기존 fast exit/SELL/cancel/체결·계좌 reconciliation 우선순위를 유지한 뒤 완료 queue를 제한된 batch로 처리한다. holding/exit·필수 계좌/주문 관리가 굶지 않도록 한다. worker/WS callback은 readiness 알림과 불변 결과 전달만 한다. DB/주문 mutation은 Main thread의 기존 lock 경계 안에서만 수행한다.

현재 completion event를 재사용하되 `queue 확인 → wait → clear` 사이의 lost wakeup과 기존 drain 이후 재처리 누락을 테스트한다. 단순 polling 단축이나 busy-loop로 성능을 얻지 않는다. 수신·소비 완료가 이미 있는 경우는 새로 구현했다고 표시하지 않고 실제 caller 연결과 경합 결함만 고친다.

이벤트는 알림이고 queue가 실제 상태다. 게시 sequence와 pending 확인/clear를 같은 동기화 경계에서 연결하여 새 게시를 지우지 않게 한다. 일반 scanner의 scheduler COMMIT과 fixed-watch의 Main take를 구분하고, drain 뒤 `_ready`에 남아 있는 값을 계속 새 알림으로 세어 busy-loop를 만들지 않는다. queue 확인 직전/직후 완료, clear 직전 완료, batch 한도 후 잔여, 만료/종료 drain을 각각 재현한다. slow I/O를 기존 ENTRY/WS lock 안에 넣어 소유권 원자성을 얻지 않는다.

### 5.3 R2b 신호 전달과 준비 단축

비상시감시의 `no_current_operating_signal` 후속은 [NS0~NS5 상세계획](main-nonfixed-native-signal-observation-and-consumption-remediation-plan-2026-10-08.md)이 소유한다. 15~20초 후보 대기·60/120초 branch 이력·60초 queue watchdog을 함께 대조하고, machine-only의 비소비 관측→Main admission→원 native event의 단일 실행 claim을 연결한다. NS2/NS3는 본 R2b의 실제 probe caller 보완이며 별도 신호/주문 owner를 만들지 않는다. 장기관측은 기존 5개 상한·공정성·source lifecycle 검증과 묶고, 원 TTL 연장이나 R4 REST 분봉의 native tick 대체로 해결하지 않는다. PB/R2a의 PASS 이후 수리는 NS1 장기관측 완료를 기다리지 않는다.

NS 후속 리뷰는 ready 알림 이후의 scanner 결과 소비까지 포함한다. 동기 panel fetch를 단일 source 작업으로 격리하고 scanner는 queue의 단일 writer, Main은 admission/실행 owner를 유지한다. EventBus callback은 전달만 하며 기존 단일 lease의 adoption ACK·원 interval·expected-event claim과 epoch/perf deadline을 보존한다. 기계 pin 밖 adapter를 우선 사용하고 pinned 파일 변경 시에는 NS §9.1의 별도 code-only/loader 계약을 함께 닫는다. 이 구체화는 R1 계좌 예약·PB 완료 소비·R4 분봉 owner를 대체하지 않는다.

- native detector의 ready publication이 Main을 깨울 수 있는지 확인한다. completion 알림과 native-ready 알림은 사유/sequence를 구분한다. WS callback에서는 작은 queue/event publish만 하고 REST·AI·DB·긴 복사를 실행하지 않는다.
- detector 원 event epoch/확인점·policy generation·claim token을 유지한다. 알림 중복은 기존 기회 key로 결합하고 “최근 tick”으로 원 기회를 새로 생성해 5초를 갱신하지 않는다. source 변경/epoch 재접속/동시 branch도 원 attribution을 보존한다.
- 기존 worker의 tick→candle→부가 원천→capacity 구간에서 동일 snapshot·파생값의 재계산을 줄인다. R4 완료 전에도 기존 유효 cache/WS 체결 재사용을 유지한다. final price/tape/quote refresh는 건너뛰지 않는다.
- 독립 source I/O를 병렬화할 필요가 있으면 먼저 의존성과 공유 read 예산을 입증한다. 별도 connection·thread/동시 호출 확대를 기본 해법으로 두지 않는다. 가격에 종속된 exact capacity는 준비 초반 가격과 무분별하게 병렬화하지 않는다.
- 원 `EntryDeadline`을 각 queue/HTTP/parser/append/commit까지 전달하고 남은 예산을 다시 늘리지 않는다. provider 완료 후 필수 검증·durable append·Main 소비에 필요한 시간은 하위 측정으로 산출한다. 로컬 처리 예약시간을 도입할 때는 기존 timeout과 원 예산 중 작은 값만 사용하며, 임의의 “잔여 3초 미만이면 무조건 미호출” gate를 만들지 않는다.
- shared snapshot serialization/쓰기·관측 로그의 반복 비용도 같은 준비/loop 계측에서 확인한다. 직접 지연 기여가 입증된 복사·직렬화만 기존 writer 안에서 줄이고 required raw/0B/0D·완료봉 증거와 원 cadence를 삭제하지 않는다.

초기 **성능 목표**는 `native-ready→claim p95 ≤250ms`, `signal→machine capture p95 ≤1초`, `coordinator ready→Main guard 처리 시작 p95 ≤100ms / p99 ≤250ms`다. provider 대기시간과 실제 시스템 부하를 포함한 자연 분포로 검증한다. 목표 미달은 병목 분석 대상이며 새 매매 차단 임계값이 아니다. 기계 캡처 단축분을 실제 provider/최종 검증 여유로 전달했는지도 동일 attempt에서 확인한다.

## 6. R0/R2 — PASS terminal과 outbox의 정확한 연결

현재 [operating outbox](../../src/engine/scalping/reversal_operating_outbox.py)는 `reserved → transmission_uncertain → response_received → intent_assigned → submission_reconciliation → reconciled`다. 이 상태를 기계적으로 성공으로 전진시키거나, 소비 거절을 재요청 가능한 `reserved`로 되감지 않는다.

Main 소비 결과는 기존 outbox의 opportunity/response에 결속한 **별도 단조 증가 처리 영수증**으로 기록한다. PB3의 기존 pipeline/lifecycle writer를 사용하며 새 병렬 원장·전송 상태 owner를 만들지 않는다. schema version·response hash·attempt/trace/claim·원 deadline·Main take/guard 시각·guard 코드·원인 증거·intent ID 또는 intent 미생성 사유를 갖는다. 원 신원은 꺼낸 immutable 결과가 소유하며 현재 stock의 새 claim/최근 기계 필드를 원 판정에 덧붙이지 않는다. 현재 guard의 입력은 별도 참조다. 아직 없는 ID는 null과 이유를 남긴다. outbox 원 전송/응답 이력은 보존한다. 실제 intent가 생겼을 때만 기존 `intent_assigned`와 broker journal에 연결한다.

| 실제 결과 | 남길 처리 상태 | 의미 |
|---|---|---|
| 유효 PASS·Main guard 통과 | `accepted_to_entry_path` + 후속 intent 또는 명시적 downstream guard 결과 | Main 소비 성공; 실제 제출 성공은 별도 |
| 원 deadline 경과 | `rejected` + 원 native/result deadline 근거 | 기존 응답 보존, 주문·provider 재호출 없음 |
| path/generation/state/route/source 변경 | `rejected` + 기존 guard reason | 기존 안전 검사가 작동한 결과 |
| worker 실패·orphan·overflow·종료 drain | `terminal_nonexecution` + 실제 사유 | 조용한 소실 방지; 성공으로 간주하지 않음 |
| 응답/결과 처리 중·Main 차례 대기·경계 이후 완료 | `pending` + as-of/inflight/deferred 이유 | 최종 거절/소비로 서둘러 집계하지 않음; source 재시도 상태가 아님 |
| 과거 연결 증거 결손 | `unobservable` + 탐색한 bounded 증거 범위 | 원인이 unknown인 상태. 현재 시각·상태로 과거 terminal을 만들어 채우지 않음 |

processing receipt의 기록 실패를 기록 성공으로 표시하지 않는다. 다만 이 진단 append 실패 자체를 새 매매 veto나 이미 수행한 실행을 되돌리는 조건으로 만들지 않는다. 원 request/생산 PID/전이 종류의 결정적 event ID와 기존 `structured_append_succeeded`·raw/companion/summary 결과를 연결한다. 진단 행은 재관측/재기록할 수 있지만 이를 이유로 Main 수량 계산·intent·broker 실행을 다시 수행하지 않는다. 기존 필수 source/outbox 저장 실패의 의미는 유지한다. 상충하는 최종 전이를 마지막 시각으로 덮지 않고 `unobservable` 원천 결손으로 격리한다.

재기동 뒤 원 응답/intent/custody를 대사하는 복구와 거래 재실행을 구분한다. 진단 누락을 메우기 위해 메모리 claim이나 이전 PID의 monotonic 예산을 복원하지 않는다. 원 epoch/현재 guard와 기존 실행 journal을 확인하고 만료·불확실 시도는 재주문하지 않는다. crash-before/after take, 응답 저장 후 처리 전, intent 저장 후 진단 receipt 전을 테스트한다. 이 절의 모든 진단 연결은 기존 원장에 남은 사실만 사용한다.

분모는 고유 실제 PASS attempt다. 중복 trace를 제외하고 `Main accepted + final rejected + pending + unobservable = observed PASS`가 되게 한다. 표의 `terminal_nonexecution`은 원인별 terminal이며 이 보존식에서는 final rejected로 집계한다. `accepted`의 후단은 `intent 생성 / 명시적 후단 거절 / 아직 미확정`으로 따로 분해한다. 관측 종료 직전 응답과 전송 불확실 시도를 잃지 않는다. PASS 100% 주문화를 수용 조건으로 삼지 않는다.

PB3와 같은 진단 계약은 `metric_role=source_quality_gate`, `decision_authority=report_only`, `window_policy=current_pid_exact_attempt_with_carry_in_out`, `sample_floor=none`, `primary_decision_metric=pass_to_main_disposition_coverage`, `source_quality_gate=exact_identity_and_clock`, `forbidden_uses=policy_or_order_authority,economic_success_inference`다. 기존 stage allowlist·lineage projector·요약·submission bottleneck monitor까지 함께 검증한다. 만료/native 종료를 API 결손으로 잘못 알리지 않고 기존 알림의 의미 기반 중복 제거를 유지한다. writer가 전체 WS/AI 본문을 다시 덧붙이지 않도록 실제 기록 크기도 확인한다.

## 7. R3 — 최초 응답 원장 전체 읽기 제거

[ai_decision_trace.py](../../src/engine/scalping/ai_decision_trace.py)의 `_load_seen`, `prepare_ai_request_capture`, `record_ai_decision_trace`를 실제 호출 경로와 함께 수정한다. 기존 [증분 원장 계획](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md)과 저장 책임을 맞추되 완료한 장후 공통 원장 이관을 재개하거나 live outbox를 offline queue와 합치지 않는다.

1. request/payload/prompt뿐 아니라 response trace·outcome ID도 기동/일자 준비 단계에서 검증한다. 준비되지 않은 대형 파일을 첫 응답 `_WRITE_LOCK` 안에서 전체 decode하는 fallback을 제거한다. 기존 준비 cache를 먼저 확장하고, 재기동/동시 writer의 bounded 증분 처리를 위해 추가 영속 index가 필요한 경우에만 기존 소유 위치에 재구축 가능한 key/offset index 한 개/일자를 둔다. 본문·응답·후행 라벨은 복제하지 않는다.
2. index는 검증 가능한 파생 자료다. journal identity·마지막 완결 행 checkpoint·prefix 근거·해석 version·ID namespace를 보존하고 신규 suffix만 읽는다. 현 `_load_seen`의 오류 시 부분 set 반환을 완성 index로 게시하지 않는다. 읽기 오류/잘못된 완결 행/잘린 마지막 행과 확인된 valid-empty를 구분한다. 같은 크기의 파일 교체와 concurrent append도 검증한다. writer의 기존 파일 generation lock 경계에서 dedup check와 append의 경쟁을 닫고 원 행 append 후에만 index를 전진시킨다. trace 성공/outcome 실패는 각기 보존한다. index만 먼저 갱신하고 실제 append가 없는 상태를 완료로 인정하지 않는다.
3. 최초 전체 구축·손상 재구축은 기존 background 준비 owner에서 한 번 처리한다. scan 중 `_WRITE_LOCK`을 장시간 독점하지 않고 검증된 snapshot을 chunk로 준비한 뒤 writer 경계에서 마지막 증분과 generation을 대조해 게시한다. holding/exit·callback이 준비 완료를 기다리지 않게 한다. 현재 신호 경로에서는 bounded 증분 또는 명시적 준비 결손을 기록한다. 필수 append를 생략하거나 응답 저장 전에 Main을 실행시키는 비동기화는 하지 않는다. 기존 저장 오류의 처리 의미를 보존하고 새 전역 entry 차단기를 만들지 않는다. 준비 실패가 조용한 장시간 대기나 매 신호 전체 scan으로 이어지지 않게 한다. 활성 request 날짜는 pin하고 만료 일자의 index 메모리는 회수한다.
4. `response_validate`를 JSON/schema/native 검증·dedup lookup/init·lock wait·durable append/fsync·반환으로 나눈다. 첫 사용 비용을 일반 p95에 섞지 않으며 초기 워밍업을 steady-state 개선율로 계산하지 않는다. 실제 warm 상태에서 첫 자연 응답에 남은 초기화도 별도 보고한다.

수용: 동일 ID 중복 append/재전송 0, 충돌 은폐 0, 원 본문/해시/trace-outcome 참조 보존, 정상 응답 경로에서 과거 전체 파일 scan 0. index 부재·손상·동시 writer·crash의 제한된 회귀를 포함한다. 새 Python 모듈이 필요하면 `src/engine/scalping/` 또는 공통 저장 역할의 기존 package를 선택하고 engine root에 추가하지 않는다.

## 8. R4 — 430봉 이력과 WS

[상세계획 H0~H5](main-430-bar-shared-history-and-incremental-refresh-implementation-plan-2026-10-08.md)를 따른다. 핵심은 다음과 같다.

1. 430 raw row·forming·실제 현재 세션 소비 수를 구분한다. MTF의 당일/세션 필터와 세션 VWAP/opening range를 조사해 필요 없는 과거 이력을 WS 준비 조건에서 분리한다.
2. 같은 REST `adjusted_1` 이력을 공유·복원하고 유효한 완료 cutoff 동안 재사용한다. 새 분·정정·결손 구간만 갱신한다. API가 작은 구간 조회를 지원한다고 가정하지 않고 continuation·실제 물리 횟수로 효과를 계산한다.
3. forming 봉과 실시간 quote/tape는 기존 freshness로 따로 확보한다. raw WS와 adjusted REST의 timestamp/OHLC/거래량/route 동등성 입증 후에만 현재 지원 `_AL` 구간을 전환한다.
4. PRE `_NX`는 현행 completed-bar selector의 WS 대상이 아니다. PRE는 REST 공유부터 적용하고, WS 지원 확대를 이 계획의 즉시 효과로 계산하지 않는다. 실제 필요 prefix만 합성하고 조용한 source gap·가짜 무체결·수신 시각 갱신을 금지한다.

데이터 재사용과 진행 중 요청의 우선순위/예산 공유는 별개다. source-only와 runtime-required의 허용된 호출 범위를 유지하고 준비된 데이터만 계약에 맞게 공유한다. 정상 이력 부족과 live source의 route/epoch/hash 오류를 구분하며, 후자는 REST로 숨기지 않는다. 평가 `as_of` 이후 받은 revision을 원 판정에 소급 소비하지 않는다. 상세계획 §3.1/§6.0의 전환 표를 공통 기준으로 사용한다.

R1의 계좌 2초 receipt는 분봉 완료 구간 재사용 규칙과 전혀 다른 원천이다. 동일한 “캐시 확대” 설정으로 함께 변경하지 않는다.

## 9. 공식 gate·검증·자연 수용

### 9.1 프로토콜과 회귀

Kiwoom 요청/parser/FID/continuation/인증/계좌·주문 call/recovery를 수정하기 전에 [공식 API reference gate](../kiwoom-api-data-contract.md)에 따라 최신 공식 저장소 SHA·조회 KST·관련 `kiwoom_docs` 경로와 SDK/core/realtime/Postman 대조 경로를 기록한다. R1 호출 예약 변화도 kt00011 소비 계약을 먼저 대조한다. 새 호출 한도나 suffix/단위 의미를 추정하지 않는다. 본 계획은 실제 API 호출 검증을 실행한 기록이 아니다.

| 영향 | 표적 검증 |
|---|---|
| R1 capacity | [cash capacity](../../src/tests/test_entry_cash_capacity_contract.py), [Main REST/WS](../../src/tests/test_main_rest_ws_latency.py), [source repair](../../src/tests/test_fixed_watch_submit_source_repair.py): fixed-watch/scanner 유효 수요 보존, probe 권한 격리, idle/invalid/expired no-read, observer cache miss와 detached worker의 원 예산, exact-price/account/deposit/custody 변경, mandatory sizing 보존 |
| R2 async/Main | [coordinator](../../src/tests/test_scanner_async_eval.py), [actual bridge](../../src/tests/test_scanner_async_entry_bridge.py), [fixed watch](../../src/tests/test_main_fixed_watch.py): 진짜 outer caller→handler→기존 후속 경로→intent stub, source early return·최종 stale 거절·lost wakeup·expiry·동시 결과·후속 claim 보호·orphan·eviction·종료 drain |
| PASS/outbox | [registered operating policy](../../src/tests/test_reversal_operating_policy.py)와 native outbox/journal 영향 테스트: take/receipt/intent 전후 crash, 중복 callback·다중 정책·late 응답·재기동·후단 거절 |
| R3 trace | [trace](../../src/tests/test_ai_decision_trace.py): 큰 fixture의 최초/증분 read bytes·lookup, 오류 시 부분 index 게시 금지, valid-empty/partial tail 구분, 다중 writer의 dedup+append 경합·회전·손상·동일 ID 충돌, trace 성공/outcome 실패, 기존 보호 경로의 lock 지연 |
| R4 source | 430봉 상세계획 §6의 영향 MTF/entry/완료봉/공식 계약 회귀 |

추가로 실제 PASS 네 건의 **보존된** 원 timing을 bounded fixture로 재현한다. 원본이 모자란 경계는 합성 테스트임을 표시하고 과거 미제출 원인을 입증했다고 주장하지 않는다. 4.26/4.86초에 준비된 결과, 5초 이후 응답, fresh quote 소실, native path 변경, pending order 발생, 지연된 durable append를 각기 검증한다. 실제 broker/provider 호출 없이 의도 생성 stub과 guard reason을 확인한다.

capacity 예산은 `prefetch 성공→가격 변경→observer cache miss`, `pending 소비 전 만료`, `admission 후 전송 직전 만료`, `HTTP 응답 후 만료`, epoch 전진/역행을 fake clock/transport로 재현한다. `kt00011 source_only`의 미전송/늦은 수신과 필수 sizing/exit의 기존 timeout을 동시에 확인한다. 새 HTTP를 보낼 권한은 원 수요에서 나오며 물리 전송을 이미 시작한 뒤 만료된 응답을 미전송으로 세지 않는다. terminal writer 실패 시험에서는 진단 gap만 생기고 이미 처리한 주문 의도를 다시 실행하지 않아야 한다.

리뷰→수정→재리뷰→표적 pytest/compile·`git diff --check` 후 통합 caller 경로를 다시 검증한다. caller가 바뀌지 않은 helper 테스트만으로 완료하지 않는다. 시험 중 새 주문·연구 provider 호출·광범위 장후 재생성은 하지 않는다.

### 9.2 자연 수용과 종료 조건

성능은 각 release/PID 안에서 같은 정의의 워밍업 제외 창을 차분 집계하고, 전후 release/PID를 명시하여 동종 세션·수요별로 비교한다. 코드 변경 전후에 같은 PID가 필요하다는 뜻이 아니다. cold start/최초 사용은 별도 표로 남긴다. 4개 PASS처럼 작은 표본은 개별값·N·as-of를 제시하며 p99로 안정성을 과장하지 않는다. 전체 stage 분모와 완료된 stage만의 지연 분포를 나누어 timeout·만료·queue 대기를 빠른 표본에서 탈락시키지 않는다. REST logical/admission/physical page·retry·response/timeout/inflight, WS 수신/queue/lock·writer loss, signal age·stage별 지연을 분리한다. 수요가 다른 정규장과 AFTER의 수를 단순 개선율로 비교하지 않는다.

완료 기준은 다음 다섯 가지다.

1. 전송 시작 시 유효 수요가 없는 capacity prefetch는 0이고, 실제 진입에 필요한 exact 계좌 증거와 기존 필수 read는 정상이다. 유효 수요로 전송된 뒤 취소/만료된 시도는 별도 계수로 보존한다.
2. 기존 guard가 모두 유효한 기계 ENTER·보조 PASS fixture는 원 5초 내 Main entry 경로와 intent까지 도달한다. 자연 PASS는 동일 attempt의 accepted/rejected/pending/unobservable로 전수 연결되며 미확정과 아직 없는 표본을 구분한다.
3. 원 신호 deadline·freshness·policy/native generation·custody가 바뀐 결과는 정확히 거절되고 중복 provider 요청/의도/주문은 0이다.
4. 같은 입력의 특징/기계 결과를 유지하면서 준비·처리 시간과 수요당 분봉 전송이 감소한다. 새 결손/필수 계좌 대기/holding·exit 지연이 개선 효과를 상쇄하는지 함께 검증한다.
5. selected release·실제 PID 소비·policy/source 버전·장중 handoff·필요한 다음 기동 준비를 각각 확인한다. 자연 PASS가 없으면 코드/배포는 완료할 수 있어도 자연 연결은 미관측으로 유지한다.

기존 주문 경로의 정당한 자금·수량·가격·시장 guard로 미제출된 건은 추가 기계 결함 여부를 분리한다. 실제 제출/체결·비용 후 수익을 위 source/latency 개선의 자동 결과로 선언하지 않는다.

## 10. 인계·복구·계획 리뷰 결과

구현 시작 시 다른 세션 dirty 작업·현재 선택 release/PID·policy/overlay·pending/uncertain outbox를 고정한다. R0/R1/R2a를 우선 통합하고 source/runtime 영향을 받는 code pin과 compact reader만 검증한다. 완료된 기계·보조 연구를 반복하거나 신규 정책 gate를 추가하지 않는다.

복구 시 pending/응답/intent custody와 terminal receipt는 보존한다. 신규 완료봉 view의 정상 미지원/이력 부족은 430봉 상세계획 §6.0의 허용된 bounded REST로 복귀할 수 있으나, live identity/무결성 실패를 REST로 우회하지 않는다. rollback 후보는 Main-only와 현재 custody/응답 형식을 읽는 호환 경로를 검증하고, 되돌리는 코드 범위와 무신호 예약 재발 방지를 명시한다. 퇴역 runtime을 복원하거나 provider 불확실 예약을 지우거나 만료 PASS를 재주문하지 않는다. 장후 작업이 실행 중이면 해당 producer의 실행 source/release를 교체하거나 같은 작업을 중복 실행하지 않고 기존 owner의 다음 인계 경계를 사용한다.

현재 체크리스트에는 위 B1/B5/RESTWS 작업을 수행하는 OPEN owner가 이미 하나 있다. **이번 계획 문서 추가로 봉인된 체크리스트 바이트·AUTO 블록은 수정하지 않는다.** 상세 계획은 이 기존 owner의 B0~B7 문서에서 연결한다. 실제 후속 실행의 일정/Acceptance 인계가 필요해 체크리스트를 바꿀 때는 최종 바이트에 대한 기존 strict/장중 handoff·필요한 PREOPEN을 같은 owner에서 검증한다. 과거 PASS를 새 세대에 전용하지 않는다.

계획 리뷰에서 기존 completion-event의 존재, source gate 이전 결과 소비, 만료 generation의 terminal 손실, capacity 예약 caller의 원 deadline 부재, response/outcome dedup과 request prewarm의 차이, live outbox 단조 상태와 별도 소비 영수증, 430 요청과 실제 세션 소비의 차이를 반영했다. 함께 추가된 PB 계획과의 deferred/최종 거절·기존 writer/monitor 계약도 통합했다. 남은 원천 의미·자연 표본 부족은 각각 R4 조사와 R5 자연 관측 항목이며 완료로 가장하지 않는다.

### 10.1 후속 계획 재리뷰와 수정 사항

| 발견한 설계 결손 | 보완 위치·반례 |
|---|---|
| native claim만 허용하면 일반 scanner 준비가 탈락할 수 있음 | §4.1~4.3의 수요 종류별 identity. native 없는 유효 scanner와 무권한 probe를 분리 |
| observer의 추가 `kt00011`에는 원 budget이 전달되지 않고 공통 budget은 `ka`만 적용 | §4.3의 호출별 표와 source-only 명시 budget. 전송 전/후 만료·필수 sizing/exit 불변 시험 |
| deferred가 새 quote 대기/재시도로 해석될 여지 | §5.2에서 Main 순서 대기만 허용. 기존 quote/cooldown/source 거절은 최종 상태로 유지 |
| take 이후 후속 claim 삭제·재dispatch·후속 처리 누락 위험 | 원 request/key/token과 기존 async/inline 합류 경로를 고정. 새 분석/intent 중복 시험 |
| 진단 저장 실패가 주문 재실행·새 veto로 이어질 여지 | §6의 실행/관측 분리, 결정적 event ID, 상충 terminal 격리. 재기동은 사실 대사이며 과거 거래 재생이 아님 |
| trace 부분 읽기·다중 writer·배경 초기화 lock 비용의 명세 부족 | §7의 완결 offset·valid-empty·generation 게시·dedup+append·날짜별 메모리 회수 |
| 430봉의 class 간 inflight 공유·future revision·무결성 오류 fallback 위험 | 상세계획 §3.1/§4/§6.0: 데이터/전송 key 분리, as-of pin, 오류별 복귀 표 |
| 전후 같은 PID 요구·작은 N의 분위수 과장 가능성 | §9.2에서 PID별 차분 후 동종 수요 비교, N/미완료/first-use 분리 |

이번 재리뷰는 구현 순서와 검사 위치를 구체화한 문서 수정이다. 새 source/window 계약의 실제 코드 통과나 자연 PASS 소비 완료를 대신하지 않는다.

초안과 이번 재리뷰의 문서 검증 결과: 통합·430봉 상세·B0~B7 문서의 로컬 링크 84개 결손 0, print-only parser 22항목·현재 Main owner 1개, 공백/`git diff --check` 통과. 체크리스트 SHA는 관측 당시 봉인과 같은 `4aee28ee1c0fa26d34d8f7f7ecac25432e6680ab226ec805c59b635bb11b48ed`다. 이번 재리뷰에서는 통합 계획과 430봉 상세계획만 수정하고 다른 세션의 §15와 기존 dirty 변경을 보존했다. 문서만 변경했으므로 코드 pytest/compile·broker/provider 호출·배포/재기동·장후 재생성·외부 sync는 실행하지 않았다. 위 테스트와 성능 목표의 실제 통과는 후속 구현의 완료 조건이다.

## 11. 통합 구현·리뷰 결과

R1은 무신호/미지원 경로의 선행 계좌 예약을 제거하고 실제 평가 context와 최초 deadline에 kt00011 source-only 준비를 묶었다. R2는 완료 결과/비상시감시 신호를 Main에 전달하며 R3의 중복 인덱스는 기존 준비 worker에서 최대 4MiB씩 생성한다. R4는 완료봉 공유·revision pin·필요 이력 descriptor로 연결했다. R5 코드 회귀는 완료했으며 실제 배포/PID/장중 성능 검증은 보류한다.

검증 수치·수정한 반례·공식 API SHA·배포 보류 경계는 [통합 실행 리뷰](../audits/main-pass-residual-history-nonfixed-implementation-review-2026-10-08.md)에 한 번 기록한다. 실행 owner는 기존 `DirectFamilySourceRepairMainMechanisticEntry`를 유지하며 이번 작업은 checklist 봉인/현행 정책을 재발행하지 않는다.

### 11.1 10/10 배포 상태 대조와 잔여 결함 계획

위 배포 보류는 10/8 구현 당시 기록이며 이후 [10/9 통합 배포](../audits/main-integrated-uncommitted-deployment-review-2026-10-09.md)가 완료됐다. 현재 선택된 `main-holding-profit-exit-20261009-v4`와 작업본의 관련 6개 source가 일치한다. 다만 Main의 새 코드 소비는 `actual_pid_consumed=false`로 다음 예약기동 대기이므로 R5의 자연 PASS·장중 성능 검증까지 완료한 것은 아니다.

R2/R3/R5의 후속 범위는 [10/10 재점검·보완계획 S1~S4](main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md)에 연결한다. 결과 인수 이후 예외·직접 미제출 이유·판정 신원 충돌·동기 기록 지연과 원장 준비의 큰 행 경계를 점검했으며, 우선 정상 PASS 한 건을 실제 기존 제출 함수까지 연결하는 격리 검증을 보강한다. 기존 관련 회귀 164건의 성공만으로 이 후단 검증을 대체하지 않는다. 이번 변경은 계획이며 새 코드 수리·정책 적용·배포·재기동을 수행하지 않았다. 10/10 checklist 부재와 봉인된 10/12 입력 보존은 후속 계획 §1의 인계 조건을 따른다.

후속 계획 리뷰에서 정상 경로 검증의 끝을 고수준 제출 함수 호출에서 함수 내부 guard·intent를 거친 주문 adapter까지 확장했다. 기존 bool 반환과 호출 후 uncertain 상태, 공용 관측 executor의 backlog·종료·저장 성공 계약, 큰 원장 행의 읽기/검증 offset 분리를 함께 보완한다. 이는 계획의 구체화이며 164건의 과거 통과나 현재 배포를 새 검증의 완료로 전용하지 않는다.
