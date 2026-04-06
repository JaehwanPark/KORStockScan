# 2026-04-07 Performance Tuning Checklist

## 목적
- 장중에 `Gatekeeper`, `보유 AI`, `WS 지연/지터` 상태를 빠르게 확인한다.
- `성능 튜닝 모니터`에 보이는 `0` 값이 표본 부재인지 실제 문제인지 구분한다.
- 2단계 최적화 착수 여부를 판단할 근거를 모은다.

## 빠른 링크
- 성능 튜닝 모니터
  - `https://korstockscan.ddns.net/dashboard?tab=performance-tuning&date=2026-04-07&since=09:00:00`
- 실제 매매 복기
  - `https://korstockscan.ddns.net/dashboard?tab=trade-review&date=2026-04-07`
- 전략 성과 분석
  - `https://korstockscan.ddns.net/dashboard?tab=strategy-performance&date=2026-04-07`

## 먼저 기억할 점
- 통합 대시보드 기본 조회 범위는 `최근 120분`이다.
- 장마감 무렵 기본 화면에서 `holding_reviews=0`, `holding_skips=0`, `exit_signals=0`처럼 보일 수 있다.
- 따라서 내일은 반드시 `since=09:00:00` 또는 원하는 시작 시각을 명시해서 본다.

## 1. 장 초반 체크
- 시간대: `09:00~10:30`
- 성능 튜닝 모니터를 `since=09:00:00`으로 열기
- 아래 4개를 먼저 기록
  - `Gatekeeper p95`
  - `Gatekeeper fast reuse ratio`
  - `Gatekeeper AI cache hit ratio`
  - `holding skip ratio`

## 2. Gatekeeper 최우선 확인
- `Gatekeeper fast reuse ratio`가 여전히 `0.0%`인지 확인
- `Gatekeeper AI cache hit ratio`가 여전히 `0.0%`인지 확인
- `Gatekeeper eval p95`가 `20초+`인지 확인
- `top_gatekeeper_slow`에 `30초 이상` 사례가 반복되는지 확인
- `gatekeeper_reuse_blockers` 상위가 여전히 아래 순서인지 확인
  - `시그니처 변경`
  - `재사용 창 만료`
  - `이전 액션 없음`
  - `이전 허용값 없음`

## 3. Gatekeeper 시그니처 변화 확인
- `gatekeeper_sig_deltas` 상위 필드 확인
- 아래 필드가 반복적으로 상위인지 체크
  - `curr_price`
  - `spread_tick`
  - `v_pw_now`
  - `score`
  - `buy_ratio_ws`
- 특정 필드가 하루 내내 과도하게 반복되면 2단계 조정 후보로 메모

## 4. 보유 AI 확인
- 실제 보유 종목이 생겼을 때만 `holding_reviews`, `holding_skips`를 해석
- 보유 종목이 있는데도 아래가 유지되는지 확인
  - `holding_skips = 0`
  - `holding AI cache hit = 0.0%`
- `ai_holding_skip_unchanged`가 최소 몇 건이라도 발생하는지 확인
- `holding_reuse_blockers` 상위가 여전히 아래인지 체크
  - `시그니처 변경`
  - `AI 손절 경계`
  - `재사용 창 만료`
  - `저점수 경계`

## 5. WS 지연/지터 확인
- `LATENCY_ENTRY_BLOCK`에서 `ws_age_ms`는 정상인데 `ws_jitter_ms`만 비정상적으로 큰 사례가 다시 나오는지 확인
- 오늘 반영한 jitter reset fallback 이후에도 `수만~수십만 ms` 지터가 재발하는지 확인
- `quote_stale=True` 빈도와 `spread_ratio` 과다 차단을 같이 체크

## 6. 스프레드 차단 사례 확인
- `latency_block` 중 `spread_ratio > 0.005`로 차단된 사례 수집
- 특히 아래 패턴을 별도로 메모
  - `ws_age_ms` 정상
  - `ws_jitter_ms` 정상
  - `spread_ratio`만 높아 `DANGER`
- 복기 화면에서는 `호가스프레드`가 `%`로 보이는지 확인

## 7. 복기/성과 집계 품질 확인
- `trade-review` 종료 거래 수와 실제 체결 로그가 계속 일치하는지 확인
- `performance-tuning`의 `exit_rules` 집계가 실제 종료 거래 대비 지나치게 적은지 확인
- `strategy-performance`와 `trade-review` 수치가 계속 맞는지 확인

## 8. 0 값 해석 기준
- 아래는 표본 부재 0일 수 있음
  - `holding_reviews`
  - `holding_skips`
  - `exit_signals`
  - 관련 breakdown 비어 있음
- 아래는 실제 문제 0일 가능성이 큼
  - `holding_ai_cache_hit_ratio = 0.0%`
  - `gatekeeper_fast_reuse_ratio = 0.0%`
  - `gatekeeper_ai_cache_hit_ratio = 0.0%`

## 9. 장 종료 후 정리
- `performance-tuning?date=2026-04-07&since=09:00:00` 기준으로 수치 캡처 또는 메모 남기기
- 전일 대비 아래 4개 비교
  - `Gatekeeper p95`
  - `Gatekeeper fast reuse ratio`
  - `Gatekeeper AI cache hit ratio`
  - `holding skip ratio`

## 10. 2단계 착수 조건
- 아래 중 2개 이상이면 2단계 최적화 바로 검토
  - `Gatekeeper fast reuse 0.0%` 지속
  - `Gatekeeper AI cache hit 0.0%` 지속
  - `Gatekeeper p95`가 계속 `20초+`
  - `gatekeeper_sig_deltas` 상위 필드가 거의 동일하게 반복
  - 보유 종목이 있는데 `holding skip`이 사실상 발생하지 않음
