# DeepSeek 작업지시서 — `kiwoom_sniper_condition.py` 분리 리팩토링 (실코드 기준 최종본)

## 작업 목적
현재 `kiwoom_sniper_v2.py` 안에 섞여 있는
- 조건검색식 감시 편입
- WATCHING 상태 매수 판단
- HOLDING 상태 매도 판단
- S15 Fast-Track
- 주문 취소/복구/동기화
를 분리한다.

이번 작업은 **기존 운영 안정성을 최우선**으로 한다.
`kiwoom_sniper_v2.py`는 보존하고, 복제 기반으로 `kiwoom_sniper_condition.py`를 신규 생성한다.

---

## 절대 원칙
1. `kiwoom_utils.py`, `kiwoom_websocket.py`, `kiwoom_orders.py`의 외부 인터페이스는 바꾸지 마라.
2. `ai_engine.py`는 분할하지 마라. 필요한 프롬프트와 래퍼 메서드만 추가해라.
3. diff 형식으로 주지 말고, **패치본 파일 전문 + 변경 요약 markdown**으로 제출해라.
4. 한 번에 크게 바꾸지 말고 단계별로 나눠서 진행해라.
5. 기존 `kiwoom_sniper_v2.py`의 운영 로직은 최대한 유지하고, 책임만 분리해라.

---

## 현재 코드 기준 핵심 사실
- `kiwoom_sniper_v2.py`
  - `handle_condition_matched()`가 조건검색식 편입 + DB 반영 + 일부 S15 즉시 진입까지 처리한다.
  - `handle_watching_state()`가 WATCHING 상태 종목의 매수 판단을 맡는다.
  - `handle_holding_state()`가 HOLDING 상태 종목의 매도 판단을 맡는다.
  - `process_sell_cancellation()`가 미체결 매도 취소 공통 로직이다.
  - `run_sniper()`가 EventBus 구독, WS 시작, AI 초기화, 메인 루프까지 모두 맡는다.
- `kiwoom_websocket.py`
  - `CONDITION_MATCHED`, `CONDITION_UNMATCHED`, `REALTIME_TICK_ARRIVED`, `WS_RECONNECTED` 이벤트를 이미 발행한다.
  - `get_latest_data(code)` 인터페이스가 안정적이므로 그대로 재사용 가능하다.
- `kiwoom_orders.py`
  - `send_buy_order_market()`, `send_sell_order_market()`, `send_cancel_order()`, `get_my_inventory()` 인터페이스 유지 가능하다.
- `db_manager.py`
  - `get_active_targets()`가 `WATCHING`, `BUY_ORDERED`, `SELL_ORDERED`, `HOLDING` 상태를 엔진용 리스트로 반환한다.
- `ai_engine.py`
  - `analyze_target()`와 `evaluate_scalping_overnight_decision()` 중심 구조이므로, 조건검색식 전용 진입/청산 프롬프트만 추가하면 된다.
- `event_bus.py`
  - 싱글톤 구조이며 중복 subscribe 방지는 호출측이 신경 써야 한다.
- `logger.py`
  - 호출 파일명 기준 로그 파일 분리 구조다. 과도한 디버그 로그 증식에 주의해라.

---

## 이번 작업 범위
### 신규 생성
- `kiwoom_sniper_condition.py`

### 수정 대상
- `ai_engine.py`

### 가능하면 이번 단계에서 수정하지 말 것
- `kiwoom_sniper_v2.py`
- `kiwoom_websocket.py`
- `kiwoom_orders.py`
- `kiwoom_utils.py`
- `db_manager.py`
- `models.py`
- `event_bus.py`
- `logger.py`

---

## 목표 구조
`kiwoom_sniper_condition.py` 안에서 아래 책임을 분리해라.

1. 조건검색식 이벤트 수신
2. 감시 대상 등록 / 해제
3. WATCHING 상태 진입 평가
4. HOLDING 상태 청산 평가
5. 주문 실행 래퍼
6. 메인 루프
7. 상태 복구 / 동기화 호출

---

## 필수 상태 분리
하나의 파일 안이라도 내부적으로 아래 상태를 분리해라.

- `watchlist_by_code`: 조건검색식 감시 대상
- `positions_by_code`: 보유 종목 상태
- `pending_orders_by_code`: 미체결 주문 상태
- `condition_profiles`: 조건식 정책 사전

가능하면 딕셔너리 기반으로 먼저 구현하고, 불필요한 클래스 도입은 피하라.

---

## 조건식 정책 사전으로 분리할 것
조건식 이름별로 아래 정보를 매핑하는 정책 사전을 만들어라.

