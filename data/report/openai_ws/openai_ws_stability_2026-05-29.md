# OpenAI WS Stability Report - 2026-05-29

- generated_at: `2026-05-29T16:39:38+09:00`
- decision: `keep_ws`
- unique WS calls: `3422`
- endpoint counts: `{'analyze_target': 3422}`
- WS fallback: `0` / `3422` (`0.0`)
- WS success rate: `1.0`
- WS errors: `{'TimeoutError': 4}`
- WS transport warning: `{'ws_error_count': 4, 'ws_error_rate': 0.0012, 'warning_only': True, 'rollback_threshold_error_count': 3, 'rollback_threshold_error_rate': 0.01}`
- AI response ms: `{'n': 3422, 'avg': 1325.7, 'median': 1154.0, 'p75': 1403.0, 'p90': 1793.8, 'p95': 2310.7, 'max': 15419.0}`
- WS roundtrip ms: `{'n': 3422, 'avg': 1138.3, 'median': 947.0, 'p75': 1209.0, 'p90': 1581.9, 'p95': 2096.4, 'max': 13949.0}`
- WS queue wait ms: `{'n': 3422, 'avg': 0.4, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 1.0, 'max': 89.0}`
- <=3s rate: `0.9781`
- HTTP late baseline AI response ms: `{'n': 4, 'avg': 1630.5, 'median': 1510.5, 'p75': 1662.2, 'p90': 1918.3, 'p95': 2003.6, 'max': 2089.0}`
- baseline median improvement: `0.236`
- baseline p75 improvement: `0.1559`
- entry_price WS sample count: `0`
- entry_price canary summary: `{'canary_event_count': 281, 'applied_count': 129, 'transport_observable_count': 281, 'applied_transport_observable_count': 129, 'ws_observable_unique_count': 0, 'applied_ai_eval_ms': {'n': 129, 'avg': 1981.3, 'median': 1805.0, 'p75': 2180.0, 'p90': 2815.2, 'p95': 3350.4, 'max': 9523.0}, 'instrumentation_gap': False}`

## 판정

- `analyze_target` WS는 표본수, fallback, p75/p90/p95 latency, HTTP late baseline 대비 개선 기준을 충족한다.
- `entry_price`는 해당 날짜에 WS transport 표본이 없어 hook 미발생 또는 표본 부족으로 분리한다.
- 이는 OpenAI WS 실패 근거가 아니며, 다음 장중 표본에서 `entry_price` provenance를 재확인한다.
- 런타임 threshold, 주문 guard, provider route를 추가 변경하지 않고 현재 OpenAI WS 설정을 유지한다.
