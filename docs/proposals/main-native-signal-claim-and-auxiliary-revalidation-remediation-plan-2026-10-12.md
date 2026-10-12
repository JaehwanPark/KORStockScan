# Main native 신호 claim·보조판정 재검증 보완계획 — 2026-10-12

상태: **계획 리뷰·보완, S0/S1/N0/N1/S3 및 S2 계측·S4 source-only reader 구현과 코드리뷰 완료.** 검증은 통합 1,207건과 추가 동시성 1건이 통과했다. 선행 구현 뒤 사용자 배포·재기동 승인에 따라 16:46 통합 릴리스 `native-readiness-20261012-v1`/PID `1171338`로 적용했다. 최초 eligible 알림은 기존 Main completion Event에 연결했으며, 정책/프롬프트·원 5초는 유지한다. 추가 batch/동기 작업 최적화는 실제 병목 증거를 따른다. [통합 배포 리뷰](../audits/main-native-readiness-deployment-review-2026-10-12.md). [구현 리뷰](../audits/main-native-signal-claim-implementation-review-2026-10-12.md)에 변경·검증·남은 자연 관측을 구분했다.

## 1. 계획 수립 당시 조사 기준과 실행

- 조사 사례는 `deployment-detector-20261012-v1` / commit `e13ffcfb49fe8c1b9f003b77c85b31b771ee3b5c` / PID `981118`, start ticks `3253591`의 14:33 기동 이후 결과다. [14:51 점검](../../data/report/auxiliary_compact_adoption/2026-10-12/pid-981118-auxiliary-operating-status.json)에 자연 AI·종료 증빙을 보존했다.
- 조사 중 별도 배포로 최신 릴리스가 `auxiliary-consumption-attestation-20261012-v1` / commit `800c1d091f149809ddd6e6da2a7bf6da0f651848` / PID `1020707`, start ticks `3378564`로 바뀌었다. 14:58 대조에서 현재 보조정책 소비와 bootstrap PASS를 확인했다. PID `981118`의 34건을 새 PID의 실적으로 합산하지 않는다.
- 기계 bundle은 `f7c1454a71b284a25c40a157ea4f42f390ecc5c21f362d76f497c49bf41ec2b1`이다. 이번에 조사한 실행·관측 source 6개는 최신 릴리스와 작업본의 바이트가 일치했다. 별도 세션의 배포/기동 증빙 작업을 수정하거나 구현 완료로 대체하지 않는다.
- [후속 점검 근거](../../data/report/auxiliary_compact_adoption/2026-10-12/signal-claim-auxiliary-followup-plan-evidence.json)에 현재 PID/릴리스, 파일 해시, 사례 시계와 권한 범위를 보존했다. 대형 원장은 최대 16MiB suffix, 사례 종료는 기존 37,995바이트 분 단위 execution partition으로 조회했다.

위 PID·릴리스는 계획 수립 당시의 증빙이다. 후속 구현은 작업본에서 수행했으며, 봇 기동·재기동, 정책/프롬프트 발행, Provider/broker 호출, cron 변경, 운영 장후 producer 실행 또는 대형 원장 재생성은 수행하지 않았다.

## 2. 확정 사실과 아직 확정할 수 없는 부분

### 2.1 미claim 신호

PID `981118`의 14:51 native selected 집계는 34건 = claimed 4건 + `expired_before_claim` 30건이다. 이것은 수신 과정에서 관측한 selected backend/가격대/세대의 신호 분모이며 전체 시장 기회·승리 기회 분모가 아니다.

`runtime_performance.snapshot`는 미claim 행에 대해 `현재 시각 >= 원 신호 시각 + 5초`만으로 `expired_before_claim`을 증가시킨다. 원 반전이 그 전에 무효화됐는지, Main이 유효 구간에 방문했는지, 이미 다른 분기가 사용됐는지, exact source/guard가 막았는지를 저장하지 않는다. 따라서 **30건이 모두 전달 지연 때문에 놓친 유효 진입이라는 해석은 성립하지 않는다.** 과거 30건은 원 근거를 보존하고 세부 원인을 복원할 수 없으면 `historical_unresolved`로 남긴다.

### 2.2 claim 4건의 정확한 종료

아래 네 건은 모두 주성 `036930_AL / SOR / REGULAR`이며 같은 PID의 원 claim·attempt/trace와 [분 단위 종료 원장](../../data/threshold_cycle/date=2026-10-12/family=entry_mechanical_momentum/part-execution-202610121438.jsonl)을 연결했다.

