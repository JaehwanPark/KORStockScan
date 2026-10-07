# 키움 REST 호출의 WS 대체 가능성 전수 조사 — 2026-10-06

## 1. 결론

**대체 가능한 영역이 있다. 가장 유망한 것은 계좌 이벤트를 먼저 소비하는 체결·잔고 갱신, 신선한 정확 경로의 호가 재사용, WS 수신 이후의 분봉 증분 생성이다.** 이미 WS를 우선하는 경로도 있으므로 새 구독을 늘리기 전에 현재 수신 원천을 공용 소비자가 재사용하도록 만드는 것이 우선이다.

- 체결: WS `00`의 주문·체결 원천을 정확한 주문 체인에 결속하면 `kt00007`·`ka10075`·`ka10076`의 정상 구간 반복조회 일부를 줄일 수 있다. 최초 전체 조회, 재접속·결손 구간 복구, 정확한 terminal 대사는 계속 필요하다.
- 비용: 공식 `00`에는 FID `938`·`939`가 있지만 현재 파서가 보존하지 않는다. 원천을 보존할 수 있다는 사실과 주문·owner별 실제 비용을 확정할 수 있다는 사실은 다르다. 누적 범위·귀속·정산 보정을 검증하기 전에는 REST 비용 대사까지 대체했다고 할 수 없다.
- 잔고: WS `04`의 보유수량·매입단가 등을 받아 정상 구간 갱신과 변화 감지를 할 수 있다. 현재 Main은 `00`만 계좌 등록하며 `04`를 등록·소비하지 않는다.
- 시세: `0B`·`0D`·`0w`로 현재 체결·호가·프로그램 흐름 일부를 대체할 수 있다. 과거 봉·체결, 5/20/60분 이력, 최초 40봉, 전체 시장 순위까지 즉시 대체되지는 않는다.
- 대체 근거 없음: `kt00011`의 종목·가격별 매수 가능수량, `kt00001`의 상세 예수금, 실제 투자자 분류 집계, 과거 차트, 마스터·테마·전 시장 신규 발굴, REST 주문 쓰기.

아래는 **조사 및 후속 설계 제안**이다. 코드·구독·서비스·주문·정책을 변경하지 않았다. 기존 초기 정책 승인에 새 경제성 조건을 추가하지 않는다.

## 2. 조사 범위와 현재 실행 원천

- Plan Rebase §1–§8, 10/6 일일 체크리스트 objective/mandatory rules, Kiwoom API Data Contract의 Official Reference Gate를 확인했다.
- 종료 전 재검증한 선택 릴리스: `fd222e315577c10853b23db583f260ef76259b39`, `probe-original-source-20261006-fd222e31` (17:11:07 KST 선택).
- Main 실제 PID `126945`, 실행 사용자 `ubuntu`, `/proc` cwd는 해당 릴리스의 `src`. supervisor PID `126900`도 `ubuntu`다. 조사 초기 PID `60572`/릴리스 `eeccb1f4`는 별도 작업의 17:11 교체로 종료되었으며 최신 소비 PID를 다시 확인했다.
- 최신 릴리스 Python 612개, 작업트리 612개를 AST로 조사했다. 테스트·archive는 현재 호출 목록에서 제외했다. 상수 API ID, 헬퍼 호출, 함수 전달·주입 참조, 직접 transport, 동적 API 인자, deploy shell 참조를 대조했다. 동적 transport 인자는 현재 함수의 상수/공통 API 집합에 결속되어 있으며 새로운 ID는 찾지 못했다. AST parse 실패 0.
- REST API ID **45종의 요청 표면**과 `/oauth2/token` 인증 1종을 찾았다. 이 수는 현재 모든 API가 HTTP 요청 중이라는 뜻이 아니다. 헬퍼만 있는 API, 과거 스캐너 분기, 선택적 복구·연구 producer를 구분한다.
- Main `KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=true`. 실제 scanner 진입은 `run_zero_base_scanner` 후 return한다. 과거 `run_scalper_iteration`의 10개 순위 패널을 현재 Main 호출로 계산하지 않았다. 현재 zero-base 발굴의 중심은 `ka10023`·`ka10027`이다.
- 작업트리에는 별도 진행 중인 코드·문서·생성물 변경이 있다. 조사 도중 교체된 릴리스를 재조사하여 API ID 45종이 동일함을 확인했다. utils/orders/WS/sync/Main loop는 두 릴리스에서 byte 동일하며, 변경된 execution_receipts/state_handlers의 비용·pre-submit quote·capacity read 함수도 AST가 동일하다. source-only 원천/replay 보완은 이번 WS 대체 판정을 바꾸지 않는다. 아래 코드 링크는 조사한 **불변 릴리스**를 가리킨다. 파일별 SHA256과 전체 API→헬퍼→참조 위치는 [API별 코드 참조 및 source hash 목록](kiwoom-rest-ws-substitution-survey-2026-10-06-inventory.md)에 보존했다.
- Widget는 runtime·UI·수집·연구·장후가 영구 폐지된 상태다. 남아 있는 클래스명·과거 profile·계좌 소유 영수증을 현재 Widget 호출이나 재활성화 후보로 간주하지 않았다. Episode gateway도 정의가 존재한다는 사실만으로 현재 실행을 주장하지 않는다. systemd 표시명에 과거 Widget/Episode 문구가 남아 있는 알림 서비스는 실제 주문 producer가 아니다.

