# OpenAI WS Stability Report - 2026-05-18

- generated_at: `2026-05-18T16:18:23+09:00`
- decision: `keep_ws`
- unique WS calls: `799`
- endpoint counts: `{'analyze_target': 797, 'entry_price': 2}`
- WS fallback: `0` / `799` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- WS transport warning: `{'ws_error_count': 0, 'ws_error_rate': 0.0, 'warning_only': False, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 797, 'avg': 1367.2, 'median': 1264.0, 'p75': 1527.0, 'p90': 1964.8, 'p95': 2362.2, 'max': 4791.0}`
- WS roundtrip ms: `{'n': 799, 'avg': 1331.5, 'median': 1222.0, 'p75': 1495.0, 'p90': 1912.6, 'p95': 2317.9, 'max': 4699.0}`
- WS queue wait ms: `{'n': 799, 'avg': 0.5, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 1.0, 'max': 64.0}`
- <=3s rate: `0.9787`
- HTTP late baseline AI response ms: `{'n': 9, 'avg': 3620.1, 'median': 2555.0, 'p75': 3409.0, 'p90': 6989.6, 'p95': 7334.8, 'max': 7680.0}`
- baseline median improvement: `0.5053`
- baseline p75 improvement: `0.5521`
- entry_price WS sample count: `2`
- entry_price canary summary: `{'canary_event_count': 2, 'applied_count': 2, 'transport_observable_count': 2, 'applied_transport_observable_count': 2, 'ws_observable_unique_count': 2, 'applied_ai_eval_ms': {'n': 2, 'avg': 1046.5, 'median': 1046.5, 'p75': 1049.8, 'p90': 1051.7, 'p95': 1052.3, 'max': 1053.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price` WS transport 표본이 관찰됐다.
- 장중/장후 표본에서 fallback/fail-closed/latency guard를 계속 분리 확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