| evaluation attempt | AI 단계 | Main 종료 | 해석 |
| --- | --- | --- | --- |
| `aims-9695ea7e635b1469a30b` | 실제 OpenAI `gpt-5.4-nano` 호출, PASS, 계약/파싱/의미 검증 통과 | `reversal_signal_path_changed` reject | PASS 이후 원 native 반전이 유효하지 않음. 세부 predicate는 현재 종료 증빙에 없음 |
| `aims-df10ce27c226e8de47c0` | 미호출, 기계 입력 계약 거절 | 같은 native reject | AI veto/transport timeout으로 집계하지 않음 |
| `aims-3b636444741b146dbd02` | 미호출, `not_evaluated_source` | 같은 native reject | AI veto/transport timeout으로 집계하지 않음 |
| `aims-a5b52eb286163533d7f0` | 미호출, 필수 feature 부족으로 RECHECK/WAIT | `commit_allowed` 뒤 `first_ai_wait` | 현재가/tape stale와 provider trade late. Main commit metric 1건의 실제 소유자 |

주문 physical API 시작은 0건이다. 이 사례의 PASS를 Main 소비 성공으로 해석하거나 위 네 건을 주문 실패 네 건으로 세지 않는다. PASS 이후 거부가 적절한 손실 회피였는지, 수익 기회를 잃은 과차단이었는지는 아직 후행 승패로 확인하지 못했다.

### 2.3 PASS 사례의 시계

| 경계 | KST | 원 신호 이후 |
| --- | --- | --- |
| 원 신호 | 14:38:05.576313 | 0초 |
| AI 판정 trace 함수 진입 시각 | 14:38:09.625890 | 약 4.050초 |
| worker 완료 | 14:38:10.134875 | 약 4.559초 |
| Main 재검증 | 14:38:10.223720 | 약 4.647초 |
| 원 5초 기한 | 14:38:10.576313 | 5초 |

Main 재검증 시 원 예산은 **약 0.353초 남아 있었다.** 실제 거부는 5초 만료가 아니다. AI trace 시각부터 worker 완료까지 약 0.509초, worker 완료부터 Main 재검증까지 약 0.089초였다. 이번 한 사례에서는 Main의 완료 결과 수거만을 최우선 지연 원인으로 특정할 수 없다.

coordinator의 preparation wait 0.020초, preparation service 0.809초, AI dispatch wait 0.023초, AI client elapsed 3.607초가 기록돼 있다. 실제 HTTP Provider 구간은 trace에서 1.427초다. 두 elapsed의 약 2.180초 차이는 경계/중첩을 검증하기 전에는 미분해 구간이며, 특정 함수의 확정 비용이나 제거 가능한 지연으로 사용하지 않는다.

PID `981118`의 14:53 성능 영수증은 warm loop 751회, p95 약 1.967초, p99 약 3.015초, 최대 13.615초, 5초 초과 3회다. 기존 앞선 감시의 5초 초과 0건은 이후 실적에 그대로 적용할 수 없다. 긴 loop와 특정 신호의 미claim을 직접 연결하는 원인 영수증이 필요하다.

### 2.4 관측 저장과 후행 결과

- 14:53의 bounded observation queue는 completed 46 = append-confirmed 19 + 완료됐으나 append 영수증 없는 27이었다. unavailable/failed는 0이다. 구현은 callback 반환값이 성공 append를 명시하지 않아도 후자에 포함한다. 27건 전체를 데이터 유실이나 저장 성공으로 단정할 수 없다. producer/category별 실제 writer와 reader의 소비 계약을 대조해야 한다.
- PASS의 기존 `ai_decision_outcomes` 행은 조회 시 `pending`, matured horizon은 비어 있었다. 기준가는 `current_price=253000`이고 adverse price가 없다. 이 원장은 다른 feature/friction 진단 정보를 포함하므로 **그대로 연구 목표의 binary 승패 라벨로 사용하지 않는다.** target은 원 native 진입 호가와 별도로 결속해 확인한다.
- 이번 raw SOR 원장은 약 472MB의 진행 중 파일이다. 이를 전체 스캔하지 않았다. 14:38부터 30분 종료인 15:08:05.576까지의 완전 경로·soft-stop-first·비용 결속이 확인되기 전에는 승리/실패를 확정하지 않는다.

### 2.5 비상시감시의 기계 평가 이전 고갈

[별도 후속 점검](../audits/main-machine-signal-lifetime-and-nonfixed-readiness-review-2026-10-12.md)의 [동일 PID census 요약](../../tmp/main-machine-followup-review-20261012-pid981118/nonfixed-probe-census.json)을 읽고 관련 queue/scanner/probe 코드와 대조했다. 원 대형 파일의 64MiB 구간을 이번 계획 작업에서 재스캔하지 않았다. 이 evidence는 14:33:30~14:52:48 / PID `981118`의 lease 분모이며 위 fixed-watch 신호 34개와 합산하지 않는다.