### 2.1 공식 원천 검증

- 현재 upstream HEAD를 `git ls-remote`로 재확인했다: `953e5dbff123f437ab4d11a78a95191a685eb51f`.
- 확인·파일 hash 기록 시각: `2026-10-06T17:09:34+09:00`. 같은 SHA의 기존 checkout을 사용했다. 10/2 checkout이라는 디렉터리 이름을 최신성 증거로 사용하지 않았다.
- 이 SHA에는 `kiwoom_docs`가 없다. 공식 packaged spec, `kiwoom/specs.py`, `kiwoom/core/{client,ws_client,errors,auth}.py`, `kiwoom/realtime/{schemas,decoders,packets,stream}.py`, PRD/MOCK Postman을 대조했다.
- [공식 packaged spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json), [WS packet builder](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/realtime/packets.py), [WS client](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/core/ws_client.py), [Postman](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/postman/kiwoom-openapi.postman_collection.json).
- 공식 portal의 `00`/`04` 상세 페이지는 이번 web 도구로 열리지 않았다. `938`/`939`의 누적·귀속·반올림 설명과 `04/951`의 의미를 외부 블로그나 다른 API 제품의 FID 관행으로 채우지 않았다. 예제는 실행 권한이 아니다.
- REST는 API ID별 공식 path/header/body/continuation과 PRD/MOCK 분리가 유지되어야 한다. WS 시세 item의 KRX 원코드·`_NX`·`_AL` 차이를 계좌 API의 원 6자리 코드에 전용하지 않는다. 인증·LOGIN·REG/REMOVE·구독 한도와 기존 읽기 reserve는 이 조사로 바뀌지 않는다.

## 3. API별 전체 판정표

표의 ‘일부 가능’은 **필드와 관측 구간**의 대체를 말한다. REST 헬퍼를 바로 삭제할 수 있다는 뜻이 아니다. ‘공통 헬퍼만’은 AST에서 외부 호출·함수 참조를 찾지 못한 상태이며 런타임 호출량 0의 완전한 증명은 아니다. 조건부/연구/복구 경로도 빠짐없이 포함했다.

### 3.1 체결·계좌·비용 — 9종

| API | 현재 코드 역할 | WS 대체 판정 | 남겨야 할 REST / 결손 조건 |
|---|---|---|---|
| `ka10075` 미체결 | Main boot/45·90초 snapshot, 초기수량·취소/terminal, adaptive-exit | `00` 주문 접수·체결·미체결수량을 정확한 주문 체인에 결속하면 정상 구간 일부 가능 | 초기 미체결 전체 목록, process downtime, 재접속, 수동 주문, chain 누락, 날짜·계좌·venue 대사. ‘새 이벤트 없음’을 미체결 없음으로 사용 금지 |
| `ka10076` 체결 | `sniper_sync` 누락 보유 복구 2차 order reference | `00` 체결번호/가격/수량으로 관측 이후 일부 가능 | 시작 전 체결·누락 복구. 공식 `tdy_trde_cmsn/tax`도 원천 범위 확인 필요 |
| `kt00007` 날짜별 주문체결 | Main/S15/초기수량/정확 SELL 복구·주문 체인 대사, episode adapter | `00` + 원주문번호/상태/체결번호 journal이 완전한 구간에서 일부 가능 | `ord_dt`가 있는 주문 원장, 정정·취소 descendant와 confirmed cancel, 종결·missing-event 복구. aggregate 잔고 0으로 대신할 수 없음 |
| `kt00008` 익일결제예정 | 누락 holdings 복구 시 settlement context | 직접 대체 불가. `00/938/939`는 검증 후 비용 대사를 보완하는 후보 | 체결일/결제일/종목별 정산·수수료·세목. order_no/fill_no가 없으므로 그 자체도 정확 주문 증빙이 아님 |
| `kt00005` 체결잔고 | boot/reconnect, 45초 read-only 및 90초 lifecycle, BUY fill 후 snapshot | `04` + `00`으로 정상 구간 잔고 증분/dirty 감지 가능 | 최초 모든 보유·현금/신용/시장 census, gap 복구, 독립 주기 대사, 계좌 전체 aggregate |
| `kt00018` 계좌평가잔고 | startup sync 및 holding/add/terminal/custody 확인 | `04` 보유수량/매입가 + `0B` 표시 시가평가 일부 가능 | 모든 잔고/평가 합계·대용/신용, 수동 외부 변화, 매도가능수량 exact reconciliation. 평가용 수수료를 실제 완료 거래비용으로 승격 금지 |
| `kt00001` 상세 예수금 | watching 예산, sizing/submit, residual account guard | 직접 대체 근거 없음. `00/04`는 기존 예수금 영수증의 invalidation 신호 후보 | 예수금/출금/주문가능/결제 예정/운영 floor exact receipt. `04/951`은 공식 명세에서 Extra Item |
| `kt00011` 증거금율별 주문가능 | `_read_entry_capacity_snapshot`: 종목·가격별 sizing와 준비/관측 | 직접 대체 근거 없음 | 6자리 종목+KRW `uv`, 증거금 tier, 현금·미수불가 주문가능수량. `04/933`을 신규 매수 가능수량으로 전용 금지 |
| `ka10073` 기간별 종목 실현손익 | low_price_two_leg_tuning의 선택적 비용/실현손익 loader | 직접 대체 불가. 검증된 `00` 비용 journal의 종목·일자 합계와 대사 가능 | 종목·일자 실현손익/비용. 여러 owner·회차·수동 거래면 유일 귀속 없이는 주문별 비용 아님. 역사·선택적 producer이며 현재 Main fast loop로 간주하지 않음 |

