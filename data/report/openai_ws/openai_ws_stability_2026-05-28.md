# OpenAI WS Stability Report - 2026-05-28

- generated_at: `2026-05-28T13:02:06+09:00`
- decision: `keep_ws`
- unique WS calls: `3660`
- endpoint counts: `{'analyze_target': 3655, 'entry_price': 5}`
- WS fallback: `0` / `3660` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- WS transport warning: `{'ws_error_count': 0, 'ws_error_rate': 0.0, 'warning_only': False, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 3655, 'avg': 1235.8, 'median': 1159.0, 'p75': 1366.0, 'p90': 1612.0, 'p95': 1810.9, 'max': 6922.0}`
- WS roundtrip ms: `{'n': 3660, 'avg': 1076.4, 'median': 946.0, 'p75': 1226.0, 'p90': 1388.3, 'p95': 1608.2, 'max': 6623.0}`
- WS queue wait ms: `{'n': 3660, 'avg': 8.9, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 1.0, 'max': 8908.0}`
- <=3s rate: `0.9863`
- HTTP late baseline AI response ms: `{'n': 9, 'avg': 5607.7, 'median': 5328.0, 'p75': 7724.0, 'p90': 9036.6, 'p95': 10683.8, 'max': 12331.0}`
- baseline median improvement: `0.7825`
- baseline p75 improvement: `0.8231`
- entry_price WS sample count: `5`
- entry_price canary summary: `{'canary_event_count': 284, 'applied_count': 153, 'transport_observable_count': 284, 'applied_transport_observable_count': 153, 'ws_observable_unique_count': 5, 'applied_ai_eval_ms': {'n': 153, 'avg': 1709.7, 'median': 1525.0, 'p75': 1841.0, 'p90': 2340.4, 'p95': 2565.8, 'max': 10797.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price` WS transport 표본이 관찰됐다.
- 장중/장후 표본에서 fallback/fail-closed/latency guard를 계속 분리 확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
