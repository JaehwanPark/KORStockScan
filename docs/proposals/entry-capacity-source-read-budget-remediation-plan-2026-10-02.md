# 계좌 여력 원천 조회 중복·공용 읽기예산 보완계획

작성일: 2026-10-02 KST. 상태: 구현·반복 리뷰·표적 회귀·3회 샘플 성능 수용 완료. 배포/PID 소비·자연 절감·경제성 수용 전.
실행 소유자: [당일 checklist](../checklists/2026-10-02-stage2-todo-checklist.md)의 `EntryCapacityReadBudgetRemediation1002`.

## 1. 목적과 수용 범위

Main의 기계판정·보조 AI 장후 튜닝에 필요한 정확 계좌 여력 영수증을 유지하면서, 같은 요청의 반복과 캐시 오인 무효화를 줄인다. 특히 `BLOCK/RECHECK` 미진입 상승의 분석 원천이 줄어드는 방식으로 조회량을 낮추지 않는다.

첫 변경은 기존 **준비/ENTER_NOW 관측 2초, 비진입 관측 5초**, 정확 종목·단가, 계좌·재고·주문 소유권 세대 검증을 유지한다. 실제 sizing·주문 직전·각 leg·잔여 주문·AVG_DOWN의 필수 조회는 기존 경로로 새로 확인한다. 공유 전체 5회/초·source-only 4회/초, 기존 대기/HTTP timeout·재시도·cooldown, 거래 정책·수량·가격·provider·hard safety를 보존한다. 거래 요청과 계좌 원천을 공용 분봉 캐시에 넣지 않는다.

2026-10-02 17:49 확인 기준 선택 소스는 `d19d0d7bf9d9bd5cb491c977648783ccffb11bdc`, Main은 ubuntu PID `2920811`이다. 이는 설계 기준점이며 구현 시 selector와 실제 PID를 다시 확인한다. 이 문서는 런타임을 변경하지 않는다.

## 2. 확인된 호출 구조와 결함 후보

| 지점 | 현재 동작 | 보완 대상 |
| --- | --- | --- |
| `sniper_state_handlers._resolve_scanner_async_entry_ai::refresh_before_evaluate` | 적격 실물 초기 진입 frame에서 기계판정 전에 정확 단가 계좌 원천을 선조회한다. | 새 판정 전에 원천이 있어야 하는 시간 계약은 유지하면서 기존 정상 receipt와 중복 준비를 먼저 확인한다. 기계 결과가 BLOCK/RECHECK여도 이 단계의 조회는 이미 소비될 수 있다. |
| `_request_entry_capacity_preparation` / `prepare_pending_entry_capacity` | legacy 평가와 ENTER_NOW 결손 후속 준비가 기존 observer worker의 큐를 사용한다. 같은 종목의 낡은 pending 가격을 병합한다. | async 선조회·pending 준비가 동일한 상태표와 실행 중 요청을 사용하게 한다. 현재 pending 병합이 모든 즉시 선조회에 적용되는 것은 아니다. |
| `_entry_capacity_receipt_key` | token/origin/date scope, 계좌, 종목, 정확 단가, inventory signature 및 **예수금 meta 전체**를 해시한다. | `age_sec`, `cache_hit`, fresh→loop-cache 표시만 바뀌어도 key가 달라질 수 있다. 실제 금액·원 receipt가 같은 경우의 잘못된 cache miss를 fixture로 재현한다. 자연 발생 빈도는 아직 계측되지 않았다. |
| `_scale_in_budget_inventory_signature` | 모든 ACTIVE_TARGETS의 상태·주문 필드와 owner journal의 stat 세대를 포함한다. | 금융 상태와 관찰 상태의 변화를 계측한다. 첫 변경에서는 이 보수적 세대를 그대로 유지한다. 삭제할 필드가 안전하다는 증거 없이 key를 좁히지 않는다. |
| `_observe_entry_economics_before_ai` | ENTER_NOW는 정확 원천 조회 가능, BLOCK/RECHECK는 cache-only. | raw 기계 attempt를 모두 보존하고 비진입 economic coverage를 별도로 확인한다. 결손을 회복했다고 소급 표시하지 않는다. |
| `kiwoom_utils.get_orderable_by_margin_kt00011` | 초기 진입 원천도 `scale_in_budget_source`라는 owner를 기록한다. 성공·reuse의 전체 분모는 현재 보류 로그로 알 수 없다. | 요청 목적을 호출자가 전달하도록 명확히 하고 논리 수요·실물 요청·보류·성공을 따로 계측한다. 이름 변경만으로 호출 절감이라 하지 않는다. |