### 3.2 시세·체결·차트·프로그램 — 11종

| API | 현재 코드 역할 | WS 대체 판정 | 남겨야 할 범위 |
|---|---|---|---|
| `ka10001` 기본정보 | 수동/조건 편입·분석·scanner 보조의 기본정보 | `0B/0A` 현재값, `0g` 기준/상하한 일부 | 시총·주식수·기본정보 full schema/초기 기준값. `0g` 증거금 표시가 `kt00011` capacity는 아님 |
| `ka10003` 체결정보 | zero-base REST 보강, liquidity/분석/gateway | `0B`의 정확 경로 signed tape. zero-base는 이미 WS-first | 시작 전 N건, 표본 부족·reconnect·route gap. 희소 체결과 수신 결함 구분 |
| `ka10004` 호가 | 제출 직전 refresh, bounded quote recovery, 관측 BBO/gateway | 신선한 `0D` depth 및 `0C/0B` 최우선 호가 일부 | quote conflict·stale/gap 독립 대사, 초기 depth. pre-submit safety 동등성 확인 후에만 생략 가능 |
| `ka10005` 일주월시분 | previous-day/multi-timeframe·외부 입력 검증 | 오늘 현재 OHLCV 일부만 `0B` | 과거/기간 chart와 previous-day seed 유지 |
| `ka10046` 체결강도 추이 | legacy gatekeeper/overnight/radar | `0B/228` 현재 strength 가능, 연속 journal에서 trend 후보 | broker의 5/20/60분 강도 계산과 동일하지 않으면 별도 feature. 현재값을 세 시간축에 복사 금지 |
| `ka10080` 분봉 | zero-base 40봉, machine/aux 후행 라벨, holding·gatekeeper, 과거 보강 | `0B`를 분봉으로 누적하고 동일 route/시간/coverage 검증 시 관측 이후 증분 가능 | 최초 40봉, WS 미등록 구간, 손실·재접속, 과거 backfill/완료봉 검증. 당일 분봉 전체를 시작 직후 WS만으로 재현 불가 |
| `ka10081` 일봉 | gatekeeper·외부검증·scanner | 오늘 진행 중인 OHLCV 일부 | 여러 날 MA/수정주가/기업행사·일봉 final seed는 REST 유지 |
| `ka10084` 당일/전일 체결 | holding bounded signed tape, rising-missed guard | 관측 후 exact-route `0B` buffer/journal 가능 | 전일/미관측 과거·gap·희소구간 REST 보강. unit trade/cumulative 값 혼동 금지 |
| `ka20005` 업종 분봉 | multi-timeframe index·offline backfill | `0J`를 관측 이후 minute으로 누적하면 일부 | 과거 index 봉/최초 이력·단위·coverage proof. 현재 stock tick buffer로 업종 차트 전용 금지 |
| `ka20006` 업종 일봉 | ensemble/radar regime 조건부 | 오늘 index OHLC 일부 `0J` | 과거 업종 일봉·MA 유지 |
| `ka90008` 시간별 프로그램 | program helper·분석·radar/gatekeeper | `0w` 현재 흐름. `get_program_flow_realtime`은 이미 WS-first | 전일/시간별 이력·missing program type/clock/정확 route. `0w` 금액 단위·누적/증분 검증 필요 |

### 3.3 발견·투자자·마스터·테마·지수 breadth — 21종

