# 최초 수량 cap 호가·틱 재생 코드 재리뷰 — 2026-09-27

## 결정·범위

- 사용자 결정: 10/15/20% cap의 대체 수량은 당시 0D 매도 호가 잔량과 후행 0B 매수 주도 틱을 보수적으로 재생하고, 근거가 부족한 부분은 미체결로 남긴다. 최초 정책의 우월성 허들은 요구하지 않으며, 적용 후 갱신에만 강한 비교·원천 허들을 적용한다.
- 이번 변경은 실제 첫 진입의 source-only 호가/틱 생산자와 장후 cap 반사실 평가·유형별 선정이다. 주문 API·FID 파서·구독·실주문 수량/가격/타임아웃을 직접 바꾸지 않는다. 선정된 cap은 기존 갱신 후보→검증 stage→runtime 정책→allocator→current CAS 경로로만 전달한다.

## 코드 리뷰에서 찾고 고친 사항

1. 후행 틱이 청산 뒤 관측됐는데 진입 시각 ±1시간 join에 들어올 수 있었다. 이벤트 시각과 원천 관측 시각 모두 실제 청산 이내로 제한하고 회귀를 추가했다.
2. 캐시된 0B 틱과 채택된 quote가 다른 시각이면 같은 route/epoch이라도 결속하지 않는다. 두 원천 시각을 1ms 이내로 대사한다.
3. 익절 거래 가중평균이 cap 선정에만 표시되고 선택 판단에는 쓰이지 않던 경로를 고쳤다. 형상·시간·cap 후보의 익절 실현 순이익 원화 가중 성과를 비교하면서 손실 거래를 전체 비용 후 PnL/EV와 일별 위험에 유지한다.
4. 같은 종목에서 새 진입을 판정할 때 이전 cap 추적 정보가 남을 수 있었다. 새 판정에서 이전 정보를 지우고 1200초가 지나면 제거한다.
5. cap 원천이 없거나 broker 실제 체결 ledger와 사실 거래 수량/단가가 맞지 않으면 후보 수량을 만들어 내지 않는다. 실제 체결량 초과분은 당시 잔량과 후행 틱 양쪽으로 확인한 만큼만 조건부 체결하고 나머지는 `partial_unfilled`로 보존한다. 이를 실제 broker 체결로 표현하지 않는다.

## 검증 증거

- 수량 정책·타임아웃·bundle·terminal·진입 수량·allocator·bootstrap·장후 wrapper 영향 pytest **238건 PASS**(106.31초). 재리뷰 후 격리 릴리스에서 수량 정책·타임아웃·bundle·terminal **94건 PASS**(4.16초). 최종 trace 수리 뒤 진입/원천 표적 결과는 아래 최종 배포 기록에 적는다.
- 9/23까지 클린 기준 이후 완료 거래 **387건**, 유형 모수 `SAFE_UNKNOWN 350 / KRX_PARENT 32 / KRX_THIN_HIGH_TICK 5`, 최초 형상 6유형 모두 `parent`; replay 검증 PASS. 같은 봉인 거래 facts의 격리 재생 wall **368.549초**, CPU user/system **350.429/2.297초**, peak RSS **111,992KiB**, swap 0, read blocks 11,322,184, write blocks 0, 결과 SHA `998cc46510ef3c31933ea27420b50a5456a3061290cad90f07ef787aefacd2c0`이다. 역사 원천에는 새 cap 호가·틱 기록이 없어 이 387건으로 cap 승격을 주장하지 않는다.
- 새 코드의 9/27 적용 세대 0건 격리 CLI: `carry_parent`, stage terminal validator PASS, wall **0.401초**, CPU user/system **0.482/0.048초**, peak RSS **141,440KiB**. 과거 stage는 새 모델 버전이 없어 현 validator가 거부하며, 새 코드로 다시 생산한 stage만 사용한다.
- 9/28 **정규 장후 전체 wrapper→summary→strict→CAS의 자연 성능**은 원천일과 실제 실행 후 수용한다. 배포 전 격리 재생은 그 영수증을 대신하지 않는다.

## 공식 프로토콜 대조

- 2026-09-27 18:35 KST에 공식 `Kiwoom-Securities/Kiwoom-REST-API` commit `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/_data/kiwoom_api_spec.json`(0B FID 15 부호, 0D FID 41/61 가격·잔량), `kiwoom/realtime/decoders.py`, `kiwoom/specs.py`를 확인했다. 이 revision에는 `kiwoom_docs` 디렉터리가 없다. 기존 `src/trading/market/quote_consistency.py`와 WS 정규화 영수증의 route/item/transport epoch/time 계약을 함께 확인했다. 신규 wire·FID mapping·구독·주문 call은 없다.

## 코드 선택과 미래 수용

- 불변 코드 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-cap-depth-replay-20260927` commit `50ffc08ee976fb0cabb6cc23aae355ccfd8d7b02`를 메인 selector에 원자 선택했다. 이전 선택 `bee25b17` JSON은 `tmp/runtime-release-selection-before-initial-cap-depth-replay-20260927.json`에 보존했다. 선택 릴리스의 코드/테스트 파일 4개만 변경했고 `src`, `deploy`, `restart.sh`의 추적 파일은 clean이다. release-set PASS, cron 필수 8경로 PASS, 9/28 PREOPEN/start print-plan 모두 새 commit을 가리킨다. 선택 릴리스에서 최종 trace 수리 뒤 cap 원천 2건, 진입 수량 64건 PASS(106.23초), compile·Ruff·diff PASS다.
- 현재 v2 `current.json` 파일 SHA `a34d980f13be8c4929012557f23958871c832edb118058f498420ab078b83585`, 정책 파일 SHA `ba72d720a4c11dbcfd18a667d2f47a648c0e7b792fe9a3edbb7193f674870cca`는 값 변경 없이 보존했다. 선택 릴리스에서 9/28 `build_manifest`를 읽기 전용 재구성해 동일 정책 SHA가 env/receipt에 들어감을 확인했다. 기존 9/28 bootstrap 파일은 정규 PREOPEN의 원자 재생성/verify 대상이다.
- 정상 9/28 PREOPEN이 새 manifest/env/verify를 발행한 뒤 실제 Main PID의 같은 정책 SHA 소비를 확인한다. 자연 cap 원천·거래/취소 terminal·비용 후 정책 갱신 근거는 이후 별도 수용한다.