- 고유 예약 126 = 종료 121 + as-of 진행 5다. 종료는 기동 의존성 미준비 5, 정확 route snapshot 없음 21, 0B 미수신 22, 0B age 초과 19, 준비 경계 0B age 초과 4, residence 종료 50이다.
- residence 종료 50 중 native active branch가 전부 FALSE인 40은 정상 패턴 부재로 검증됐다. UNKNOWN이 있는 10은 window/feature 부족이며 정상 BLOCK으로 바꾸지 않는다.
- scanner의 `consumer_ready`는 EventBus subscriber 존재만 확인하고, 실제 probe는 WS_MANAGER·AI_ENGINE·token을 추가로 요구한다. 5건의 `runtime_dependency_missing`을 구분할 readiness 증빙이 부족하다.
- UNKNOWN 10 중 9는 60초 feature와 known FALSE→TRUE·1초 hold가 필요한 branch다. 연속 관측은 18.56~58.64초였다. queue는 전체 5개 슬롯 중 긴 슬롯을 최대 2개·150초, 나머지를 60초로 예약 시점부터 배정한다. 첫 체결 지연과 segment reset을 뺀 실제 유효 이력이 더 짧아진다.
- 기계 completed ENTER/RECHECK/BLOCK과 보조 호출이 없는 구간이다. 정상 패턴 부재, 준비 부족, source quiet/지연을 각각 분리한다. 0D 수신만으로 0B 체결 원천이 정상이라고 보거나 위 66 source 종료를 API 실패로 단정하지 않는다.

## 3. 목표·우선순위·실행 순서

| 순서 | 우선순위 | 보완 | 직접 owner | 닫는 조건 |
| --- | --- | --- | --- | --- |
| S0 | P0 | 미claim 모집단과 수명 종료 분류 | `runtime_performance` + native 관측 adapter | 동일 신호의 생성·유효성 변화·Main 방문·claim/비실행 terminal 보존식 |
| S1 | P0 | PASS 이후 재검증 상세 증빙 | `sniper_state_handlers` + `reversal_source_diagnostics` | 같은 attempt/trace에 실패 predicate·원 clock/quote·terminal 연결 |
| N0 | P0 | 비상시 요청의 실제 의존성 readiness | scanner dispatch + 기존 probe consumer | subscriber·WS·AI·인증 준비 전 미실행 예약 소모와 불명 사유 제거 |
| S2 | P1 | 유효 신호의 평가 도달 및 로컬 처리 지연 | Main scheduler + 기존 async/AI caller | 확인된 blocker만 수리, 정책/guard parity 및 전체 loop 회귀 없음 |
| S3 | P1 | 관측 callback→writer→reader 저장 계약 | `BoundedObservationQueue`와 실제 callback owner | 필수 append·정상 skip·실패·미확인의 분리와 직접 consumer 확인 |
| S4 | P1 | 동일 기회 후행 binary 승패·과차단 평가 | 기존 Main shared ledger/postclose owner | native 진입 호가·cost/target/stop/30분 결속, 결손/미성숙 별도 집계 |
| N1 | P1 | 비상시 feature readiness와 residence 배정 | 기존 discovery queue + native 관측 adapter | 기존 5슬롯·150초 긴 슬롯 최대 2개 안에서 판단 불가능한 배정 분리 |

S0·S1·N0를 먼저 구현·검증한다. S2의 scheduler 변경은 S0에서 실제 eligible 시간과 방문 지연이 확인된 구간에 적용한다. N1은 source/feature 계약이 확인된 branch의 기존 슬롯 배정부터 보완한다. S3는 S0·S1 저장 검증에 필수인 callback부터 점검한다. S4는 확보된 기존 원천만으로 연구하며 Provider 호출은 하지 않는다. 프롬프트/신호 수명 변경이 필요하면 S4 결과를 근거로 별도 정책 연구를 구성한다.

## 4. S0 — 미claim 분류 보완

구현 리뷰 보완: 기존 age-only `expired_before_claim`은 호환용 참고 수치로만 남기고 `age_only_not_delivery_failure`를 명시한다. 새 lifecycle 모집단은 별도 버전·정확 identity·배타적 상태로 집계한다. ingress와 Main 방문은 별도 관측이며, ingress 없는 구간을 연속 유효로 추정하지 않는다. 기한 경계까지 유효함을 입증할 원천이 부족하면 `unobservable`이다. 신호가 ready에서 사라졌다는 사실만으로 replacement를 확정하지 않는다.