| API | 호출 표면 / 현재성과 구분 | WS 대체 판정 |
|---|---|---|
| `ka00198` 실시간 조회순위 | legacy scanner의 함수 전달 경로; 현재 zero-base Main 분기 아님 | 조회인기도 순위는 `0B` 거래량 순위와 다른 지표. 대체 불가 |
| `ka10016` 신고저가 | legacy scanner | 관측 watch 안에서 근사 가능하나 전 시장 최초 발굴·20일 기준은 대체 불가 |
| `ka10018` 고저가 근접 | legacy scanner | 등록 종목 조건은 계산 가능하나 전 시장·기준 고저가·동일 분모 대체 불가 |
| `ka10019` 가격급등락 | legacy scanner | 관측 이후 수익률 계산 가능; 미구독 시장 순위·과거 기준 구간 대체 불가 |
| `ka10021` 잔량 급증 | legacy scanner | 관측 이후 `0D` 변동 가능; 전체 시장 잔량급증 신규 발견 대체 불가 |
| `ka10023` 거래량 급증 | **현재 zero-base activity panel** 및 legacy/kosdaq | 관측 watch 내 `0B` 변동만 가능. 미등록 종목 신규 발견·1분 비교 panel은 그대로 필요 |
| `ka10027` 등락률 상위 | **현재 zero-base gainer panel**, census 및 legacy | watch 내부 순위만 가능. REST panel과 동일 전 시장 분모/필터를 WS 일부 watch로 만들 수 없음 |
| `ka10028` 시가 대비 | legacy/kosdaq scanner | watch 종목 일부 계산; 미구독 종목 전 시장 발굴 유지 |
| `ka10032` 거래대금 상위 | legacy scanner | `0B/14`로 watch 값은 계산 가능; 전 시장 순위 대체 불가 |
| `ka10054` VI 발동 목록 | legacy scanner | 등록 종목 `1h` 통지는 일부 대체. 전 시장 VI census/누락 이력은 대체 불가; VI type·activation/release clock 계약 유지 |
| `ka10013` 신용 매매동향 | kosdaq/update_kospi 배치 | 신용 역사·분류는 WS 동등 원천 없음 |
| `ka10059` 투자자/기관 | institutional/AI snapshot·분석·배치 | `0F` 외국계 거래원 추정과 `0w` 프로그램은 외국인·기관 실거래 분류가 아님. 대체 불가 |
| `ka10061` 투자자 기간합계 | institutional context | 과거 투자자 분류 기간합계 대체 불가 |
| `ka10063` 장중 투자자 매매 | 공통 헬퍼만; 외부 AST 참조 미발견 | 투자자 분류 집계 대체 근거 없음 |
| `ka10064` 장중 투자자 차트 | institutional context | `0F/0w`로 외국인·기관 시계열 대체 불가 |
| `ka10066` 장마감 투자자 | 공통 헬퍼만; 외부 AST 참조 미발견 | 사후 확정 투자자 분류 대체 근거 없음 |
| `ka10099` 종목정보 리스트 | update_kospi eligibility/NXT universe | 전체 마스터·거래 가능 universe 대체 불가. 갱신 cadence/cache 후보 |
| `ka10100` 종목정보 | 공통 헬퍼만; 외부 AST 참조 미발견 | `0g` 일부 변화만 가능. full master 대체 불가 |
| `ka10101` 업종코드 리스트 | 공통 헬퍼만; 외부 AST 참조 미발견 | 업종 code/name 매핑은 seed/cache 유지 |
| `ka90001` 테마 그룹 | swing_sector_theme_source 조건부 | WS 실시간 가격으로 테마 구성·그룹 마스터 대체 불가 |
| `ka20003` 전 업종지수 | market_panic_breadth collector, 별도 source producer | **`0J+0U`가 대체 후보.** 동일 업종 코드/필터/신선도와 상·하한 중복계수, 상장종목 분모를 검증해야 함. `0U/256` 거래형성종목수는 REST 상장종목수와 같다고 할 수 없음. 전체 표 wght 등 미제공 항목·초기 census는 REST 유지 |

### 3.4 주문 쓰기와 인증 — 5종

| API | 역할 | WS 대체 판정 |
|---|---|---|
| `kt10000` 매수 | Main/S15·IPO·주문 adapter의 승인된 주문 | 대체 없음. `00`은 사후 통보이며 주문 명령이 아님 |
| `kt10001` 매도 | Main·adaptive-exit·승인된 owner exit | 대체 없음 |
| `kt10002` 정정 | adaptive-exit native amend | 대체 없음 |
| `kt10003` 취소 | Main·adaptive-exit·초기수량 주문 체인 | 대체 없음. 취소 통보 수신은 취소 명령 대체가 아님 |
| `au10001` `/oauth2/token` | utils token 발급/cache/recovery; AST ID literal 없는 인증 경로 | WS LOGIN 전에 REST token 필요. WS 자체로 인증 발급 대체 없음. `au10002` revoke 요청 구현은 이번 census에서 미발견 |

대조 합계: 계좌 9 + 시장/차트 11 + 기타 21 + 주문 4 = REST ID 45. 인증 endpoint 1은 별도다. WS 조건검색 `CNSRLST/CNSRREQ/CNSRCLR`는 이미 WS 제어 흐름이며 위 REST 수량에 더하지 않았다.

