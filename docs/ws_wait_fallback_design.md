# 웹소켓 첫 수신 대기 후 REST 폴백 설계안

## 목표
- `COMMAND_WS_REG` 직후 곧바로 REST 폴백으로 내려가는 현상을 방지한다.
- `REG 전송 완료`와 `첫 실시간 데이터 수신`을 구분한다.
- `0D(호가)`/`0w(프로그램)`가 먼저 들어오고 `0B(체결)`가 늦는 상황을 정상으로 처리한다.
- 충분히 기다린 뒤에도 체결가가 없을 때만 `ka10003` REST 폴백을 실행한다.

## 현재 문제
1. `kiwoom_websocket.py::_send_reg()`의 로그가 등록 패킷 전송 완료인데도 `데이터 수신 시작`처럼 보인다.
2. `kiwoom_sniper_v2.py::analyze_stock_now()`는 `curr > 0`만 성공으로 간주한다.
3. 호가/프로그램이 이미 들어와도 체결이 늦으면 즉시 실패처럼 취급되어 REST 폴백이 발생한다.

## 핵심 개선

### 1) KiwoomWSManager에 첫 수신 판정 상태 추가
종목별 `realtime_data`에 아래 메타를 유지한다.
- `received_types: set()`
- `last_ws_update_ts: float`
- `_first_tick_logged: bool`

각 `REAL` 수신 시:
- `received_types.add(real_type)`
- `last_ws_update_ts = time.time()`
- 최초 유효 수신 시 `✅ [WS] 첫 실시간 데이터 수신 확인` 로그 출력

### 2) wait_for_data() 헬퍼 추가
`wait_for_data(code, timeout, require_trade)`를 추가한다.
- `require_trade=False`: `0D/0w/0B` 중 아무 WS 데이터나 오면 성공
- `require_trade=True`: `curr > 0` 또는 `0B` 수신까지 기다림

### 3) analyze_stock_now()의 대기 단계를 2단계로 분리
1차 대기:
- `require_trade=False`, 1.5초
- 호가/프로그램이라도 들어오면 WS가 살아있다고 판단

2차 대기:
- `require_trade=True`, 1.5초
- 체결가까지 조금 더 기다림

그래도 체결 데이터가 없을 때만 REST `ka10003` 폴백 실행

## 로그 정책
기존:
- `📡 [WS] 종목 등록 완료 및 데이터 수신 시작`

변경:
- `📡 [WS] 종목 등록 패킷 전송 완료`
- 실제 첫 수신 때만 `✅ [WS] 첫 실시간 데이터 수신 확인: 005930 / types=['0D']`

## 기대 효과
- REG 직후 즉시 폴백 감소
- 0D/0w 선행 수신을 정상 처리
- 체결이 늦더라도 짧은 warm-up 동안 WS를 우선 신뢰
- REST 호출 횟수 감소

## 적용 파일
- `kiwoom_websocket.py`
  - `wait_for_data()` 추가
  - `realtime_data` 메타 확장
  - 첫 수신 로그 추가
  - `_send_reg()` 로그 수정
- `kiwoom_sniper_v2.py`
  - `analyze_stock_now()` 대기 로직 교체
  - REST 폴백 전에 2단계 WS 대기 적용
  - 폴백 시 WS의 호가/프로그램 데이터를 최대한 보존
