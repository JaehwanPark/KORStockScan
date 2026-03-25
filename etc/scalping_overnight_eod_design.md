# SCALPING 15:15 오버나이트 판정 설계 + 패치 가이드

## 목표

`kiwoom_sniper_v2.py`에서 **15:15에 DB 기준으로 무조건 작동하는 독립 로직**을 추가한다.
대상은 다음 조건을 만족하는 종목이다.

- `strategy in ('SCALPING', 'SCALP')`
- `status in ('HOLDING', 'SELL_ORDERED')`
- `rec_date = today`

이 로직은 기존 `handle_holding_state()`의 시간초과/장마감 청산과 **완전히 분리**되어야 하며,
15:15 시점에 AI가 아래 둘 중 하나를 결정한다.

- `SELL_TODAY`: 당일 시장가 매도
- `HOLD_OVERNIGHT`: 오버나이트 유지

---

## 핵심 설계

### 1) 독립 스케줄러

메인 루프 내부에서 `now_t >= TIME_SCALPING_OVERNIGHT_DECISION` 이 되는 순간,
해당 날짜에 아직 실행되지 않았다면 `run_scalping_overnight_gatekeeper(ai_engine)`를 1회 실행한다.

특징:
- 다른 매도 판단 로직과 무관하게 **DB 기준으로 강제 실행**
- 실패 시 60초 후 재시도 가능
- 성공 시 당일 1회만 실행

---

### 2) 시간 변수는 `constants.py` -> `TRADING_RULES`로 이동

하드코딩된 `15:00`, `15:15`, `15:30`, `20:00`을 `TradingConfig`로 이동한다.

추가 필드:
- `SCALPING_NEW_BUY_CUTOFF = "15:00:00"`
- `SCALPING_OVERNIGHT_DECISION_TIME = "15:15:00"`
- `MARKET_CLOSE_TIME = "15:30:00"`
- `SYSTEM_SHUTDOWN_TIME = "20:00:00"`

`kiwoom_sniper_v2.py`는 `_rule_time()` 헬퍼로 파싱해서 사용한다.

---

### 3) 15시 이후 SCALPING 신규 매수 금지

기존 `handle_watching_state()`와 `check_watching_conditions()`는
`TIME_15_30` 이후 제외였는데, 이를 `TIME_SCALPING_NEW_BUY_CUTOFF` 기준으로 변경한다.

즉:
- **15:00 이후 SCALPING 종목은 감시는 가능**
- 하지만 **신규 매수 진입은 금지**

또한 SELL 체결 후 SCALPING 부활(`is_scalp_revive`)도 같은 컷오프로 맞춘다.

---

### 4) 기존 SCALPING 장마감 강제청산 로직 제거

`handle_holding_state()`의 SCALPING 섹션에 있던 아래 로직을 제거한다.

- `SCALP_TIME_LIMIT_MIN` 타임아웃 청산
- `now_t >= TIME_15_30` 장마감 현금화

이제 SCALPING의 종가 판단은 오직 **15:15 독립 AI 판정**이 담당한다.

`check_holding_conditions()`의 관련 안내 문구도 함께 제거한다.

---

### 5) AI 판정은 `ai_engine.py`에 신규 메서드 추가

`generate_realtime_report()`는 유지하고,
별도로 `evaluate_scalping_overnight_decision()`를 추가한다.

이 메서드는:
- `realtime_ctx` dict를 입력받고
- 15:15 전용 프롬프트로
- `SELL_TODAY` / `HOLD_OVERNIGHT` JSON을 반환한다.

기본 원칙:
- 기본값은 `SELL_TODAY`
- 데이터 부족/AI 에러/애매한 응답이면 `SELL_TODAY`
- `HOLD_OVERNIGHT`는 예외적으로만 허용

---

### 6) 기존 `kiwoom_utils.build_realtime_analysis_context()` 재사용

이번 변경에서는 `kiwoom_utils.py`를 수정하지 않는다.

이미 존재하는 `build_realtime_analysis_context(token, stock_code, position_status, ws_data)`를 재사용하고,
`kiwoom_sniper_v2.py`에서 아래 항목만 추가 주입한다.

추가 보강값:
- `avg_price`
- `pnl_pct`
- `held_minutes`
- `order_status_note`
- `strat_label = 'SCALPING_EOD_REVIEW'`

즉 데이터 수집 파이프라인은 그대로 두고,
`15:15용 판단 컨텍스트`만 `kiwoom_sniper_v2.py`에서 완성한다.

---

## 파일별 변경 사항

### `src/utils/constants.py`
- 거래시간 제어용 문자열 상수 추가

### `src/engine/ai_engine.py`
- `SCALPING_OVERNIGHT_DECISION_PROMPT` 추가
- `generate_realtime_report()`가 dict 입력도 안전하게 처리하도록 보강
- `_format_scalping_overnight_context()` 추가
- `evaluate_scalping_overnight_decision()` 추가

### `src/engine/kiwoom_sniper_v2.py`
- `_rule_time()` 추가
- `TIME_SCALPING_NEW_BUY_CUTOFF`, `TIME_SCALPING_OVERNIGHT_DECISION`, `TIME_MARKET_CLOSE` 도입
- 15:00 이후 SCALPING 신규 매수 차단
- `run_scalping_overnight_gatekeeper()` 추가
- `_execute_scalping_sell_today()` 추가
- `_execute_scalping_hold_overnight()` 추가
- 메인 루프에 15:15 독립 실행 구간 삽입
- `handle_holding_state()`의 기존 시간초과/장마감 강제청산 제거

---

## SELL_ORDERED 처리 원칙

### AI가 `SELL_TODAY`를 선택한 경우
- 기존 미체결 매도 주문이 있으면 취소 확인 후
- 잔량을 재조회해서
- **시장가 매도**로 전환

### AI가 `HOLD_OVERNIGHT`를 선택한 경우
- `status == HOLDING`: 그대로 유지
- `status == SELL_ORDERED`: 기존 매도 주문을 취소해야만 진짜 오버나이트 가능
- 원주문번호가 없거나 취소 실패 시, 보수적으로 `SELL_TODAY` 전환 가능

---

## 운영상 주의점

1. 이 설계는 **SCALPING 포지션의 종가 의사결정만 독립화**한다.
2. 장중 익절/손절/AI 모멘텀 로직은 그대로 살아 있다.
3. 15:15 판정은 **오늘 DB에 적재된 상태 기준**으로 작동한다.
4. `SELL_ORDERED`인데 원주문번호가 메모리에 없으면 오버나이트 취소가 완전 보장되지 않을 수 있다.
   이 경우는 로그와 텔레그램 알림으로 추적해야 한다.

---

## 적용 우선순위

1. `constants.py`
2. `ai_engine.py`
3. `kiwoom_sniper_v2.py`

---

## 첨부물 사용 원칙

- `*.patch` = 현재 코드베이스 기준 적용용 변경안
- `*_patched.py` = 최종 형태 참고용 전체 파일
- 이 문서 = 설계 의도와 책임 분리 설명서
