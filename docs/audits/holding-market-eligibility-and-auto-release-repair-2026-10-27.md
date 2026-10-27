# 보유 적격 시세 선택과 수동관리 자동 해제 수리 — 2026-10-27

## 결정·범위

사용자의 원인 수리·다른 보유 종목 점검·원본/안전장치 보존·리뷰/회귀·클린 커밋/푸시 지시를 수행한다. 코드 기준은 당시 선택된 운영 커밋 `97bc1f62e3668b2456c9638fff5ce225ea483fe5`이며, 격리 작업본은 `/home/ubuntu/KORStockScan-worktrees/holding-quote-manual-release-20261027`, branch는 `codex/holding-quote-manual-release-20261027`이다. 기준 당시 canonical/origin main은 `1756de1d9d7943739d539d5207cc55484185bff5`였다. 기준 커밋의 기존 수정은 이번 변경분으로 계산하지 않는다.

현재 계약의 첫 위반인 복원 보유 시세 등록을 수리하고, 등록→REAL→보유/빠른 청산 소비→기존 자동 해제 경로를 함께 검증했다. 운영 배포·selector 변경·재기동·정책/주문/수량/평단 변경은 수행하지 않았다. 기존 담당은 [오늘 체크리스트의 HoldingProfitExitSourceContractRepair](../checklists/2026-10-27-stage2-todo-checklist.md)이며 코드 완료와 운영·자연 수용을 구분해 OPEN을 유지한다.

## 원본과 최초 위반

원본은 [09:11 사건 보관본](/home/ubuntu/KORStockScan-storage-archives/manual-release-036930-20261027T091126/diagnosis.md), 추가 검증은 [이번 증거 목록](/home/ubuntu/KORStockScan-storage-archives/holding-quote-manual-release-repair-20261027/evidence-manifest.json)에 보존한다. 원 실패/시세/제외 파일/DB/재생 바이트를 덮어쓰지 않았다.

| 계층 | 보존 근거와 판정 |
| --- | --- |
| 보유 | 주성엔지니어링 `036930`, native record `49532`, 원 HOLDING/SCALPING, 수량 1, DB 평단 171,500원. 원 관측 release `ab663e13b`/PID `3940489`와 현재 기준 `97bc1f62e`를 분리한다. |
| 종목 마스터 | 10/27 08:23:10+09의 native ka10099: KRX regular/aftermarket true, NXT false, quality VALID, payload SHA `eb11d2262651b52a02e0463b6b7be747575decb30e6446f4abce7b30ba187714`. |
| 초기 등록 | 복원 HOLDING이 fixed-watch 신규 감시 템플릿을 먼저 따라 08:23에 `036930_NX`만 선택했다. NXT 부적격인 보유 종목의 당일 원천과 불일치한다. |
| 09:09 원 시세 | 연결은 열려 있었지만 해당 종목의 curr/수신 시각은 0, 0B/0D 원천은 없었다. 원 snapshot SHA `f1dbe535025d69642558bd07d07b52a3ac65faf815403f7856306a182074faea`. 같은 frame의 다른 종목 수신은 정상이다. 등록 inventory는 item별 broker ACK나 실제 체결 venue 증명이 아니다. |
| 순환 차단 | 기존 자동 해제는 신선한 가격이 없으면 false. 바로 뒤 수동관리 veto가 return하므로 더 뒤의 보유 시세 복구가 실행되지 않는다. fixed-watch reconcile도 veto에 막히며, 그 WATCHING 경로를 통과시키는 것만으로 HOLDING 등록 소유가 해결되지 않는다. |
| 별도 보완 | 공통 REG의 plain→AL 변환과 reconnect 복원, 글로벌 통합 flag에만 의존한 다른 route 프레임 격리, 깊이/기타 REAL 시각으로 갱신된 curr 소비가 원천 결속을 다시 깨뜨릴 수 있었다. |

