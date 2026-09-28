# 제로베이스 SCALPING 발견·기계판정 구현 리뷰와 릴리스 문턱 — 2026-09-28

## 17:26 KST 기계판정 도달 우선 수리 리뷰

- **새 PID 기준 병목:** 16:58~17:21 KST `zero_base_probe_result` 777건/428개 고유 코드 중 `assessed` 3건(`RECHECK` 2, `BLOCK` 1), `route_snapshot_missing` 608건, `probe_worker_capacity` 155건이었다. `zero_base_watch_attach`는 0건이다. 반복 시도와 source gap을 종목 수나 무수익으로 치환하지 않는다. 감시 슬롯 퇴출은 아직 이 단절점의 원인이 아니다.
- **수정:** 정확 route 0B·0D와 0B 다섯 건을 기다리는 기본 상한을 전 세션 3초→5초로 늘렸다. 준비되면 즉시 반환한다. 최대 8개 claim/10초를 처리하는 실행 작업자는 2→5, 예약 한도는 8→12로 조정했다. 한쪽 수신에만 적용되던 프리마켓·통합 애프터마켓 추가 2초는 유지해 해당 최대 대기는 7초다. 실제 기다린 시간과 기본·실효 예산을 결과에 기록한다. 마지막 0B·0D의 3초 신선도, 정확 route/transport, 공유 REST 5/4 admission, 감시 상한, 주문·수량·가격·hard safety는 유지한다.
- **리뷰 경계:** 새 동시성은 REG item을 더 오래/동시에 점유할 수 있다. 공유 WS item budget 및 실제 peak를 배포 후 별도 확인한다. 5초가 기계판정·실제 제출을 늘리는지와 `probe_capacity_deferred`, 3~5초 첫 수신, 기계 직전 자료 결손을 동일 PID/세션에서 대사하기 전에는 개선이라고 판정하지 않는다. 9/28 기존 감시 의미 재생에서 5분 조기 퇴출 후 회복이 관측되고 10분 적격 후보가 0이므로 새 라이브 퇴출 규칙을 넣지 않았다.
- **공식 참조:** 2026-09-28 17:24 KST 공식 원격 HEAD와 `/tmp/kiwoom-rest-api-20260928` checkout이 모두 `953e5dbff123f437ab4d11a78a95191a685eb51f`였다. `kiwoom/realtime/packets.py`, `kiwoom/core/ws_client.py`, `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 WebSocket/REG/REMOVE·0B/0D 및 Postman collection을 확인했다. 이 revision에는 `kiwoom_docs`가 없다. 패킷·FID·URL·인증·REG/REMOVE 형식은 수정하지 않았고, 공식 자료에는 첫 수신 보장 시간이나 고정 동시 item 한도가 없다.
- **검증·상태:** zero-base probe/Main/queue/source와 Kiwoom 시장자료·읽기 제어 회귀 128건 통과. 다음 재리뷰·compile·diff·문서 parser를 거쳐 불변 릴리스에 담는다. 이 시점은 작업본 검증이며 배포/PID 소비·자연 판정 증거가 아니다.

## 16:59 KST 세션 경계 재리뷰·수정·재기동

- **리뷰 결함과 수정:** 종전 `_AL`·SOR 주문 결속은 감시 편입 당시의 `KRX`/통합 애프터마켓 표기만 확인하고 주문 시점의 세션을 다시 묶지 않았다. 또한 프리마켓·정규장 감시가 세션 전환 뒤에도 기존 최대 30분 TTL 동안 슬롯과 동일 코드의 새 세션 probe를 막을 수 있었다. 제로베이스 주문은 현재 KST 매수창, 정확 route·broker·effective venue·market session bucket을 함께 검사한다. 제로베이스 WATCHING은 기존 FIFO 만료 경로에서 세션이 달라지면 만료하며 `session_changed` terminal 이유를 남긴다. 기존 비활성 WS 구독 정리 주기가 해당 종목을 후속 해제한다. 다른 소유자의 감시·보유·매도는 이 규칙의 대상이 아니다.
- **재리뷰와 검증:** 첫 회귀에서 새 helper의 미정의 `KST` 이름을 발견해 `session_contract.KST`로 고쳤다. 수정 후 제로베이스 경로 51건, 인접 시장 세션·최초 수량·WS·조건검색 627건이 통과했다. 영향 Python compile과 `git diff --check`도 통과했다. 3초 0B/0D 신선도, Kiwoom 요청/응답 형식, 주문 수량·가격·하드 가드는 변경하지 않았다.
- **공식 참조:** 2026-09-28 16:49:58 KST 원격 HEAD가 이전 검토와 같은 `953e5dbff123f437ab4d11a78a95191a685eb51f`임을 재확인했다. 로컬 공식 checkout의 `kiwoom/_data/kiwoom_api_spec.json` `kt10000` 주문 거래소 필드와 앞 절에 기록한 `kiwoom/specs.py`, `kiwoom/core`, `kiwoom/realtime`, Postman 경로를 대조했다. 이번 변경은 로컬 세션 권한 검사이며 주문 API 패킷을 바꾸지 않는다.
- **배포·기동:** 커밋 `527f27a3f72c9a11405064fb90a06df99cf995d8`, 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/zero-base-session-bound-20260928-527f27a3`를 선택했다. 이전 선택 백업은 `tmp/zero-base-session-bound-selection-before-deploy-20260928T165734.json`이다. 16:57:48 정상 재기동 후 Main PID `725217`의 cwd가 새 릴리스 `src`와 일치하고 `KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED=true`, runtime source clean, 9/28 정책 bootstrap PASS, release-set Main PID 결속 PASS다. 16:58 신규 PID에서 조건검색 목록 요청 생략, 통합 `_AL` probe REG/REMOVE 및 WS 연결·수신을 확인했다. 당시 Main은 HOLDING 1건·WATCHING 0건이어서 새 세션 만료와 주문 차단의 자연 발생은 관측되지 않았다. 다음 프리마켓 `_NX` 자연 수신, 실제 제출·체결·terminal·비용 후 경제성도 별도 OPEN이다.

