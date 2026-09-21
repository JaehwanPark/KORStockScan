# 위젯 WS 원천 차단 원인과 P3 연결 확정

판정 기준: 2026-09-21 16:40:30–16:41:00 KST의 동일 파일16회 관측(2초 간격), bounded 원장/로그, 실제 선택 release. 이번 작업은 원인 분석·계획 확정과 문서 수정이다. 서비스/정책/구독/한도/guard를 변경하거나 REST/API 요청·재기동·주문을 수행하지 않았다. 기존 재기동 승인을 다시 요구하지 않으며, 새 구현은 해당 계약의 검토·검증 이후 인계한다.

## 1. 결론과 정확한 원인 경계

**프리·애프터마켓의 체결 공백은 연결 장애가 아니다.** 사용자의 최신 지시대로 0B/0D age만으로 REG/REMOVE·재접속·REST 재조회를 요구하지 않는다. 반면 이미 끊어진 연결의 이전 세대 값이나 현재 주문에 필요한 신선도가 없는 값은 실행 입력으로 승격하지 않는다. 저장된 마지막 값/완료 봉의 유효성, 현재 거래 준비, 연결 상태를 각각 표시해야 한다.

| 확인 층 | 근거 | 판정 |
| --- | --- | --- |
| 현 메인 | [선택·PID 영수증](../../tmp/widget-p3-plan-20260921/main-selection-as-of.json): 다른 승인 작업이16:29에4c5dc8a06/PID285831에서5e3f48bd9/PID297783으로 교체 | 앞선 보고의 메인285831은 현재값이 아님. 이 분석은 새PID로 고정 |
| 실제 연결 사건 | [로그](../../tmp/widget-p3-plan-20260921/reconnect-log-excerpt.txt):16:36:06 close1006,16:36:10 LOGIN/재접속,16:36:11 관측 cohort REG 두batch 전송 | 실제 단절 및epoch1→2 전환 확인. 단순 저빈도만으로 설명하지 않음 |
| 발행기 | [16회 원시 필드 대사](../../tmp/widget-p3-plan-20260921/source-clock-trace.json): snapshot age약1초 이내, PID generation일치, connection_available=true | 프로세스/파일 발행은 살아 있음. 이 상태가 모든 item의 현재epoch 수신 완료를 뜻하지 않음 |
| 확장3종목 | 006800/010140/080220_AL 모두 등록목록에 존재. stock/producer epoch2이나0B·0D row epoch1. age약264–298초. item/suffix/route/venue/날짜/세션/sequence 및 field≤publication 검사는 통과 | 정확한 차단은 **이전epoch +20초 초과**. REG 전송을 현재epoch 첫 수신으로 오인하면 안 됨. 재접속 뒤 조용한 종목의 첫 수신 대기는 별도 상태이며 그 자체로 재접속을 반복하지 않음 |
| 삼성 | 005930_AL epoch2 일치.0B age35.6→65.9초,0D41.4→71.8초 | 이 표본의 차단은 **age 초과만**. 이것만으로 추가 단절/재구독 필요를 판정할 수 없음 |
| 수신 지연 | [원장 health와 rejection 표본](../../tmp/widget-p3-plan-20260921/bounded-lineage-trace.json): 제공시각→앱의ws.recv 반환시각 지연23.177–24.646초, 반환후정규화0–442ms. 기록worker/queue/writer error0 | 지연은 적어도 정규화/원장writer 이후의 문제는 아님. provider/network/socket buffer/event-loop scheduling 중 어느 층인지는 현재 증거로 확정하지 않음 |
| 호스트 경합 | [로그](../../tmp/widget-p3-plan-20260921/ws-errors-excerpt.txt):16:36:10 I/O wait58.15%,16:37:12 42.61% | 수신 지연과 동시 발생한 위험 요인. 원인으로 단정하거나 guard를 완화할 근거는 아님 |

`field_clock_route_or_epoch_invalid:0B`는 여러 검사를 묶은 현재 오류명이다. 위 표는 같은 checkpoint의 각 조건을 풀어서 확인한 결과이며 과거16:37 한 순간의 정확한 패킷을 복원한 것은 아니다. 소스 검사 실패 시 이전 종목의 `client.last_request_receipt`가 남는 [실패 귀속](../../tmp/widget-p3-plan-20260921/failure-attribution.json)도 확인했다. 예:006800 WS 실패에006110_AL REST 영수증,010140 실패에007810_AL 영수증이 붙었던 조회가 있었다. 이 영수증은 해당 WS 실패의 인과 증거가 아니다.

## 2. 구현 우선순위에 포함할 관측·복구 결함