## 4. 체결·비용 증빙의 구체적 결함과 가능 범위

### 4.1 WS `00`이 이미 제공하는 원천과 현재 손실

공식 FID: 계좌 `9201`, 주문번호 `9203`, 종목 `9001`, 주문상태 `913`, 주문수량 `900`, 미체결 `902`, 누적체결금액 `903`, 원주문번호 `904`, 주문가격 `901`, 체결시각 `908`, 체결번호 `909`, 체결가격/수량 `910/911`, 단위 체결 `914/915`, 거부사유 `919`, 수수료/세금 `938/939`, 실제 거래소 `2134/2135`, SOR `2136`.

현재 `_ORDER_EXECUTION_RAW_FIDS`는 `938/939`, `904`, `901`, 계좌 `9201`, 신용 구분을 보존하지 않는다. `_parse_order_execution_notice`는 명시 `type=00`일 때만 감사 가능한 raw envelope를 붙이고, legacy name fallback은 같은 증명으로 승격하지 않는다. 이 구분은 유지해야 한다.

`_state_event_queue`는 메모리 Queue이고 dispatch 예외는 로그로 남긴다. 이후 일부 exact SELL receipt journal/재처리 경로가 존재하지만, 그것이 **모든 account raw frame이 durable하게 선보존된다**는 뜻은 아니다. 따라서 현재 수신 성공만 보고 REST 복구를 제거할 수 없다.

후속 설계: 현재 00 ingress의 packet receive clock·connection epoch·raw value·source hash를 먼저 append하고, 계좌는 안전한 scope hash로 관리한다. 주문 ACK→부모/정정/취소 child→fill의 owner registry 결속, 날짜+계좌+주문+체결번호 dedup, cumulative/unit 중복 방지, out-of-order/재전송/동일 번호 다음 날짜/late parent fill을 검증한다. 확인 취소수량 `C`, 실행체결 `F`, 원수량 `Q`를 별도로 대사하고, 미확정 `R`과 chain gap을 남긴다. `Q=F+C`와 `R=0` 및 정확한 체인 증명 없이는 terminal로 닫지 않는다.

### 4.2 실제 비용을 WS만으로 확정할 수 있는가

**현재 확정할 수 없다.** `938/939` 값이 있다는 것은 비용 원천 수집 기회다. 공식 packaged spec에는 ‘당일매매수수료/세금’ 명칭이 있으나 per-fill/per-order/account-day 누적 범위와 최종 정산 수정·반올림 설명이 없다. 원천 값은 보존하되 그 의미를 임의 배분·단순합산·연속 차감으로 정하지 않는다. 표본 1건 일치만으로 여러 주문·여러 owner 일반화를 하지 않는다.

Main `_main_lifecycle_exit_economics_fields`의 현재 cost basis는 `configured_trade_cost_rate`, broker actual fee-tax는 `None`이다. 설정 비용을 gross-net로 역산한 값은 실제 브로커 비용이 아니다. 구현 후에도 원천 수준을 `configured_estimate`, `ws_reported_unallocated`, `broker_reconciled_exact` 등으로 분리하는 설계가 필요하다. 이 명칭은 후속 schema 제안이며 현행 필드가 아니다.

비용 대사 후보:

- `ka10075/ka10076`의 `tdy_trde_cmsn/tax`: 날짜/주문/체결 scope 검증 후 사용. ‘당일’ 필드의 반복 row를 모두 합산하지 않는다.
- `kt00008`: 결제일·종목·수수료·세목 정보. 주문/체결번호가 없어 복수 owner/회차를 임의 분배하면 안 된다.
- `ka10073`: 종목·일자 실현손익/비용. 유일 identity가 증명된 경우에만 exact attribution. aggregate 일치가 모든 주문별 PnL 일치를 증명하지 않는다.
- `kt00018`: 매입수수료·평가수수료·세금 등 평가/잔고 항목. 이를 완료된 실제 체결의 최종 비용과 동일시하지 않는다.
- 슬리피지: 실제 fill price 외에 **판정/제출 당시 동일 route의 실행 가능 bid/ask 영수증**이 필요하다. 시장 `0B` 체결은 내 주문 fill이 아니며, 미래 quote·중간가·당일 최저가를 체결가 기준으로 쓰지 않는다.

불명/누락 비용은 null·source_gap로 남긴다. 보고용 진단, 모델 비용 추정, actual completed economics는 구별한다. 비용 원천 확정 결손이 quote/position의 독립적인 WS 최적화까지 전체 차단하는 사유는 아니다.

### 4.3 잔고 `04`의 한계

`04`는 `930` 보유수량, `931` 매입단가, `932` 총매입가, `933` 주문가능수량, 신용·대출 구분 등을 제공한다. 이는 잔고 문맥의 정보다. 종목·매수가격·적용 증거금 tier에 따른 신규 BUY 수량 `kt00011`과 동등하다는 근거가 없다. `951`은 이번 공식 명세에서 **Extra Item**이다. 예수금으로 이름을 바꿔 쓰면 안 된다.

