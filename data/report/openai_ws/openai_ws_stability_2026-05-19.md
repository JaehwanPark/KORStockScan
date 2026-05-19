# OpenAI WS Stability Report - 2026-05-19

- generated_at: `2026-05-19T16:12:45+09:00`
- decision: `keep_ws`
- unique WS calls: `3960`
- endpoint counts: `{'analyze_target': 3854, 'entry_price': 106}`
- WS fallback: `0` / `3960` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{'TimeoutError': 4}`
- WS transport warning: `{'ws_error_count': 4, 'ws_error_rate': 0.001, 'warning_only': True, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 3854, 'avg': 1256.1, 'median': 1128.0, 'p75': 1381.8, 'p90': 1747.0, 'p95': 2040.3, 'max': 15120.0}`
- WS roundtrip ms: `{'n': 3960, 'avg': 1204.5, 'median': 1096.0, 'p75': 1342.0, 'p90': 1699.2, 'p95': 1999.1, 'max': 12663.0}`
- WS queue wait ms: `{'n': 3960, 'avg': 0.3, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 1.0, 'max': 227.0}`
- <=3s rate: `0.9899`
- HTTP late baseline AI response ms: `{'n': 10, 'avg': 4142.6, 'median': 2980.5, 'p75': 3175.8, 'p90': 6466.7, 'p95': 11662.9, 'max': 16859.0}`
- baseline median improvement: `0.6215`
- baseline p75 improvement: `0.5649`
- entry_price WS sample count: `106`
- entry_price canary summary: `{'canary_event_count': 106, 'applied_count': 9, 'transport_observable_count': 106, 'applied_transport_observable_count': 9, 'ws_observable_unique_count': 106, 'applied_ai_eval_ms': {'n': 9, 'avg': 1527.3, 'median': 1506.0, 'p75': 1715.0, 'p90': 1848.8, 'p95': 1926.4, 'max': 2004.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price` WS transport 표본이 관찰됐다.
- 장중/장후 표본에서 fallback/fail-closed/latency guard를 계속 분리 확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
