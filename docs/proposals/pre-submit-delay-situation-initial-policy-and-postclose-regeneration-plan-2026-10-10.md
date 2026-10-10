# Pre-submit delay 상황별 초기정책·장후 재생성 상세 개선계획

작성일: 2026-10-10 KST. 상태: 공통 코드 구현·반복 리뷰 및 승인된 코드 배포를 완료했다. **전체 계획 수용은 미완료**이며 `PreSubmitDelaySituationImplementation1010`를 OPEN으로 유지한다. 전수 원천 연결·상한 초과 분할·전체 연구 성능과 S6 신규 정책 발행/장후 재생성은 남아 있다. 아래 기존 문서 검증 기록은 작성 당시 이력이며 현행 코드·배포 근거는 후속 기록을 따른다.

후속 승인 배포(10/10): 검증된 공통 코드와 부모 동등 초기 구성은 `main-trailing-delay-20261010-v1` / `d61b36b00696865ca9dd13a466d8544a886e2e28`로 배포했다. 10/12 PREOPEN 전체 계약·예약경로·최종화 세대는 PASS다. 신규 제출 지연 v2 정책 발행 및 전수 연구/대용량/전체 연구 성능 수용은 OPEN이며 상세 상태는 [후속 리뷰·배포 기록](../audits/main-all-scope-trailing-and-pre-submit-delay-implementation-review-2026-10-10.md)을 따른다.

계획 기록 owner: [10/10 checklist](../checklists/2026-10-10-stage2-todo-checklist.md)의 `PreSubmitDelayInitialPolicyPlan1010`.
후속 리뷰: 장중 지연·공유 queue·정책 로딩·장후 스캔/캐시·성능 적용 기준을 보완했다. 성능 수치는 구현 단계에서 측정하며 이번 문서는 측정 결과가 아니다.

현재 v2 원천 구현은 원 record identity를 검증한 뒤 필요한 필드와 full-field conflict SHA만 보관한다. scan-job 2GiB/record 64KiB의 상한과 두 family가 함께 쓰는 resident-data 64MiB budget을 적용한다. 이는 2GiB 전체 decode나 자동 저장 확대가 아니다. 최종 기회/index/artifact 상한을 넘는 전역 census·split·발행은 아직 OPEN이며 legacy v1 상한을 무단 확대하지 않는다. 격리 실자료 계산·원천/consumer 세대 재사용과 실제 성능 수치는 연결된 구현 리뷰를 현재 근거로 사용한다.

## 1. 목표와 완료 산출물

검증된 Main `ENTER_NOW + PASS` 기회와 그 후행 가격을 활용해 **상황별 첫 BUY 제출 지연 초기정책을 기존 장후 작업에서 생성하고, 다음 영업일 PREOPEN loader가 읽을 수 있게 한다.** 제출·체결하지 않은 기회도 가격 분석 모집단에 포함한다. 최종 목적은 진입 시점 개선이며, 초기정책 근거는 실제 체결·순익과 구별되는 호가 비교 추정치다.

초기정책은 `0/30/60/120/180초` 중 지원되는 값을 선택한다. 학습한 양수 지연이 없으면 검증 결과와 지원 범위를 표시한 0초 초기 baseline을 발행할 수 있다. **양수 지연을 만들기 위해 결손을 채우거나, 0초를 실증된 최적값으로 포장하지 않는다.** 전체 원천이 검증되지 않거나 유효 비교가 전혀 없으면 정책 생성은 `blocked`이며 기존 즉시 제출 동작을 유지한다.

후속 구현·재생성의 완료 산출물은 다음과 같다.

1. 동결 원천 manifest와 전체 PASS→관측→가격 pair의 분모 대사표.
2. 원천 자격을 먼저 확정한 시간순 학습·검증 및 상황별 비교 보고서.
3. `pre_submit_delay_policy_v2` 초기정책: 학습 선정/0초 baseline/미지원 fallback을 구분한 cell, 원천·알고리즘·부모 정책 hash, 적용일, loader 계약.
4. 같은 장후 generation의 stage→runtime summary→tower/checklist→strict verifier→controller/finalization 수용.
5. 적용일 PREOPEN의 v2 정책 검증과 격리 제출 경로 검사. 실제 예약기동 PID 소비·자연 제출·체결·순익은 별도 후속 영수증이다.

[10/2 계획](pre-submit-delay-price-pattern-calculation-remediation-plan-2026-10-02.md)은 호가 비교를 report-only로 구현했다. 본 계획은 그 다음 단계인 전체 PASS 모집단과 초기정책 발행·소비 계약을 설계한다. [10/10 PASS 처리 지연 계획](main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md)은 결과 전달·저장·인수 지연의 수리이며, 그 원 5초 deadline과 주문 안전 계약을 유지한다. 현재 문서 작업은 코드 변경·장후 재실행·정책 선택·서비스 재기동을 실행하지 않는다.

## 2. 확인한 현재 상태와 개선 항목

근거는 [10/8 보고서](../../data/report/pre_submit_delay_tuning/pre_submit_delay_tuning_2026-10-08.json), [정책](../../data/threshold_cycle/pre_submit_delay_policy/pre_submit_delay_policy_2026-10-08.json), [summary](../../data/report/runtime_approval_summary/runtime_approval_summary_2026-10-08.json), [현재 생산자](../../src/engine/scalping/pre_submit_delay_tuning.py)다. 10/10 점검에서 report/policy/summary hash, family ledger와 선택 릴리스의 영향 코드 5개 일치를 확인했고, 관련 회귀 56개가 통과했다. 이는 이번 신규 설계의 구현 검증 수치가 아니다.

| ID | 현재 근거 | 구현할 개선 |
| --- | --- | --- |
| D1 | 누적 commit 31건, 적격 29건. 10/8 당일 delay ledger는 `valid_empty`, 공통 ID 0건 | PASS 전체를 원 기회로 등록하고 제출 준비 전 종료도 관측한다. 당일과 누적 수를 별도 표시한다. |
| D2 | 관측 등록이 `_submit_watching_triggered_entry`의 주문가·수량 준비 뒤에 있음 | PASS 확정 기준과 주문 준비 기준의 시계를 각각 보존한다. 관측은 수량/주문 발생에 종속시키지 않는다. |
| D3 | 적격 29건 중 유효 P0 6건, 30초 6쌍·60/120/180초 각 5쌍. 9/29 21건은 유효 P0 0 | P0 원천 자격을 먼저 판정한 뒤 분할한다. 결손 행은 원천 분모에 남기고 비교 학습에서는 격리한다. |
| D4 | KRX의 `5_TO_10BP` 10기회 및 `GE_10BP` 15기회 모두 common learning pair 0 | 유효 기회가 검증 구간에만 몰려 학습이 비는 구조를 수정한다. 미래 가격을 보고 split을 조절하지 않는다. |
| D5 | 10/7 2건은 `auxiliary_effective_action=UNKNOWN`으로 제외 | 같은 시도의 검증된 보조 응답/최종 판정 영수증을 연결한다. 근거 없는 PASS 복원은 금지한다. |
| D6 | type은 venue/session/tick band. spread는 진단, 유동성·변동성은 UNKNOWN | 기존 기계 branch/phase와 보조 위험 근거, 판정 당시 호가 여건을 계층적으로 사용한다. |
| D7 | `build_report`는 후보 EV=null, passed=false, 선택=null을 고정 작성 | 초기 가격 시점 정책 생성기를 구현하고 v2 전용 validator/publisher/loader로 소비한다. v1 경제성 검증기에 가짜 EV를 넣지 않는다. |
| D8 | 기존 v1 loader/bootstrap은 양수 지연과 비용모형 검증만 허용 | v2의 0초/양수/미지원 cell과 초기정책 근거를 동일 계약으로 검증한다. |
| D9 | 양수 지연은 원 PASS의 유효시간보다 길 수 있음 | due 시 기존 재평가에서 얻은 현재 증빙으로 제출한다. 원 응답의 TTL 연장·늦은 재사용을 차단한다. |
| D10 | 제출 함수가 `load_runtime_policy`를 호출하고 enabled loader는 policy/report를 읽어 hash·전체 branch를 검증 | PREOPEN/기존 준비 경로에서 한 번 검증해 불변 lookup으로 설치한다. 장중 선택은 메모리 조회만 한다. |
| D11 | `observe_pre_submit_delay_quote`가 호가 전체를 JSON/hash하고 `_log_entry_pipeline`을 호출. Main은 due 종목의 WS snapshot도 별도로 얻음 | 같은 snapshot의 복사·hash를 재사용하고 작은 관측 envelope만 기존 executor로 넘긴다. 주문 필수 저장과 관측 접수는 분리한다. |
| D12 | 공유 `BoundedObservationQueue`는 1 worker·1,024 items·4MiB·item 64KiB이며 접수도 JSON 크기 계산을 수행 | 전체 PASS 확대가 기존 scanner 관측을 밀어내지 않게 category별 접수 예산·실제 retained bytes·drain 공정성을 함께 제한한다. |
| D13 | `seal_family_source_ledger → family_source_ledger_issues → build_report`에서 `_source_rows`가 반복 호출됨. report도 검증 직후 같은 compact를 다시 decode | 원천 snapshot/index 한 번 검증 후 같은 run에서 재사용하고 각 소비 경계의 세대 검증은 유지한다. |
| D14 | `_existing_quote_census`는 별도 partition 조회·raw tail 최대 64MiB·cache 쓰기를 수행하며 pair 선정 입력이 아님 | exact BBO projection과 구분한 선택적 운영 진단으로 읽기 예산을 배정한다. 정책 계산이 별도 raw 진단 반복에 종속되지 않게 한다. |
| D15 | `pre_submit_delay_source_semantics`는 raw cursor를 재사용하지만 compact는 호출마다 당일 최대 8MiB 재탐색/decode | compact도 세대/완결 offset cursor를 쓰고 변경분만 대사한다. backlog와 결손·관측 회복을 구별한다. |
| D16 | `kiwoom_sniper_v2`의 async scheduler 범위는 WATCHING이며 pre-submit retry는 기존 별도 owner로 명시됨 | due successor가 이미 지원된다고 가정하지 않는다. WATCHING 평가 owner와의 명시적 재점검 인계·native claim 종료/접수·부하 계약을 S3에서 구현한다. |

