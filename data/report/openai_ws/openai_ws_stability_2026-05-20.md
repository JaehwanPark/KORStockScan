# OpenAI WS Stability Report - 2026-05-20

- generated_at: `2026-05-20T16:56:56+09:00`
- decision: `keep_ws`
- unique WS calls: `3074`
- endpoint counts: `{'analyze_target': 2830, 'entry_price': 244}`
- WS fallback: `0` / `3074` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- WS transport warning: `{'ws_error_count': 0, 'ws_error_rate': 0.0, 'warning_only': False, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 2830, 'avg': 1194.4, 'median': 1080.0, 'p75': 1300.0, 'p90': 1604.1, 'p95': 1950.0, 'max': 9466.0}`
- WS roundtrip ms: `{'n': 3074, 'avg': 1151.8, 'median': 1035.0, 'p75': 1254.8, 'p90': 1565.7, 'p95': 1924.7, 'max': 9432.0}`
- WS queue wait ms: `{'n': 3074, 'avg': 0.4, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 0.3, 'max': 90.0}`
- <=3s rate: `0.9905`
- HTTP late baseline AI response ms: `{'n': 7, 'avg': 1963.0, 'median': 2008.0, 'p75': 2095.5, 'p90': 2200.2, 'p95': 2231.1, 'max': 2262.0}`
- baseline median improvement: `0.4622`
- baseline p75 improvement: `0.3796`
- entry_price WS sample count: `244`
- entry_price canary summary: `{'canary_event_count': 244, 'applied_count': 0, 'transport_observable_count': 244, 'applied_transport_observable_count': 0, 'ws_observable_unique_count': 244, 'applied_ai_eval_ms': {'n': 0, 'avg': None, 'median': None, 'p75': None, 'p90': None, 'p95': None, 'max': None}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price` WS transport 표본이 관찰됐다.
- 장중/장후 표본에서 fallback/fail-closed/latency guard를 계속 분리 확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