bootstrap 전체 REST snapshot을 기준으로 `00/04` 변화를 적용하는 동안에도 connection epoch, 소비 commit/journal watermark, reconnect/gap, manual/external trade, 모든 account/credit/venue 분모를 관리해야 한다. `04` 이벤트가 없다는 것은 보유가 없다는 뜻이 아니다. account market-scoped data를 공용 시장 캐시에 넣지 않는다.

## 5. 현재 경로에서 실제로 줄일 후보

### 5.1 45초 snapshot / 90초 lifecycle 계좌 조회

Main `BROKER_SNAPSHOT_REFRESH_INTERVAL_SEC=45`, `ACCOUNT_RECONCILIATION_INTERVAL_SEC=90`. 두 경로는 single-flight로 조정되며 90초 작업이 먼저 수행되면 snapshot 시간도 갱신한다. 이를 독립적인 두 주기가 언제나 동시에 호출하는 것으로 합산하면 과장된다. `refresh_broker_account_snapshot_read_only`는 `kt00005`와 `ka10075`를 읽으며 BUY fill 후에도 호출될 수 있다. `periodic_account_sync`는 exact terminal 복구까지 소유한다.

개선 후보: `00/04` 이벤트를 freshness/dirty 신호로 소비하고, 완전하고 신선한 증분 상태를 holding context가 먼저 읽게 한다. 변화 없는 정상 구간 REST poll을 생략/완화하되 부팅, 재접속, journal/owner gap, 수동 변화, 독립 대사 SLA에는 REST를 유지한다. 단순 타이머 연장으로 현재 영수증이 늙어 holding/submit을 막지 않도록 consumer freshness 계약도 함께 설계해야 한다. 정해진 새 주기나 예상 절감률은 이번 조사에서 확정하지 않았다.

### 5.2 제출 직전 호가 refresh

현재 Main env에서 REST orderbook refresh는 true이며 `_pre_submit_refresh_rest_orderbook_snapshot`은 해당 guard들을 통과하면 WS가 이미 신선한지에 따라 먼저 생략하는 분기 없이 `ka10004` 요청을 수행한다. 정확 route/epoch의 `0D` quote depth가 소비 마감까지 fresh하고 기존 quote consistency guard와 동등하면 중복 요청을 줄일 후보가 된다.

후속 구현에서는 stale/diverged/route conflict, independent reconciliation, force의 목적을 유지한다. freshness threshold를 느슨하게 하거나 REST off env만 바꾸는 조치는 이 조사 결론이 아니다. 제출/수량/보호 guard는 그대로 유지한다.

### 5.3 분봉·후행 가격 원천

현재 zero-base probe는 candle 40개를 REST로 확보하고, candle 처리 후 WS를 다시 확인한다. signed tape는 exact WS가 충분하면 REST를 읽지 않도록 이미 구현되어 있다. 반면 미래/현재 봉 공용 소비를 제공하는 Main 전체 범위의 WS 완성봉 증명은 이번 조사에서 확인되지 않았다. 기존 micro-reversion observer completed-bar 기능은 제한된 관측 producer이며 그 존재만으로 기계/AI 입력의 대체 권한을 갖지 않는다.

WS 분봉은 symbol+item route+market session+KST date+epoch로 분리하고, REST seed와 겹치는 timestamp를 중복합산하지 않는다. signed per-trade volume과 누적 volume을 구별하며 zero/빈 봉, quiet tape, 손실, late tick, half bar, 장경계와 기업행사 adjustment를 검증한다. packet sequence가 로컬에서 연속이라고 거래소 이벤트 누락이 없었다는 것은 아니다.

장후 후행 라벨은 **향후 실제 수신한** exact-route journal이 price horizon을 충분히 덮으면 재사용할 수 있다. 과거 미수신을 복구했다고 주장하지 않는다. minute 봉은 intrabar 목표/손절 도달 순서를 확정하지 못하는 경우가 있고, 가격 경로가 있어도 비용·entry plan·owner replay는 별도 계약이다. WS 대체로 BLOCK/RECHECK의 경제성 결손을 0손익 또는 임의 stop으로 채우지 않는다.

### 5.4 Gatekeeper 분석 context의 추가 demand

`build_realtime_analysis_context`는 WS snapshot을 받으면서도 `ka10046`, `ka10003`, `ka10080`, `ka10081`, `ka10059` producer를 호출한다. 단순 수동 브리핑만이 아니라 legacy watching 최종 gatekeeper에도 caller가 있다. 내부 TTL/cache/single-flight 때문에 producer 호출이 모두 HTTP는 아니다. 실제 선택된 entry branch를 증명하지 않은 채 현재 Main 판정 1건당 5HTTP라고 계산할 수 없다.