현재 데이터에서 양수 지연이 선정될지는 재생 전 확정할 수 없다. integrated aftermarket의 기존 유형은 학습 1쌍·검증 1쌍에서 `no_price_difference`였다. 기존 6기회를 최대 24개 독립 기회로 늘려 세지 않는다. 10/2 문서의 자연 분석 `not_observed`는 현재 `partial` 산출 확인으로 갱신하며, 자동 정책 미선정 상태는 그대로 기록한다.

## 3. 모집단·기준 시각·기회 신원

### 3.1 두 시계와 세 모집단

| 모집단/시계 | 정의 | 용도 |
| --- | --- | --- |
| `signal_ready` | 원 기계 `ENTER_NOW`와 그 시도에 대한 보조의 **유효 PASS 확정 시각**. 물리 응답·필수 저장·Main 인수 시각도 별도 보존 | 전체 PASS 기회 census와 이후 가격·처리 지연 분석 |
| `price_ready` | 기존 `decision_committed_at_epoch`, 주문가·수량 계획이 준비된 시각 | 보유 원천의 즉시/지연 비교와 초기정책의 실제 제출 대기 기준 |
| 실제 주문/체결 | 실제 API 시작·응답·fill·종료 원장 | 실행 품질·실현손익 관측, 위 두 모집단의 진입 조건으로 쓰지 않음 |

첫 v2 정책의 실행 시간축은 `price_ready`로 고정한다. 기존 원천으로 이 초기정책을 재계산할 수 있다. `signal_ready` 기반 비교는 전체 PASS로 확대해 별도 산출하고, 그 기준의 정책은 해당 기준 P0/Pd가 확보됐을 때 **별도 anchor cell**로 선정한다. 두 기준의 30초를 같은 비교군으로 합치거나 `price_ready` 호가를 과거 PASS 시점의 P0로 소급하지 않는다. 정책에 `anchor_kind`를 필수로 넣고 초기 발행에서는 `price_ready` 하나만 실행 지원한다.

주요 모집단은 `main_scalping + ENTER_NOW + effective PASS`다. 기존 CAUTION은 분석에서 보존하되 PASS와 다른 strata로 표시한다. 현재 기계/보조의 합성 결과가 CAUTION을 WAIT로 처리하면 초기 실행 cell을 만들지 않는다. VETO/BLOCK/RECHECK, 퇴역 owner, manual/scale-in은 이 초기 진입 정책에 섞지 않는다. `planned_qty`는 `signal_ready` 가격 분석의 필수 조건이 아니며, 실제 대기 intent를 만드는 시점에는 기존 가격·수량 owner가 확정한 값이 필요하다.

기회 key는 `source_date + symbol + owner + original_machine_observation_sha256 + native evaluation/response identity + policy bundle`로 만들고, 기존 `delay_intent_id`·`entry_submit_attempt_id`는 별도 연결한다. 같은 신호의 재시도는 보존된 원 signal/opportunity identity로 묶는다. primary branch만 같은 독립 시도를 합치지 않는다. 연결이 증명되지 않은 retry는 raw census에는 남기고 독립 학습·검증에서 제외한다.

### 3.2 보조판정 UNKNOWN 처리

신규 writer는 최종 유효 보조판정과 그 source schema/hash를 scalar로 함께 보존한다. v1/v2 응답의 canonical effective verdict 변환은 기존 보조 owner의 검증 함수를 재사용한다. raw PASS가 최종 유효 PASS인지 별도 확인하며, `entry_ai_screen_pass`, 문자열 JSON, dict 표현을 임의 우선순위로 덮어쓰지 않는다.

과거 10/7 두 건은 exact attempt·machine hash·response/판정 hash가 일치하는 영수증이 있을 때만 **새 projection에** 복원한다. historical commit/quote bytes, event ID, 봉인 source hash는 바꾸지 않는다. 근거가 없으면 `auxiliary_verdict_unresolved` 2건을 유지하고 다른 유효 기회 계산을 계속한다.

## 4. 원천 재사용·역사 재계산·장중 수집

### 4.1 원천 등급과 사용 방법

| 원천 | 역사 재사용 조건 | 계산 권한 |
| --- | --- | --- |
| 전용 `family=pre_submit_delay` commit/quote | 기존 family ledger와 event hash, 같은 intent P0/Pd | 현재 `price_ready` 비교의 우선 입력 |
| AI request/payload/trace·기계 원 관측 | exact attempt/hash로 현재 시점 특징·effective PASS·원 시각 확인 | `signal_ready` 기회 등록과 상황 특징 복원 |
| 보존된 정확 시각의 BBO/0D snapshot | 동일 symbol·세션 경로, 관측 clock·원천 generation·freshness 검증, 정해진 horizon 오차 | 대응하는 anchor의 P0/Pd로 사용 가능. 종목·근접 시각만으로 다른 기회를 합치지 않음 |
| 기존 1/3/5/10/20/30/60분 후행 bar/label | 동일 판정 identity와 완료된 관측창·가격 의미 검증 | 신호 지속·상승/하락 후행 진단. 없는 30초 ask나 체결 가격의 대체 입력으로 사용하지 않음 |
| 실제 submit/fill/terminal/cost | 원 주문·부모·부분체결·비용 원장과 exact join | 실행 및 경제성 검증. 가격 비교 표본의 추가 필수 조건이 아님 |

S0는 파일 목록·크기·schema·기존 index를 먼저 읽는다. 당일 거대 raw를 기회마다 재조회하지 않고, 필요한 원천을 승인된 자원 예산 안에서 **한 번** 읽어 identity→필드 projection을 만든다. 기존 bounded index가 해당 창을 덮지 못하면 partial 범위를 명시한다. raw 전체 무제한 scan, 현시세 REST 조회로 과거 호가 backfill, 과거 원장의 in-place 수정은 하지 않는다.

재계산 원천 구간은 `2026-09-29`부터 고정 source date까지다. 현재 실행 예시는 `source_date=2026-10-08`, `publication_date=실제 재생일`, `effective_from=그 다음 적격 거래일`이며 10/10 실행이면 10/12다. 실제 실행이 늦어지면 적용일을 재계산하고 과거 적용일에 소급하지 않는다. 오래된 machine/aux 정책의 의사결정은 그 당시 hash를 유지한다. 서로 다른 정책 세대를 동일 기회나 무표시 공통 최적화 모집단으로 합치지 않는다.

### 4.2 봉인과 중복 방지

기존 raw/compact 공통 ID 원장은 전용 이벤트의 소유자로 유지한다. v2는 별도 연결 manifest에 **원 경로·원 ID·원 hash·원 날짜·projection version·anchor kind**를 기록한다. 복원된 기회를 runtime commit으로 합성하지 않는다. 기존 commit과 같은 기회가 다른 입력에서도 발견되면 우선순위에 따라 한 번만 사용하고 alias를 남긴다. raw/compact 수가 다르면 공통 ID를 계산 분모로 쓰며, 차이 수·격리 ID는 진단으로 남긴다. 단순히 앞에서 `min(count)`개를 잘라 다른 이벤트를 짝짓지 않는다.

경로는 세션 규칙으로 정한다: 프리마켓 `NXT_ONLY`, 정규·통합 애프터 `KRX_NXT_INTEGRATED`. venue나 route 메타데이터가 비었다는 이유만으로 기회를 제외하지 않는다. 명시 annotation과 기대 route는 진단으로 보존한다. 실제 BBO가 다른 feed이거나 source clock/가격/epoch가 충돌한 경우는 해당 quote/pair의 물리 원천 품질로 분리한다. 두 호가 모두 경로·clock·hash가 있어야 하고 reconnect를 가로지르는 비교는 초기 v2에서 지원하지 않는다. 이는 venue 기반 분류 결손과 다른 판정이다.

### 4.3 전향적 관측과 의미감시