17:45:59 부분일 점검에서는 최근 30분 보류 1건, 최근 10분 0건이었다. 17:24:41의 005930 kt00011은 5건 사용 중 source-only 한도 4건·약 1.058초 대기 후 보류, HTTP 시도 0회였다. 이 보류 건수는 전체 호출량이나 실패율이 아니다. 재기동 후 probe 55건 중 54건이 다른 WS 원천 결손으로 끝난 창도 있어, 단순 전후 0건 비교는 절감 근거가 될 수 없다.

## 3. 구현 순서

### P0. 물리 호출과 원천 커버리지의 분모 확보

- 기존 capacity helper에 `purpose`를 전달한다: `entry_capacity_prefetch`, `entry_operating_observation`, `entry_live_sizing`, `entry_pre_submit_capacity`, `entry_residual_capacity`, `scale_in_live_capacity`. 독립 연구 계좌 수집은 자신의 기존 owner를 유지한다.
- 기존 logger/pipeline writer로 논리 요청 ID, 연결 가능한 evaluation/preparation ID, PID/commit, code, 정확 단가, 계좌 scope hash, 날짜/route/session, 요청 지문, 준비 시작·HTTP 시작·응답 수신·관측 시각을 남긴다. 계좌번호·token·요청 headers는 기록하지 않는다.
- 결과는 `exact_reused`, `fresh_success`, `inflight`, `pending`, `deferred`, `http_failed`, `contract_invalid`, `expired`, `scope_changed`로 나눈다. 논리 요청 수와 admission 시도/실물 HTTP 수를 별도 집계한다. 연속조회·인증 재시도도 실물 요청에서 누락하지 않는다.
- cache miss 원인을 만료/가격/계좌·token·origin·날짜/재고·custody/예수금 원천 세대/진단 meta 변화로 구분한다. 금융 금액과 세대의 전체 snapshot/hash는 보존한다.
- 집계는 당일 incremental cursor 또는 이미 읽는 bounded source로 생성한다. raw 전체 로딩, 새 cron, 추가 계좌 조회·provider 호출·계측 실패의 매매 예외 전파를 추가하지 않는다.

### P1. 진단 meta로 인한 오인 무효화 제거

`_entry_capacity_receipt_key`의 예수금 부분을 아래 두 객체로 나눈다.

1. **동일성:** 계좌/token/origin/date, 원 조회 receipt 세대와 실제 원 수신시각, 원금액·적용금액, operator floor 적용 값/authority, 원천 신뢰 상태. 원 금액이 같더라도 새 broker 조회는 새 receipt 세대다.
2. **진단:** 호출 시점 `age_sec`, `cache_hit`, 캐시 전달 경로. 동일한 원 receipt를 fresh/loop-cache로 읽었다는 차이만으로 새 계좌 세대를 만들지 않는다.

`kiwoom_orders`의 기존 deposit cache record에 원 정상 조회 세대와 원 시각을 전달한다. 캐시 hit마다 시각을 갱신하지 않는다. cooldown/fallback·원천 결손·override 변경은 신뢰 조건으로 계속 차단/무효화한다. 기존 주문가능금액 operator floor와 실제 주문 계산은 바꾸지 않는다. 원 세대를 확인할 수 없으면 기존 보수적 key 또는 `capacity_scope_unavailable`로 남긴다.

이 세대/신뢰 검사는 source-only 재사용에 적용한다. 정상 실행의 deposit fallback/floor 반환이나 기존 필수 계좌 조회 결과를 새 관측 기준으로 차단하지 않는다. 새 receipt 세대 때문에 합법적으로 필요한 조회와 단순 진단 변화의 중복을 따로 비교하고, 자연 총 요청 절감은 실측 전 확정하지 않는다.

가격을 다르게 요청한 kt00011 결과는 나눗셈으로 수량을 환산해 쓰지 않는다. 다른 종목·계좌의 응답도 공통 예수금처럼 취급하지 않는다. 관측 당시 금액·세대와 보존된 original metadata를 나중의 상태로 덮지 않는다.

### P2. 기존 준비 경로의 중복 실행 통합