1. key는 `source_date/PID/start_ticks/bundle/family/scope_execution_hash/symbol/item/route/session/native_epoch/signal_id/branch`다. 서로 다른 가격대·backend·generation·PID·route를 병합하지 않는다. 같은 canonical opportunity에 여러 패턴이 맞으면 opportunity 수는 한 번, branch membership은 별도로 보존한다.
2. raw ready membership과 native selector가 지금 실제로 claim할 수 있는 상태를 분리한다. FIRST 필터, claimed 상태, 선택 branch/가격대, 원 5초 기한과 quote/source/native epoch 조건을 native owner와 일치시킨다. 기존 `observe_snapshot`의 읽기 전용 계약을 재사용하되, 관측 과정에서 claim·ack·FSM을 소비하거나 provider를 호출하지 않는다.
3. `first_native_seen`, `first_eligible_seen`, `last_eligible_seen`, `first_ineligible_seen`, `main_first_visit`, `claim_attempt`, `claimed`, `original_deadline`를 wall/monotonic 경계와 함께 기록한다. tick 사이의 정확한 변화 시각이 없으면 마지막 valid~첫 invalid의 구간으로 남기고 임의의 순간을 합성하지 않는다.
4. 서로 배타적인 주 종료 상태는 `claimed`, `invalidated_before_claim`, `replaced_before_claim`, `observed_valid_until_deadline_unclaimed`, `source_or_guard_blocked_before_claim`, `not_yet_due`, `unobservable`로 정의한다. 추가 원인은 field로 보존하고 같은 신호를 여러 주 종료 분모에 중복 추가하지 않는다.
5. `observed_valid_until_deadline_unclaimed`은 기한까지 유효성·관측 연속성 및 Main 방문 원천이 확인된 경우에만 사용한다. 단순 age 증가, tick 정적 상태 또는 최근 시세 미수신으로 이 상태를 만들지 않는다. 설명할 수 없는 과거 행은 `historical_unresolved`다.
6. eligible 시간이 있었는데 Main이 방문하지 않은 경우의 `main_visit_gap`과 방문했으나 source/guard가 막은 경우를 나눈다. native 신호 없음, 정상 반전 무효화, 실제 source gap, transport 지연 및 정책 미적용을 서로 대체하지 않는다.
7. 현재 크기 제한을 유지하는 scalar ring과 기존 performance/분 단위 execution projection을 사용한다. WS/native lock 안에서는 유한 scalar snapshot만 취하고 disk/hash/provider 작업을 하지 않는다. lock 순서는 native owner→기존 diagnostic owner로 고정하고 반대 방향 획득을 금지한다. ring eviction/재기동/날짜 변경/큐 거부는 `unobservable`로 대사한다.

회귀: 처음부터 eligible하지 않은 FIRST, 1초 내 저점 재시험, 복수 분기의 일부 생존, 기한까지 valid한 미방문, source stale, guard 차단, replaced 신호, 같은 ID의 다른 route/generation, 중복 관측, ring eviction, 날짜/PID 변경을 각각 구분한다. 관측 추가 전후 native machine/claim 결과는 동일해야 한다.

## 5. S1 — PASS 이후 거부 증빙 보완

`_resolve_scanner_async_entry_ai`는 `validate_claim_with_receipt`의 예외에서 오류 문자열만 유지한다. 이미 생성된 `exc.reversal_source_receipt`의 상세 실패 증빙을 compact projection으로 연결한다.

- 저장: stage=`commit_revalidation`, attempt/trace/request/native signal, PID/start/cwd, policy·scope·registration hash, 원 신호/판정/worker 완료/Main 검증 clock, 남은 예산, failed predicate, branch별 생존 여부, `current_turn_id`, `registered_signal_ready`, latest native sequence/price/원천 valid 상태.
- 원 claim 등록 증빙과 최신 상태 증빙은 별도 시점으로 보존한다. 현재 turn/ready 부재를 과거 claim 생성 당시의 결손으로 소급하지 않는다. generation 비교는 v6 envelope와 실제 selected scope hash를 각각 검증한다.
- full input/claim/raw response를 여러 원장에 복제하지 않는다. 기존 registration/capture를 해시·경로로 참조하고 작은 실패 capsule만 정확 분 단위 execution partition에 기록한다. 토큰·인증·계좌 비밀정보는 기존 sanitizer를 통과한다.
- 모든 claim은 accepted/rejected/deferred/unobservable의 명시적 terminal 또는 진행 상태를 갖는다. `worker_completed`, `accepted_to_entry_path`, 주문 intent, physical submit, fill은 각각 다른 증거다. 거부 뒤 cleanup/ack 실패나 큐 거부는 원거부를 덮지 않는다.
- `reversal_signal_path_changed`가 정상 저점 재시험인지, FIRST 교체인지, ready 제거인지, 최신 source invalid인지 확인한다. 복수 패턴에서 다른 유효 branch가 남는데 전부 거절되는 재현이 나오면 기존 native branch 계약 내의 구현 결함으로 별도 수리한다. 현 branch 정책을 넓히거나 만료 PASS를 재사용하지 않는다.

회귀: 시간 내 PASS의 정상 native 무효화, 정확 기한 만료, source/generation/route 불일치, 일부 branch 생존, 이미 취소/교체된 request, 동일 결과 재수거, 관측 실패·ack 예외·successor 존재를 검증한다. 거부 이유가 표시용 KRX/SOR 차이로 덮이지 않고, 유효 결과는 기존 Main 경로에 한 번만 전달돼야 한다.

## 6. S2 — 확인된 지연 구간만 보완

### 6.1 Main 방문·claim