- 기존 PASS 완료 영수증 owner에서 scalar 신원·확정 시각을 동결하고 기존 Main/WS 관측 경로가 기회를 받는다. Main 인수 지연이 원 PASS 시각을 바꾸지 않게 한다. 당시 snapshot이 없으면 P0 missing으로 남긴다.
- 관측 상태는 broker intent와 분리하고 `opportunity_id`별로 관리한다. 동일 종목의 새 PASS가 이전 기회의 180초 관측을 덮어쓰지 않게 한다. 제출 실패/미체결/guard 종료 뒤에도 기존 WS 입력으로 정해진 horizon을 관측한다.
- watch 제거·WS 구독 종료·프로세스 종료는 명시적 observation terminal이다. 이를 피하려고 watch cap을 늘리거나 새 구독·worker·API polling을 만들지 않는다. 필요한 snapshot이 없어지면 해당 이후 horizon만 censored다.
- 고정 5개 horizon, 최대 lifetime `180초 + 기존 3초 허용오차`, 동시 기회 수·bytes 상한을 둔다. 상한은 S0의 기존 관측 executor/관측량을 근거로 정하고 포화는 source gap으로 기록한다. 새 worker 없이 기존 owner에서 bounded하게 처리한다.
- 기존 5분 의미감시가 `PASS 확정 → 기회 등록 → P0 → due Pd → 원천 봉인 → 정책 consumer`를 대사한다. 각 상태는 같은 관측창·기회 ID 기준이며 미래 horizon은 `not_due`, 관측 종료는 censored, 원천 미도착은 missing이다.
- 경보는 종목·세션·원 attempt·직접 reason과 수를 포함한다. 당일 등록 0과 이전 누적 유효 pair를 함께 보여줘 과거 분석 성공이 당일 source 단절을 가리지 않게 한다. 감시 회복은 같은 종류의 새 정상 영수증으로만 확인한다.

### 4.4 장중 비용을 제한하는 구현 계약

관측 대상 확대 전에 아래 경계를 구현한다. [기존 단일 관측 queue](../../src/utils/pipeline_event_logger.py)의 전역 상한을 키우거나 별도 executor를 만들지 않는다.

1. **등록은 원 PASS마다 한 번:** 완료 owner가 이미 가진 신원·시각·기계/보조 특징의 작은 scalar envelope를 동결한다. 원문 payload·mutable stock·전체 WS 객체를 queue에 넣지 않는다. 필수 응답 저장/ready 게시/claim을 관측 저장 완료까지 기다리게 하지 않는다. enqueue와 raw append, compact append 성공을 각각 기록한다. `_log_pre_submit_delay_event`의 예외 없음만으로 저장 성공을 간주하는 기존 bool은 새 관측 완료 영수증으로 재사용하지 않는다.
2. **기회 수와 snapshot 수를 구분:** 두 anchor의 같은 물리 호가는 `(symbol, expected_route, transport_epoch, native snapshot generation)`로 공유할 수 있다. 각 anchor의 시각/유효성/pair는 독립이다. fresh source identity가 같은 경우에만 복사·canonical hash를 한 번 수행하고 기회는 참조한다. 객체 주소나 가격 동일만으로 재사용하지 않는다. 큐를 통과할 때 동일 book을 기회마다 재직렬화하지 않게 bounded 불변 snapshot과 참조 lifetime을 연결하며, 각 기회/horizon의 raw·compact 영수증은 빠짐없이 별도로 기록한다. 마지막 소비/실패 때 참조를 해제한다. v1 digest 의미는 보존하고 v2 hash 계약을 명시하며 근거 필드를 잘라 같은 hash라고 표시하지 않는다.
3. **due 작업만 처리:** 기존 Main 관측 지점에서 가장 이른 due를 O(1) 확인하고 해당 symbol의 due 기회만 처리한다. 전 기회를 매 tick 정렬하거나 순회하지 않는다. 기존 loop의 due index를 재사용하거나 동일 owner 안에서 heap+identity map을 둔다. 등록/진척은 O(log A), due 처리 D건은 O(D log A)이며 A는 제한된 active 기회 수다. tombstone·dedup·종료 map·공유 snapshot도 개수/bytes 제한과 종료 시 참조 해제를 가진다. live 기회를 덮어써 메모리를 맞추지 않는다.
4. **한 번 받은 WS를 재사용:** 같은 Main turn에서 이미 받은 정확 0D snapshot이 있으면 재사용한다. WS lock 안에서는 필요한 bounded 불변 값을 확보하는 작업만 하며 JSON/hash/파일 기록/통계는 밖에서 한다. 지연 관측만을 위한 중복 `get_latest_data`, 새로운 callback 전체 종목 순회, REST 요청을 추가하지 않는다. 비동기 worker가 나중의 WS를 다시 읽어 원 P0를 대체해서도 안 된다.
5. **공유 queue 접수 보호:** delay 관측에 별도 category quota를 두되 전체는 기존 1,024 items/4MiB/item 64KiB 이하다. S0에서 실제 envelope 크기·active/anchor 수·동시 due burst·기존 scanner 수요를 측정해 category items/bytes, 회차당 due 수/CPU 시간 예산과 기존 작업 reserve를 고정한다. 수치 미정인 상태로 S1 확대를 완료하지 않는다. queue 객체, snapshot cache, pending/heap까지 합친 peak retained memory도 별도 상한을 둔다. drain은 실행 중 callback 포함 회차별 budget으로 기존 executor에 양보하며 공유 FIFO의 불필요한 순서 변경은 하지 않는다. 단일 callback의 blocking fsync를 budget이 중단할 수 있다고 가정하지 않는다. 다음 callback 이전에 양보하고 reschedule/close/실패 경합에서 drain owner는 하나만 유지한다. 필수 append/fsync를 잘라서 시간을 맞추지 않는다.
6. **포화와 늦은 관측:** capacity 전에 접수를 거절하고 신원/원 시각·사유를 bounded health counter 및 가능한 영수증에 남긴다. 관측 queue 실패 시 Main 동기 append·무한 retry·sleep을 하지 않는다. 3초 관측 오차를 넘긴 horizon은 현재 호가로 여러 과거 horizon을 채우지 않고 `observation_budget_exceeded` 또는 `horizon_late`로 종료한다. 대량 만료도 회차별로 처리하고 counters/examples 수를 제한한다. 정상/설계 burst 부하의 추가 유실은 성능 수용 실패이며, 과부하의 명시적 거절은 성공 coverage로 계산하지 않는다.
7. **제출 권한과 분리:** committed/quote 같은 분석 기록을 비동기화해도 native request·필수 response·영속 주문 intent·broker terminal의 저장 계약은 유지한다. 이미 선택한 양수 지연의 pending 제어를 만들 수 없으면 해당 기회를 직접 사유로 종료하며 즉시 제출로 임의 전환하지 않는다. 관측 전용 실패 자체가 기존 0초 제출의 새 차단 조건이 되지도 않는다.

### 4.5 장후 단일 원천 읽기·재사용·감시

- S0의 `SourceSnapshot`은 기존 family owner 내부의 계산 context다. 원천 경로/representation, 고정 cutoff·inventory hash, ledger hash, schema/정규화/특징/알고리즘 버전, exact-ID index를 가진다. `seal/verify/report`가 같은 context를 소비하도록 인자를 연결하고 함수마다 전체 `_source_rows`를 재호출하지 않는다. 독립 프로세스의 verifier는 producer 메모리를 신뢰하지 않고 봉인 manifest와 artifact bytes를 다시 검증한다.
- 첫 decode에서 content hash·identity 검증·필드 projection·유형 index를 함께 만든다. 원문 dict 전체와 동일 내용의 여러 사본을 유지하지 않는다. 기회 정렬·partition은 한 번 수행하고 parent/child에 index를 전달한다. 유형은 실제 관측된 key만 생성하며 branch 부분집합의 모든 조합을 열거하지 않는다. horizon은 고정 5개, fallback 깊이는 고정이며 기회별 hash/특징을 cell마다 재계산하지 않는다.
- raw/compact/AI trace 각각 읽은 bytes·JSON decode 수·full pass 수·cache hit/miss·재검증 bytes를 따로 센다. 같은 run의 같은 입력 generation은 한 번 decode한다. process 간 재사용은 versioned bounded projection으로 연결하며 필수 byte/hash 확인 비용은 별도로 공개한다. 64MiB는 현행 **누적 전용 compact decode 상한**이며 압축 파일 크기나 파일당 상한으로 바꾸지 않는다. 추가 AI 입력·projection·row/item·파일 개수·전체 RSS/temp bytes도 S0에서 별도 합계 상한을 고정한다.
- cache key는 source inventory/content/ledger hash, source cutoff·date, anchor, schema/feature/algorithm/split/mapping version, parent compatibility를 포함한다. 가격 pair projection과 selection 결과 cache를 나눠 적용일·선정 계약 변경이 원천 재스캔까지 유발하지 않게 한다. mutable 원천의 inode/mtime/size만으로 내용 동일성을 인증하지 않는다. 독립 검증이 없는 가변 파일은 한 번 읽어 hash를 확인한다.
- append·late partition·rotation·축소·같은 크기 교체·verdict 복원·부모/알고리즘 변경은 영향 projection을 무효화한다. 불변으로 봉인된 변경 없는 partition은 재사용한다. 날짜 추가로 70/30 경계가 이동하면 cached pair를 재사용하되 전체 대상 partition/선정은 다시 계산한다. 옛 train/validation label을 그대로 이어 붙이지 않는다. 손상 cache는 제한된 1회 재구축, 필수 원천 손상은 source gap이다.
- `_existing_quote_census`는 별도 진단 budget/cache를 사용하고 exact-ID BBO 원천을 대체하지 않는다. 생략/예산 소진이면 `not_evaluated_diagnostic`와 coverage를 남긴다. source-valid pair·family ledger 검증을 생략하거나 진단 0을 실제 무체결로 표시하지 않는다. dry-run의 모든 cache write는 명시한 task root로 제한한다.
- 5분 감시의 compact cursor는 path/device/inode/검증된 완결 offset·prefix generation을 저장한다. writer의 append-only generation 계약이 확인된 prefix만 건너뛰며, 같은 크기 rewrite 등 세대 변경을 검출할 수 없는 원천은 stat 값만 믿지 않고 bounded 재검증/미확정으로 처리한다. 행/byte/time budget 안에서 변경분을 처리하고 incomplete tail은 다음 회차로 남긴다. rotation/reset은 이전 window coverage를 무효화해 `catching_up/unobservable`로 표시한다. 서로 다른 watermark를 비교해 count mismatch를 만들지 않는다. queue 저장 유예 뒤 같은 event-time window만 비교하고, writer health와 실제 append 결손을 같이 확인한다. `not_due/catching_up`는 정상 회복 증거가 아니다.
- 검사 비용 절감을 위해 source/identity/hash 검증을 없애거나 샘플을 줄이지 않는다. source 규모가 상한을 넘으면 정확한 지원 범위와 미처리량을 남긴다. 최근 tail만 읽고 전체 기간 검증 성공으로 게시하지 않는다.

