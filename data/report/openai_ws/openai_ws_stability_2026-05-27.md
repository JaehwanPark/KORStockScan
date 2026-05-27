# OpenAI WS Stability Report - 2026-05-27

- generated_at: `2026-05-27T18:53:47+09:00`
- decision: `keep_ws`
- unique WS calls: `5769`
- endpoint counts: `{'analyze_target': 5769}`
- WS fallback: `0` / `5769` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{}`
- WS transport warning: `{'ws_error_count': 0, 'ws_error_rate': 0.0, 'warning_only': False, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 5769, 'avg': 1108.5, 'median': 1007.0, 'p75': 1208.0, 'p90': 1489.2, 'p95': 1745.2, 'max': 10640.0}`
- WS roundtrip ms: `{'n': 5769, 'avg': 966.9, 'median': 868.0, 'p75': 986.0, 'p90': 1317.0, 'p95': 1569.6, 'max': 10313.0}`
- WS queue wait ms: `{'n': 5769, 'avg': 0.4, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 0.0, 'max': 77.0}`
- <=3s rate: `0.9957`
- HTTP late baseline AI response ms: `{'n': 8, 'avg': 4565.8, 'median': 3181.5, 'p75': 8033.5, 'p90': 8354.8, 'p95': 8507.4, 'max': 8660.0}`
- baseline median improvement: `0.6835`
- baseline p75 improvement: `0.8496`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 523, 'applied_count': 205, 'transport_observable_count': 523, 'applied_transport_observable_count': 205, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 205, 'avg': 1620.1, 'median': 1414.0, 'p75': 1755.0, 'p90': 2066.6, 'p95': 2603.6, 'max': 8580.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
