# OpenAI WS Stability Report - 2026-05-21

- generated_at: `2026-05-21T17:31:44+09:00`
- decision: `keep_ws`
- unique WS calls: `4278`
- endpoint counts: `{'analyze_target': 4092, 'entry_price': 186}`
- WS fallback: `0` / `4278` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{'TimeoutError': 2}`
- WS transport warning: `{'ws_error_count': 2, 'ws_error_rate': 0.0005, 'warning_only': True, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 4092, 'avg': 1140.5, 'median': 999.0, 'p75': 1225.0, 'p90': 1592.0, 'p95': 1915.4, 'max': 15092.0}`
- WS roundtrip ms: `{'n': 4278, 'avg': 1084.1, 'median': 952.0, 'p75': 1170.8, 'p90': 1542.0, 'p95': 1850.8, 'max': 6664.0}`
- WS queue wait ms: `{'n': 4278, 'avg': 0.3, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 1.0, 'max': 73.0}`
- <=3s rate: `0.9883`
- HTTP late baseline AI response ms: `{'n': 4, 'avg': 1458.8, 'median': 1331.0, 'p75': 1577.5, 'p90': 2012.2, 'p95': 2157.1, 'max': 2302.0}`
- baseline median improvement: `0.2494`
- baseline p75 improvement: `0.2235`
- entry_price WS sample count: `186`
- entry_price canary summary: `{'canary_event_count': 188, 'applied_count': 18, 'transport_observable_count': 187, 'applied_transport_observable_count': 18, 'ws_observable_unique_count': 186, 'applied_ai_eval_ms': {'n': 18, 'avg': 1257.8, 'median': 1002.5, 'p75': 1372.0, 'p90': 1910.7, 'p95': 2462.6, 'max': 2738.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price` WS transport 표본이 관찰됐다.
- 장중/장후 표본에서 fallback/fail-closed/latency guard를 계속 분리 확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
