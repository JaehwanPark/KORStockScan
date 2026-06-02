# OpenAI WS Stability Report - 2026-06-02

- generated_at: `2026-06-02T16:09:28+09:00`
- decision: `keep_ws`
- unique WS calls: `5994`
- endpoint counts: `{'analyze_target': 5994}`
- WS fallback: `0` / `5994` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{'TimeoutError': 1}`
- WS transport warning: `{'ws_error_count': 1, 'ws_error_rate': 0.0002, 'warning_only': True, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 5994, 'avg': 1307.5, 'median': 1127.0, 'p75': 1404.0, 'p90': 1828.1, 'p95': 2230.1, 'max': 15092.0}`
- WS roundtrip ms: `{'n': 5994, 'avg': 1167.9, 'median': 956.0, 'p75': 1241.5, 'p90': 1666.4, 'p95': 2075.7, 'max': 13113.0}`
- WS queue wait ms: `{'n': 5994, 'avg': 0.5, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 5.0, 'max': 73.0}`
- <=3s rate: `0.9778`
- HTTP late baseline AI response ms: `{'n': 12, 'avg': 3774.6, 'median': 2450.5, 'p75': 4262.8, 'p90': 6854.0, 'p95': 9736.5, 'max': 13108.0}`
- baseline median improvement: `0.5401`
- baseline p75 improvement: `0.6706`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 480, 'applied_count': 208, 'transport_observable_count': 479, 'applied_transport_observable_count': 208, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 208, 'avg': 824.9, 'median': 760.0, 'p75': 792.2, 'p90': 833.6, 'p95': 852.3, 'max': 8356.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