## 16:32 KST 프리마켓 수신시점과 구현 리뷰

- **관측 모집단:** 2026-09-28 source-only 연속 구독의 동일한 선택 23종목, `_AL` 0B/0D, 각 세션 15분(프리마켓 08:03–08:18, 통합 애프터마켓 16:00–16:15), 종목별 10초 간격 90개 anchor로 세션당 2,070개 anchor를 읽었다. 프리마켓은 SOR 관측 스트림으로, 새 NXT `_NX` 임시 REG의 수신률을 측정한 것이 아니다. 유효 signed 0B와 양의 BBO 0D의 *어느* 수신쌍이 anchor 뒤 3/5/10초 이내에 함께 나타나고 두 수신시각 차가 2초 이내인 anchor는 프리마켓 423/499/579, 통합 애프터마켓 414/586/852였다. 이것은 연속 구독의 도착 분포이며 새 probe의 성공률이나 제출률이 아니다.
- **최종 신선도 비교:** 같은 23종목·anchor에서 각 3/5/10초 종료시점의 *최신* 0B/0D를 비교하고 두 수신시각 차 2초 이내를 요구했다. 10초 종료시점에 쌍이 있던 프리마켓 453건 중 두 자료가 모두 최근 2초인 것은 369건, 3초인 것은 403건이었다. 통합 애프터마켓은 468건 중 각각 315건, 379건이다. 종료시점에 최근 2초 조건을 만족한 전체 anchor는 3/5/10초 순서로 프리마켓 363/380/369, 애프터마켓 301/322/315였다. 따라서 기다림을 늘려도 고정 2초 기준의 통과율은 단조 증가하지 않는다. 이 계산은 주문 유효성·순익을 평가하지 않으며 전체 시장이나 `_NX`에 대한 임계값 증거가 아니다.
- **판정:** 신선한 동일 route·transport의 체결과 호가는 진입 판단에 필요한 원천 가드다. 정확한 **2초**는 종전 zero-base probe의 로컬 값이며 Kiwoom API가 명령한 수치도, 전 종목에서 경제적으로 최적인 값도 아니다. 사용자의 명시적 후속 지시에 따라 probe의 대기 종료·기계 직전 0B/0D 상한을 **3초**로 변경해 공유 AI 입력 preflight의 3초 상한과 맞췄다. 전체 시장 최적값이라는 주장은 아니다. 다음 자연 `_NX` 프리마켓과 `_AL` 애프터마켓의 대기 종료·기계 직전 0B/0D 나이, 기계 action, 실제 제출·체결·비용 후 결과를 분리 대사한다.
- **구현·자체 리뷰:** 프리마켓만 `ka10027 stex_tp=2`, NXT `_NX` WS/REST, Main `PREMARKET_KRX_LIKE` 감시, 명시 NXT 주문으로 결속했다. 정규장/통합 애프터마켓 `stex_tp=3`·`_AL`·SOR는 유지한다. 첫 리뷰에서 구독 해제의 원래 plain-code 표기, 감시 등록의 `_NX` 누락, 세션 전환 뒤 옛 route claim 재평가, 최초 수량 후속 주문의 SOR 고정이 드러나 각각 수정했다. 신선도별 종료시점 재검토 후 두 저활동 세션은 정확 한쪽 자료만 3초 안에 받은 경우에만 최대 2초를 추가 대기하도록 축소했다. 두 자료 모두 없는 probe는 연장하지 않는다. 최종 3초·정확 route·transport 검사는 유지하며, 주문 직전의 별도 신선도와 보호 장치는 변경하지 않았다. 2-worker와 REST 공유 admission은 유지한다. 워커 점유 증가 가능성은 다음 자연 PID의 capacity-deferred와 함께 평가한다.
- **공식 참조:** 2026-09-28 16:22–16:32 KST 원격 HEAD/checkout `953e5dbff123f437ab4d11a78a95191a685eb51f`를 확인했다. 이 revision에는 `kiwoom_docs`가 없다. `kiwoom/_data/kiwoom_api_spec.json`의 `ka10027`(POST `/api/dostk/rkinfo`, `stex_tp 1/2/3`, KOSPI 001/KOSDAQ 101, 응답·continuation), `ka10003`(`/api/dostk/stkinfo`), `ka10080`(`/api/dostk/chart`)의 plain/`_NX`/`_AL`, `kt10000`(`/api/dostk/ordr`, `dmst_stex_tp KRX/NXT/SOR`), 0B/0D FID·WebSocket `/api/dostk/websocket`, `kiwoom/specs.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/packets.py`의 REG/REMOVE, Postman collection을 대조했다. 공식 명세는 프리마켓 `_NX` 자연 수신률·종목별 주문 가능성·전체 시장의 적정 3초 값을 보증하지 않는다. 계좌·실주문 API는 호출하지 않았다.
- **검증·배포:** 관련 발견·queue·probe·Main·초기 수량·세션·캔들 회귀 265건과 인접 scanner runtime/WS 회귀 14건, Python compile, `git diff --check`, 문서 print-only parser가 통과했다. 커밋 `16927a8687403df65d6a01cb44777f8794f21344`의 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/zero-base-premarket-20260928-16927a86`를 선택했다. 직전 선택 포인터 백업은 `tmp/zero-base-premarket-selection-before-deploy-20260928T164245.json`이다. 정상 재기동 뒤 Main PID `717094`는 해당 릴리스 `src`를 실행하고 scanner flag=true, runtime source clean, 9/28 정책 bootstrap PASS, release-set의 Main PID 결속 PASS다. 기능/경제성은 release-set의 `not_assessed`를 그대로 따른다.
- **새 PID 자연 영수증:** 16:43:23 KST 통합 애프터마켓 KOSPI/KOSDAQ `stex_tp=3`·SOR 각 200행 `observed_panel` 2/2를 확인했다. 16:43:27–16:43:55의 신규 probe 24건은 `assessed` 1, `source_unavailable` 17, `probe_capacity_deferred` 6이고, `_AL` 임시 REG/REMOVE와 한 건의 기계 `RECHECK`가 있었다. 이 짧은 창에서는 3초 신선도 변경의 경제적 효과를 판정할 수 없다. 다음 프리마켓 `_NX` 패널→REG/REMOVE→정확 0B/0D→기계 action, 제출·체결·terminal·비용 후 경제성은 각각 별도 미수용이다.

## 15:23 KST WS 프로브 대기 보완·재리뷰·재기동

- **원인 구분:** 14:56 이후 3초 임시 구독에서 0B를 먼저 받으면 공통 `wait_for_data(require_trade=True)`가 0D 수신 전에 반환했다. 해당 구간 `0D_missing` 30건 중 REG·첫 수신 로그를 대응할 수 있는 29건의 첫 수신은 0B였다. 이것은 조기 반환 결함의 증거이며, `route_snapshot_missing` 전체나 실제 체결 간격의 원인 증명은 아니다. 3초 내 정확 `_AL` 수신 건수·시각이 없던 기존 영수증으로 저유동성을 단정하지 않는다.
- **공식 계약 확인:** 2026-09-28 15:11 KST `Kiwoom-Securities/Kiwoom-REST-API` 원격 HEAD와 로컬 checkout SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`를 재확인했다. `kiwoom/realtime/packets.py`, `events.py`, `stream.py`, `kiwoom/core/ws_client.py`, `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `_AL` 종목코드 설명, Postman collection을 대조했다. 이 revision에는 `kiwoom_docs`가 없다. REG/REMOVE 패킷·FID·REST 요청·주문·인증·reconnect 계약은 변경하지 않았다. 로컬 정확 route·transport·시각·BBO 안전 검사는 유지한다.
- **첫 수정·자연 결과:** 불변 릴리스 `f349a1c9fa6759efb9b2d9bc1f4cf95cfdfcdbb1`은 `_AL` 0B·0D가 모두 신선해질 때까지 기존 최대 3초 안에서 기다리고, 정확 route의 보존된 체결·호가 시각/건수와 signed 0B 건수를 대기 종료 및 기계 직전에 결과 영수증으로 기록한다. 리뷰 중 잘못된 첫 수신시각 대체와 비정상 계측 자료 예외를 고쳤다. 영향 회귀 186건, Python compile, diff check 통과 후 15:18 KST 배포·재기동해 PID `673949`, 당일 정책 handoff와 release-set PASS를 확인했다. 자연 24개 결과 중 `TRIGGER_CONFIRMATION_RECHECK` 1건은 대기 755ms, 기계 직전 정확 0B 5건이었다. 별도 3건은 0B·0D가 0.1~1.2초 안에 갖춰졌어도 기계 직전 정확 0B가 2/4/1건뿐이며 `strategy_tape_score_source_missing`이었다.
- **후속 수정·현재 릴리스:** 위 새 영수증 때문에 같은 3초 한도에서 정확 route 0B 다섯 건을 기다릴 기회도 주되, 한도 내 다섯 건이 없어도 원천·기계 판정을 그대로 통과시키거나 체결 방향을 추정하지 않도록 했다. 3초 종료 시 신선한 0B·0D가 없으면 기존 source gap으로 닫고, 5건 미달이면 실제 기계 계약이 판정한다. 관련 회귀 187건, Python compile, `git diff --check` 통과 후 불변 릴리스 `71caed8458c1a98c5f1b655de2c64b9be38a824a`를 선택·재기동했다. 현재 Main PID `676594`는 `/home/ubuntu/KORStockScan-runtime-releases/scanner-zero-base-20260928-wsdwell/src`를 실행하며 flag=true, PID 영수증·2026-09-28 정책 handoff·release-set PASS다. 이전 릴리스 선택 백업은 `tmp/scanner-selection-before-wsdwell-deploy-20260928T152236.json`에 있다.
- **수용 경계:** `first_0b/0d_ms`는 정확 route의 보존된 버퍼 중 가장 이른 시각이고 `latest_0b/0d_ms`는 최신 타입 스냅숏 시각이다. 두 값은 시장의 실제 최초 체결시각이나 WS 지연 전체를 증명하지 않는다. 새 PID의 다음 자연 매수창에서 5건 수집률·원천 결손·기계 판정과 probe 처리량을 확인해야 하며, ENTER_NOW·제출·체결·비용 후 성과는 아직 별개다.

## 14:56 KST 사용자 route 정정 후 리뷰·배포 영수증

- **결정:** 기존 KRX/NXT 분리 패널 릴리스 `7d0c12d2`는 정규장·통합 애프터마켓의 후보·주문 계약에 맞지 않았다. 14:38 KST 퇴역 전용 `53854ced`로 롤백해 Main PID `647108`, 당일 bootstrap PASS, release-set PASS를 확인했다. 기존 분리 queue는 삭제하지 않고 보존했다.
- **공식 계약:** 14:39 KST `git ls-remote`로 Kiwoom 공식 HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 재확인했다. 해당 checkout의 `kiwoom/_data/kiwoom_api_spec.json` `ka10027`(약 10091행, `stex_tp=3` 통합), `kt10000`(약 52180행, `dmst_stex_tp=SOR`), `ka10003`, `ka10080`, `kiwoom/specs.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/packets.py` 및 Postman을 교차 확인했다. 이 revision에는 `kiwoom_docs` 디렉터리가 없었다. `_AL` 실시간 item과 REST 종목코드의 로컬 공식 참조는 [Kiwoom API 계약](../kiwoom-api-data-contract.md)의 통합 SOR 절을 따랐다. 예제는 주문 권한으로 사용하지 않았다.
- **구현·재리뷰:** KOSPI/KOSDAQ 2패널을 `stex_tp=3`, `krx_nxt_integrated`로 바꾸고 장전·전환·마감 밖 조회를 차단했다. probe와 WATCHING REG는 `_AL`만 쓰며 이미 다른 route로 구독된 코드는 재사용하지 않고 source gap으로 남긴다. Main은 정규장 `KRX`/통합 애프터마켓 `KRX_NXT_INTEGRATED` 코호트를 유지하되 신규 스캐너의 주문 요청은 명시 `SOR`로 묶고 누락·불일치는 주문 직전 거부한다. 최초 수량 연속 계획도 SOR를 사용한다. 분리 route queue는 새 `integrated_v2` 경로로 격리한다. queue 공정성·Main·probe·세션·주문·초기수량 회귀 210건, 후속 분류 회귀 35건, Python compile 및 diff check가 통과했다.
- **실측·당시 PID:** 캐시 토큰의 source-only 호출에서 통합 KOSPI/KOSDAQ 각 200행, 2/2 `observed_panel`, 오류 0, 7.75초를 확인했다. 불변 릴리스 `826f3d725f6154dfb320f998d4371b19ceaea692` 배포 후 Main PID `657079`에서 flag=true, `_AL` WS REG/REMOVE와 통합 route queue 및 자연 `RECHECK` 1건을 확인했다. 14:56 KST 후속 릴리스 `d619923abecf1c44c4bc925eebf68526f71c3534`는 `strategy_tape_score_source_missing`을 정확히 `required_feature_insufficient`로 분류한다. 당시 PID `661520`, cwd=`/home/ubuntu/KORStockScan-runtime-releases/scanner-zero-base-20260928-sourcegap/src`, 당일 bootstrap PASS 및 release-set PASS를 확인했다. 이 분류는 REST 가격변화 추정치를 신뢰 체결 방향으로 바꾸거나 정책 임계치를 완화하지 않는다.
- **미수용:** 자연 probe 중 0B/0D 시차·신뢰 체결 방향 결손이 많고, 현재까지 기계 `ENTER_NOW`/실제 주문/체결/terminal/비용 후 성과는 확인되지 않았다. `ka10027`의 400행은 시장 전수가 아니다. 분리 패널 릴리스 `d525ece7`, `7d0c12d2`는 운영 롤백 대상에서 제외하고 퇴역 전용 `53854ced`를 되돌림 기준으로 유지한다.

## 결정

작업공간에 독립 KRX/NXT 관측 패널, 영속 평가 큐, 정확 route WS/REST 프로브, provider 없는 기계 판정, Main의 동일 세대 감시 편입, VCP/S15 신규 경로 퇴역을 구현했다. 장중 구조 변경 재기동은 체크리스트의 `ScannerSemanticWatchReplacement0928` POSTCLOSE 16:30~21:40 범위 밖이다. 아래 두 커밋은 준비된 불변 릴리스이며, 선택·PID 소비·자연 제출·terminal·비용 후 순익의 영수증이 아니다.

| 릴리스 | 경로 | 커밋 | 신규 스캐너 |
| --- | --- | --- | --- |
| 퇴역 기준 | `/home/ubuntu/KORStockScan-runtime-releases/scanner-retirement-only-20260928` | `53854ced39ee6e43f1c3f9bb4256a16042232964` | 신규 스캐너 코드 없음 |
| 새 발견 | `/home/ubuntu/KORStockScan-runtime-releases/scanner-zero-base-20260928-review` | `d525ece7bb83150c2bffce5e783951c10ce86a51` | launcher `true` |

첫 릴리스는 원본 `8e8def53`에서 VCP/S15 신규 진입 제거와 custody 보전만 발췌했다. 새 발견 모듈, `machine_only` 확장, 새 스캐너 flag는 없다. 둘째 릴리스는 같은 퇴역 규칙 위에 새 패널·queue·probe·Main 편입과 launcher `true`를 더한다. 앞서 만든 새 스캐너 코드를 `false`로만 끈 `scanner-retirement-20260928-review`는 순수 퇴역 계약에 맞지 않아 배포 후보에서 제외했다. 기존 선택 릴리스 `8e8def53`으로 되돌리면 VCP/S15가 다시 유입될 수 있으므로, 퇴역 후 롤백 기준은 첫 릴리스다. 공용 `data/docs/logs/tmp/.venv/restart.flag`는 작업공간을 가리키며, `src/deploy/restart.sh`는 두 후보에서 clean이다. 작업공간의 별도 미완료 변경은 릴리스에 포함하지 않았다.

## 코드리뷰와 수정

- discovery `ka10027`은 시장 전수로 표시하지 않고 KOSPI/KOSDAQ × KRX/NXT 각 최대 200행의 `observed_panel`만 기록한다. 같은 날짜·종목·route·원천 SHA claim을 영속화하고 오래된/중복 결과의 `ENTER_NOW` 승격을 거부한다.
- 동일 마지막 평가시각·첫 발견시각의 미평가 후보에서는 관측 거래량을 탐색 순서의 tie-breaker로 사용한다. 유동성 하한을 새 진입 허가나 전역 폐기로 만들지 않으며, 먼저 발견한 미평가 후보의 공정성을 유지한다. queue/runtime/source 회귀 13건이 통과했다.
- 프로브는 임시 WS 0B·0D만 요청한다. 같은 item/route/transport, 새 관측시각, 2초 내 0B·0D와 BBO를 요구한다. 비동기 REG 완료 전 timeout이면 그 코드의 새 probe 예약을 유지하다 완료 callback에서 REMOVE한다. 기계 직전 WS를 다시 읽고, tick/분봉 REST 요청코드·수신시각을 검증한다. KRX 평문 코드의 자동 `_AL` 전환을 차단했다.
- 이미 다른 owner가 같은 코드를 구독한 경우 probe는 그 구독에서 새 0B·0D를 기다리며 REG·REMOVE나 required realtime type을 변경하지 않는다. 정확 route 자료가 없으면 `source_unavailable`로 남긴다. 기존 구독 재사용과 소유권 보존 회귀 1건을 추가했고 probe/Main 14건이 통과했다.
- 기계 전용 호출은 현재 선택 bundle 없이는 fail closed하고 provider를 호출하지 않는다. `ENTER_NOW`는 다시 5초 이내의 WS 관측·bundle SHA·기존 hard guard와 슬롯 상한을 거쳐 Main 감시로 간다. `PROBE_READY` DB 행은 같은 ID의 감시 편입 성공 때만 확정되고, 실패/재시작에서 주문 대상으로 복원되지 않는다. Main 진입 락으로 동시성을 통일했다.
- Main 동기 편입 또는 scheduler inbox 편입 중 예외가 나면 해당 `PROBE_READY` 행을 만료하고 같은 ID의 임시 감시를 되돌린 뒤 거절 영수증을 남긴다. 예외가 나더라도 다음 inbox 항목을 처리한다. 이 보강의 새 회귀 2건을 포함한 41건과 Python compile·`git diff --check`를 통과했다.
- 새 모드는 SCALPING 조건검색 구독과 원시 편입을 중단한다. swing은 독립 owner 설정을 따른다. swing도 OFF이면 조건검색 목록 `CNSRLST` 요청 자체를 생략한다. 이는 기존 식별 결손과 낮은 제출 표본 아래의 구조적 WS 감축이며, 개별 식의 비용 후 수익성 0이나 새 패널의 완전한 대체를 주장하지 않는다.
- VCP 3식/S15 2식의 신규 구독·후보·주문 dispatch, 직접 S15 BUY 함수와 미사용 S15 후보 무장 상태·그림자 후보 생성·BUY 전용 가격 헬퍼를 제거했다. 도달 불가능한 `VCP_NEXT` 매수 분기도 제거했고, 나머지 56문장의 AST가 동일함을 확인했다. 보유·미결 주문·청산·journal 복구, 주문 동기화/영수증 및 역사적 원천은 남겼다. S15 dead helper 제거 후 custody 회귀 39건이 통과했다.

## 공식 계약

2026-09-28 12:36~13시대 KST에 `Kiwoom-Securities/Kiwoom-REST-API` 커밋 `953e5dbff123f437ab4d11a78a95191a685eb51f`를 확인했다. `kiwoom/_data/kiwoom_api_spec.json`의 `ka10027`, `ka10171`, `ka10173`, `ka10003`, `ka10080`, `kiwoom/specs.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/packets.py`, 해당 Postman 항목을 열람했다. 이 revision에는 `kiwoom_docs`가 없다. `ka10003/ka10080`의 `stk_cd`는 KRX 평문, NXT `_NX`, SOR `_AL`이며, `ka10027`의 연속조회·패널 범위와 조건검색 CNSRLST/CNSRREQ/REAL 02 I/D 및 REG/REMOVE 흐름을 확인했다. 공식 명세로 시장 전체 coverage, 실 broker ACK 또는 전략 수익성은 증명되지 않는다.

## 검증 영수증과 남은 문턱

분리한 두 릴리스의 queue·probe·Main·WS·condition·S15·VCP 회귀는 초기 각 852건 통과했다. S15/VCP 잔여 분기 정리 후 각 98건이 통과했고, 확장 회귀 각 924건 통과·1건 실패에서 제거된 S15 진입 함수에 분봉 조회 참조가 남아야 한다는 옛 검사 가정을 발견해 수정했다. 최신 원천·transport 검증과 함께 각 46건을 다시 통과했다. 최종 통합 후보에서는 큐 호출주기·원천 유효기간 보강 후 확장 회귀 928건이 통과했다. 이후 순수 퇴역 릴리스를 별도 재구성해 영향 회귀 1,545건과 WS 목록 1건을 통과했다. Python compile, `bash -n`, `git diff --check`는 최신 두 후보에서 통과했다. 800개 합성 관측의 큐 갱신 4.0ms, 8개 claim 0.29ms는 API/WS 부하의 실측값이 아니다.

13:42~13:44 KST source-only 실호출에서 KRX KOSPI `ka10027` 1페이지 20행의 `verified_success/admitted`를 확인했다. 첫 4패널 연속 시험은 7.04초, 완전 패널 2/4, 유효 행 356개였다. 공유 읽기 예산에서 일부 페이지가 대기 한도에 걸려 행이 반환돼도 패널 전체를 `source_unavailable`로 분류했다. 원천 대기 한도만 1.25초에서 3초로 늘리고 같은 4패널을 재시험한 결과 8.38초, 정상 패널 4/4, 관측 행 757개(KOSPI/KOSDAQ × KRX/NXT 200/200/200/157), 응답 페이지 6/5/2/1, 반환 오류·rate limit 0이었다. 이는 각 route의 최대 200행 관측이며 전체 시장 coverage 또는 다음 자연 세션의 지속 성공 증거가 아니다.

두 날짜 저장 시장조사 `all` 패널의 고정 prefix(9/25 31,890,583 bytes, 9/28 14,623,974 bytes)를 대기열에만 재생했다. 최초 구현은 패널 60~90초당 8건만 claim해서 마지막 관측으로부터 3,299초/20,715초가 지난 후보도 재요청했다. 리뷰 수정으로 원천 120초 초과 claim을 막고 패널 조회 사이 10초마다 최대 8건을 추가 dispatch한다. 동일한 **즉시 `source_unavailable`로 resolve하는 큐 전용 모형**에서는 9/25 관측 code-route 388/388, 9/28 845/862가 적어도 한 번 claim됐고, 최대 claim 원천 나이는 두 날짜 모두 120초였다. 이 모형에는 실제 WS·REST probe, 공유 호출 경쟁, 기계 판정·주문·경제성이 없으며 9/28 미claim 17건은 그대로 남긴다. 따라서 2일 큐 공정성 검사는 통과했지만 2일 기계 입력/제출 재생은 원천 결손으로 OPEN이다.

유동성 순서 보강 후 같은 고정 byte prefix를 별도 정의로 재실행했다. `all`·source `ok`·정확 KRX/NXT route·6자리 코드·양의 가격/상승률만 적격으로 놓고 capture ID/code/route를 원천 SHA로 묶었다. 10초마다 최대 8건을 claim한 뒤 즉시 `source_unavailable`, 60초 재확인으로 푸는 모형에서 9/25는 388/388, 9/28은 865/897 code-route가 한 번 이상 claim됐고 최대 원천 나이는 120초였다. 9/28의 32개 미claim은 남는다. 앞 시험의 862 분모와 적격 필터가 달라 845→865를 개선 효과로 비교하지 않는다. 유동성 tie-break는 같은 나이 후보의 순서만 바꾸며 이 재생도 물리 호출·실제 probe·기계 입력/제출을 포함하지 않는다.

설계 상한은 10초당 probe 8건 × 필수 REST 2종으로 probe read 1.6회/초 평균이다. 같은 60초에 오늘 실호출과 같은 패널 14페이지가 발생하면 패널 평균 약 0.23회/초가 추가된다. 이 산술값은 실제 burst, retries, 다른 owner의 물리 호출을 포함하지 않는다. 영속 queue는 파일과 교체 후 상위 디렉터리까지 fsync한다. 공유 per-token 5회/초·source-only 4회/초 admission은 그대로 적용하며, 두 worker/8 lease와 실패·결손 영수증을 새 PID에서 검증한다.

기존 `test_openai_scalping_analyze_target_returns_feature_audit_fields` 1건은 수정 전 선택 릴리스 `8e8def53`에서도 `microstructure_reaction_context_delivery_state` 기대 `computed_not_sent`/실제 `not_attempted`로 단독 실패했다. 이 별도 baseline 결함을 새 기계 전용 경로의 통과로 재분류하지 않는다.

9/28 재기동은 [NXT 애프터마켓 체결 종료 20:00 KST](https://www.nextrade.co.kr/marketOverview/content.do) 뒤의 체크리스트 POSTCLOSE 범위에서 수행한다. 필요한 순서는 (1) 실제 PID cwd/env와 S15 journal, DB active row·주문 원장, KRX/NXT broker 보유·미결을 같은 시점에 대사, (2) 퇴역 릴리스 선택·기동과 VCP/S15 신규 구독/주문 0 및 custody 보전 확인, (3) 새 발견 릴리스 선택·기동과 PID 코드/launcher/env/정책 SHA, REST 물리 호출·WS item peak 확인, (4) 다음 자연 매수창의 독립 panel→probe→판정→감시·제출 영수증과 후속 terminal/비용 후 결과를 분리 수용이다. 장기 점유·반전 부재 감시 퇴출의 live 임계치는 10분 적격 후보 0건의 근거로 선정하지 않았다.
