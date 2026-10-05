# 비삼성 현행 강약 입력 복원·청산 재생 계획

## 범위와 소유

- 사용자 다음액션 실행. `pullback_p60_v0`, 부모 정책, 9/29·9/30·10/2 원천 및 직전 연구의483개 첫 anchor를 그대로 사용한다. 삼성·보조 AI·새 원천 수집은 제외한다.
- 코드는 기존 scalping 연구 패키지의 `entry_mechanical_exit_research.py`, 테스트는 `src/tests`에 둔다. 직전 봉인 연구 코드/산출물과 운영 소비자는 수정하지 않는다.
- 소유자:10/5 `NonSamsungMechanicalExit1005`. 결과는 `tmp/non-samsung-mechanical-exit-20261005`에 격리한다. 기준·결손을 바꾸어 정책을 선정하지 않는다.

## 공식 규격과 복원 계약

- 공식 저장소 current main `953e5dbff123f437ab4d11a78a95191a685eb51f`, 조회 `2026-10-04T23:37:16.653940+00:00`(10/5 08:37 KST)을 확인했다. 해당 tree에는 `kiwoom_docs`가 없다.
- 검사 경로: `kiwoom/_data/kiwoom_api_spec.json`의0B/0D, `kiwoom/specs.py`, `kiwoom/core/{client,ws_client}.py`, `kiwoom/realtime/{decoders,schemas,packets}.py`, Postman collection. 원문/해시는 산출물의 `upstream`에 보관한다.
-0B 거래량15는 명시적 `+` 매수/`-` 매도이며,13은 누적거래량이다. quote10/27/28의 가격 부호를 거래 방향으로 쓰지 않는다.0D의41/51 가격과61/71 수량은 원 canonical top-of-book에서 가져온다. KRX/plain, NXT/_NX, SOR/_AL을 바꾸지 않는다.
- 원 producer `forward_collector.py`가 raw15를 `trade_volume_raw`로 저장함을 확인했다. 명시적 부호·양의 정수·canonical 체결 수량 일치를 만족하는 행만 분류기 signed source로 복원한다. 무부호/0/잘못된 값/수량 충돌은 UNKNOWN이며 기존 side로 대체하지 않는다. 원 문자열·해시·기존 side와의 차이를 보존한다.
- upstream REAL/REG/REMOVE, URL/real-demo, 시각·단위와 local raw mapping을 교차 확인했다. 이 연구는 저장 원천만 읽는다. 인증·WS 연결·등록·계좌/주문·REST·continuation 변경/실행은 없다.

## 고정 실험

1. 이전 원천/선택 릴리스/10/6 준비 policy hash를 재검증한다. 원 ask와 전비용, default Main SCALP stop-1.4/emergency-2.4 및 trailing start0.4/weak0.4/strong0.8을 고정한다.
2. archive 자체 item/epoch/sequence/시각으로 정규화한다. 첫 진입에서 분류기 상태를 초기화하고 진입 이전 강약을 승계하지 않는다. 현행 `classify_ws_history`를 직접 호출하며120개 bounded buffer·1초 tape·700ms quote 기준과 두 번의 악화 확인을 그대로 쓴다.
3. 실제 runtime의 depth bid와 실행 bid 불일치/수량 결손 시 강약 UNKNOWN 처리도 반영한다. UNKNOWN은 label로 보존하고 현행 `strong == STRONG` 분기대로 약세 폭을 사용한다. UNKNOWN을 실제 약세 증거라고 기록하지 않는다.
4. 같은 이벤트와 진입에 고정 weak·고정 strong·복원 M1 세 경로를 함께 계산한다. peak는 진입 후 신선한 체결, 청산은 유효 bid로만 판단한다. 이벤트 시각 재생이며 PID의250ms poll 스케줄이나 주문/체결을 복원한 것으로 주장하지 않는다.
5. 원천 epoch/순번/서로 다른 스트림의 같은 시각 순서 불명에 도달하면 그 뒤의 첫 청산을 확정하지 않는다. 가격 CF와 실제 체결/PnL을 분리한다. 강약 입력이 복원돼도 원 보유·protect/AI·주문 상태 결손이 사라지는 것은 아니다.
6. 동일 진입/공통 평가 분모의 결과 차이, STRONG/WEAK/UNKNOWN·전환·원천 이유, 목표 선도달 이후 이익 반납 경로를 출력한다. 후속 점유도 별도 비교한다. 미확정/검열을 손실·0수익으로 바꾸지 않는다.

## 완료 기준

공식 원문/원 producer 대사 → adapter/현행 분류기 연결 → source/clock/초기화/UNKNOWN·상태 전환 회귀 → 리뷰/수정 → 격리 전수 재생 → 고정 폭과의 paired 비교/미복원 범위 → 재리뷰/compile/hash/link/단일 owner/diff/print-only parser. 성공100%/80% 보존 veto와 운영 배포/기동은 없다.
