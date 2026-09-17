# 공통 데이터 판정·미진입 기회비용 전수 튜닝 통합 구현계획

작성 기준: 2026-09-17 KST. 상세 구현계획이며 코드 완료·현재 release/PID·오늘 자연 원천·자동 정책 선정의 receipt가 아니다.

**이 문서가 두 계획의 단일 실행계획이다.** 기존 기회비용 계획의 경로를 유지하여 공통 데이터 판정 계획을 본문에 통합했다. 기존 C0–C7/OC0–OC8은 §8의 U0–U12로 대응되며 별도 작업으로 합산/이중 실행하지 않는다. [기존 공통 판정 문서](kiwoom-intraday-common-data-health-implementation-plan-2026-09-16.md)는 보존된 통합 전 설계이며 독립 실행계획으로 사용하지 않는다.

## 1. 목적·최종 개선 방향·권한

구현 현황: [9/17 부분 구현 리뷰](../audit-reports/2026-09-17-common-health-opportunity-cost-scoped-implementation.md). WS 공통 health/quote clock·observer age, 기존 튜닝/원천 전달의 부분 보완과 U3 canonical activity/required feature 분리를 범위별로 검증했다. 최신 release/PID와 자연/경제성 잔여는 해당 리뷰의 receipt를 따른다. U2~U4 전수 전환·U0–U12 전수 완료 또는 전체 미진입 튜닝 완료가 아니다.

목표는 **잘못된 입력 차단과 중복작업을 먼저 수리한 뒤, 진입하지 않은 실행가능 기회를 포함한 동일 모집단의 비용 후 기대값·일별 순이익을 최대화하는 것**이다. 작은 양수 수익의 유효 반복·tail·자본점유를 함께 평가한다. 주문 수나 체결된 거래의 평균 수익률만 높이는 후보를 고르지 않는다.

하나의 흐름으로 개선한다:

    genuine WS/REST 원천
      → 공통 facts/health·route/type/time/continuity
      → main/scanner/widget/episode·micro/holding 소비
      → 기계 평가 전체·실제 compact AI 보조심사·가격/수량 계획
      → 미제출/미체결/부분·전체체결 및 후행 executable outcome
      → 기계·AI·가격·수량/leg 각각의 전체 모집단 paired 평가
      → 기존 bounded candidate/publisher/PREOPEN/dated loader
      → actual PID 소비·R6·비용 후 자연 경제성

기계 action owner, ENTER_NOW 이후 compact AI 보조심사, numeric 가격, 최초 수량/leg, AVG_DOWN/PYRAMID action/price/sizing, widget/episode/manual custody는 독립 유지한다. 공통 health는 입력 사실만 전달하며 ENTER/PASS/BUY/SELL/가격/수량 authority를 만들지 않는다. 기계 BLOCK에 가상 AI 응답을 붙이지 않는다. AI 모델 비교·Bedrock Entry 재도입은 범위 밖이다.

**기존 module/helper/cache/adapter/report section/정책 family를 재사용한다. 새 collector·service·timer·cron·DB·운영 CLI·별도 장후 단계·Python production module을 만들지 않는다.** 기존 test를 우선 확장한다. 불가피한 새 test 파일은 기존 파일 확장이 불가능한 이유와 location gate를 확인한다. 공유 kernel 변경이 runtime 판정에 영향을 주면 source-only report 수리로 분류하지 않는다.

이번 요청은 두 계획의 통합이다. 코드·실API/Provider 호출·운영 report 재생성·commit/push·정책/env/lock/주문·배포/재기동을 실행하지 않는다. 후속 일괄 구현 승인 시 package별로 수행하되 실제 기동/적용은 해당 권한과 기존 실행 contract를 확인한다. 기존 승인된 bounded family의 후보별 사용자 재승인을 새로 요구하지 않는다.

소유 기준:

