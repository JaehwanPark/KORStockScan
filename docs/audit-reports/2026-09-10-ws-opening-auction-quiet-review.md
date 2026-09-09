# 9/10 동시호가 무수신 진단 계약 보완

## 범위와 사전 근거

사용자 요청: 08:50~09:00 동시호가/휴장 구간의 예상된 무수신을 장애로 오인하지 않도록 코드와 계약 보완. 수신 기대 진단만 변경하며 연결/LOGIN/REG 오류·저장 실패·stale 주문 guard·재기동·실주문 권한은 변경하지 않는다.

공식 Kiwoom upstream을 2026-09-10 08:20 KST 이후 읽기 전용 재확인했다. `git ls-remote HEAD`와 기존 checkout SHA는 모두 `234560d213acd8871ae344b5481aecd2f30287fa`다. `kiwoom_docs` 부재 상태에서 `kiwoom/specs.py`, packaged spec의 0B/0D, `kiwoom/realtime/{packets,schemas,stream}.py`, `kiwoom/core/ws_client.py`, Postman을 확인했다. 운영/모의 WS URL·LOGIN/PING·REG/REMOVE·refresh·KRX/NXT/SOR item과 오류 응답을 대사했으며 실제 API는 호출하지 않았다. 예상체결/호가 패킷까지 반드시 중단된다고 해석하지 않는다.

