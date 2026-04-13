# 스캘핑 전문가 제안 중 현 단계 부적합 항목 메모

## 목적

- 전문가 의견 자체를 부정하는 문서가 아니다.
- 다만 전문가들이 코드베이스와 현재 운영 제약을 모두 알지는 못하므로, `지금 바로 적용하면 안 되는 제안`과 그 이유를 분리해 둔다.

## 1. 신규 텔레그램 연동이 최우선이라는 제안

- 제안 요지:
  - `latency_block`를 텔레그램으로 실시간 발송하자.
- 현재 코드베이스 상황:
  - `TELEGRAM_BROADCAST`, `TELEGRAM_ADMIN_NOTIFY`, `buy_pause_guard`, `entry_metrics`가 이미 존재한다.
  - 관리자 전용 알림 경로도 이미 운영 중이다.
- 왜 지금 안 맞는가:
  - 현재 부족한 것은 `알림 채널`이 아니라 `latency_block의 세부 판정근거`와 `partial fill mismatch` 같은 구조화 데이터다.
  - 새 알림을 먼저 늘리면 잡음만 커질 수 있다.
- 대체 처리:
  - 새 텔레그램 기능 개발은 보류
  - 먼저 `ENTRY_PIPELINE/HOLDING_PIPELINE` 계측을 강화한다

## 2. latency 원인을 내부 처리 지연 또는 인프라 문제로 단정하는 제안

- 제안 요지:
  - async 이벤트 루프, EC2 리소스, 프로세스 분리 이슈일 가능성이 높다.
- 현재 코드베이스 상황:
  - 현재 로그는 `latency symptom`은 보여주지만 `root cause`를 고정할 만큼 상세하지 않다.
  - `quote_stale=False` 표본이 있는 것은 사실이지만, 그것만으로 곧바로 내부 처리 지연으로 단정할 수는 없다.
- 왜 지금 안 맞는가:
  - 원인 확정 전에 인프라 리팩터링부터 들어가면 다축 변경이 된다.
  - 현재 운영 원칙인 `한 번에 한 축 canary`에 어긋난다.
- 대체 처리:
  - 먼저 `ws_age/ws_jitter/spread/slippage/decision reason` 분포를 남긴다
  - 그 결과로 내부 처리 지연 가설이 강해질 때만 원격에서 별도 실험

## 3. fallback 주문을 즉시 FOK로 바꾸자는 제안

- 제안 요지:
  - partial fill이 싫으니 FOK 또는 즉시 취소 규칙을 강하게 적용하자.
- 현재 코드베이스 상황:
  - 현재 fallback은 `fallback_scout=IOC`, `fallback_main=DAY` 번들 구조다.
  - partial/full fill 누적 처리와 preset TP 재발행 로직이 이미 존재한다.
- 왜 지금 안 맞는가:
  - FOK로 즉시 전환하면 partial fill은 줄겠지만, 동시에 진입 기회도 크게 줄 수 있다.
  - 지금은 `partial fill 자체`가 문제인지, `partial fill 후 sync mismatch`가 문제인지 아직 분리되지 않았다.
- 대체 처리:
  - `preset_exit_sync_mismatch`부터 계측
  - 이후 필요하면 원격에서 `min_fill_ratio` 또는 `cancel_remaining_fast` 형태로만 단일축 canary

## 4. hard time stop이 live에서 AI를 구조적으로 무력화하므로 즉시 수정해야 한다는 제안

- 제안 요지:
  - hard time stop이 AI 보유 판단을 덮어쓰는 구조일 수 있다.
- 현재 코드베이스 상황:
  - `SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY=True`
  - common hard time stop은 현재 `shadow-only`다.
  - 다만 이 메모는 `즉시 수정` 제안만 보류하는 문서이며, 별도로 `scalp_preset_hard_stop_pct / protect_hard_stop / scalp_hard_stop_pct` 같은 live stop taxonomy audit 필요성까지 부정하는 것은 아니다.
- 왜 지금 안 맞는가:
  - live exit 충돌을 전제로 한 즉시 수정 과제는 현재 상태와 맞지 않는다.
  - 지금은 `영향 관측`이 맞고 `실전 변경`은 아직 아니다.
- 대체 처리:
  - `exit_decision_source` 로깅만 추가
  - `hard_time_stop_shadow`와 post-sell 결과를 비교해 장후 평가용으로만 축적

## 5. AI raw edge가 이미 충분히 검증됐으니 필터를 빨리 걷어내자는 제안

- 제안 요지:
  - missed winner가 높으니 AI를 더 믿고 필터를 제거하자.
- 현재 코드베이스 상황:
  - OpenAI 실시간 입력에는 이미 `latest_strength`, `buy_pressure_10t`, `distance_from_day_high_pct`, `intraday_range_pct`가 포함된다.
  - 그러나 `dynamic strength`, `momentum_tag`, `threshold_profile`, `overbought`와 완전히 같은 판단인지 아직 증명되지 않았다.
- 왜 지금 안 맞는가:
  - AI가 이미 본 것을 다시 막는 `이중 검열`일 수도 있지만, 아직 감사 전이다.
  - 바로 필터를 제거하면 원인 식별력이 떨어진다.
- 대체 처리:
  - `AI overlap audit` 먼저
  - 감사 결과가 확인되면 원격 selective cohort에서만 완화

## 6. AI 재학습·drift 대응을 바로 붙이자는 제안

- 제안 요지:
  - 피드백 루프와 drift monitoring을 우선 구축하자.
- 현재 코드베이스 상황:
  - 현재 최상위 병목은 `latency`와 `진입 전 차단`이다.
  - 거래 표본도 아직 많지 않다.
- 왜 지금 안 맞는가:
  - 현 단계에서 재학습 파이프라인을 먼저 건드리면 범위가 너무 커진다.
  - 현재 의사결정에 필요한 것은 모델 변경보다 `실매매 퍼널 회복`이다.
- 대체 처리:
  - 당장은 `ai_confirmed score vs realized return` 모니터링만 추가
  - 재학습/드리프트는 중기 과제로 보류

## 최종 정리

- 부적합 제안의 공통점은 `문제 축은 맞을 수 있지만, 현재 코드베이스/운영 단계에서는 너무 이르거나 이미 일부 구현돼 있는 것`이다.
- 따라서 이번 세션의 원칙은 아래로 고정한다.
  1. `계측 먼저`
  2. `원격 단일축 실험`
  3. `본서버 후행 반영`