- `role`: `watch_only` / `entry_trigger` / `swing_candidate`
- `family`: `intraday_breakout` / `intraday_rebreak` / `afternoon_second_wave` / `vcp_breakout` / `swing_breakout` / `swing_pullback`
- `entry_policy`
- `exit_policy`
- `start_time`
- `end_time`
- `is_next_day_target`
- `position_tag`

기존 `resolve_condition_profile()`를 참고하되, 새 파일에서는 **조건식 프로파일 레지스트리**로 재구성해라.

---

## S15 관련 처리 원칙
- S15 Fast-Track은 기존 운영 안정성을 위해 당장은 유지해도 된다.
- 단, `handle_condition_matched()` 안에 직접 섞지 말고 `handle_s15_candidate()` / `handle_s15_trigger()` 같은 내부 전용 함수로 분리해라.
- 일반 조건검색식 매수 로직과 S15 Fast-Track을 같은 경로로 태우지 마라.

---

## WATCHING 매수 판단 분리 원칙
기존 `handle_watching_state()` 로직을 새 파일에서 아래처럼 분리해라.

- `should_skip_watching_target(stock, code, ws_data)`
- `evaluate_condition_entry(stock, code, ws_data, radar, ai_engine)`
- `execute_condition_entry(stock, code, decision, ws_data)`

매수 판단은 아래 3단 구조를 유지해라.

1. 하드필터
   - 시간 조건
   - 쿨다운
   - 신규매수 컷오프
   - 현재가/유동성/VI/갭상승 과열
2. 규칙 점수
   - 전략별 체결강도/호가/거래량/위치 조건
3. AI 최종 판단
   - `BUY / WAIT / DROP`

---

## HOLDING 매도 판단 분리 원칙
기존 `handle_holding_state()`를 새 파일에서 아래처럼 분리해라.

- `check_hard_exit(stock, code, ws_data)`
- `evaluate_condition_exit(stock, code, ws_data, market_regime, ai_engine)`
- `execute_condition_exit(stock, code, exit_plan)`

매도는 아래 원칙을 따라라.

1. **하드 손절/강제 청산**은 AI 없이 즉시 실행
2. **익절/부분청산/보유 지속**만 AI가 관여
3. `process_sell_cancellation()` 성격의 공통 로직은 재사용 가능한 보조 함수로 분리

---

## `ai_engine.py` 수정 원칙
파일 분할은 금지한다.
아래만 추가해라.

### 1. 프롬프트 추가
- 조건검색식 진입 판단 프롬프트
- 조건검색식 청산 판단 프롬프트

### 2. 래퍼 메서드 추가
- `evaluate_condition_entry(...)`
- `evaluate_condition_exit(...)`

### 3. 출력 형식
반드시 JSON으로 제한해라.

진입:
```json
{
  "decision": "BUY|WAIT|SKIP",
  "confidence": 0,
  "order_type": "MARKET|LIMIT_TOP|NONE",
  "position_size_ratio": 0.0,
  "invalidation_price": 0,
  "reasons": [""],
  "risks": [""]
}
```

청산:
```json
{
  "decision": "HOLD|TRIM|EXIT",
  "confidence": 0,
  "trim_ratio": 0.0,
  "new_stop_price": 0,
  "reason_primary": "",
  "warning": ""
}
```

---

## EventBus 사용 원칙
`event_bus.py`는 싱글톤이며 중복 subscribe 방지가 자동이 아니다.
따라서 새 엔진 파일에서도 구독 등록 시 아래 원칙을 따라라.

- 함수 속성 플래그 또는 인스턴스 플래그로 **1회만 subscribe** 하게 해라.
- `CONDITION_MATCHED`, `CONDITION_UNMATCHED`, `WS_RECONNECTED`, `ORDER_EXECUTED`만 우선 구독해라.
- 무거운 로직은 EventBus 콜백 안에서 직접 처리하지 말고 내부 함수/스레드로 넘겨라.

---

## logger 사용 원칙
`logger.py`는 호출 파일명 기준 로그 파일을 쓴다.
새 파일에서는 디버그 로그를 남발하지 마라.

원칙:
- 상태 전이 로그만 남겨라.
- 틱 단위 반복 로그는 최소화해라.
- 예외 로그는 `log_error()`로 통일해라.
- 정상 흐름은 꼭 필요한 지점만 `log_info()`를 써라.

---

## `kiwoom_utils.py` 관련 주의사항
유틸 함수는 이미 충분히 많고 외부 API 규격이 맞춰져 있다. 바꾸지 마라.
특히 아래는 그대로 써라.

- `get_tick_history_ka10003()`
- `get_minute_candles_ka10080()`
- `get_basic_info_ka10001()`
- `get_program_flow_realtime()`
- `get_investor_flow_summary_ka10059()`
- `get_target_price_up()`
- `get_target_price_by_percent()`
- `get_tick_size()`