상시감시를 scanner heavy 작업보다 앞에 배치하는 개선은 이미 배포됐다. 이를 반복 구현하지 않는다. S0의 exact 원천에서 긴 scanner/account/recovery 작업 또는 loop 대기가 유효 신호를 실제로 앞지르는지 확인한다.

입증되면 기존 scheduler/notify 경로에 유한 signal-ready 힌트와 기존 Main 방문을 결속한다. 동일 key는 coalesce하고, 힌트 자체는 claim/ENTER/PASS/주문 권한을 갖지 않는다. 주문·실보유·COMMIT/FAST_PRECHECK의 기존 우선순위와 manual veto를 유지한다. heavy 작업은 기존 작업 사이에서 cursor를 보존하고 양보하며, 진행 중 physical 요청을 취소하거나 quota/retry/concurrency를 높이지 않는다. 모든 기존 대상 수와 fairness를 보존한다.

마감이 지난 힌트는 원 기한 그대로 terminal 처리한다. 새 시각으로 다시 생성하거나 거래가 없는 구간에 fake tick/반전을 넣지 않는다. 전체 기간 `expired_before_claim`이 줄었다는 숫자만으로 성공을 주장하지 않는다. 실제로 유효했던 같은 신호의 first visit/claim 지연을 평가한다.

### 6.2 async·AI 로컬 처리

coordinator/AI caller/capture의 기존 계측에 비중첩 clock을 추가하여 준비 큐→source 준비→policy resolve/검증→input freeze→payload/schema→HTTP 시작/수신→validator→trace/캐시/후행 pending 기록→worker 완료→Main 재검증을 연결한다.

- 원 5초 deadline과 monotonic budget을 모든 구간이 공유한다. timeout/reserve 추정값을 새 hard 진입 조건으로 추가하지 않는다. 실제 남은 기한 밖 Provider 호출·원천/응답 소비는 계속 거절한다.
- 동일 입력의 중복 graph/copy/hash/schema 구성이나 필수 완료 후 비실행용 저장이 지연을 만든 것이 확인되면 해당 owner 안에서만 줄인다. cache key에는 policy/source/registry/schema/validator/route/generation을 결속하고 CAS·변경 감지·반환 envelope 소유권을 보존한다.
- order/action 증빙의 필수 append를 뒤로 미루거나 누락하지 않는다. 비필수 보조 저장만 기존 bounded 큐와 재시작 복구 계약이 확인된 경우에 옮긴다. 유효한 machine/AI 결과·수량·가격·guard의 바이트/의미 parity를 비교한다.
- benchmark는 같은 frozen 입력으로 baseline/candidate 교대 3회, wall/CPU/lock/copy bytes와 worker/Main/terminal 결과를 비교한다. 현재 자연 1건의 Provider 1.427초를 일반 p95로 삼거나 전체 절감량을 합성하지 않는다.

### 6.3 N0·N1 — 비상시 준비와 관측기간

구현 리뷰 보완: subscriber 등록은 준비 완료가 아니다. 소비자가 제공하는 읽기 전용 readiness callback이 없거나 실패하면 예약하지 않는다. 준비 조회는 EventBus lock 밖에서 실행하고, 실제 callback은 물리 작업 시작 전에 같은 준비 조건을 재확인한다. 인증 값은 존재 여부만 기록한다. 관측기간은 활성 branch 정의의 실제 필수 필터·hold에서 산출한다. 여러 독립 branch 중 짧은 기간에도 평가 가능한 branch가 있으면 짧은 슬롯을 사용할 수 있으나, 미완성 branch는 UNKNOWN으로 남긴다. 모든 branch가 60초를 초과해 필요하면 긴 슬롯을 기다린다. 120초 등 backward history와 최대 confirmation 대기시간은 서로 다른 개념이며 최대 대기시간을 필수 warmup으로 더하지 않는다.

N0는 기존 dispatch owner에 읽기 전용 readiness receipt를 연결한다. subscriber, 실제 WS 객체/연결·epoch, 기계/AI 소비자 준비, 기존 인증 존재·환경을 비밀값 없이 확인한다. 실제 준비 전에는 새 예약·전송을 시작하지 않고 `not_ready`와 첫 결손 의존성을 남긴다. 확인 후 전송 사이의 상태 변화도 기존 callback 시도·정확 claim/lease·physical 전송 증빙으로 대사한다. 미전송이 입증된 예약만 기존 해제 계약으로 정리하고 전송 uncertain/cleanup pending 슬롯은 풀지 않는다. 기동 비용은 steady-state 지표와 분리한다.

N1은 선택 branch가 요구하는 backward history·transition·hold와 현재 same-source 연속 구간을 대조한다. 기존 5슬롯·긴 슬롯 최대 2개·150초, 나머지 60초와 전체 요청 예산은 유지한다. 준비가 필요한 유형에 기존 긴 슬롯을 배정하고, 짧은 슬롯에서 판단할 수 없는 유형은 명시적으로 긴 슬롯 대기 또는 검증된 동일 route/epoch 이력 재사용으로 처리한다. 기존 fairness·cleanup을 보존하며 판단을 위해 time budget을 갱신하거나 슬롯/요청 수를 늘리지 않는다.

