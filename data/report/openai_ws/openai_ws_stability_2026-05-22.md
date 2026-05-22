# OpenAI WS Stability Report - 2026-05-22

- generated_at: `2026-05-22T16:55:56+09:00`
- decision: `keep_ws`
- unique WS calls: `3715`
- endpoint counts: `{'analyze_target': 3581, 'entry_price': 134}`
- WS fallback: `0` / `3715` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- WS transport warning: `{'ws_error_count': 0, 'ws_error_rate': 0.0, 'warning_only': False, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 3581, 'avg': 1191.6, 'median': 1034.0, 'p75': 1295.0, 'p90': 1667.0, 'p95': 2255.0, 'max': 6954.0}`
- WS roundtrip ms: `{'n': 3715, 'avg': 1136.5, 'median': 984.0, 'p75': 1220.0, 'p90': 1593.6, 'p95': 2201.0, 'max': 6858.0}`
- WS queue wait ms: `{'n': 3715, 'avg': 0.2, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 0.0, 'max': 116.0}`
- <=3s rate: `0.9827`
- HTTP late baseline AI response ms: `{'n': 10, 'avg': 2163.8, 'median': 2208.0, 'p75': 2687.5, 'p90': 2872.9, 'p95': 2903.9, 'max': 2935.0}`
- baseline median improvement: `0.5317`
- baseline p75 improvement: `0.5181`
- entry_price WS sample count: `134`
- entry_price canary summary: `{'canary_event_count': 134, 'applied_count': 12, 'transport_observable_count': 134, 'applied_transport_observable_count': 12, 'ws_observable_unique_count': 134, 'applied_ai_eval_ms': {'n': 12, 'avg': 1269.6, 'median': 1088.5, 'p75': 1295.5, 'p90': 1321.3, 'p95': 2214.3, 'max': 3305.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price` WS transport 표본이 관찰됐다.
- 장중/장후 표본에서 fallback/fail-closed/latency guard를 계속 분리 확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
