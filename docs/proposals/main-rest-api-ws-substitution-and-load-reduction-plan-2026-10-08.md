# Main REST 호출량 절감과 WS 재사용 계획 — 2026-10-08

## 1. 결정과 범위

**기존 WS의 정확한 체결·호가·완성봉을 재사용하고, REST만 제공하는 원천은 유지한다.** 새 WS 세션이나 전시장 구독 확대부터 시작하지 않는다. 조사 대상은 `kt00011`에 한정하지 않은 저장소 전체 키움 호출 경로다. [전체 조사](../audits/main-rest-api-ws-callsite-and-load-audit-2026-10-08.md), [호출·참조 위치 TSV](../audits/main-rest-ws-callsite-inventory-2026-10-08.tsv), [증거 manifest](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/manifest.json)를 함께 본다. 정적 목록은 조사 시점의 46종 API/86개 endpoint 지정 지점이며, 현재 활성 호출량과 혼동하지 않는다.

사용자는 에피소드 프로세스 삭제와 잔여 체결분의 수동관리를 지시했다. 따라서 에피소드 전용 WS 전환·캐시·수집기 증설은 계획하지 않는다. [Main-only 제거 계획](main-only-widget-episode-full-retirement-plan-2026-10-07.md)이 전용 프로세스·원천·예약·설치본 제거를 소유하며, 잔여 보유·주문/intent·flat 대사는 퇴역/삭제의 선행 조건이 아니다. [11:02 이후 OFF 실행 기록](../audits/episode-permanent-off-lock-release-2026-10-08.md)을 기준으로 삭제 전 부하와 이후 Main 부하를 분리한다. episode 자동 청산/복구를 재개하거나 잔여 수량을 Main이 자동 인수하지 않는다. Main/수동관리와 생존 소비자에 필요한 공통 WS·주문/체결·계좌 원천 및 역사적 소유권 증거는 보존한다.

이번 결과는 **읽기 전용 조사와 계획**이다. API 호출, WS 연결·REG/REMOVE, 런타임 구현, 환경변수 변경, 정책 발행, 배포·재기동, 프로세스/파일 삭제를 실행하지 않았다. 다른 지연 개선 작업의 승인을 이 계획의 새로운 프로토콜·소비 계약 변경 승인으로 확장하지 않는다. 이미 별도로 승인된 작업은 그 범위에서 지속한다.

실행 인계는 [오늘 checklist](../checklists/2026-10-08-stage2-todo-checklist.md)의 기존 `DirectFamilySourceRepairMainMechanisticEntry` 내부 `RW0`~`RW6`로 둔다. 새 중복 OPEN owner를 만들지 않는다. 현재 매매 조건, 5초 claim, 가격·수량·자본·manual veto·broker·hard safety와 사용자 지정 초기 정책 채택 계약은 보존한다. 원천 절감 검증에 별도 EV/최소 체결/holdout 게이트를 추가하지 않는다.

## 2. 공식 확인과 설계 경계

