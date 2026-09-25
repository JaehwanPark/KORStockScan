# 스캘핑 익절 운영 입력 재생 구현·재검토

기준: 2026-09-25 KST 작업본. 이 기록은 코드와 합성 원천의 검증이며 선택 릴리스, 실제 PID 소비, 자연 완료 포지션의 비용 후 개선 또는 운영값 변경을 증명하지 않는다.

## 선행 4축 최종 점검

- 현재 `trailing_four_axis_replay.py`는 더 이른 후보의 최우선 bid 전량 수량 확인과 0/30/100bp 슬리피지 민감도, 잔량 부족 검열을 계산한다. 관련 시작값·4축 회귀 27건이 통과했다.
- 실제 익절보다 늦은 후보는 후행 실행가능 bid·경쟁 청산 경로가 없으면 여전히 `censored_after_actual_take_profit`이다. 9/25 저장 보고서의 엄격 완료 모수는 0건이고 완료 census는 미봉인 62일·평일 스냅샷 결손 20일로 불완전하다. 따라서 원천 연결과 4축 실행·검열 모형의 **실데이터 최종 수용은 미완료**다. 사용자의 완료 진술을 작업본의 자연 증거로 대체하지 않는다.

## 운영 입력 구현

- 새 계산 owner는 `src/engine/scalping/trailing_operational_replay.py`다. 기존 `scalp_trailing_input_transition`과 엄격 완료 position outcome을 사용해 17개 운영값의 진단 격자와 현행값을 프리마켓·정규장·통합애프터마켓으로 나눈다. `QUOTE_CONSISTENCY_OK_GAP_BPS` 30bp는 공유 분류값으로 남기고 익절 후보에서는 제외한다.
- 런타임 관측은 값·원천·position identity와 함께 AI 재평가 전 이익·가격변화·경과시간, NXT 0B/0D age·item·route, WS/REST age·gap, 실제 REST 요청 경과시간과 재시도 간격, 원시 0D/REST bid 잔량을 기록한다. 매 평가에서 고정 진단 격자의 gate vector hash를 계산해 경계 변화 시 bounded transition을 남긴다. 장후 계산은 같은 version/hash·평가시계·원천세대를 재계산하여 누락·변조·초과 시 ID별 source gap으로 격리한다.
- 후보별 관측 metric crossing 수, 최초 변화 시각, 변경·미식별·결손 ID를 분리한다. 빠른 polling, 변경된 AI provider 출력, 미관측 REST 응답, 변경된 시세 채택과 체결은 반사실 결과로 만들지 않는다. 모든 후보의 `paired_ev_pct`와 적용값은 `null`이다. 공유 시세·REST는 entry/scale-in/holding/stop/protect/emergency 전체의 안전 검토, 보유 AI는 real/sim·provider 비용·TTL 검토가 필요하다는 owner receipt를 내고 `allowed_runtime_apply=false`를 유지한다.
- 기존 full monitor snapshot의 holding-exit observation에 `trailing_operational_input_replay`를 추가하고 sentinel·runtime summary는 상태·source gap만 소비한다. 새 wrapper, Kiwoom API 요청·응답 parser, 정책·임계값·실주문 동작은 변경하지 않았다.
- 재검토에서 실제 NXT route는 `nxt_only` 또는 `krx_nxt_integrated`이며 `_AL`·`_NX`가 모두 가능함을 확인했다. 재생은 NXT guard 원천 item·route를 사용한다. 보유 AI의 sim 전용 cooldown은 실거래 cadence 후보에 섞지 않고 결손으로 격리한다. 80bp는 fast 경로에서 스프레드·mark 대비 bid 차이를, 공통 분류에서 5호가 tick 하한을 함께 적용한다. owner receipt에는 공유 quote/REST·AI·스캘핑 입력의 실제 코드 경로와 교차 소비자 검토 범위를 기록한다.

## 리뷰·검증과 남은 경계

- 첫 회귀에서 17개 값 외 공유 30bp가 원본 hash에 포함된다는 점을 확인하여 값 subset 검사와 전체 원본 hash 검증을 분리했다. 후속 회귀에서 긴 평가 간격의 허위 coverage, NXT route 오분류, 프리마켓 청산 불가 관측, normal/fast 소유 평가 혼합, sim AI cooldown 혼합, 80bp 근사 계산을 찾아 shadow hash·실제 route·clock·evaluator별 노출·원천별 판정으로 수정했다. 기존 큰 핸들러의 unrelated Ruff 경고는 이 변경으로 생성되지 않았으며 변경 모듈 검사는 통과했다.
- 영향 범위 pytest 347건과 후속 회귀 79건·보고서 연결 25건, Python compile, 수정 모듈 Ruff, `git diff --check`를 통과했다. 최종 코드의 합성 shadow gate 10,000회는 0.681초(평가당 68.1µs), 합성 329 포지션×40 전이 운영 집계는 0.411초였고 source gap은 0건이었다. 이는 원천 I/O·동시 live 부하·전체 장후 chain 성능 증명이 아니다.
- 현재 값 비교는 **관측 입력 민감도**까지 가능하다. 운영 후보의 실행 가능 비용 후 손익을 비교하려면 후보가 바꾼 시세·AI 호출 이후 원천, 주문 지연/부분체결, 공유 소유자 안전 결과와 새 자연 완료 모수가 필요하다. 식별 불가를 0효과나 정책 후보로 바꾸지 않는다. 9/28 `HoldingExitPositionOutcomeLineageClosure`에서 새 원천의 shadow hash·ID 분모와 실제 PID 세대를 확인한다.