현재값/tape는 정확한 WS 영수증으로 재사용하고, 과거 일봉·투자자·강도 trend 등 동등 원천이 없는 feature는 별도 cache/required-fetch로 분리할 후보다. `get_program_flow_realtime`는 이미 `0w`를 우선하지만 type 존재/기존 nonzero 값만으로 quote와 동일 신선도를 주장해서는 안 된다. 수신 clock·route·epoch·누적 단위가 필요하다. source manifest는 WS/REST/cache의 실제 관측시각을 구분해야 한다.

### 5.5 지수·breadth

market_panic_breadth collector는 `ka20003` snapshot을 사용하고 `0J/0U`를 문서상 대안으로 언급한다. Main WS에는 현재 `0J/0U` 등록·파싱 경로가 확인되지 않았다. 두 시장 대표 index를 추가로 받는 설계는 후보지만 전체 종목 구독으로 순위를 대체하는 설계는 아니다.

seed된 업종 코드/상장종목 분모와 `0J/0U`의 current index·상승/하락 counts를 동일 시각/모집단으로 대조해야 한다. market weakness guard가 소비하는 기존 의미와 일치하기 전에 값을 교체하지 않는다. 공식 generic index FID 단위 설명의 적용, 제외종목과 상·하한 포함관계도 검증 대상으로 남긴다.

## 6. 오늘 로그로 확인한 호출·대기 증거

bounded log snapshot은 `2026-10-06T17:07:42+09:00`에 고정하여 `2026-10-06` line만 사용했다. 종료 직전 릴리스 교체 이후의 모든 로그를 포괄하는 장부가 아니다. 과거 파일 전체나 모든 raw trace를 재생성하지 않았다.

- `kiwoom_utils_info.log`: 오늘 `KIWOOM_READ_TR_DEFERRED` **19행**. `ka10080/zero_base_machine_probe` 15행, `kt00011` preparation/observation 4행. 여러 릴리스 PID가 섞여 있으므로 현재 PID 오류로 합산하지 않는다. 조사 초기 PID `60572` candle defer는 이 snapshot에서 1행이다.
- 해당 defer의 `deferred_attempt_sent=false`는 **그 시도**가 전송되지 않았다는 뜻이다. `prior_http_attempt_count`가 있으면 이전 page/retry의 HTTP와 구분한다. 19행을 ‘19건 broker HTTP 실패’로 보고하지 않는다.
- `ENTRY_CAPACITY_READ`: 오늘 보존된 **349 logical row**, transport metadata가 알려진 HTTP attempt 합 **218**, unknown HTTP row 0. 이는 이 함수의 kt00011 읽기만 측정하며 전체 Kiwoom HTTP가 아니다.
- 조사 초기 PID `60572` (16:05~17:11 실행): preparation 30 logical/30 HTTP, operating observation 30 logical/0 HTTP. observation 중 exact reuse 23, expired 7. observation 0HTTP가 capacity 성공 30건을 뜻하지는 않는다. 일부는 결손을 그대로 남겼다. 이 범위에서 재사용은 이미 작동하고 있으며 이를 WS 대체 절감으로 계산하지 않는다.
- shared coordinator 파일은 rolling admission 상태이고 성공 HTTP 전체를 API별 누적하는 장부가 아니다. 일반 API는 성공·재시도·page 전체에 대한 통일 transport counter가 부족하다. 따라서 이 조사로 ‘전체 호출의 X%가 WS로 감소’ 또는 특정 최적 주기를 확정하지 않았다.

후속 성능 측정은 기존 transport 경계에서 credential/account를 노출하지 않는 API ID/PID/owner/purpose/date/HTTP attempt/page/retry/admission wait 로그를 사용한다. 비교는 동일 실제 실행 window·universe·venue/session·결정건수를 사용하고, logical demand와 실제 HTTP, p50/p95 결정 지연, WS ingress/consumer lag, defer/source_gap, REST 대사 불일치, terminal/economic 귀속을 함께 본다. HTTP 429가 없다는 이유만으로 여유를 선언하지 않는다.

## 7. 후속 구현 우선순위와 완료 조건

아래는 제안이며 이번 조사에서 구현·OPEN 작업 생성·배포를 실행하지 않았다. 본문에 정의한 비용 scope·문서 결손은 quote 등 독립 영역의 작업 완료와 분리한다.