전체 scope와 향후 대용량 지원은 [보유청산 계획의 범위 계약](main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md#3-전체-종목시장-범위-계약) 및 [합산 예산·분할 재개 계약](main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md#103-계층-cache와-두-계획의-합산-자원)을 함께 따른다. 삼성/비삼성·고정 감시/scanner·모든 지원 세션의 PASS를 코드 whitelist 없이 처리하고, universe enumeration은 세대 변경에서 한 번 수행한다. 거래 불가·현재 비운영·무기회·무관측을 구분하며 기존 entry 허용 범위는 유지한다. 64MiB를 넘는 전체 범위 지원에는 bounded partition 작업과 전역 분모·완료 검증을 함께 구현해야 하며 상한만 올리거나 미처리 scope를 지워 완료하지 않는다.

Kiwoom request/response/FID/REG/REMOVE/recovery 수정이 필요하면 구현 전에 [공식 API reference gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 수행하고 upstream SHA·경로·조회 시각을 기록한다. 원천 projection/기존 snapshot 소비만으로 해결되는 부분은 wire 변경을 추가하지 않는다.

## 5. 가격 비교·분할·상황별 초기 선정

### 5.1 원천 자격을 분할 전에 확정

1. 전체 PASS census를 동결하고 원천 identity·유효 P0·anchor·판정 당시 특징을 검증한다. P0 미관측/무효 행은 이유와 raw 분모를 보존하되 비교 학습 split에는 넣지 않는다.
2. **P0 유효 여부와 당시 입력만으로** 기준 모집단을 고정한다. Pd의 등락·최저가·나중의 체결 여부·검증 결과는 모집단 선정에 쓰지 않는다.
3. 같은 anchor·세션·정책 호환 집합에서 `anchor_at, canonical opportunity_id` 순 정렬한 앞 70%/뒤 30%를 기본 학습/검증으로 한다. n≥2에서 양쪽 최소 1개, n=1은 계산만 가능하다. parent와 child는 같은 partition을 상속하며 유형마다 다시 쪼개지 않는다. 일수·실체결 수·10 terminal/3 holdout 거래수 gate를 초기 가격 정책에 추가하지 않는다.
4. 학습 기회의 관측 구간이 검증 시작에 닿으면 purge한다. 관측 종료는 **가장 늦게 존재하는 quote가 아니라 후보 비교의 예정 horizon 끝**으로 정해 결손 때문에 overlap이 사라진 것으로 처리하지 않는다. 이 purge 규칙도 검증 가격을 보기 전에 고정한다.
5. 후보별 기초 통계는 해당 P0/Pd pair로 계산한다. 후보 grid는 30/60/120/180초이며 학습 유효 pair가 0인 horizon만 `unsupported`로 제외한다. 나머지 후보는 공통으로 관측된 같은 학습 기회에서 비교한다. 공통 집합이 비면 `insufficient_comparable_pairs`로 선정만 유보하고 각 horizon의 유효 계산은 남긴다. 검증 결손이나 개선값을 보고 후보 목록·분할·비교 집합을 바꾸지 않는다. 관측 구간 purge는 원 grid의 최대 180초와 허용오차를 기준으로 먼저 고정해 후보 지원 여부와 순환하지 않게 한다.
6. 비교 집합 수·분모·제외·예정 horizon·purge·source/partition hash를 보고서에 봉인한다. 전체 raw, anchor 유효, train, validation, purge, retry 제외, horizon missing 수의 보존식을 검사한다.

### 5.2 선정 목적과 초기정책 조건

기회별 `improvement_bp(d) = (ask_0 - ask_d) / ask_0 × 10000`을 계산하고 평균·중앙값·p10/p90·개선/악화/동일률·pair coverage를 산출한다. 이 값은 호가 가격 개선이며 체결/순익/실행 가능한 전량 fill로 명명하지 않는다. 실제 비용·손익은 해당 원천이 있는 별도 부록에 남긴다.

학습 공통 집합에서 평균 개선이 가장 큰 지연 하나를 고정한다. 동률은 더 짧은 지연이다. 고정 지연의 별도 검증에서 방향과 tail·coverage를 확인하고 결과를 아래대로 결정한다. 초기 버전은 기존 가격 알고리즘을 확장하며 수십 개 경계값/모델을 탐색하지 않는다.

| 결과 | v2 cell 값·근거 |
| --- | --- |
| 학습·검증의 같은 후보가 모두 평균 개선 >0, 각 split 유효 독립 pair 존재 | 해당 지연, `selection_basis=paired_quote_initial`, `evidence_grade=estimated_provisional` |
| 고정 비교 후보가 학습·검증 모두 악화 또는 가격 차이 없음 | 0초, `selection_basis=paired_quote_immediate`와 비교한 지연을 기록 |
| 학습 양수이나 관측된 검증 평균이 0 이하, 또는 학습 비양수이나 검증 양수 | 해당 cell은 기존 동작 0초, `selection_basis=incumbent_on_unconfirmed_pattern`; 차순위 재선정·parent 양수 덮어쓰기 금지 |
| 공통 학습·독립 검증 부족, 검증 pair 결손, 세부 유형 미지원 | 해당 child는 `unsupported`; 지원된 같은 세션·같은 anchor의 상위 cell을 사용하고 fallback 경로를 기록 |
| 상위 cell도 미지원 | `default_delay_sec=0`, `selection_basis=unsupported_existing_behavior`; 학습 성공으로 집계하지 않음 |

초기정책 발행에는 실행 지원 anchor인 `price_ready`의 적격 기회에서 최소 한 개의 유효 P0/Pd 비교가 있어야 한다. 이는 가격 계산의 원천 조건이다. 양수 지연 선정에는 별도의 비중복 학습·검증 pair가 각각 필요하며, 단일 pair로 발행할 수 있는 것은 근거 한계를 표시한 0초 baseline이다. 부족한 cell까지 양수 지연으로 채우지 않는다. 모든 선정값이 0이면 `initial_baseline_immediate`, 양수 cell이 있으면 `initial_timing_policy_selected`다. 둘을 모두 `validated_edge`나 비용 후 경제성 성공으로 표시하지 않는다. 초기 cell의 작은 N과 coverage·tail을 그대로 공개한다. 실제 체결·청산·양의 실현 EV를 초기 도입의 추가 승인 gate로 요구하지 않는다.

초기 선정 이후 갱신도 같은 등록 목적·원천 자격·시간순 검증을 사용한다. 이후 실행/비용 모델이 구현되면 별도 `economic_successor` 근거 등급으로 확장하고, 그 검증 결과를 과거 초기정책에 소급하지 않는다.

### 5.3 상황 유형과 fallback

초기 lookup은 `anchor_kind → session → machine_situation → optional execution_context` 순서로 제한한다. venue는 진단값으로 남기고 정책 key에서 제거한다. 시장 route도 이미 세션에서 결정되므로 별도 분기 축으로 늘리지 않는다.

- `machine_situation`: 판정 당시 등록된 machine branch/phase·confirmation recipe를 deterministic mapping으로 사용한다. 회복/반전/지속 등 상위 묶음의 실제 branch 목록과 mapping version은 S0에서 현행 catalog로 확정한다. 명칭을 먼저 정해 없는 원천을 추정하지 않는다.
- 복수 branch union은 보존된 primary가 있을 때 사용하고 없으면 사전 고정 정렬된 matched-branch set을 사용한다. 미래 성과가 가장 좋은 branch 하나를 고르지 않는다. 세부 set은 표본이 부족하면 상위 세션으로 fallback한다.
- 보조는 effective PASS/CAUTION과 원 risk code를 보존한다. 첫 실행 정책은 유효 PASS만 지원한다. PASS 내부의 위험 맥락은 source-known일 때만 세부 설명/비교에 사용하며 별도 AI 재분류 호출을 만들지 않는다.
- `execution_context`: 현재 tick band와 spread, 원 신호 기준가 대비 P0 괴리 중 실제 동결된 값을 사용한다. 첫 초기정책에서 연속값의 임의 cutpoint 탐색은 하지 않는다. 기존 등록 경계가 없는 값은 설명 변수로 먼저 산출한다.
- 특징 UNKNOWN은 상위 fallback이며 기회 자체의 폐기 조건이 아니다. child가 원천·표본 부족으로 미지원이면 parent 선정값/기존 동작으로 fallback한다. child에서 검증된 0초나 방향 불일치에 따른 0초가 있으면 parent의 양수 값을 덮어씌우지 않는다. 다른 세션·다른 anchor cell을 빌리지 않는다. fallback 계층은 학습 전에 고정한다.

## 6. v2 정책·검증·runtime 계약

### 6.1 artifact와 consumer migration

기존 family와 dated 경로를 사용하고 report/policy schema를 v2로 확장한다. v1은 기존 의미로만 읽는다. `price_pattern_analysis`의 report-only 추천을 v1 `validated_edge`로 다시 해석하지 않는다.

| 필드 | v2 계약 |
| --- | --- |
| `policy_kind` / `metric_role` | `initial_paired_quote_timing` / `initial_entry_price_timing_estimate` |
| `decision_authority` | `next_preopen_initial_pre_submit_timing_policy` — 첫 제출 readiness만 조절 |
| `primary_decision_metric` | `mean_paired_price_improvement_bp` |
| `window_policy` | `forward_from_20260929_frozen_opportunity_chronological_validation` |
| `sample_floor` | 가격 계산 유효 pair 1; 학습 선정은 비중복 학습/검증 pair 각 1 이상. 실제 거래 수 조건 없음 |
| `source_quality_gate` | exact opportunity/anchor/P0/Pd/clock/source hash, 비교 집합 및 분모 보존 |
| `cells` | anchor/session/type, delay, 선정근거, train/validation N·coverage·mean·tail, parent/fallback, 원천·특징·알고리즘 hash |
| `default_delay_sec` | 0; 미지원 구간의 기존 동작이며 학습된 최적값과 구분 |
| generation | source/publication/effective date, policy/report/manifest hash, selected release code contract, incumbent CAS |
| forbidden uses | machine/aux action 변경, numeric price/수량/분할/cancel-wait 변경, stale/deadline/order guard 우회, fill/net PnL 주장 |

0초는 v2의 유효 cell 값이다. 전역 양수 scalar를 요구하지 않으며 cell별 지원 범위 밖으로 spill하지 않는다. `runtime_apply_allowed`는 유효한 v2 발행·소비 계약을 만족한 cell에만 true이며 문서나 연구 JSON의 수동 플래그로 열지 않는다. 이전 유효 정책은 원 expiry/carry 계약 안에서만 유지한다. v2 초기 baseline은 명시한 carry 규칙·machine/aux 부모 호환 범위 안에서만 다음 generation으로 승계하며, 명시적 owner 중지·원 expiry·hard guards가 우선한다. 재기동으로 pending 기회는 복원하지 않는다.

동시에 수정할 consumer는 `_validated_candidate`의 schema dispatch, `load_runtime_policy`, bootstrap `_pre_submit_delay_handoff`, stage 입출력 검증, runtime approval summary, 의미감시, checklist/strict 검증이다. source-valid v2가 v1의 model-null 사유로 `not_applicable` 처리되지 않게 한다. 과거 v1 정책/report hash는 재작성하지 않는다.

report+policy+manifest는 기존 family 아래의 불변 generation 경로에 준비하고 각 파일 hash·의미 결속을 검증한다. manifest는 report/policy/source/code를 참조하며 자신을 참조하는 순환 hash를 만들지 않는다. publisher 잠금과 incumbent CAS 아래 **committed generation pointer 하나를 atomic rename**으로 교체한다. 모든 v2 reader는 pointer를 한 번 고정한 뒤 해당 generation 파일만 읽는다. 파일 여러 개를 차례로 rename하고 이를 하나의 원자적 발행이라고 부르지 않는다. 기존 dated discovery 경로는 호환 projection이며 v2 소비의 권위는 committed manifest다. 원 dated v1 bytes는 archive receipt로 보존한다. 이 generation resolver를 모르는 consumer가 남아 있으면 v2를 발행하지 않는다.

실제 구현에서는 [traceability](../report-based-automation-traceability.md)의 family 계약과 [운영 runbook](../time-based-operations-runbook.md)의 정책·감시 의미, 필요한 Plan Rebase 축을 변경된 코드와 함께 의도적으로 갱신한다. 지금은 제안 문서이며 현행 v1 권한이 이미 변경됐다고 보고하지 않는다.

### 6.2 대기와 만료된 PASS의 처리

- 0초 cell은 현재 제출 경로를 그대로 거친다. 양수 cell은 `price_ready`에서 기존 비차단 pending intent에 원 기회·정책 cell·cap·확정 수량·due monotonic을 결속한다. 가격/분할/수량 owner를 새로 만들지 않는다.
- 원 PASS/native request는 그 요청의 기존 deadline 안에서 소비·종료한다. 30~180초 대기를 위해 5초 TTL을 연장하거나 같은 요청을 계속 accepted로 붙잡아 두지 않는다.
- due 때 **기존 Main 재평가 scheduler**에서 현재 기계 판정 및 필요한 보조판정·가격·자금·수량·source를 확인한다. 새 요청은 자체 native claim/TTL을 가지며 원 기회와 successor 관계를 기록한다. delay owner가 별도 provider를 직접 호출하거나 실패한 요청을 무한 재전송하지 않는다.
- 기존 scheduler에 fresh 평가가 없으면 기존 재점검 상태로 처리하고 늦은 주문을 보내지 않는다. 새 PASS까지 연결됐을 때만 기존 제출 함수·최종 guard·영속 주문 intent→adapter로 진행한다. 그때 수량/cap/부모 정책/owner가 달라졌으면 원 delay intent를 취소하고 새 계획을 자동 확대하지 않는다.
- due 이후 재점검의 대기 상한은 현재 공통 entry deadline budget(현행 5초)을 재사용한 `due + budget`이다. 새 native request의 자체 deadline은 그대로 두고 제출은 두 deadline을 모두 만족해야 한다. scheduler 접수 지연도 이 budget에 포함하며 불가하면 `recheck_not_ready_before_expiry`로 종료한다. 목표 due·재평가 완료·실제 API 시작과 추가 지연을 별도 기록하고, Pd 호가 개선을 실제 재평가 후 제출 가격으로 간주하지 않는다.
- due 재평가를 새 delay intent로 다시 arm하여 영구 대기하는 일을 막는다. 한 원 기회에 `armed → due/recheck → submitted 또는 cancelled/expired/uncertain` 한 lifecycle만 허용한다. 같은 종목의 독립 새 신호는 별도 기회다.
- 보유·미체결·manual veto·watch eviction·세션 종료·원 정책 교체·재시작은 직접 사유로 종료한다. 응답 미확정은 주문 재전송 사유가 아니다. retired episode/widget 보유를 Main으로 편입하거나 flat을 기다리지 않는다.

이 runtime 경계의 격리 통합 검증은 양수 정책 발행 전 필수다. 실제 broker 체결 발생은 코드 검증의 전제가 아니다.

### 6.3 정책 lookup·재점검 부하 보호

PREOPEN/기존 runtime 준비 owner가 v2 manifest·report·policy·cell·hash/date를 검증하고 불변 lookup을 설치한다. report 전체와 evidence 배열은 장중 lookup 객체에 보관하지 않는다. [현행 loader](../../src/engine/scalping/pre_submit_delay_tuning.py)의 매 호출 파일 읽기·전체 branch 검증을 이 준비 단계로 이동하며, 장중 selector는 고정 깊이의 cell 조회와 현재 날짜/세션/부모 hash·expiry·veto만 확인한다. 준비 비용·첫 호출·warm 조회를 각각 측정한다.

캐시 key는 검증된 release/policy/manifest generation·부모 호환과 적용일이다. 시간 TTL만으로 정책 정당성을 연장하지 않는다. 새 policy 파일이 나타났다고 Main이 즉석 glob/read/hash/reload하지 않으며, 기존 owner의 승인된 generation 교체에서만 atomic swap한다. 잘못된 신규 generation은 활성화하지 않고 기존 정책도 원 expiry/carry 안에서만 유지한다. 명시된 중지·부모 변경은 기존 owner의 generation invalidation으로 전달한다. 검증 준비가 없는 초기기동은 기존 0초 동작과 source 상태를 반환하고, warm submit 안에서 동기 재구축하지 않는다.

현 async scheduler는 pre-submit retry를 소유하지 않으므로 due 이벤트만 넣으면 재평가된다고 가정하지 않는다. S3에서 기존 WATCHING 평가 owner의 명시적인 demand 인계 지점과 완료 consumer를 연결한다. delay owner는 due/원 기회 관계만 전달하고 WATCHING owner가 현재 입력·native claim·접수 여부를 결정한다. 이미 원 요청을 종료한 stock의 잔여 request 필드를 새 평가 identity로 재사용하지 않는다. handler 분기부터 coordinator·완료 consumer·최종 adapter까지 통합 fixture로 이 경계를 증명한다.

due가 몰려도 별도 provider request를 기회마다 강제 생성하지 않는다. 진행 중이거나 사용할 수 있는 **동일 현재 평가 identity**가 있을 때만 native dedup·기존 동시성/요율/queue 예산 안에서 successor 한 번을 연결한다. 다른 기회의 PASS를 공유하거나 기존 요청을 취소해 delay 우선권을 만들지 않는다. due budget 안에 접수하지 못하면 정상 만료다. `requested/joined/admitted/completed/expired`, 실제 provider 호출 수와 평가 대기를 함께 기록하며 예산·worker 수를 늘려 성능을 맞추지 않는다.

## 7. 구현 단계·파일 위치·완료 기준

| 단계 | 기존 owner/수정 위치 | 완료 기준 |
| --- | --- | --- |
| S0 원천·지원 범위 고정 | `pre_submit_delay_tuning.py`, 기존 AI trace/outcome/원천 index | 9/29~고정일의 PASS·commit·P0/Pd·UNKNOWN·alias 대사, 원천 크기·복구 가능 필드·mapping 확정. §4.4/4.5의 수치 budget, baseline 부하/작업량/메모리와 §9 비교 절차를 후보 측정 전에 동결 |
| S1 기회·판정·관측 | `sniper_state_handlers.py`, `kiwoom_sniper_v2.py`, `scalping/ai_decision_trace.py`, 기존 pipeline writer/projection | 전체 PASS 신원 전달·두 anchor·bounded due index·동일 snapshot 재사용·queue 공정성, UNKNOWN exact projection. 정상/burst 유실·중복 0, Main/보호 경로 반복 지연 악화 0 |
| S2 비교·분류·초기 선정 | `scalping/pre_submit_delay_tuning.py` | 단일 decode/index→원천 자격→공유 split/purge→비교→cell/default. cache 무효화와 null 경제성 보존; warm/delta 작업량 감소 |
| S3 정책·runtime·PREOPEN | 같은 policy owner, `sniper_state_handlers.py`, `automation/runtime_policy_bootstrap.py` | v1/v2 사전 검증·메모리 lookup, 0초·양수·fallback, due scheduler dedup/예산, 한 번 제출·원 deadline·기존 guard |
| S4 장후·summary·의미감시 | `automation/postclose_summary_handoff.py`, `runtime_approval_summary.py`, `monitoring/submission_bottleneck_monitor.py`, 기존 checklist/strict consumer | v2 generation·동일 watermark·증분 cursor·당일/누적 분모·연구/정책/실행 상태 일치, PASS 등록 단절 경보 |
| S5 반복 리뷰·격리 재생 | 기존 `src/tests`, task별 `tmp/pre-submit-delay-initial-policy-20261010/` | 영향 회귀·독립 손계산·원천 재생과 §9 성능 gate 통과, 미해결 in-scope finding 0; v1/v2 대응 불변 후보 release에서도 검증 |
| S6 정식 장후 발행·마지막 consumer | 기존 release selector·stage dispatcher·summary/tower/checklist·strict/controller/finalization·PREOPEN | 검증한 v2 코드와 같은 source date의 새 세대를 결속, 초기정책 receipt와 새 handoff 완료, 기존 다른 family 정책 보존 |

새 engine-root Python, 새 cron/서비스/DB/AI 연구 worker를 만들지 않는다. 분리가 필요하면 기존 `src/engine/scalping`에서 가격 시점 owner를 유지하고 위치 gate를 먼저 기록한다. 구현 시작 시 현재 release/dirty 상태를 다시 확인하고 이미 완료된 Main PASS 처리 지연 수리를 되돌리지 않는다.

## 8. 장후 재생성 실행 절차

이 절은 **후속 구현 검증 후 사용할 절차**다. 현재 계획 작성에서 아래 명령을 실행하지 않는다.

1. **원 세대 고정:** 선택 release·실행 중 stage/lock/PID·기존 10/8 report/policy/summary/strict/finalization 및 10/12 PREOPEN/checklist hash를 manifest에 기록한다. 원 bytes는 보존한다. 최신 처리일이 바뀌었으면 owner와 target을 다시 정한다.
2. **격리 입력 준비:** 원 파일은 읽기 전용으로 참조하고 새 bounded projection/report/policy만 task root에 쓴다. 기존 `pre_submit_delay_tuning` CLI에 명시적인 input/output root 옵션을 추가할 필요가 있으면 같은 모듈에 구현하고 시험한다. 현재 `build_report(write=False)` 내부의 quote census cache 쓰기까지 점검해 격리 실행이 운영 경로에 부수 write를 남기지 않게 한다.
3. **원천 대사와 복원:** S0의 한 번 scan/index로 exact-linked PASS·특징·호가만 연결한다. 복원/신규 projection/제외/원래 유효 pair를 별도로 보고한다. 복구 불가능한 과거 P0나 30초 호가는 그대로 제외하고 그 원장을 반복 생성하지 않는다.
4. **격리 재생 1회:** 동일 동결 원천으로 기존 계산과 v2 계산을 비교한다. 원래 유효 21쌍의 값/근거를 보존하고 새 anchor/복원 기회는 추가분으로 구분한다. 유형별 초기 선정값·지원 N·검증·fallback·0초/양수 cell 수를 산출한다. 독립 손계산과 loader dry-run을 대조한다.
5. **최종 리뷰:** producer→projection→publisher→loader→due recheck→guard/adapter와 summary 소비를 재리뷰한다. 새 결함이면 수정·영향 회귀 후 해당 격리 계산만 갱신한다. 입력·알고리즘이 같은 실패 generation은 반복하지 않는다.
6. **정식 family 재실행:** 실행 권한이 있는 후속 작업에서 기존 closed-target recovery/단일 writer 잠금을 사용한다. S5에서 검증한 불변 코드로 producer를 실행하고 그 release/contract hash를 generation에 봉인한다. 현재 dispatcher는 `--stage pre_submit_delay --date 2026-10-08 --publication-date <실제 재생일> --recover-closed-target --launch` 경로를 제공한다. `<실제 재생일>`은 설명용 자리표시자이며 실행 전 날짜로 치환한다. `--check`/stage receipt로 실제 완료를 확인하고 launch의 exit 0만으로 끝내지 않는다. 전체 Main wrapper는 bot stop 부작용이 있으므로 family 계산을 위해 수동 재실행하지 않는다.
7. **후행 영향 갱신:** 변경된 family의 직접 projection/summary→tower→다음 checklist→strict `--require-summary-handoff`→controller/finalization을 원 target date와 같은 generation으로 닫는다. 기계·보조·수량·청산 정책 연구를 다시 돌리지 않는다. 원천/consumer hash가 달라져 재사용 불가한 후행 산출물만 재생성한다. cleanup/detector는 운영 지침의 predecessor 검증으로 재사용 가능한 범위를 구분하며, 최종화 전체에 이전 PASS를 복사하지 않는다.
8. **새 PREOPEN 준비:** 초기정책은 정책 내용 변경이므로 이전 same-policy code-refresh 영수증을 재사용하지 않는다. 현재 선택된 `main-pass-submit-20261010-v1`에는 v2 loader가 없으므로 workspace 계산만으로 인계를 완료할 수 없다. 후속 배포 범위에서 S5의 v2 대응 불변 release를 정식 선택하고 selector·bootstrap·예약기동 cwd가 같은 코드를 소비하도록 결속한다. 기계/보조 등 변경하지 않은 정책은 기존 bytes를 보존하고 필요한 코드 결속만 각 owner의 정식 절차로 갱신한다. 실제 발행일 기준 다음 적격일의 신규 prepared generation을 만들고 v2 정책·코드·source hash와 전체 계약을 검증한다. 기존 봉인된 10/12 세대는 기록으로 보존하고, 후속 실행이 새 세대를 발행하는 경우 정식 인계 절차로 successor를 연결한다. 10/10의 이전 작업에 있던 ‘동일 정책만 갱신’ 권한을 본 초기정책 선정 권한으로 오해하지 않는다.
9. **종료:** 생성된 정책·발행 경로·선정근거·coverage·최종 chain 상태를 보고한다. 현재 PID 적용을 주장하려면 별도 실제 소비 영수증이 필요하다. 아직 도래하지 않은 예약기동/자연 주문은 `future_due/not_observed`다.

현재 등록 CLI의 실행 골격은 다음과 같다. 실제 구현에서 schema migration과 root 격리를 먼저 닫은 뒤 재검증한다.

```text
PYTHONPATH=. .venv/bin/python -m src.engine.automation.postclose_summary_handoff
  --stage pre_submit_delay --date SOURCE_DATE --publication-date PUBLICATION_DATE
  --recover-closed-target --launch
```

## 9. 표적 검증·성능·종결 조건

### 9.1 의미·권한·실패 반례

| 반례/검사 | 기대 결과 |
| --- | --- |
| ENTER_NOW+PASS 뒤 인수 만료/자금 거절/미제출 | signal 기회·후행 가격 관측 유지, 실제 제출/체결/수익 합성 0 |
| 계획수량 없음, 유효 PASS와 P0/Pd 있음 | signal 가격 비교 가능; runtime 지연 intent/주문 생성 없음 |
| legacy price_ready와 신규 signal_ready 혼재 | anchor별 분모·통계·정책 분리, 시각 소급 0 |
| 과거 P0 결손 21건+최근 유효 기회 | 결손 census 보존, 기준 자격 이후 split으로 유효 학습 가능; 미래 Pd 등락으로 선별 0 |
| quote 없는 늦은 horizon과 split 경계 | 예정 관측구간으로 purge, 누락을 이용한 겹침 은폐 0 |
| UNKNOWN 보조판정 복원 가능/불가·raw PASS지만 effective VETO | exact 유효 증거만 복원, raw만으로 PASS 승격 0, 불가 row만 제외 |
| 같은 symbol 다중 기회·retry·snapshot 재사용 | canonical 기회 dedup, 원 기회 overwrite·이중 분모·train/validation 중복 0 |
| parent/child·policy generation 혼재 | 같은 partition 상속, 다른 부모의 validation 행을 학습으로 재사용 0; child의 명시 0초를 양수 parent로 덮어쓰기 0 |
| venue missing/annotation mismatch | 세션 기준 route 및 상위 type fallback, metadata만의 blanket block 0 |
| 실제 다른 feed·stale·crossed·epoch 교체 | 해당 quote/pair 격리, 정상 pair 보존 |
| 학습 1위의 관측된 검증 실패·2위 성공 | 고정 1위 미확인, 해당 cell 0초 incumbent. 검증을 보고 후보 재선정·양수 parent 덮어쓰기 0 |
| 모두 동일/모두 악화/일부 개선 | zero cell도 schema 유효, 선정/기존 baseline 근거 구분, no-data를 성공으로 표시 0 |
| source 전체 무효/유효 pair 0 | 정식 초기 정책 생성 blocked, 진단·기존 제출 동작 보존 |
| v2 hash/date/type/source 조작, v1 legacy 보고서 | 변조 거절·legacy 의미 보존·혼합 세대 소비 0 |
| 30~180초 due, 원 PASS 만료, 재평가 새 PASS 또는 WAIT | 새 유효 증거만 제출 가능, TTL 연장·old PASS 재사용·WAIT 강제 BUY 0 |
| due 뒤 scheduler 미접수·새 요청 deadline이 더 늦음 | due+기존 budget 안에서만 제출 가능, 독립 native deadline 연장 0, 기한 뒤 pending 종료 |
| due 재평가·중복 tick·restart·order 응답 미확정 | re-arm 무한 루프·중복 adapter 호출·미확정 자동 재전송 0 |
| 정책/source/report 갱신 중 crash·다른 publisher 실행 | 원자적 세대 게시·parent CAS·기존 유효 세대 보존 |
| workspace v2·선택 release v1 또는 bootstrap/예약기동 root 불일치 | v2 PREOPEN 수용 거절, 코드·정책 동시 결속 전 적용 주장 0 |
| 공유 queue 포화·느린 writer·실행 중 callback·종료 drain | 기존 scanner/필수 저장의 starvation·Main 동기 fallback 0, 접수/실제 append/부분 저장을 분리 |
| 동일 snapshot의 여러 기회·늦은 worker·mutable book 교체 | 물리 snapshot 공유와 원 기회 분모 유지, 늦은 가격으로 P0/Pd 교체 0 |
| 반복 등록/취소·동시 due·모든 horizon 만료 | 회차별 작업/메모리 상한, heap/dedup/snapshot 참조 유한 회수, live 기회 overwrite 0 |
| 원천 same-size 교체·late partition·partial line·날짜 추가 | 영향 cache/cursor 무효화, 변경된 70/30 분할 재계산, 이전 cutoff의 선정 재사용 0 |
| 저장 지연·raw/compact watermark 차이·cursor 재기동 | 유예 전 count mismatch 단정 0, bounded catch-up 및 같은 창의 새 정상 receipt로 회복 판정 |

기존 pre-submit delay, scanner async bridge, runtime bootstrap, stage handoff, runtime summary, submission monitor, strict/checklist와 실제 제출 경로의 영향 selector만 시험한다. Python compile·diff, 변경 wrapper가 있으면 bash syntax/계약, 문서는 링크·owner·print-only parser를 검증한다. API/AI 호출이나 실제 주문으로 테스트하지 않는다.

### 9.2 성능 측정 절차와 목표 작업량

현재 선택 배포본·workspace 기준 SHA, 후보 SHA, 입력/clock/설정 hash와 CPU/RSS 측정 환경을 고정한다. 먼저 baseline 반복 변동폭을 기록하고 baseline/후보를 번갈아 각 3회 측정한다. 같은 bounded fixture/projection을 사용하며 역사 raw full scan이나 정식 장후 발행을 3회 반복하지 않는다. cold 검사는 task-local cache만 비우고 운영 캐시·OS page cache를 지우지 않는다.

| 시나리오 | 함께 측정할 값 | 개선·비악화 조건 |
| --- | --- | --- |
| 현재와 같은 0초 동작, 관측 없음/정상 PASS/동일 종목 다중 PASS | Main `loop_work_warm`, response→claim→guard→adapter, lock wait/hold, CPU/RSS, 관측 등록·append 수 | warm selector의 policy/report open·JSON decode·전체 hash 0. 기존 제출 처리의 반복 지연 악화·추가 만료 0 |
| 전체 PASS 확대, 두 anchor·동시 due·설계 burst·보유/청산 혼합 | WS snapshot 횟수/복사 bytes, hash 횟수, due dispatch·queue 대기, exit wake/guard, category backlog·RSS | 같은 source snapshot의 중복 복사/hash 제거, 정상/burst 유실 0, 기존 scanner/보호·청산 starvation 0 |
| 느린 관측 writer·필수 저장 지연·queue 포화·shutdown/restart | 접수/append 수, 실패·거절·drain 시간, Main/WS lock, full/partial write | 관측 지연이 제출의 선행 대기로 전파되지 않음. 필수 저장 지연은 원 deadline 그대로 만료, 무한 대기/동기 fallback 0 |
| 양수 지연 및 같은 due burst | 목표 지연, 실제 due→재평가→API 시작, 초과 지연, scheduler 접수/합류/만료·provider 호출 수 | 정책 대기와 처리 지연을 별도 표시. 동일 신원 중복 호출 0, 기존 요율/동시성/5초 budget 유지 |
| 장후 cold·동일 generation warm·하루/partition delta | wall/CPU/peak RSS/temp bytes, 원천/검증 read bytes, JSON decode/scan/sort 횟수, pair·cell 수/hash | 동일 raw/compact를 run 안에서 한 번 decode, warm 원천 재decode 0, delta는 영향 projection만 재구축. 순수 계산·필수 byte 검증 비용을 별도 보고 |
| 5분 감시 정상 append·큰 tail·rotation/partial line | 읽기/검증 bytes, cursor 진척, backlog age·남은 bytes, 실행 시간/RSS | 변경 없는 compact JSON 재decode 0, 검증 없는 prefix skip 0. catch-up은 유한 진척하며 원 상한을 넘지 않음 |

시간은 N·p50/p95/p99/max와 성공·실패·만료를 함께 보고한다. 작은 N에서는 개별값·max를 보고하며 의미 없는 p99를 새 합격선으로 만들지 않는다. 종료한 기회만 골라 평균을 내지 않는다. 공유 queue는 신규 delay뿐 아니라 기존 scanner 완료율/지연을 같이 대조한다. 일정 시간이 지나면 cache·heap·map이 안정된 상한으로 수렴하는 반복 등록/종료 fixture도 포함한다.

기존 작업의 성능은 **같은 기능·같은 기회/호가 분모**에서 비교한다. 신규 전체 PASS 기능의 순증 비용은 별도 표로 제시하고 총부하도 gate에 포함한다. 소표본·원천 범위 축소·일부 horizon 포기로 빨라진 결과를 최적화로 인정하지 않는다. 양수 정책의 의도된 30~180초는 제거한 처리 비용으로 계산하지 않으며, 총 사용자 관측 지연과 due 초과 지연 모두 공개한다.

### 9.3 적용 전 성능 gate와 실패 처리

1. **의미/안전:** 최적화 전후 같은 v2 의미 계약의 reference 계산과 identity·P0/Pd·분모·선정값·hash 계약 차이 0을 확인한다. 기존 v1과 다른 새 split·유형·선정은 명시한 fixture/손계산으로 검증하며, v1의 결함을 그대로 재현해야 한다는 뜻이 아니다. 정상/설계 burst의 설명되지 않은 관측 손실·중복·추가 PASS 만료·늦은/중복 주문은 0이다. 필수 저장과 hard/protect/emergency·보유/청산 경로의 반복 지연 악화가 없어야 한다.
2. **장중 비악화와 개선:** warm policy 파일 I/O 제거, snapshot/hash 재사용, 제한된 due 처리의 작업량 감소를 계수로 입증한다. baseline 변동폭을 넘는 반복 p50/p95·CPU·queue 악화는 실패다. Main/WS/보호 경로가 비악화하면서 정책 조회 또는 관측 처리의 실측 시간/CPU도 반복 개선되어야 성능 개선으로 수용한다. 평균 CPU 감소만으로 tail·만료·queue 악화를 상쇄하지 않는다.
3. **장후 개선:** 같은 입력에서 중복 decode/index/sort가 줄고 cold 계산이 반복 악화하지 않아야 한다. warm/delta의 wall 또는 CPU 개선과 원천 작업량 감소를 함께 확인한다. 이전 계획의 wall/CPU ×1.20은 개선 목표에서 제거한다. `RSS baseline×1.10+64MiB`는 기존 비교 상한으로만 유지하고 현재 시스템의 절대 한도·S0의 전체 retained-memory 한도를 동시에 만족한다. 모든 기능 추가에 64MiB를 각각 더 허용하지 않는다.
4. **판정 불가:** 환경 부하나 작은 N 때문에 차이를 판단할 수 없으면 `performance_not_established`다. 동결 fixture의 충분한 반복·프로파일링으로 원인을 확인하되 원천/정식 장후 재실행을 반복하지 않는다. 단일 max 잡음을 이유로 hard guard를 완화하거나 baseline 변동폭을 후보 결과에 맞춰 늘리지 않는다.
5. **실패 시:** in-scope 코드/자료구조/스케줄링을 보완한 뒤 영향 반례와 동일 부하를 다시 비교한다. 미해결이면 S6 발행·새 v2 release 선택을 진행하지 않고 기존 선택 정책/코드를 유지한다. 처리량을 맞추려고 worker·provider quota·관측 queue 상한·watch cap·deadline을 늘리거나 source 검증을 끄지 않는다. 이미 활성화된 다른 owner의 안전 중지/rollback은 그 owner의 기존 계약을 따른다.

계측은 [기존 runtime performance](../../src/engine/monitoring/runtime_performance.py)의 bounded counters/histogram을 확장하고 lock 안에서 분위수·JSON·동기 로그를 계산하지 않는다. 관측 개별 event를 별도 대용량 성능 원장으로 복제하지 않는다. 적용 gate 자체는 오프라인 격리 검증이며 추가 실거래 표본/경제성 승인 조건이 아니다.

보유청산과 함께 실행할 때는 [공통 자원 계약과 결합 gate](main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md#103-계층-cache와-두-계획의-합산-자원)도 S0/S5가 확인한다. 두 family는 원천 decode·정확한 identity/clock·같은 계약의 snapshot만 공유하며, quote 가격 개선과 실제/CF 손익·후보 선택은 각자의 owner를 유지한다. 한 개의 예산 manifest로 합산 RSS/CPU/I/O/queue/Provider 수요와 stage 시간창을 고정하고 단독 통과만으로 결합 부하를 통과시키지 않는다. 각 경로의 기존 절대 guard와 이 계획의 수용 조건을 유지하며, 공통 경로에 여러 기준이 적용되면 더 엄격한 기준을 사용한다. 개별 모듈마다 메모리 여유분을 중복 배정하지 않는다.

### 9.4 유한 종결

유한 종료 조건은 **미해결 구현 finding 0 + 영향 검증 및 §9.3 성능 gate PASS + 실제 동결 원천에서 의미가 검증된 초기정책 생성 + stage/summary/strict/최종화 및 PREOPEN 인계 일치**다. 정책의 모든 값이 0이어도 근거와 미지원 범위가 정확하면 초기 baseline 생성은 완료할 수 있다. 양수 지연의 검증 개선이나 실제 순익 향상을 추가로 주장하지 않는다. 원천이 전부 무효이면 `blocked`의 owner/artifact/영향 범위와 다음 source 조건을 기록하고 같은 재생을 중단한다. 자연 표본을 만들기 위한 주문·AI 호출을 하지 않는다.

## 10. 문서 검토 기록

최초 검토 대상은 D1~D9의 원천·분모·초기정책·TTL·consumer·재생성 연결이었다. 현재 코드 점검의 56 PASS를 이 계획의 신규 구현 완료로 사용하지 않는다. 아래 수치는 최초 계획 검증 기록이며 이번 성능 리뷰 결과는 §11에 구분한다.

계획 self review와 보완에서 anchor 혼합, source-invalid 행의 split 참여, partial horizon purge, 지원 후보의 공통 분모, parent/child 분할·0초 우선순위, due 재평가의 유한 대기, v1 비용 gate와 v2 초기 근거를 정리했다. 후속 재리뷰에서 다중 파일 발행의 혼합 세대 가능성과 v2 정책을 v1 선택 release에 넘기는 공백을 확인해 committed manifest의 단일 pointer와 검증한 불변 release의 정식 인계를 추가했다.

- 문서 4개의 로컬 링크 42개·anchor 2개 결손 0, 신규 문서를 포함한 공백 검사 통과.
- print-only parser: 20항목, 경고 0, 10/12 `DirectFamilyPreopenPolicyHandoff` 1개. 이번 완료된 계획 기록은 backlog의 OPEN 항목으로 새로 생성하지 않는다.
- 10/10 계획 완료 owner 1개, 봉인된 10/12 checklist는 HEAD와 동일하다(SHA256 `9e7d9f001a13cfac3b0fbd566bcfa860bd598ce41a9d1280437dcccaefff40a3`).
- 이번 변경은 신규 상세 계획·기존 계획 2개의 상태/연결·10/10 계획 기록이다. Python·wrapper·정책 bytes·release·장후 원장·PREOPEN을 변경하지 않았다. 문서 작업이므로 신규 pytest/compile·성능 실측·장후 재생성·외부 sync는 실행하지 않았다.

## 11. 성능 저하 방지·개선 후속 리뷰

사용자의 계획 리뷰 요청에 따라 실제 loader·Main 관측 caller·호가 hash/기록·공유 queue·ledger 검증/보고서·감시 cursor를 다시 읽었다. D10~D16은 코드 경로에서 확인한 작업량·인계 공백이며 운영 지연의 실측 원인이나 개선 완료 수치가 아니다.

| 확인한 계획 공백 | 보완한 계약 |
| --- | --- |
| `bounded`만 명시하고 공유 queue의 기존 작업 reserve·실행 중 callback·보유 메모리를 제한하지 않음 | §4.4 category quota·S0 수치 budget·due index·공유 snapshot·공정 drain·실제 append 대사 |
| 장중 정책 선택 때 보고서를 반복 읽는 비용을 그대로 둠 | §6.3 준비 단계 검증·불변 lookup·generation invalidation·warm 동기 rebuild 금지 |
| 기존 scheduler가 지연 재점검을 이미 지원한다고 가정 | D16·§6.3 WATCHING owner 명시 인계·원 claim 종료·통합 adapter 검증 |
| 장후 단일 scan 선언과 실제 seal/verify/report 중복 decode가 충돌 | §4.5 공유 snapshot/index·봉인 projection·독립 verifier 경계·cache 무효화 |
| 70/30 분할과 parent/child cache를 날짜가 늘어도 그대로 재사용할 수 있음 | 원천 pair 재사용과 partition/선정 재계산을 분리, late/복원/정책/알고리즘 변경 반례 추가 |
| 성능의 평균·상대 상한만 있고 총부하·보호 경로·실제 개선 수용이 없음 | §9.2 부하별 계수/지연/메모리 측정, §9.3 작업량 및 실측 개선·실패 시 발행 중단 |

재리뷰에서 source 의미 보존, 미래 가격/원 anchor 보존, 큐 접수와 durable 저장의 차이, snapshot 공유와 기회 dedup의 차이, 정책 캐시와 stale/expiry guard를 대조했다. 추가로 callback 중 fsync를 회차 budget이 중단할 수 없다는 점, drain 재접수의 단일 owner, v1 대비 의도된 선정 변경과 v2 최적화의 동일성 검사를 구분해 보완했다.

- 최종 문서 2개의 로컬 링크 17개·anchor 1개 결손 0, fence·신규 문서를 포함한 공백 검사 PASS, `git diff --check` PASS.
- print-only parser 20항목·stderr/경고 0, 기존 10/12 `DirectFamilyPreopenPolicyHandoff` 1개와 10/10 계획 완료 기록 1개 유지.
- 작업 시작 때 고정한 다른 계획 3개·10/9 및 10/12 checklist·runtime selector·10/8 report/policy 총 8개 파일 hash 변화 0.
- 보완 범위는 이 계획과 기존 10/10 계획 기록이다. 이번 문서 리뷰의 미해결 in-scope finding은 0이며, 수치 budget 확정·신규 코드/통합 시험·성능 실측·장후 재생성·정책 발행·배포는 S0–S6 후속 작업으로 남아 있다. 계획 검증을 성능 개선 실적으로 보고하지 않는다.

보유청산 계획과의 후속 연결 리뷰에서는 §4.5에 전체 종목·시장 scope 및 상한 초과 시 분할/재개·전역 완료 검증을, §9.3에 두 family의 공통 예산·결합 부하 gate를 추가했다. 각각의 가격/경제 owner와 기존 수용 조건은 유지한다. 두 상세계획 로컬 링크 52개(앵커 포함 6개)·참조 테스트 경로·공백/fence 및 print-only parser 20항목을 재검증했다. 이 연결 보완도 코드·실측·정책 실행을 수행하지 않은 문서 변경이다.