- 현재 reader의 복합 오류를 개별 사실로 분해: `field_age_exceeded`, `prior_epoch`, `item_or_route_conflict`, `field_after_publication`, `date_or_session_conflict`. 성공/실패 모두 원본0B/0D 시각·source epoch·producer epoch와 evaluated_at을 보존한다. stale 값의 시각 갱신 금지.
- 연결 상태는 명시적 close/LOGIN·현재epoch·지원되는 기존 PING/PONG/연결 health로 판단한다. 새 heartbeat API나 더 잦은 ping을 추가하지 않는다. 조용한 연결의 field age 증가는 `quiet_or_no_recent_event`로 관측하되, no-trade 완전성은 추가 근거 없이 확정하지 않는다. 전송 장애와 consumer 신선도 부족을 분리한다.
- 재접속 시 전송목록과 실제 item/type 첫 수신을 별도 receipt로 관리한다. 이전epoch cache는 이력으로만 보존한다. reconnect 복구는 현재epoch desired set을 한 번 복원하고, 명시적 전송 실패/누락 등록만 기존 bounded 경로로 처리한다. 첫 체결 미도래·quiet age로 강제 재구독하지 않는다.
- [bounded 로그](../../tmp/widget-p3-plan-20260921/ws-log-excerpt.txt)에005930/034020의 `micro_reversion_collection_feedback_demotion` REMOVE→REG가약5초 간격 반복된다. `retain_micro_reversion_as_observation_only`와 `_configure_micro_reversion_observation_items`의 보호/관측 역할 계산을 함께 점검해 같은 desired item/type/epoch에 대한 변경을 멱등화한다. 반복 제어명령은 확인된 현상이나 이번1006의 직접 원인으로 단정하지 않는다. 메인/holding/다른 consumer의 owner는 보존한다.
- symbol별 시작에 오류 context를 초기화하고 해당 attempt가 실제 발행한 REST 요청만 오류에 연결한다. WS 실패에는 다른 symbol의 마지막 REST receipt를 붙이지 않는다. `read_only_source_error:RuntimeError`로 구체 원인을 소실하지 않는다.

## 3. AL 내부 연속성 증거

[원장 표본](../../tmp/widget-p3-plan-20260921/bounded-lineage-trace.json)은 파일stat후SOR_AFTERMARKET canonical `market_stream` 끝4MiB만 읽었다(4,730행). 신규 체결 요청이나 하루 전체 재스캔은 없다.

| 종목 | 표본행 | 동일 observer epoch의 local sequence gap | 인접 FID13 증가량과 현재 abs(FID15) 차이 |
| --- | ---: | ---: | ---: |
| 005930 | 1,751 | 0 | 16 |
| 006800 | 20 | 0 | 0 |
| 010140 | 49 | 0 | 0 |
| 080220 | 28 | 0 | 0 |

이는 AL와개별 REST 비교가 아니라 **같은 AL 원천 내부 진단**이다. 삼성 예시는 누적량+33,502에 현재 체결량2주였다. 누락/coalescing/누적량 의미 중 원인이 확정되지 않았으므로 raw를 보존한다. FID13 차이로 가격 경로·OHLC나 누락 체결을 합성하지 않는다. 공식 의미 대조와 기존 수신 처리 경로 확인 후 설명된 구간과 미설명 구간을 분리한다. 다른3종목의 bounded 차이0도 broker 전체 무손실의 증명은 아니다.

현재 health는 timestamp rejection1,693건(체결508,호가1,185)의 누적과 마지막64개만 보존한다. local sequence는 enqueue 이전 제외를 잡지 못한다. 따라서 local gap0만으로 P3 완전성을 주장할 수 없다. 현재 손실 구간은 제외하고, 신규P3 세대부터 rejection/queue/connection 변화의 범위와 cursor를 함께 기록해야 한다. 과거 누락 원시자료는 재실행으로 만들지 않는다.

## 4. 확정된 P3 연결과 종료 조건

상세 구현 순서와 파일 소유 경계는 [계획 §3.3.1](../proposals/widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md#331-p3-연결-확정-원천-상태분리와-단일-완료-분봉-발행)에 반영했다. 순서는 **원인 귀속/멱등 복구 → 기존 canonical writer의 분봉 투영 → 공통 reader → 현재AL consumer → 나머지 위젯/episode**다. 별도 WS 연결·새 전체 tick 수집기·수신 callback 내부 파일쓰기·한도 증액은 없다.

분봉 건전성은 프리/정규/애프터별 데이터 계약으로 검사하고 주문 실행 guard와 분리한다. 저빈도에서 과거 정상 완료봉을 나이가 들었다는 이유만으로 삭제하거나 REST를 반복하지 않는다. 새 체결이 없는 분은 상태로 남기며 임의0거래량 봉·전종가 채움은 금지한다. 정책이 연속N분을 요구하면 그 정책의 대기 상태를 보존한다.

코드·배포·자연 수용·체결·비용 후 성과는 각각 남는다. 이번 문서 변경은 link/owner/diff 및 print-only parser로 검증하며 runtime pytest/보고서 재생성·외부 sync는 실행하지 않는다.


## 5. 조사 범위와 검증

문서상 단일 구현·자연 수용 owner는 `KiwoomCommonHealthOpportunityCostAcceptance0917`로 유지했다. 확정 계획은 source helper의 위치·기존 writer/reader 소유 경계·consumer 인계·quiet/누락 구분·단일 REST seed·복구/rollback·종료 검사를 포함한다. 이번은 문서 수정이므로 trading pytest, 실제 API, 배포·재기동, 외부 Project/Calendar sync는 생략했다.

조사 중 기존 freshness report에 wildcard 검색을 한 차례 잘못 적용해 큰 단일행 출력이 발생했고 해당 명령을 중지했다. 그 출력은 원인 판정이나 통계에 사용하지 않았다. 위16:36 지연/I/O 증거는 그 조회 이전의 기록이며, 이후 host 부하를 같은 원인 증거로 확장하지 않는다. 원장 비교는 별도로 stat후4MiB, 로그는stat후파일당3MiB로 제한한 증거다.