- 기존 `_ENTRY_CAPACITY_*` 상태와 helper를 확장한다. 새 thread/service/engine-root module을 추가하지 않는다. async final-frame 선조회, legacy pending 준비, ENTER_NOW 후속 준비가 같은 정확 request 상태를 확인한다.
- 정상 exact receipt가 있으면 원 시각 그대로 재사용한다. 동일 지문의 진행 중 준비에는 두 번째 source-only HTTP를 보내지 않는다. pending 요구만 하나로 합치며 현재 큐 8건·pending 5초·retry suppression 0.5초 한도를 보존한다.
- 최종 평가 frame을 준비하는 worker만 자신의 기존 deadline·최대 admission 대기 1.25초 안에서 완료를 확인할 수 있다. 이미 확정된 평가/observer는 기다렸다가 미래 응답을 채택하지 않는다. 필수 주문 조회는 source-only 진행 중 상태를 기다리거나 재사용하지 않는다.
- 기존 요청 합류를 기다린 시간과 이후 admission 대기를 합산해 기존 preparation 대기 예산을 적용한다. 합류 대기 뒤 1.25초를 다시 부여하거나 HTTP 시간을 worker deadline 밖으로 추가하지 않는다. 기계/AI observer의 동기 호출은 기존 wait bound를 유지한다.
- 동일 종목의 진행 중 가격이 달라졌으면 새 frame은 최신 pending 가격을 남긴다. 기존 응답을 새 가격의 응답으로 재명명하지 않는다. superseded/기한 만료 요구는 원 attempt의 결손으로 보존한다. 모든 서로 다른 정확 가격을 하나의 성공으로 세지 않는다.
- network I/O 동안 공유 state lock을 잡지 않는다. 정상/예외/timeout/취소/프로세스 재기동에서 in-flight 정리와 원 clock/hash 보존을 검증한다. source-only/account의 프로세스 간 응답 공유는 첫 변경에 추가하지 않는다.
- 양쪽 준비 경로가 이미 배제하는 simulated/보유 초기진입 아님·가격 결손 및 기존 replay route 불지원은 원천 준비 전에 확인할 수 있다. **기계 BLOCK/RECHECK 자체를 선조회 제외 조건으로 만들지는 않는다.** 누락된 route를 추정해 채우거나 경제성 원천 실패로 기계판정을 생략하지 않는다.

### P3. 판정과 장후 경제성 결속 검증

- 원 source 준비 → 최종 특징/가격 확인 → 기계판정 → AI 전 owner plan 동결 → 필요 시 보조 AI의 순서를 유지한다. 계좌 조회를 기계판정 뒤로 단순 이동하지 않는다.
- account receipt 수신시각은 해당 frozen decision/plan 시각보다 늦을 수 없다. 이후 도착한 응답은 다음 자연 attempt에서만 적격성 검증 후 사용할 수 있다. 지난 economic gap을 backfill하지 않는다.
- 모든 기계 `BLOCK/RECHECK/ENTER_NOW` attempt와 고유 opportunity를 보존한다. BLOCK/RECHECK도 기존 5초 exact cache-only 경로의 양성·음성 표본이 유지되는지 검사한다. ENTER_NOW만 모아 coverage를 좋게 보이게 하지 않는다.
- machine 가격/목표·손절·정확 비용 평가 가능, owner/capacity economic replay 가능, auxiliary 실제 PASS/VETO/timeout·의미 거절·후행 라벨 가능을 각각 집계한다. capacity gap 때문에 가격 분석이나 raw 기계 표본을 전체 제거하지 않는다.
- 비용·stop/owner·후행 경로 결손은 별도 유지하고 net EV·PnL을 0으로 채우지 않는다. 계좌 원천 보강은 정책 승계·실주문·순익의 증거가 아니다. SOR/애프터 unsupported operating replay는 조회 최적화로 지원됐다고 표시하지 않는다.

## 4. 표적 샘플·회귀·성능 검증

