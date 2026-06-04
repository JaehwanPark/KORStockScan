# OpenAI WS Stability Report - 2026-06-04

- generated_at: `2026-06-04T17:53:35+09:00`
- decision: `keep_analyze_target_only`
- unique WS calls: `567`
- endpoint counts: `{'analyze_target': 567}`
- WS fallback: `0` / `567` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- WS transport warning: `{'ws_error_count': 0, 'ws_error_rate': 0.0, 'warning_only': False, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 567, 'avg': 1255.5, 'median': 1053.0, 'p75': 1314.5, 'p90': 1637.0, 'p95': 2021.8, 'max': 7109.0}`
- WS roundtrip ms: `{'n': 567, 'avg': 1214.3, 'median': 1008.0, 'p75': 1270.5, 'p90': 1588.2, 'p95': 2004.3, 'max': 6988.0}`
- WS queue wait ms: `{'n': 567, 'avg': 1.1, 'median': 0.0, 'p75': 1.0, 'p90': 3.0, 'p95': 6.0, 'max': 85.0}`
- <=3s rate: `0.9788`
- HTTP late baseline AI response ms: `{'n': 0, 'avg': None, 'median': None, 'p75': None, 'p90': None, 'p95': None, 'max': None}`
- baseline median improvement: `None`
- baseline p75 improvement: `None`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 18, 'applied_count': 10, 'transport_observable_count': 18, 'applied_transport_observable_count': 10, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 10, 'avg': 737.1, 'median': 726.5, 'p75': 767.8, 'p90': 789.9, 'p95': 798.5, 'max': 807.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