2026-10-08 10:34:31 KST에 키움 공식 저장소 HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 확인했다. [공식 원천 영수증](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/official-reference.json)에 검사 경로와 SHA256을 보존했다. 현재 tree에는 `kiwoom_docs`가 없다. `kiwoom/_data/kiwoom_api_spec.json`, `specs.py`, `core/{client,ws_client,auth,errors}.py`, `realtime/{packets,schemas,decoders,stream}.py`, PRD/MOCK Postman 및 [공식 이용안내](https://openapi.kiwoom.com/intro)를 대조했다. 구현 착수 시 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 다시 적용한다.

- 국내주식 계좌/토큰별 조회 5회/초와 주문 5회/초는 별도 한도다. 모의는 TR별 1회/초다. 기존 shared read gate의 source-only 4/전체 5 reserve·FIFO·cooldown·retry 제한을 보존한다. 주문을 읽기 single-flight/retry에 넣지 않는다.
- WS는 계좌/토큰별 1세션, 세션당 실시간 시세 200종목이다. 조건검색 10건/결과 100종목은 별도 계약이다. `종목×type`, suffix별 item, 복수 group이 vendor 한도에서 어떻게 중복 계산되는지는 이 안내만으로 확정하지 않는다. 로컬 cap56은 조사 PID의 관측값이다. 착수 시 승인된 실제 cap/protected reserve를 확인해 보존하며 이 문서로 56을 새 운영 상수로 고정하지 않는다. 그룹·프로세스·token 교체를 한도 회피 수단으로 쓰지 않는다.
- 운영/모의 `wss://api.kiwoom.com:10000/api/dostk/websocket` / `wss://mockapi.kiwoom.com:10000/api/dostk/websocket`, LOGIN 성공, PING echo, REG/REMOVE와 `refresh=1` 유지/`0` 교체, REAL의 item/type/FID를 구별한다. 전송, ACK, 첫 유효 수신, 지속 수신, 소비 가능은 각각 별도 상태다.
- REST는 POST JSON, `api-id`/authorization/continuation header 및 body return code를 기존 계약대로 검사한다. 현재 SDK의 JSON body와 Postman query 표현 차이는 해소되지 않은 공식 원천 차이다. 이를 근거로 wire를 임의 변경하지 않는다.
- `04`의 FID933 잔고 주문가능수량과 의미가 비어 있는 FID951은 `kt00011`의 가격별 BUY capacity/예수금 대체 근거가 아니다. `00/04`는 계좌 변경 감지·기존 receipt 반영의 후보이며 시작·재접속·누락 후 REST reconciliation을 대체하지 않는다.

## 3. 전환 우선순위

| 순위 | 전체 호출군 | 적용안과 남겨야 할 REST |
| --- | --- | --- |
| P0 | 모든 HTTP transport, direct caller, continuation·retry | 호출 총량의 전송 기준 계측을 공통 지점에 완성한다. 캐시 hit·논리요청·admission·HTTP attempt·page·실패를 분리한다. 현재 전체 전송량과 절감률은 미확정이다. |
| P0 | `ka20006` SignalRadar fallback | 공식 `/api/dostk/chart`, `inds_cd`, `base_dt`와 다른 `/mrkcond`, `upjong_cd` 경로를 수정 대상으로 등록한다. 실제 fallback 발생량은 미관측이다. 공통 transport와 20일 이력 소비 계약으로 수리한다. 현행 helper의 2값 tuple로 단순 교체하지 않는다. 실패 시 기존 보수적 BEAR 동작과 정상 지수로 산출한 BEAR의 원천 상태를 구분한다. |
| P1 | `ka10080`, `ka10003/84`, `ka10004`, `ka10001`의 Main 평가·소스 준비 | 현재 등록된 exact item의 적합한 WS 원천을 먼저 선택한다. 원천이 없는 시작·재접속·미구독 구간은 기존 bounded REST seed/recovery를 남긴다. 필드/이력 계약을 API 단위가 아닌 소비자별로 검증한다. |
| P1 | 동일 정책 평가/다른 helper의 반복 source 요청 | 한 평가에서 동일 검증 view를 공유하고, 기존 cache/single-flight의 정확한 key와 원 수신시각을 유지한다. 이미 구현된 재사용은 중복 개발하지 않는다. |
| P1 | `kt00011` 사전 준비 | 기존 exact-price coalescing·deadline·in-flight join·관측 cache-only를 유지하고, 원천 준비 후 실제 소비율/실패를 측정해 불필요한 준비를 줄인다. capacity 검증용 REST는 유지한다. |
| P2 | `ka90008`, `ka10046`, 시장지수 | WS 수급의 원천시각·경로·단위, 체결강도 시간축, 지수 일봉 기반선이 같을 때만 부분 대체한다. 전일 프로그램/분 단위 집계/일봉 이력을 현재 tick으로 덮지 않는다. 새 `0J` 구독은 기존 소비 수요와 부하 측정 후 별도 검토한다. |
| 유지 | 전시장 순위·발굴, 투자자/신용 집계, 종목·거래가능시장 메타, 과거 일봉, 계좌 대사, 주문·정정·취소·인증 | 동일 목적끼리 캐시/요청 결합을 검토하되 WS로 전부 바꿀 수 있다고 가정하지 않는다. 주문·인증·계좌를 공용 시장 cache에 저장하지 않는다. |
| 삭제 계획 인계 | episode/Samsung 전용 gateway·장후/연구·독립 IPO/위젯 잔존 경로 | 삭제 전 실측량과 남는 Main caller를 분리한다. 새 WS 전환 투자 없이 제거 계획의 마지막 전용 consumer·설치 경로 제거로 닫으며 episode flat을 기다리지 않는다. |

절감 효과는 같은 호출 목적·유효 평가/원천 수요당 HTTP attempts와 시간당 실제 전송량을 함께 비교한다. 대상 release가 바뀌는 것은 전환의 일부다. baseline/treatment의 commit·PID·정책·대상·source schema·설정과 변경 차이를 각각 보존하고, 정책/시장/session/종목 구성·입력률이 비교 가능한 구간을 사용한다. 비교할 수 없는 차이는 총량 변화로만 보고하고 전환 효과를 단정하지 않는다. 에피소드 삭제, 관측 중단, 거래량 감소로 줄어든 호출을 Main WS 전환 절감에 넣지 않는다. 같은 release에서 승인된 source 선택만 바꿀 수 있을 때는 그 비교를 우선하되 새 전환 권한을 만들지 않는다.

### 3.1 전체 호출 목록의 처리 경계

RW0는 정적 각 지점을 `Main live / Main 공통·offline / 삭제 예정 전용 / OFF·미확인`으로 매핑하고, 마지막 caller·transport·실행 owner 및 확인 근거를 남긴다. 이름에 episode가 있다는 이유만으로 삭제 대상으로 확정하지 않는다. 예를 들어 pruned BBO의 관측 episode는 삭제 예정 독립 매매 프로세스와 다르다. 미확인 caller는 비활성/호출0으로 처리하지 않는다.

생존 경로는 공통 transport 계측으로 묶고 공통 계측을 우회하는 직접 전송만 추가 연결한다. 삭제 예정 gateway에 새 WS·전용 계측 체계를 개발하지 않는다. 삭제 전 수치는 이미 있는 증거/공통 계측으로 분리하거나 `unknown`으로 남긴다. 전체 계정 부하 결손은 명시하되, 그것만으로 분모를 확인한 Main 부분군의 검증을 막지 않는다. 제거 종료 증거는 별도 제거 계획이 소유한다.

## 4. Main 소비자별 WS 재사용

### 4.1 체결·호가·가격

목표 소비 경로는 `kiwoom_websocket → exact route snapshot → Main prepare/refresh → machine/auxiliary → submit guard`다. 기존 [WS manager](../../src/engine/kiwoom_websocket.py), [Main handler](../../src/engine/sniper_state_handlers.py), [entry WS adapter](../../src/trading/market/entry_ws_snapshot.py), [공통 snapshot](../../src/trading/market/shared_ws_snapshot.py)의 실제 Main caller를 먼저 대조한다. 에피소드 adapter가 있다는 이유만으로 Main이 이미 그 adapter를 사용한다고 표시하지 않는다.

`0B`의 가격·누적량·체결강도·개별 체결과 `0D`의 호가·수량을 이용한다. `0C` 및 `0B`의 최우선 가격 두 필드만으로 depth/수량을 채우지 않는다. `ka10001`의 시총·유통주식·상하한가/정적 metadata 전체를 WS 현재가로 대체하지 않는다.

원천 key는 `date/session + exact item/suffix/route + transport epoch + source sequence + producer generation + schema`다. 거래소시각과 수신시각, 처리시각을 분리한다. stale/future/역행/중복/단절/교차호가/필수수량 누락/다른 route는 원천 오류다. snapshot delivery나 cache hit 시각으로 원 수신시각을 갱신하지 않는다. 최신가와 다른 epoch의 호가를 합성하지 않는다.

여기서 sequence는 출처를 명시한다. 로컬 ingress/journal 번호를 브로커 제공 sequence로 해석하지 않는다. 로컬 순서·drop0만으로 서버→클라이언트 전 구간의 무손실을 증명할 수 없다. type별 마지막 수신과 실제 거래 발생 기대, 누적량/완성봉 대사 및 기존 source-quality 계약을 함께 사용한다. 조용한 종목의 무체결과 수신 단절을 일률적인 새 TTL로 판정하지 않는다.

현재 Main의 `_pre_submit_refresh_rest_orderbook_snapshot`은 실행 직전 REST 비교와 별도 execution-critical 역할이 있다. **RW2에서 일괄 제거하지 않는다.** 준비/관측 중복 절감을 먼저 끝낸 뒤, independent REST 확인이 담당한 conflict 탐지까지 동등하게 유지할 수 있는 별도 소비 계약을 검토한다. `force`, 긴급 청산, 최종 가격/수량/계좌 검사 및 늦은 REST 응답의 재적용 방지는 그대로 남긴다. `_fetch_rest_orderbook_snapshot_bounded`의 caller timeout 뒤 worker가 진행하는 물리 호출도 계측하며, timeout을 취소 완료나 재호출 권한으로 취급하지 않는다.

### 4.2 분봉·체결 이력

`0B → ordered trade journal → completed 1m bars → 3/5/15m context`를 검토한다. 시작 전에 필요한 과거 구간은 `ka10080` REST로 seed하고, 현재 열린 봉은 확정봉 소비에서 제외한다. 기존 [completed bars](../../src/engine/scalping/micro_reversion/completed_bars.py)와 shared bar reader의 역할을 재사용하되 현재 reader의 episode 전용 admission을 Main 승인으로 간주하지 않는다. 현 projection은 SOR/`_AL` 대상이며 raw writer 설정에 의존한다. KRX/NXT가 자동 지원된다고 간주하거나 제거할 episode 환경변수를 Main 설정으로 재사용하지 않는다. Main 공통 writer·설정·reader·마지막 소비자의 이관을 먼저 검증한다.

현재 등록 scope, 순서·누락·writer loss, transport epoch, 수정주가 설정, KRX/NXT/SOR 세션 경계, 부분봉, 장중 기동 이전 이력, 휴장/거래정지/정정 체결을 확인한다. 0B의 제한된 120개 trade buffer로 API가 요구하는 모든 기간을 충족한다고 가정하지 않는다. `ka10003/84`의 aggressor·누적량·시간창과 같은 계산이 가능한 소비자만 전환한다. 지원하지 않는 window는 기존 REST/명시 source gap을 유지한다.

REST seed와 WS overlap은 동일 체결 식별자가 없는 경우 임의 timestamp dedup이나 volume 합산을 하지 않는다. 확정된 분 경계에서 provenance를 나누고 겹친 경계 봉은 REST 확정값과 검증한다. REST로 빈 이력을 채운 사실은 WS 무손실 수신 증거가 아니다. Main-only 전환 시 episode 전용 bar writer를 지우더라도 Main 소비가 남는 공통 journal/projection은 먼저 이관한다.

완성봉은 거래소시각뿐 아니라 durable writer watermark와 소비 시점까지 실제 확정·도착한 범위를 묶는다. 3/5/15분 경계, 무체결 분의 표현, 지연 도착·정정, 세션 간 단절과 수정주가 기준을 기존 소비 계산과 비교한다. 나중에 완성된 봉/seed를 과거 판정에 backfill하지 않는다. journal 확장에 필요한 보존량·디스크/쓰기 비용·consumer lookback을 RW3에 포함하며, 짧은 120개 버퍼를 단순 증대하는 것을 이력 계약 충족으로 보지 않는다.

### 4.3 수급·지수·발굴

`get_program_flow_realtime`는 이미 `0w` 우선이다. 다만 helper는 수신 type/값 존재를 보며 freshness/정확 route를 직접 보증하지 않는다. 소비자까지 시간/route/세대 검증을 연결한 후 재사용 범위를 결정한다. 공식 `0w` FID204의 원 단위와 `ka90008` 금액의 백만원 단위, 설명이 불완전한 FID208/212/213, 전일 fallback과 당일 현재값을 구별한다. REST 삭제를 위해 unknown 단위를 추정하지 않는다.

`ka10046`의 5/20/60분 체결강도는 단일 `0B/228`과 같지 않다. 공식 집계식·충분한 구간이 확인되기 전 기존 값/REST를 유지한다. `0F` 외국계 거래원 추정은 `ka10059/61/63/64/66` 투자주체 집계와 같지 않다. `0J` 최신 지수 역시 `ka20006`의 20일 평균 이력을 대신하지 않는다.

`get_index_daily_ka20006`의 현재 반환은 최신/5거래일 전 지수 2값이며 SignalRadar의 20일 평균 계약과 다르다. RW1은 공식 `inds_dt_pole_qry`의 날짜·순서·부호/배율·유효 20거래일·기준일 포함 여부를 검사하는 소비 경로를 사용하고, 기존 2값 helper의 다른 caller를 깨지 않는다. 부족한 이력/NaN을 평균에서 조용히 제외하지 않는다. FDR→키움 순서와 보수적 실패 동작을 유지하되 원천 실패를 별도 기록한다. 동기 EventBus callback의 FDR/키움 네트워크 작업은 기존 latency owner와 함께 준비 worker/검증된 결과 소비로 옮기는 안을 포함한다. 과거 결과의 허용 age·deadline은 해당 소비 계약에서 정하며 stale cache로 숨기지 않는다.

`ka00198/10016/10018/10019/10021/10023/10027/10028/10032/10054`의 전시장 발굴을 현재 감시 중인 수십 종목의 WS로 대체하면 미감시 기회를 잃는다. REST discovery panel과 후보 편입 후 WS update를 구분한다. scanner-prune BBO/census는 이미 구독된 exact item에 한해서 causal WS 재사용을 검토하고, 미구독 전시장 후보를 절감 명목으로 제외하거나 모두 구독하지 않는다. sparse REST 관측은 continuous WS path와 분모를 합치지 않는다.

### 4.4 소비자별 전환 증거

API 이름이 같아도 consumer 요구가 다르면 별도 판정한다. 구현 전에 아래 행을 실제 callsite ID/함수와 연결하고 **필수 필드·단위·최소 이력·허용 age·route/session·원천 소유자·fallback budget**의 현재 값을 고정한다. 아직 확인하지 못한 값은 `unknown`이며 해당 consumer의 전환만 보류한다.

| 소비 목적 | 재사용 조건 | 유지할 경계 |
| --- | --- | --- |
| Main entry prepare/동일 평가의 machine·auxiliary context | 같은 cutoff·exact scope의 불변 view, 0B/0D 및 계산에 필요한 이력 검증 | 후속 재평가/submit은 현 시각·가격·계좌 상태 재검증; 같은 평가 view를 다음 평가로 연장하지 않음 |
| 보유·청산/잔량·scale-in/장외·매도 후 관측 | 각 handler의 요구 필드·lookback·우선순위를 별도로 입증 | entry 성공 시험을 holding/exit 적용 증거로 사용하지 않음; force·긴급 exit·계좌/수량 검사는 유지 |
| tape/분봉/프로그램·강도 분석 | window 전체 coverage·단위·집계·원 시각 일치 | 현재 tick으로 역사 집계/전일 값을 대체하지 않음 |
| scanner/probe/pruned BBO/census | 원 관측 cutoff에 이미 수신된 exact item/type, 유효 lease | 전시장 후보/관측 offset·valid-empty·미관측 분모 유지, 미래 packet으로 과거 observation 채우지 않음 |
| 실행 직전 BBO/계좌·capacity | 기존 독립 REST/계좌 안전 계약 | 이번 source-only 절감의 제거 대상에서 제외 |

parity는 보존 입력 replay에서 정규화·계산·판정 의미를 비교한다. 자연 WS/REST 수신시각 차이로 값이 달라진 것을 곧바로 결함 또는 개선으로 판정하지 않는다. 정상적인 새 tick, 의미 불일치, 기존 원천 결손 수정의 차이를 원 시각과 함께 분류한다. 기존 오류/결손값에 맞추기 위해 잘못된 입력을 복제하지 않는다.

### 4.5 결손·동시 요청·deadline

§4.4에서 전환 적격으로 확인한 시장 source-only 요청은 적격 WS view → 동일 key의 유효 cache/진행 중 요청 → 기존 admission 안의 bounded REST → 명시 source gap 순으로 처리한다. WS 전용 mode나 기존 계약상 fallback 금지 consumer는 그 금지를 유지한다. frozen observer의 cache-only 계약에 새 HTTP/대기 권한을 부여하지 않으며 계좌/capacity에는 이 WS 선택 순서를 적용하지 않는다. key는 API/정규화 payload·real/demo/token scope·exact route·기간/수정주가·source 목적을 포함하며 서로 다른 priority/force/fresh-query 요구를 임의 결합하지 않는다. market cache와 account cache를 분리한다.

남은 deadline은 admission wait·네트워크·page/retry·decode/검증·소비 전달까지 포함한다. caller 대기 종료는 물리 worker 취소가 아니다. 늦은 응답은 원 timestamp/key로만 보관하고 만료된 판정/계좌 세대에는 적용하지 않는다. follower마다 자체 deadline/validity를 재검증하며, reconnect·동시 miss 시 caller마다 새 REST를 시작하지 않는다. 기존 rate reserve·우선순위·cooldown·max pages/attempts 안에서 복구하며 WS 결손을 이유로 조회 budget을 늘리지 않는다.

## 5. WS 부하와 구독 관리

10:37:34~10:38:04 KST, Main PID70105/v4의 30.17초 읽기 전용 표본은 local registry 22~25 exact items, cap56, 관측 target20 중 양쪽 타입 수신18, target 0B/0D 약83.2개/초, WS TCP 수신 약116.7KB/초였다. 이 수신률은 관측 target subset이며 전체 wire message 수가 아니다. TCP bytes는 TLS/WS overhead 포함이다. Main CPU92.8% 한 코어와 RSS 약1.46→1.47GiB는 전체 Main 값이다. 다른 실행 작업과 조사 프로세스가 같은 호스트를 사용했으므로 격리 benchmark가 아니다.

같은 표본의 dashboard `capture_lock_ms`는 60.5~86.4ms다. 이는 lock 획득 후 snapshot을 만드는 해당 임계구역 측정이다. 전체 WS lock 측정과 계측 범위가 다르다. 10:37:30 누적 성능 영수증은 warm loop87회 p95=5.79초/p99=9.13초, 별도 WS lock 표본 최근4096개 p99 wait=87.4ms/hold=23.1ms다. cap 여유만으로 구독을 늘릴 근거가 부족하다. [지연 개선 계획](main-evaluation-loop-latency-remediation-plan-2026-10-08.md)의 잠금·snapshot 개선과 중복 구현하지 않는다.

1. 기존 Main WS 연결을 유지한다. `00` 계좌 receipt, Main 보유/청산, fixed watch와 유효 watch, source-only 관측/짧은 discovery lease의 우선순위·정확 owner를 기록한다. Main/수동관리에 필요한 공통 수신은 보존하되 episode 잔여 수량만으로 전용 구독·자동 관리의 유지/복구를 요구하지 않는다. 실제 생존 소비자와의 공통 의존성을 확인해 제거 계획으로 인계한다.
2. owner별 desired item/type/group, sent, ACK, first-valid, last-valid, release를 별도 관리한다. 공용 item은 refcount/lease가 모두 끝나야 REMOVE한다. transport 재접속은 기존 receipt를 새 epoch의 유효 원천으로 재사용하지 않으며 계좌/시장/보유/활성 watch 순서로 재등록·대사한다.
3. 7분 동안 `zero_base_exact_probe` REG 시도96건이 있었다. 영구 동시 구독96개가 아니다. 잦은 lease 교체의 REG/REMOVE·대기·첫 수신 실패를 측정하고 기존 protected capacity 안에서 중복 제어패킷을 줄인다. ACK 미수집/전송 성공만으로 활성화를 확정하지 않는다.
4. `0w/0F`는 현재 필요 소비자에만 유지한다. 타입별 bytes/처리시간/유효 소비율 없이 임의 제거하지 않는다. 0D가 필요 없는 후보에 type별 구독을 나눌지는 정확 consumer 증거 이후 검토한다.
5. raw0B/0D 원천은 기존 무손실·순서 계약을 보존한다. 최신상태 EventBus 병합과 raw row drop은 다르다. state receipt 큐, pending tick age, ingress→parse→raw→consumer 지연, writer queue/depth/high-water/drop/error, fsync/RSS, lock wait/hold를 함께 측정한다. queue 증가로 지연을 숨기거나 역압 때 주문/체결 receipt를 버리지 않는다.
6. `036930_NX`, `403870_NX`는 표본에서 해당 epoch의 첫0B/0D 미수신이다. 전송 기록만으로 성공/실패·NXT 거래가능 여부를 판정하지 않는다. exact-date eligibility/session/ACK/수신 기대 계약을 대조하고 unsupported/no-trade/gap을 구분한다.

RW5a는 RW2/RW3에 필요한 **해당 source의 최소 readiness 검증**이다. exact item/type/route/epoch·기존 freshness·필수 필드·consumer 요구 coverage를 전환 전에 확인한다. full refcount/lease/queue 개선은 RW5b로 구분한다. 공식 packet에 임의 request ID를 추가하지 않으며 control 응답이 개별 item/type 작업까지 식별되지 않으면 ACK는 `unattributed/unknown`으로 남긴다. 제어 작업 순서/세대를 대조할 수 있는 범위만 귀속하고 late ACK/packet으로 해제된 lease를 되살리지 않는다. ACK 부재를 첫 유효 수신으로 위조하지 않되, 공식적으로 식별 불가능한 ACK를 기존 유효 packet 재사용의 새 필수 gate로 만들지도 않는다.

부하 모델은 `타입별 유효 item 수 × 관측 평균/peak message rate × 평균 bytes/처리시간`에 REG/REMOVE와 raw writer·snapshot 비용을 더한다. frame 수와 한 REAL frame 안의 data record 수, decoded bytes와 TCP/TLS bytes는 별도 단위로 센다. 구독 재사용이 늘어도 Main consumer 처리·복사·journal 비용이 늘 수 있으므로 REST 감소와 WS/CPU/queue 증가를 함께 보고한다. 현재 전체 type별 frame 수/peak·ACK·최종 consumer lag 계측이 없으므로 전체 부하의 상한과 추가 구독 가능량은 **미확정**이다. 200종목까지 선형 외삽하지 않는다.

## 6. 전송 계측과 계좌 호출 절감

RW0는 audit에 나열한 11개 물리 HTTP 코드 지점과 86개 endpoint 지정 지점을 §3.1의 생존/퇴역 분류로 연결한다. 하나의 transport attempt는 하나의 고유 ID만 센다. wrapper·follower·retry/page·중복 로그를 별도 차원으로 남긴다. auth/order/read는 별도 집계하며 orders를 test 호출하거나 재전송하지 않는다. 동적·callback caller는 callsite ID와 `request_owner`로 연결한다.

분당 bounded 집계에 API ID/owner/PID+start ticks/release, request class, token-origin scope digest, exact route/session, cache hit/miss, admission wait/defer, HTTP attempt/page/status/return code/timeout, elapsed, bytes, follower HTTP0 및 unknown을 남긴다. 계좌·token·payload 원문은 로그에 저장하지 않는다. 정상 전송도 집계하되 tick마다 동기 로그를 늘리지 않는다. sliding gate 파일은 직전1초 상태일 뿐 누적 호출 원장이 아니다.

attempt는 물리 transport 호출 직전 시작하고 완료/timeout/예외를 같은 ID에 닫는다. 이는 client 전송 시도 수이며 서버 수신·처리 성공 증명은 아니다. 페이지별 요청, 인증 후 재시도, 네트워크 retry는 각각 별도 attempt이고 logical request/leader ID로 연결한다. admission 거부·cache hit·follower는 자체 HTTP0을 명시한다. 중단/PID 교체 뒤 완료가 없는 attempt는 `inflight/unknown`으로 남긴다. 요청 시작 KST 날짜/세대와 완료 시각을 보존하고 자정·PID 전환 구간을 억지로0에 맞추지 않는다.

계측 coverage는 `알려진 생존 transport 중 연결된 지점 / 알려진 생존 지점`과 미확인 caller 목록을 함께 제시한다. 성공 로그만으로 분모를 만들지 않는다. read/order/auth별 `started = terminal + inflight/unknown`을 집계창의 경계 이월까지 대사한다. 고유 ID는 제한된 진단 원장에, 상시 지표는 bounded 차원/집계에 남겨 cardinality·writer I/O 폭증을 피한다. RW0 자체의 CPU/lock/queue·저장 비용도 기준선에 기록한다.

절감 비교의 logical demand는 source 선택/성공 여부를 알기 전의 같은 목적 요청을 센다. unavailable/defer/실패 수요도 남기고 유효 원천 비율을 별도로 계산한다. 성공한 평가만 분모에 넣어 원천 누락을 절감으로 보이게 하지 않는다.

계좌는 현재 `_get_loop_cached_deposit`, account snapshot/reconciliation, capacity exact key를 유지한다. `00`의 주문접수/체결/취소/거부 및 선택적으로 검증된 `04`는 cache invalidation과 필요한 reconciliation을 촉발할 수 있다. WS 이벤트가 없었다는 사실로 입출금/수동 주문/외부 변경이 없었다고 증명할 수 없으므로 기존 account refresh/fresh submit·residual·scale-in 검사를 생략하지 않는다. `04` 추가는 별도 공식 parser/계좌 귀속·누락 회복 검증 후의 선택 항목이며 P1 절감 선행 조건이 아니다.

오류 사례의 사전 capacity는 connect/read 각각0.15초, 1회 시도였다. `034020/76,700원`, admission3.044ms, HTTP1회 뒤 receipt 없음이 직접 증거다. 429/1700 또는 주문 거부 증거는 없다. 7분 Main 표본의 prefetch16회 중14성공/2실패, observer15회는 HTTP0/유효 재사용10회였다. 일반 평가의 BLOCK/RECHECK도 관측상 capacity를 요구할 수 있으므로 **ENTER_NOW만 조회**로 일괄 바꾸지 않는다. 원천 분모·미래정보 backfill·exact-price validity와 기존2초/관측5초를 보존한 중복만 제거한다. timeout/TTL 확대와 retry 증가를 절감안으로 삼지 않는다.

## 7. 구현 순서와 종료 기준

| 단계 | 변경/검증 owner | 구체적인 종료 증거 |
| --- | --- | --- |
| RW0 | utils read control/transport + Main monitoring | 모든 생존 HTTP 지점에 실제 attempt 계측 연결, retry/page/follower/defer/실패의 계수 중복0, 기존 safety 불변. Main-only/삭제 전 episode 분모 분리. |
| RW1 | signal_radar + 공통 지수 source/latency owner | ka20006 공식 path/body/response fixture, 유효20일/MA·기존 실패 동작 보존. 2값 helper와 분리하고 WS callback의 동기 외부 I/O를 준비/소비로 분리한 경로 검증. |
| RW2 | Main market adapter + handler prepare | 기존0B/0D exact source로 source-only/준비 호출 감소, 원 시각/입력·판정 parity, 소비 불가 때 기존 recovery/차단. 최종 REST guard 유지. |
| RW3 | Main 공통 completed-bar/tape owner | seed→live overlap·누락·재접속·수정주가·세션·확정봉·history 길이 회귀, 충족한 window만 REST polling 대체. episode 전용 import 없이 Main 소비. |
| RW4 | Main capacity/분석 context | existing cache hit/follower/정확 가격 변화·계좌 변경·expiry를 구분, 반복 preparation 감소 및 관측 coverage 보존. 수급/지수는 미확정 단위/집계 해결분만 전환. |
| RW5a → RW5b | WS manager + 기존 loop latency owner | a: 전환할 consumer의 최소 readiness/원천 품질 검증. b: protected/refcount/type/ACK 귀속/lease·full-history 격리, raw 보존, pending lag/queue·dashboard lock 개선. cap·소켓·freshness 가드 불변. |
| RW6 | 현재 release/PID 인계 owner | 승인된 구현의 리뷰→수정→재리뷰→targeted validation 뒤 배포 범위 확인. 정확 release/정책/PID 및 비교 가능한 자연 window의 절감과 source-quality 별도 확인. |

단계 번호는 순차 실행 강제가 아니다. 의존성은 **RW0(대상 분모) + RW5a(해당 source readiness) → RW2**, **RW2 + 공통 writer/reader 이관·이력 계약 → RW3**, **RW0 + 계좌/분석 consumer 계약 → RW4**, **전환 대상의 리뷰/시험 → RW6**다. RW1은 독립 결함 수리로 진행할 수 있다. RW5b는 기존 latency 작업과 병행하며 관련 source에 영향을 주는 변경은 그 source의 적용 전에 검증한다. 전체 episode 제거·모든 WS 관리 개선이 끝날 때까지 이미 적격인 Main 부분군의 절감을 묶어 두지 않는다.

RW0 결과로 P1 내부 순서는 실제 물리 전송량·deadline 영향 순으로 정한다. source-only의 한 consumer/정확 route에서 보존 입력 검증→기존 허용 관측 범위 검증→승인된 적용→자연 계측 순으로 확대한다. 비교를 위해 추가 broker REST·WS 구독을 보내는 shadow double-read는 하지 않는다. 개발 위치는 기존 utils transport/`trading/market` adapter/`scalping` context/`monitoring` 집계를 우선하며 engine root에 새 Python 모듈을 만들지 않는다. source owner가 episode에서 Main으로 이동하면 마지막 producer/consumer와 제거 계획을 같은 변경으로 인계한다.

[평가루프 후속 LP7~LP12](main-evaluation-loop-latency-remediation-plan-2026-10-08.md#14-lp7lp12-실행-계획)와는 대상 API의 물리 요청 ID·attempt timing을 연결한다. 기존 유효 view 재사용·원 claim deadline 전달은 전체 API 전환 완료를 선행 조건으로 두지 않는다. 원천 선택 변경은 위 RW 의존성을 그대로 따르며 provider deadline을 이유로 최종 REST/source guard를 제거하지 않는다. provider timeout은 남은 유효시간으로 제한하고 age≤2초 성능 목표를 새 호출 cutoff로 쓰지 않는다. fixed-watch/scanner coverage와 episode OFF 전후 window를 나눠 거절·관측 중단을 지연/REST 절감 성공으로 표시하지 않는다.

검증은 보존 응답/모의 transport로 TTL 경계, 계좌·token 교체, 동시 miss, follower expiry, late response, reconnect, partial frame, 중복/역행 tick, silent interval, type/route 불일치, queue-full, open order/late fill/cancel/SELL 우선순위를 재현한다. 신규 broker/provider 실호출과 전시장 구독은 검증 수단으로 쓰지 않는다. 수급 unknown이나 incomplete window가 정상값/0으로 바뀌면 실패다.

자연 검증은 §3의 baseline/treatment 계약으로 기록한다. 초기 수집 제안은 정상15분 창3개와 관측된 peak window이며 거래/session 특성에 맞춰 owner가 확정한다. 이는 코드 종료·사용자 지정 초기 정책 채택의 추가 최소 표본 gate가 아니다. 재접속·장경계 반례는 보존 packet replay로 시험하고 실제 미발생분은 자연 미관측으로 남긴다. 기존 latency 목표와 유효 source coverage를 함께 확인한다. 절감률 목표는 RW0에서 확인한 대상별 기준선·전환 가능한 호출/유지할 REST/최대 fallback budget을 근거로 고정한다. 전체50% 같은 임의 목표를 선언하지 않는다.

수용 결과는 API/owner/consumer별 logical demand·HTTP attempts·cache/WS reuse·fallback·valid-source/unknown·loop/last-consumer lag·WS/CPU/queue 비용을 함께 낸다. demand0/분모 결손이면 절감률은 null이다. 동일 scope에서 원천 coverage가 줄거나 queue/마지막 소비 지연이 기존 수용 계약을 위반하면 호출 감소만으로 성공 처리하지 않는다. Main 부분군 수용, 전체 계정 계측 결손, 배포/PID 소비, 자연 peak 미관측은 각각 별도 상태다.

## 8. 권한·롤백·검토

metric contract는 `metric_role=runtime_transport_diagnostic`, `decision_authority=none`, `window_policy=exact_pid_release_policy_session_scope_load_window`, `sample_floor=counts_with_explicit_unobservable`, `primary_decision_metric=physical_http_attempts_and_consumer_valid_source_ratio`, `source_quality_gate=original_clock_exact_route_epoch_and_complete_attempt_accounting`, `forbidden_uses=order_authority_threshold_relaxation_policy_promotion_or_profit_claim`다. 신규 필드는 실제 consumer schema와 함께 반영한다.

롤백은 현행 정책/보조·Main-only 경계와 호환되는 검증된 이전 source adapter다. WS 결손 시 무제한 REST 폭주를 만들지 않고 기존 shared admission·fallback budget을 따른다. quote/custody 오독, receipt 유실, 중복 주문, hard exit 지연은 기존 안전 절차로 대응한다. 단순 절감 목표 미달은 후속 개선이며 자동 재기동/매매중단 권한을 새로 만들지 않는다. 퇴역 episode/widget을 rollback으로 복원하지 않는다.

계획 재리뷰에서 ① endpoint/HTTP/callback 정적 목록과 실제 전송량 구분 ② 조사 중 PID70105→76094 변경 ③ 에피소드 전용 전환 제외 ④ pre-submit REST의 독립 역할 ⑤ 04/FID951·0w 단위·분봉 overlap의 미확정 의미 ⑥ registry/ACK/첫 수신 구분 ⑦ 일반 BLOCK/RECHECK capacity 관측 보존을 보완했다. 상세 검증 결과는 [조사 기록](../audits/main-rest-api-ws-callsite-and-load-audit-2026-10-08.md)에 남긴다. 문서 종료는 구현·배포·자연 호출 절감·경제성 완료와 별도다.

추가 요청에 따른 리뷰는 단계 의존성, release 간 비교, 20일 지수 계약, consumer별 age/이력, bounded fallback·attempt 대사, SOR 완성봉의 Main 이관, ACK/sequence의 증거 한계와 생존/삭제 경로 계측 범위를 수정했다. Git 제외 패턴에 걸리던 CSV 대신 같은 376행을 버전 관리 가능한 TSV로 보존한다. 상세 원본 evidence의 `data/report` 경로는 로컬 조사 artifact이므로 배포본에 자동 포함된다고 가정하지 않으며, 인계 시 manifest/hash와 함께 별도 보존한다.

평가루프 후속 계획 재리뷰에서는 최신 수동관리 지시에 맞춰 episode custody/flat을 삭제 선행 조건으로 삼던 문구를 정정하고, LP7~LP12와 RW의 부분군 계측·deadline·source guard 인계를 연결했다. 이 문서 보완은 API/프로토콜 구현이나 런타임 변경을 실행하지 않는다.


## 2026-10-08 승인 구현·리뷰 인계

사용자가 구현·반복 리뷰/보완·배포·재기동을 승인하여 위 계획의 생존 Main 경로를 구현했다. [구현/검증 기록](../audits/main-rest-ws-latency-implementation-review-2026-10-08.md)에 단계별 실제 소비·제외 근거·공식 원천과 성능을 연결한다. 원 5초/native claim·현재 v6/보조·Main-only/cap/quota/최종 주문 보호는 유지한다. WS 분봉은 430봉·전체 prefix가 부족하면 REST를 유지하며, terminal 원문 compaction은 exact attempt 소비 계약 때문에 제외했다. 신규 AI 비교 원장·provider/broker 검증 호출은 생성하지 않았다. 코드 종료와 배포/PID/자연 성능·경제성을 각각 확인한다.