lease별 예약·REG/first 0B/0D·segment reset·feature ready·remaining residence·native signal/원 5초를 연결한다. gap/reset을 가로질러 이력을 이어붙이거나 UNKNOWN을 FALSE로 바꾸지 않는다. 현재 허용 residence 내에서 원천이 완성되지 않으면 `feature_window_incomplete` terminal로 남긴다. 정상 FALSE 40과 UNKNOWN 10을 각각 검증하고 부실 window를 정책의 낮은 승률로 반영하지 않는다.

회귀: subscriber만 준비된 기동, WS/AI/token 각 결손, 전송 직전 준비 변경, 실제 미전송/전송 uncertain 구분, 60초 feature+1초 hold의 짧은 배정, 첫 체결 지연·segment reset, 이미 존재하는 동일 source 이력, 긴 슬롯 2개 소진, 동시 종료/cleanup, 날짜/PID·시장 전환을 검증한다. WebSocket control/recovery나 API 계약을 실제 수정하는 경우에는 공식 reference gate를 먼저 적용한다.

## 7. S3 — 관측 append 계약 대사

구현 리뷰 보완: queue 완료 보존식은 `completed = append_confirmed + intentionally_not_written + append_unobservable`, `queued = completed + append_failed + pending_items`다. 종전 `failed`와 새 `append_failed`는 같은 실패 분모다. bool/None 반환을 append 성공으로 간주하지 않으며, 의도된 skip은 명시적 반환 계약이 있을 때만 인정한다. callback/category별 진단은 개수 제한과 overflow 합계를 둔다.

`completed_without_append_receipt`의 producer/category/callback를 값 없이 유한 범위에서 식별하고, 실제 writer가 파일/세대/내용 또는 append 결과를 확인한 반환 계약을 대조한다.

- 필수 native/async/claim/거부 증빙의 저장 성공은 `append_confirmed`로만 인정한다. callback 완료·Future 완료·None 반환으로 성공을 만들어내지 않는다.
- 의도된 skip은 조건/owner를 명시한 `intentionally_not_written`으로 남긴다. 실패 또는 확인 불가는 `append_failed`/`append_unobservable`로 분리한다. 기존 backlog/ring/queue 한도와 failed 경보를 보존한다.
- 계좌/custody writer의 반환만 누락됐으나 실제 파일·consumer가 맞는 경우에는 그 writer의 반환/검증 계약을 수리한다. 과거 27건을 모두 실패나 모두 성공으로 재작성하지 않는다.
- append receipt에는 exact source date/PID/key/source hash를 결속하고, 기존 reader가 읽은 필드를 확인한다. queue가 받은 수·처리 수·필수 append 수·skip/실패/미확인 수의 보존식을 검증한다.

## 8. S4 — 과차단·타점 연구의 source 계약

구현 리뷰 보완: S4는 기존 원장 행과 exact normalized quote 구간을 받아 native label owner를 호출하는 source-only reader로 구현한다. source index 부재는 `excluded`이며, 이를 해결하려고 live 원장 전체를 복제하거나 전수 스캔하지 않는다. WIN이 관측되기 전의 원천 결손도 제외한다. 같은 opportunity의 동일 복제본은 한 번만 집계하고, 원천/판정 내용이 충돌하는 중복은 제외한다. 종목 유형이 미확정이면 `unobservable`로 두며 이름이나 수익 결과로 유형을 추정하지 않는다. S2 scheduler 변경·성능 절감은 실제 eligible→Main 방문 지연이 입증된 경우에만 진행하며, 계측 추가 자체를 성능 향상으로 표시하지 않는다.

분류·수리의 운영 수용에는 경제성 추가 hurdle을 붙이지 않는다. 정책 변경의 필요성은 다음 source-only 비교로 따로 평가한다.