새 엔진은 유틸 함수 호출 순서와 조합만 바꿔라.

---

## 제출 형식
각 단계마다 아래 2개만 제출해라.

1. **패치본 전체 파일 전문**
   - 예: `kiwoom_sniper_condition.py` 전체
   - 예: 수정된 `ai_engine.py` 전체
2. **짧은 markdown 변경 요약**
   - 변경 파일
   - 핵심 변경점
   - 주의사항
   - 아직 안 건드린 것

diff 금지.

---

# 단계별 작업 지시

## STEP 1
### 작업
`kiwoom_sniper_v2.py`를 복제해 `kiwoom_sniper_condition.py`를 생성하라.

### 목표
아직 동작 변경은 최소화하고, 아래 4개 진입점만 명확히 보이게 정리하라.
- `handle_condition_matched()`
- `handle_condition_unmatched()`
- `handle_watching_state()`
- `handle_holding_state()`

### 지시
기존 동작을 깨지 말고, 함수/섹션 주석 구조만 먼저 재배치해라.

---

## STEP 2
### 작업
조건검색식 프로파일 레지스트리를 도입하라.

### 목표
기존 `resolve_condition_profile()` 의 if/elif 사슬을 정책 사전으로 교체하라.

### 지시
- 조건식명 → 정책 딕셔너리 구조로 바꿔라.
- `s15_*`, `scalp_*`, `kospi_*`, `vcp_*`를 모두 포함해라.
- 동작은 바꾸지 말고 참조 구조만 바꿔라.

---

## STEP 3
### 작업
WATCHING 매수 로직을 분리하라.

### 목표
`handle_watching_state()`를 아래 내부 함수들로 쪼개라.
- `should_skip_watching_target()`
- `build_entry_context()`
- `evaluate_condition_entry()`
- `execute_condition_entry()`

### 지시
- 기존 매수 조건을 유지해라.
- 주문 모듈 인터페이스는 바꾸지 마라.
- S15 Fast-Track은 별도 경로로 남겨라.

---

## STEP 4
### 작업
HOLDING 매도 로직을 분리하라.

### 목표
`handle_holding_state()`를 아래 내부 함수들로 쪼개라.
- `check_hard_exit()`
- `build_exit_context()`
- `evaluate_condition_exit()`
- `execute_condition_exit()`
- `cancel_existing_sell_if_needed()`

### 지시
- 손절/강제청산은 규칙 기반으로 먼저 처리해라.
- AI는 익절/보유 지속 판단에만 쓰도록 분리해라.

---

## STEP 5
### 작업
`ai_engine.py`에 조건검색식 전용 프롬프트와 래퍼를 추가하라.

### 목표
기존 `analyze_target()`는 유지하고, 새 메서드를 추가해라.

### 지시
- `evaluate_condition_entry()` 추가
- `evaluate_condition_exit()` 추가
- JSON 출력 강제
- 설명문은 짧고 단호하게 유지

---

## STEP 6
### 작업
`run_sniper()`를 참고해 `run_condition_sniper()` 엔트리 함수를 만들고, 새 파일에서만 구독/초기화가 가능하게 하라.

### 목표
`kiwoom_sniper_v2.py`는 건드리지 않고도 새 엔진을 독립 실행할 수 있게 만들어라.

### 지시
- EventBus 구독 중복 방지
- `WS_RECONNECTED` 시 복구 루틴 연결
- `DB.get_active_targets()` 재사용
- `WS_MANAGER.get_latest_data()` 재사용

---

# 병합 검토 지침
이번 단계에서 `final_ensemble_scanner.py`와 `scalping_scanner.py`를 `sniper_v2`에 병합하지 마라.

이유:
- `final_ensemble_scanner.py`는 배치/장마감/장전 추천 엔진이다.
- `scalping_scanner.py`는 전방 탐색조 성격이다.
- 이번 작업의 핵심은 조건검색식 기반 감시/매수/매도 상태 머신 분리다.

추후 병합은 아래 조건을 만족할 때만 검토해라.
- 추천 코드가 주문/체결/잔고를 직접 건드리지 않을 것
- 출력이 `code`, `strategy_id`, `score`, `reason` 수준일 것
- 공통 신호 소스 인터페이스로 흡수 가능할 것

이번 단계에서는 병합 금지. 신호 소스 통합은 후속 작업으로 남겨라.

---

# 최종 한 줄 지시
기존 운영 안정성을 해치지 않는 범위에서, `kiwoom_sniper_v2.py`를 보존한 채 `kiwoom_sniper_condition.py`를 신규 생성하고, 조건검색식 감시/매수/매도 책임을 단계적으로 분리하라. 제출은 항상 **패치본 전체 파일 + 짧은 markdown 요약**만 해라.