| fixture | 정확 통과 조건 |
| --- | --- |
| 동일 receipt, 2초 내 반복 10회, age/cache-hit만 변화 | 계측에서 기존 잘못된 miss를 재현한 뒤 candidate 실물 source 조회 1회, 원 시각/hash·경제 입력 값 동일. 기준선이 원래 1회인 경로는 추가 감소를 주장하지 않는다. |
| async·pending·후속 준비의 같은 정확 요청 경합 | 동일 준비 실물 source 조회 1회 이하. 재사용/대기/결손 개별 수요는 독립 receipt를 남긴다. observer 미래 응답 채택 0회. |
| 진짜 새 broker deposit receipt가 같은 금액을 반환 | 세대 변경으로 이전 원천 재사용 차단. 금액 동일만으로 동일성을 확정하지 않는다. |
| 가격·account/token/origin/date·inventory/custody/floor 변경 | 이전 원천 재사용 0회. 서로 다른 가격의 응답 환산 0회. 신뢰/세대 결손은 명시적 source_gap. |
| 2초 및 5초 경계, 미래 시각, 조회 중 상태 변경 | 기존 준비/ENTER_NOW 2초·nonentry 5초 경계를 그대로 통과/차단. 원 수신시각 갱신 없음. |
| BLOCK/RECHECK 양성·음성, ENTER_NOW, unsupported route | exact raw attempt/기회 분모·기계 action·후행 라벨 및 가능한 economic coverage가 baseline보다 줄지 않는다. 결손/unsupported 행은 유지한다. |
| 늦은 응답·worker deadline·보류·timeout·schema 실패 | 이전 plan으로 소급 연결 0회. 중복 재시도/실패 cache 성공화 0회, FD/lock/in-flight 잔류 없음. 기존 admission/HTTP 시간 상한 유지. |
| live sizing·pre-submit·각 leg·residual·AVG_DOWN, Main/widget/episode/manual | 모든 실행 필수 조회/guard/소유권은 동일. 같은 observation cache가 있어도 필수 확인 생략 0회. |

기존 `test_entry_cash_capacity_contract.py`, `test_entry_execution_sizing_plan.py`의 경제성 observer tests, `test_scanner_async_entry_bridge.py`/`test_scanner_async_eval.py`, `test_kiwoom_read_request_control.py`, `test_sniper_scale_in.py`의 영향 selector를 보강한다. 정확 deposit 세대 전달은 기존 deposit/cache tests도 포함한다. 실제 API/주문/인증/provider를 호출하는 시험은 수행하지 않는다.

고정 요청·상태 변화·응답 시각·admission workload의 baseline/candidate를 각각 3회 재생한다. 물리 요청/보류, source 수요와 exact reuse, raw opportunity, BLOCK/RECHECK·ENTER_NOW·auxiliary별 usable economic source를 같은 분모에서 비교한다. wall/CPU 중앙값은 baseline×1.10 이내, RSS 증분은 16MiB 이내를 첫 엔지니어링 수용 기준으로 둔다. 기존 절대 memory/대기 가드는 우선한다. 원천 clock/hash·기계/AI 선택·실행 safety 불일치 허용은 0건이다.

성공 fixture의 physical call 감소와 deadline/source 회귀를 모두 통과해야 코드 gate를 닫는다. 모의 호출 절감률은 자연 시장의 호출 절감률이나 수익률로 발표하지 않는다.

## 5. 변경 파일·리뷰·배포 수용

1. 기존 `src/engine/sniper_state_handlers.py`는 capacity identity/preparation/state/observer를, `src/engine/kiwoom_orders.py`는 deposit 원 receipt 세대 전달을 소유한다. `src/utils/kiwoom_utils.py`는 기존 governed account 호출의 purpose·실물 요청 메타만 확장한다. 분석 producer는 `src/engine/monitoring`의 기존 패키지를 재사용하며 필요한 새 파일은 역할/location gate 후 결정한다.
2. 구현 전 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)의 최신 upstream SHA·회수시각과 kt00011/kt00001의 docs/specs/core/Postman을 다시 확인한다. 문서/SDK 불일치와 불명확한 응답 의미는 추정하지 않는다. 이 계획 작성에서는 wire/parser/account call을 수정하지 않았고 새 공식 확인을 완료했다고 주장하지 않는다.
3. 구현 → self review → 보완 → 재리뷰 → 표적 pytest/compile/diff gate를 완료한다. producer→저장→machine/auxiliary/owner replay 소비와 예외의 권한 누출을 함께 검토한다. cron/wrapper 수정이 필요하면 당일 운영 문서와 checklist 및 shell 계약 검증을 같은 변경 집합에 포함한다.
4. 배포 단계는 같은 정책/PREOPEN/prepared 5파일·독립 서비스 pin·cron·별도 승인 override를 보존한 불변 release로 진행한다. ubuntu 계정의 native bot supervisor를 사용하고 root tmux를 만들지 않는다. guarded Main 종료 후 singleton·계정·cwd/commit·당일 bootstrap/native consumed·WS·다음 정기 consumer를 확인한다. 독립 widget/episode는 필요 근거 없이 재기동하지 않는다.
5. 자연 수용은 venue/session·물리 HTTP·필수/원천 등급·주체·적격 평가 workload가 맞는 창에서 판단한다. 경제성 가능 비율과 source 준비 지연이 악화되지 않아야 한다. 표본/동일 중복이 없으면 `not_observed`로 남기고 요청을 만들어 채우거나 05시까지 대기하지 않는다. 코드 수용·실제 PID 소비·자연 절감·정책/순익 수용은 각각 별도 기록한다.
6. scope/hash/clock/금액·cap 또는 안전 조회 회귀는 즉시 candidate 부적격이다. 이전 불변 release를 기존 정책 보존 handoff로 복귀한다. 원 source/실패 receipt는 보존하고 감시 기준·기존 lock을 완화해 성공 처리하지 않는다.