1. 기존 Main shared ledger와 원 normalized source/registration/capture/분 단위 종료 partition을 재사용한다. 하나의 opportunity에 원 신호 시점, 실제 machine/AI/main terminal, branch membership을 참조로 붙인다. 새 AI 비교 호출·full ledger 복제·전체 과거 원장 재생성을 하지 않는다.
2. 원 native 진입 ask, 같은 route의 이후 실행 가능한 exit quote, cost rate `0.0023`, 비용 후 목표 `+0.4%`, soft-stop `−3%`, 원 진입 이후 최대 `1800초`를 기존 native binary label owner와 일치시킨다. 비용 차감 방식과 stop 가격은 해당 owner의 정의를 재사용하며 진단 friction 값을 더하거나 대체하지 않는다.
3. stop에 먼저 닿지 않고 목표에 30분 내 도달한 지점만 승리다. 완전한 30분 경로에서 목표 미도달은 실패, stop-first는 실패다. 같은 시각 순서 불명, quote/비용/source 결손, 불완전 window는 Unknown/excluded로 구분한다. 30분 이후 도달은 후순위 분석이다.
4. claim 전 소실/만료, AI PASS 후 native 무효화, AI VETO/미호출과 정상 ENTRY를 서로 다른 모집단으로 비교한다. old claim 뒤 새 반전이 생기면 별도 opportunity로 평가한다. 무효화 뒤 상승한 가격을 원 PASS의 합법적 재사용 근거로 삼지 않는다.
5. 삼성/비삼성, PRE/REGULAR/AFTER, 비삼성 종목 유형·branch별로 집계한다. 실제 order/fill/PnL과 CF 승패는 합산하지 않는다. 비용 EV 크기, 과거 제출 이벤트 통과 또는 새 sample floor를 이번 원천 결함 수리의 요건으로 추가하지 않는다.
6. 기존 pending AI outcome row는 원 entry ask/soft stop/비용/label owner가 맞는 경우에만 join한다. 기존 current-price 진단 행은 그대로 보존한다. 정확 분 partition/기존 source index로 필요한 구간을 읽고, index/수신 원천이 없어 복원할 수 없는 행은 이유와 함께 제외한다. 재기동 경계를 price path 연속으로 합성하지 않는다.
7. 누적 승률과 paired false-negative/false-positive·winner retention을 보고하되, 자료가 없는 cell은 measured 0%로 만들지 않는다. 증거가 없는 시장의 정책은 현행 승계 계약을 유지한다. native 수명/FIRST 또는 프롬프트를 변경하는 후보가 필요하면 이 결과를 근거로 별도 등록·적용 계약을 검토한다.

## 9. 소유 위치·리뷰·검증

기존 소유 파일을 우선 수정한다. 운영 진입은 `src/engine/kiwoom_sniper_v2.py`·`sniper_state_handlers.py`, 비실행용 계측은 `src/engine/monitoring/runtime_performance.py`, native source adapter는 `src/engine/scalping/reversal_source_diagnostics.py`, async/기한·probe는 기존 scalping package, discovery readiness/queue는 `src/scanners/zero_base_discovery_runtime.py`·`zero_base_discovery_queue.py`, 관측 queue는 `src/utils/pipeline_event_logger.py`가 소유한다. `src/engine` root에 새 Python 모듈이나 이중 구현 wrapper를 만들지 않는다.

- 기존 `test_scanner_async_eval.py`, `test_scanner_async_entry_bridge.py`, `test_fixed_watch_submit_source_repair.py`, `test_main_fixed_watch.py` 및 해당 queue/source/loop 회귀를 우선 확장한다. 새 테스트가 필요하면 현재 테스트 구조 확인 후 `src/tests`에 명시적 역할로 둔다.
- 리뷰 순서는 구현→self review→보완→재리뷰→targeted validation이다. missing/stale, native invalidate, branch union, 동시 tick/claim, late response, 서로 다른 request의 cleanup, PID/date/route 변경, retry/dedup, 관측 failure를 검증한다.
- source/guard 결정 parity와 유효 결과 1회 인계를 확인한다. selected opportunity 보존식은 분류된 cohort에서 닫고, EV·실제 주문·모든 시장 자연 표본을 코드 결함 수리의 추가 gate로 만들지 않는다.
- Python targeted pytest·compile, wrapper 변경 시 `bash -n`·기동/ordered deployment 회귀, `git diff --check`를 수행한다. 문서 변경은 link/owner/authority와 print-only parser만 검증한다.
- Kiwoom request/parser/FID/REG/recovery를 변경하지 않는 현재 계획에는 신규 API 호출이 없다. 후속 구현이 그 경계를 건드리면 실제 수정 전에 현행 공식 revision/spec gate를 적용한다. 기존 normalized receipt를 새로운 broker protocol 해석으로 대체하지 않는다.

## 10. 인계·배포·자연 수용

현재 장후 OPEN `DirectFamilySourceRepairCompactAuxiliary`와 `continuous_reversal_postclose`를 S4 분석/보조 튜닝 인계 owner로 유지한다. S0~S3 후속 구현은 기존 `MachineAuxiliarySignalDeliveryRepair1012`, N0·N1은 기존 `NonfixedDispatchReadinessReview1012`의 새 결함 범위로 리뷰하며 이전 완료 기록을 보존한다. 배포 증빙은 기존 `OrderedIntradayDeploymentRepair1012`를 사용하고 별도 자동 실행 owner/cron을 만들지 않는다.

이번 구현은 현재 실행 중 PID에 봉인된 체크리스트를 바꾸지 않는다. 실행 OPEN/시간창/Acceptance는 같은 stable owner의 [후보 checklist](../../tmp/native-signal-claim-repair-20261012/2026-10-12-stage2-todo-checklist.md)에 준비했고, 이전 완료 근거를 유지했다. 이 후보는 운영에 게시하지 않았다. 승인된 ordered 배포가 현행 종료·게시·검증 순서를 지킨다. baseline README/runbook/Plan Rebase/AGENTS는 수정하지 않았다.