원 `automatic-release-causal-reproduction.json`의 `regular_expected_item=036930_AL`은 당시 fixed-watch 진입 템플릿으로 적은 초기 기대값이다. 보존된 native 적격성까지 대사한 이번 수리의 **보유 정규장 적격 항목은 plain `036930`**이다. 원 증거의 초기 해석 필드를 사후 수정하지 않는다. 외부 화면의 과거 고가와 종목별 broker ACK, 실제 체결 venue는 복구·증명했다고 주장하지 않는다.

## 공식 Kiwoom Reference Gate

수정 전에 10/27 `10:29:58+09:00` 현재 [공식 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API) HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 조회·고정했다. [정확 경로/시각/SHA](/home/ubuntu/KORStockScan-storage-archives/holding-quote-manual-release-repair-20261027/official-reference-gate.json)와 원문을 보존했다.

검사 경로는 `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, `kiwoom/realtime/packets.py`, `kiwoom/realtime/decoders.py`, `kiwoom/core/ws_client.py`, `postman/kiwoom-openapi.postman_collection.json`이다. 구 `kiwoom_docs/실시간시세.md`·`종목정보.md`는 이 revision에 없으므로 현재 공식 packaged spec/API 0B·0D·ka10099·ka10001·ka10004와 packet/core/Postman을 대사했다.

plain=KRX, `_NX`=NXT, `_AL`=SOR 항목 구분, ka10099 `nxtEnable`, 0B 가격, REG/REMOVE·refresh=1·0B/0D와 native 수신 envelope를 확인했다. 예제/provider/계좌/주문 호출은 실행하지 않았다. 이 gate는 주문 route/실제 물리 venue나 주문 권한을 부여하지 않는다.

## 수리·소비 경로

1. 기존 `aftermarket_eligibility`에서 native 날짜·종목·provenance·품질·관측 시각을 검증하고 Main의 세션별 데이터 원천에 적격 축만 선택한다. PRE의 기존 NXT-only 원천은 NXT true에만 허용하고, 정규장은 KRX regular/NXT, 장후는 KRX aftermarket/NXT를 구분한다. 알려진 한 축만 적격이면 그 항목을 사용하고, 원천/전체 provenance 충돌·결손은 임의 기본값으로 채우지 않는다. 날짜/출처 결손, 미래/다른 날짜 master, transition/closed는 선택하지 않는다.
2. decision cohort/open_venues와 data item은 별개다. 기존 PRE native source는 NXT이고, REG의 KRX decision cohort도 적격 종목의 AL 데이터를 소비할 수 있다. 두 축 모두 적격이면 AL, KRX만이면 plain, NXT만이면 NX다. clock은 기존 `session_contract`에서 읽으며 broker route와 position identity는 변경하지 않는다.
3. 초기 HOLDING은 fixed-watch 진입 템플릿보다 적격 시세 선택을 먼저 수행한다. 기존 boot dispatch를 HOLDING의 정확한 REG 소유 경로와 나머지 priority/scanner 경로로 나눠 발행한다. 새 worker나 broker API를 추가하지 않는다.
4. 기존 `holding_ws_freshness_repair`는 해당 항목만 요청한다. plain은 오래된 is_nxt/default route로 다시 변환하지 않고, primary item은 통합 flag와 독립적으로 다른 route의 REAL을 기존 관측 store로 격리한다. reconnect는 이미 등록된 정확 항목과 primary binding을 보존한다. 다른 route/이전 연결의 가격을 새 frame으로 복사하지 않는다.
5. 자동 제외 보유는 수동관리 veto 앞에서 WS 등록만 복구할 수 있다. 기존 동일 원천 재시도 간격은 유지하며 날짜/세션/항목/원 master SHA가 변하면 새 결속을 다시 검사한다. 강제 해제·REST 우회·주문·slot 해제는 이 경로에 없다. 명시 operator/env/legacy-env와 별도 owner 표시는 시세 복구로 인수하지 않는다.
6. 일반 보유와 빠른 청산은 동일한 exact-item snapshot을 읽는다. 빠른 WS wake는 Main이 마지막으로 확인한 native binding만 재사용하며 DB/provider I/O를 추가하지 않는다. Main은 기존 보유 루프에서 원 binding을 갱신한다. 아직 binding이 없거나 날짜/세션이 바뀌면 빠른 경로는 fail closed다.
7. 자동 해제 가격은 현재 item의 native **0B last_trade_tick 가격·수신 시각·transport epoch**로 결속한다. 다른 item, 이전 연결, 오래된 체결에 새 0D/0F만 도착한 경우, 미래 시각, 다른 세션, 원 0B FID10 결손/가격 불일치, 평단 미달, sim/probe는 해제하지 않는다. 현재 producer의 실제 필드를 확인했으며 구 사건 frame에 이 필드가 있었다고 소급하지 않는다.
8. 유효 가격이 기존 DB 평단 이상일 때만 기존 native auto-row 제거 함수를 호출한다. operator/다른 symbol row와 hard/protect/emergency·broker/account/order/quantity/cooldown 및 retired 경계는 유지한다. source 미확인은 일반 보유 복구에서도 REST 긍정 가격으로 바꾸지 않는다.

## 다른 보유 종목·운영 확인

[10:30 원 조회](/home/ubuntu/KORStockScan-storage-archives/holding-quote-manual-release-repair-20261027/other-holdings-before.json)와 [10:53:52 재조회](/home/ubuntu/KORStockScan-storage-archives/holding-quote-manual-release-repair-20261027/current-holdings-final.json)는 승인된 native custody 환경의 read-only transaction으로 `recommendation_history` 전체 positive-quantity HOLDING/SELL_ORDERED를 조회했다. 두 번 모두 **0건**이다. 다른 보유를 일부 종목으로 제한해 정상 판정한 것이 아니다. record49532는 후속 조회에서 COMPLETED이며 buy_qty의 역사 값 1은 현재 보유 수량 증거가 아니다. broker 실잔고·체결·손익은 이 작업에서 판정하지 않았다.

공통 경로는 주성엔지니어링·삼성전자·두산에너빌리티 fixture와 전체 세션/적격성 조합으로 검증했다. 새 실보유를 만들거나 가입·주문을 실행해 자연 표본을 제조하지 않았다.

[10:54 PID 재고정](/home/ubuntu/KORStockScan-storage-archives/holding-quote-manual-release-repair-20261027/runtime-pin-final.json): 선택본은 계속 `quantity-pointer-20261027-97bc1f62e`, 앞서 고정한 Main PID4063772/start70694913/cwd 해당 release의 src를 읽었다. 최초 argv 직접-script/module 검색 결과가 비어 있었으므로 이를 Main 부재로 해석하지 않고 고정 PID로 재확인했다. 이번 코드의 배포/PID 소비나 현재 정책 소비를 새로 증명한 기록이 아니다.

## 리뷰·검증

- 원 수정 전 full handler causal regression은 수동관리 앞 REG event가 없어 실패했다. [원 실패 로그](/home/ubuntu/KORStockScan-storage-archives/holding-quote-manual-release-repair-20261027/original-causal-regression.log)를 보존했다.
- 자체 리뷰에서 plain 변환/reconnect, 이전 연결의 재등록을 새 가격으로 오인하는 경우, fresh 0D/0F가 오래된 0B를 되살리는 경우, 빠른 감시의 DB I/O 추가를 발견·보완하고 재리뷰했다. 항목/원본 가격/시각·epoch 검사와 Main binding 재사용으로 원인 경로를 닫았다.
- 새 WS 테스트의 첫 실행은 native `_send_reg`에 지원되지 않는 `required_realtime_types`를 준 fixture 오류 3건이었다. native signature의 `realtime_types`로 수정했고, 실패 로그 `expanded-regression-1.log`는 보존했다. 운영 결함/수리 통과로 오분류하지 않았다.
- 최종 검증: **2,035 passed, 0 failed, 0 skipped**, pandas_ta의 Pandas4Warning 1건(설치/버전 변경 없이 보존). [최종 로그](/home/ubuntu/KORStockScan-storage-archives/holding-quote-manual-release-repair-20261027/price-field-final-regression.log). 범위는 manual exclusion, market eligibility/session, WS, Main runtime, REST reduction, fixed-watch, fast-exit, 전체 sniper scale-in, engine location gate의 10개 파일이다.
- 실제 native REG/REAL→Main exact reader→기존 native auto-row 제거를 오프라인 연결해 검증했다. 잘못된 NX·fresh 0F와 이전 0B·새 연결 REG만 받은 상태는 차단되고 새 연결의 올바른 0B 이후에만 해제된다. 주문 경로는 실행하지 않았다.
- `git diff --check`, Python compile, Black 26.5.1 검사 PASS. 문서 링크/기존 stable owner/authority와 print-only backlog parser도 검증했다. 외부 Project/Calendar 동기화는 실행하지 않는다.

## 대체·제거·증가분

| 기존 경로 | 처분 | 소비자/이유 |
| --- | --- | --- |
| HOLDING의 fixed-watch 진입 템플릿/일반 latest 시세 선택 | consolidated | 초기 등록과 일반/빠른 보유 소비는 적격 exact reader로 통합. fixed-watch WATCHING·scanner와 현재 계약 이전 역사 경로는 해당 소비자 때문에 retained. |
| boot의 단일 priority 인라인 발행 | removed/replaced | `_publish_initial_ws_registrations`가 holding/기존 priority/scanner를 구분. run_sniper가 직접 소비하며 이전 인라인은 삭제. |
| auto-release의 generic curr/last_ws 시각 검사 | consolidated | `_holding_source_trade_quote`를 Main/자동 해제가 공유. 원 generic 중복 검사는 삭제. |
| 현재 보유 WS 복구의 sell-route 선택/alternate route 추가 | replaced | 시장 데이터 적격성 선택으로 대체. 실행 route resolver는 실제 sell와 현재 계약 이전 재생 소비자가 있어 retained. |
| 통합 flag일 때만 primary 격리 | replaced | 어느 primary 항목이든 동일 원칙 적용. 다른 route는 기존 관측 store에 보존. |
| native auto/manual 파일 writer·수동 veto·stop/주문/퇴역 guard | retained | 현재 소비자가 유지되며 권한/안전장치 변경 없음. |

새 Python 모듈·CLI·worker·정책 owner는 0개다. 기존 역할 모듈 내부 helper 7개로 pure 선택, native read, bound quote, 초기 dispatch와 빠른 재사용을 나눴다. 런타임 새 진입점/registry/schedule은 추가하지 않았다. 직접/동적 호출·boot dispatch·fast monitor와 관련 회귀 소비자를 대사했으며 이번에 대체된 인라인/중복 검사는 남기지 않았다. 역사 reader와 기존 주문 route는 명시한 현재 소비자 때문에 보존한다.

기준 `97bc1f62e` 대비 non-test source는 **+313/-54 (net +259)**, tests는 **+770/-0**, docs는 **+80/-0**(audit79행·기존 checklist1행)이다. source 증가분은 기존에 없던 적격성·가격/연결 결속과 초기/빠른 소비 연결이다. 테스트는 원 사건의 full handler, native producer→consumer 연결, route/세션/원 master/transport 전환 및 명시 veto의 서로 다른 실패를 다루며 단순 출력 복제 테스트가 아니다. unrelated canonical dirty 변경은 포함하지 않는다.

## 남은 수용·다음 동작

코드·오프라인 인과/회귀 완료와 운영 수용을 구분한다. 이번 요청 범위의 끝은 작업별 clean commit/push다. 다른 세션의 배포/복구를 중복 실행하지 않는다.

기존 HoldingProfitExitSourceContractRepair owner는 승인된 후속 통합 배포 뒤, 최초 실제 SCALPING 보유에서 selected release/PID→exact native eligibility→REG item→현재 epoch의 0B→자동 등록 row의 평단 도달 해제→기존 veto/guard 유지까지 대사할 때 닫는다. 10/27 남은 정규장에 적격 실제 보유가 없으면 첫 다음 거래일 10/28 08:00~08:50 NXT 적격 PRE 및 09:00~15:30 REG를 구분해 확인한다. KRX-only 종목의 PRE 미수신은 잘못된 NX 가입으로 보완하지 않는다. 현재 실제 보유 0건/코드 테스트 PASS를 자연 해제 완료나 체결·경제성 PASS로 바꾸지 않는다.
