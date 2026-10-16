# 비상시 원천 연속성 및 제어응답 수리 — 2026-10-16

Owner: `NonfixedDispatchReadinessReview1012`. 사용자 승인: 개선·리뷰·보완·배포·재기동. 기준 배포본45fa0470e/PID167546에서 f1863b353의 문서 후속을 보존한 별도 작업 트리로 구현했다. 다른 작업공간의 미커밋 변경은 포함하지 않았다.

## 수리 및 리뷰

1. 같은 exact item/route/transport epoch/physical lease와 원 native observation의 PID/start·신호·기한을 검증한 경우, WS 잠금 안에서 기존 수신 버퍼의 쓰기 소유권을 Main으로 이동한다. 과거 snapshot을 임의 복사하거나 native ingest를 재실행하지 않는다. strength 이력에 원 item/route/epoch/sequence/수신시각을 연결했다. 잘못된 이력·미래시각·현재 stale·0D 결손은 연속성 승인에서 제외한다.
2. Main 신규 편입과 WATCHING 갱신에 같은 불변 영수증을 전달한다. 일반 post-attach 검사는 유지하고, 검증된 연속 원천만 별도 준비 조건으로 인정한다. 실제 첫 post-attach 수신시각과 연속 원천 준비를 구별한다. no-trade eviction도 같은 검증을 사용한다. 원 5초 deadline과 native claim, 수량/계좌/주문/manual/stop 가드는 유지한다.
3. finalize의 signal/event ID를 실제 nested snapshot에서 읽는다. 신규 target은 adoption 이전에 생성되므로 영수증을 이후에 명시적으로 전달하는 누락을 방지했다. 갱신 시 옛 영수증도 제거한다.
4. bootstrap 00/0s를 포함한 REG/REMOVE 전송과 응답을 기존 WS 소유자에서 bounded 메모리(요청128/응답128)로 보존한다. wire payload·구독 수·재시도·타임아웃·로그인 정책은 변경하지 않는다. 전송 중 응답, uncertain send, 중복/늦은 응답, reconnect를 구별한다. 공식 최소 응답에 요청 식별자가 없으므로 동일 연결에서 유일했던 첫 요청/첫 응답만 귀속하고, 복수 요청 또는 이전 응답이 있으면 연결 단위 unknown으로 보존한다. FIFO 추정이나 ACK 대기를 하지 않는다.
5. 리뷰에서 local `registered`를 서버 결과와 혼합한 부분을 수정했다. local 등록 여부와 `server_registration_rejected`를 분리하고, 확정 거절만 원 probe의 기존 종료/cleanup owner에 전달한다. 다른 lease/current owner를 제거하거나 추가 retry를 만들지 않는다. source trace와 dashboard 등록 영수증은 서버 결과/실제 wire/정규화/native를 구별한다.
6. 미배포 보고 전용 수정29a973248을 통합했다. 방향 미확정 첫 0B가 있는 검증된 feature-gap 관측은 명시적 signed count0을 허용하되 no-match/평가/주문 가능으로 승격하지 않는다. 기존 source/PID/시각/집계 검증은 유지한다.

새 파일의 위치는 live 원천 인계 계약을 소유하는 `src/engine/scalping/native_source_continuity.py`와 WS 제어 영수증 인프라를 소유하는 `src/engine/infrastructure/ws_control_receipts.py`다. engine root 모듈을 추가하지 않았다.

## 검증

- Main 인계/WS/entry latency/shared deadline: 538 passed (최초 교차 회귀).
- 보완 후 WS/Main 인계/정규 배포·인계 gate: 2613 passed.
- monitor/artifact freshness: 1087 passed.
- no-trade 및 실제 post-attach clock: 10 passed.
- 최종 제어응답/원천 probe 회귀와 거절 cleanup 검증은 아래 evidence의 `pytest-control-final.txt`, `pytest-rejection.txt`에 보존한다. 중복 실행 횟수를 유일 테스트 수로 합산하지 않는다.
- 원천 버퍼 보존→신규 Main 편입→precheck→동일 native claim·원 deadline 연결을 격리 검증했다. 실제 provider/order 호출 및 전체 주문 경로 재생은 하지 않았다. 자연 AI PASS/submit/broker/fill/경제성은 별도 수용이다.
- 기존 pandas_ta Pandas4Warning 1종 외 오류 없음. 프로젝트 Python compile, diff check 및 print-only checklist parser를 수행한다.
- 고정 native parity: 128 scopes / 76,800 rows / 594 hits, 기존 배포본과 signal digest 동일, mismatch0. native 계약 모듈 bytes도 동일하다.

## 공식 API 참조

2026-10-16T18:44:06+09:00 HEAD 재조회: `953e5dbff123f437ab4d11a78a95191a685eb51f`. 해당 revision의 `kiwoom/core/ws_client.py`, `kiwoom/realtime/{stream,packets,schemas}.py`, `kiwoom/specs.py`, packaged `kiwoom/_data/kiwoom_api_spec.json`의0B/0D·REG/REMOVE와 Postman collection을 대조했다. `kiwoom_docs`는 해당 tree에 없다. 공식 최소 제어응답은 trnm/return_code/return_msg만 제공하며 요청 순서·종목 귀속을 추정하지 않는다. 원 자료는 선행1814 점검과 아래 evidence에 보존한다. 실계좌/주문/API 호출로 확인하지 않았다.

## 배포 경계

이번 수정은 Main 입력 경로 변경이며 보고서만의 변경이 아니다. 기존 장기4/단기1, 손절, VI 제외 범위를 유지한다. exact PREOPEN 원본23a13aba628과 검토된 새 handler/Main/monitor bytes의 source pair만 인계 validator에 추가했다. 후보 커밋의 active-policy handoff와 fresh native parity를 정지 전에 발급·검증한다. 원 정책/PREOPEN/strict/실패 기록은 변경하지 않는다. 정규 ordered transition 후 actual PID 소비와 startup observer publication, full detector를 확인한다. 이 문서의 커밋 시점에는 배포 전이며 실제 전환 결과는 아래 최종 영수증으로 보고한다.

Evidence: `/home/ubuntu/KORStockScan/tmp/nonfixed-source-continuity-20261016/`.
선행: [구현 전 상세 리뷰](/home/ubuntu/KORStockScan/tmp/nonfixed-implementation-review-20261016-1830/report.md).
자연 잔여: 새 PID에서 원 신호→AI/Main/submit을 관측하며443670/007610 과거 수신0을 소급 정상화하지 않는다. source gap과 경제성은 구현/기동 성공과 별개다.
