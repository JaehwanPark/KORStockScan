# OpenAI WS Stability Report - 2026-06-01

- generated_at: `2026-06-01T22:27:54+09:00`
- decision: `keep_ws`
- unique WS calls: `6203`
- endpoint counts: `{'analyze_target': 6203}`
- WS fallback: `0` / `6203` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{'TimeoutError': 1}`
- WS transport warning: `{'ws_error_count': 1, 'ws_error_rate': 0.0002, 'warning_only': True, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 6203, 'avg': 1212.9, 'median': 1089.0, 'p75': 1284.0, 'p90': 1613.0, 'p95': 1927.6, 'max': 15132.0}`
- WS roundtrip ms: `{'n': 6203, 'avg': 1082.2, 'median': 932.0, 'p75': 1101.0, 'p90': 1481.0, 'p95': 1767.9, 'max': 7897.0}`
- WS queue wait ms: `{'n': 6203, 'avg': 0.5, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 4.0, 'max': 58.0}`
- <=3s rate: `0.9881`
- HTTP late baseline AI response ms: `{'n': 10, 'avg': 2089.6, 'median': 1588.0, 'p75': 2937.8, 'p90': 3378.5, 'p95': 3565.2, 'max': 3752.0}`
- baseline median improvement: `0.3142`
- baseline p75 improvement: `0.5629`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 517, 'applied_count': 290, 'transport_observable_count': 514, 'applied_transport_observable_count': 290, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 290, 'avg': 741.5, 'median': 734.0, 'p75': 768.0, 'p90': 795.0, 'p95': 831.5, 'max': 1097.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
