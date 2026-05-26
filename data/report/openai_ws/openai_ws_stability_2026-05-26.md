# OpenAI WS Stability Report - 2026-05-26

- generated_at: `2026-05-26T16:18:26+09:00`
- decision: `keep_ws`
- unique WS calls: `6506`
- endpoint counts: `{'analyze_target': 6506}`
- WS fallback: `0` / `6506` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{'TimeoutError': 4}`
- WS transport warning: `{'ws_error_count': 4, 'ws_error_rate': 0.0006, 'warning_only': True, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 6506, 'avg': 1243.3, 'median': 1081.5, 'p75': 1332.0, 'p90': 1679.0, 'p95': 2014.2, 'max': 15418.0}`
- WS roundtrip ms: `{'n': 6506, 'avg': 1084.3, 'median': 914.0, 'p75': 1157.8, 'p90': 1485.0, 'p95': 1811.2, 'max': 12105.0}`
- WS queue wait ms: `{'n': 6506, 'avg': 0.4, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 1.0, 'max': 522.0}`
- <=3s rate: `0.9774`
- HTTP late baseline AI response ms: `{'n': 10, 'avg': 4730.6, 'median': 3409.0, 'p75': 7645.0, 'p90': 8012.3, 'p95': 8877.7, 'max': 9743.0}`
- baseline median improvement: `0.6828`
- baseline p75 improvement: `0.8258`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 583, 'applied_count': 430, 'transport_observable_count': 583, 'applied_transport_observable_count': 430, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 430, 'avg': 1367.0, 'median': 1213.0, 'p75': 1481.5, 'p90': 1868.2, 'p95': 2341.8, 'max': 5815.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
