# Tuning Observability Summary

- target_date: `2026-05-18`
- analysis_period: `2026-04-21 ~ 2026-05-18`

## Entry Funnel

- gatekeeper_decisions: `62`
- gatekeeper_eval_ms_p95: `5441ms`
- gatekeeper_lock_wait_ms_p95: `0ms`
- gatekeeper_model_call_ms_p95: `5441ms`
- budget_pass_events: `11`
- submitted_events: `0`
- budget_pass_to_submitted_rate: `0.0%`
- latency_block_events: `11`
- quote_fresh_latency_blocks: `10`

## Buy Recovery Canary

- total_candidates: `12`
- recovery_check: `0`
- promoted: `0`
- submitted: `0`
- blocked_ai_score_share: `91.7%`

## Priority Findings

- `AI threshold dominance`: 경고 — `blocked_ai_score_share=91.7%`로 WAIT/BLOCK 비중이 높아 BUY drought 해석을 지지한다.
- `Budget pass without submit`: 경고 — `budget_pass=11`인데 `submitted=0`라 제출 전 병목이 기대값 회복을 끊고 있다.
