# 2026-04-07 코드베이스 증가 대응 저위험 리팩토링 사전검토 작업지시서

## 목적

- 코드베이스가 커지는 흐름에 대비해, 로직 변경 없이 유지보수 난이도만 낮추는 저위험 리팩토링 작업 순서를 정한다.
- 특히 `중복 import`, `중복 호출`, `중복 파라미터 정규화`, `중복 스냅샷 로드/빌드 분기`처럼 행동 보존이 쉬운 항목만 먼저 다룬다.
- 의사결정 엔진, 주문 처리, 손익 계산처럼 거래 결과를 흔들 수 있는 핵심 로직은 이번 사전검토 범위에서 제외한다.

## 최우선 원칙

1. 로직을 바꾸지 않는다.
   - 조건식, threshold, AI prompt, order lifecycle, cache key, DB write timing은 손대지 않는다.
2. 호출하는 쪽부터 정리한다.
   - 라우트/화면/오케스트레이션 레이어를 먼저 정리하고, 실제 계산/판단 함수는 나중에 본다.
3. 작은 단위로 나눈다.
   - 한 번에 큰 공통화나 프레임워크화는 하지 않는다.
   - "같은 코드 2~3군데를 helper로 묶는 수준"까지만 허용한다.
4. 출력 형태를 유지한다.
   - API JSON shape, 화면 텍스트, 로그 stage 이름, DB 저장값은 변경하지 않는다.
5. 테스트 없이 합치지 않는다.
   - 최소 `py_compile` + 기존 관련 pytest로 회귀 확인 후 반영한다.

## 이번 작업에서 허용하는 변경

- 중복 import 제거
- 같은 파일 안의 반복 파라미터 파싱 helper 추출
- 같은 파일 안의 반복 snapshot load/build 분기 helper 추출
- 같은 파일 안의 반복 `jsonify(report)` / `render_template_string(...)` 직전 데이터 준비 정리
- 동작이 같은 문자열/상수의 지역 상수화
- 읽기 어려운 장문 함수에서 "행동 보존 helper"로 분리

## 이번 작업에서 금지하는 변경

- AI 점수 기준, 시장 국면 기준, hard stop, early exit, near band, cache TTL 조정
- 주문 전송/체결 매칭 순서 변경
- `sniper_state_handlers.py`, `ai_engine.py`, `sniper_execution_receipts.py`, `sniper_sync.py` 내부 의사결정 로직 수정
- 로그 stage 이름 변경
- API 필드명 변경
- 클래스/모듈 대규모 재구성
- 호출당하는 함수의 시그니처를 먼저 바꾸고 상위 호출부를 나중에 맞추는 작업

## 호출 계층 기준 작업 순서

### 1차: 웹/화면 라우트 계층부터 시작

우선 대상:

- [app.py](../src/web/app.py)

이유:

- 현재 가장 바깥 호출 계층이다.
- 여러 리포트 빌더를 호출하는 구조라, 여기서 중복을 줄여도 내부 로직을 흔들 가능성이 낮다.
- 이미 `performance-tuning`, `trade-review`, `daily-report` 등에서 유사한 파라미터 정규화와 snapshot 분기 패턴이 반복된다.

이번 단계 허용 작업 예시:

- 상단에서 이미 import한 `datetime`을 route 내부에서 다시 import하는 패턴 제거
  - 예: [app.py](../src/web/app.py#L75), [app.py](../src/web/app.py#L620)
- `target_date`, `since`, `refresh`, `top` 파싱의 중복 helper화
- `snapshot 있으면 사용 / 없으면 build` 패턴을 리포트별 얕은 helper로 정리
- API route와 preview route가 공유하는 입력 정규화 코드를 합치되, 응답 shape는 그대로 유지

주의:

- 라우트를 데코레이터/메타 프로그래밍으로 일반화하지 않는다.
- 템플릿 구조를 손대는 리팩토링은 "중복 제거가 명확한 경우"만 허용한다.
- 화면 스타일/문구 변경은 금지한다.

완료 기준:

- 파일 길이가 조금 줄거나, 중복 블록이 helper 수준으로 정리된다.
- `/api/*` 및 preview route 응답 필드가 기존과 동일하다.
- 기존 성능 모니터, trade-review, strategy-performance, entry-pipeline-flow가 모두 정상 렌더링된다.

권장 검증:

- `./.venv/bin/python -m py_compile src/web/app.py`
- 관련 API smoke check
- 관련 pytest가 있으면 우선 실행

### 2차: 호출 오케스트레이션 계층

우선 대상:

- [bot_main.py](../src/bot_main.py)
- [kiwoom_sniper_v2.py](../src/engine/kiwoom_sniper_v2.py)
- [kiwoom_websocket.py](../src/engine/kiwoom_websocket.py)
- [telegram_manager.py](../src/notify/telegram_manager.py)

이유:

- 이 계층은 여러 엔진/리포트/이벤트를 호출하지만, 실제 판단 계산식은 상대적으로 안쪽에 있다.
- 바깥쪽에서 중복 로그 포맷, 중복 event publish, 중복 상태 텍스트 조립을 정리하면 유지보수성이 올라간다.

이번 단계 허용 작업 예시:

- 같은 이벤트 payload 조립 코드 정리
- 같은 상태 메시지 포맷 helper화
- 같은 시간 문자열/세션 날짜 계산 정리
- 같은 "캐시 읽기 후 없으면 계산" 호출 흐름 정리

주의:

- 주문 전송 순서, 체결 이벤트 처리 순서, active order 등록 시점은 건드리지 않는다.
- `EXEC_IGNORED` 계열 race 보정은 이 문서 범위가 아니다.

완료 기준:

- 중복 포맷/중복 publish 코드가 줄어든다.
- 텔레그램/콘솔/웹소켓 이벤트 의미는 바뀌지 않는다.

### 3차: 중간 리포트/집계 어댑터 계층

우선 대상:

- [daily_report_service.py](../src/engine/daily_report_service.py)
- [sniper_performance_tuning_report.py](../src/engine/sniper_performance_tuning_report.py)
- [sniper_trade_review_report.py](../src/engine/sniper_trade_review_report.py)
- [strategy_position_performance_report.py](../src/engine/strategy_position_performance_report.py)
- [sniper_entry_pipeline_report.py](../src/engine/sniper_entry_pipeline_report.py)
- [sniper_strength_observation_report.py](../src/engine/sniper_strength_observation_report.py)

이유:

- 이 계층은 이미 "호출당하는 쪽"이긴 하지만, 아직 계산 엔진 내부보다는 바깥쪽이다.
- 웹/오케스트레이션 계층 안정화 후 들어가면 안전하다.

이번 단계 허용 작업 예시:

- 같은 날짜 파싱 helper 재사용
- 같은 counter 요약 패턴 통일
- 같은 snapshot schema version 확인 패턴 정리
- 같은 warning merge / recent rows normalize 패턴 정리

주의:

- 손익 계산 공식, 상태 정규화 기준, lifecycle 보정 로직은 바꾸지 않는다.
- "중복 코드가 있어 보여도 미세하게 다른 의미"면 합치지 않는다.

완료 기준:

- 리포트 출력 JSON과 화면 렌더 결과가 동일하다.
- 최근 수정한 집계 항목(`holding_sig_deltas`, `swing_daily_summary` 등)이 그대로 유지된다.

### 4차: 실제 계산/판단 엔진은 나중에

후순위 대상:

- [sniper_state_handlers.py](../src/engine/sniper_state_handlers.py)
- [ai_engine.py](../src/engine/ai_engine.py)
- [ai_engine_openai_v2.py](../src/engine/ai_engine_openai_v2.py)
- [sniper_execution_receipts.py](../src/engine/sniper_execution_receipts.py)
- [sniper_sync.py](../src/engine/sniper_sync.py)
- [trade_profit.py](../src/engine/trade_profit.py)
- [sniper_market_regime.py](../src/engine/sniper_market_regime.py)
- [market_regime](../src/market_regime)

원칙:

- 이 레이어는 "중복이 있어 보여도 실제론 거래 의미를 품고 있는 코드"가 많다.
- 바깥 호출부 정리가 먼저 끝나고, 테스트/관측값이 충분해진 뒤에만 검토한다.
- 이번 사전검토 문서에서는 착수 금지 영역으로 본다.

## 현재 코드베이스 기준 1차 실제 후보

### A. 즉시 검토 가능

- [app.py](../src/web/app.py)
  - route 내부 `datetime` 중복 import 제거
  - route별 `target_date/since/refresh` 정규화 보조 helper 검토
  - route별 snapshot load/build 분기 정리

### B. 다음 검토 가능

- [bot_main.py](../src/bot_main.py)
  - 일일 리포트 호출/세션 날짜 계산 중복 확인
- [kiwoom_sniper_v2.py](../src/engine/kiwoom_sniper_v2.py)
  - 상태 문구/시장 국면 텍스트 조합 중복 확인
- [kiwoom_websocket.py](../src/engine/kiwoom_websocket.py)
  - 주문상태/실체결 payload 조립 중복 확인

### C. 아직 보류

- [sniper_state_handlers.py](../src/engine/sniper_state_handlers.py)
- [ai_engine.py](../src/engine/ai_engine.py)

보류 이유:

- 현재 성능 튜닝 2단계와 라이브 매매 보정 작업이 겹쳐 있어, 저위험 리팩토링이라도 체감 리스크가 높다.

## 진행 결과 기록

### 2026-04-07 1차 완료: route 입력 정규화 helper 추출

대상:

- [app.py](../src/web/app.py)

반영 내용:

- [app.py](../src/web/app.py#L36) 에 `_today_string()`, `_request_target_date()`, `_request_flag()`, `_request_since()`, `_request_top()` 추가
- route 내부의 `datetime` 중복 import 제거
- `daily-report`, `strength-momentum`, `entry-pipeline-flow`, `gatekeeper-replay`, `performance-tuning`, `strategy-performance`, `trade-review` API/preview 입력 파싱을 helper로 치환

왜 저위험인지:

- query string 파싱만 공통화했고, 각 route가 호출하는 실제 report builder와 response shape는 유지했다.
- threshold, cache, DB, 로그 stage, 화면 문구는 변경하지 않았다.

검증:

- `./.venv/bin/python -m py_compile src/web/app.py` 통과
- `daily-report`, `performance-tuning`, `trade-review` API smoke 확인
- gunicorn 재기동 후 응답 구조 유지 확인 (`2026-04-07 18:37:56 KST` 기준)

### 2026-04-07 2차 완료: snapshot load/build 분기 helper 추출

대상:

- [app.py](../src/web/app.py)

반영 내용:

- [app.py](../src/web/app.py#L99) 에 `_load_or_build_performance_tuning_report()` 추가
- [app.py](../src/web/app.py#L111) 에 `_load_or_build_trade_review_report()` 추가
- `performance-tuning` API/preview의 `snapshot 있으면 사용 / 없으면 build` 분기 중복 제거
- `trade-review` API/preview의 `snapshot 있으면 사용 / 없으면 build` 분기 중복 제거

왜 저위험인지:

- 기존에 있던 `_load_saved_*` helper와 `build_*` 호출 순서를 그대로 감쌌다.
- 내부 report builder 시그니처와 snapshot invalidation 규칙은 그대로 유지했다.

검증:

- `./.venv/bin/python -m py_compile src/web/app.py` 재통과
- `curl`로 `/api/performance-tuning?date=2026-04-07&refresh=1` 확인
- `curl`로 `/api/trade-review?date=2026-04-07&top=1&refresh=1` 확인
- `curl`로 `/api/daily-report?date=2026-04-07` 확인
- `2026-04-07 18:37:56 KST` gunicorn 재기동 후 정상 응답 확인

### 2026-04-07 3차 완료: bot_main 상단 날짜 helper 및 중복 import 정리

대상:

- [bot_main.py](../src/bot_main.py)

반영 내용:

- 중복 `sys` import 제거
- [bot_main.py](../src/bot_main.py) 상단에 `_today_string()`, `_resolve_target_date()` 추가
- `broadcast_today_picks_job()`, `broadcast_entry_metrics_job()`, `generate_monitor_archive_job()` 의 날짜 문자열 생성 중복 축소

왜 저위험인지:

- 부팅/스케줄러 상단에서 쓰는 날짜 문자열 조립만 공통화했다.
- 스케줄 시각, 이벤트 publish, 리포트 생성 로직, 매매 엔진 기동 흐름은 변경하지 않았다.

검증:

- `./.venv/bin/python -m py_compile src/bot_main.py` 통과
- 라이브 봇은 수동 재실행 정책을 유지하므로 자동 재기동은 하지 않음

### 2026-04-07 4차 완료: app.py gatekeeper/trade-review 입력 파싱 helper 정리

대상:

- [app.py](../src/web/app.py)

반영 내용:

- [app.py](../src/web/app.py#L53) 에 `_request_stripped()` 추가
- [app.py](../src/web/app.py#L65) 에 `_request_scope()` 추가
- `gatekeeper-replay` API/preview의 `code`, `time` 파싱을 helper로 치환
- `trade-review` API/preview의 `code`, `scope` 파싱을 helper로 치환

왜 저위험인지:

- query parameter의 `strip/default` 처리만 공통화했다.
- Gatekeeper snapshot 조회, trade-review 빌드, 템플릿/JSON 필드는 그대로 유지했다.

검증:

- `./.venv/bin/python -m py_compile src/web/app.py` 통과
- `curl`로 `/api/gatekeeper-replay?date=2026-04-07` 확인
- `curl`로 `/api/trade-review?date=2026-04-07&top=1&refresh=1` 확인
- `2026-04-07 18:43:41 KST` gunicorn 재기동 후 정상 응답 확인

### 2026-04-07 5차 완료: app.py 공용 unpack helper 정리

대상:

- [app.py](../src/web/app.py)

반영 내용:

- [app.py](../src/web/app.py#L73) 에 `_report_value()`, `_report_dict()`, `_report_list()` 추가
- `strength-momentum`, `entry-pipeline-flow`, `performance-tuning`, `strategy-performance`, `trade-review` preview에서 반복되던 `report.get(... ) or {}` / `or []` 구간을 helper로 치환

왜 저위험인지:

- report 읽기 방식만 공통화했고, builder 호출 순서와 템플릿 변수명은 그대로 유지했다.
- 화면 구조, API 필드, 집계 로직은 변경하지 않았다.

검증:

- `./.venv/bin/python -m py_compile src/web/app.py src/engine/kiwoom_websocket.py` 통과
- `curl`로 `/api/performance-tuning?date=2026-04-07&refresh=1` 확인
- `curl`로 `/api/trade-review?date=2026-04-07&top=1&refresh=1` 확인
- `2026-04-07 18:47:57 KST` gunicorn 재기동 후 정상 응답 확인

### 2026-04-07 6차 완료: kiwoom_websocket 주문/체결 notice 파싱 helper 정리

대상:

- [kiwoom_websocket.py](../src/engine/kiwoom_websocket.py)

반영 내용:

- [kiwoom_websocket.py](../src/engine/kiwoom_websocket.py) 에 `_parse_order_execution_notice()` 추가
- 주문상태/실체결 notice에서 `status`, `code`, `order_no`, `order_type_str`, `exec_price`, `exec_qty`, `exec_type` 조립 중복을 helper로 이동
- 기존 `ORDER_EXECUTED` enqueue 조건과 로그 문구는 그대로 유지

왜 저위험인지:

- 기존 값을 같은 필드로 재조립하는 수준이며, 이벤트 타입/발행 시점/매칭 로직은 건드리지 않았다.
- 기존에 흩어져 있던 숫자 파싱을 이미 존재하던 `_safe_abs_int()` 기반으로 맞춘 수준이다.

검증:

- `./.venv/bin/python -m py_compile src/web/app.py src/engine/kiwoom_websocket.py` 통과
- `./.venv/bin/python -m pytest src/tests/test_kiwoom_websocket.py` 통과 (`3 passed`)
- 웹 서비스는 `2026-04-07 18:47:57 KST` 재기동 상태에서 정상 응답 확인
- 라이브 봇 프로세스는 수동 재실행 정책에 따라 자동 재기동하지 않음

### 2026-04-07 운영 확인: 봇 수동 재실행 반영

확인 내용:

- `2026-04-07 18:49 KST` 기준 `python bot_main.py` 신규 프로세스 확인
- [bot_history.log](../logs/bot_history.log) 기준 부팅 직후 아래 흐름 정상 확인
  - 일일 리포트 생성 완료
  - 텔레그램 수신탑 가동
  - 스나이퍼 엔진 가동
  - 웹소켓 로그인/조건검색식 등록 완료
  - 시장 판독 출력 정상 (`하락장`, `risk=RISK_OFF`)

관찰 메모:

- LightGBM warning은 기존 운영 중에도 보이던 설정 경고로, 이번 저위험 리팩토링과 직접 관련된 신규 오류로 보이지 않음
- `UNKNOWN_CONDITION` 초기 load 로그는 별도 기존 현상으로 보이며, 이번 워크오더 범위의 변경점과 직접 연결되지는 않음

판정:

- 이번 워크오더 범위에서 실제 적용 가능한 저위험 정리 작업은 완료
- 현재 남는 항목은 별도 위험평가 후 다음 라운드에서 다룰 후속 주제이며, "잔여 미완료 작업"으로 보지 않음

## 잔여작업 처리 결과

- [x] [app.py](../src/web/app.py) route 입력 정규화 helper 추출
- [x] [app.py](../src/web/app.py) snapshot load/build 분기 helper 추출
- [x] [app.py](../src/web/app.py) `gatekeeper-replay` / `trade-review` 입력 파싱 helper 추출
- [x] [app.py](../src/web/app.py) preview 공용 unpack helper 정리
- [x] [bot_main.py](../src/bot_main.py) 상단 날짜 helper 및 중복 import 정리
- [x] [kiwoom_websocket.py](../src/engine/kiwoom_websocket.py) 주문/체결 notice payload 조립 helper 정리
- [x] [kiwoom_sniper_v2.py](../src/engine/kiwoom_sniper_v2.py) 사전검토 완료
  - 현재 라운드의 저위험 원칙 기준으로는 즉시 분리 가능한 독립 중복이 부족해, 코드 변경 없이 보류 확정

메모:

- [kiwoom_sniper_v2.py](../src/engine/kiwoom_sniper_v2.py)는 사전 훑어본 결과, 즉시 분리할 만한 중복이 대부분 런타임 초기화/매매 루프에 붙어 있었다.
- 이번 워크오더 범위의 "저위험 실행 가능 항목"은 모두 소화했고, 남는 것은 별도 위험평가가 필요한 후속 라운드로 넘긴다.

## 작업 단위 규칙

각 PR 또는 작업 단위는 아래 중 하나만 처리한다.

1. import 정리만
2. route 입력 정규화 helper 추출만
3. snapshot load/build helper 추출만
4. 화면/API 공용 데이터 준비 정리만

한 작업에서 여러 종류를 동시에 섞지 않는다.

## 리뷰 체크리스트

- [ ] 조건식/threshold 변경 없음
- [ ] API 필드명 변경 없음
- [ ] 로그 stage 이름 변경 없음
- [ ] DB write/read 의미 변경 없음
- [ ] helper 추출 전후 반환값 동일
- [ ] route query 기본값 동일
- [ ] 기존 pytest 통과
- [ ] `py_compile` 통과

## 테스트 원칙

공통:

- `./.venv/bin/python -m py_compile <대상 파일>`

웹 계층 작업 시:

- 관련 route 직접 curl 확인
- 필요 시 `refresh=1` 옵션으로 snapshot 우회 확인

리포트 어댑터 작업 시:

- 해당 리포트 pytest 우선 실행
  - 예: `test_performance_tuning_report.py`
  - 예: `test_daily_report_service.py`
  - 예: `test_entry_pipeline_report.py`

오케스트레이션 작업 시:

- 관련 단위 테스트가 없으면 smoke 수준 로그 확인까지만 하고, 기능 변경으로 넘어가지 않는다.

## 산출물 형태

각 작업 완료 후 남길 내용:

1. 무엇을 정리했는지
2. 왜 저위험이라고 판단했는지
3. 어떤 호출부부터 손댔는지
4. 어떤 내부 함수는 의도적으로 건드리지 않았는지
5. 테스트/검증 결과

## 최종 지시

- 첫 착수는 [app.py](../src/web/app.py)부터 시작한다.
- 그 다음은 `bot_main.py` 또는 `kiwoom_sniper_v2.py` 같은 호출 상단 계층으로 이동한다.
- `sniper_state_handlers.py`, `ai_engine.py`는 이번 저위험 리팩토링 라운드의 직접 대상이 아니다.
- "호출하는 쪽 정리 완료 -> 테스트 통과 -> 그 다음 한 단계 안쪽" 순서를 지킨다.