| 순서 | 제안 / 기존 owner | 완료 조건 | REST 유지·rollback |
|---|---|---|---|
| 1 | `kiwoom_websocket`→`sniper_execution_receipts/sniper_sync`: `00` raw 비용·원주문·account scope 보존, durable ingress/owner journal, `04` 잔고 source consumer | partial/full, cancel/amend/late fill/duplicate/out-of-order, epoch·날짜/계좌/owner 충돌, raw append 실패/재시작, manual 변화 시 격리; WS와 REST exact identity·수량·가격 대조. 비용 의미 미확정은 null 유지 | 부팅/reconnect/gap/terminal/정산 REST. journal·source 소비 불완전하면 현재 REST 경로로 복귀 |
| 2 | `sniper_sync/kiwoom_sniper_v2`의 event-first broker snapshot | 정상 변화와 quiet 구간에서 holding context 신선도·전체 census 계약 유지, polling HTTP 감소와 대사 mismatch 없음; change event 없다고 flat 판정하지 않음 | 정기 독립 대사 SLA 및 exact terminal owner 유지; freshness/불일치면 poll 복귀 |
| 2 | `sniper_state_handlers` 제출 전 quote와 `kiwoom_utils` context의 WS 영수증 재사용 | stale/diverged/route/epoch/누락별 guard 결과가 기존과 동등; orderbook/tape required feature 정상. 같은 stale 값을 skip으로 숨기지 않음 | force/conflict/gap REST 및 현재 guard 유지 |
| 3 | 기존 market-data/완성봉 producer를 공용 source consumer로 확장; 기계·AI 후행 라벨 재사용 | 동일 완료봉/route/date seed overlap dedup, quiet/gap/half-bar, signed volume/cumulative, horizon/stop-order ambiguity, caller schema/hash 보존. 귀속 안 된 비용/owner는 별도 gap | 최초 이력/과거 backfill, 결손행 정확 REST 보강; 전체 raw 재계산 강제 없음 |
| 4 | `market_panic_breadth_collector`의 `0J/0U` 수신 소비 | 동일 code·모집단·단위·분모·상하한 포함관계/수신시각 검증, 기존 guard 의미 동등, source/lag/budget counters | initial census 및 누락/불일치 `ka20003` 유지 |

샘플 검증은 위 경계의 비용·시간순 실제 영수증을 사용하고 요청을 mock하여 재접속/중복/partial/결손을 주입한다. 성능 replay는 동일 원천의 baseline/candidate를 비교한다. 훈련/검증 미래 누출, frozen attempt의 미래 영수증 소급, 서로 다른 source-era/venue, 생존편향을 배제한다. guard 보존과 source 완전성, 실제 요청 감소는 각각 증명하며 승률만으로 비용/종결 또는 정책 승계를 대체하지 않는다. 구독 예산·receive loop latency와 기존 Main/manual/역사 custody를 보호하고 retired consumer를 복원하지 않는다.

## 8. 주요 producer → consumer 코드 근거

- [00 raw FID allowlist](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_websocket.py:110).
- [00 notice parser](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_websocket.py:921).
- [메모리 state-event queue](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_websocket.py:2400).
- [계좌 00 REG; 04 없음](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_websocket.py:3124).
- [Main configured cost / broker actual null](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_execution_receipts.py:2176).
- [45/90초 계좌 주기](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_sniper_v2.py:357).
- [single-flight 주기 호출](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_sniper_v2.py:13103).
- [reconnect sync consumer](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_sniper_v2.py:12565).
- [read-only kt00005+ka10075 snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2323).
- [periodic lifecycle/terminal reconciliation](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2474).
- [kt00008 settlement와 exact fill 분리](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:921).
- [pre-submit REST 호가 refresh](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:31967).
- [exact-route WS tape / REST candle](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/zero_base_probe.py:440).
- [분석 context producer demand](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:6293).
- [프로그램 0w 우선](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4347).
- [kt00011 exact code/price](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1078).
- [capacity helper source/required 구분](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:2998).
- [zero-base enabled return](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:7008).
- [현재 발견 panel 헬퍼 참조](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/zero_base_discovery_source.py:63).
- [ka20003 breadth producer](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/market_panic_breadth_collector.py:1241).
- [정확 날짜 주문/미체결 대사](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:286).
- [ka10073 optional 비용 loader](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_tuning.py:398).

## 9. 조사 종료와 검증

- runtime code/env/WS REG/REMOVE/서비스/release/정책/계좌·주문 API 변경 없음. 공식 GitHub read-only 접근과 local 파일·프로세스 조회만 수행했다.
- 저장소 산출물은 이 문서와 API별 참조/source hash 목록다. JSON manifest와 tmp AST/명세·bounded log 계산 파일은 로컬 재현 보조 자료이며 실행 코드 배포 대상이 아니다.
- 검증 완료: REST 45 ID와 본문 표·목록가 1:1 일치(중복/누락 0), upstream path/hash 및 불변 source link 존재/line 범위 확인, source/비용/owner/현재성 및 17:11 릴리스 변경 delta 재검토, manifest JSON parse/목록 및 trailing whitespace 확인, `git diff --check` exit 0, 문서 print-only backlog parser exit 0. 실제 broker 호출이나 구독 변경은 0이다.
- 조사/문서 작업이므로 pytest·거래 suite·실계좌 API·새 REG·expensive report regeneration·외부 Project/Calendar sync는 실행하지 않는다. 남는 한계는 비용 FID scope 문서 미확정, WS 전체 수신의 natural 완전성 미검증, API별 전 구간 physical HTTP counter 부재다.