- [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8: active/OFF·경제성·권한·rollback 및 clean baseline.
- [당일 체크리스트](../checklists/2026-09-17-stage2-todo-checklist.md): 실제 OPEN·Due/TimeWindow·수용조건. U package는 schedule/native 추천 ID가 아니다.
- [Kiwoom API data contract](../kiwoom-api-data-contract.md): 공식 protocol reference gate와 source precedence.
- [장후 지시문](../postclose-tuning-result-review-task-instructions.md): 승인된 구현 후 기존 producer/last consumer/strict closure.
- [기계+compact workorder](machine-compact-auxiliary-postclose-implementation-workorder-2026-09-14.md): 기존 역할·prompt/source partition 계약.
- [Widget source·성능 계획](widget-postclose-performance-and-source-closure-implementation-plan-2026-09-16.md): 필요한 W0–W7 source/replay closure와 연결한다. 그 계획까지 신규 package로 중복 합산하지 않는다.

## 2. 선행·병행 순서와 두 개의 독립 완료 gate

### 2.1 실행 원칙

**공통 입력 판정 개선이 선행이고, 전수 inventory·기회비용 분모/quality gate 수리는 병행한다.** 전체 공통 계획의 모든 자연 sample/경제성을 기다리며 연구를 멈추지 않는다. 반대로 입력 결손을 정상 BLOCK/VETO로 학습해 threshold를 완화하지 않는다.

| 경로 | 시작/진행 조건 | 종료 gate |
| --- | --- | --- |
| 공통 판정 U0→U1→U2→U3/U4→U5 | current code/official contract 고정 | 원시각/route/type parity·전수 consumer 계약·새 source 정상 wakeup·중복 억제·guard 불변 |
| 분모/quality U0→U6 | U1 구현과 병행 가능; shared schema는 먼저 합의 | raw/기계/AI/집행 counts 보존·role별 gate 분리·미분류0 |
| 기계 U7·AI U8 | U6 + 해당 scope의 유효 frozen 원천/후행 label | full-population paired EV/holdout·current policy/prompt partition·tail guard |
| 가격/수량 U9·독립 owner/기타 U10 | U6 + 해당 scope/역할 원천 검증 | price-ready/holding-ready 등 실제 role 분모·CF/actual 구분·각 family 선정 contract |
| 자동 handoff U11 | 해당 후보평가 package의 review/validation 종료 | publisher→PREOPEN→dated loader→verify/source hash의 같은 generation |
| 통합 closure U12A 및 허용 배포 U12B | 배포 범위의 모든 직접 의존 변경 검증 | 작업본/release hash 일치·필요 owner/PID·자연 receipt·독립 경제성 보고 |

유효한 기존 과거 원천은 clean baseline/route/time/cost/current-compatible policy partition이 검증되면 U7–U10 연구에 사용할 수 있다. 신규 health metadata가 없다는 이유만으로 유효 원천을 전부 폐기하지 않는다. 다만 과거 packet/receipt로 동등 사실을 입증할 수 없는 row는 diagnostic/missing이고, metadata·과거 signal/attempt를 합성하지 않는다.

U9의 action baseline은 현재 검증 incumbent로 고정할 수 있다. U7/U8의 새 후보가 먼저 승격되어야만 가격/수량 연구를 시작하도록 하지 않는다. U10도 필요한 Widget source closure만 의존한다. 범위가 다른 W package 전체의 완료를 무조건 전제로 추가하지 않는다.

### 2.2 입력 수리 gate H와 정책 선정 gate E

- **H: 입력/운영 수리 완료.** 동일 원천/clock/scope/contract parity, false freshness0, 중복 공백계수0, 새0B/0D 정상 복귀, account/order/SELL 감시 불변, targeted validation/finding0. 양수 EV·실체결·전horizon·5/10/20일 동시floor를 요구하지 않는다.
- **E: 경제성 후보 선정 완료.** 해당 family의 source-valid 공통 기회 모집단·비용/exit/capital 계약·rolling/chronological holdout·paired 개선·tail/source/authority guard를 만족해야 한다. H만으로 E를 PASS시키지 않는다.
- **부분 H 배포 가능.** 후속 배포 권한이 있으면 검증된 공통 판정 범위는 U12A의 scoped closure→U12B로 먼저 전달할 수 있다. 경제성 표본/새 후보를 기다리며 유효 raw 수리를 지연하지 않는다. 그 범위의 downstream parser/source gate도 함께 검증해야 하고 미검증 변경을 release에 섞지 않는다.
- 최종 전체 구현 완료는 U0–U11 전수 disposition과 U12A 통합 finding0이다. 부분 H release/PID 성공을 전체 기회비용 구현·자연 수익 완료로 보고하지 않는다.

### 2.3 source 결손과 정책 과차단의 귀속

source-invalid row는 전체 census에 남기고 source-quality 복구 owner로 보낸다. 경제성 usable row에만 기계/AI 정책 오류 가능성을 평가한다. metadata 수리 뒤 동일 입력/동일 action policy 비교로 source 판정 효과를 확인하고, candidate action 변경 효과는 별도로 측정한다. 정상 quiet만으로 SOURCE_INVALID를 해제하거나 필수 tape/1초micro/quote 안전을 무시하지 않는다.

## 3. 공통 입력 사실·health·공백 episode·API 정규화



### 3.1 단순한 체결 공백 기준

제안 초기값은 **공백 10초, 서로 다른 공백 episode 3회 반복**이다. 10초는 단순한 engineering 초기 제안값이지 전문가 공인 기준·경제적 최적값 또는 현재 적용값이 아니다. 호가/주문 안전 TTL을 10초로 변경하는 값도 아니다.

| 상태 | 판정 |
| --- | --- |
| `RECENT_TRADE` | 마지막 정상 `0B` 이후 10초 미만 |
| `QUIET_TAPE_OBSERVED` | 10초 이상이고 해당 scope의 관측 경로 정상성을 확인할 수 있음 |
| `REPEATED_QUIET_TAPE_OBSERVED` | 서로 다른 공백 episode가 3회에 도달 |
| `OBSERVATION_UNPROVEN` | 첫 체결 미수신, 등록/epoch/route 불명, 연결 이상, 로컬 drop 또는 관측 연속성 미입증 |

이 상태는 **로컬 관측 체결 공백**이다. WS LOGIN/PING이나 다른 종목의 체결만으로 해당 종목의 시장 무체결을 확정하지 않는다. 반복 공백도 저유동성의 관측 징후이지 실제 무체결·손실 또는 주문 미체결의 증명은 아니다. `trade_event_age_ms`와 `trade_receive_age_ms`를 함께 보존해 오래된 체결의 뒤늦은 전달을 구분한다. provider 시각 의미가 불명확하면 null/직접 사유로 남긴다.

**평가 3회·REST 조회 3회·promotion 3개·5분 내 retry 3회로 반복을 세지 않는다.** 같은 연속 공백은 수백 번 읽어도 한 번이다. 시간대별 세분화, 종목별 adaptive p99 또는 새 EV 승격 gate를 추가하지 않는다.

### 3.2 공통화가 바꾸지 않는 것

- `0D` freshness, crossed/nonpositive BBO, quote divergence, hard/protect/emergency, broker/account/order/quantity/cooldown과 승인 override는 기존 owner 계약을 유지한다.
- 6초 전 `0B`를 현재 공격적 매수체결·buy pressure·유효한 1초 micro 창으로 바꾸지 않는다.
- 오래된 last sale는 참고 mark일 수 있어도 현재 executable 가격이 아니다. 가격 owner는 기존 fresh bid/ask와 자신의 계약만 소비한다.
- 정상 관측 공백 자체를 `SOURCE_INVALID`로 세지 않는다. 그러나 stage에 필수인 현재 tape/feature가 불충분하면 기존 owner의 명시적 입력 부족/`RECHECK`/차단을 유지한다. guard 삭제나 무조건 중립 feature 대입으로 우회하지 않는다.
- quote와 tape의 서로 다른 갱신 빈도는 통신 latency가 아니다. 반대로 새 provider 체결이 오래 지연돼 도착한 것을 정상 공백으로 숨기지 않는다.
- 이번 요청은 계획 수립이다. 코드 수정·API 호출·env 변경·배포·재기동은 문서 작성 중 실행하지 않는다.

### 3.3 소스 조사에서 확인한 공통 판정 개선 후보

아래는 소스상 경로 확인 결과다. runtime 발생량·경제적 영향은 별도 확인하며, 파일 존재를 현재 ON/PID 소비로 간주하지 않는다.

| 경로 | 확인점 | 개선 내용 |
| --- | --- | --- |
| `ai_market_snapshot.realtime_type_provenance` | type별 시각/route를 보존하지만 `_FRESH_MS=3000`을 여러 입력에 사용 | provenance 존재·동일성, 체결 활동, feature 유효시간을 분리 |
| AI snapshot preflight | current price/tape/BBO와 source-time skew가 연결됨 | 오래된 체결·fresh quote 조합을 전체 원천 손상으로 오인하는지 stage별 확인; 실제 missing/conflict 유지 |
| scanner normalize/fresh helper | `0B`, last trade/history와 aggregate 시각으로 freshness를 따로 계산 | 공통 필드 소비; history/aggregate로 exact receipt를 대체하지 않음 |
| pre-AI refresh/freshness helper | aggregate `last_ws_update_ts` 기반 3초 판정이 존재 | 새 quote 도착과 consume lag 분리; 동일 frame 반복 refresh 제거 |
| `MarketDataCache` | symbol key와 단일 `last_packet_ts`로 quote age/jitter 계산 | route/session/epoch별 실제 `0D` 시각과 별도 trade 시각; 평가 호출을 packet으로 세지 않음 |
| `sniper_entry_latency` | 평가 시 `_CACHE.update`; observer refresh 뒤 `received_at=None` 갱신 | quote 원시각 유지; refresh 소비 시각을 새 호가 수신시각으로 발명하지 않음 |
| episode gateway | utils 외에 `post_kiwoom_episode_read`/직접 POST 경로 사용 | utils만 고쳐 완료하지 않음; response/snapshot에 같은 metadata 전달 |
| widget advisory | `KiwoomReadOnlyClient`의 별도 shared-budget POST | 동일 classifier/adapter 사용; source-only 조회 class 유지 |
| snapshot writer/reader | WS 원시 dict와 파일 투영의 schema/시각이 다름 | route별 판정 보존; 파일 생성시각으로 원천 age 초기화 금지 |
| tick/history helper | 목적·limit·payload별 cache와 여러 호출 지점 | 동일 요청만 합치고 historical/live·route별 의미를 섞지 않음 |

실제 구현 위치는 line number 대신 함수명과 구현 시 source hash로 고정한다.

- `src/engine/kiwoom_websocket.py`: `_snapshot_target`, `get_latest_data`, `get_all_data`, type별 receipt 갱신, raw trade/depth callback, subscription freshness.
- `src/engine/bd_fbuy_accum_pre_scanner.py`: `write_ws_snapshot`, `_ws_machine_route_payload`, `_ws_live_for_code`.
- `src/engine/scalping/ai_market_snapshot.py`: `realtime_type_provenance`, `build_ai_market_snapshot`, `ai_input_preflight`, venue consistency/source-time skew.
- `src/engine/kiwoom_sniper_v2.py`: `_scanner_normalize_ws_snapshot_for_entry_eval`, `_scanner_ws_snapshot_entry_realtime_fresh`, stale-park/fresh-WS reactivation, batched WS snapshot cache.
- `src/engine/sniper_state_handlers.py`: `_normalize_pre_ai_strength_ws_timestamp`, `_pre_ai_refresh_strength_momentum_ws_snapshot`, `_update_ai_quote_freshness_fields`, `_pre_submit_refresh_real_ws_snapshot`, holding refresh와 REST refresh.
- `src/engine/sniper_entry_latency.py`: entry 평가 내 `_CACHE.update`, `_maybe_refresh_stale_quote_from_observer`, relief/remeasure helper.

### 3.4 기존 owner의 분담

| 기존 파일 | 구현 역할 | 금지사항 |
| --- | --- | --- |
| `src/trading/market/quote_consistency.py` | 공통 health pure helper·source 시각 읽기를 최소 추가. 기존 numeric quote consistency 유지 | scalping/AI 역의존, network 호출, 새 가격/매매 owner |
| `src/trading/market/market_data_cache.py` | 기존 cache를 route/session/epoch·type별 시각으로 확장. 필요한 bounded activity state 보관 | 별 cache daemon/DB, symbol-only cross-route 합류 |
| `src/engine/kiwoom_websocket.py` | genuine event 도착으로 state 갱신. atomic snapshot에 공통 metadata 부착 | callback 내 REST, history 전체 복사 증가, getter 횟수로 gap count 갱신 |
| `src/utils/kiwoom_utils.py` | 기존 REST parser/helper·cache에 response/source 시각과 metadata 부착. 호환 return 유지 | 모든 응답을 trade/quote로 취급, quote 상태로 auth/주문/reconcile 차단 |
| `src/trading/order/kiwoom_episode_read_control.py` | 기존 pacer/짧은 TTL cache/공유 admission 재사용. market read의 metadata 결속 | 주문 single-flight, fresh account read cache화, retry/capacity 상향 |
| `src/engine/scalping/market_data_enrichment.py` | 기존 WS/REST envelope에 health 투영, common pure helper에 위임 | 두 번째 판정 로직, 정상 경로의 자동 REST 재조회 |
| `src/trading/market/quote_health.py` | 기존 `QuoteHealth`에 필요한 source/age metadata를 호환 전달 | 단일 `ws_age_ms`로 trade/quote/transport 전부 설명 |
| 기존 snapshot writer·consumer | 같은 metadata 저장·소비; consume clock으로 age만 재평가 | 생성/copy 시각으로 fresh화, 같은 공백 재계수 |

표의 추가 helper/field는 구현 예정이다. 기존 API로 오인하지 않는다. 기존 module 내부 최소 함수/field 추가는 허용하되 새 package/CLI/report producer는 추가하지 않는다. common market package가 engine을 import하지 않도록 import cycle을 검사한다. 큰 파일의 무관한 정리·이동도 함께 하지 않는다.

### 3.5 공통 판정 데이터 계약

기존 envelope 안에 `market_data_health` metadata를 추가한다. 소비자마다 competing envelope를 만들지 않는다. schema `kiwoom_market_data_health_v1`은 제안값이며 기존 versioning과 정합시킨다.

| field군 | 의미 |
| --- | --- |
| scope | symbol, requested route/item, market-data route, effective venue, actual execution venue, session, trade date, transport epoch |
| 원시각 | quote receive (`0D`), trade receive (`0B`), provider trade/event, REST response receive, snapshot capture 시각 |
| 소비시각 | `evaluated_at`, snapshot age, receive→consume lag. copy/serialize는 원시각을 바꾸지 않음 |
| age | `quote_age_ms`, `trade_receive_age_ms`, `trade_event_age_ms`, `transport_receive_age_ms`, `local_consume_lag_ms`; 불명은 null |
| identity/연속성 | type별 item/route/epoch/sequence, 등록 receipt, first-data, local drop/gap, continuity quality |
| trade activity | §3.1의 상태, quiet episode key, derived repeat count, 공백10초/반복3회, evidence basis |
| quote/source | fresh/stale/missing/future/conflict/unproven와 직접 reasons. stage별 quote TTL은 기존 consumer contract에서 전달 |
| REST | API/payload digest, request owner/class, requested/response route, cache/single-flight reuse, admission wait, HTTP RTT, source timestamp authority |
| authority | `decision_authority=market_data_input_only_no_order_authority`, `actual_order_submitted=false`; BUY/SELL/price/quantity/provider authority 없음 |

동일 symbol의 KRX/NXT/integrated scope는 분리한다. `last_ws_update_ts`는 transport 관측용으로 남기되 BBO/tape 대리시각으로 쓰지 않는다. `0w`/program/LOGIN/PING이 `0B`/`0D`의 freshness를 갱신하지 않는다.

WS manager가 quiet episode state의 authoritative producer다. 같은 manager의 consumer는 해당 snapshot을 공유하고, 파일 consumer는 동일 state receipt를 읽는다. REST client가 별도 repeat count를 만들지 않는다. 대응 WS 관측이 없는 REST-only scope는 `OBSERVATION_UNPROVEN` 또는 명시적 적용외로 두고, metadata 누락을 정상값으로 채우지 않는다.

### 3.6 공백 반복 episode 규칙

1. scope의 첫 정상 `0B`로 시작한다. epoch/session/route 변경·continuity 손상으로 state를 reset/invalid 처리한다.
2. 마지막 genuine trade 뒤 10초 이상 공백이면 한 episode다. key는 기존 scope·epoch·마지막 genuine trade sequence/시각에 결속한다. 새 추천/workorder ID는 만들지 않는다.
3. getter는 age와 현재 episode의 기준 도달 여부를 pure 계산한다. getter/retry/copy/promotion이 counter를 증가시키지 않는다.
4. 다음 genuine `0B` 도착 시 직전 공백이 10초 이상이었다면 closed quiet count를 한 번 증가시킨다. 동일 event/sequence 재소비는 제외한다.
5. 현재 공백도 10초 이상이면 `closed count + 현재 episode 1`이 derived count다. 긴 30초 공백을 10초×3으로 나누지 않는다.
6. 각 trade 간격이 10초 미만인 정상 활동이 10초 지속되면 반복 count를 reset한다. 별도 시간 parameter는 추가하지 않는다. connection recovery만으로 활동 회복을 선언하지 않는다.
7. provider 과거 event, regression, duplicate, route mismatch, drop/epoch 변경은 genuine 회복/반복 증거로 쓰지 않는다. 원packet은 유지한다.

10초 정확히부터 quiet로 판정한다. future 시각을 `max(0, age)`로 정상화하지 않는다. 동일 process의 duration은 monotonic clock을 우선하고, 저장 epoch 시각은 provenance/재생 기준을 명시한다. 재생은 저장된 event cutoff 기준이지 현재 시각 기준이 아니다.

### 3.7 type·route·시각

`0B` trade와 `0D` quote의 receipt를 별도 보관한다. provider시각의 정밀도·날짜·session을 선언하고 동일초 경계를 억지로 확정하지 않는다. future/regression/route mismatch/cross-epoch는 직접 source gap으로 남긴다.

requested route와 actual execution venue를 분리한다. integrated `AL`을 개별 KRX/NXT의 actual 체결 venue로 쓰지 않는다. 정상 과거 item/등록 binding을 동일 epoch에서 유지하더라도 **identity 증거 보존**일 뿐 최신 event freshness의 대리가 아니다.

`krx_integrated_event_venue_unproven`, `realtime_type_provenance_missing_or_stale`를 다음으로 분해한다.

1. item/route/epoch/등록/first-data 자체 결손·충돌.
2. 정상 과거 type receipt는 있지만 최근trade 없음.
3. provider/receive 지연, local drop 또는 연속성 결손.
4. 실제 최신quote가 오래돼 executable source 사용 불가.

2를1에 합치지 않는다. 1/3/4를 quiet값으로 해제하지 않는다. registered view와 event actual venue의 불명을 구분하고 근거 없는KRX/NXT 추정을 추가하지 않는다.

### 3.8 REST별 의미

- `ka10004`: response receive시각으로 REST snapshot age를 측정한다. fresh orderbook은 trade 생성/0B freshness/매수 우세 증거가 아니다. `bid_req_base_tm`의 `raw_not_freshness_input` 계약 유지.
- `ka10003`/`ka10084`: response시각과 provider trade시각 분리. 최신행·route·정렬·중복·continuation·범위 확인. 많은 응답행/HTTP200을 현재 활발한tape로 간주하지 않는다.
- `ka10080`: completed bar/date/route/coverage 계약 유지. 분봉을10초 공백 규칙으로 invalid 처리하지 않는다.
- basic/program/investor/index/rank: source별authority/TTL 유지. generic HTTP wrapper가 trade health를 임의 판정하지 않는다.
- account/order/auth: market activity 적용외. failure/rejection/rate limit 원계약 유지.

REST-only client는 기존read 응답에 metadata만 결속한다. **무체결을 증명하려고 quiet를 읽을 때마다 ka10084/ka10003을 호출하지 않는다.** 독립 확인이 필요한incident는 기존bounded 진단/공유budget 내 sample로 한정한다.

실제 구현 전 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 수행한다. 현재 upstream SHA·조회시각·확인paths를 review에 기록하고 `kiwoom_docs`, spec/core/realtime/Postman과 필요한portal을 대사한다. 과거SHA를 현행으로 고정하지 않는다. 미정의FID/suffix/time은 추측하지 않고 raw/null/contract gap으로 남긴다. request/parser/REG 불변 부분도 범위를 기록한다.

## 4. latency·반복호출·감시예산 개선

### 4.1 시계를 분리한다

| 값 | 측정 대상 | 잘못된 대체 |
| --- | --- | --- |
| trade gap | 해당route 정상trade 간 관측 공백 | HTTP RTT/WS delivery latency |
| provider→receive | provider시각 입증 시 전달 지연 | source시각 불명인데0ms |
| receive→consume | 새quote 이후queue/analysis/AI/guard 지연 | snapshot copy시각 |
| quote age at submit | submit 직전 채택 BBO 연령 | 최근trade/program/PING/함수return시각 |
| REST wait/RTT | admission/HTTP/retry/parse 시간 | 모든quote age를 외부API 탓으로 귀속 |

기존 `LatencyMonitor` SAFE/CAUTION/DANGER, slippage/spread/quote/price guard와 별도 승인relief를 유지한다. 700ms/1500ms/2000ms 등 stage quote 기준을10초로 치환하지 않는다. 독립latency 장후 family도 복원하지 않는다.

`MarketDataCache.update`는 genuine source quote identity/시각으로만 quote freshness/jitter를 진행한다. 같은/오래된packet 재평가로 서로 다른context의가격을 섞지 않는다. observer refresh의 `received_at=None`을 제거하는 방향으로 채택quote 원timestamp/route/epoch/endpoint를 전달한다. 원시각 불명은 unproven 그대로다.

### 4.2 동일attempt read/refresh 통합

1. 기존batched WS getter에서 atomic frame을 얻어 setup/기계판정/AI입력에 같은identity를 전달한다.
2. 동일frame/policy/attempt의pure preflight는 재사용하되 소비시점age 만료를 다시 확인한다.
3. AI 중source가 만료되면 submit 직전 새WS cache를 다시 읽는다. 이 안전 재검증은 삭제하지 않는다.
4. fresh canonical WS quote가 있으면 REST fallback을 생략한다. 없으면 기존bounded REST 계약만 이용한다.
5. REST refresh 응답은 payload/route/source/deadline이 맞을 때만 공유한다. AI전/submit전 age조건 차이를 보존한다.
6. 실패/rate limit/source rejection을 guard별로 각각retry하지 않는다. failure receipt를 공유하고 새source 또는 기존bounded 조건에서만 재개한다.

절약 대상은 동일원입력의중복조회·heavy평가다. cheap freshness 재검증, broker safety, order terminal 확인은 절약 대상으로 삼지 않는다.

### 4.3 cache/single-flight

기존 `_MARKET_DATA_CACHE`, `ShortTtlSnapshotCache`, `SameMinuteSnapshotCache`와 lock을 확장한다. 별 framework/cache/worker를 만들지 않으며 실제 동시 read 중복이 있는 기존 함수 내부에서만 single-flight를 보완한다.

- fetch key: real/demo origin, token/account scope digest, api-id, canonical wire payload, exact requested item/route, date/tm/continuation. bearer token 저장/출력은 금지한다.
- consumer owner/policy/attempt/purpose/deadline은 receipt별로 결속한다. wire data가 같아도 판단은 공유하지 않는다. query/auth scope가 다르면 fetch도 공유하지 않는다.
- limit 10/30이 같은 wire payload라면 정상 raw response 공유 가능성을 검토하되 slice/parser는 유지한다. pages/cutoff 차이는 무조건 합치지 않는다.
- 성공·source-valid 응답만 기존 TTL 안에서 재사용한다. failure/admission defer의 동일 attempt suppression은 명시적 failure receipt이며 positive cache와 구분한다.
- producer는 shared gate를 한 번 통과하고 waiter는 추가 request를 만들지 않는다. waiter deadline 만료 때문에 duplicate request를 발생시키지 않는다.
- memory/pending cap을 유지한다. timeout 후 late result가 새 epoch/current-policy context를 덮어쓰지 않게 한다. 종료되지 않은 HTTP를 끝난 worker로 가장하지 않는다.
- single-flight는 process-local이다. 다른 process까지 호출 0을 보장하는 새 daemon은 만들지 않고 기존 snapshot 공유/pacer/budget을 사용한다.
- 주문/취소/auth/fresh account·broker·terminal 확인은 대상외다. execution-critical slot을 source-only waiter가 점유하지 않는다.

### 4.4 scanner 감시·평가 예산

- 같은 scope/policy/source generation/event identity의 in-flight evaluation을 기존 coordinator에서 중복 제거한다.
- frame이 그대로인 SOURCE_INVALID를 매 loop heavy 평가/AI/REST에 재전송하지 않는다. 기존 deadline/backoff/source wakeup으로 대기하고 retry/capacity를 늘리지 않는다.
- blocker에 대응하는 genuine source에서 대기를 해제한다. quote 부족은 새 0D, trade feature 부족은 새 0B, binding 결손은 등록/epoch/source 복구다.
- 기존 stale park의 1-generation reactivation bound와 enqueue 실패 invalidate를 유지한다. quiet getter가 generation을 늘리지 않는다.
- 반복 quiet만으로 새 BUY 거부·universe 제외·slot/cap 변경을 추가하지 않는다. 기존 owner가 nonentry/입력 부족으로 닫은 같은 source의 중복 heavy 평가만 억제한다.
- slot/예약수/universe/promotion rule은 그대로 두고 기존 valid terminal/expiry의 reservation 반환·orphan 정리를 검증한다.
- 0D 변화만으로 entry 조건이 변할 수 있는 scope를 새 0B만 기다리게 하지 않는다. wakeup을 일괄 trade-only로 만들지 않는다.
- independent census/prune observer의 선언 sampling을 유지한다. 평가 절약을 시장 분모 삭제/감시 종료로 바꾸지 않는다.
- SELL/holding/custody/manual 감시와 주문 receipt는 계속 우선한다. BUY 예산 절약으로 보유 감시를 간헐화하지 않는다.

### 4.5 기존event에서 효과 확인

현재 pipeline/threshold/WS freshness/entry flow event에 최소 필드만 추가한다. 별 report/job은 없다.

- source frame/quote/trade identity, quiet episode/count, 채택 age/consume lag.
- request owner/class/API/route/payload digest, actual request/reuse/suppressed, admission wait/RTT/기존 retry 수.
- evaluation enqueue/start/end, duplicate suppression, park/wakeup reason, watch reservation 반환.
- raw event와 unique attempt/frame/promotion 분모는 분리한다. transition/terminal/기존 bounded 요약 중심으로 로그 burst를 피한다.

이 필드들의 계약은 `metric_role=source_quality_gate|funnel_count` 중 실제 역할을 명시하고, `decision_authority=diagnostic_no_order_authority`, `window_policy=exact_scope_event_or_attempt_window`, `primary_decision_metric=not_applicable_diagnostic`, `sample_floor=not_applicable_contract_validation`로 선언한다. source-quality gate는 exact route/type/epoch/time 검증이다. 금지 용도는 양수 EV/수익/BUY/SELL/정책 승격의 대용이다. quiet 반복 기준 3은 관측 상태의 기준이지 경제적 표본 floor가 아니다.

수리 acceptance는 동일 입력 1 in-flight, 동일 payload 동시 read 1 transport, 새 source 정상 복귀, 기존 guard 유지다. 공유 API 상한/source-only 예약/주문 bucket은 현재 설정을 확인하고 retry/density/capacity를 상향하지 않는다.

### 4.6 요청 목적별 budget class 점검

현재 `src/web/samsung_price_widget_routes.py._kiwoom_post`의 화면 fallback은 `request_owner=samsung_price_widget_http_fallback`, `request_class=runtime_required`를 사용한다. 화면 기본가격 `ka10001`과 account `kt00018`을 한꺼번에 같은 market-read 절약 규칙으로 바꾸지 않는다.

- 비주문 화면 가격/연구/advisory/census read는 실제 intended consumer를 확인해 기존 `source_only` reservation으로 분류 가능한지 검토한다. 화면 refresh가 execution용 slot을 소모하는 직접 후보다.
- gateway의 BUY 직전 liquidity/velocity, holding 안전 확인, 실제 broker/account/terminal read는 기존 `runtime_required|execution_critical` 역할을 유지한다.
- `get_tick_history_ka10003` 등 helper가 request owner/class를 전달하지 못하면 기존 함수에 호환 keyword 인자를 추가하고 callsite가 목적을 전달하도록 한다. 새 helper 복제 또는 API-id만으로 전체 class 변경은 하지 않는다.
- class 변경은 호출 목적의 잘못된 귀속을 고치는 범위다. source-only capacity 확대, 새 polling, shared limit 완화 또는 주문 budget 축소가 아니다. 분류 근거·API 수·대기 receipt로 검증한다.
- 여러 소비자의 동일 raw 응답을 공유하더라도 우선순위가 낮은 작업의 긴 대기 때문에 execution consumer가 같은 pending 작업에 무조건 묶이지 않게 한다. deadline/예약 계약을 먼저 검증하고, 안전하게 묶을 수 없으면 기존 명시적 defer를 유지한다.

## 5. 수신부터 raw 기반 튜닝·policy 소비까지 전수 inventory

하나의 ledger에서 live 수신/소비 callsite와 raw/파생/선정/publisher callsite를 결속한다. 두 검색 inventory의 개수를 더해서 고유 consumer 수라고 하지 않는다. 파일이 같아도 역할/function/callsite/consumed_field가 다르면 구분하고 같은 source reader의 검색 중복은 제거한다.

### 5.1 장중 공통 수신·소비 inventory

조사 범위는 `src`의 비test Python, `tools` client, `deploy` launcher다. 직접 API/WS import·alias, 직접 POST, 주입 getter/client, common parser, passed dict와 snapshot file read를 추적했다. 아래는 소스 경로 inventory이며 active runtime 전수 receipt 검증 완료표는 아니다. 구현 시작 시 callsite·source hash·installed owner를 다시 고정한다.

모든 후보를 `market_live_consume / metadata_pass_through / account_order_only / historical_only / retired_off / transport_only`로 분류한다. account/history도 조사에서 누락하지 않되 trade activity 적용외다. **모든 지점에 동일3초/10초를 적용한다는 뜻이 아니다.**

#### 5.1.1 수신·공유·main/scanner

| 파일/경로 | 전환·검증 범위 |
| --- | --- |
| `src/utils/kiwoom_utils.py` | `fetch_kiwoom_api_continuous`, `get_stock_orderbook_ka10004`, `get_tick_history_ka10003`, `get_recent_signed_trades_ka10084`, `get_minute_candles_ka10080_with_meta`, program/investor/basic, `build_realtime_analysis_context`; API별 의미 유지 |
| `src/utils/kiwoom_read_request_control.py` | 공유 read budget/cooldown; health 재판정 없이 owner/class/대기 provenance 전달 |
| `src/engine/kiwoom_websocket.py` | raw0B/0D, target/getter, 등록/repair, async writer; 주문execution type 별도 |
| `src/engine/bd_fbuy_accum_pre_scanner.py` | file writer/route 투영, 장중 확인/daily fallback; DB/daily 가격을 freshWS로 바꾸지 않음 |
| `src/engine/kiwoom_sniper_v2.py` | batched WS, normalize, scheduler freshness, park/reactivation, REST fallback |
| `src/scanners/scalping_scanner.py` | 주입/alias getter, candidate/BBO/candle/tape, promotion; 독립 시장 분모를 quiet로 삭제하지 않음 |
| `src/scanners/final_ensemble_scanner.py`, `kosdaq_scanner.py`; `src/engine/signal_radar.py`, `market_panic_breadth_collector.py`, `ipo_listing_day_runner.py` | rank/breadth/daily/margin/live quote 분류; 현재 scope만 전환, OFF 전략 복원 금지 |
| `src/engine/sniper_state_handlers.py` | target→analysis/pre-AI/pre-submit/holding/multi-leg/scale-in frame, quote refresh, tick/candle/context 호출을 함수·callsite 단위로 대사 |
| `src/engine/sniper_analysis.py`, `sniper_condition_handlers.py` | basic/program/investor, 반복 tick/candle 조회; 기존 snapshot의 안전한 재사용 |
| `src/engine/sniper_s15_fast_track.py`, `sniper_overnight_gatekeeper.py` | live tick/candle/context, 보유 감시; quote/broker/exit 안전 유지 |
| `src/engine/sniper_scale_in.py`, `sniper_execution_receipts.py`, `scalping_feature_packet.py`; 기존 `ai_decision_trace.py`와 lifecycle/pipeline logger | passed frame/feature/receipt metadata 상속; scale-in action/sizing 변경 없음. journal에서 scope/type 시각이 탈락하지 않음 |
| `src/engine/ai_engine_openai.py` | machine-primary/compact auxiliary/holding 등 stage별 preflight; 필수feature·prompt partition 유지 |
| `src/engine/scalping/ai_market_snapshot.py`, `market_data_enrichment.py`, `entry_setup_evidence.py` | 독립 freshness 추정을 공통 판정으로 위임; source 수정과 action threshold 수정 분리 |
| `src/engine/scalping/entry_candle_context.py`, `holding_decision_context.py`, `multi_timeframe_context.py`, `microstructure_reaction_context.py`, `main_ai_current_axis_input.py` | completed bar/tape/reaction; 0B/REST/bar/source-only 분리 |
| `src/engine/scalping/scanner_async_eval.py`, `micro_estimator_state.py`, `entry_reprice_after_submit.py`, `entry_split_order_plan.py`, `scale_in_split_order_plan.py`, `risky_micro_episode/policy.py` | 주입 scheduler/quote/feature; deadline/bundle/source lineage 유지 |
| `src/trading/entry/entry_orchestrator.py`, `entry_policy.py`, `normal_entry_builder.py`, `signal_snapshot.py`, `entry_types.py`, `state_machine.py` | 직접 health 사용/pass-through 분리; SAFE/CAUTION normal-submit와 DANGER/slippage 유지 |
| `src/engine/sniper_entry_latency.py`; `src/trading/entry/latency_monitor.py`, `orderbook_stability_observer.py`; `src/trading/market/quote_consistency.py`, `quote_health.py`, `market_data_cache.py` | quote/trade 시계, observe/consume 분리; observer endpoint 원시각/route 읽기 |

#### 5.1.2 위젯·episode·micro·기존 exit

| 파일/경로 | 전환·검증 범위 |
| --- | --- |
| `src/trading/order/kiwoom_episode_read_control.py` | utils 우회 gateway read metadata/짧은TTL; 주문/fresh broker snapshot 제외 |
| `src/trading/samsung_morning_one_share/gateway.py`, `samsung_midday_one_share/gateway.py`, `samsung_afternoon_one_share/gateway.py`, `low_price_two_leg/gateway.py`, `widget_auto_trade/gateway.py` | `_post`, liquidity/velocity, completed minute parser/read budget; dataclass/return에서 metadata 탈락 방지 |
| 위 episode package의 `machine.py`, `service.py`, `preflight.py`; `src/trading/widget_auto_trade/engine.py`, `service.py` | 직접 getter뿐 아니라 공통 wrapper/주입client의 scope, preflight/signal/SELL/보유 복구 |
| `src/trading/order/regular_two_leg_machine.py`, `entry_liquidity_guard.py` | 공통 liquidity/velocity parser/guard; print count·depth·속도·가격·수량 계약 유지 |
| `src/trading/market/confirmation_window.py`, `micro_confirmation.py` | file exact-route0B+0D, past-only1초창; health는 전제, feature validity는 기존 kernel 소유 |
| `src/trading/market/entry_adverse_flow.py`, `target_pressure.py`, `profit_stagnation_quote.py` | adverse/target pressure/depth; quiet를 trade backing으로 보간 금지, 기존 executable quote TTL 유지 |
| `src/trading/order/entry_adverse_guard.py`, `entry_adverse_owners.py`, `target_ratchet.py`, `profit_stagnation.py`, `profit_stagnation_exit.py`, `profit_stagnation_owners.py` | 파생source 소비 owner; target/수량/취소/exit 로직 변경 없음 |
| `src/trading/order/adaptive_exit/market_source.py`, `source.py`, `runtime.py`, `group_runtime.py`, `driver.py`, `owner_loop.py`, `group_owner_loop.py`, `decision.py`, `group_decision.py`, `models.py`; `src/engine/monitoring/machine_adaptive_exit_source.py` | 연구/주입source와 runtime 연결 분류; 신규 exit 활성화/enrollment/보유 이관 없음 |
| `src/engine/scalping/limit_down_watch.py`, `micro_reversion/forward_collector.py`, `micro_reversion/canary_monitor.py` | getter 우회 raw callback; ordered0B+0D, route/epoch/sequence/source-only 유지 |
| `src/engine/monitoring/samsung_widget_advisory.py` | `KiwoomReadOnlyClient._post`, collector/BBO/tape/flow parser; source-only budget 유지 |
| `src/engine/monitoring/doosan_widget_advisory.py`, `hanwha_ocean_widget_advisory.py`, `widget_auxiliary_context.py` | 공유/상속client, symbol별advisory; market/flow/bar TTL와 metadata |
| `src/engine/monitoring/widget_symbol_runtime_collector.py`, `widget_research_watch_collector.py` | 주입 API, raw current/BBO/bar와 출력; signal source→trader 전달 |
| `src/engine/monitoring/pruned_candidate_bbo_collector.py`, `market_opportunity_census.py` | source-only bounded REST/독립census; quiet로 sampling·전체prune 분모 누락 금지 |
| `src/web/samsung_price_widget_routes.py`, `doosan_price_widget_routes.py`, `hanwha_ocean_price_widget_routes.py`; `src/notify/telegram_manager.py` | WS file/REST fallback, 공유client, 수동 분석/표시; file age와 quote age 분리, 오래된 가격 표시 주석 |
| `tools/windows` widget client, `deploy` 기존 collector/trader/monitor launcher | 서버 결과 pass-through/표시와 실제 실행 entrypoint; client의 자체 source verdict 생성 금지 |

#### 5.1.3 적용외·기존 downstream 누락 방지

- `src/engine/sniper_sync.py`, `sniper_trade_utils.py`, `kiwoom_orders.py`, `src/trading/order/broker_gateway.py`, `manual_episode_exit_reconciliation.py`, symbol-owner apply/auto-apply와 각 gateway account/order/cancel/auth/preflight: `account_order_only`. quiet 때문에 reconcile/SELL/terminal 확인을 늦추지 않는다. request budget·실제 receipt 계약 유지.
- `src/bot_main.py` calendar/auth/startup, `src/engine/error_detectors/kiwoom_auth_8005_restart.py`: `transport_only` 등. 체결 공백을 auth 실패/재기동 이유로 만들지 않는다.
- `src/engine/monitoring/low_price_two_leg_entry_spot_research.py`, `widget_symbol_signal_policy_research.py`, `pure_market_kiwoom_backfill.py`, `low_price_two_leg_expanded_candidate_research.py`, `low_price_two_leg_tuning.py`: live 수집/historical 연구 구분. 과거 tm/date 조회를 현재 activity state에 넣지 않는다. 기존 source-only budget/metadata 계약 확인.
- `src/engine/monitoring/intraday_ws_freshness_monitor.py`, `intraday_entry_flow_report.py`, `intraday_entry_blocker_diagnostics.py`, 기존 rising-missed/pyramid 진단: 기존event metadata 소비. 별도 job 없이 quote age/trade quiet 진단 혼동 수정.
- #11/#74 `observation_source_quality_audit`, #119 `buy_funnel_sentinel`, #76 materialization, #82 calibration, #77–#80/기존 replay, machine attribution/entry timing, widget calibration/evaluation: 기존 downstream. 새field/label의 false-invalid·metadata 탈락·episode 중복을 필요한 기존parser/test에서만 보완한다. **새 장후 producer·schedule·필수artifact·추천/승격 gate는 추가하지 않는다.**
- `daily_report_service.py`, `codebase_performance_workorder_report.py`, `wait6579_ev_cohort_report.py`, lifecycle/strategy replay, post-sell/missed-entry, `src/utils/update_kospi.py`: live read/historical/pass-through 분류. 검색 hit를 새 실행 owner로 만들지 않는다.
- `institutional_flow_context.py`, `swing_sector_theme_source.py`, opening rotation, 퇴역shadow/ADM/LDM/bucket/greenfield: `retired_off` 또는 historical. 적용/수집/복구/ETA를 열지 않으며 기존 custody/parser 호환만 보존한다.

#### 5.1.4 전수 완료 계약

inventory는 `file:function:callsite/consumed_field`별 source→adapter→consumer, scope, 분류, 전환 방법, test, 현재 owner를 기록한다. alias·주입client·passed dict·file reader 미분류를0으로 한다. 적용외도 분모에서 조용히 빼지 않는다.

재조사에서는 `rg`로 실제 조회 helper·Kiwoom URL·`session.post`·WS getter·snapshot path·type 시각·signed trade 필드를 검색한 뒤 Python AST로 import alias와 callsite를 대사한다. 직접 조회가 없는 downstream도 그 return/dataclass/주입 client의 사용처를 역추적한다. `curr/best_bid/best_ask/quote_stale`만 소비하는 지점도 별도 검색한다. test·archive·퇴역 코드는 적용외 분류하되 임의 삭제하지 않는다. 실행 파일 밖 client와 launcher의 import/공유 path도 조사한다. 이 inventory는 본 문서의 부록/검증 결과로 유지하고 이를 만드는 새 운영 프로그램은 만들지 않는다.

- `candidate_total = migrated_market_live + verified_metadata_pass_through + classified_not_applicable`.
- `unclassified_count=0`, `live_consumer_missing_common_health_count=0`, `independent_trade_activity_classifier_count=0`.
- 기존 stage별 quote/micro/bar/velocity 안전validator는 마지막 계수에 포함하지 않는다. 사실 age의 독립 추정·공백 재계수만 제거한다.
- grep/AST 잔존 결과를 각각 분류한다. consumer의 현재시각 읽기는 consume age 재계산이면 정상, source receive시각 대입이면 결함이다.
- static coverage, offline 연결 coverage, 실제 active PID 자연 coverage는 별개다. 비가동 scope를 자연 소비 완료로 표시하지 않는다.

### 5.2 코드 조사 결과: 이미 있는 기능과 실제 결손

#### 5.2.1 조사 방법과 전수 범위

작업본의 src/engine, src/trading, src/web, analysis를 대상으로 raw 원천 이름·JSONL/Parquet/DB reader·관련 report 입력을 검색하고, 핵심 선정기·publisher·장후 wrapper의 호출을 추적했다. 직접 raw/원천 계약 검색 131개 파일, 일반 I/O 후보 검색 295개 파일의 합집합은 부록 A에 전수 기록한다. 일반 JSON reader는 정책 로더일 수도 있으므로 raw 소비자로 단정하지 않는다.

직접 검색 키: pipeline_events, entry_observation_source, missed_entry_counterfactual, mechanistic_entry_trace, machine_decision_case_table, market_opportunity_census, scanner_prune_bbo, monitor_snapshots, micro_observer, raw_execution, observation_source_quality_audit, ai_decision_payloads, mechanistic_entry_observation, execution_replay_input, confirmation_input_trace, widget_raw, seeded_advisory, advisory_history, main_lifecycle_paired, entry_price_profile_selected_candidate, quantity_leg_four_arm_evaluation.

보완 검색 키: read_csv/read_parquet/read_json, json.load/json.loads, JSONL/Parquet 경로, sqlite3/duckdb connect. 함수 단위의 의미 확인은 아래 핵심 경로를 우선 수행했다. 부록의 I/O-only 파일 전체가 의미 검토 완료라는 뜻은 아니다. U0에서 일반 reader의 원천/간접 호출/producer 등록을 끝까지 분류하여 실제 raw 소비자와 무관한 정책·웹·archive reader를 분리해야 한다. 단순 문자열 전수 검색을 동적 전수 소비 검증으로 보고하지 않는다.

큰 원천은 stat 먼저 확인한다. 64MiB 초과 또는 증가 중이면 이번 진단에서 전체 raw를 반복 스캔하지 않고 기존 manifest/요약 또는 최대16MiB bounded tail을 사용한다. 구현하는 정상 report reader는 frozen 입력에 대해 기존 streaming/index를 재사용하고, bounded tail을 경제성 전체 분모로 바꾸지 않는다.

#### 5.2.2 확인된 구조적 보완 우선순위

| 우선 | 확인 위치 | 확인된 현행 동작 | 보완 |
| --- | --- | --- | --- |
| P1 | observation_source_quality_audit._machine_terminal_tuning_gate | AI PASS 보존식과 submitted/final_guard_blocked/broker_rejected 합이 하나 이상인지를 economic_tuning_input_allowed에 사용 | AI 보조심사 경제성과 PASS 이후 operational closure gate를 분리. 이미 독립된 machine_threshold_tuning_input_allowed는 보존. 전부 VETO여도 유효한 후행 원천이 있으면 AI 판단 연구가 가능해야 함 |
| P1 | ai_action_outcome_calibration.build_machine_decision_case_table | source-date 9/15 이후 compact tuning에도 위 terminal gate를 결합 | AI VETO 자체가 정상 미노출 terminal임을 평가할 수 있게 분리. PASS 뒤 unresolved lineage 제외는 정확히 해당 row에 유지 |
| P1 | ai_action_outcome_calibration.build_clean_baseline_mechanistic_refinement | common threshold refinement는 detailed paired report 원천, delta의 비교는 기존 AI control_action | 자연 기계 전체 평가 모집단을 common refinement에도 연결하고 비교 기준을 실제 incumbent machine policy 재판정으로 변경 |
| P1 | daily_threshold_cycle_report._entry_price_profile_candidate_grid | 관찰 profile별 COMPLETED profit_rate 평균과 exact outcome20/EV0.1%로 후보 인정. 취소 missed_upside는 별도 CF 미join 상태 | 미제출·미체결의 동일 기회 가격 replay와 paired 순이익/참여율을 선정 주근거로 추가. observed-profile 성과 비교만으로 가격 최적이라고 하지 않음 |
| P1 | daily_threshold_cycle_report._materialize_mechanistic_entry_price_policy | publisher도 joined20/EV0.10%를 다시 검사 | 새 평가 contract와 publisher/PREOPEN를 함께 정합화. 작은 양수 기대수익을 배제하는 절대0.1% 기준의 목적/근거 재검토 |
| 조건부 P1 | machine_entry_timing_tuning._candidate_observation 및 일부 economic baseline | actual_order_submitted와 owner_outcome.realized를 요구하는 adapter | 이 조건은 actual arm 검증에는 맞지만 미진입 admission 연구 전체의 공통 gate로 쓰면 안 됨. 기존 raw paired replay adapter로 source-only arm을 병렬 수용 |
| P1 점검 | sniper_missed_entry_counterfactual._build_buy_attempts | buy intent가 없는 segment는 건너뛸 수 있고 일부 terminal은 inferred 진단 | BLOCK 이전 탈락 모집단은 machine capture/census로 보완. inferred terminal/종목근접 join은 정책 승인 근거에서 제외 |
| P1 점검 | 삼성 오전 reentry 연구 | 여러 family를 같은 holdout으로 순차 검사하며 holdout reuse warning을 발급 | calibration만으로 family·후보를 고정한 뒤 한 번 검증. 실패 후 같은 holdout으로 다른 family를 채택하지 않음 |

위 항목은 작업본 계약 결손/위험이다. 오늘 특정 수치의 원인으로 확정하려면 exact-date source와 실제 분기 receipt가 필요하다.

#### 5.2.3 체결만 분석한다는 설명의 정정

#82의 load_machine_observation_rows는 이미 실제 AI 미호출 기계 관찰을 읽고 mature_outcome_labels로 후행경로를 연결한다. case table에는 BLOCK/RECHECK의 missed_opportunity_candidate와 ENTER_NOW 이후 VETO의 CLEAN_FAST_PROFIT 집계가 있다. hierarchy runtime extension에도 scope별 기계 관찰 입력이 들어간다. 이 경로는 실체결만 쓰는 구조가 아니다.

Widget paired/mechanical replay와 low-price entry-spot 연구도 raw 또는 local market bars 기반 반사실을 이미 사용한다. 따라서 결론은 새 collector가 아니라 **기존 미진입 원천의 누락·조건 결합·비교 분모·선정·자동 소비 연결을 수리하는 것**이다. OHLCV touch 기반 연구는 실체결 증거가 아니고 source-only 후보 단계로 구분한다.

### 5.3 소비자별 조사·수정 매핑

상태: A=미진입/CF 소비가 이미 있음, F=실체결 중심 선정, R=실체결 필요 역할이므로 유지, G=원천/정책 경계 보완, X=OFF/퇴역/비우선으로 복원하지 않음. 한 행에 복수 상태가 가능하다. 메타데이터 요약기는 경제성 계산기로 바꾸지 않는다.

| 역할·기존 파일/함수 | 입력과 현행 분모 | 상태·구체적인 개선 책임 |
| --- | --- | --- |
| #11 ai_decision_quality, #74 observation_source_quality_audit, source_quality_hard_gate | payload archive·machine capture·pipeline·가격/체결·quality manifest | A/G: source-invalid·지원scope 밖·hash/window/cost 결손도 census에 유지. 기계/AI/집행 gate 분리, row별 배타적 제외와 소비 보존식 |
| #76 ai_decision_quality materialization, ai_input_quality_baseline_replay | machine-only와 실제 provider 원천 | A/G: machine action/reason/threshold hash와 AI exact prompt/response를 다른 분모로 보존. machine-only를 Provider replay 완료로 세지 않음 |
| #82 ai_action_outcome_calibration | detailed paired + machine observations + compact screens | A/G: common refinement·scope hierarchy·compact 각각 전체 기회 경제성→candidate까지 연결; early continue row가 case 분모에서 사라지지 않게 exclusions 반환 |
| #77 micro_reversion.ai_quality_cycle/bridge/replay, #78 main_ai_prompt_optimizer, #80 main_ai_prompt_consumer | prepared request·paired replay·calibration·frozen prompt evidence | A/G: 현재 compact 보조심사 역할/모델/부가지시문으로 비교. legacy independent BUY/WAIT Control을 compact 판단 최적 기준으로 재사용하지 않음 |
| mechanistic_entry_runtime_policy, entry_setup_live_policy, calibration.build_mechanistic_hierarchy_candidate | calibration threshold/hierarchy/compact registered variants | A/G: candidate publisher/activation projection/PREOPEN source hash와 새 full-population metric 계약을 결속. 서로 다른 owner 후보를 무조건 동시 승격하지 않음 |
| #119 buy_funnel_sentinel→#23 entry_recheck_policy/entry_recheck_submit_budget | exact machine evaluation ledger·최근 scope별 drought·attempt/cycle | A/G: BLOCK/RECHECK/AI차단/최종 guard/submit/no-fill 보존. 기회 손실 증거를 기존 recheck family로 전달하되 drought 자체를 승인/차단의 단일 사유로 쓰지 않음 |
| sniper_missed_entry_counterfactual, entry_observation_source | buy intent·watch cycle·미제출 CF·가격경로 | A/G: main capture 우선 exact key, buy intent 이전 결손 포함; 종목명/시간근접·inferred terminal은 진단 전용 |
| sniper_entry_pipeline_report, intraday_entry_flow_report, intraday_entry_blocker_diagnostics, sniper_entry_latency | raw pipeline·stage/latency·promotion lineage | A/G: 처음 사라지는 모집단과 남은 blocker를 분리. 실제 정상 회복 fallback을 놓친 기회 또는 terminal veto로 중복 집계하지 않음 |
| market_opportunity_census/review, pruned_candidate_bbo_collector | 독립 상승 census·full prune·bounded BBO | A/G: scanner 밖 기회 분모·forward exact/SLA·master. bounded 관측 EV를 full-prune 전체로 외삽 금지 |
| scanner_lookup_attention_tuning, scanner_scheduler_replay | admission·budget·marginal CF와 실제 full-fill | A/G: 이미 있는 비노출 CF 유지, full population/자본예산·미관측 결손을 선정까지 연결. slot/source selection은 기존 family guard |
| rising_missed_*·one_share_threshold_opportunity·entry_hurdle_backtest | 미진입 관찰·기존 source-only opportunity | A/G: 실행가능성과 비용/상승 label 구분. 진단 prior를 BUY로 쓰지 않음. entry_ai_gate_backtest는 on-demand legacy 연구이며 compact regular owner 대체 금지 |
| daily_threshold_cycle_report dynamic_entry_price_resolver | observed price profile·exact completed PnL·cancel CF 진단 | F/G: 가격 계획 생성까지 도달한 미제출/미체결을 동일 모집단 replay. 기존 실현 성과는 monitoring/calibration anchor로 별도 유지 |
| position_sizing_allocator, entry_split_order_plan, entry_execution_sizing_plan | real/sim 분리·atomic qty/leg plan·four-arm executable receipt | A/G: 네 arm receipt는 이미 CF 검증 구조. receipt 생성 시 no-submit/no-fill 누락·직접/간접 submit predicate만 수리; atomic binder에 새 action/price authority 추가 금지 |
| strategy_owner_replay, main_lifecycle_paired/journal | policy-bound executable CF·actual fill/terminal/no-fill | A/R/G: no-fill 실제 상태 유지. actual quality는 not_applicable_no_fill, CF decision 경제성 companion과 같은 attempt로 join |
| entry_cancel_wait_tuning | 제출 후 대기·취소·호가/체결·CF timeout | A/G: 확인된 무체결의 기회비용·TTL·residual 비용. cancel authority와 entry price AI advisory/가격 owner 분리 |
| Widget advisory/mechanical/paired replay·widget_signal_quality | raw advisory·before_confirmation trace·BBO·bars | A/G: incumbent rejects도 기존 등록 candidate가 원래 입력으로 재판정. 두 정책의 union opportunity/capacity replay; AI-free widget에 main Provider 조건 추가 금지 |
| widget_advisory_calibration, widget_auto_trade_policy_calibration, widget_symbol_signal_policy_research | 시장 raw·paired calibration/holdout·incumbent | A/G: raw scope 누락과 선정탈락/무신호를 구분. candidate-specific signal/fill 모집단 평균이 아닌 공통 기회·일별 순익으로 비교 |
| widget_symbol_runtime_policy·policy apply·collector expansion | source readiness·selected study·exact-date family | G: W0–W7 source closure→paired selection→정식 guard→dated loader→receipt. 연구watch 등록을 실전 universe 승격으로 변경하지 않음 |
| machine_microstructure_attribution→machine_entry_timing_tuning→machine_microstructure_policy_approval | actual signal anchor·micro checkpoint·policy evidence | A/F/G: filled timing adapter 유지 + raw decision CF adapter 재사용. 실제 signal 없는 prospective anchor는 원래 signal로 위조하지 않음 |
| samsung_machine_entry_tuning·low_price_two_leg_tuning | actual-policy completed/HELD·local market study | A/R/G: 실제 실현/cohort 계산 유지; entry admission 후보는 기존 entry-spot/timing source-only child에서 연결. 무손절·목표유지 exit 계약 임의 변경 금지 |
| low_price_two_leg_entry_spot_research·samsung_morning_reentry_research | market bars·calibration/holdout·CF signal/legs | A/G: 이미 미진입 후보를 평가. 분봉 가격touch를 executable filled로 승격 금지; family 선택의 holdout 독립성·결측 처리 보완 |
| low_price_two_leg_expanded_candidate_research·low_price_two_leg_auto_expansion_policy | completed market bars·source-only CF signal/target·dated candidate | A/G: completed bar/CF leg는 실제 broker 체결을 뜻하지 않음. scope별 미입장/미완료 포함 분모·실제 자동family source/economic 경계 확인; 실전 universe 확대 승인 상속 금지 |
| market_weakness_hysteresis_tuning·market_weakness_threshold_policy | 기존 source report의 CF label/holdout·reviewed candidate | A/G: no-call/blocked signal의 opportunity가 원천에서 누락되는지 확인. source report→reviewed bounded candidate→dated policy 연결만 수리, 기계/AI action owner나 hard market veto 변경 금지 |
| entry_turn_point_replay·micro_reversion.counterfactual_entry_diagnostic·p2_replay·ai_stage_coverage_replay | raw promotion/blocked TP1·exact replay·미제출 진단/coverage | A/G: 기존 diagnostics/CF 중복 없이 재사용, 관찰단계 miss와 executable net outcome 분리. diagnostic output만으로 새 live owner 생성 금지 |
| pure_market_regime/reversal/adaptive_opportunity_replay | completed market bars·causal classifier·oracle CF benchmark | A/G: 이미 실제 거래 없이 기회를 연구. oracle은 진단 upper bound이며 automatic runtime/widget apply 금지 계약 유지; 기존 active owner의 별도 검증 없이 정책 발행하지 않음 |
| AVG_DOWN recovery·pyramid quality/feedback·scale_in_split_order_plan | 실제 holding 시작 후 ADD/NO_ADD 및 추가주문 CF | A/R/G: 같은 holding decision 모집단의 ADD opportunity도 조사. 최초 진입 후보와 합치지 않고 기존 scale-in action owner 수용조건으로만 선정 |
| holding_exit_*·sniper_post_sell_feedback·stop_loss_recovery_backtest·adaptive-exit attribution | 실제 holding/매도 이후 HOLD/EXIT CF | R/G: 보유가 있어야 함은 적정. 실제 terminal/비용과 exit opportunity를 분리하되 초기 미진입 모집단을 억지로 붙이지 않음 |
| strategy_position_performance_report·sniper_performance_tuning_report·execution receipts·trade fact | 실제 주문·체결·terminal·비용 | R: 실현 headline은 COMPLETED+valid profit_rate만 유지. 놓친 기회 CF는 별도 필드/분모, 합산손익 아님 |
| Pattern lab prepare/build_dataset·automation·AI review | 시장/거래 관찰·raw/paired·feature/label | A/G/X: active main pattern의 admission 원천 선택편향 조사. source-only 연구를 independent Entry AI/sim/retired bucket 승인 경로로 우회 금지 |
| EV/Daily cumulative·runtime summary/gap/lineage·tower·workorder/checklist·strict verifier | 상위 report/calibration·selected/blocked recommendation | G: 전체 cohort disposition·native ID·raw/economic/count 보존과 hash 확인. 요약 selected-only로 미진입 case를 탈락시키지 않음 |
| DuckDB/parquet/dashboard/archive·웹 route·runtime service | raw/파생 읽기 또는 정책·UI/실행 | R/G: 역할 분류 후 경제성 reader의 WHERE/join에 fill-only 숨은 filter 조사. UI/주문 service 자체는 정책 연구 producer로 확장하지 않음 |
| Swing/scalp sim·ADM/LDM/bucket·institutional·opening rotation·remote baseline 등 | historical/offline/raw compatibility | X: 전수 목록에는 남겨도 복원·정기실행·표본모집·현재 튜닝 분모에서 제외 |

## 6. 전체 기회 모집단·후행경로·비용 후 paired 평가

### 6.1 원천·기회·평가·주문 key를 구분

기존 source manifest와 row digest를 재사용한다. raw file path/logical hash/row hash/source date/as-of, owner/symbol/effective venue/session/connection epoch, 실제 signal_decision_at 또는 evaluation timestamp, promotion/attempt, machine policy hash, 실제 compact prompt/model/response hash, micro kernel/window cutoff·completeness, cost/master/exit contract hash를 보존한다.

기회 episode는 기존 census/prune/watch/signal owner의 선언된 crossing·TTL/reset을 사용한다. 반복 evaluation은 episode 안 attempt들로 남기되 opportunity EV를 매번 중복 계수하지 않는다. scanner opportunity key와 실제 평가6필드 key, broker order/leg/lifecycle key는 각자 유지한다. main/widget/episode·KRX/NXT/SOR route·세션을 심볼만으로 join하지 않는다.

과거 attempt/signal이 없으면 row digest는 진단 식별자로만 쓴다. 새 exact lineage 또는 실제 signal 시각으로 발명하지 않는다. 모든 capture를 보존하되 경제성 usable/failure reason을 따로 표시한다.

### 6.2 서로 다른 네 모집단과 두 결과

1. 시장/신호 기회: independent census 또는 기존 owner가 실제 관찰한 전체 signal/prune/watch. 관찰 안 된 시장 전체를 주관적으로 복원하지 않는다.
2. 기계 평가: SOURCE_INVALID/BLOCK/RECHECK/ENTER_NOW 전체. 정상 BLOCK도 진단 분모에서 제거하지 않는다.
3. AI 보조심사: 실제 ENTER_NOW 이후 prepared/called/trusted PASS/VETO/CAUTION/INSUFFICIENT_DATA 및 transport/schema fail. 기계 BLOCK/RECHECK에는 실제 미호출 사유만 남긴다.
4. 집행: 가격/수량 계획 준비→미제출→submit/reject→full/partial/no-fill/pending→holding/terminal. 제출이 없으면 broker 체결 join을 강제하지 않는다.

각 모집단에서 raw rows = deduplicated retained + duplicates/rejections, retained = economic complete + maturity waiting + censored/source gap + role-not-applicable의 배타적 합을 닫는다. stage간 expected/consumed/excluded/unmatched를 source hash와 scope별로 대사한다. attempt raw count와 unique opportunity count를 동시에 출력한다.

actual outcome: confirmed no exposure, submitted terminal no-fill, full/partial fill, HELD, terminal completed, unknown. counterfactual outcome: executable modeled fill+exit complete, supported modeled no-fill, not executable, censored/missing. 둘은 독립 필드다. actual no-fill이 CF no-profit이라는 뜻은 아니다.

실제 no exposure의 거래손익0은 주문/노출 부재가 확인된 경우만 가능하다. 실제 Provider 등 발생비용은 별도 차감한다. missing realized PnL/cost는 null. 미관측 CF fill/exit/cost도 null이며 가짜0원·합성체결 금지.

여기서 미체결은 내 주문의 무체결이다. 시장 전체 무체결/저유동성과 다르다. 시장 체결 tape·호가가 충분한데 내가 주문하지 않은 사례가 핵심 기회비용 원천이며, 내 broker fill 부재를 market-data stale 또는 경제성 label 부재의 근거로 쓰지 않는다.

### 6.3 경제성 판정의 공통 출력

기존 case table/paired_comparisons/source_metrics에 embedded opportunity evaluation을 추가한다. 새로운 DB·CLI·report producer·collector·timer를 만들지 않는다.

각 신규 metric은 기존 Metric Decision Contract에 맞춰 schema/version, metric_role, decision_authority, window_policy, sample_floor, primary_decision_metric의 실제 field/formula, source_quality_gate, forbidden_uses를 선언한다. CF expected-value field는 source_quality_adjusted_ev_pct 또는 notional_weighted_ev_pct 등 소유 계약으로 명명하고 actual realized headline과 구분한다. 단순 손익합은 EV라고 이름 붙이지 않는다.

출력 계약의 필수 의미:

- incumbent/candidate action과 fixed policy hashes; admitted/rejected/recheck/AI screened 여부 및 최초 blocker.
- 원래 guard의 정당성 증거와 후보로 회복되어도 남아 있는 next blocker. source-invalid 복구를 threshold 효과로 귀속하지 않음.
- executable entry/limit-fill/exit 모델·비용·window·data coverage·maturity deadline·품질 제외 사유.
- missed-profitable entry, correct risk avoidance, dangerous admission, unnecessary rejection, delayed opportunity, execution miss, transport/schema/source gap, unresolved. 정상 위험차단도 대칭 평가.
- recovered net opportunity와 added loss/tail, per-opportunity EV, attempted-notional net return, inclusive-source-day net profit, positive terminal frequency/time, participation, capital minutes, p10/drawdown. CF/actual 각각 suffix/source 표시.

관찰이 유효한 무기회일·0참여일·손실일은 일별 분모에 포함한다. 원천 missing인 날짜를 정상0으로 채우지 않는다. 모든 1/3/5/10/20/30/60분 horizon이 끝나야 label을 만들도록 하지 않고 family가 실제 선언한 exit/window의 completeness만 요구한다.

### 6.4 당시 입력만으로 재판정

incumbent와 challenger를 같은 frozen opportunity union에 실행한다. 선정 시 보지 못했던 실제 future high·first-hit·MFE는 action input이 아니라 label이다. 후보가 생성한 signal만 자기 EV 분모로 쓰지 않는다. calibration에서 grid·family를 고정하고 chronological holdout은 채택 확인에 한 번 사용한다. 반복 family 선택에는 다음 미사용 날짜 또는 별도 nested split이 필요하다.

기계는 현재 공유 decision function/kernel로 BLOCK/RECHECK/ENTER_NOW를 재산출한다. 정상 hard negative는 그대로이며 허용된 bounded threshold만 바꾼다. 모든 미진입을 한 번에 뚫는 relaxation grid는 금지한다.

AI는 actual ENTER_NOW의 동일 machine context+compact base+PASS/VETO auxiliary instruction을 사용한다. 실제 사용하지 않은 compact 정책에 legacy 원천을 incumbent 검증으로 붙이지 않는다. 기존 Provider checkpoint/budget 안에서 등록 후보 replay를 재사용하고 기계 BLOCK 전체에 새 AI 호출을 요구하지 않는다.

기계 후보가 기존 BLOCK을 ENTER_NOW로 바꾸더라도 실제 AI 호출이 없었다면 그 결과는 우선 upstream machine opportunity이며 end-to-end 제출/수익 회복이 아니다. 후보 ENTER의 정확한 당시 context로 기존 승인·budget·checkpoint 계약 안에서 offline compact replay를 수행할 수 있는 경우에만 modeled 보조심사 결과를 연결한다. 이를 실제 호출/실제 PASS로 재라벨링하지 않는다. replay 근거가 없으면 AI 및 후단 guard 통과 여부는 unresolved/null로 남기고 PASS를 가정해 최종 기대순익을 부풀리지 않는다.

CAUTION/INSUFFICIENT_DATA는 semantics를 VETO/PASS로 바꾸지 않고 실제 router의 미진입/재검사 동작을 재현한다. 경제적 opportunity label과 의미/전송품질 gate는 별도다. transport timeout/schema 오류의 놓친 기회는 운영비용으로 남기지만 모델 전략의 false VETO로 학습하지 않는다.

### 6.5 미체결·청산·비용 모델

fresh ask 즉시체결도 깊이·수량·spread·slippage·집행 지연이 유효해야 한다. passive 지정가는 가격touch만으로 full-fill을 만들지 않는다. 정확한 route/체결/잔량/queue 증거가 없으면 conservative feasibility 또는 diagnostic proxy로 낮추고 auto promotion eligible과 분리한다.

진입하지 않은 종목에는 실매도 receipt가 없으므로 기존 family의 연구용 exit 계약/timeout executable bid를 재사용한다. 이것은 실제 exit 계약을 변경하는 권한이 아니고, 시장경로가 충분하지 않은 HELD/무기한 target은 censored로 유지한다. 분봉 하나의 고가/저가 순서는 알 수 없으면 ambiguous이다.

비용은 해당 family effective-dated fee/tax/spread/slippage·cost/master hash를 사용한다. R0–R3 비교의 고정 비용은 별도 계약대로 유지하며 broker 실제비용과 바꾸지 않는다. Provider cost는 실제 screen 또는 선언 replay 모델에서만 차감; machine-only에 AI비용을 붙이지 않는다.

모든 후보는 같은 원래 quantity/cap/account budget과 fixed exit를 사용한다. 겹치는 symbol/episode·cooldown·동시자본·시간창을 replay하여 동시에 못 잡는 기회를 모두 합산하지 않는다.

### 6.6 기대효과와 손실함수

미진입 기회비용 = 유효한 동일 기회에서 사전 등록된 실행가능 대안의 modeled net payoff − incumbent modeled payoff. 양의 부분은 놓친 이익, 음의 부분은 회피한 손실로 따로 표시한다. hindsight oracle 최선진입은 진단 상한일 뿐 후보 선정·예상수익으로 사용하지 않는다.

선정 주목적은 공통 기회/자본 제약 아래 modeled net profit/source day 또는 해당 family의 기존 primary EV 개선이다. 작은 수익 빈도·참여율은 tail/순이익 비훼손 조건의 보조목표다. 기대효과는 회복 가능한 미진입 수·후행순익·added loss·원천coverage로 정량 예상하고, 자연 실현수익 개선과 동일시하지 않는다.

예: A가 후보로 회복되어도 unchanged liquidity guard에서 막히면 recovered executable trade가 아니다. B가 정책상 통과해도 주문가격/TTL 때문에 no-fill이면 가격/집행 후보의 기회비용이다. C의 VETO를 PASS로 바꿔 얻는 +작은 순익과 D의 신규 손실을 함께 차감해야 AI 후보 개선이다.

## 7. 기존 정책 생성·자동 적용의 구체적 변경

### 7.1 Main 기계·AI

#74는 이미 독립된 machine/source attempt admission을 유지하고, AI screen label admission과 AI PASS operational conservation의 현재 결합을 분리한다. PASS가0일 때 operational 상태는 no_pass_population일 수 있지만 AI VETO 연구를 전체 중단시키는 근거가 아니다. 기계 BLOCK 연구에도 이 조건을 새로 붙이지 않는다. PASS 이후 exact unresolved row는 실제 효과/전환과 policy learning에서 역할에 맞춰 제외한다. raw count와 결손은 계속 남긴다.

#82 common refinement는 machine natural usable rows를 기존 detailed paired adapter와 함께 정규화하되 중복 source/attempt를 제거한다. 현행 incumbent policy로 동일 rows를 재판정하여 delta 계산한다. hierarchy runtime extension은 이미 natural source를 소비하므로 이 연결을 유지하면서 parent threshold hash와 scope/holdout을 고정한다.

compact case table→등록 prompt variant 선택→mechanistic_entry_runtime_policy publisher→activation projection→dated policy/PREOPEN→loader→PID receipt에 동일 경제성 계약/source partition을 전달한다. 다른 prompt/model/hash 세대는 관측·연구로 격리하고, 현재 적용 compact를 legacy result가 덮어쓰지 못하게 한다.

U7/U8 연구 병행은 서로 다른 조작축을 같은 entry stage에 무조건 동시 적용하는 권한이 아니다. 최종 선정은 기존 same-stage owner/canary·family의 조작점/적용시각/rollback 계약을 따른다. 여러 축을 함께 바꾸려면 기존 승인된 bounded bundle/multi-arm 계약이 실제로 존재하는지 확인하고, 없으면 해당 stage의 단일 후보만 적용하며 다른 후보는 연구/다음 선정으로 유지한다.

### 7.2 가격·수량/leg

가격 평가 모집단은 **기계+AI/원래 authority가 통과했고 원래 가격 계획 입력을 만들 수 있었던 기회**다. BLOCK 종목에 주문가격을 발명해서 가격 owner 탓으로 돌리지 않는다. downstream source/account guard 불통과는 별도 원인이다.

daily_threshold_cycle_report의 existing profile grid 안에서 incumbent와 등록 numeric candidate를 같은 executable opportunity에 replay한다. confirmed cancel/no-fill을 CF 경로와 join하고 missed_upside null 상태를 근거가 있는 경우에만 해소한다. 실제 COMPLETED 평균은 real monitoring 지표로 유지하지만 recovered-entry/낮은 참여 후보의 선정 주근거로 쓰지 않는다.

publisher의 fixed20/EV0.1%와 evaluator/후행 family validation을 한 contract에서 대사한다. 개선 제안은 절대0.1%를 보편 수익 floor로 유지하기보다 **비용 후 양의 기대값+동일모집단 대비 개선+stress/tail 비훼손**을 쓰는 것이다. 실제 numeric 기준 변경은 기존 권한·근거·회귀검증을 확인한 후 구현하며 이 문서가 임의 floor 변경 receipt는 아니다. 표본20 자체는 충분성 근거/유입 가능성을 확인하고 raw CF eligible을 수용하되 후보의 사전 실체결20건을 새 요구조건으로 추가하지 않는다.

현재 Plan Rebase §5/§7에도 비용후0.10% 기준이 존재한다. 따라서 절대 floor 재설계는 현행 계약이 아니라 제안이며, 승인된 구현에서 owning contract 변경과 관련 운영문서 정합화를 함께 닫아야 한다. 소스만 낮추고 상위 계약은 그대로 남기거나, 이 계획을 근거로 현재 runtime floor를 변경하지 않는다.

수량/leg는 existing four-arm evaluator를 재사용한다: incumbent qty×incumbent leg, candidate qty×incumbent leg, incumbent qty×candidate leg, candidate qty×candidate leg. 동일 opportunity/price/cost/exit/capital contract에서 complete4군을 평가하고 no-fill도 지원된 모델일 때 포함한다.

atomic entry_execution_sizing_plan은 이미 승인된 quantity/split/price를 결속하는 binder다. 이를 새 action 선정기로 바꾸지 않는다. Daily가 quantity·split hash와 selected arm을 묶어 기존 PREOPEN dated loader로 전달하며 quantity conservation/cap/safe budget/scale-in owner 경계를 유지한다.

### 7.3 Widget·episode 및 기타 family

2026-09-17 추가 코드 점검: [정책 연구 로직 리뷰](../audit-reports/2026-09-17-widget-episode-policy-research-logic-review.md). 분봉/paired CF 연구가 이미 있는 경로와 actual-only timing adapter를 구분한다. U10A에서 raw opportunity union·실행가능성·source-day/자본 계약을 확인하고, 최초 EV 탐색과 총 순익 목표의 차이는 기존 component/paired guard를 보존한 채 검토한다. [장후 계산 최적화 3후보 계획](postclose-computation-optimization-implementation-plan-2026-09-17.md)은 별도 계산 후속이며 작성 완료가 구현·배포·자연 정책·수익 acceptance를 뜻하지 않는다. 기존 U10A/B owner를 중복 생성하지 않는다.

Widget paired replay의 before_confirmation trace/BBO loader를 미진입 timing adapter에 재사용한다. source-only 경제성 outcome의 modeled terminal과 실제 owner_outcome.realized를 분리하고, actual adapter의 실체결 검증은 삭제하지 않는다. 모든 raw signal이 정책 anchor인 것은 아니므로 실제 decision anchor·incumbent reject·diagnostic prospective를 명시한다.

entry-spot/reentry의 minute-bar proxy 후보는 raw exact feasibility를 확인하기 전 자동 실전 승격 자료가 아니다. 기존 삼성/저가주 admission·source day·baseline/holdout 계약을 각각 유지한다. 위젯 signal/target과 entry-timing을 같은 stage에서 중복 변경하지 않는다.

scanner/recheck/ADD-NOADD/exit family에서도 raw/미노출 CF가 existing candidate 생성으로 연결될 수 있으면 같은 보존·paired 비교를 적용한다. 다만 보유가 필요한 scale-in/exit 평가의 holding 조건은 제거하지 않는다. OFF/퇴역 producer의 raw 호환 reader는 current optimization으로 복원하지 않는다.

### 7.4 달성 가능성·불합리한 gate 검토

| 조건 | 유지/보완 판단 | 구현 acceptance |
| --- | --- | --- |
| exact route/source hash·past-only·cost·holdout·authority·owner | 유지 | 부족 row를 제외하고 census에 사유 유지; 전체 block은 전제 계약 결손일 때만 |
| AI PASS downstream terminal 1건 이상이 모든 판단 연구의 전제 | 제거/분리 대상 | all BLOCK 또는 all VETO fixture에서도 유효 CF 연구 가능, 운영보존 검사는 독립 |
| 미진입 후보가 실거래로 먼저 체결되어야 후보가 될 수 있음 | 순환조건 제거 | declared source-only modeled complete pair로 연구/정식 자동계약의 후보 gate 평가 가능 |
| 실제 completed 손익·실제 주문 no-fill 비용 검증 | 유지 | actual headline에서 CF0/CF수익으로 대체 금지 |
| 가격의 절대 비용후0.1%를 일반 승격 minimum으로 사용 | 재설계 대상 | 소액 양수 개선·tail 통과 후보를 이유 없이 배제하지 않음; evaluator/publisher/PREOPEN 동일 기준 |
| sample floor/관측일 | family별 근거 검토 | 0유입/impossible join을 대기라고 하지 않음. 공통5/10/20일 동시gate 또는 새 universal uplift 금지 |
| 모든 horizon의 후행 관측 또는 미승인 실제 exit 성공 | 추가 금지 | 기존 연구용 exit/window만 complete면 해당 연구 판단 가능; live 활성화와 분리 |
| 후보별 사용자 재승인 | 기존 자동계약에는 추가 금지 | approved bounded candidate는 기존 publisher/PREOPEN/loader가 선택. 새 safety/provider/universe 권한은 자동 상속 안 됨 |

## 8. 통합 일괄 작업지시 U0–U12

후속 일괄 구현 요청은 아래 전체를 intake하되 작업은 package별로 분할한다. 각 단위에서 **구현→self review→finding별 수정→re-review→targeted validation**을 반복하고 unresolved finding을 남긴 채 의존package를 완료시키지 않는다. shared schema와 calibration/Daily/shared WS 파일은 한 편집owner가 관리하며, 같은파일의 다른세션변경이 들어오면 영향package와closure를 재검증한다.

| 통합 package | 기존 계획 대응 | 주요 선행 |
| --- | --- | --- |
| U0 전수inventory/환경·공식contract 고정 | C0 + OC0 | 없음 |
| U1 공통facts/state | C1 | U0 |
| U2 adapter/원천 투영 | C2 | U1 |
| U3 main/scanner/AI 등 | C3 | U2 해당scope |
| U4 독립owner/collector/micro/web | C4 | U2 해당scope |
| U5 latency/read/evaluation 예산 | C5 | U3/U4 해당scope |
| U6 raw분모·role별quality/terminal gate | OC1 + C6 downstream 호환 중 해당부분 | U0; U1과병행 |
| U7 기계threshold/hierarchy | OC2 | U6 + 유효scope원천 |
| U8 compact AI missed opportunity | OC3 | U6 + 실제ENTER/currentprompt원천 |
| U9 가격/수량·leg/미체결 | OC4 | U6 + incumbent-passed price-ready원천 |
| U10A/B widget/episode 및 기타active family | OC5 + OC6 | U6 + 해당scope원천/필요Widget sourceclosure |
| U11 자동policy handoff·gate 합리성 | OC7 | 해당U7–U10 validation |
| U12A closure/U12B 허용release/PID | C6/C7 + OC8 | §2.2의H scope 또는전체범위 |

이 매핑은 이전task 이름의대응표이지 신규native ID·OPEN·예정owner가 아니다. 이전C/OC task가 이미검증완료이면 직접consumer/currentgeneration을확인해해당U receipt로대사하고, 같은작업을다시구현하지 않는다.


### U0 — live/raw 소비자 전수 계약·공식 reference·환경 고정

- 대상: §5.1 장중 callsite와 부록 A 전체 파일, 기존 producer registry·report 계약·deploy 호출, 관련 SQL/DuckDB/pandas filter와 API runtime adapter.
- 작업: 실제 raw/derived/policy/archive/OFF 여부, source path/loader/function, WHERE/join/predicate, admitted/excluded/0 stage, report→candidate→publisher→loader를 파일/함수별 표로 확정. 간접 import와 동적 report path도 역추적한다.
- 출력: 이 계획의 inventory 표 또는 동일 구현 audit의 명시적 전수 ledger. 코드에 독립 census producer를 만들지 않는다.
- acceptance: 실제 raw 소비자 미분류0, active tuning/policy 소비자 미추적0. I/O-only 미검토 파일을 완료로 세지 않음. 이미 있는 missed CF 경로를 중복 구현하지 않음.

- 공통 보완: src/utils/scanners 및 src/trading/market/order, tools client, deploy launcher의 직접POST·alias/주입getter·file/passed-frame까지 전수 대사한다. account_order_only/history/transport/OFF도 분류하며 조사에서 누락하지 않는다.
- 구현 전 Official Kiwoom Reference Gate를 수행하여 현행 upstream SHA/조회시각/inspected paths·REST/WS 문서/spec/Postman을 기록한다. protocol 미정의/conflict는 raw/null과 contract gap으로 남긴다.
- 고정: 작업본 HEAD/diff/hash, 다른 세션 변경, selected release/current PID root, stage TTL/authority/승인override, existing policy/metric contract. 신규 raw 수집기·독립 inventory 프로그램 금지.
- 추가 acceptance: 장중 callsite/source→adapter→consumer와 raw→candidate→publisher 미분류0. 정적search/AST coverage·offline parity·actual PID 자연coverage는 별도 상태.


### U1 — 공통 source facts/health·quiet state

- 의존: U0의 소유/공식contract 고정. U6와 병행 가능하되 shared metadata/schema를 먼저 합의한다.
- 대상: quote_consistency, market_data_cache/quote_health, kiwoom_websocket의 기존 helper/cache/callback.
- 작업: 0B/0D/provider/receive/consume 시각 분리, route/session/epoch/type identity/continuity, 10초공백/3episode 반복을 기존 state에 결속한다. getter는 무부작용이며 timeout·future·late·drop을 가짜fresh로 만들지 않는다.
- acceptance: 9.999/10초·긴30초공백·동일frame100회·세episode·정상활동reset·first-data/epoch/drop 경계 parity, common market→engine 역의존/network callback0.
- 테스트: 기존 quote consistency/market cache/websocket tests. 10초는 engineering 제안값이고 quote/submit/micro TTL 변경값이 아님을 검증한다.

### U2 — WS/REST/direct-client·writer/reader adapter 전수 결속

- 의존: U1.
- 대상: kiwoom_utils, kiwoom_episode_read_control, direct episode gateway/KiwoomReadOnlyClient, market_data_enrichment, 기존 snapshot writer와 file reader.
- 작업: 호환 dataclass/return/envelope에 같은 health를 전달한다. REST API별 source 의미·route·response시각/cache provenance, WS quiet state를 보존한다. REST-only는 독립repeat counter를 만들지 않는다.
- acceptance: 직접/우회client metadata 탈락0, file capture/serialize 시각으로 fresh화0, minute/history/account/auth/order에 trade activity 적용0, legacy adapter 명시적동등/parity 또는unproven.
- 테스트: 기존 kiwoom/utils/episode read-control/enrichment/collector tests. request/parser/FID/REG 변경은 U0 reference 근거와 protocol regression을 확인한다.
- 검증된 부분 전달: 기존 WS dashboard writer의 bounded type projection에 transport epoch·0B provider clock·quiet observation 원시각을 보존한다. 공통 owner가 raw route/file projection을 같은 함수로 소비하며 capture 시각·이전 health companion으로 fresh화하지 않는다. 이 전달과 micro/web 소비 parity는 U2 전수 direct REST/client 전환 완료를 대신하지 않는다.
- writer worker의 consume 시각은 callback launch가 아니라 lock 아래 두 view를 고정한 뒤 기록한다. source가 launch 뒤 수신돼 가짜 future age로 보이지 않게 하되 원 receipt clock·주기 제어·callback lock·atomic publish는 유지한다.

### U3 — main/scanner·기계/AI·price/sizing/holding consumer 전환

- 장중 관측 보완: 일반 `watching_analyze_target`에서 handler 시작 시 current/tape 1.55초·BBO0.98초였던 입력이 준비3.33초 뒤4.88/4.31초로 stale 전환됐다. U3/U5의 기존 작업 안에서 history/context 준비 완료→로컬 최신 WS 단회 재취득→기존 `revalidate_entry_candle_snapshot`→기계/AI 판정으로 연결한다. async evaluation도 실행 직전 같은 처리와 같은 frame의 prepared handoff를 유지한다. source별 원시각/route/epoch/완성봉·optional 원천을 보존하고 새 snapshot에 없는 tape를 과거 REST로 메우지 않는다. 기존 입력 age 계약으로 취득하되 최종 submit TTL/guard는 별도 유지한다. 새 collector/API/Provider 호출·장후 작업·3초/700ms 완화·가격/수량/scale-in owner 변경은 없다. missing/malformed 계약·route 변경·역행 clock은 기존 canonical preflight에서 차단하고 refresh/준비 age/error를 기존 이벤트에 보존한다. 최종 자연 검증은 같은 attempt의 queue/start/preflight와 source별 observed_at을 연결하며, input freshness 회복과 수익·제출 개선을 구분한다.

- 의존: U2의 해당scope adapter.
- 검증한 구현 closure는 일반 WATCHING과 async WATCHING 실행 직전 로컬 재취득/재검증·immutable execution frame 전달이다. 기존 coordinator의 선택적 refresh callback은 queue 대기 뒤 실행 직전에 수행하고 같은 고정 frame을 평가·결과·최종 commit에 보존한다. refresh 오류·malformed 반환·deadline 초과·generation 취소는 Provider 호출 전에 차단한다. 원 준비/generation frame은 덮어쓰지 않으며 commit의 현재 quote/state/position/cooldown guard는 별도 유지한다. 자연 async receipt와 전수 consumer migration은 아직 잔여다. 10초/3episode는 trade activity 계약이며 기존 3초 입력 freshness·최종 submit700ms·micro1초를 일괄 치환하지 않는다.
- 대상: kiwoom_sniper_v2/scalping_scanner, sniper_state_handlers/analysis, ai_market_snapshot/preflight, entry_setup_evidence, feature/context, orchestrator/latency/scale-in/holding passed frame.
- 작업: 독립 freshness 추정을 위임하고 quote/tape/transport/local lag·required feature 이유를 분리한다. atomic frame/attempt/promotion/정책hash를 다음stage로 전달한다. 공통health가 action/threshold를 변경하지 않는다.
- 소비 계약 보완: canonical snapshot은 기존 공통 `build_market_data_health`에 원래 WS route receipt를 전달해 현재 consume 시점의 facts를 받는다. 이전 envelope의 health를 신뢰하거나 소비자가10초/공백 횟수를 재계산하지 않는다. 동일 item/route/venue/type 시각·epoch/연속성이 결속된 정상 체결공백의 `current_price_stale/tape_stale/source_time_skew`는 source 손상과 분리한 `required_feature_*` 부족이다. source/feature gate를 분리하되 최종 `allowed`는 둘 다 만족해야 하며, 오래된 tape 값·원시각·quality는 그대로다. feature-only 미판정 receipt는 `RECHECK/WAIT`·Provider 미호출로 보존하고 실제 missing/conflict/quote 및 runtime artifact 실패는 기존 source/runtime 차단이다. late confirmation recheck도 source뿐 아니라 전체 preflight를 확인해 feature 우회를 막는다. 기존 #11/#74의 expected attempt 보존식은 feature-before-assessment를 별도 제외 분모로 소비해야 한다.
- 필수 회귀: `공백5/9.999초+fresh0D+정상 관측`은 공통 `RECENT_TRADE`와 일치하고 전체 `SOURCE_INVALID`로 라벨링하지 않는다. `10/30초`·서로 다른3episode·같은 frame 반복·새 trade/epoch 복귀를 공통 facts와 대사한다. 필수 현재 feature가 부족하면 여전히 미진입/AI 미호출이며, stale/crossed quote·cross-epoch·route/clock/continuity 결손·변조 companion은 source 차단한다. snapshot→ai ops/tick event→trace→#11/#74가 상태/원시각/분모를 보존해야 한다. 이 회귀나 한 helper 적용만으로 U2~U4의 전수 adapter/file reader/독립 owner 전환을 완료로 판정하지 않는다.
- 자연 관측 후 보완: `_AL/krx_nxt_integrated`의 동일 item/type/epoch 관측 범위는 underlying event venue UNKNOWN과 별개다. 공통 health는 integrated scope를 증명하되 실제 거래소를 추정하지 않는다. canonical SOR view도 기존 KRX regular 시간창·candle·stage/broker 계약 안에서만 이 facts를 소비하며 old tape quality/feature 차단을 유지한다. scanner subscription recheck는 공통 경로가 정상인 required trade feature 대기를 재등록 필요와 분리한다. entry feature TTL·warm reactivation/new source·최종 quote/submit guard는 그대로다.
- acceptance: source-time skew/current_price/type provenance의 원인 구분, 동일input health parity·consumer TTL 유지, quote-only 변화로 판단 가능한 경로의정상복귀, PASS/SAFE/CAUTION/DANGER의 기존 집행contract 유지.
- 테스트: 기존 ai_market_snapshot/entry_setup/scanner async bridge/orchestrator/holding 관련tests; actual source collection→#11/#74/#76/#119의 metadata 전달 테스트.

### U4 — widget/episode·micro·exit·web/외부client 소비 전환

- 의존: U2의 해당scope adapter. U3와 분리 수행 가능; schema를 fork하지 않는다.
- 대상: §5.1.2의 gateway/machine/service/preflight, advisory/collector/file micro kernel, 기존 adaptive exit source/runtime, web routes/Telegram/tools client.
- 작업: injected/direct read·snapshot reader도 공통 health를 소비한다. 원래 signal/target/수량/보유·manual custody·SELL guard를 유지하고 micro past-only1초 validity는 기존kernel로 판정한다.
- acceptance: active role별 direct/pass-through missing0, 계좌/주문/취소/보유·terminal 확인 지속, crossowner/route/epoch 흡수0. quiet를 trade backing/refill 증거로 보간0; 신규 exit enrollment0.
- 테스트: 기존 widget/episode gateway/collector/dynamic micro/entry adverse/target pressure/profit stagnation/exit source tests와 표시client 호환검증.

### U5 — latency·중복 read/refresh·scheduler 감시예산

- queue14.29초 표본은 앞 handler12.27초의 직렬 점유와 함께 관측됐으나 뒤 handler 실행 전 snapshot 갱신도 있었다. queue 전체를 stale의 직접 원인으로 합산하지 않는다. 원천이 시작 전부터 stale인 사례와 준비 중 fresh→stale 전환을 분리하고, 기존 stage receipt로 queue·history/context·Provider·최종 source age를 대사한다. 먼저 U3 최종 로컬 재취득 비대칭을 닫으며, 광범위 scheduler 재설계/실주문 floor 완화나 동일 원천의 반복 replay로 대체하지 않는다.

- 의존: U3/U4의 해당scope health/frame 연결. 공유 TTL/identity가 고정되기 전 무조건 caching하지 않는다.
- 대상: sniper_entry_latency/MarketDataCache, existing market/shortTTL/sameMinute caches/read control/coordinator와 request class callsite.
- 작업: same payload single-flight/짧은TTL·same frame/policy/attempt pure evaluation reuse, freshWS 시 불필요REST 생략, failure/defer receipt sharing, 기존source wakeup/park/reservation 반환을 수리한다. wire fetch와 owner decision은 별개다.
- acceptance: 동일payload 동시read1 transport·same frame1 in-flight, new0B/0D 적정wakeup·deadline/noorphan, submit전freshness 재검증 유지, sharedlimit/source-only예약/criticaldeadline/retry불변. 화면fallback과 BUY직전/account조회 purpose class를 분리한다.
- 테스트: route/tm/date/origin/account/continuation/deadline/late-result singleflight, enqueuefail/reconnect/backoff와 observer원시각 tests. 해당scope recorded before/after 호출수/queue progress를 비교한다.

### U6 — 공통 모집단·quality·terminal gate 분리 (U1과 병행)

- 의존: U0의 source/consumer 분류. U1과 schema/facts 계약을 먼저 고정하되 U1–U5 전체 완료 또는 새 정책의 선승격을 요구하지 않는다.
- 대상: ai_decision_quality, observation_source_quality_audit, buy_funnel_sentinel, existing entry_observation_source.
- 작업: §6 필드와 배타적 counts/row disposition, source-date/hash·attempt 보존, machine/AI/operational gate 분리. synthetic terminal/weak key는 진단 전용.
- acceptance: full BLOCK, full VETO, PASS 뒤 final guard terminal, PASS lineage gap, missing artifact 각각 기대 분기. source-quality 없으면 경제성fail closed, 단순 PASS0으로 연구 금지 안 됨.
- 테스트: 기존 test_observation_source_quality_audit, test_ai_decision_quality, test_buy_funnel_sentinel 계열과 source adapter 테스트.

### U7 — 기계 natural 전체 모집단→common/hierarchy threshold 선정

- 의존: U6 + 해당 scope의 검증된 원천. U3의 새 health 연결 또는 동등성이 확인된 기존 frozen 원천을 사용한다.
- 대상: ai_action_outcome_calibration의 existing refinement/hierarchy 함수, entry_setup_evidence.
- 작업: natural rows+paired rows 정규화·중복제거; shared current incumbent 재판정; BLOCK/RECHECK의 executable recovered/loss 비교; stage별 incumbent policy parent 고정.
- 상충 원천 보완: 같은 exact6 attempt의 decision/outcome 본문 상충은 첫 행부터 모두 학습 제외하고 paired 별칭도 우회하지 못하게 한다. 위치·count가 독립 대사된 상충만 row 단위로 격리하며 정상 scope의 미진입 연구는 유지한다. 외부 상충 count에 위치 근거가 없으면 natural lane은 fail closed한다. [부분 구현 리뷰 §16](../audit-reports/2026-09-17-common-health-opportunity-cost-scoped-implementation.md#16-기계ai-상충-attempt의-행-격리와-자동-선정-전달-보완)를 따른다.
- acceptance: submitted0이면서 raw CF valid인 cohort도 후보 연구 가능. 유리한 진입일만 남긴 후보/unsafe guard relaxation/ambiguous future touch는 승격 불가.
- 테스트: 기존 test_ai_action_outcome_calibration 및 shared machine policy tests; 동일6필드·동일입력 action/metric parity.

### U8 — compact AI 보조심사의 false-negative·위험회피 대칭 환류

- 의존: U6 + 해당 ENTER_NOW/compact scope의 검증된 원천. U7과 공유 calibration 파일은 순차 관리한다.
- 대상: calibration case table, ai_quality_bridge/cycle/replay, optimizer/consumer, mechanistic_entry_runtime_policy 등록variant selector.
- 작업: PASS/VETO와 router 의미의 CAUTION/INSUFFICIENT outcome 보존; machine ENTER만 economic screening 분모; all VETO 해석; 현재 compact hash/role partition guard; transport/schema 별도.
- acceptance: profitable VETO·correct VETO·dangerous PASS·transport fail를 서로 구분. machine BLOCK에 가상 AI 호출/응답 없음. legacy prompt 결과로 current compact policy 자동 overwrite 불가.
- 테스트: 기존 compact/runtime policy·main_ai_prompt_optimizer/consumer·paired replay contract tests, provider mocking. 자연 Provider 호출은 구현테스트에 필요 없음.

### U9 — 가격·수량/leg의 no-submit/no-fill 경제성→Daily publisher

- 의존: U6 + 해당 가격/집행 scope의 검증된 원천. 초기 action은 검증된 현재 incumbent로 고정하며 U7/U8 새 정책의 선승격을 요구하지 않는다.
- 대상: daily_threshold_cycle_report grid/materializers, entry_split_order_plan four-arm, strategy_owner_replay, position_sizing_allocator, entry_execution_sizing_plan, main_lifecycle_paired.
- 작업: incumbent-passed price-ready 분모/가격 replay/no-fill CF join; absolute EV gate 타당성 및 중복 검사 통일; atomic four-arm receipt source 누락 수리; actual/CF 지표 분리.
- 4군 선정 증거 보완: 새 평가 계약 `quantity_leg_chronological_paired_v2`는 immutable receipt 안의 source-date로 calibration/최신일 holdout을 분리하고 동일 4군·비용/exit/terminal을 대사한다. 전체 기존30건/coverage80%를 유지하되 partition마다30건이나0.10%를 추가 요구하지 않는다. 각 partition은 비용 후 양수·incumbent 대비 개선·빈도/자본효율/tail 비훼손·fill 하락5%p 이내를 검증한다. Daily publisher→PREOPEN→runtime이 같은 evidence의 분모·partition digest 보존식·유한 metric·현재 정책 결속을 독립 검사한다. source9/17부터 proof 없는 신규 원자 정책의 legacy downgrade를 금지하며 기존 frozen 정책은 보존한다.
- 위 새 선정 계약의 배포를 natural quartet 생성·미진입 price CF adapter 완료로 대체하지 않는다. 기존 raw consumer의 4군 receipt 실제 생성/서명 date·직접 전달 결손과 가격의 절대0.10% 재설계는 잔여다. event 외피 날짜나 terminal 날짜로 signed source date를 합성하지 않는다.
- 원천 전달 보완: 기존 owner 발급 price/sizing plan의 hash·schema·exact attempt/scope·quantity 보존을 검증하여 기존 미진입 후행 보고서와 Daily compact reader에 전달한다. 중복은 최초 anchor를 유지하고 상충은 격리한다. 원래 계획 qty를 virtual sizing으로 대체하거나 probe 잔량의 미래 가격을 만들지 않는다. 분봉 결과의 economic pair는 미충족이며 CF notional/PnL null·watch EV 제외를 보존한다. 이는 no-submit 원천 전달의 보완이지 executable no-fill/exit/cost quartet 생성 완료가 아니다. [부분 구현 리뷰 §15](../audit-reports/2026-09-17-common-health-opportunity-cost-scoped-implementation.md#15-owner-발급-price-ready-계획의-기존-미진입-보고서daily-전달-보완)를 따른다.
- acceptance: completed 성과가 좋아도 참여/전체순익이 나쁜 가격 후보 탈락. 비용 후 작은 개선 후보가 절대0.1% 또는 사전candidate실체결 때문에 영구 대기하지 않음. leg·qty·price 후보가 action owner/scale-in/cap 변경 못 함.
- 테스트: 기존 Daily/position sizing/entry split/execution sizing/strategy owner/lifecycle paired tests. complete4arm hash·partial/no-fill/late-fill·cancel overlap fixture.

### U10 — 독립 owner와 남은 active family

#### U10A — Widget·episode admission/timing 미진입 adapter 연결

- 의존: U6 + 해당독립scope의원천검증. U4연결 또는입증된기존원천과Widget source plan의필요한W0–W7 closure.
- 대상: widget_paired_policy_replay/calibrations/signal research, machine_microstructure_attribution, machine_entry_timing_tuning, entry-spot/reentry research 및 existing approval.
- 작업: raw-before-gate opportunity union, actual/source-only outcome adapter 분리, common1초 window/실제signal/hash, capacity/exit 계약; holdout family 고정.
- acceptance: raw valid no-order signal이 CF 평가에 들어감. 실제signal 없는 diagnostic는 정책 표본 제외. future touch/부족level/cross epoch/신호+target동시 변경은 자동 후보 금지. 원래 수량/target/무손절 계약 유지.
- 테스트: 기존 widget paired/mechanical replay·symbol research·machine timing/attribution·entry-spot/reentry/approval tests.

#### U10B — 남은 active raw 기반 family의 선정편향 정합화

- 의존: U0/U6.
- 대상: scanner lookup/census/prune, recheck, cancel-wait, rising-missed/one-share/active Pattern, AVG_DOWN/PYRAMID/holding-exit 각 소유 평가기.
- 작업: ledger에서 실제로 확인된 fill-only 선정편향/미진입 join 누락만 수리. 이미 대칭 CF가 있는 family는 보존식/consumer 검증으로 닫는다.
- acceptance: 모든 active tuning/candidate row의 disposition 근거. holding/exit의 적정 fill 조건은 유지, OFF reader는 X. main 초기진입과 독립 scale-in/exit의 승인 계약 혼합0.
- 테스트: 수정된 family의 기존 targeted suite만; 전체 trading/퇴역 sim 테스트를 무조건 실행하지 않는다.

### U11 — 자동 policy handoff·조건 달성 가능성·요약 전수 closure

- 의존: U7/U8/U9/U10 중 해당 family의 수정된 평가기·publisher 직접 의존 변경 검증.
- 대상: existing runtime policy publisher, Daily, threshold_cycle_preopen_apply, family apply/dated loader, runtime verify·EV/summary/gap/lineage/tower/checklist/strict verifier.
- 작업: full-population metric schema/source hash/holdout/owner/selected disposition를 마지막 소비자까지 연결. 각 gate 입력·실제predicate·reason·유입률·가능 최대표본·다음경계 기록.
- acceptance: eligible candidate 자동 발행→PREOPEN 선택→loader hash 검증 경로가 테스트로 재현되고 manual env/후보별 재승인 없음. noEligible는 valid carry/hold, missing consumer는 실패. gate ETA는 무유입/구조결손이면 null+원인이지 무조건 내일 기대가 아님.
- 테스트: 기존 PREOPEN/runtime policy/approval/verify 및 summary-handoff/parser contract tests.

### U12 — scoped/전체 fixed-point 리뷰와 허용된 release/PID 검증

#### U12A — review·작업본 validation closure

- 전체 완료 의존: U0–U11의 전수 disposition. 중간 H closure는 배포범위 U0–U6의 관련 package와 모든직접downstream 의존 변경만 scoped 검증하되 나머지는 pending으로 남긴다.
- 작업: producer→adapter→consumer→raw label→candidate→publisher→dated loader의 교차scope/소유/보존/hash/silent-fail/authority·동시작업·same-stage mutation을 리뷰한다. finding 수정 후 영향경로를 재검증하고 eligible actionable defect0까지 반복한다.
- acceptance: reviewed 범위 P0–P2 미해결0, static/AST 잔존판정 전수분류, live health missing0, 해당raw/active candidate 미분류0, targeted pytest/compile/필요shell contract/diff check PASS. scoped PASS를 전체구현완료로 바꾸지 않는다.
- 같은generation checkpoint/frozenpolicy를 보존한다. 테스트Provider mocking·offline fixtures를 우선하고 비싼report/실API/restart는 review/권한 확인 전 금지한다.

#### U12B — 승인된 follow-up만 release/actual PID

- 의존: U12A의 같은 code generation 검증 + 대상commit/push/managed release 선택/기동의 실행권한. 현재계획작성은 실행하지 않는다.
- 작업: §10의 작업본→검증commit→managedrelease→release-local 재검증→필요owner만 기동→policy/PID/WS/custodyreceipt→자연coverage를 수행한다.
- 공통H는 자연경제성/후보E를 기다리지 않고 승인범위로 먼저 배포할 수 있다. 전체통합release는 U0–U11 전수closure를 재검증한다. 다른세션변경/구PASS/mtime만으로 새release를 선택하지 않는다.
- acceptance: 검증source/hash와 실제release 일치, current PID root/import/policy/date/provenance 확인, 기존미체결/전시장inventory·manual/독립owner보존, WSlogin/REG/type firstdata 또는명시적인자연미관측. 자연submit/수익은 별도판정.


## 9. 필수 회귀 테스트·결과물

### 9.1 필수 테스트

1. 3/6/9.999초 공백+fresh 0D, 10초 정확히, 긴 30초 공백: activity/quote age/반복 분모 일치.
2. 같은 공백 100회 get, 여러 promotion/owner의 동일 frame 소비: 반복 count 1.
3. 공백→genuine trade→공백 3회, 10초 정상 활동, scope/epoch reset: 일관 계수/복귀.
4. 첫 0B 미수신, quote-only/PING-only/타 symbol 활발, local drop/reconnect: 시장 무체결 확정 금지.
5. 과거 provider 시각 late trade/future/regression/duplicate/cross-route: fake fresh/recovery 금지.
6. program만 갱신, quote 오래됨/trade 새로움, 반대 조합: 시계 혼합 금지.
7. 동일 입력/시점/contract를 main/AI/gateway/widget/episode/file이 소비: common health parity, stage TTL 차이만 허용.
8. REST fresh book+오래된/불명 trade, minute/history: fake 0B/매수 우세/current state 갱신 금지.
9. 동일 payload 동시 read/다른 route/tm/date/origin/account/continuation/deadline: 정확한 reuse와 오공유 0.
10. rate limit/shared budget wait/timeout/parser fail/late completion: 기존 retry/예약 유지, 빈 source 성공 금지.
11. AI 중 expiry/submit 전 new frame/observer refresh 후 age 경과: submit 재검증·원시각 유지.
12. 동일 frame 반복 평가, 새 0B/0D wakeup, enqueue fail/deadline: duplicate/orphan/무기한 park 없음.
13. quiet에서도 holding SELL/cancel/terminal/custody 확인 지속, owner/주문/수량/target 불변.
14. 1초 micro/trade backing/refill 결손: 보간 금지, 기존 fallback/원 target 유지.
15. legacy/new envelope 혼재: 원packet의 pure 호환 adapter 또는 명시 unproven, blind fresh/예외 은폐/전체 날짜 false block 금지.
16. callback/getter/writer 부하: history deepcopy/global-lock network/pending 무제한/로그 burst 금지.

기존 test 파일을 우선 확장한다. 주경로: `src/tests/test_kiwoom_websocket.py`, `test_ai_market_snapshot.py`, `test_market_data_enrichment.py`, `test_quote_consistency.py`, `test_kiwoom_quote_consistency.py`, `test_kiwoom_episode_read_control.py`, `test_entry_liquidity_guard.py`, `test_sniper_entry_latency.py`, `test_scanner_async_eval.py`, `test_scanner_async_entry_bridge.py`, `test_widget_symbol_runtime_collector.py`, `test_widget_research_watch_collector.py`, `test_dynamic_micro_confirmation.py`, `test_entry_adverse_flow.py`, `test_target_pressure.py`, `test_profit_stagnation.py`; `src/trading/tests/test_market_data_cache.py`, `test_entry_orchestrator.py`, `test_latency_monitor.py`. 영향받는 기존 audit/sentinel/downstream test도 추가한다.

프로젝트 `.venv`의 관련 pytest/변경 Python compile, wrapper 변경 시 bash syntax/contract test, `git diff --check`를 실행한다. mock/offline fixture로 실API/Provider/실주문 없이 먼저 닫는다. 새 test module도 기존 파일 확장이 불가능한 이유와 role location을 확인하며 engine-root allowlist를 불필요하게 넓히지 않는다.

### 9.2 필수 회귀 fixture와 결과물

최소 fixture는 현재 test 파일에 추가한다. 새 mock service/전체collector 구축을 요구하지 않는다.

1. 기계100평가 모두 BLOCK, exact raw/outcome 유효: census100, usable 분모 유지, PASS0 이유로 연구 중단 없음.
2. ENTER_NOW20 모두 VETO: AI screening20, profitable/correct veto 분리, actual0과 modeled payoff 별도.
3. 기계 mixed actions·같은 opportunity 다중recheck: event count 보존, unique opportunity payoff 중복0.
4. PASS→source/final guard/reject/no-fill/partial/full: exact parent 보존; 후단 차단을 AI 품질 또는 upstream 미발견으로 오귀속0.
5. 실제 no-fill CF profitable vs CF unsupported: 전자는 가격기회비용, 후자는 null+missing. 가격touch를 실제fullfill로 승격0.
6. SOURCE_INVALID/routeUNKNOWN/window truncated/cost missing: census 유지, 경제성eligible 제외, source-quality 수리 owner로 전달.
7. legacy prompt only 및 compact 미적용일: current compact candidate gate는 current-compatible evidence만. 연구는 격리, 자동overwrite0.
8. candidate trades fewer/gross winrate higher/day net lower: 전체목적에서 탈락. 작은순익빈도 상승·stress/tail 악화 후보도 탈락.
9. no exposure/무기회일/negative일/missing일: 정상0과 결측을 분리, 양의날짜만 평균내기0.
10. same symbol 다른owner/venue/session/epoch/policy: exact join 실패와 사유 유지, cross-owner fill 흡수0.
11. calibration 선택→holdout 실패→다른family 동일holdout 성공: 자동 재선정 금지.
12. candidate valid→publisher→PREOPEN→dated loader, mismatched hash/late refresh/frozen date: 성공·carry·차단 예상분기, 이미 소비policy 조용한교체0.

구현 보고에는 파일/함수별 inventory, package별 review/fix/test receipt, source generation와 counts, 바뀐candidate gate와 근거, 기대회복순익/추가손실/원천coverage, auto handoff·현재PID·자연실체결 경제성의 별도 상태를 남긴다. 아직 자연 acceptance를 보지 못했다면 미관측이라고 보고한다.

### 9.3 두 개선 축의 교차 회귀 fixture

1. 6초 관찰공백+fresh0D·정상연속성: quiet/source/type 구분과 stage-required feature 판정. health공통화가 micro trade backing을발명하거나 ENTER를직접생성하지않음.
2. 동일frame을100회소비: 공백episode1·중복heavy억제, 그러나 raw기회/attempt/event보존식과독립census/prune sampling은 유지.
3. genuinely new0D만도착: quote-dependent source blocker는복귀하고 trade-required feature는원계약대로판정. 일괄trade-only park로기회를잃지않음.
4. metadata/시각귀속만수리하고 machine/AI/price/qty policy동일: source 판정 효과만 귀속. 후행수익label을현재action에역류시키지않음.
5. allBLOCK 또는 allVETO인데source/outcome유효: H/sourcequality검증가능, machine 또는AI의해당CF연구가능. AI PASS0을다른모집단의경제성gate로결합하지않음.
6. allSOURCE_INVALID: census는남기되후행상승만으로E승격불가. first-data/drop/route/time복구owner로전달; missing경제성0대입없음.
7. 가격ready미제출·확인된no-fill: actual0/비용·CF기회비용분리. binder/actionowner불변과fourarmhash검증.
8. old/new envelope·code release·prompt partition혼재: 동등성있는순수adapter 또는unproven. 기존compact미적용원천을currentprompt효과로자동재라벨링하지않음.
9. singleflight wait/timeout과critical deadline: budget/slippage/submit전age재검증/account/SELL감시보존, waiter의duplicate request·latecontextoverwrite0.
10. H scope부분release/PID완료·E미관측: H배포성공만보고하고U7–U11전수완료/수익개선으로대체하지않음.


## 10. 작업본→배포본→실제PID

1. **작업본 고정**: branch/HEAD/diff/hash, dirty/다른 세션 변경, selected release/current PID/서비스 root 읽기. mtime/최신 폴더명으로 배포 대상을 정하지 않는다.
2. **작업본 구현·검증**: U0–U5/U6의 해당 범위와 U12A scoped review/finding 0/targeted validation/consumer coverage. 경제성 자연 표본 부족을 코드 수리의 가짜 실주문 요구로 바꾸지 않는다.
3. **commit/push**: 후속 구현 요청 권한에 따라 검증 변경만 commit한다. 무관 생성물/custody/env/다른 세션 변경을 합치지 않고 remote branch/hash를 확인한다.
4. **기존 managed release**: `deploy/run_runtime_release.sh`/`src/engine/infrastructure/runtime_release_router.py`의 현재 contract대로 생성한다. 새 배포 script/service는 없다. 가동 release 직접 편집/rsync 덮어쓰기는 금지한다.
5. **배포본 재검증**: 변경 source·의존 helper·gateway·writer·tests/config hash가 검증 작업본과 일치해야 한다. 공유 data/.venv symlink 실체와 code 범위를 분리한다. release-local import/compile/targeted test로 workspace 오import PASS를 방지한다.
6. **선택/기동 분리**: 선택만으로 구 PID는 갱신되지 않는다. main/collector/widget trader/episode/web의 cwd/ExecStart/import 방식을 각각 확인하고 필요 대상만 허용 권한/기존 절차로 갱신한다. 포괄 재기동은 금지한다.
7. **실PID 검증**: root/commit/source hash, policy date/hash, custody·미체결/전시장 balance, WS login/REG/type first-data/epoch, common health import/config receipt를 확인한다. metadata 성공을 정책 적용/주문 성공으로 대체하지 않는다.
8. **자연 coverage**: 실제 source→공통 판정→machine/AI/price/sizing/submit 또는 valid nonentry terminal을 연결한다. widget/episode/holding은 독립 receipt다. sample 0은 설정 확인/자연 미관측을 구분한다.
9. **rollback**: route 혼합/fake freshness/guard 누출/SELL·reconcile 중단/lock·latency 악화 시 새 세대 사용을 중단한다. 갱신됐다면 기존 managed rollback·허용 기동 범위로 구 검증 release에 복귀한다. source/주문/custody는 되돌리지 않는다.

이번 계획 작성은 selected release/PID를 변경하지 않는다. 후속 기동 허가도 numeric 가격/수량/manual lock/provider/cap/안전 threshold의 포괄 변경권한은 아니다.

## 11. 기대효과·조건의 합리성

| 기대효과 | 구현 acceptance | 자연/경제성 확인 |
| --- | --- | --- |
| source-invalid 오귀속 감소 | quiet/identity/quote/전달·소비 지연 분리, same input parity | 원 floor/분모 축소 없이 valid 기회 평가 회복 |
| 중복 read/heavy 평가 감소 | same payload 동시 read 1 transport, same frame 1 in-flight, fresh WS 시 호가 REST fallback 0, new source 복귀 | API 수/budget wait/queue lag/consumer latency 개선 |
| 유효 기회 우선 소비 | 중복 억제·정상 wakeup, slot/guard 불변 | 독립 recall/promotion→eval 지연/submit·fill 유지 개선 |
| 안전·회전 유지 | quote/price/adverse/broker/quantity/cooldown/SELL 감시 유지 | full/partial/terminal/tail/자본점유/비용 후 순익 |

‘비용을 차감하고 작은 수익을 빈번하게’의 구체목표는 **fresh executable quote의 유효 기회를 빨리 평가하고, 같은 입력의 반복작업으로 다음 기회를 놓치지 않는 것**이다. guard 무차별 완화/quiet BUY화/주문 수 증가 자체는 목적이 아니다.

코드 수리 완료에 양수 EV/전 horizon/5·10·20일 동시 floor/별도 장후 승인을 요구하지 않는다. 반대로 parity/호출 절약만으로 수익 개선을 선언하지 않는다. 경제성은 기존 owner의 effective cost·exact terminal·owner/venue/session·policy/source generation·complete/censored 계약으로 측정하고 불명 cost/PnL은 null로 유지한다. 기존 장후 측정은 그대로 사용하고 quiet 10초를 자동 최적화하는 새 job/family는 없다.

호출/평가 절약은 동일 recorded 입력·도착순서·clock의 offline fixture에서 before/after 호출수·대기·queue 진행을 확인한다. 다른 시장일의 단순 평균이나 SOURCE_INVALID 분모 감소로 효과를 귀속하지 않는다. 무조건 submit 증가율, 고정 ms 감소율 또는 모든 scope 자연 sample을 코드 배포 gate로 추가하지 않는다. 실제 적용 뒤 active scope의 예산/latency가 악화하거나 새 source를 놓치면 원인을 수정한다.

최종보고는 `code/contract closure → 작업본/release 일치 → PID 소비 → 자연 coverage → latency/예산 효과 → 비용 후 경제성`을 분리한다. ENTER_NOW 부족이 기존 micro/경제성의 정상 nonentry로 남으면 해당 owner를 설명하며 입력 수리 완료와 혼동하지 않는다.

### 11.1 통합 경제성 기대효과·조건 검토

입력 수리 H는 유효 기회에 대한 정상 평가/latency 예산을 회복하고, E는 회복한 기회와 회피한 손실을 동일 모집단에서 비교해 등록 기계 threshold·compact prompt·가격/수량 leg 후보를 선정한다. 두 효과를 source-quality/count 감소나 한 건 submit으로 합쳐 선언하지 않는다.

정량 예상은 동일 frozen 기회에서 incumbent/candidate의 cost-adjusted payoff delta, recovered executable participation, added loss/tail, net profit/source day·capital occupancy로 계산한다. overlap/cooldown/기존 quantity/cap과 exit가 동일해야 한다. 실제 trades·비용·실현순익은 별도 actual acceptance이며 CF 이익을 실현 headline에 합산하지 않는다.

§7.4의 gate 합리성 검토를 H에도 경제성 floor를 붙이는 일반 gate로 사용하지 않는다. source-invalid는 수리 대상이고, 정상 BLOCK/VETO의 경제적 최적성은 source-valid 대칭 평가 대상이다. 가격의 0.10% 재설계는 현재 Plan 계약과 다른 제안이므로 owning contract/권한/문서 정합화가 선행되어야 한다.

## 12. 문서 정합·전수 완료·이번 요청의 검증 범위

- 이 통합 문서의 U0–U12만 현재 일괄 작업계획으로 사용한다. 두 구계획의 C/OC 명칭은 대응 이력이지 별도 native 추천/작업 분모가 아니다.
- 기존 source manifest/hash·raw 보존/품질 exclusion·frozen published policy·valid checkpoint·별도 승인 custody/override를 유지한다. 전일 결손을 새 원천으로 재라벨링하거나 실제 signal/attempt/fill을 발명하지 않는다.
- 설치된 장후 producer/consumer 순서와 21:05 follower·20:10 widget/21:15 machine·strict finalization closure를 변경하지 않는다. report 내부 adapter/metric/기존 자동 family를 보완하며 새 stage/schedule/필수 운영 producer를 추가하지 않는다.
- upstream code/계산 결과 변경 시 승인된 최소 재생성은 최초 영향 producer부터 last consumer까지 한다. downstream이 stale이면 EV/summary/gap/lineage→tower→checklist→strict verifier/controller/finalization을 필요한 범위로 같은 target date/hash에 결속한다. 이전 PASS로 최신 명령 FAIL을 가리지 않는다.
- executable 자연 후속은 기존 daily checklist OPEN ID를 재사용하고 package 이름을 새 schedule로 만들지 않는다. 기존 완료 review는 새 결함/contract 변경/필수 handoff 실패가 있을 때만 재개한다.
- baseline README/runbook/Plan/AGENTS는 명시 요청이 있을 때만 수정한다. 허용된 실제 automation/wrapper 수정 시 관련 운영 설명과 checklist를 같은 change set에서 정합화하고 print-only parser로 owner 유일성을 확인한다.
- 전체 implementation acceptance: raw/live/tuning/candidate 미분류0, live 소비의 common health 누락0, independent trade activity classifier0, opportunity/attempt/count 보존, eligible actionable defect0, review P0–P2 미해결0, targeted validation PASS. actual policy/PID/자연 경제성은 별도 상태다.
- 이번 계획 통합의 검증은 문서 내용/상호참조/owner·권한·의존/구계획 누락·중복 리뷰와 print-only parser·diff check다. 코드 구현/거래 test/실API/Provider/report regeneration/release/start는 실행하지 않는다.
- 미확정사항: U0의 일반 I/O-only reader 의미분류/간접 callsite 완료와 active family의 자연 유입/실제 gate 달성 가능성. 문자열/AST 전수 검색을 동적 소비/경제성 완료로 보고하지 않는다.

문서/checklist 변경 후 검증 명령:

~~~bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
~~~



## 부록 A. 작업본 정적 reader/원천 참조 전수 inventory

아래 D는 직접 raw/원천 계약 검색, I는 일반 I/O 검색이다. D/I는 검색 membership이지 함수 의미 검토 완료/active 상태가 아니다. §5와 U0에서 실제 소비역할·미진입 predicate·최종 policy consumer를 확정한다. OFF/퇴역 파일도 삭제하거나 재활성화하지 않는다.

<details>
<summary>전체 파일 목록: 306개 (D 131개, I 295개)</summary>

~~~text
-I analysis/claude_scalping_pattern_lab/analyze_ev_patterns.py
-I analysis/claude_scalping_pattern_lab/build_claude_payload.py
D- analysis/claude_scalping_pattern_lab/config.py
-I analysis/claude_scalping_pattern_lab/economic_evidence.py
DI analysis/claude_scalping_pattern_lab/prepare_dataset.py
-I analysis/deepseek_swing_pattern_lab/analyze_swing_patterns.py
DI analysis/deepseek_swing_pattern_lab/build_deepseek_payload.py
D- analysis/deepseek_swing_pattern_lab/config.py
DI analysis/deepseek_swing_pattern_lab/prepare_dataset.py
-I analysis/gemini_scalping_pattern_lab/analyze_patterns.py
DI analysis/gemini_scalping_pattern_lab/build_dataset.py
-I analysis/gemini_scalping_pattern_lab/build_llm_payload.py
D- analysis/gemini_scalping_pattern_lab/config.py
DI analysis/gemini_scalping_pattern_lab/generate_final_report.py
DI analysis/tuning_observability_summary.py
-I src/engine/ai/postclose_structured_review_provider.py
-I src/engine/ai_engine_openai.py
DI src/engine/automation/ai_multi_timeframe_context_promotion.py
DI src/engine/automation/automation_chain_slimming_audit.py
DI src/engine/automation/automation_chain_trigger_decision.py
DI src/engine/automation/codex_workorder_runner.py
-I src/engine/automation/conversion_lane.py
-I src/engine/automation/drought_handoff.py
DI src/engine/automation/entry_cancel_wait_tuning.py
DI src/engine/automation/key_lineage_ledger.py
DI src/engine/automation/ldm_hypothesis_discovery.py
DI src/engine/automation/ldm_hypothesis_parent_refinement.py
-I src/engine/automation/low_price_two_leg_auto_expansion_policy.py
-I src/engine/automation/low_price_two_leg_policy_apply.py
-I src/engine/automation/machine_adaptive_exit_approval.py
-I src/engine/automation/machine_adaptive_exit_policy_apply.py
-I src/engine/automation/machine_entry_timing_tuning.py
-I src/engine/automation/machine_microstructure_policy_approval.py
-I src/engine/automation/main_ai_current_axis.py
-I src/engine/automation/main_ai_quality_runtime_family.py
-I src/engine/automation/market_weakness_hysteresis_tuning.py
-I src/engine/automation/monitoring_instruction_refresh.py
-I src/engine/automation/operator_policy_succession.py
-I src/engine/automation/pattern_lab_source_contract.py
-I src/engine/automation/postclose_done_controller.py
-I src/engine/automation/postclose_recommendation_intake.py
DI src/engine/automation/postclose_summary_handoff.py
DI src/engine/automation/producer_gap_discovery.py
-I src/engine/automation/producer_gap_source_bundle.py
DI src/engine/automation/samsung_machine_entry_policy_apply.py
-I src/engine/automation/source_quality_clean_baseline.py
DI src/engine/automation/source_quality_hard_gate.py
-I src/engine/automation/stage_hook_runtime_scaffold.py
-I src/engine/automation/stage_hook_workorder_discovery.py
DI src/engine/automation/time_window_regime_counterfactual.py
DI src/engine/automation/tuning_performance_control_tower.py
DI src/engine/backfill_threshold_cycle_events.py
-I src/engine/bd_fbuy_accum_pre_scanner.py
-I src/engine/bedrock_nova_provider.py
DI src/engine/build_code_improvement_workorder.py
DI src/engine/build_codex_daily_workorder.py
DI src/engine/build_next_stage2_checklist.py
DI src/engine/build_tuning_monitoring_parquet.py
DI src/engine/buy_funnel_sentinel.py
-I src/engine/buy_pause_guard.py
DI src/engine/collect_remote_latency_baseline.py
DI src/engine/compare_tuning_shadow_diff.py
DI src/engine/compress_db_backfilled_files.py
-I src/engine/daily_report_service.py
DI src/engine/daily_threshold_cycle_report.py
DI src/engine/dashboard_data_repository.py
DI src/engine/error_detectors/artifact_freshness.py
-I src/engine/error_detectors/cron_completion.py
-I src/engine/error_detectors/kiwoom_auth_8005_restart.py
-I src/engine/error_detectors/log_scanner.py
DI src/engine/error_detectors/process_health.py
-I src/engine/error_detectors/resource_usage.py
DI src/engine/fetch_remote_scalping_logs.py
-I src/engine/holding_exit_matrix_runtime.py
DI src/engine/holding_exit_observation_report.py
DI src/engine/holding_exit_sentinel.py
-I src/engine/infrastructure/runtime_release_router.py
DI src/engine/institutional_flow_context.py
-I src/engine/ipo_listing_day_runner.py
-I src/engine/kiwoom_orders.py
D- src/engine/kiwoom_sniper_v2.py
DI src/engine/kiwoom_websocket.py
-I src/engine/lifecycle/avg_down_policy_replay.py
-I src/engine/lifecycle/greenfield_authority.py
DI src/engine/lifecycle/scale_in_incremental_counterfactual.py
DI src/engine/lifecycle/stop_loss_recovery_backtest.py
DI src/engine/lifecycle_ai_context.py
-I src/engine/lifecycle_bucket_discovery.py
DI src/engine/lifecycle_decision_matrix.py
-I src/engine/lifecycle_decision_matrix_runtime.py
DI src/engine/log_archive_service.py
-I src/engine/macro_briefing_complete.py
-I src/engine/market_panic_breadth_collector.py
-I src/engine/monitor_snapshot_runtime.py
-I src/engine/monitoring/doosan_widget_contract.py
-I src/engine/monitoring/doosan_widget_telegram_notify.py
-I src/engine/monitoring/entry_adverse_flow_summary.py
-I src/engine/monitoring/entry_turn_point_replay.py
D- src/engine/monitoring/error_detector_coverage.py
-I src/engine/monitoring/hanwha_ocean_widget_contract.py
-I src/engine/monitoring/hanwha_ocean_widget_telegram_notify.py
DI src/engine/monitoring/intraday_entry_blocker_diagnostics.py
DI src/engine/monitoring/intraday_entry_flow_report.py
DI src/engine/monitoring/intraday_ws_freshness_monitor.py
DI src/engine/monitoring/limit_down_watch_report.py
DI src/engine/monitoring/limit_down_watch_research.py
-I src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py
DI src/engine/monitoring/low_price_two_leg_tuning.py
-I src/engine/monitoring/machine_adaptive_exit_source.py
-I src/engine/monitoring/machine_candidate_lifecycle.py
-I src/engine/monitoring/machine_lifecycle_turnover_policy_research.py
-I src/engine/monitoring/machine_market_weakness_response.py
-I src/engine/monitoring/machine_microstructure_attribution.py
-I src/engine/monitoring/machine_rebound_reentry_source.py
-I src/engine/monitoring/market_halt_windows.py
DI src/engine/monitoring/market_opportunity_census.py
D- src/engine/monitoring/market_opportunity_review.py
DI src/engine/monitoring/one_share_threshold_opportunity.py
D- src/engine/monitoring/pruned_candidate_bbo_collector.py
-I src/engine/monitoring/pure_market_adaptive_opportunity_replay.py
-I src/engine/monitoring/pure_market_kiwoom_backfill.py
-I src/engine/monitoring/pure_market_regime_replay.py
-I src/engine/monitoring/pure_market_reversal_replay.py
DI src/engine/monitoring/quote_consistency_backtest.py
DI src/engine/monitoring/quote_stale_frequency_report.py
DI src/engine/monitoring/rising_missed_classifier_prior.py
DI src/engine/monitoring/rising_missed_intraday_feedback.py
DI src/engine/monitoring/rising_missed_scout_workorder.py
DI src/engine/monitoring/samsung_machine_entry_tuning.py
-I src/engine/monitoring/samsung_morning_reentry_research.py
DI src/engine/monitoring/samsung_widget_advisory.py
-I src/engine/monitoring/samsung_widget_advisory_evaluation.py
-I src/engine/monitoring/samsung_widget_contract.py
-I src/engine/monitoring/samsung_widget_entry_notify.py
DI src/engine/monitoring/scalping_avg_down_recovery_calibration.py
DI src/engine/monitoring/scalping_pyramid_intraday_feedback.py
-I src/engine/monitoring/scalping_pyramid_quality_calibration.py
DI src/engine/monitoring/scanner_lookup_attention_tuning.py
-I src/engine/monitoring/system_metric_sampler.py
-I src/engine/monitoring/widget_advisory_calibration.py
-I src/engine/monitoring/widget_advisory_calibration_policy.py
-I src/engine/monitoring/widget_auto_trade_policy_calibration.py
DI src/engine/monitoring/widget_collector_expansion_recommendation.py
-I src/engine/monitoring/widget_execution_quality.py
DI src/engine/monitoring/widget_mechanical_entry_replay.py
DI src/engine/monitoring/widget_paired_policy_replay.py
-I src/engine/monitoring/widget_research_watch_collector.py
DI src/engine/monitoring/widget_signal_quality.py
-I src/engine/monitoring/widget_symbol_runtime_collector.py
-I src/engine/monitoring/widget_symbol_runtime_contract.py
-I src/engine/monitoring/widget_symbol_runtime_policy.py
-I src/engine/monitoring/widget_symbol_signal_policy_research.py
-I src/engine/monitoring/ws_freshness_acceptance.py
-I src/engine/notify_error_detection_admin.py
-I src/engine/notify_monitor_snapshot_admin.py
-I src/engine/notify_panic_state_transition.py
DI src/engine/observation_source_quality_audit.py
DI src/engine/panic_sell_defense_report.py
D- src/engine/panic_sell_state_detector.py
DI src/engine/pattern_lab_ai_review.py
-I src/engine/pattern_lab_currentness_audit.py
-I src/engine/pattern_lab_propagation_audit.py
-I src/engine/pipeline_event_summary.py
DI src/engine/pipeline_event_verbosity_report.py
-I src/engine/risk/market_weakness_entry_guard.py
-I src/engine/risk/market_weakness_threshold_policy.py
D- src/engine/run_monitor_snapshot.py
-I src/engine/runtime_apply_bridge.py
DI src/engine/runtime_apply_gap_audit.py
DI src/engine/runtime_approval_summary.py
DI src/engine/scalp_entry_action_decision_matrix.py
-I src/engine/scalp_entry_adm_runtime.py
DI src/engine/scalp_sim_ev_midcheck.py
DI src/engine/scalping/ai_action_outcome_calibration.py
DI src/engine/scalping/ai_decision_quality.py
DI src/engine/scalping/ai_decision_trace.py
DI src/engine/scalping/ai_input_external_validation.py
DI src/engine/scalping/ai_input_quality_baseline_replay.py
-I src/engine/scalping/ai_market_snapshot.py
DI src/engine/scalping/ai_stage_coverage_replay.py
DI src/engine/scalping/entry_ai_gate_backtest.py
-I src/engine/scalping/entry_candidate_lifecycle_state.py
DI src/engine/scalping/entry_context_intraday_probe.py
-I src/engine/scalping/entry_execution_sizing_plan.py
DI src/engine/scalping/entry_hurdle_backtest.py
D- src/engine/scalping/entry_observation_source.py
-I src/engine/scalping/entry_price_live_policy.py
DI src/engine/scalping/entry_recheck_submit_budget.py
-I src/engine/scalping/entry_setup_evidence.py
-I src/engine/scalping/entry_setup_intraday_activation.py
-I src/engine/scalping/entry_setup_live_policy.py
-I src/engine/scalping/entry_setup_paired_replay_batch.py
-I src/engine/scalping/entry_setup_scalping_rollout.py
DI src/engine/scalping/entry_split_order_plan.py
DI src/engine/scalping/holding_prompt_live_policy.py
DI src/engine/scalping/limit_down_watch.py
-I src/engine/scalping/main_ai_current_axis.py
-I src/engine/scalping/main_ai_current_axis_input.py
-I src/engine/scalping/main_ai_current_axis_runtime.py
DI src/engine/scalping/main_ai_holding_base_replay_batch.py
DI src/engine/scalping/main_ai_prompt_consumer.py
-I src/engine/scalping/main_ai_quality_live_policy.py
DI src/engine/scalping/main_lifecycle_journal.py
DI src/engine/scalping/main_lifecycle_paired.py
DI src/engine/scalping/mechanistic_entry_runtime_policy.py
DI src/engine/scalping/micro_reversion/ai_quality_bridge.py
DI src/engine/scalping/micro_reversion/ai_quality_cycle.py
-I src/engine/scalping/micro_reversion/canary_monitor.py
-I src/engine/scalping/micro_reversion/collection_targets.py
-I src/engine/scalping/micro_reversion/counterfactual_entry_diagnostic.py
-I src/engine/scalping/micro_reversion/depth_join.py
-I src/engine/scalping/micro_reversion/economic_reference.py
-I src/engine/scalping/micro_reversion/economic_reference_owner.py
DI src/engine/scalping/micro_reversion/forward_collector.py
DI src/engine/scalping/micro_reversion/main_ai_prompt_optimizer.py
-I src/engine/scalping/micro_reversion/p2_replay.py
-I src/engine/scalping/micro_reversion/path_capture.py
-I src/engine/scalping/micro_reversion/path_journal.py
-I src/engine/scalping/micro_reversion/provider_budget.py
DI src/engine/scalping/micro_reversion/replay.py
DI src/engine/scalping/micro_reversion/storage_maintenance.py
-I src/engine/scalping/micro_reversion/symbol_master.py
DI src/engine/scalping/microstructure_reaction_context.py
-I src/engine/scalping/multi_timeframe_context.py
-I src/engine/scalping/opening_rotation.py
DI src/engine/scalping/opening_rotation_backtest.py
DI src/engine/scalping/opening_rotation_tuning.py
-I src/engine/scalping/position_peak_ledger.py
-I src/engine/scalping/position_sizing_allocator.py
DI src/engine/scalping/scale_in_split_order_plan.py
-I src/engine/scalping/scanner_lookup_attention_policy.py
DI src/engine/scalping/scanner_scheduler_replay.py
-I src/engine/scalping/score_recovery_observation.py
-I src/engine/scalping/strategy_owner_components.py
-I src/engine/scalping/strategy_owner_replay.py
-I src/engine/scalping_feature_packet.py
DI src/engine/scalping_pattern_lab_automation.py
-I src/engine/sentinel_event_cache.py
-I src/engine/sniper_config.py
D- src/engine/sniper_entry_latency.py
DI src/engine/sniper_entry_pipeline_report.py
DI src/engine/sniper_execution_receipts.py
-I src/engine/sniper_gatekeeper_replay.py
-I src/engine/sniper_market_regime.py
DI src/engine/sniper_missed_entry_counterfactual.py
DI src/engine/sniper_performance_tuning_report.py
DI src/engine/sniper_post_sell_feedback.py
-I src/engine/sniper_s15_fast_track.py
DI src/engine/sniper_state_handlers.py
-I src/engine/sniper_strength_shadow_feedback.py
DI src/engine/strategy_position_performance_report.py
-I src/engine/swing/bottom_rebound_candidate_source.py
-I src/engine/swing/bottom_rebound_policy_auto_loop.py
-I src/engine/swing/sim_auto_approval_control_tower.py
DI src/engine/swing_daily_simulation_report.py
DI src/engine/swing_lifecycle_audit.py
-I src/engine/swing_lifecycle_bucket_discovery.py
DI src/engine/swing_lifecycle_decision_matrix.py
-I src/engine/swing_pattern_lab_automation.py
-I src/engine/swing_sector_theme_source.py
DI src/engine/swing_selection_funnel_report.py
-I src/engine/swing_strategy_discovery_ev_report.py
-I src/engine/swing_strategy_discovery_label_builder.py
DI src/engine/swing_strategy_discovery_sim.py
-I src/engine/sync_docs_backlog_to_project.py
-I src/engine/sync_github_project_calendar.py
DI src/engine/threshold_cycle_ev_report.py
DI src/engine/threshold_cycle_preopen_apply.py
DI src/engine/tuning_duckdb_repository.py
DI src/engine/verify_threshold_cycle_postclose_chain.py
DI src/engine/wait6579_ev_cohort_report.py
-I src/trading/config/machine_adaptive_exit_activation.py
-I src/trading/config/machine_entry_adverse_policy.py
-I src/trading/config/machine_entry_timing_policy.py
-I src/trading/config/machine_profit_stagnation_policy.py
-I src/trading/config/machine_rebound_reentry_policy.py
-I src/trading/config/machine_target_ratchet_policy.py
-I src/trading/config/symbol_owner_policy.py
-I src/trading/config/symbol_owner_standing_authority.py
-I src/trading/entry/orderbook_stability_observer.py
-I src/trading/low_price_two_leg/policy_runtime.py
-I src/trading/low_price_two_leg/preflight.py
-I src/trading/market/aftermarket_eligibility.py
-I src/trading/market/machine_rebound_reentry.py
-I src/trading/market/micro_confirmation.py
-I src/trading/order/adaptive_exit/group_decision.py
-I src/trading/order/entry_adverse_owners.py
-I src/trading/order/manual_episode_exit_reconciliation.py
-I src/trading/order/owner_custody_registry.py
-I src/trading/order/regular_two_leg_machine.py
-I src/trading/order/samsung_entry_policy.py
-I src/trading/order/symbol_owner_policy_apply.py
-I src/trading/order/symbol_owner_policy_auto_apply.py
-I src/trading/samsung_afternoon_one_share/preflight.py
-I src/trading/samsung_midday_one_share/preflight.py
-I src/trading/samsung_morning_one_share/authority_handoff.py
-I src/trading/samsung_morning_one_share/manual_addon.py
-I src/trading/samsung_morning_one_share/preflight.py
-I src/trading/samsung_morning_one_share/reentry.py
-I src/trading/widget_auto_trade/engine.py
-I src/trading/widget_auto_trade/manual_orders.py
-I src/trading/widget_auto_trade/notifications.py
-I src/trading/widget_auto_trade/policy.py
-I src/trading/widget_auto_trade/runtime_verification.py
-I src/web/bucket_tracking_routes.py
-I src/web/samsung_price_widget_routes.py
~~~

</details>
