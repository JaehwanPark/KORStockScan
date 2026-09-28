# 키움 읽기 관측 분산·정확 요청 재사용 구현계획 (2026-09-28)

## 1. 결정과 권한

첫 구현 후보는 `market_opportunity_census.ka10027`의 네 패널을 한 5분 수집 주기 안에서 분산하고, `kt00005` 잔고 대사 영수증에 KRX·NXT별 완전성 상태를 남기는 것이다. 공유 읽기 상한, Main 주문·진입/청산 판정, 공급자, 임계치, 수량, 계좌/주문 보호 장치는 변경 대상이 아니다. 이 문서는 구현·릴리스 선택·프로세스 재기동·실거래 효과의 완료 영수증이 아니다. 현재 일일 실행 owner는 [9/28 checklist](../checklists/2026-09-28-stage2-todo-checklist.md)이며, 이 제안서만으로 새 장중 런타임 작업을 열지 않는다.

목적은 같은 token·origin의 국내 읽기 TR에서 source-only 관측 호출이 한꺼번에 몰릴 때 생기는 HTTP 이전 보류를 줄이는 것이다. 현행 [공유 읽기 계약](../kiwoom-api-data-contract.md#2026-09-03-domestic-read-tr-shared-rate-gate)은 전체 5회/초, source-only 4회/초이고 보류는 증권사 제한 응답이나 주문 제출 실패가 아니다. `kt00005` KRX·NXT 완전 대사와 정확 호가/용량 안전 계약은 우선한다.

## 2. 실제 기록·테스트 기준선

아래 수치는 **9/28 장중 누적 파일을 해당 시각까지 읽은 부분일 재생**이다. 파일은 계속 추가되므로 날짜 전체 결과나 고정 artifact로 취급하지 않는다. 동일 비교를 구현 시에는 입력 cutoff와 SHA를 고정해 재생한다.

| 입력·cutoff | 관측 | 설계에 주는 제약 |
| --- | --- | --- |
| `data/pipeline_events/pipeline_events_2026-09-28.jsonl`, 10:30까지 `scalping_scanner_prune_bbo_observation` 384건·40 episode | 정확 호가 포착 330, 원천 결손 54. 1/2/5/10초 이전 성공 응답을 같은 종목 다음 관측에 적용하는 후보는 각각 0/2/39/124건이다. 2초 이상 후보 전부 원 응답시각이 다음 요청 시작보다 이르다. 종일 후보 345건도 전부 그 상태다. | 다른 시점의 `ka10004` 성공값을 새 표본으로 재사용할 수 없다. 결손을 과거 가격으로 채우지 않는다. |
| 같은 BBO 384건의 예약시각·요청시각 재생 | 요청 시작 지연 p95 4.428초, 최초 표본 p95 3.276초. 최소 시작 간격 0.25→0.35/0.50초의 보수적 고정 소요시간 재생에서 최초 표본 p95 3.371/3.920초. | 10개 표본 오프셋 `0,3,10,20,30,60,180,300,600,1200`과 0.25초 최소 간격을 첫 변경에서 유지한다. 이는 경합 감소에 따른 실제 지연 개선을 예측하는 모델이 아니다. |
| `data/market_opportunity_census/market_opportunity_census_2026-09-28.jsonl`, 10:35까지 104개 패널 | 88개 정상·16개 `ka10027_shared_read_budget_deferred`. 같은 거래소·패널·요청 조건의 연속 정상 스냅샷 84쌍 중 **외부 BBO 필드를 제외한 조사 행**은 83쌍, 종목 목록은 80쌍이 다르다. 정상 쌍의 중간 간격은 300.2초다. 원장의 전체 hash는 외부 BBO도 포함하므로 순수 `ka10027` 변동 증거로 세지 않는다. | 장중 `ka10027`의 5분/종일 응답 캐시는 현재 수집시각을 대체할 수 없다. 현행 연속조회 경로의 관측용 1페이지 한도를 유지한다. |
| 같은 시장 조사 32회 수집 주기의 완료시각 재생 | 네 패널 완료시각에 최소 5초 간격을 부과한 낙관적 일정 재생에서 마지막 패널은 예약시각 기준 최대 41.94초였다. 현행 cadence는 300초, 허용 지연은 60초다. | 5초 패널 간격은 **시험 후보**다. 실제 호출 대기·외부 BBO·다른 프로세스 경합을 재생하지 못하므로 속도 제한 감소나 60초 준수를 아직 입증하지 않는다. |
| `logs/kiwoom_utils_info.log`, 장중 10:36 무렵 | `scale_in_budget_source` 보류 40건 중 같은 종목의 2초 이내 후속 보류는 1건뿐이다. 그 기록에는 단가·계좌 세대가 없다. `kt00005`의 KRX 또는 NXT 요청 보류 뒤 정기 대사 차단이 09:31·10:27 두 번 있었다. | `kt00011`의 기존 진입 2초·비진입 5초 정확 재사용을 연장할 근거가 없고, 잔고 완전성은 별도 운영 지표가 필요하다. |

현행 코드의 영향을 받는 계약 테스트 네 파일을 `PYTHONPATH=. .venv/bin/pytest -q`로 실행해 **185 passed**를 확인했다. 대상은 `test_pruned_candidate_bbo_collector.py`, `test_market_opportunity_census.py`, `test_kiwoom_read_request_control.py`, `test_entry_cash_capacity_contract.py`다. 이 통과는 후보 pacing의 실제 효과, 릴리스 배포 또는 Main PID 소비를 증명하지 않는다.

## 3. 변경 설계와 소유 경계

### 3.1 시장 조사 source-only 네 패널 분산

- 생산자: `src/engine/monitoring/market_opportunity_census.py::capture_market_snapshots`. 기존 `liquid_common` 우선, KRX/NXT별 요청 조건, 관측 주기 300초, 허용 지연 60초, 외부 BBO 240초 수집 창, `max_pages_limit=1`을 보존한다. 독립 스캐너나 주문 경로로 기능을 옮기지 않는다.
- 구현: 기존 주입 가능한 `monotonic_clock`·`sleeper`를 사용해 **직전 `ka10027` 패널 요청 시작으로부터 최소 5초**를 후보로 둔다. 완료시각이나 cron 기동시각을 새 증권사 수신시각으로 찍지 않는다. 관측/응답 실제 시각, panel별 `request_attempt_count`, 대기시간, `read_rate_control_status`, page count를 남긴다. 계획한 대기만으로 60초 cadence 또는 세션 경계를 넘을 예상이면 pacing을 우회하고 incumbent 방식으로 요청하며 우회 사유를 기록한다. 실제 실패는 기존 source-gap 의미를 보존한다.
- 적용 스위치: `panel_min_start_interval_sec=0`을 기본으로 하여 incumbent와 동일하게 둔다. source-only collector에서만 후보 5초를 지정한다. cron의 5분 slot과 다른 process의 요청 등급·속도 상한은 유지한다. cron/wrapper 또는 자동화 규칙을 실제 수정할 때에는 운영 문서와 당일 checklist를 같은 변경 집합에서 갱신한다.
- 후속 분석: 수집 주기별 네 패널 성공률·시각 간격과 외부 BBO 요청수/결손을 기록한다. KRX·NXT와 `all`·`liquid_common`을 합쳐 단일 성공으로 세지 않는다. 5초 간격이 경합을 낮추지 못하면 다른 source-only owner와의 시각 중첩을 실측한 다음 별도 후보를 낸다.

### 3.2 정확 요청 재사용의 구현 범위

| 요청 | 이번 변경 | 유효성 계약 |
| --- | --- | --- |
| 탈락 후보·외부 시장 조사 `ka10004` | 새 완료 응답 캐시 없음. 10개 표본 및 정확 route/시각 유지. | 뒤의 관측 시작 전에 받은 호가를 그 관측의 현재 호가로 승격 금지. 동일 시점의 다중 owner 합류는 응답 수신시각이 모든 참여 요청 시작 이후임을 증명하는 별도 연구가 필요하다. |
| 장중 시장 조사 `ka10027` | 5분 주기·1페이지 유지. 주기 간 재사용 없음. | 요청 조건이 같아도 응답 내용·종목 집합이 실제로 변했다. 5→10분은 현행 최대 360초 cadence 계약을 위반한다. |
| 진입 용량 `kt00011` | 기존 source-only 2초/비진입 5초 정확 receipt 재사용 유지; runtime-required sizing은 새로 읽는다. | token/origin/KST 날짜·계좌/재고 세대·종목·단가·원 수신시각과 유효 응답 hash가 맞아야 한다. 보류/빈 응답은 성공 cache에 넣지 않는다. |
| 잔고 `kt00005`, 미체결·주문 참조 | 실행 custody용 캐시·종일 재사용 없음. 두 거래소 완전성 영수증만 보강한다. | 한 거래소의 성공 또는 `BROKER_SNAPSHOT_REFRESHED`만으로 KRX+NXT 대사 성공을 주장하지 않는다. |
| 확정된 과거 날짜의 보고 전용 자료 | 별도 2차 후보로 분리. | 날짜별 terminal/원천 hash의 불변성, 같은 요청의 반복 여부와 물리 호출 절감량을 먼저 증명한다. 현재 날짜 자료나 실거래 입력에는 확대하지 않는다. |

재사용 구현의 첫 단계는 source-only 요청에 민감정보가 없는 **정확 요청 지문과 시작·수신시각**을 남겨 같은 KST 날짜·token/origin·TR·payload·route·요청 등급·page/timeout 조건의 동시 중복을 세는 것이다. `ka10004` 후보는 후속 요청 시작 **이후**에 받은 동일 지문의 성공 응답만 합류 가능하다. 독립 프로세스 사이에서 적격 동시 중복이 실제로 관측되면 저장·잠금·대기 상한·원 수신시각 보존을 갖춘 별도 source-only 합류 후보를 작성하고 동일 분모 재생으로 물리 호출 절감을 입증한다. 적격 중복이 0이면 캐시 코드를 추가하지 않고 `no_eligible_exact_reuse`로 닫는다. 오류·보류·부분 응답, account/order, 실행 필수·critical 요청은 이 합류 후보에서 제외한다.

### 3.3 잔고 대사 가시성

`src/engine/sniper_sync.py::refresh_broker_account_snapshot_read_only`와 정기 대사 경로의 기존 로그에 `successful_exchanges`, `required_exchanges`, `inventory_complete`, 조회 시작·완료 시각을 민감정보 없이 추가한다. 두 경로의 기존 실행·차단 의미는 유지한다. `BROKER_SNAPSHOT_REFRESHED`는 미체결 응답 확인과 잔고 완전성을 각각 표시한다. 이를 통해 한 거래소만 성공한 뒤의 일반 갱신 기록을 완전 복구 영수증으로 오독하지 않게 한다. 이후 자연 실행에서 양 거래소의 동시 성공과 차단 이후 정상 대사 완료를 확인한다.

## 4. 구현 순서·검증·롤백

1. **원천 동결 및 공식 API gate.** 9/28 종료 뒤 로그·파이프라인·시장 조사 원장의 cutoff·SHA·release/PID를 따로 고정한다. 첫 Kiwoom 요청 흐름 수정 전에 [공식 참조 gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)에 따라 당일 upstream SHA, `kiwoom_docs`, specs/core/Postman의 해당 TR·continuation·거래소 필드를 확인해 기록한다. 실제 API나 주문을 테스트용으로 호출하지 않는다.
2. **코드·테스트.** 기존 monitoring producer·탈락 후보 BBO 관측기, 공통 지문 helper, `sniper_sync.py`의 로그를 수정하고 엔진 root 새 모듈을 만들지 않는다. 패널 순서/간격, 네 패널 결과 독립성, 300±60초·세션 경계·240초 BBO 창, deferred/HTTP 429 분리, 재시작·날짜 변경, 정확 수신시각, KRX·NXT 부분/완전 대사의 fixture를 기존 테스트에 추가한다. 요청수/지연/CPU·RSS를 incumbent 0초와 후보 5초 동일 원천으로 재생한다.
3. **검토 gate.** 구현→자체 리뷰→수정→재리뷰를 닫고 영향 pytest·compile·`git diff --check`를 통과시킨다. shared coordinator 5/4 상한, pre-submit·잔고·주문 경로의 요청 등급과 관측 외 사용자에 영향이 없는지 확인한다. 자동화 파일 변경 시 `bash -n`·wrapper 계약 테스트 및 문서 print-only parser를 추가한다.
4. **운영 후보 수용.** 별도로 선택된 불변 release의 source-only 자연 수집으로 최소 하루 전체와 독립적인 다음 거래일의 동일 시간대/시장별 `physical HTTP`, `deferred`, `rate-limit`, 네 패널 포착률, 외부 BBO 결손, 300±60초 cadence, source hash·시각, 정기 잔고 완전 대사를 비교한다. `ka10027` 보류가 같은 모집단에서 감소하고 다른 source-quality/지연·required/critical 조회가 악화되지 않을 때만 후보를 유지한다. 보류 감소의 수치 목표는 baseline 전체 날짜가 닫힌 뒤 고정한다. 후보가 실패하면 0초 incumbent 설정 또는 이전 불변 release로 되돌리고 원천 결손을 보존한다.

코드 통과, 배포 선택, cron 자연 실행, 실제 Main PID 소비, 주문·완료 손익 효과는 서로 다른 영수증이다. 이 source-only 변경의 성공만으로 진입 성능이나 비용 후 순익 개선을 주장하지 않는다. 마지막 남는 확인 항목은 장중 기록이 닫힌 뒤 동일 분모의 자연 비교와 KRX·NXT 완전 대사 영수증이다.

## 5. 구현·리뷰 기록 (2026-09-28)

- 공식 참조 gate: 10:46 KST에 upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`를 가져와 `kiwoom/_data/kiwoom_api_spec.json`의 `ka10004`·`ka10027`·`kt00005`, `kiwoom/specs.py`, `kiwoom/core/client.py`, `postman/kiwoom-openapi.postman_collection.json`의 운영/모의 요청을 확인했다. 이 리비전에 `kiwoom_docs` 디렉터리는 없다. `ka10027`은 `/api/dostk/rkinfo`·거래소 `stex_tp=1/2`와 응답 헤더 `cont-yn`/`next-key`, `ka10004`는 `/api/dostk/mrkcond`·`stk_cd`, `kt00005`는 `/api/dostk/acnt`·`dmst_stex_tp=KRX/NXT`를 확인했다. 요청 본문·응답 파서·연속조회·실/모의 분리·공유 한도는 바꾸지 않았다.
- 구현: `market_opportunity_census` 수집기는 기본 0초·명시 후보 5초의 패널 시작 간격, 60초/세션 경계 우회, 패널별 시작·완료·원 응답시각/호출수/보류/페이지 메타를 남긴다. 외부 BBO와 스캐너 탈락 후보 호가에는 같은 공통 지문 함수를 써서 token·origin·날짜·TR·route·payload·등급·연속조회·페이지·재시도·대기·timeout 조건을 해시로 남긴다. `ka10027`의 반환 행 제한도 지문에 포함한다. 지문은 **호출자 조건**이며 인증 재시도나 연속 페이지별 실제 wire 요청 증거가 아니다. 성공 응답 캐시와 주문·실행 입력 재사용은 추가하지 않았다.
- 잔고: read-only refresh와 정기 대사의 로그가 `required_exchanges`, `successful_exchanges`, `inventory_complete`, 시작·완료시각을 각각 남긴다. 미체결 확인은 독립 필드다. 리뷰에서 첫 `kt00005` 실패 뒤 재조회가 양 거래소 모두 성공해도 무조건 대사를 건너뛰던 경로를 발견하여, **재조회 성공 시에만** 기존 KRX+NXT 완전성 차단과 후속 대사를 계속하도록 고쳤다. 조회 예외는 초기/재조회 각각 실패 영수증을 남기며 custody를 변경하지 않는다. 차단·DB 실패와 정상 대사 완료는 별도 로그다.
- 고정 입력 재생: 10:35 KST 이전 `data/market_opportunity_census/market_opportunity_census_2026-09-28.jsonl` 선택 100행·31주기, 선택 원문 SHA-256 `c1163770b2c5055b7e555e879c0d18a127934498612fbe2d7e0290f122ffffee`. BBO 없이 기존 `read_rate_control_waited_sec`를 고정 소요시간으로 사용한 가짜 fetch 재생에서 0초와 5초 모두 100호출, 마지막 패널 가상 지연 p95 3.654→15.926초, 최대 4.617→16.130초였다. 한 재생의 가짜 sleeper 벽시계 6.15→5.94ms, CPU 6.15→5.89ms, 최대 RSS 144,352KB였다. 이는 broker 경합·HTTP 429 감소나 BBO 포함 실제 60초 달성을 예측하지 않는다.
- 리뷰/검증: 첫 전체 영향 테스트에서 기존 BBO 테스트가 주입 시계의 추가 호출로 6건 실패했다. 계측 시계를 분리하고 기본 0초에서 기존 단조시계 호출을 유지한 뒤 같은 범위를 재실행했다. 짧게 깨어난 sleeper에서도 5초 최소 간격을 다시 확인한다. 추가 리뷰에서 token 의존 지문이 정규화 시장 원천 hash를 바꾸지 않도록 지문만 hash 대상에서 제외했다. 배포 전 재리뷰에서 서로 다른 반환 행 제한이 같은 요청 지문을 만들던 결함을 발견해 제한값과 회귀 테스트를 추가했다. 최종 영향 `pytest` **283 passed**, Python compile·`git diff --check` 통과, 문서 print-only parser **32건** 정상 파싱을 확인했다. 자연 수집 릴리스·PID·실제 중복/재사용 절감·종일 9/28 분모·비용 후 손익은 아직 영수증이 없다.