거래시간은 [NXT 공식 거래제도](https://www.nextrade.co.kr/menu/transactionSys.do)의 프리마켓08:00~08:50, 메인09:00:30~15:20을 따른다. 이 수리는 KRX/NXT/SOR의 공통08:50~09:00 및 NXT-only09:00~09:00:30 경계에 한정한다. 일반 휴일/VI/임시 시장시간/다른 구간을 새로 추정하지 않는다.

위치 gate: runtime WS와 offline freshness producer가 함께 쓰는 순수 진단 함수를 `src/engine/monitoring/ws_receive_expectation.py`에 둔다. engine root 새 모듈·별도 서비스/정기 producer는 만들지 않는다. 기존 WS/문서의 병행 사용자 변경은 보존한다.

## 구현·재리뷰

- WS `get_subscription_freshness_snapshot`에서 등록 route와 실제 as-of로 `expected_market_quiet`를 계산한다. raw age/미수신 type/원 상태와 재개 시각은 보존하고 absence-only 복구 권고만 제외한다. 미등록·알 수 없는 route/시각·명시적 오류를 정상 구독/fresh로 바꾸지 않는다. 실제 REG/REMOVE 송신·LOGIN 처리·시장 raw 파서·bot/주문 guard는 변경하지 않았다.
- #89 producer는 과거 pipeline event 시각과 snapshot 시각을 사용한다. current snapshot은 현재 as-of로 재평가하며 장후 finalize는 원 시각으로 평가한다. 이전 quiet marker를 영속 면제로 사용하지 않고 개장 후 원 repair 상태를 복원한다. cache v16→v17로 구 집계가 재사용되지 않는다.
- dashboard가 REAL 수신 때만 저장되는 직접 경로도 확인했다. same-date/지원 schema/확인된 route이고08:49:30 이후 생성된 파일만 해당 휴지 동안 `scheduled_opening_gap_snapshot`으로 읽을 수 있다. 원 파일 age를 보존하고 `current_freshness_usable=false`이며 더 오래된 파일·다른 날짜·개장 후 미갱신은 계속 source gap이다. 과거 quote를 실행 가능한 fresh로 만들지 않는다.
- 재리뷰 보완:08:50 이전부터 이미 stale한 receive gap은 quiet로 덮지 않는다. 비정상 age/필수 type 계약도 면제하지 않는다. quiet 전용 관찰창은 수신 결손 진단률의 정상0% 표본이 아니므로 해당 rate를 null로 두고 eligible 분모를 따로 제공한다. 혼합 창에서도 quiet가 실제 fault 비율을 희석하지 않는다. 별도의 실제 decision-stage stale 차단·Provider 오류·queue/writer/storage 및 오류 detector는 유지한다.
- 기존20:10 장후 및 장중 #89 producer를 재사용한다. 설치 cron상 장중 첫 실행은09:05이며, 다음 호출에서 새 report 코드를 읽어 과거 동시호가 event도 분리한다. 실행 중 WS PID는 수정 모듈을 자동 reload하지 않는다. 이번 작업은 운영 report 재생성·재기동·실주문·정책/env/guard 변경·Project/Calendar sync를 실행하지 않았다.

## 검증과 남은 acceptance

경계08:49:59/08:50/09:00/09:00:30, 혼합 route/UNKNOWN, pre-existing gap, 명시적 연결·ACK·저장 실패, 미래/과거 snapshot, 일중→장후 cache 재소비와 개장 후 복구 권고 재개를 격리 fixture로 검증한다. 원 runtime quote·subscription route consumer, 오류 detector와 checklist builder도 회귀 범위에 포함한다.

자연 acceptance는 현재 체크리스트의 `RuntimeEnvIntradayObserve0910`(09:05~09:20)에 연결했다. #89 다음 자연 output·현재 WS 코드/PID 세대·개장 후 수신 재개는 테스트와 별도다. 코드 반영이 아직 없는 PID를 재기동 없이 새 동작으로 표시하지 않는다. 현재 새 수익/경제성 개선을 측정한 작업이 아니다.

최종 검증: 위8개 테스트 모듈 **617 PASS / 12.95초**, pandas_ta의 기존 pandas Copy-on-Write deprecation warning1개. Ruff·Black check·Python compile·`git diff --check` PASS. 문서 print-only parser30건/당일14건·ID 중복0이며 신규 checkbox는 만들지 않았다. review→경계/영속 marker·개장 전 기존 결손·quiet 분모 보완→재리뷰→회귀 검증을 거쳐 **이번 수신 기대 진단/계약 범위 미해결 finding0**이다. 병행 parser/적응형 청산/recheck 변경 전체의 완료나 현재 PID 적용 성공으로 확대하지 않는다.

## 후속 사용자 재리뷰 — 9/10 08:40 KST 이후

위617건은 최초 검증 receipt다. 추가 반례에서 다음 다섯 결함을 재현한 후 수정했다.

1. 저장된 quiet의 원 repair metadata가 새 ACK 실패를 덮었다. 현재 값이 이 classifier 자신의 quiet 출력인 경우에만 원 repair를 복원한다.
2. fallback의 관측 NXT가 함께 제공된 KRX 정보를 가려09:00~09:00:30에도 면제했다. 등록 route가 없는 경우 제공된 fallback route 전체를 대사한다.
3. dashboard adapter가 명시적 연결/저장/ACK 오류를 버렸다. 해당 진단 필드와 fallback route를 보존한다.
4. 개장 후 영속 no_tick marker의 원 상태를 복원해도 pipeline stale 집계가 이전 marker를 사용했다. 복원된 진단을 집계에 반영한다.
5. 잘못된 age가 snapshot 변환에서 null/no_tick으로 정규화된 뒤 정상 무수신으로 면제됐다. NaN/음수/파싱 실패/bool을 계약 결손으로 보존한다.

최초 추가6개 반례 실패→수정 후 관련102건 PASS→두 번째 추가4개 반례 실패→추가 수정→동일8개 모듈 **627 PASS / 13.17초**로 재검증했다. cache v18은 과거 잘못된 quiet 집계의 재사용을 막는다. 현재 범위의 helper·dashboard/explicit snapshot·pipeline·집계/후속 consumer 재리뷰를 수행했다. 운영 보고서 재생성·PID reload·재기동·주문/guard 변경은 하지 않았으며 자연 acceptance owner는 기존 `RuntimeEnvIntradayObserve0910`를 유지한다.

후속 검증: Ruff·Black check·Python compile·문서 print-only parser30건·`git diff --check` PASS. 테스트 warning은 동일한 pandas Copy-on-Write deprecation1건이다. 추가 반례 수정 뒤 이번 수신 기대 진단/직접 consumer 범위의 미해결 finding0이며, 병행 변경 전체나 자연 운영 성공의 판정은 아니다.
