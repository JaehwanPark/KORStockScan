# Tuning Observability Summary

- target_date: `2026-05-15`
- analysis_period: `2026-05-15 ~ 2026-05-15`

## Entry Funnel

- gatekeeper_decisions: `81`
- gatekeeper_eval_ms_p95: `5421ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `5421ms`
- budget_pass_events: `82`
- submitted_events: `0`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `82`
- quote_fresh_latency_blocks: `81`

## Buy Recovery Canary

- total_candidates: `19`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `100.0%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=100.0%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
- `Budget pass without submit`: 경고 — `budget_pass=82`인데 `submitted=0`라 제출 전 병목이 기대값 회복을 끊고 있다.
