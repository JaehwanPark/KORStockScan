# 실시간 프로그램 수급 0w 전환 통합 설계

## 결론

현재 기준 `kiwoom_websocket.py`는 **`0w`를 이미 구독하고 있습니다.**

- REG 등록: `0B`, `0D`, `0w` 모두 등록
- 수신 파싱: `real_type == '0w'` 분기 존재
- 저장 필드: `prog_net_qty`, `prog_delta_qty`, `prog_net_amt`, `prog_delta_amt`

즉 **문제는 “0w가 빠져 있다”가 아니라, 소비 계층이 아직 `check_program_buying_ka90008()`를 실시간 source of truth처럼 사용한다는 점**입니다.

## 현재 구조 진단

### 1) `kiwoom_websocket.py`
- `_send_reg()`에 `0w` 포함
- `real_type == '0w'` 파싱 존재
- 다만 현재 구현은 `safe_int()`가 `-`를 제거하므로 **프로그램 순매수/순매도 부호가 깨질 수 있음**
- `0w` 수신 메타(`received_types`, `program_history`, `last_prog_update_ts`)가 없어 downstream 판단이 약함

### 2) `kiwoom_utils.py`
- `check_program_buying_ka90008()`가 `date=today` 고정
- 장중에는 API가 0 스냅샷만 줄 수 있어 **모든 값이 0으로 떨어질 수 있음**
- 따라서 이 함수는 실시간용이 아니라 **전일 마감 스냅샷 / fallback 용도**로 격하하는 것이 맞음

### 3) `kiwoom_sniper_v2.py`
- `analyze_stock_now()`에서 프로그램 수급을 아직 `check_program_buying_ka90008()`로 조회
- WATCHING 상태 AI 호출부도 `program_net_qty`를 `check_program_buying_ka90008()`에서 주입
- 즉 실시간 분석이 **WS보다 REST snapshot을 더 신뢰하는 구조**가 남아 있음

## 목표 구조

### Source of Truth 우선순위
1. **WS `0w`**
2. `ka90008` 직전 영업일 스냅샷
3. 0 기본값

## 수정 방향

### A. `kiwoom_websocket.py`
- `0w`는 이미 포함되어 있으므로 제거/신규 추가 필요 없음
- 대신 아래 보강
  - `0w` 파싱 시 `safe_int()` 대신 `_safe_signed_int()` 사용
  - `received_types` 추가
  - `last_prog_update_ts` 추가
  - `program_history` 추가
- 등록 로그는 “수신 시작”이 아니라 “패킷 전송 완료(실수신 대기)”로 수정

### B. `kiwoom_utils.py`
- `_get_prev_business_day_str()` 추가
- `check_program_buying_ka90008()`는 기본 조회일을 **직전 영업일**로 변경
- `today` 명시 조회 + 올제로 결과 시 직전 영업일로 1회 재시도
- 새 helper `get_program_flow_realtime(token, code, ws_data=None)` 추가
  - `0w`가 있으면 WS 값 반환
  - 없으면 `ka90008` 직전 영업일 snapshot 반환

### C. `kiwoom_sniper_v2.py`
- `analyze_stock_now()` 프로그램 수급을 `get_program_flow_realtime()`로 전환
- WATCHING 상태 AI 주입용 `program_net_qty`도 동일 helper 사용
- 표시 문구도 `순매수/증감`으로 확장

## 운영상 의미

- 실시간 분석에서 프로그램 수급이 더 이상 장중 0으로 굳지 않음
- `0w`가 있으면 AI/리포트/게이트 판단이 WS 기준으로 바로 반응
- `0w`가 없더라도 `ka90008` 전일 snapshot으로 최소한의 수급 맥락은 유지
- 부호가 유지되므로 순매수/순매도 방향성이 보존됨

## 패치 범위

### 수정 대상
- `kiwoom_websocket.py`
- `kiwoom_utils.py`
- `kiwoom_sniper_v2.py`

### 비수정
- `ai_engine.py`
- 주문 실행 로직
- DB 스키마

## 적용 우선순위

1. `kiwoom_websocket_program0w.patch`
2. `kiwoom_utils_program0w.patch`
3. `kiwoom_sniper_v2_program0w.patch`

## 검토 포인트

- 다른 모듈이 `prog_net_qty`를 **양수 전용**으로 가정하는지
- `REALTIME_TICK_ARRIVED` 소비자가 `received_types` / `program_history` 추가를 문제 없이 무시하는지
- 장중 `ka90008(today)` 직접 호출이 다른 곳에 남아 있는지