배포는 후속 구현·검증과 해당 변경의 승인 범위가 확인된 뒤 수행한다. native candidate preflight/unchanged-policy 호환성 확인이 Main 종료보다 앞선다. detector 직렬화, 정상 drain, selector/checklist 게시, exact-PID handoff/bootstrap/보조 registry 소비 검증 및 마지막 selector/PID 안정성 대사를 유지한다. 기존 5초·provider/model·source/quote/order/custody/수량·cap·cooldown·manual/hard safety와 퇴역 owner 경계는 유지한다.

새 PID 자연 창은 PRE/REGULAR/AFTER·상시/비상시를 분리하고 동일 source load 상태에서 검사한다. S0 모집단 보존식, S1 exact terminal, S3 mandatory append→reader를 각각 확인한다. S2는 기존 guard를 통과할 수 있었던 동일 신호의 방문·처리 지연과 전체 loop tail을 확인한다. 자연 신호가 없으면 코드/로드 PASS와 자연 수용 미관측을 분리한다. invalidated/expired가 줄거나 PASS가 생겼다는 사실만으로 수익 개선을 선언하지 않는다.

rollback trigger는 중복 인계/주문, original deadline 연장, source/quote 검증 누락, custody/주문·실보유 우선순위 손상, 동시성/한도 위반, crash 또는 검증된 처리·원천 부하 회귀다. source/diagnostic rollback은 기존 native 결정과 manual custody를 보존하고 퇴역 소비자를 복원하지 않는다. 정상 반전 무효화·희소 신호·원천 제외 또는 손익 무표본 자체는 rollback 이유가 아니다.

## 11. 이번 계획의 완료 상태

| 범위 | 작업본 구현·검증 결과 | 남은 증거 |
| --- | --- | --- |
| S0 | 정확 scope/generation별 lifecycle, 유효 구간·Main 방문·claim·정상 무효화·불명 상태, bounded ring/append 및 기존 분 partition 연결 | 배포 후 동일 PID 자연 모집단 |
| S1 | Main 재검증 predicate·branch 생존·원 기한·registration hash capsule, ack 오류에도 원 거부 이유 보존 | 실제 PASS 이후 재검증 표본 |
| N0/N1 | subscriber와 실제 WS/AI/token/기계 consumer 준비 구분, 시작 직전 재검사, branch 필수 history 기준 기존 residence 배정, FALSE/UNKNOWN 구분 | 현재 시장별 실제 수신·관측기간 표본 |
| S2 | Provider 전/호출/응답 후/기록·캐시 구간 clock 추가. 기존 정책·5초 기한 유지 | eligible→Main 지연의 인과 확인 뒤 조건부 scheduler 최적화 |
| S3 | 저장 확인/의도적 미기록/미확인/실패, owner별 bounded 집계, 실제 checkpoint writer 저장 영수증 | 새 PID writer→reader 자연 대사 |
| S4 | 기존 shared ledger owner의 bounded source-only 승패 reader. native ask→동일 경로 bid·비용·stop-first·30분 및 후순위 늦은 도달, 중복 충돌 제외, 시장/종목 유형/branch·paired 집계 | native ask·epoch·scope·원천 window index가 결속된 유효 표본 |

통합 회귀 1,207건과 추가 동시성 1건이 통과했다. 실제 native selector와의 관측/claim parity, 성공 원장 append와 lossless 분 partition의 해시·필드 보존, queue 보존식·기존 worker/슬롯 한도를 검증했다. [계측 비용 비교](../../tmp/native-signal-claim-repair-20261012/diagnostic-overhead-benchmark.json)는 동일 5,000개 관측·500개 기회, baseline/candidate 교대 3회이며 callback p95는 약 0.0049ms→0.0155ms다. 이는 약 0.011ms 추가 계측 비용이며 전체 Main 처리 속도 향상 주장이 아니다.

[기존 4건의 source-only 재검토](../../tmp/native-signal-claim-repair-20261012/historical-source-research.json)는 작은 exact terminal partition과 capture 요약을 대조했다. 이 원천에는 native 진입 ask·scope/native epoch·정규화 후행 window index 결속이 없어 4건 모두 제외했고 승률은 null이다. 원장 전체를 재스캔하거나 종가/current-price를 대신 넣지 않았다. 과거 age-only 30건도 `historical_unresolved`로 남긴다.

코드리뷰 범위에서 미해결 결함은 없으며, 배포/재기동·운영 정책 변경·전체 보조판정 성능·경제성 개선은 별도 증빙 대상이다. AI 호출과 운영 장후 재실행은 하지 않았다. parser·compile·link·diff 및 파일 해시 근거는 [완료 영수증](../../tmp/native-signal-claim-repair-20261012/completion.json)에 보존한다.