## 6. 이번 단계에서 유보하는 변경

2초/5초 TTL 확대, 계좌 세대에서 journal/inventory 필드 제거, 다른 단가·종목의 kt00011 환산, 계좌 응답 프로세스 간 캐시, ENTER_NOW 전용 경제성 모집단 축소는 별도 근거가 없으므로 첫 구현에 포함하지 않는다. 계측·정확 재사용·준비 통합 이후에도 **다른 정확 가격의 진짜 수요**가 주된 경쟁이면 남은 요청량을 그대로 공개한다. 감소 목표를 맞추려고 미진입 원천을 희생하지 않는다.

## 7. 계획 리뷰 및 현재 상태

현재 source caller/계좌 identity/메타 생성/준비 worker/경제성 frozen clock/후속 replay를 대조했다. 초기 검토에서 단순 TTL 연장·판정 이후 조회는 계좌 변경/미래 원천 채택 위험을, ENTER_NOW만 선조회하는 안은 미진입 상승 학습 원천 손실을 확인해 위 설계에서 제외했다. first phase는 deposit 진단 오인 key와 기존 준비 중복을 다루고, 광범위 inventory signature의 안전한 축소는 유보한다.

`EntryCapacityReadBudgetRemediation1002`는 새 중복/identity/물리 호출 계측·성능 개선을 소유한다. 기존 `MainEntryEconomicLineageRepair1002`는 정확 ENTER_NOW capacity와 guard/residual의 자연 lineage 수용을 계속 소유한다. 이미 완료된 공용 분봉/selector custody 수리를 새 계획의 미완료 상태로 바꾸지 않는다.

구현 결과는 [반복 리뷰·샘플 성능 기록](../audits/entry-capacity-source-read-budget-implementation-review-2026-10-02.md)이 소유한다. P0는 기존 로그의 목적별 당일/PID 누계와 정확 영수증 해시를 사용하며 새 cron/report producer나 전체 raw 로딩을 추가하지 않았다. `inventory_or_custody`는 기존 결합 signature를 그대로 대사하며, `deposit_identity_or_unproven_diagnostics`는 원 receipt를 확인하지 못하는 보수적 분기까지 포함한다. 이 혼합 사유를 금융 결손 또는 진단 중복 하나로 단정하지 않는다.

최신 격리 후보는 표적 회귀 278 PASS·동결 plan/장후 소비 64 PASS·native 배포/재기동 계약 136 PASS로 총 478개를 통과했다. 추가 재리뷰에서 늦은 자정 완료의 날짜 집계 초기화와 worker 마감 뒤 ready 표시를 보완했다. 동일 18,000개 논리 요청의 3회 모의 재생에서 source HTTP 10,000→1,000·필수 HTTP 5,000 유지·전체 15,000→6,000, 원 clock/hash/수량·고정 action별 capacity 분모 동일이다. Wall/CPU 중앙값 비율 1.031/1.031·RSS +1.29MiB로 첫 성능 기준을 통과했다. 실제 자연 절감/정책 수익률 시험은 아니다.

사용자 배포·재기동 승인에 따라 별도 clean checkout의 이번 계좌 여력 보완만 commit·불변 배포했다. 릴리스 `c61fefcf`, ubuntu Main PID `2948449`/supervisor `2948381`/tmux `bot`의 native handoff·당일 bootstrap·실제 소비를 확인했다. 불변 root 478 PASS, 정책 5파일·독립 pin 416개·cron hash 보존, heartbeat·WS·process health PASS다. 원 workspace의 다른 가격 패턴 작업은 보존했다. 실제 증거는 구현 audit이 소유한다. 단일 BLOCK의 원 receipt 재사용·추가 HTTP 0회는 확인했으나 전체 자연 절감률은 적격 비교 분모가 부족해 같은 OPEN owner로 남긴다. 전일 postclose FAIL과 정책 경제성을 이 배포로 닫지 않는다.
